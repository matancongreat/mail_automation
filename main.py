from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from config.settings import settings
from routes.gmail.router import router as connect_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

app.include_router(connect_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
