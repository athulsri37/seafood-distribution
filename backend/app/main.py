from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.routers import auth, products, orders, reports, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Seafood Distribution & Order Management API",
    description="Backend API for managing seafood inventory, orders, and distribution reporting.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(reports.router)
app.include_router(users.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
