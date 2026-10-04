from fastapi import APIRouter

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)


@router.post("/bank")
def bank_webhook():
    return {
        "result": "ok"
    }