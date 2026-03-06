from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, catalogue, auction, payment, notification

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StackOverbid API",
    description="API for the StackOverbid auction e-commerce system",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(catalogue.router)
app.include_router(auction.router)
app.include_router(payment.router)
app.include_router(notification.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to StackOverbid API"}
