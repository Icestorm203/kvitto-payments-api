TARIFFS = [
    {
        "title": "basic",
        "price": 990000
    },
    {
        "title": "standard",
        "price": 1990000
    },
    {
        "title": "premium",
        "price": 2990000
    }
]

VALID_METHODS = (
    "card",
    "sbp",
    "installment"
)

VALID_STATUSES = (
    "pending",
    "succeeded",
    "failed",
    "refunded"
)

PROMO_CODE = "KVITTO10"

PROMO_DISCOUNT_PERCENT = 10

VALID_INSTALLMENT_MONTHS = (
    3,
    6,
    12,
)

VALID_TRANSITIONS = {
    "pending": {
        "succeeded",
        "failed",
    },
    "succeeded": {
        "refunded",
    },
    "failed": set(),
    "refunded": set(),
}