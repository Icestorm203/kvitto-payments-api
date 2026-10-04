from pydantic import BaseModel


class TariffResponse(BaseModel):
    id: int
    title: str
    price: int

    class Config:
        from_attributes = True