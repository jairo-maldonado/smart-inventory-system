import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Smart Inventory System API",
    description="Backend service for tracking technology inventory and stock thresholds.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_config = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE")
}

class ProductCreate(BaseModel):
    name: str
    sku: str
    price: float
    stock: int = 0
    min_stock: int = 5

class ProductUpdate(BaseModel):
    name: str
    price: float
    stock: int
    min_stock: int

class StockAdjustment(BaseModel):
    quantity: int

@app.get("/db-check")
def db_check():
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DATABASE();")
                db_name = cursor.fetchone()[0]
                return {
                    "database_status": "connected",
                    "message": f"Successfully connected to {db_name} database on port 3306."
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.post("/products", status_code=201)
def create_product(product: ProductCreate):
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO products (name, sku, price, stock, min_stock)
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (product.name, product.sku, product.price, product.stock, product.min_stock)
                cursor.execute(query, values)
                conn.commit()
                product_id = cursor.lastrowid
                return {
                    "status": "success",
                    "message": "Product registered successfully in database",
                    "data": {"id": product_id, "name": product.name, "sku": product.sku}
                }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Database Error: {err.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/products")
def get_products():
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id, name, sku, price, stock, min_stock FROM products")
                products = cursor.fetchall()
                return {
                    "status": "success",
                    "count": len(products),
                    "data": products
                }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/products/{product_id}")
def get_product_by_id(product_id: int):
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = "SELECT id, name, sku, price, stock, min_stock FROM products WHERE id = %s"
                cursor.execute(query, (product_id,))
                product = cursor.fetchone()
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found")
                return {
                    "status": "success",
                    "data": product
                }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/alerts/low-stock")
def get_low_stock_alerts():
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id, name, sku, price, stock, min_stock FROM products WHERE stock <= min_stock")
                low_stock_products = cursor.fetchall()
                return {
                    "status": "success",
                    "count": len(low_stock_products),
                    "alerts_active": len(low_stock_products) > 0,
                    "data": low_stock_products
                }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                query = """
                    UPDATE products 
                    SET name = %s, price = %s, stock = %s, min_stock = %s 
                    WHERE id = %s
                """
                values = (product.name, product.price, product.stock, product.min_stock, product_id)
                cursor.execute(query, values)
                conn.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Product not found")
                return {
                    "status": "success",
                    "message": "Product updated successfully in database"
                }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Database Error: {err.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.patch("/products/{product_id}/stock")
def adjust_stock(product_id: int, adjustment: StockAdjustment):
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                query = "UPDATE products SET stock = stock + %s WHERE id = %s"
                cursor.execute(query, (adjustment.quantity, product_id))
                conn.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Product not found")
                return {
                    "status": "success",
                    "message": "Stock adjusted successfully"
                }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Database Error: {err.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    try:
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                query = "DELETE FROM products WHERE id = %s"
                cursor.execute(query, (product_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Product not found")
                return {
                    "status": "success",
                    "message": "Product deleted successfully from database"
                }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Database Error: {err.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")