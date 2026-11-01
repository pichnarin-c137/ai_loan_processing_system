import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.core import clock
from app.models.enums import Currency, CustomerStatus, DocType, Product

MIN_AGE = 18
MAX_AGE = 75
MIN_TERM = 3
MAX_TERM = 60
_PHONE = re.compile(r"^(\+855|0)[0-9]{8,9}$")
_NATIONAL_ID = re.compile(r"^[0-9]{9}$")


def _places(value: Decimal) -> int:
    _, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int) or exponent >= 0:
        return 0
    trailing = 0
    for digit in reversed(digits):
        if digit != 0:
            break
        trailing += 1
    return max(0, -exponent - trailing)


class LoanIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product: Product
    currency: Currency
    amount: Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
    term_months: Annotated[int, Field(ge=MIN_TERM, le=MAX_TERM)]
    purpose: Annotated[str, Field(min_length=1, max_length=500)]

    @field_validator("amount")
    @classmethod
    def _check_places(cls, value: Decimal, info: ValidationInfo) -> Decimal:
        currency = info.data.get("currency")
        places = _places(value)
        if currency == Currency.USD and places > 2:
            raise PydanticCustomError("amount_decimals", "At most 2 decimal places")
        if currency == Currency.KHR and places > 0:
            raise PydanticCustomError("amount_whole_riel", "Whole riel only")
        return value


def _age(dob: date, today: date) -> int:
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class ApplicantIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name_km: Annotated[str | None, Field(max_length=100)] = None
    full_name_en: Annotated[str | None, Field(max_length=100)] = None
    dob: date
    national_id: str
    phone: str

    @field_validator("full_name_km", "full_name_en")
    @classmethod
    def _empty_to_none(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def _need_a_name(self) -> Self:
        if self.full_name_km is None and self.full_name_en is None:
            raise PydanticCustomError("name_required", "Enter a name in Khmer or English")
        return self

    @field_validator("dob")
    @classmethod
    def _check_age(cls, value: date) -> date:
        if not MIN_AGE <= _age(value, clock.today()) <= MAX_AGE:
            raise PydanticCustomError("age_range", "Age must be between 18 and 75")
        return value

    @field_validator("national_id")
    @classmethod
    def _check_national_id(cls, value: str) -> str:
        if not _NATIONAL_ID.match(value):
            raise PydanticCustomError("national_id_format", "National ID is 9 digits")
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def _normalize_phone(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = re.sub(r"[ \-]", "", value.strip())
            if not _PHONE.match(value):
                raise PydanticCustomError("phone_format", "Enter a Cambodian phone number")
        return value


class SubmitIn(BaseModel):
    confirm_sample: Literal[True]


class ApplicantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name_km: str | None
    full_name_en: str | None
    dob: date
    national_id: str
    phone: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doc_type: DocType
    content_type: str
    size_bytes: int
    page_count: int
    uploaded_at: datetime


class ApplicationSummary(BaseModel):
    id: uuid.UUID
    product: Product
    currency: Currency
    amount: Decimal
    term_months: int
    status: CustomerStatus
    created_at: datetime
    submitted_at: datetime | None


class ApplicationDetail(ApplicationSummary):
    purpose: str
    updated_at: datetime
    applicant: ApplicantOut | None
    documents: list[DocumentOut]
    required_documents: list[DocType]
    missing: list[str]


class LoanOptions(BaseModel):
    policy_version: str
    khr_per_usd: Decimal
    max_amount: dict[Currency, Decimal]
    min_term_months: int
    max_term_months: int
    products: list[Product]
