from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if (
        db.query(models.User)
        .filter(models.User.username == req.username)
        .first()
    ):
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = models.User(
        username=req.username,
        password_hash=security.hash_password(req.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
        .filter(models.User.username == req.username)
        .first()
    )
    if not user or not security.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = security.create_access_token(str(user.id), user.role)
    return schemas.TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    req: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not security.verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = security.hash_password(req.new_password)
    db.commit()
    return {"msg": "密码已修改"}
