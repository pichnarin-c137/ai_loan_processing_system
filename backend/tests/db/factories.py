from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Applicant, LoanApplication
from app.models.enums import Product


def new_application(session: Session) -> LoanApplication:
    """A synthetic application that is not in the session yet (its applicant is flushed)."""
    applicant = Applicant(
        full_name_en="Sample Applicant",
        dob=date(1990, 1, 1),
        national_id="000000000",
        phone="+855 00 000 000",
    )
    session.add(applicant)
    session.flush()
    return LoanApplication(
        applicant_id=applicant.id,
        product=Product.PERSONAL,
        amount_usd=Decimal("1000.00"),
        term_months=12,
        purpose="test",
        created_by="tester",
    )
