from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def interview():
    return {"message": "Interview router is working"}