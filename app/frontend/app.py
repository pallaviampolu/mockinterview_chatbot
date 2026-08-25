# frontend/app.py

import time

import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# ============================================================
# Configuration
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000"

QUESTION_TIME_LIMIT = 300  # 5 minutes


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="MOCK-BOT",
    page_icon="💬",
    layout="centered",
)


# ============================================================
# Header
# ============================================================

st.markdown(
    """
<div style="display: inline-block;">
    <h1 style="margin: 0; padding: 0; line-height: 1;">
        MOCK-BOT
    </h1>
    <div style="
        text-align: right;
        font-size: 13px;
        color: grey;
        margin-top: -2px;
        line-height: 1;
    ">
        an interview preparation chatbot
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

st.write(
    "Upload your CV, choose a target job role, "
    "and practise a personalised mock interview."
)


# ============================================================
# Session State
# ============================================================

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "cv_text" not in st.session_state:
    st.session_state.cv_text = ""

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "questions" not in st.session_state:
    st.session_state.questions = []

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "interview_ended" not in st.session_state:
    st.session_state.interview_ended = False

if "job_role" not in st.session_state:
    st.session_state.job_role = ""

if "provider" not in st.session_state:
    st.session_state.provider = "ollama"

if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None

if "processed_questions" not in st.session_state:
    st.session_state.processed_questions = set()


# ============================================================
# Helper Function - Submit/Evaluate Answer
# ============================================================

def submit_interview_answer(
    current_question: dict,
    answer: str,
    current_index: int,
):

    question_id = current_question["question_id"]

    # Prevent duplicate submissions
    if question_id in st.session_state.processed_questions:
        return

    submitted_answer = answer.strip()

    if not submitted_answer:
        submitted_answer = (
            "No answer was submitted within the five-minute time limit."
        )

    evaluation_payload = {
        "session_id": st.session_state.session_id,
        "question_id": question_id,
        "question": current_question["question_text"],
        "answer": submitted_answer,
        "cv_text": st.session_state.cv_text,
        "provider": st.session_state.provider,
    }

    try:

        response = requests.post(
            f"{API_BASE_URL}/interview/evaluate",
            json=evaluation_payload,
            timeout=180,
        )

        if response.status_code == 200:

            result = response.json()

            evaluation = result["evaluation"]

            # Mark question as processed
            st.session_state.processed_questions.add(
                question_id
            )

            # Save result
            st.session_state.evaluations.append(
                {
                    "question_number": current_index + 1,
                    "question": current_question[
                        "question_text"
                    ],
                    "answer": submitted_answer,
                    "evaluation": evaluation,
                }
            )

            # Move to next question
            st.session_state.current_question_index += 1

            # Reset timer
            st.session_state.question_start_time = None

            st.rerun()

        else:

            st.error(
                f"Backend error "
                f"{response.status_code}: "
                f"{response.text}"
            )

    except requests.Timeout:

        st.error(
            "Evaluation took too long."
        )

    except requests.RequestException as exc:

        st.error(
            f"Unable to connect to backend: {exc}"
        )


# ============================================================
# 1. Interview Setup
# ============================================================

st.subheader("1. Interview Setup")


job_role = st.text_input(
    "Target Job Role",
    value=st.session_state.job_role,
    placeholder="Example: Frontend Developer",
)


provider_options = [
    "ollama",
    "gemini",
    "huggingface",
]


provider = st.selectbox(
    "Select LLM Provider",
    provider_options,
    index=provider_options.index(
        st.session_state.provider
    ),
)


# ============================================================
# CV Upload
# ============================================================

uploaded_file = st.file_uploader(
    "Upload your CV",
    type=[
        "pdf",
        "docx",
        "txt",
    ],
)


# ============================================================
# Parse CV
# ============================================================

if uploaded_file is not None:

    if st.button("Parse CV"):

        try:

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }

            with st.spinner(
                "Parsing CV..."
            ):

                response = requests.post(
                    f"{API_BASE_URL}/cv/parse",
                    files=files,
                    timeout=60,
                )

            if response.status_code == 200:

                result = response.json()

                st.session_state.cv_text = (
                    result["data"]["raw_text"]
                )

                st.success(
                    "CV parsed successfully."
                )

                skills = result["data"].get(
                    "skills",
                    [],
                )

                if skills:

                    st.write(
                        "**Detected Skills:**"
                    )

                    st.write(
                        ", ".join(skills)
                    )

            else:

                st.error(
                    f"Backend error "
                    f"{response.status_code}: "
                    f"{response.text}"
                )

        except requests.RequestException as exc:

            st.error(
                f"Unable to connect to backend: {exc}"
            )


# ============================================================
# CV Ready
# ============================================================

if st.session_state.cv_text:

    st.success(
        "CV text is ready for interview generation."
    )


# ============================================================
# Start Interview
# ============================================================

if (
    st.session_state.cv_text
    and not st.session_state.interview_started
):

    if st.button(
        "Start Interview"
    ):

        if not job_role.strip():

            st.warning(
                "Please enter a target job role."
            )

        else:

            try:

                st.session_state.job_role = (
                    job_role.strip()
                )

                st.session_state.provider = provider

                payload = {
                    "cv_text": (
                        st.session_state.cv_text
                    ),
                    "job_role": (
                        st.session_state.job_role
                    ),
                    "provider": (
                        st.session_state.provider
                    ),
                    "interview_type": "personalised",
                }

                with st.spinner(
                    "Generating personalised interview questions..."
                ):

                    response = requests.post(
                        f"{API_BASE_URL}/interview/questions",
                        json=payload,
                        timeout=180,
                    )

                if response.status_code == 200:

                    result = response.json()

                    st.session_state.user_id = (
                        result["user_id"]
                    )

                    st.session_state.session_id = (
                        result["session_id"]
                    )

                    st.session_state.questions = (
                        result["questions"]
                    )

                    st.session_state.current_question_index = 0

                    st.session_state.evaluations = []

                    st.session_state.interview_started = True

                    st.session_state.interview_ended = False

                    st.session_state.question_start_time = None

                    st.session_state.processed_questions = set()

                    st.rerun()

                else:

                    st.error(
                        f"Backend error "
                        f"{response.status_code}: "
                        f"{response.text}"
                    )

            except requests.Timeout:

                st.error(
                    "Question generation took too long."
                )

            except requests.RequestException as exc:

                st.error(
                    f"Unable to connect to backend: {exc}"
                )


# ============================================================
# 2. Mock Interview
# ============================================================

if (
    st.session_state.interview_started
    and st.session_state.questions
    and not st.session_state.interview_ended
):

    st.divider()

    st.subheader(
        "2. Mock Interview"
    )

    current_index = (
        st.session_state.current_question_index
    )

    total_questions = len(
        st.session_state.questions
    )


    # ========================================================
    # Current Question
    # ========================================================

    if current_index < total_questions:

        current_question = (
            st.session_state.questions[
                current_index
            ]
        )


        # ----------------------------------------------------
        # Start timer
        # ----------------------------------------------------

        if (
            st.session_state.question_start_time
            is None
        ):

            st.session_state.question_start_time = (
                time.time()
            )


        # ----------------------------------------------------
        # Auto-refresh every second
        # ----------------------------------------------------

        st_autorefresh(
            interval=1000,
            key=f"timer_{current_index}",
        )


        # ----------------------------------------------------
        # Calculate remaining time
        # ----------------------------------------------------

        elapsed_time = (
            time.time()
            - st.session_state.question_start_time
        )

        remaining_seconds = max(
            0,
            QUESTION_TIME_LIMIT
            - int(elapsed_time),
        )

        minutes = (
            remaining_seconds // 60
        )

        seconds = (
            remaining_seconds % 60
        )


        # ----------------------------------------------------
        # Question Progress
        # ----------------------------------------------------

        st.write(
            f"Question "
            f"{current_index + 1} "
            f"of {total_questions}"
        )


        # ----------------------------------------------------
        # Timer Display
        # ----------------------------------------------------

        if remaining_seconds > 60:

            st.info(
                f"⏱ Time remaining: "
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        elif remaining_seconds > 0:

            st.warning(
                f"⏱ Time remaining: "
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        else:

            st.error(
                "⏱ Time is up. "
                "Your answer is being submitted automatically."
            )


        # ----------------------------------------------------
        # Display Question
        # ----------------------------------------------------

        st.info(
            current_question[
                "question_text"
            ]
        )


        # ----------------------------------------------------
        # Answer Box
        # ----------------------------------------------------

        answer = st.text_area(
            "Your Answer",
            key=f"answer_{current_index}",
            height=180,
            placeholder=(
                "Type your interview answer here..."
            ),
            disabled=(
                remaining_seconds == 0
            ),
        )


        # ----------------------------------------------------
        # Manual Submit
        # ----------------------------------------------------

        if remaining_seconds > 0:

            if st.button(
                "Submit Answer",
                key=f"submit_{current_index}",
            ):

                if not answer.strip():

                    st.warning(
                        "Please enter an answer."
                    )

                else:

                    with st.spinner(
                        "Evaluating your answer..."
                    ):

                        submit_interview_answer(
                            current_question=(
                                current_question
                            ),
                            answer=answer,
                            current_index=(
                                current_index
                            ),
                        )


        # ----------------------------------------------------
        # Automatic Submission
        # ----------------------------------------------------

        else:

            question_id = (
                current_question[
                    "question_id"
                ]
            )

            if (
                question_id
                not in st.session_state.processed_questions
            ):

                with st.spinner(
                    "Submitting and evaluating answer..."
                ):

                    submit_interview_answer(
                        current_question=(
                            current_question
                        ),
                        answer=answer,
                        current_index=(
                            current_index
                        ),
                    )


    # ========================================================
    # Current Batch Completed
    # ========================================================

    else:

        st.success(
            f"You have completed "
            f"{total_questions} interview questions."
        )

        st.subheader(
            "Would you like to continue?"
        )

        col1, col2 = st.columns(2)


        # ----------------------------------------------------
        # End Interview
        # ----------------------------------------------------

        with col1:

            if st.button(
                "End Interview",
                use_container_width=True,
            ):

                st.session_state.interview_ended = True

                st.rerun()


        # ----------------------------------------------------
        # Generate More Questions
        # ----------------------------------------------------

        with col2:

            if st.button(
                "Generate 5 More Questions",
                use_container_width=True,
            ):

                try:

                    payload = {
                        "cv_text": (
                            st.session_state.cv_text
                        ),
                        "job_role": (
                            st.session_state.job_role
                        ),
                        "provider": (
                            st.session_state.provider
                        ),
                        "interview_type": (
                            "personalised"
                        ),
                    }

                    with st.spinner(
                        "Generating 5 more questions..."
                    ):

                        response = requests.post(
                            (
                                f"{API_BASE_URL}/interview/"
                                f"{st.session_state.session_id}"
                                "/more-questions"
                            ),
                            json=payload,
                            timeout=180,
                        )

                    if response.status_code == 200:

                        result = response.json()

                        new_questions = (
                            result["questions"]
                        )

                        st.session_state.questions.extend(
                            new_questions
                        )

                        st.session_state.question_start_time = None

                        st.rerun()

                    else:

                        st.error(
                            f"Backend error "
                            f"{response.status_code}: "
                            f"{response.text}"
                        )

                except requests.Timeout:

                    st.error(
                        "Question generation took too long."
                    )

                except requests.RequestException as exc:

                    st.error(
                        f"Unable to connect to backend: {exc}"
                    )


# ============================================================
# 3. Final Interview Result
# ============================================================

if (
    st.session_state.interview_started
    and st.session_state.interview_ended
):

    st.divider()

    st.success(
        "Interview completed."
    )

    st.subheader(
        "3. Final Interview Result"
    )


    try:

        response = requests.get(
            (
                f"{API_BASE_URL}/interview/"
                f"{st.session_state.session_id}"
                "/score"
            ),
            timeout=30,
        )

        if response.status_code == 200:

            final_result = response.json()

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Average Score",
                    (
                        f"{final_result['average_score']}"
                        "/25"
                    ),
                )

            with col2:

                st.metric(
                    "Percentage",
                    (
                        f"{final_result['percentage']}"
                        "%"
                    ),
                )

            st.write(
                "**Evaluated Answers:**",
                final_result[
                    "evaluated_answers"
                ],
            )

            st.write(
                "**Total Score:**",
                (
                    f"{final_result['total_score']}"
                    f"/"
                    f"{final_result['maximum_score']}"
                ),
            )

        else:

            st.error(
                f"Unable to retrieve final score: "
                f"{response.text}"
            )

    except requests.RequestException as exc:

        st.error(
            f"Unable to retrieve score: {exc}"
        )


    # ========================================================
    # 4. Detailed Rubric Results
    # ========================================================

    st.divider()

    st.subheader(
        "4. Detailed Rubric Results"
    )


    for item in st.session_state.evaluations:

        evaluation = item[
            "evaluation"
        ]

        with st.expander(
            (
                f"Question "
                f"{item['question_number']} "
                f"- "
                f"{evaluation['total_score']}/25"
            )
        ):

            st.markdown(
                "#### Interview Question"
            )

            st.write(
                item["question"]
            )


            st.markdown(
                "#### Your Answer"
            )

            st.write(
                item["answer"]
            )


            st.markdown(
                "#### Rubric Scores"
            )


            col1, col2, col3, col4, col5 = (
                st.columns(5)
            )


            with col1:

                st.metric(
                    "Relevance",
                    (
                        f"{evaluation['relevance']['score']}"
                        "/5"
                    ),
                )


            with col2:

                st.metric(
                    "Technical",
                    (
                        f"{evaluation['technical_accuracy']['score']}"
                        "/5"
                    ),
                )


            with col3:

                st.metric(
                    "Clarity",
                    (
                        f"{evaluation['clarity_communication']['score']}"
                        "/5"
                    ),
                )


            with col4:

                st.metric(
                    "CV Evidence",
                    (
                        f"{evaluation['cv_evidence']['score']}"
                        "/5"
                    ),
                )


            with col5:

                st.metric(
                    "Depth",
                    (
                        f"{evaluation['depth_completeness']['score']}"
                        "/5"
                    ),
                )


            st.markdown(
                "#### Rubric Feedback"
            )


            st.write(
                "**Relevance to Question**"
            )

            st.caption(
                evaluation[
                    "relevance"
                ]["feedback"]
            )


            st.write(
                "**Technical Accuracy / Subject Knowledge**"
            )

            st.caption(
                evaluation[
                    "technical_accuracy"
                ]["feedback"]
            )


            st.write(
                "**Clarity & Communication**"
            )

            st.caption(
                evaluation[
                    "clarity_communication"
                ]["feedback"]
            )


            st.write(
                "**Use of Personal Experience / CV Evidence**"
            )

            st.caption(
                evaluation[
                    "cv_evidence"
                ]["feedback"]
            )


            st.write(
                "**Depth & Completeness**"
            )

            st.caption(
                evaluation[
                    "depth_completeness"
                ]["feedback"]
            )


            st.divider()


            st.markdown(
                (
                    f"### Total Score: "
                    f"{evaluation['total_score']}/25"
                )
            )


            st.markdown(
                "#### Overall Feedback"
            )

            st.write(
                evaluation[
                    "overall_feedback"
                ]
            )


    # ========================================================
    # Start New Interview
    # ========================================================

    st.divider()

    if st.button(
        "Start New Interview"
    ):

        st.session_state.user_id = None
        st.session_state.cv_text = ""
        st.session_state.session_id = None
        st.session_state.questions = []
        st.session_state.current_question_index = 0
        st.session_state.evaluations = []
        st.session_state.interview_started = False
        st.session_state.interview_ended = False
        st.session_state.job_role = ""
        st.session_state.provider = "ollama"
        st.session_state.question_start_time = None
        st.session_state.processed_questions = set()

        st.rerun()