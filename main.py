import uvicorn
from fastapi import FastAPI, HTTPException
from dbmodule import dbmodule
import pandas as pd
import datetime
db = dbmodule()
app = FastAPI()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
