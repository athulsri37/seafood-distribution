from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, products, orders, reports, users


def create_app() -> FastAPI:
    app = FastAPI(
        title="Seafood Distribution & Order Management API",
        description="Backend API for managing seafood inventory, orders, and distribution reporting.",
        version="1.0.0",
    )

    # Only listed origins may call the API from another site. Logins travel in the
    # Authorization header rather than cookies, so credentialed requests stay off.
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(orders.router)
    app.include_router(reports.router)
    app.include_router(users.router)

    @app.get("/api/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
