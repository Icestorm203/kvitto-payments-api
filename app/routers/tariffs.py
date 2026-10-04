from fastapi import APIRouter

router = APIRouter(
    prefix="/tariffs",
    tags=["Tariffs"]
)


@router.get("")
def get_tariffs():
    return []