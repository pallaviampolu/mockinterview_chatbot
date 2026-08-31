

import time

import requests
import streamlit as st


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
    "> an interview preparation chatbot
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

if "cv_id" not in st.session_state:
    st.session_state.cv_id = None

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

if "auto_submit_question_id" not in st.session_state:
    st.session_state.auto_submit_question_id = None


# ============================================================
# Timer
# ============================================================

@st.fragment(run_every="1s")
def show_timer(start_time: float):

    elapsed = time.time() - start_time

    remaining = max(
        0,
        QUESTION_TIME_LIMIT - int(elapsed),
    )

    minutes = remaining // 60
    seconds = remaining % 60

    if remaining > 60:
        st.info(
            f"⏱ Time remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )

    elif remaining > 0:
        st.warning(
            f"⏱ Time remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )

    else:
        st.error(
            "⏱ Time is up."
        )


# ============================================================
# Submit Answer
# ============================================================

def submit_answer(
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
            "No answer was submitted within "
            "the five-minute time limit."
        )


    # ========================================================
    # Answer Time
    # ========================================================

    if st.session_state.question_start_time is not None:

        time_taken_seconds = int(
            time.time()
            - st.session_state.question_start_time
        )

    else:
        time_taken_seconds = 0


    time_taken_seconds = min(
        time_taken_seconds,
        QUESTION_TIME_LIMIT,
    )

    answer_minutes = (
        time_taken_seconds // 60
    )

    answer_seconds = (
        time_taken_seconds % 60
    )

    time_taken_display = (
        f"{answer_minutes:02d}:"
        f"{answer_seconds:02d}"
    )


    # ========================================================
    # Payload
    # ========================================================

    payload = {
        "session_id": (
            st.session_state.session_id
        ),
        "question_id": (
            question_id
        ),
        "question": (
            current_question[
                "question_text"
            ]
        ),
        "answer": (
            submitted_answer
        ),
        "cv_text": (
            st.session_state.cv_text
        ),
        "provider": (
            st.session_state.provider
        ),
    }


    try:

        # ====================================================
        # Start submission timer
        # ====================================================

        submission_start_time = (
            time.perf_counter()
        )


        with st.spinner(
            "Submitting and evaluating your answer..."
        ):

            response = requests.post(
                (
                    f"{API_BASE_URL}"
                    "/interview/evaluate"
                ),
                json=payload,
                timeout=180,
            )


        # ====================================================
        # End submission timer
        # ====================================================

        submission_time_seconds = round(
            time.perf_counter()
            - submission_start_time,
            2,
        )


        if response.status_code == 200:

            result = response.json()

            evaluation = (
                result["evaluation"]
            )


            # ------------------------------------------------
            # Mark question completed
            # ------------------------------------------------

            st.session_state.processed_questions.add(
                question_id
            )


            # ------------------------------------------------
            # Prevent duplicate results
            # ------------------------------------------------

            already_saved = any(
                item.get("question_id")
                == question_id
                for item
                in st.session_state.evaluations
            )


            if not already_saved:

                st.session_state.evaluations.append(
                    {
                        "question_id": (
                            question_id
                        ),

                        "question_number": (
                            current_index + 1
                        ),

                        "question": (
                            current_question[
                                "question_text"
                            ]
                        ),

                        "answer": (
                            submitted_answer
                        ),

                        # User answering time
                        "time_taken_seconds": (
                            time_taken_seconds
                        ),

                        "time_taken_display": (
                            time_taken_display
                        ),

                        # Backend processing time
                        "submission_time_seconds": (
                            submission_time_seconds
                        ),

                        "evaluation": (
                            evaluation
                        ),
                    }
                )


            # =================================================
            # Move to Next Question
            # =================================================

            st.session_state.current_question_index = (
                current_index + 1
            )

            st.session_state.question_start_time = None

            st.session_state.auto_submit_question_id = None

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


    except Exception as exc:

        st.error(
            f"Unexpected error: {exc}"
        )


# ============================================================
# 1. Interview Setup
# ============================================================

st.subheader(
    "1. Interview Setup"
)


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

    if st.button(
        "Parse CV"
    ):

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


                skills = result[
                    "data"
                ].get(
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

                st.session_state.provider = (
                    provider
                )


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
                    "Generating personalised "
                    "interview questions..."
                ):

                    response = requests.post(
                        (
                            f"{API_BASE_URL}"
                            "/interview/questions"
                        ),
                        json=payload,
                        timeout=180,
                    )


                if response.status_code == 200:

                    result = response.json()


                    st.session_state.user_id = (
                        result["user_id"]
                    )


                    if "cv_id" in result:

                        st.session_state.cv_id = (
                            result["cv_id"]
                        )


                    st.session_state.session_id = (
                        result["session_id"]
                    )


                    st.session_state.questions = (
                        result["questions"]
                    )


                    st.session_state.current_question_index = 0

                    st.session_state.evaluations = []

                    st.session_state.processed_questions = set()

                    st.session_state.question_start_time = None

                    st.session_state.auto_submit_question_id = None

                    st.session_state.interview_started = True

                    st.session_state.interview_ended = False


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


        question_id = (
            current_question[
                "question_id"
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


        elapsed = (
            time.time()
            - st.session_state.question_start_time
        )


        remaining_seconds = max(
            0,
            QUESTION_TIME_LIMIT
            - int(elapsed),
        )


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        st.write(
            f"Question "
            f"{current_index + 1} "
            f"of {total_questions}"
        )


        # ----------------------------------------------------
        # Timer
        # ----------------------------------------------------

        show_timer(
            st.session_state.question_start_time
        )


        # ----------------------------------------------------
        # Question
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
        )


        # ====================================================
        # Submit Answer
        # ====================================================

        if st.button(
            "Submit Answer",
            key=f"submit_{current_index}",
        ):

            if not answer.strip():

                st.warning(
                    "Please enter an answer."
                )


            else:

                submit_answer(
                    current_question=(
                        current_question
                    ),

                    answer=answer,

                    current_index=(
                        current_index
                    ),
                )


        # ====================================================
        # Automatic Timeout
        # ====================================================

        if remaining_seconds <= 0:

            if (
                question_id
                not in st.session_state.processed_questions
                and
                st.session_state.auto_submit_question_id
                != question_id
            ):

                st.session_state.auto_submit_question_id = (
                    question_id
                )


                submit_answer(
                    current_question=(
                        current_question
                    ),

                    answer=answer,

                    current_index=(
                        current_index
                    ),
                )


    # ========================================================
    # Batch Complete
    # ========================================================

    else:

        st.success(
            f"You have completed "
            f"{total_questions} interview questions."
        )


        st.subheader(
            "Would you like to continue?"
        )


        col1, col2 = st.columns(
            2
        )


        # ----------------------------------------------------
        # End Interview
        # ----------------------------------------------------

        with col1:

            if st.button(
                "End Interview",
                use_container_width=True,
            ):

                st.session_state.interview_ended = (
                    True
                )

                st.session_state.question_start_time = (
                    None
                )

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
                                f"{API_BASE_URL}"
                                f"/interview/"
                                f"{st.session_state.session_id}"
                                "/more-questions"
                            ),
                            json=payload,
                            timeout=180,
                        )


                    if response.status_code == 200:

                        result = response.json()


                        st.session_state.questions.extend(
                            result["questions"]
                        )


                        st.session_state.question_start_time = (
                            None
                        )

                        st.session_state.auto_submit_question_id = (
                            None
                        )


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
                f"{API_BASE_URL}"
                f"/interview/"
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


            if "provider" in final_result:

                st.write(
                    "**LLM Provider:**",
                    final_result["provider"],
                )


            if "job_role" in final_result:

                st.write(
                    "**Target Job Role:**",
                    final_result["job_role"],
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
    # Detailed Rubric Results
    # ========================================================

    st.divider()

    st.subheader(
        "4. Detailed Rubric Results"
    )


    for item in st.session_state.evaluations:

        evaluation = (
            item["evaluation"]
        )


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


            # =================================================
            # Time Information
            # =================================================

            st.markdown(
                "#### Time Information"
            )


            time_col1, time_col2 = (
                st.columns(2)
            )


            with time_col1:

                st.metric(
                    "Answer Time",
                    item[
                        "time_taken_display"
                    ],
                    help=(
                        "Time taken by the user "
                        "before submitting the answer."
                    ),
                )


            with time_col2:

                st.metric(
                    "Submission Time",
                    (
                        f"{item['submission_time_seconds']:.2f} sec"
                    ),
                    help=(
                        "Time taken after submitting "
                        "the answer until the rubric "
                        "evaluation was returned."
                    ),
                )


            # =================================================
            # Rubric Scores
            # =================================================

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


            # =================================================
            # Rubric Feedback
            # =================================================

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
        st.session_state.cv_id = None
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
        st.session_state.auto_submit_question_id = None

        st.rerun()