import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.auth import CurrentUser
from app.models import Applicant, Document, LoanApplication, PolicyVersion
from app.models.enums import Currency, CustomerStatus, DocType, Product, Stage
from app.schemas.applications import (
    ApplicantOut,
    ApplicationDetail,
    ApplicationSummary,
    DocumentOut,
)

MAX_LOAN_USD = Decimal(20000)

_STATUS: dict[Stage, CustomerStatus] = {
    Stage.DRAFT: CustomerStatus.DRAFT,
    Stage.SUBMITTED: CustomerStatus.CHECKING,
    Stage.EXTRACTING: CustomerStatus.CHECKING,
    Stage.CHECKING: CustomerStatus.CHECKING,
    Stage.ANALYST_REVIEW: CustomerStatus.UNDER_REVIEW,
    Stage.RISK_REVIEW: CustomerStatus.UNDER_REVIEW,
    Stage.MANAGER_APPROVAL: CustomerStatus.UNDER_REVIEW,
    Stage.INFO_REQUESTED: CustomerStatus.ACTION_NEEDED,
    Stage.APPROVED: CustomerStatus.APPROVED,
    Stage.REJECTED: CustomerStatus.NOT_APPROVED,
}


def required_documents(product: Product) -> list[DocType]:
    docs = [DocType.NATIONAL_ID, DocType.PAYSLIP, DocType.BANK_STATEMENT]
    if product == Product.SMALL_BUSINESS:
        docs.append(DocType.BUSINESS_LICENSE)
    return docs


def customer_status(stage: Stage) -> CustomerStatus:
    return _STATUS[stage]


def current_policy(session: Session) -> PolicyVersion:
    policy = session.scalars(
        select(PolicyVersion)
        .where(PolicyVersion.effective_from <= clock.today())
        .order_by(PolicyVersion.effective_from.desc())
        .limit(1)
    ).first()
    if policy is None:
        raise HTTPException(503, detail={"code": "no_policy"})
    return policy


def to_usd(amount: Decimal, currency: Currency, policy: PolicyVersion) -> Decimal:
    return amount / policy.khr_per_usd if currency == Currency.KHR else amount


def max_amount(currency: Currency, policy: PolicyVersion) -> Decimal:
    if currency == Currency.KHR:
        return MAX_LOAN_USD * policy.khr_per_usd
    return MAX_LOAN_USD


def check_amount(amount: Decimal, currency: Currency, policy: PolicyVersion) -> None:
    limit = max_amount(currency, policy)
    if amount > limit:
        raise HTTPException(
            422,
            detail=[
                {
                    "type": "amount_too_high",
                    "loc": ["body", "amount"],
                    "msg": "Amount is above the limit",
                    "ctx": {"max": str(limit.quantize(Decimal(1)))},
                }
            ],
        )


def own_application(
    session: Session, app_id: uuid.UUID, user: CurrentUser, *, lock: bool = False
) -> LoanApplication:
    query = select(LoanApplication).where(
        LoanApplication.id == app_id, LoanApplication.created_by == user.id
    )
    if lock:
        query = query.with_for_update()
    application = session.scalars(query).first()
    if application is None:
        raise HTTPException(404, detail={"code": "not_found"})
    return application


def require_draft(application: LoanApplication) -> None:
    if application.stage != Stage.DRAFT:
        raise HTTPException(409, detail={"code": "not_draft"})


def active_documents(session: Session, application: LoanApplication) -> list[Document]:
    return list(
        session.scalars(
            select(Document)
            .where(Document.application_id == application.id, Document.replaced_at.is_(None))
            .order_by(Document.uploaded_at)
        )
    )


def missing_items(
    session: Session, application: LoanApplication, documents: list[Document] | None = None
) -> list[str]:
    missing: list[str] = []
    if application.applicant_id is None:
        missing.append("applicant")
    if documents is None:
        documents = active_documents(session, application)
    have = {doc.doc_type for doc in documents}
    missing.extend(doc.value for doc in required_documents(application.product) if doc not in have)
    return missing


def to_summary(application: LoanApplication) -> ApplicationSummary:
    return ApplicationSummary(
        id=application.id,
        product=application.product,
        currency=application.currency,
        amount=application.amount,
        term_months=application.term_months,
        status=customer_status(application.stage),
        created_at=application.created_at,
        submitted_at=application.submitted_at,
    )


def to_detail(session: Session, application: LoanApplication) -> ApplicationDetail:
    applicant = (
        session.get(Applicant, application.applicant_id) if application.applicant_id else None
    )
    documents = active_documents(session, application)
    return ApplicationDetail(
        **to_summary(application).model_dump(),
        purpose=application.purpose,
        updated_at=application.updated_at,
        applicant=ApplicantOut.model_validate(applicant) if applicant else None,
        documents=[DocumentOut.model_validate(doc) for doc in documents],
        required_documents=required_documents(application.product),
        missing=missing_items(session, application, documents),
    )
