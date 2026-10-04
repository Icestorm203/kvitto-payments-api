from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base


class Tariff(Base):
    __tablename__ = "tariffs"

    id = Column(Integer, primary_key=True)

    title = Column(
        String,
        unique=True,
        nullable=False
    )

    price = Column(
        Integer,
        nullable=False
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)

    tariff_id = Column(Integer)

    email = Column(String)

    amount = Column(Integer)

    discount = Column(Integer)

    status = Column(String)

    method = Column(String)

    installment_months = Column(Integer)

    schedule = Column(String)

    idempotency_key = Column(
        String,
        unique=True,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )