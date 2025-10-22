from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import Session
from .database import Base, engine, get_db

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Product API")

# SQLAlchemy model for the 'products' table
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    price = Column(Float)
    stock = Column(Integer)

@app.get("/products/{product_id}")
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    Fetches a product by its ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/")
def read_root():
    return {"message": "Welcome to the Product API"}