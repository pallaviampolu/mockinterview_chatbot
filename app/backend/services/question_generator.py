# services/question_generator.py

import re

from services.llm_integration import generate_text


SYSTEM_PROMPT = """
You are an experienced professional interview coach.

Generate realistic and relevant interview questions based on
the candidate's CV and target job role.

Only use information supported by the candidate's CV.
Do not invent qualifications, skills, projects, responsibilities,
or work experience.

Do not include any introduction, explanation, heading,
closing statement, or additional commentary.

Return only the interview questions.
"""


def clean_generated_questions(
    generated_text: str,
    number_of_questions: int,
) -> list[str]:
    """
    Extract only actual numbered interview questions
    from the LLM response.
    """

    questions = []

    for line in generated_text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Match:
        # 1. Question
        # 1) Question
        # 1 - Question
        match = re.match(
            r"^\s*\d+\s*[\.\)\-:]\s*(.+)$",
            line,
        )

        if match:

            question = match.group(1).strip()

            if question:
                questions.append(question)

    # Fallback if model did not number questions correctly
    if not questions:

        for line in generated_text.splitlines():

            line = line.strip()

            # Keep only lines that actually look like questions
            if line.endswith("?"):
                questions.append(line)

    # Guarantee requested maximum
    return questions[:number_of_questions]


def generate_interview_questions(
    cv_text: str,
    job_role: str,
    provider: str = "ollama",
    number_of_questions: int = 5,
) -> list[str]:
    """
    Generate personalised interview questions.

    Returns:
        list[str]
    """

    if not cv_text or not cv_text.strip():
        raise ValueError(
            "CV text cannot be empty."
        )

    if not job_role or not job_role.strip():
        raise ValueError(
            "Target job role cannot be empty."
        )

    if number_of_questions < 1:
        raise ValueError(
            "Number of questions must be at least 1."
        )


    prompt = f"""
Candidate CV:

{cv_text.strip()}


Target Job Role:

{job_role.strip()}


Generate exactly {number_of_questions} personalised
interview questions.


Requirements:

1. Every question must be relevant to the target job role.

2. Questions must be supported by information contained
   in the candidate's CV.

3. Include a balanced mixture of:
   - technical questions
   - behavioural questions
   - experience-based questions

4. Do not invent experience or skills that are not
   present in the CV.

5. Avoid duplicate or very similar questions.

6. Each question must end with a question mark.

7. Return exactly {number_of_questions} questions.

8. Number the questions from 1 to {number_of_questions}.

IMPORTANT:

Do NOT write an introduction such as:
"Here are five interview questions..."

Do NOT include a title.

Do NOT explain the questions.

Do NOT include any text before or after the numbered questions.


Required output format:

1. First interview question?
2. Second interview question?
3. Third interview question?
4. Fourth interview question?
5. Fifth interview question?
"""


    generated_text = generate_text(
        prompt=prompt,
        provider=provider,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.5,
    )


    questions = clean_generated_questions(
        generated_text=generated_text,
        number_of_questions=number_of_questions,
    )


    if len(questions) != number_of_questions:

        raise RuntimeError(
            f"Expected {number_of_questions} interview questions "
            f"but received {len(questions)}."
        )


    return questions