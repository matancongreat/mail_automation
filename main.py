from fastapi import FastAPI
from fastapi.requests import Request
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World!"}

@app.post("/publish")
async def read_root(request: Request):
    print(request.headers)
    print(await request.body())
    return 200

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)