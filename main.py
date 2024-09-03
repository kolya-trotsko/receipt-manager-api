from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import SessionLocal, engine
import models, schemas, auth
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user = db.query(models.User).filter(models.User.id == payload.get("user_id")).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.login == user.login).first()
    if db_user:
        return db_user
    hashed_password = auth.hash_password(user.password)
    new_user = models.User(name=user.name, login=user.login, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.login == form_data.username).first()
    if not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect login or password")
    access_token = auth.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/receipts", response_model=schemas.ReceiptResponse, status_code=status.HTTP_201_CREATED)
def create_receipt(receipt: schemas.ReceiptCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    total = sum([p.price * p.quantity for p in receipt.products])
    rest = receipt.payment.amount - total
    new_receipt = models.Receipt(
        total=total,
        rest=rest,
        payment_type=receipt.payment.type,
        payment_amount=receipt.payment.amount,
        owner=current_user
    )
    db.add(new_receipt)
    db.commit()
    db.refresh(new_receipt)
    
    for product in receipt.products:
        prod_total = product.price * product.quantity
        db_product = models.Product(
            name=product.name,
            price=product.price,
            quantity=product.quantity,
            total=prod_total,
            receipt_id=new_receipt.id
        )
        db.add(db_product)
    db.commit()
    
    products = db.query(models.Product).filter(models.Product.receipt_id == new_receipt.id).all()
    product_responses = [
        schemas.ProductResponse(
            name=prod.name,
            price=prod.price,
            quantity=prod.quantity,
            total=prod.total
        ) for prod in products
    ]
    
    response = schemas.ReceiptResponse(
        id=new_receipt.id,
        products=product_responses,
        payment=schemas.Payment(
            type=new_receipt.payment_type,
            amount=new_receipt.payment_amount
        ),
        total=new_receipt.total,
        rest=new_receipt.rest,
        created_at=new_receipt.created_at
    )
    
    return response

@app.get("/receipts", response_model=List[schemas.ReceiptResponse])
def get_receipts(
    skip: int = 0,
    limit: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_total: Optional[float] = None,
    max_total: Optional[float] = None,
    payment_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Receipt).filter(models.Receipt.user_id == current_user.id)
    if date_from:
        query = query.filter(models.Receipt.created_at >= date_from)
    if date_to:
        query = query.filter(models.Receipt.created_at <= date_to)
    if min_total:
        query = query.filter(models.Receipt.total >= min_total)
    if max_total:
        query = query.filter(models.Receipt.total <= max_total)
    if payment_type:
        query = query.filter(models.Receipt.payment_type == payment_type)
    
    receipts = query.offset(skip).limit(limit).all()
    
    result = []
    for receipt in receipts:
        products = db.query(models.Product).filter(models.Product.receipt_id == receipt.id).all()
        product_responses = [
            schemas.ProductResponse(
                name=product.name,
                price=product.price,
                quantity=product.quantity,
                total=product.total
            ) for product in products
        ]
        
        response = schemas.ReceiptResponse(
            id=receipt.id,
            products=product_responses,
            payment=schemas.Payment(
                type=receipt.payment_type,
                amount=receipt.payment_amount
            ),
            total=receipt.total,
            rest=receipt.rest,
            created_at=receipt.created_at
        )
        result.append(response)
    
    return result

@app.get("/receipts/{receipt_id}", response_model=schemas.ReceiptResponse)
def get_receipt(receipt_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    receipt = db.query(models.Receipt).filter(models.Receipt.id == receipt_id, models.Receipt.user_id == current_user.id).first()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    
    products = db.query(models.Product).filter(models.Product.receipt_id == receipt.id).all()
    product_responses = [
        schemas.ProductResponse(
            name=product.name,
            price=product.price,
            quantity=product.quantity,
            total=product.total
        ) for product in products
    ]
    
    response = schemas.ReceiptResponse(
        id=receipt.id,
        products=product_responses,
        payment=schemas.Payment(
            type=receipt.payment_type,
            amount=receipt.payment_amount
        ),
        total=receipt.total,
        rest=receipt.rest,
        created_at=receipt.created_at
    )
    
    return response

@app.get("/public/receipts/{receipt_id}")
def public_receipt(receipt_id: int, line_length: int = 40, db: Session = Depends(get_db)):
    receipt = db.query(models.Receipt).filter(models.Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    
    products = db.query(models.Product).filter(models.Product.receipt_id == receipt_id).all()
    
    lines = []
    lines.append("ФОП Джонсонюк Борис")
    lines.append("="*30)
    for product in products:
        lines.append(f"{product.quantity} x {product.name[:10]:10} {product.total:.2f}")
    lines.append("-"*30)
    lines.append(f"СУМА\t{receipt.total:.2f}")
    lines.append(f"{receipt.payment_type.capitalize()}\t{receipt.payment_amount:.2f}")
    lines.append(f"Решта\t{receipt.rest:.2f}")
    lines.append("="*30)
    lines.append(receipt.created_at.strftime("%d.%m.%Y %H:%M"))
    lines.append("Дякуємо за покупку!")
    
    receipt_text = "\n".join(lines)
    receipt_text = "\n".join([line[:line_length] for line in receipt_text.split("\n")])
    
    return {"receipt": receipt_text}
