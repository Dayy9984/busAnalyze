from fastapi import FastAPI
from fastapi.responses import FileResponse
from routers.LocationBorder import router as LocationBorderRouter 
from routers.SmartBus import router as SmartBusRouter 
from routers.BusBlindSpot import router as BusBlindSpotRouter
from routers.AutoComplete import router as AutoCompleteRouter
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")

app = FastAPI()

app.include_router(AutoCompleteRouter)
app.include_router(LocationBorderRouter)
app.include_router(SmartBusRouter)
app.include_router(BusBlindSpotRouter)


app.mount("/", StaticFiles(directory=RESOURCES_DIR, html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

    