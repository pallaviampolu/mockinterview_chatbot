from services.llm_integration import generate_text


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """
You are an experienced professional interview coach.

Your task is to generate realistic and relevant interview
questions based on the candidate's CV and their target job role.

Only use information that is present in the candidate's CV.
Do not invent qualifications, skills, projects, responsibilities,
or work experience that are not supported by the CV.
"""


# ============================================================
# Generate Personalised Interview Questions
# ============================================================

def generate_interview_questions(
    cv_text: str,
    job_role: str,
    provider: str = "ollama",
    number_of_questions: int = 5,
) -> str:
    """
    Generate personalised interview questions using
    the selected LLM provider.

    Parameters:
        cv_text:
            Extracted text from the candidate's CV.

        job_role:
            Target job role selected by the candidate.

        provider:
            LLM provider to use.
            Example: "ollama" or "gemini".

        number_of_questions:
            Number of interview questions to generate.

    Returns:
        Generated interview questions as a string.
    """

    # --------------------------------------------------------
    # Validate CV text
    # --------------------------------------------------------

    if not cv_text or not cv_text.strip():
        raise ValueError(
            "CV text cannot be empty."
        )

    # --------------------------------------------------------
    # Validate job role
    # --------------------------------------------------------

    if not job_role or not job_role.strip():
        raise ValueError(
            "Target job role cannot be empty."
        )

    # --------------------------------------------------------
    # Validate number of questions
    # --------------------------------------------------------

    if number_of_questions < 1:
        raise ValueError(
            "Number of questions must be at least 1."
        )

    # --------------------------------------------------------
    # Clean input
    # --------------------------------------------------------

    cv_text = cv_text.strip()
    job_role = job_role.strip()

    # --------------------------------------------------------
    # Create Interview Prompt
    # --------------------------------------------------------

    prompt = f"""
Candidate CV:
{cv_text}

Target Job Role:
{job_role}

Generate exactly {number_of_questions} personalised
interview questions for this candidate.

Requirements:

1. Questions must be relevant to the target job role.

2. Questions should be based on information available
   in the candidate's CV.

3. Include a mixture of:
   - technical questions
   - behavioural questions
   - experience-based questions

4. Ask questions that allow the candidate to explain
   their skills, experience, projects, and achievements.

5. Do not invent information that is not present in
   the candidate's CV.

6. Keep the questions professional and suitable for
   a realistic job interview.

7. Avoid asking duplicate or very similar questions.

Return only the numbered interview questions.
"""

    # --------------------------------------------------------
    # Generate Questions
    # --------------------------------------------------------

    questions = generate_text(
        prompt=prompt,
        provider=provider,
        system_prompt=SYSTEM_PROMPT,
    )

    # --------------------------------------------------------
    # Validate LLM Response
    # --------------------------------------------------------

    if not questions or not questions.strip():
        raise RuntimeError(
            "The LLM did not generate any interview questions."
        )

    return questions.strip()