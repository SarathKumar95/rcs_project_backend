from fastapi import FastAPI
from app.routes import user_routes

app = FastAPI()


# Include your user routes (register/login)
app.include_router(user_routes.router, prefix="/auth", tags=["authentication"])

