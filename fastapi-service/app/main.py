from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from .database import Base, engine, get_db

# Схема для создания и обновления продукта. 
class ProductSchema(BaseModel):
    name: str
    description: str
    price: float
    stock: int

# Схема для ответа, чтобы FastAPI мог корректно сериализовать объект SQLAlchemy
class ProductResponse(ProductSchema):
    id: int

    class Config:
        orm_mode = True 


# Создание таблиц в БД (если их нет)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Product API")

# модель для таблицы 'products'
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    price = Column(Float)
    stock = Column(Integer)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Product API"}

#  C.R.U.D. Эндпоинты 
# Получение списка всех продуктов
@app.get("/products/", response_model=list[ProductResponse])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    READ ALL: Получает список всех товаров с пагинацией.
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

# CREATE: Создание нового продукта
@app.post("/products/", response_model=ProductResponse)
def create_product(product: ProductSchema, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# READ: Получение продукта по ID
@app.get("/products/{product_id}", response_model=ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# UPDATE: Обновление существующего продукта
@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_data: ProductSchema, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Обновляем поля
    for key, value in product_data.dict().items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    return db_product

# DELETE: Удаление продукта
@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db.delete(db_product)
    db.commit()
    return {"message": f"Product with id {product_id} was deleted successfully."}