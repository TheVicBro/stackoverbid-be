from dotenv import load_dotenv

load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, catalogue, auction, payment, notification

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StackOverbid API",
    description="API for the StackOverbid auction e-commerce system",
    version="1.0.0",
)

origins = [
    "http://localhost:3000",
]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalogue.router)
app.include_router(auction.router)
app.include_router(payment.router)
app.include_router(notification.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to StackOverbid API"}
