# routers/interview.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db

from services.question_generator import generate_interview_questions
from services.rubric_evaluator import evaluate_response

from services.interview_service import (
    create_interview_session,
    save_questions,
    save_response,
    save_evaluation,
    calculate_session_score,
)


router = APIRouter(
    prefix="/interview",
    tags=["Interview"],
)


# ============================================================
# Request Models
# ============================================================

class QuestionRequest(BaseModel):
    user_id: int
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
# Generate Questions + Create Interview Session
# ============================================================

@router.post("/questions")
def create_questions(
    request: QuestionRequest,
    db: Session = Depends(get_db),
):

    try:
        # 1. Create interview session
        interview_session = create_interview_session(
            db=db,
            user_id=request.user_id,
            job_role=request.job_role,
            provider=request.provider,
            interview_type=request.interview_type,
        )

        # 2. Generate questions
        generated_questions = generate_interview_questions(
            cv_text=request.cv_text,
            job_role=request.job_role,
            provider=request.provider,
            number_of_questions=5,
        )

        # 3. Convert the LLM string output into a list
        question_list = [
            line.strip()
            for line in generated_questions.splitlines()
            if line.strip()
        ]

        # 4. Save questions in PostgreSQL
        saved_questions = save_questions(
            db=db,
            session_id=interview_session.session_id,
            questions=question_list,
            question_type=request.interview_type,
        )

        # 5. Return saved questions
        return {
            "session_id": interview_session.session_id,
            "user_id": request.user_id,
            "job_role": request.job_role,
            "interview_type": request.interview_type,
            "provider": request.provider,
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
# Evaluate Answer + Save Response + Save Evaluation
# ============================================================

@router.post("/evaluate")
def evaluate_answer(
    request: EvaluationRequest,
    db: Session = Depends(get_db),
):

    try:
        # 1. Save candidate answer
        saved_response = save_response(
            db=db,
            question_id=request.question_id,
            answer_text=request.answer,
        )

        # 2. Evaluate answer using rubric
        evaluation_result = evaluate_response(
            question=request.question,
            candidate_answer=request.answer,
            cv_text=request.cv_text,
            provider=request.provider,
        )

        # 3. Save evaluation in PostgreSQL
        saved_evaluation = save_evaluation(
            db=db,
            response_id=saved_response.response_id,
            evaluation_data=evaluation_result,
        )

        # 4. Return evaluation result
        return {
            "session_id": request.session_id,
            "question_id": request.question_id,
            "response_id": saved_response.response_id,
            "evaluation_id": saved_evaluation.evaluation_id,
            "provider": request.provider,
            "question": request.question,
            "answer": request.answer,
            "evaluation": evaluation_result,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# Get Overall Interview Score
# ============================================================

@router.get("/{session_id}/score")
def get_interview_score(
    session_id: int,
    db: Session = Depends(get_db),
):

    try:
        result = calculate_session_score(
            db=db,
            session_id=session_id,
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc