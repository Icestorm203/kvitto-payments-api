from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    model_validator,
)


class TariffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: int


class PaymentCreate(BaseModel):
    tariff_id: int
    email: EmailStr
    method: Literal["card", "sbp", "installment"]
    installment_months: Literal[3, 6, 12] | None = None
    promo_code: str | None = None

    @model_validator(mode="after")
    def validate_installment(self):
        if self.method == "installment":
            if self.installment_months is None:
                raise ValueError(
                    "installment_months is required "
                    "for installment payment"
                )

        elif self.installment_months is not None:
            raise ValueError(
                "installment_months is allowed only "
                "for installment payment"
            )

        return self


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    tariff_id: int
    amount: int
    discount: int
    method: str
    installment_months: int | None
    schedule: list[int] | None
    email: str
    created_at: datetime


class BankWebhook(BaseModel):
    payment_id: int

    status: Literal[
        "pending",
        "succeeded",
        "failed",
        "refunded",
    ]