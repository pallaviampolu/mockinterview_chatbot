# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.cv import router as cv_router
from routers.interview import router as interview_router


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="CV-Aware Interview Preparation Chatbot API",
    description=(
        "Backend API for CV parsing, personalised interview "
        "question generation, rubric-based evaluation, "
        "and interview score calculation."
    ),
    version="1.0.0",
)


# ============================================================
# CORS Configuration
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=["*"],
)


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": (
            "CV-Aware Interview Preparation "
            "Chatbot API is running."
        )
    }


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy"
    }


# ============================================================
# Routers
# ============================================================

app.include_router(
    cv_router,
    prefix="/cv",
    tags=["CV Parser"],
)

app.include_router(
    interview_router,
)