from fastapi import FastAPI
from routers.test import router as test
import uvicorn

app = FastAPI()

from routers.test import router as test


app.include_router(test)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

