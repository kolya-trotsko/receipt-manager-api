from pydantic import BaseModel
from typing import List
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    price: float
    quantity: float

class Payment(BaseModel):
    type: str
    amount: float

class ReceiptCreate(BaseModel):
    products: List[ProductCreate]
    payment: Payment

class ProductResponse(BaseModel):
    name: str
    price: float
    quantity: float
    total: float

    class ConfigDict:
        from_attributes = True

class ReceiptResponse(BaseModel):
    id: int
    products: List[ProductResponse]
    payment: Payment
    total: float
    rest: float
    created_at: datetime

    class ConfigDict:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    login: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    login: str

    class ConfigDict:
        from_attributes = True
