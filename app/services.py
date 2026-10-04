from sqlalchemy.orm import Session

from app.constants import TARIFFS
from app.models import Tariff

from fastapi import HTTPException

from app.constants import PROMO_CODE
from app.constants import PROMO_DISCOUNT_PERCENT
from app.constants import VALID_INSTALLMENT_MONTHS

from app.models import Payment
from app.schemas import PaymentCreate

def seed_tariffs(db: Session):
    existing_count = db.query(Tariff).count()

    if existing_count:
        return

    for tariff in TARIFFS:
        db.add(
            Tariff(
                title=tariff["title"],
                price=tariff["price"]
            )
        )

    db.commit()


def calculate_discount(
    amount: int,
    promo_code: str | None,
) -> tuple[int, int]:
    """
    return:
    (discount, final_amount)
    """

    if not promo_code:
        return 0, amount

    if promo_code.upper() != PROMO_CODE:
        raise HTTPException(
            status_code=422,
            detail="Invalid promo code"
        )

    discount = (
        amount * PROMO_DISCOUNT_PERCENT
    ) // 100

    final_amount = amount - discount

    return discount, final_amount


def calculate_schedule(
    amount: int,
    months: int,
) -> list[int]:

    if months not in VALID_INSTALLMENT_MONTHS:
        raise HTTPException(
            status_code=422,
            detail="Invalid installment period"
        )

    base_payment = amount // months

    remainder = amount % months

    schedule: list[int] = []

    for i in range(months):

        payment = base_payment

        if i < remainder:
            payment += 1

        schedule.append(payment)

    return schedule


def get_tariff_by_id(
    db: Session,
    tariff_id: int,
):
    return (
        db.query(Tariff)
        .filter(Tariff.id == tariff_id)
        .first()
    )


def get_tariff_by_id(
    db: Session,
    tariff_id: int,
) -> Tariff | None:
    return (
        db.query(Tariff)
        .filter(Tariff.id == tariff_id)
        .first()
    )


def create_payment_record(
    db: Session,
    payload: PaymentCreate,
    tariff: Tariff,
    idempotency_key: str | None,
) -> Payment:
    discount, final_amount = calculate_discount(
        amount=tariff.price,
        promo_code=payload.promo_code,
    )

    schedule: list[int] | None = None

    if payload.method == "installment":
        schedule = calculate_schedule(
            amount=final_amount,
            months=payload.installment_months,
        )

    payment = Payment(
        tariff_id=tariff.id,
        email=str(payload.email),
        amount=final_amount,
        discount=discount,
        method=payload.method,
        status="pending",
        installment_months=payload.installment_months,
        schedule=schedule,
        idempotency_key=idempotency_key,
    )

    db.add(payment)

    try:
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise

    return payment


def get_payment_by_idempotency_key(
    db: Session,
    idempotency_key: str,
) -> Payment | None:
    return (
        db.query(Payment)
        .filter(
            Payment.idempotency_key == idempotency_key
        )
        .first()
    )