# main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from routers.sgg_emd import router as sgg_emd_router 
from routers.smart_bus import router as smart_bus_router 
from routers.bus_blind_spot import router as bus_blind_spot
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")

app = FastAPI()

app.include_router(sgg_emd_router)
app.include_router(smart_bus_router)
app.include_router(bus_blind_spot)
# You can add a prefix here, e.g., app.include_router(test_router, prefix="/api")

app.mount("/", StaticFiles(directory=RESOURCES_DIR, html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

    