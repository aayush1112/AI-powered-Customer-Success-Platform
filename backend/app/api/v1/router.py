from fastapi import APIRouter

from app.api.v1.endpoints import auth, customers, dashboard, health, insights, interactions, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(interactions.router)
api_router.include_router(insights.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
