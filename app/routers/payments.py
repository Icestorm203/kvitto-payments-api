from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi import Header
from fastapi import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PaymentCreate
from app.schemas import PaymentResponse
from app.services import create_payment_record
from app.services import get_tariff_by_id
from app.services import get_payment_by_idempotency_key
from app.services import get_payment_by_id

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "model": PaymentResponse,
            "description": (
                "Existing payment returned for "
                "the same Idempotency-Key"
            ),
        },
        201: {
            "model": PaymentResponse,
            "description": "Payment created",
        },
    },
)
def create_payment(
    payload: PaymentCreate,
    response: Response,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    if idempotency_key:
        existing_payment = get_payment_by_idempotency_key(
            db=db,
            idempotency_key=idempotency_key,
        )

        if existing_payment is not None:
            response.status_code = status.HTTP_200_OK
            return existing_payment

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
        idempotency_key=idempotency_key,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    responses={
        404: {
            "description": "Payment not found",
        },
    },
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    payment = get_payment_by_id(
        db=db,
        payment_id=payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return payment