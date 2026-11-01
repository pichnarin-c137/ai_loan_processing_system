import uuid
from tempfile import SpooledTemporaryFile
from typing import TYPE_CHECKING, Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.auth import CurrentUser, require_role
from app.core.config import get_settings
from app.core.db import get_session
from app.core.storage import get_s3_client
from app.models import Applicant, Document, LoanApplication
from app.models.enums import ActorType, Currency, DocType, Product, Role, Stage
from app.schemas.applications import (
    MAX_TERM,
    MIN_TERM,
    ApplicantIn,
    ApplicationDetail,
    ApplicationSummary,
    DocumentOut,
    LoanIn,
    LoanOptions,
    SubmitIn,
)
from app.services import applications as svc
from app.services import documents as docs
from app.services.audit import record

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

router = APIRouter(tags=["applications"])

Customer = Annotated[CurrentUser, Depends(require_role(Role.CUSTOMER))]
DbSession = Annotated[Session, Depends(get_session)]

_PDF_BODY = {"schema": {"type": "string", "format": "binary"}}
_UPLOAD_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "application/pdf": _PDF_BODY,
            "image/jpeg": _PDF_BODY,
            "image/png": _PDF_BODY,
        },
    }
}


@router.get("/loan-options")
def loan_options(_user: Customer, session: DbSession) -> LoanOptions:
    policy = svc.current_policy(session)
    return LoanOptions(
        policy_version=policy.version,
        khr_per_usd=policy.khr_per_usd,
        max_amount={c: svc.max_amount(c, policy) for c in Currency},
        min_term_months=MIN_TERM,
        max_term_months=MAX_TERM,
        products=list(Product),
    )


@router.post("/applications", status_code=201)
def create_application(body: LoanIn, user: Customer, session: DbSession) -> ApplicationDetail:
    svc.check_amount(body.amount, body.currency, svc.current_policy(session))
    application = LoanApplication(
        product=body.product,
        currency=body.currency,
        amount=body.amount,
        term_months=body.term_months,
        purpose=body.purpose,
        stage=Stage.DRAFT,
        created_by=user.id,
    )
    record(
        session,
        actor_type=ActorType.HUMAN,
        actor_id=user.id,
        action="application.created",
        payload={"product": body.product, "currency": body.currency},
        application=application,
    )
    session.commit()
    session.refresh(application)
    return svc.to_detail(session, application)


@router.get("/applications")
def list_applications(user: Customer, session: DbSession) -> list[ApplicationSummary]:
    rows = session.scalars(
        select(LoanApplication)
        .where(LoanApplication.created_by == user.id)
        .order_by(LoanApplication.created_at.desc())
    )
    return [svc.to_summary(row) for row in rows]


@router.get("/applications/{app_id}")
def get_application(app_id: uuid.UUID, user: Customer, session: DbSession) -> ApplicationDetail:
    return svc.to_detail(session, svc.own_application(session, app_id, user))


@router.put("/applications/{app_id}/loan")
def update_loan(
    app_id: uuid.UUID, body: LoanIn, user: Customer, session: DbSession
) -> ApplicationDetail:
    application = svc.own_application(session, app_id, user, lock=True)
    svc.require_draft(application)
    svc.check_amount(body.amount, body.currency, svc.current_policy(session))
    changed = [
        name
        for name in ("product", "currency", "amount", "term_months", "purpose")
        if getattr(application, name) != getattr(body, name)
    ]
    for name in changed:
        setattr(application, name, getattr(body, name))
    removed: list[str] = []
    if "product" in changed:
        needed = svc.required_documents(application.product)
        for doc in svc.active_documents(session, application):
            if doc.doc_type not in needed:
                # Kept, not deleted, like a replaced file.
                doc.replaced_at = func.clock_timestamp()
                removed.append(str(doc.id))
        session.flush()
    payload: dict[str, object] = {"fields": changed}
    if removed:
        payload["removed_document_ids"] = removed
    record(
        session,
        actor_type=ActorType.HUMAN,
        actor_id=user.id,
        action="application.updated",
        payload=payload,
        application=application,
    )
    session.commit()
    session.refresh(application)
    return svc.to_detail(session, application)


