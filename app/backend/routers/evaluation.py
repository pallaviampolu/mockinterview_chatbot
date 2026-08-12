from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def evaluation():
    return {"message": "Evaluation router is working"}