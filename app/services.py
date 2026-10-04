from sqlalchemy.orm import Session

from app.constants import TARIFFS
from app.models import Tariff


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