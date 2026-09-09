from app.config import settings
from app.db.models import Base, SessionLocal, engine


def init_db() -> None:
    if engine is not None:
        Base.metadata.create_all(bind=engine)


def get_db():
    if SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
