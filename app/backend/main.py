from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from routers.cv import router as cv_router
from routers.interview import router as interview_router
from routers.evaluation import router as evaluation_router

app = FastAPI(
    title="CV-Aware Interview Preparation Chatbot API",
    description="Backend API for generating CV-based interview questions and rubric-based evaluation.",
    version="1.0.0"
)

# Root endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to the CV-Aware Interview Preparation Chatbot API"
    }

# Register API routers
app.include_router(
    cv_router,
    prefix="/cv",
    tags=["CV"]
)

app.include_router(
    interview_router,
    prefix="/interview",
    tags=["Interview"]
)

app.include_router(
    evaluation_router,
    prefix="/evaluation",
    tags=["Evaluation"]
)
