# routers/interview.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db

from services.question_generator import generate_interview_questions
from services.rubric_evaluator import evaluate_response

from services.interview_service import (
    create_user,
    create_interview_session,
    save_questions,
    save_response,
    save_evaluation,
    calculate_session_score,
    get_interview_session,
)


router = APIRouter(
    prefix="/interview",
    tags=["Interview"],
)


# ============================================================
# Request Models
# ============================================================

class QuestionRequest(BaseModel):
    cv_text: str
    job_role: str
    provider: str = "ollama"
    interview_type: str = "personalised"


class EvaluationRequest(BaseModel):
    session_id: int
    question_id: int
    question: str
    answer: str
    cv_text: str = ""
    provider: str = "ollama"


# ============================================================
# Generate First 5 Questions
# ============================================================

@router.post("/questions")
def create_questions(
    request: QuestionRequest,
    db: Session = Depends(get_db),
):

    try:
        # ----------------------------------------------------
        # 1. Automatically create a new user
        # ----------------------------------------------------

        user = create_user(
            db=db,
            role="candidate",
        )

        # ----------------------------------------------------
        # 2. Create interview session
        # ----------------------------------------------------

        interview_session = create_interview_session(
            db=db,
            user_id=user.user_id,
            job_role=request.job_role,
            provider=request.provider,
            interview_type=request.interview_type,
        )

        # ----------------------------------------------------
        # 3. Generate exactly 5 questions
        # ----------------------------------------------------

        question_list = generate_interview_questions(
            cv_text=request.cv_text,
            job_role=request.job_role,
            provider=request.provider,
            number_of_questions=5,
        )

        if not question_list:
            raise RuntimeError(
                "No interview questions were generated."
            )

        if len(question_list) != 5:
            raise RuntimeError(
                f"Expected 5 questions but received "
                f"{len(question_list)}."
            )

        # ----------------------------------------------------
        # 4. Save questions in PostgreSQL
        # ----------------------------------------------------

        saved_questions = save_questions(
            db=db,
            session_id=interview_session.session_id,
            questions=question_list,
            question_type=request.interview_type,
        )

        # ----------------------------------------------------
        # 5. Return result
        # ----------------------------------------------------

        return {
            "user_id": user.user_id,
            "session_id": interview_session.session_id,
            "job_role": request.job_role,
            "provider": request.provider,
            "interview_type": request.interview_type,
            "questions": [
                {
                    "question_id": question.question_id,
                    "question_text": question.question_text,
                }
                for question in saved_questions
            ],
        }

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# Generate 5 More Questions in Existing Session
# ============================================================

@router.post("/{session_id}/more-questions")
def generate_more_questions(
    session_id: int,
    request: QuestionRequest,
    db: Session = Depends(get_db),
):

    try:
        # ----------------------------------------------------
        # 1. Check that interview session exists
        # ----------------------------------------------------

        interview_session = get_interview_session(
            db=db,
            session_id=session_id,
        )

        if interview_session is None:
            raise HTTPException(
                status_code=404,
                detail="Interview session not found."
            )

        # ----------------------------------------------------
        # 2. Generate another 5 questions
        # ----------------------------------------------------

        question_list = generate_interview_questions(
            cv_text=request.cv_text,
            job_role=request.job_role,
            provider=request.provider,
            number_of_questions=5,
        )

        if not question_list:
            raise RuntimeError(
                "No additional questions were generated."
            )

        if len(question_list) != 5:
            raise RuntimeError(
                f"Expected 5 questions but received "
                f"{len(question_list)}."
            )

        # ----------------------------------------------------
        # 3. Save questions under SAME interview session
        # ----------------------------------------------------

        saved_questions = save_questions(
            db=db,
            session_id=session_id,
            questions=question_list,
            question_type=request.interview_type,
        )

        # ----------------------------------------------------
        # 4. Return new questions
        # ----------------------------------------------------

        return {
            "user_id": interview_session.user_id,
            "session_id": session_id,
            "job_role": interview_session.job_role,
            "provider": interview_session.provider,
            "interview_type": interview_session.interview_type,
            "questions": [
                {
                    "question_id": question.question_id,
                    "question_text": question.question_text,
                }
                for question in saved_questions
            ],
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# Evaluate Candidate Answer
# ============================================================

@router.post("/evaluate")
def evaluate_answer(
    request: EvaluationRequest,
    db: Session = Depends(get_db),
):

    try:
        # ----------------------------------------------------
        # 1. Check interview session exists
        # ----------------------------------------------------

        interview_session = get_interview_session(
            db=db,
            session_id=request.session_id,
        )

        if interview_session is None:
            raise HTTPException(
                status_code=404,
                detail="Interview session not found."
            )

        # ----------------------------------------------------
        # 2. Save candidate response
        # ----------------------------------------------------

        saved_response = save_response(
            db=db,
            question_id=request.question_id,
            answer_text=request.answer,
        )

        # ----------------------------------------------------
        # 3. Evaluate answer using rubric
        # ----------------------------------------------------

        evaluation_result = evaluate_response(
            question=request.question,
            candidate_answer=request.answer,
            cv_text=request.cv_text,
            provider=request.provider,
        )

        # ----------------------------------------------------
        # 4. Save evaluation
        # ----------------------------------------------------

        saved_evaluation = save_evaluation(
            db=db,
            response_id=saved_response.response_id,
            evaluation_data=evaluation_result,
        )

        # ----------------------------------------------------
        # 5. Return evaluation result
        # ----------------------------------------------------

        return {
            "user_id": interview_session.user_id,
            "session_id": request.session_id,
            "question_id": request.question_id,
            "response_id": saved_response.response_id,
            "evaluation_id": saved_evaluation.evaluation_id,
            "provider": request.provider,
            "question": request.question,
            "answer": request.answer,
            "evaluation": evaluation_result,
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# Get Final Interview Score
# ============================================================

@router.get("/{session_id}/score")
def get_interview_score(
    session_id: int,
    db: Session = Depends(get_db),
):

    try:
        # ----------------------------------------------------
        # Check session exists
        # ----------------------------------------------------

        interview_session = get_interview_session(
            db=db,
            session_id=session_id,
        )

        if interview_session is None:
            raise HTTPException(
                status_code=404,
                detail="Interview session not found."
            )

        # ----------------------------------------------------
        # Calculate final score
        # ----------------------------------------------------

        result = calculate_session_score(
            db=db,
            session_id=session_id,
        )

        # Add session information
        result["user_id"] = interview_session.user_id
        result["job_role"] = interview_session.job_role
        result["provider"] = interview_session.provider
        result["interview_type"] = interview_session.interview_type

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc