from fastapi import APIRouter

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post("")
def create_payment():
    return {
        "message": "not implemented"
    }


@router.get("/{payment_id}")
def get_payment(payment_id: int):
    return {
        "payment_id": payment_id
    }