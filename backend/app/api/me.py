from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import CurrentUser, current_user
from app.models.enums import Role

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    id: str
    role: Role


@router.get("/me")
def me(user: Annotated[CurrentUser, Depends(current_user)]) -> MeResponse:
    return MeResponse(id=user.id, role=user.role)
