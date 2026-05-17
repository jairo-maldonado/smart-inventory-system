from fastapi import FastAPI

app = FastAPI(
    title="Smart Inventory System API",
    description="Backend service for tracking and managing tech accessory stock.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Smart Inventory System API",
        "environment": "development"
    }