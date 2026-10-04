from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PaymentCreate
from app.schemas import PaymentResponse
from app.services import create_payment_record
from app.services import get_tariff_by_id


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
):
    tariff = get_tariff_by_id(
        db=db,
        tariff_id=payload.tariff_id,
    )

    if tariff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tariff not found",
        )

    return create_payment_record(
        db=db,
        payload=payload,
        tariff=tariff,
    )


@router.get("/{payment_id}")
def get_payment(payment_id: int):
    return {
        "payment_id": payment_id,
    }