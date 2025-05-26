# main.py
from fastapi import FastAPI
from routers.sgg_emd import router as sgg_emd_router 
from routers.smart_bus import router as smart_bus_router 
import uvicorn

app = FastAPI()

app.include_router(sgg_emd_router)
app.include_router(smart_bus_router)# You can add a prefix here, e.g., app.include_router(test_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
