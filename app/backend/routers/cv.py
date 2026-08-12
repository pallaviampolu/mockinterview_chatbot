from fastapi import APIRouter, File, HTTPException, UploadFile, status

from services.cv_parser import CVParserError, parse_cv_bytes


router = APIRouter()


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("/")
def cv_router_status() -> dict[str, str]:
    return {
        "message": "CV parser route is working."
    }


@router.post("/parse")
async def parse_cv(
    file: UploadFile = File(...),
) -> dict:
    """
    Upload and parse a CV.

    Supported formats:
    - PDF
    - DOCX
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must have a filename.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, DOCX and files are supported.",
        )

    try:
        file_bytes = await file.read()

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="The uploaded file must be smaller than 10 MB.",
            )

        parsed_cv = parse_cv_bytes(
            file_bytes=file_bytes,
            filename=file.filename,
        )

        return {
            "message": "CV parsed successfully.",
            "data": parsed_cv,
        }

    except CVParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected CV parsing error: {exc}",
        ) from exc

    finally:
        await file.close()