@router.put("/applications/{app_id}/applicant")
def save_applicant(
    app_id: uuid.UUID, body: ApplicantIn, user: Customer, session: DbSession
) -> ApplicationDetail:
    application = svc.own_application(session, app_id, user, lock=True)
    svc.require_draft(application)
    applicant = (
        session.get(Applicant, application.applicant_id) if application.applicant_id else None
    )
    if applicant is None:
        applicant = Applicant(user_id=user.id)
        session.add(applicant)
    fields = ["full_name_km", "full_name_en", "dob", "national_id", "phone"]
    for name in fields:
        setattr(applicant, name, getattr(body, name))
    session.flush()
    application.applicant_id = applicant.id
    record(
        session,
        actor_type=ActorType.HUMAN,
        actor_id=user.id,
        action="applicant.saved",
        payload={"fields": fields},
        application=application,
    )
    session.commit()
    session.refresh(application)
    return svc.to_detail(session, application)


def _precheck_upload(
    session: Session, app_id: uuid.UUID, doc_type: DocType, user: CurrentUser
) -> None:
    try:
        application = svc.own_application(session, app_id, user)
        svc.require_draft(application)
        if doc_type not in svc.required_documents(application.product):
            raise HTTPException(422, detail={"code": "doc_type_not_needed"})
    finally:
        session.rollback()


def _store_document(
    session: Session,
    s3: "S3Client",
    *,
    app_id: uuid.UUID,
    doc_type: DocType,
    user: CurrentUser,
    file: SpooledTemporaryFile[bytes],
    sha256: str,
    size: int,
    content_type: str,
    page_count: int,
) -> DocumentOut:
    try:
        application = svc.own_application(session, app_id, user, lock=True)
        svc.require_draft(application)
        old = session.scalars(
            select(Document).where(
                Document.application_id == app_id,
                Document.doc_type == doc_type,
                Document.replaced_at.is_(None),
            )
        ).first()
        if old is not None:
            old.replaced_at = func.clock_timestamp()
            session.flush()
        doc_id = uuid.uuid4()
        key = f"applications/{app_id}/documents/{doc_id}"
        document = Document(
            id=doc_id,
            application_id=app_id,
            doc_type=doc_type,
            storage_key=key,
            sha256=sha256,
            page_count=page_count,
            content_type=content_type,
            size_bytes=size,
            uploaded_by=user.id,
        )
        session.add(document)
        session.flush()
        file.seek(0)
        try:
            s3.put_object(
                Bucket=get_settings().s3_bucket,
                Key=key,
                Body=file,
                ContentType=content_type,
                ContentLength=size,
            )
        except (BotoCoreError, ClientError):
            session.rollback()
            raise HTTPException(503, detail={"code": "storage_unavailable"}) from None
        record(
            session,
            actor_type=ActorType.HUMAN,
            actor_id=user.id,
            action="document.uploaded",
            payload={
                "document_id": doc_id,
                "doc_type": doc_type,
                "sha256": sha256,
                "size_bytes": size,
                "page_count": page_count,
                "replaced_document_id": old.id if old is not None else None,
            },
            application=application,
        )
        session.commit()
        session.refresh(document)
        return DocumentOut.model_validate(document)
    except BaseException:
        session.rollback()
        raise


@router.put(
    "/applications/{app_id}/documents/{doc_type}", status_code=201, openapi_extra=_UPLOAD_BODY
)
async def upload_document(
    app_id: uuid.UUID,
    doc_type: DocType,
    request: Request,
    user: Customer,
    session: DbSession,
    s3: Annotated["S3Client", Depends(get_s3_client)],
) -> DocumentOut:
    await run_in_threadpool(_precheck_upload, session, app_id, doc_type, user)
    file, sha256, size = await docs.read_body(request)
    try:
        content_type, page_count = await run_in_threadpool(docs.inspect, file)
        return await run_in_threadpool(
            _store_document,
            session,
            s3,
            app_id=app_id,
            doc_type=doc_type,
            user=user,
            file=file,
            sha256=sha256,
            size=size,
            content_type=content_type,
            page_count=page_count,
        )
    finally:
        file.close()


@router.post("/applications/{app_id}/submit")
def submit_application(
    app_id: uuid.UUID, _body: SubmitIn, user: Customer, session: DbSession
) -> ApplicationDetail:
    application = svc.own_application(session, app_id, user, lock=True)
    svc.require_draft(application)
    missing = svc.missing_items(session, application)
    if missing:
        raise HTTPException(409, detail={"code": "incomplete", "missing": missing})
    policy = svc.current_policy(session)
    svc.check_amount(application.amount, application.currency, policy)
    application.stage = Stage.SUBMITTED
    application.submitted_at = func.clock_timestamp()
    application.policy_version = policy.version
    record(
        session,
        actor_type=ActorType.HUMAN,
        actor_id=user.id,
        action="application.submitted",
        payload={"policy_version": policy.version},
        application=application,
    )
    session.commit()
    session.refresh(application)
    return svc.to_detail(session, application)
