from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import get_db
from app.deps import get_current_user, require_role
from app.models.models import User, UserRole
from app.schemas.schemas import UserOut
from pydantic import BaseModel, EmailStr

router = APIRouter(tags=["users"])


class UserInvite(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    password: str


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (await db.execute(select(User).where(User.company_id == user.company_id))).scalars().all()
    return rows


@router.post("/users", response_model=UserOut, status_code=201)
async def invite_user(
    payload: UserInvite,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    from app.deps import ROLE_RANK
    if ROLE_RANK[payload.role] > ROLE_RANK[user.role]:
        raise HTTPException(status_code=403, detail="Нельзя назначить роль выше своей")
    if (await db.execute(select(User.id).where(User.email == payload.email))).first():
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже есть")
    new_user = User(
        company_id=user.company_id, email=payload.email, full_name=payload.full_name,
        hashed_password=hash_password(payload.password), role=payload.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
