from enum import StrEnum


# No separate committee stage; decisions.role records whether a manager or the
# committee signed at MANAGER_APPROVAL.
class Stage(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    EXTRACTING = "EXTRACTING"
    CHECKING = "CHECKING"
    ANALYST_REVIEW = "ANALYST_REVIEW"
    RISK_REVIEW = "RISK_REVIEW"
    MANAGER_APPROVAL = "MANAGER_APPROVAL"
    INFO_REQUESTED = "INFO_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Role(StrEnum):
    CUSTOMER = "customer"
    OFFICER = "officer"
    ANALYST = "analyst"
    RISK = "risk"
    MANAGER = "manager"
    COMMITTEE = "committee"
    ADMIN = "admin"


class ActorType(StrEnum):
    AI = "ai"
    RULE = "rule"
    HUMAN = "human"
    SYSTEM = "system"


class Product(StrEnum):
    PERSONAL = "personal"
    SMALL_BUSINESS = "small_business"


class DocType(StrEnum):
    NATIONAL_ID = "national_id"
    PAYSLIP = "payslip"
    BANK_STATEMENT = "bank_statement"
    BUSINESS_LICENSE = "business_license"
    OTHER = "other"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FlagStatus(StrEnum):
    OPEN = "open"
    CLEARED = "cleared"
    CONFIRMED = "confirmed"


class DecisionKind(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_INFO = "request_info"


class Recommendation(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REFER = "refer"


class RuleAction(StrEnum):
    REJECT = "reject"
    ANALYST_REVIEW = "analyst_review"
    REQUEST_INFO = "request_info"
    RISK_REVIEW = "risk_review"
    OFFICER_VERIFY = "officer_verify"


class AiCallStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Currency(StrEnum):
    USD = "USD"
    KHR = "KHR"


# What the customer sees; derived from Stage, never stored.
class CustomerStatus(StrEnum):
    DRAFT = "draft"
    CHECKING = "checking"
    UNDER_REVIEW = "under_review"
    ACTION_NEEDED = "action_needed"
    APPROVED = "approved"
    NOT_APPROVED = "not_approved"
