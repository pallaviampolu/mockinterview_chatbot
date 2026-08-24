# services/interview_service.py

import json

from sqlalchemy.orm import Session

from models import (
    InterviewSession,
    Question,
    Response,
    Evaluation,
)


# ============================================================
# Create Interview Session
# ============================================================

def create_interview_session(
    db: Session,
    user_id: int,
    job_role: str,
    provider: str,
    interview_type: str = "personalised",
) -> InterviewSession:

    interview_session = InterviewSession(
        user_id=user_id,
        job_role=job_role,
        interview_type=interview_type,
        provider=provider,
    )

    db.add(interview_session)
    db.commit()
    db.refresh(interview_session)

    return interview_session


# ============================================================
# Save Single Question
# ============================================================

def save_question(
    db: Session,
    session_id: int,
    question_text: str,
    question_type: str = "personalised",
) -> Question:

    question = Question(
        session_id=session_id,
        question_text=question_text,
        question_type=question_type,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


# ============================================================
# Save Multiple Questions
# ============================================================

def save_questions(
    db: Session,
    session_id: int,
    questions: list[str],
    question_type: str = "personalised",
) -> list[Question]:

    saved_questions = []

    for question_text in questions:

        question = Question(
            session_id=session_id,
            question_text=question_text,
            question_type=question_type,
        )

        db.add(question)
        saved_questions.append(question)

    db.commit()

    for question in saved_questions:
        db.refresh(question)

    return saved_questions


# ============================================================
# Save Candidate Response
# ============================================================

def save_response(
    db: Session,
    question_id: int,
    answer_text: str,
) -> Response:

    response = Response(
        question_id=question_id,
        answer_text=answer_text,
    )

    db.add(response)
    db.commit()
    db.refresh(response)

    return response


# ============================================================
# Save Evaluation
# ============================================================

def save_evaluation(
    db: Session,
    response_id: int,
    evaluation_data: dict,
) -> Evaluation:
    """
    Save the complete rubric result.

    The current Evaluation model contains:
    - score
    - feedback
    - rubric

    Therefore the 5 criterion scores are stored
    as JSON inside the rubric column.
    """

    total_score = evaluation_data.get(
        "total_score",
        0,
    )

    overall_feedback = evaluation_data.get(
        "overall_feedback",
        "",
    )

    rubric_data = {
        "relevance": evaluation_data.get(
            "relevance",
            {},
        ),
        "technical_accuracy": evaluation_data.get(
            "technical_accuracy",
            {},
        ),
        "clarity_communication": evaluation_data.get(
            "clarity_communication",
            {},
        ),
        "cv_evidence": evaluation_data.get(
            "cv_evidence",
            {},
        ),
        "depth_completeness": evaluation_data.get(
            "depth_completeness",
            {},
        ),
    }

    evaluation = Evaluation(
        response_id=response_id,
        score=total_score,
        feedback=overall_feedback,
        rubric=json.dumps(rubric_data),
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return evaluation


# ============================================================
# Get Interview Session
# ============================================================

def get_interview_session(
    db: Session,
    session_id: int,
) -> InterviewSession | None:

    return (
        db.query(InterviewSession)
        .filter(
            InterviewSession.session_id == session_id
        )
        .first()
    )


# ============================================================
# Get Questions for Session
# ============================================================

def get_session_questions(
    db: Session,
    session_id: int,
) -> list[Question]:

    return (
        db.query(Question)
        .filter(
            Question.session_id == session_id
        )
        .all()
    )


# ============================================================
# Get Response by Question
# ============================================================

def get_response_by_question(
    db: Session,
    question_id: int,
) -> Response | None:

    return (
        db.query(Response)
        .filter(
            Response.question_id == question_id
        )
        .first()
    )


# ============================================================
# Get Evaluation by Response
# ============================================================

def get_evaluation_by_response(
    db: Session,
    response_id: int,
) -> Evaluation | None:

    return (
        db.query(Evaluation)
        .filter(
            Evaluation.response_id == response_id
        )
        .first()
    )


# ============================================================
# Calculate Interview Score
# ============================================================

def calculate_session_score(
    db: Session,
    session_id: int,
) -> dict:

    questions = get_session_questions(
        db=db,
        session_id=session_id,
    )

    total_score = 0
    evaluated_answers = 0

    for question in questions:

        response = get_response_by_question(
            db=db,
            question_id=question.question_id,
        )

        if response is None:
            continue

        evaluation = get_evaluation_by_response(
            db=db,
            response_id=response.response_id,
        )

        if evaluation is None:
            continue

        total_score += evaluation.score
        evaluated_answers += 1

    if evaluated_answers == 0:

        return {
            "session_id": session_id,
            "evaluated_answers": 0,
            "total_score": 0,
            "maximum_score": 0,
            "average_score": 0,
            "percentage": 0,
        }

    maximum_score = evaluated_answers * 25

    average_score = (
        total_score / evaluated_answers
    )

    percentage = (
        total_score / maximum_score
    ) * 100

    return {
        "session_id": session_id,
        "evaluated_answers": evaluated_answers,
        "total_score": total_score,
        "maximum_score": maximum_score,
        "average_score": round(
            average_score,
            2,
        ),
        "percentage": round(
            percentage,
            2,
        ),
    }