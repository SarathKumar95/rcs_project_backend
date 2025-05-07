from fastapi import FastAPI
from app.routes import user_routes
from app.routes import auth_routes

app = FastAPI()


# Include your user routes (register/login)
app.include_router(user_routes.router, prefix="/users", tags=["users"])
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])