from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    login = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    receipts = relationship("Receipt", back_populates="owner")

class Receipt(Base):
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    total = Column(Float, nullable=False)
    rest = Column(Float, nullable=False)
    payment_type = Column(String, nullable=False)
    payment_amount = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="receipts")
    products = relationship("Product", back_populates="receipt")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    receipt_id = Column(Integer, ForeignKey("receipts.id"))
    
    receipt = relationship("Receipt", back_populates="products")
