from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tariff

router = APIRouter(
    prefix="/tariffs",
    tags=["Tariffs"]
)


@router.get("")
def get_tariffs(
    db: Session = Depends(get_db)
):
    return db.query(Tariff).all()