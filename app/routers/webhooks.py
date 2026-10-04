from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BankWebhook
from app.services import (
    can_transition,
    get_payment_by_id,
    update_payment_status,
)

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)


@router.post(
    "/bank",
    responses={
        404: {
            "description": "Payment not found",
        },
        409: {
            "description": "Invalid status transition",
        },
    },
)
def bank_webhook(
    payload: BankWebhook,
    db: Session = Depends(get_db),
):

    payment = get_payment_by_id(
        db,
        payload.payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if not can_transition(
        payment.status,
        payload.status,
    ):
        return JSONResponse(
            status_code=409,
            content={
                "error": "invalid_transition",
            },
        )

    update_payment_status(
        db,
        payment,
        payload.status,
    )

    return {
        "result": "ok"
    }