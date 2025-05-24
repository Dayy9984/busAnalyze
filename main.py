# main.py
from fastapi import FastAPI
from routers.test import router as test_router # Renamed to avoid conflict if 'test' is a common variable name
import uvicorn

app = FastAPI()

app.include_router(test_router) # You can add a prefix here, e.g., app.include_router(test_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
