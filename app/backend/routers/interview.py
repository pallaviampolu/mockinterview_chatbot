# routers/interview.py

import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db

from services.question_generator import (
    generate_interview_questions,
)

from services.rubric_evaluator import (
    evaluate_response,
)

from services.interview_service import (
    create_user,
    save_cv,
    create_interview_session,
    get_interview_session,
    save_questions,
    save_response,
    save_evaluation,
    get_response_by_question,
    get_evaluation_by_response,
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
        # 1. Automatically create user
        # ----------------------------------------------------

        user = create_user(
            db=db,
            role="candidate",
        )


        # ----------------------------------------------------
        # 2. Save CV
        # ----------------------------------------------------

        saved_cv = save_cv(
            db=db,
            user_id=user.user_id,
            cv_text=request.cv_text,
        )


        # ----------------------------------------------------
        # 3. Create interview session
        # ----------------------------------------------------

        interview_session = (
            create_interview_session(
                db=db,
                user_id=user.user_id,
                job_role=request.job_role,
                provider=request.provider,
                interview_type=(
                    request.interview_type
                ),
            )
        )


        # ----------------------------------------------------
        # 4. Generate 5 questions
        # ----------------------------------------------------

        question_list = (
            generate_interview_questions(
                cv_text=request.cv_text,
                job_role=request.job_role,
                provider=request.provider,
                number_of_questions=5,
            )
        )


        if len(question_list) != 5:

            raise RuntimeError(
                f"Expected 5 interview questions "
                f"but received {len(question_list)}."
            )


        # ----------------------------------------------------
        # 5. Save questions
        # ----------------------------------------------------

        saved_questions = save_questions(
            db=db,
            session_id=(
                interview_session.session_id
            ),
            questions=question_list,
            question_type=(
                request.interview_type
            ),
        )


        # ----------------------------------------------------
        # 6. Return result
        # ----------------------------------------------------

        return {
            "user_id": (
                user.user_id
            ),
            "cv_id": (
                saved_cv.cv_id
            ),
            "session_id": (
                interview_session.session_id
            ),
            "job_role": (
                request.job_role
            ),
            "provider": (
                request.provider
            ),
            "interview_type": (
                request.interview_type
            ),
            "questions": [
                {
                    "question_id": (
                        question.question_id
                    ),
                    "question_text": (
                        question.question_text
                    ),
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
# Generate 5 More Questions
# ============================================================

@router.post(
    "/{session_id}/more-questions"
)
def generate_more_questions(
    session_id: int,
    request: QuestionRequest,
    db: Session = Depends(get_db),
):

    try:

        interview_session = (
            get_interview_session(
                db=db,
                session_id=session_id,
            )
        )


        if interview_session is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Interview session not found."
                ),
            )


        question_list = (
            generate_interview_questions(
                cv_text=request.cv_text,
                job_role=(
                    interview_session.job_role
                ),
                provider=(
                    interview_session.provider
                ),
                number_of_questions=5,
            )
        )


        if len(question_list) != 5:

            raise RuntimeError(
                f"Expected 5 interview questions "
                f"but received {len(question_list)}."
            )


        saved_questions = save_questions(
            db=db,
            session_id=session_id,
            questions=question_list,
            question_type=(
                interview_session.interview_type
            ),
        )


        return {
            "user_id": (
                interview_session.user_id
            ),
            "session_id": (
                session_id
            ),
            "job_role": (
                interview_session.job_role
            ),
            "provider": (
                interview_session.provider
            ),
            "questions": [
                {
                    "question_id": (
                        question.question_id
                    ),
                    "question_text": (
                        question.question_text
                    ),
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
        # 1. Check session
        # ----------------------------------------------------

        interview_session = (
            get_interview_session(
                db=db,
                session_id=request.session_id,
            )
        )


        if interview_session is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Interview session not found."
                ),
            )


        # ----------------------------------------------------
        # 2. Check if response already exists
        # ----------------------------------------------------

        existing_response = (
            get_response_by_question(
                db=db,
                question_id=request.question_id,
            )
        )


        # ----------------------------------------------------
        # 3. Return existing completed evaluation
        # ----------------------------------------------------

        if existing_response is not None:

            existing_evaluation = (
                get_evaluation_by_response(
                    db=db,
                    response_id=(
                        existing_response.response_id
                    ),
                )
            )


            if existing_evaluation is not None:

                rubric_data = json.loads(
                    existing_evaluation.rubric
                )


                evaluation_result = {
                    **rubric_data,

                    "total_score": (
                        existing_evaluation.score
                    ),

                    "overall_feedback": (
                        existing_evaluation.feedback
                        or ""
                    ),
                }


                return {
                    "user_id": (
                        interview_session.user_id
                    ),

                    "session_id": (
                        request.session_id
                    ),

                    "question_id": (
                        request.question_id
                    ),

                    "response_id": (
                        existing_response.response_id
                    ),

                    "evaluation_id": (
                        existing_evaluation.evaluation_id
                    ),

                    "provider": (
                        interview_session.provider
                    ),

                    "question": (
                        request.question
                    ),

                    "answer": (
                        existing_response.answer_text
                    ),

                    "evaluation": (
                        evaluation_result
                    ),
                }


        # ----------------------------------------------------
        # 4. Evaluate answer FIRST
        # ----------------------------------------------------

        evaluation_result = (
            evaluate_response(
                question=request.question,
                candidate_answer=(
                    request.answer
                ),
                cv_text=request.cv_text,
                provider=(
                    interview_session.provider
                ),
            )
        )


        # ----------------------------------------------------
        # 5. Save response
        # ----------------------------------------------------

        saved_response = save_response(
            db=db,
            question_id=request.question_id,
            answer_text=request.answer,
        )


        # ----------------------------------------------------
        # 6. Save evaluation
        # ----------------------------------------------------

        saved_evaluation = (
            save_evaluation(
                db=db,
                response_id=(
                    saved_response.response_id
                ),
                evaluation_data=(
                    evaluation_result
                ),
            )
        )


        # ----------------------------------------------------
        # 7. Return complete result
        # ----------------------------------------------------

        return {
            "user_id": (
                interview_session.user_id
            ),

            "session_id": (
                request.session_id
            ),

            "question_id": (
                request.question_id
            ),

            "response_id": (
                saved_response.response_id
            ),

            "evaluation_id": (
                saved_evaluation.evaluation_id
            ),

            "provider": (
                interview_session.provider
            ),

            "question": (
                request.question
            ),

            "answer": (
                request.answer
            ),

            "evaluation": (
                evaluation_result
            ),
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
# Final Interview Score
# ============================================================

@router.get(
    "/{session_id}/score"
)
def get_interview_score(
    session_id: int,
    db: Session = Depends(get_db),
):

    try:

        interview_session = (
            get_interview_session(
                db=db,
                session_id=session_id,
            )
        )


        if interview_session is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Interview session not found."
                ),
            )


        result = (
            calculate_session_score(
                db=db,
                session_id=session_id,
            )
        )


        result["user_id"] = (
            interview_session.user_id
        )

        result["job_role"] = (
            interview_session.job_role
        )

        result["provider"] = (
            interview_session.provider
        )

        result["interview_type"] = (
            interview_session.interview_type
        )


        return result


    except HTTPException:
        raise


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc