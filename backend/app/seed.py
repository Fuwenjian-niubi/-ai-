from sqlalchemy.orm import Session

from . import models, security
from .config import settings
from .database import SessionLocal


def seed_admin() -> None:
    db: Session = SessionLocal()
    try:
        exists = (
            db.query(models.User)
            .filter(models.User.username == settings.ADMIN_USERNAME)
            .first()
        )
        if not exists:
            admin = models.User(
                username=settings.ADMIN_USERNAME,
                password_hash=security.hash_password(settings.ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
