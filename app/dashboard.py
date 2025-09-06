import streamlit as st
import pandas as pd
from mongo_storage import get_users, get_user_results

def show_dashboard():
    st.title("📊 Quiz Performance Dashboard")

    users = [u["email"] for u in get_users()]
    if not users:
        st.warning("No users found.")
        return

    selected_email = st.selectbox("Select a user", users)
    if not selected_email:
        return

    results = get_user_results(selected_email)
    if not results:
        st.info("No results found for this user.")
        return

    df = pd.DataFrame(results)
    st.subheader(f"📋 Summary for {selected_email}")
    total_questions = len(df)
    avg_score = df["score"].mean() if total_questions > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Questions Answered", total_questions)
    with col2:
        st.metric("Average Score", f"{avg_score:.2f}")

    st.subheader("📈 Score Over Time")
    trend = df[["timestamp", "score"]].copy()
    trend["timestamp"] = pd.to_datetime(trend["timestamp"])
    trend = trend.set_index("timestamp").resample("D").sum()
    st.line_chart(trend)

    st.subheader("🧠 Recent Answers")
    st.dataframe(
        df[["question_id", "user_answers", "correct_answers", "score", "timestamp", "topic_id"]].tail(20),
        use_container_width=True
    )
