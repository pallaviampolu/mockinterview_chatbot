# frontend/app.py

import requests
import streamlit as st


# ============================================================
# Configuration
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000"


# ============================================================
# Page Settings
# ============================================================

st.set_page_config(
    page_title="CV-Aware Interview Preparation Chatbot",
    page_icon="💬",
    layout="centered",
)


st.title("CV-Aware Interview Preparation Chatbot")

st.write(
    "Upload your CV, choose a target job role, "
    "and practise a personalised mock interview."
)


# ============================================================
# Session State
# ============================================================

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


# ============================================================
# User Details
# ============================================================

st.subheader("1. Interview Setup")

user_id = st.number_input(
    "User ID",
    min_value=1,
    value=1,
    step=1,
)

job_role = st.text_input(
    "Target Job Role",
    placeholder="Example: Data Analyst",
)

provider = st.selectbox(
    "Select LLM Provider",
    [
        "ollama",
        "gemini",
    ],
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

                st.write("Detected Skills:")

                skills = result["data"].get(
                    "skills",
                    [],
                )

                if skills:
                    st.write(
                        ", ".join(skills)
                    )

                else:
                    st.write(
                        "No predefined skills detected."
                    )

            else:

                st.error(
                    response.json().get(
                        "detail",
                        "CV parsing failed.",
                    )
                )

        except requests.RequestException as exc:

            st.error(
                f"Unable to connect to backend: {exc}"
            )


# ============================================================
# Display CV Status
# ============================================================

if st.session_state.cv_text:

    st.success(
        "CV text is ready for interview generation."
    )


# # ============================================================
# # Start Interview
# # ============================================================

# if st.session_state.cv_text:

#     if st.button("Start Interview"):

#         if not job_role.strip():

#             st.warning(
#                 "Please enter a target job role."
#             )

#         else:

#             try:

#                 payload = {
#                     "user_id": user_id,
#                     "cv_text": st.session_state.cv_text,
#                     "job_role": job_role,
#                     "provider": provider,
#                     "interview_type": "personalised",
#                 }
                

#                 response = requests.post(
#                     f"{API_BASE_URL}/interview/questions",
#                     json=payload,
#                     timeout=120,
#                 )

#                 if response.status_code == 200:

#                     result = response.json()

#                     st.session_state.session_id = (
#                         result["session_id"]
#                     )

#                     st.session_state.questions = (
#                         result["questions"]
#                     )

#                     st.session_state.current_question_index = 0

#                     st.session_state.evaluations = []

#                     st.session_state.interview_started = True

#                     st.success(
#                         "Interview started successfully."
#                     )

#                 else:

#                     st.error(
#                         response.json().get(
#                             "detail",
#                             "Question generation failed.",
#                         )
#                     )

#             except requests.RequestException as exc:

#                 st.error(
#                     f"Unable to connect to backend: {exc}"
#                 )


# ============================================================
# Start Interview
# ============================================================

if st.session_state.cv_text:

    if st.button("Start Interview"):

        if not job_role.strip():
            st.warning("Please enter a target job role.")

        else:
            try:
                payload = {
                    "user_id": int(user_id),
                    "cv_text": st.session_state.cv_text,
                    "job_role": job_role,
                    "provider": provider,
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

                    st.session_state.session_id = result["session_id"]
                    st.session_state.questions = result["questions"]

                    st.session_state.current_question_index = 0
                    st.session_state.evaluations = []
                    st.session_state.interview_started = True

                    st.success(
                        "Interview started successfully."
                    )

                    st.rerun()

                else:
                    st.error(
                        f"Backend error {response.status_code}: "
                        f"{response.text}"
                    )

            except requests.Timeout:
                st.error(
                    "Question generation took too long. "
                    "Please try again."
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
# Interview Section
# ============================================================

if (
    st.session_state.interview_started
    and st.session_state.questions
):

    st.divider()

    st.subheader("2. Mock Interview")

    current_index = (
        st.session_state.current_question_index
    )

    total_questions = len(
        st.session_state.questions
    )


    # --------------------------------------------------------
    # Questions Remaining
    # --------------------------------------------------------

    if current_index < total_questions:

        current_question = (
            st.session_state.questions[
                current_index
            ]
        )

        st.write(
            f"Question "
            f"{current_index + 1} "
            f"of {total_questions}"
        )

        st.info(
            current_question[
                "question_text"
            ]
        )


        answer = st.text_area(
            "Your Answer",
            key=f"answer_{current_index}",
            height=180,
            placeholder=(
                "Type your interview answer here..."
            ),
        )


        # ----------------------------------------------------
        # Submit Answer
        # ----------------------------------------------------

        if st.button(
            "Submit Answer",
            key=f"submit_{current_index}",
        ):

            if not answer.strip():

                st.warning(
                    "Please enter an answer."
                )

            else:

                try:

                    evaluation_payload = {
                        "session_id": (
                            st.session_state.session_id
                        ),
                        "question_id": (
                            current_question[
                                "question_id"
                            ]
                        ),
                        "question": (
                            current_question[
                                "question_text"
                            ]
                        ),
                        "answer": answer,
                        "cv_text": (
                            st.session_state.cv_text
                        ),
                        "provider": provider,
                    }

                    response = requests.post(
                        f"{API_BASE_URL}/interview/evaluate",
                        json=evaluation_payload,
                        timeout=120,
                    )

                    if response.status_code == 200:

                        result = response.json()

                        evaluation = result[
                            "evaluation"
                        ]

                        st.session_state.evaluations.append(
                            evaluation
                        )

                        st.success(
                            "Answer evaluated successfully."
                        )


                        # ------------------------------------
                        # Display Rubric Result
                        # ------------------------------------

                        st.write(
                            "### Rubric Evaluation"
                        )

                        st.write(
                            "Relevance:",
                            evaluation[
                                "relevance"
                            ]["score"],
                            "/5",
                        )

                        st.write(
                            evaluation[
                                "relevance"
                            ]["feedback"]
                        )


                        st.write(
                            "Technical Accuracy:",
                            evaluation[
                                "technical_accuracy"
                            ]["score"],
                            "/5",
                        )

                        st.write(
                            evaluation[
                                "technical_accuracy"
                            ]["feedback"]
                        )


                        st.write(
                            "Clarity & Communication:",
                            evaluation[
                                "clarity_communication"
                            ]["score"],
                            "/5",
                        )

                        st.write(
                            evaluation[
                                "clarity_communication"
                            ]["feedback"]
                        )


                        st.write(
                            "CV Evidence:",
                            evaluation[
                                "cv_evidence"
                            ]["score"],
                            "/5",
                        )

                        st.write(
                            evaluation[
                                "cv_evidence"
                            ]["feedback"]
                        )


                        st.write(
                            "Depth & Completeness:",
                            evaluation[
                                "depth_completeness"
                            ]["score"],
                            "/5",
                        )

                        st.write(
                            evaluation[
                                "depth_completeness"
                            ]["feedback"]
                        )


                        st.write(
                            "### Score:",
                            evaluation[
                                "total_score"
                            ],
                            "/25",
                        )

                        st.write(
                            "Overall Feedback:"
                        )

                        st.write(
                            evaluation[
                                "overall_feedback"
                            ]
                        )


                        # ------------------------------------
                        # Move to next question
                        # ------------------------------------

                        st.session_state.current_question_index += 1

                        st.rerun()

                    else:

                        st.error(
                            response.json().get(
                                "detail",
                                "Evaluation failed.",
                            )
                        )

                except requests.RequestException as exc:

                    st.error(
                        f"Unable to connect to backend: {exc}"
                    )


    # ========================================================
    # Interview Finished
    # ========================================================

    else:

        st.success(
            "Interview completed."
        )

        st.subheader(
            "3. Final Interview Result"
        )


        # ----------------------------------------------------
        # Get Session Score
        # ----------------------------------------------------

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
                    "Evaluated Answers:",
                    final_result[
                        "evaluated_answers"
                    ],
                )

                st.write(
                    "Total Score:",
                    (
                        f"{final_result['total_score']}"
                        f"/{final_result['maximum_score']}"
                    ),
                )

            else:

                st.error(
                    "Unable to retrieve final score."
                )

        except requests.RequestException as exc:

            st.error(
                f"Unable to retrieve interview score: {exc}"
            )


        # ----------------------------------------------------
        # Start New Interview
        # ----------------------------------------------------

        if st.button(
            "Start New Interview"
        ):

            st.session_state.session_id = None
            st.session_state.questions = []
            st.session_state.current_question_index = 0
            st.session_state.evaluations = []
            st.session_state.interview_started = False

            st.rerun()