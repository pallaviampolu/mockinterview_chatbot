# services/rubric_evaluator.py

import json

from services.llm_integration import generate_text


SYSTEM_PROMPT = """
You are an interview evaluator.

Evaluate the candidate's answer using only the rubric provided.

Be consistent, objective, and concise.
Do not invent information.
Do not reward content that is not supported by the candidate's answer.

Return valid JSON only.
"""


RUBRIC = {
    "relevance": {
        "max_score": 5,
        "description": (
            "How directly the answer addresses the interview question."
        ),
    },
    "technical_accuracy": {
        "max_score": 5,
        "description": (
            "How accurate the technical or subject-specific content is."
        ),
    },
    "clarity_communication": {
        "max_score": 5,
        "description": (
            "How clearly, logically, and professionally the answer is communicated."
        ),
    },
    "cv_evidence": {
        "max_score": 5,
        "description": (
            "How effectively the candidate uses relevant personal experience, "
            "projects, skills, or evidence from the CV."
        ),
    },
    "depth_completeness": {
        "max_score": 5,
        "description": (
            "How complete, detailed, and well-supported the answer is."
        ),
    },
}


# ============================================================
# Build Rubric Text
# ============================================================

def build_rubric_text() -> str:
    """
    Convert the rubric dictionary into readable text
    for the LLM prompt.
    """

    lines = []

    for criterion, details in RUBRIC.items():
        lines.append(
            f"{criterion}: 0-{details['max_score']} marks\n"
            f"Description: {details['description']}"
        )

    return "\n\n".join(lines)


# ============================================================
# Validate Evaluation
# ============================================================

def validate_evaluation(result: dict) -> None:
    """
    Validate the five rubric scores returned by the LLM.

    The total score is calculated automatically in Python.
    """

    criteria = [
        "relevance",
        "technical_accuracy",
        "clarity_communication",
        "cv_evidence",
        "depth_completeness",
    ]

    calculated_total = 0

    for criterion in criteria:

        if criterion not in result:
            raise RuntimeError(
                f"Missing rubric criterion: {criterion}"
            )

        criterion_data = result[criterion]

        if not isinstance(criterion_data, dict):
            raise RuntimeError(
                f"{criterion} must contain score and feedback."
            )

        score = criterion_data.get("score")

        if not isinstance(score, int):
            raise RuntimeError(
                f"Score for {criterion} must be an integer."
            )

        if score < 0 or score > 5:
            raise RuntimeError(
                f"Score for {criterion} must be between 0 and 5."
            )

        # Ensure feedback exists
        if "feedback" not in criterion_data:
            criterion_data["feedback"] = ""

        calculated_total += score

    # Python calculates the total
    result["total_score"] = calculated_total

    # Ensure overall feedback exists
    if "overall_feedback" not in result:
        result["overall_feedback"] = ""


# ============================================================
# Evaluate Candidate Response
# ============================================================

def evaluate_response(
    question: str,
    candidate_answer: str,
    cv_text: str = "",
    provider: str = "ollama",
) -> dict:
    """
    Evaluate an interview response using the 25-mark rubric.

    Returns:
        Dictionary containing:
        - 5 individual criterion scores
        - criterion feedback
        - total score out of 25
        - overall feedback
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not question or not question.strip():
        raise ValueError(
            "Interview question cannot be empty."
        )

    if not candidate_answer or not candidate_answer.strip():
        raise ValueError(
            "Candidate answer cannot be empty."
        )

    rubric_text = build_rubric_text()

    # --------------------------------------------------------
    # Build evaluation prompt
    # --------------------------------------------------------

    prompt = f"""
Interview Question:
{question.strip()}

Candidate Answer:
{candidate_answer.strip()}

Candidate CV:
{cv_text.strip() if cv_text else "Not provided"}

Rubric:
{rubric_text}

Scoring Scale:

0 = Not demonstrated
1 = Poor
2 = Limited
3 = Satisfactory
4 = Good
5 = Excellent

Instructions:

1. Evaluate the candidate's answer using all five criteria.
2. Give an integer score from 0 to 5 for each criterion.
3. Give short, specific feedback for each criterion.
4. Do not calculate the final score.
5. The application will calculate the total score automatically.
6. Do not include markdown.
7. Return valid JSON only.

Return JSON in exactly this format:

{{
    "relevance": {{
        "score": 0,
        "feedback": ""
    }},
    "technical_accuracy": {{
        "score": 0,
        "feedback": ""
    }},
    "clarity_communication": {{
        "score": 0,
        "feedback": ""
    }},
    "cv_evidence": {{
        "score": 0,
        "feedback": ""
    }},
    "depth_completeness": {{
        "score": 0,
        "feedback": ""
    }},
    "overall_feedback": ""
}}
"""

    # --------------------------------------------------------
    # Call selected LLM
    # --------------------------------------------------------

    raw_response = generate_text(
        prompt=prompt,
        provider=provider,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.0,
    )

    if not raw_response or not raw_response.strip():
        raise RuntimeError(
            "The LLM did not return an evaluation."
        )

    # --------------------------------------------------------
    # Clean possible Markdown JSON wrapper
    # --------------------------------------------------------

    cleaned_response = raw_response.strip()

    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]

    elif cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]

    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]

    cleaned_response = cleaned_response.strip()

    # --------------------------------------------------------
    # Convert JSON string into Python dictionary
    # --------------------------------------------------------

    try:
        result = json.loads(cleaned_response)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON returned by the LLM: {raw_response}"
        ) from exc

    # --------------------------------------------------------
    # Validate scores and calculate total
    # --------------------------------------------------------

    validate_evaluation(result)

    return result