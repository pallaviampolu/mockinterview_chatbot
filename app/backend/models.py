
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from sqlalchemy.orm import relationship

from database import Base


# ============================================================
# User
# ============================================================

class User(Base):

    __tablename__ = "users"

    user_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    role = Column(String)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    cvs = relationship(
        "CV",
        back_populates="user"
    )

    sessions = relationship(
        "InterviewSession",
        back_populates="user"
    )


# ============================================================
# CV
# ============================================================

class CV(Base):

    __tablename__ = "cvs"

    cv_id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id")
    )

    cv_text = Column(Text)

    skills = Column(Text)

    experience = Column(Text)

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="cvs"
    )


# ============================================================
# Interview Session
# ============================================================

class InterviewSession(Base):

    __tablename__ = "interview_sessions"

    session_id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id")
    )

    job_role = Column(String)

    interview_type = Column(String)

    provider = Column(String)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="sessions"
    )

    questions = relationship(
        "Question",
        back_populates="session"
    )


# ============================================================
# Question
# ============================================================

class Question(Base):

    __tablename__ = "questions"

    question_id = Column(
        Integer,
        primary_key=True
    )

    session_id = Column(
        Integer,
        ForeignKey(
            "interview_sessions.session_id"
        )
    )

    question_text = Column(Text)

    question_type = Column(String)

    session = relationship(
        "InterviewSession",
        back_populates="questions"
    )

    responses = relationship(
        "Response",
        back_populates="question"
    )


# ============================================================
# Response
# ============================================================

class Response(Base):

    __tablename__ = "responses"

    response_id = Column(
        Integer,
        primary_key=True
    )

    # One question = one candidate response
    question_id = Column(
        Integer,
        ForeignKey("questions.question_id"),
        unique=True,
        nullable=False
    )

    answer_text = Column(
        Text,
        nullable=False
    )

    question = relationship(
        "Question",
        back_populates="responses"
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="response",
        uselist=False
    )


# ============================================================
# Evaluation
# ============================================================

class Evaluation(Base):

    __tablename__ = "evaluations"

    evaluation_id = Column(
        Integer,
        primary_key=True
    )

    # One response = one evaluation
    response_id = Column(
        Integer,
        ForeignKey("responses.response_id"),
        unique=True,
        nullable=False
    )

    score = Column(Integer)

    feedback = Column(Text)

    rubric = Column(Text)

    response = relationship(
        "Response",
        back_populates="evaluation"
    )