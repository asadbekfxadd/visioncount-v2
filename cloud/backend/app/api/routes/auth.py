import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# защита от подбора пароля: 10 неудачных попыток за 15 минут на email и на адрес
_FAILS: dict[str, list[float]] = defaultdict(list)
_MAX, _WINDOW = 10, 15 * 60


def _client_ip(request: Request) -> str:
    # за прокси (Railway) настоящий адрес — последний элемент X-Forwarded-For (его добавляет сам прокси)
    xff = request.headers.get("x-forwarded-for", "")
    return (xff.split(",")[-1].strip() if xff else (request.client.host if request.client else "?"))[:60]


def _keys(request: Request, email: str) -> list[str]:
    return [f"ip:{_client_ip(request)}", f"email:{email.lower()[:120]}"]


def _blocked(keys: list[str]) -> bool:
    now = time.time()
    for k in keys:
        _FAILS[k] = [t for t in _FAILS[k] if now - t < _WINDOW]
    return any(len(_FAILS[k]) >= _MAX for k in keys)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    keys = _keys(request, payload.email)
    if _blocked(keys):
        raise HTTPException(status_code=429, detail="Слишком много попыток входа. Повторите через 15 минут.")
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        now = time.time()
        for k in keys:
            _FAILS[k].append(now)
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь деактивирован")

    for k in keys:
        _FAILS.pop(k, None)
    token = create_access_token(subject=user.id, extra_claims={"role": user.role.value, "company_id": user.company_id})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
