import streamlit as st
import random
import time
from streamlit_autorefresh import st_autorefresh
from mongo_storage import (
    save_result_mongo,
    get_all_topics,
    get_topic_questions,
)

class QuizApp:
    def __init__(self, config):
        self.duration_minutes = config["duration_minutes"]
        self.num_questions = config["num_questions"]
        self.randomize = True
        self.questions = []
        self.training_mode = False
        self.init_state()

    def load_questions_topic(self, topic_id: str):
        return get_topic_questions(topic_id)

    def init_state(self):
        defaults = {
            "started": False,
            "index": 0,
            "score": 0,
            "answers": [],
            "quiz_questions": [],
            "start_time": None,
            "end_time": None,
            "shuffled_options": {},
            "key_maps": {},
            "feedback": "",
            "selected_topic_id": None,
            "training_mode": False,
            "last_index": -1,
        }
        for k, v in defaults.items():
            st.session_state.setdefault(k, v)

    def shuffle_options(self, options):
        items = list(options.items())
        random.shuffle(items)
        shuffled = {chr(65 + i): val for i, (_, val) in enumerate(items)}
        key_map = {chr(65 + i): orig_key for i, (orig_key, _) in enumerate(items)}
        return shuffled, key_map

    def start_quiz(self):
        st.session_state.started = True
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.answers = []
        st.session_state.shuffled_options = {}
        st.session_state.key_maps = {}
        st.session_state.feedback = ""
        st.session_state.last_index = -1
        self.training_mode = st.session_state.get("training_mode", False)

        topic_id = st.session_state.selected_topic_id
        self.questions = self.load_questions_topic(topic_id)

        selected_questions = self.questions[self.start_question-1:self.end_question]
        if self.randomize:
            random.shuffle(selected_questions)

        st.session_state.quiz_questions = selected_questions[:self.num_questions]
        st.session_state.start_time = time.time()
        st.session_state.end_time = st.session_state.start_time + self.duration_minutes * 60

    def get_time_remaining(self):
        end = st.session_state.get("end_time")
        if not end:
            return 0
        return max(0, int(end - time.time()))

    def render_settings(self):
        st.sidebar.header("⚙️ Quiz Settings")

        topics = get_all_topics()
        if not topics:
            st.sidebar.warning("🚫 No quizzes available. Please upload a question set in the Admin panel.")
            return

        options = {t["topic_name"]: t["topic_id"] for t in topics}
        topic_names = ["-- Select a topic --"] + list(options.keys())
        selected_name = st.sidebar.selectbox("Topic", topic_names, index=0)
        selected_topic_id = options.get(selected_name)
        st.session_state.selected_topic_id = selected_topic_id
        st.write(f"Available Questions: {self.num_questions}")
        self.start_question=1
        self.end_question=self.num_questions
        self.start_question = st.sidebar.number_input("From Question", value=1,min_value=1,max_value=self.end_question)
        self.end_question = st.sidebar.number_input("To Question", value=self.num_questions,min_value=self.start_question,max_value=len(self.questions))
        st.sidebar.write(f"Range selected: {self.start_question} to {self.end_question}")
        self.available_questions=self.end_question-self.start_question+1

        self.num_questions = st.sidebar.number_input("Number of questions", 1, 1000, self.available_questions)
        self.randomize = st.sidebar.checkbox("Randomize question order", value=True)
        st.session_state.training_mode = st.sidebar.checkbox("Training mode (show correct answers)", value=False)
        self.duration_minutes = st.sidebar.number_input("Quiz duration (minutes)", 1, 360, self.duration_minutes)

        if selected_topic_id:
            if st.sidebar.button("Start Quiz"):
                self.start_quiz()
        else:
            st.sidebar.button("Start Quiz", disabled=True)
            st.sidebar.info("Please select a topic to begin.")

    def render_question(self):
        if st.session_state.index != st.session_state.last_index:
            st.session_state.last_index = st.session_state.index
            for k in list(st.session_state.keys()):
                if k.startswith("show_"):
                    del st.session_state[k]

        remaining = self.get_time_remaining()
        minutes, seconds = divmod(remaining, 60)
        st.markdown(f"⏳ **Time Remaining:** {minutes:02d}:{seconds:02d}")
        total_time = max(1, self.duration_minutes * 60)
        st.progress(min(1.0, remaining / total_time))
        st.markdown(f"📘 You’ve answered {st.session_state.index} of {len(st.session_state.quiz_questions)} questions")

        if st.session_state.feedback:
            st.success(st.session_state.feedback) if "✅" in st.session_state.feedback else st.error(st.session_state.feedback)

        q = st.session_state.quiz_questions[st.session_state.index]
        qid = q.get("id", st.session_state.index + 1)

        st.header(f"Question {qid}")
        st.write(q["text"])

        if q.get("image"):
            st.image(q["image"], caption=f"Image for Question {qid}", use_column_width=True)

        if qid not in st.session_state.shuffled_options:
            shuffled, key_map = self.shuffle_options(q["options"])
            st.session_state.shuffled_options[qid] = shuffled
            st.session_state.key_maps[qid] = key_map

        shuffled = st.session_state.shuffled_options[qid]
        key_map = st.session_state.key_maps[qid]
        display_options = {k: f"{k}. {v}" for k, v in shuffled.items()}

        if q["type"] == "single":
            selected = st.radio("Choose one:", list(display_options.values()), key=f"q{st.session_state.index}")
            selected_key = selected.split(".")[0] if selected else None
            user_answers = [key_map[selected_key]] if selected_key else []
        else:
            st.markdown("Choose one or more:")
            selected_keys = [
                k for k, label in display_options.items()
                if st.checkbox(label, key=f"{st.session_state.index}_{k}")
            ]
            user_answers = [key_map[k] for k in selected_keys]
        
        if "showe_answers" not in st.session_state:
            st.session_state.show_answers = False
        if self.training_mode:
            st.session_state.show_answers=st.checkbox("👁️ Show correct answers", value=st.session_state.show_answers)

        if self.training_mode and st.session_state.show_answers:
            correct = q["correct"]
            correct_keys = [k for k, v in key_map.items() if v in correct]
            correct_texts = [f"{k}. {shuffled[k]}" for k in correct_keys]
            st.info(f"🎯 Correct answer(s): {', '.join(correct_texts)}")

        if st.button("Submit Answer"):
            correct = q["correct"]
            gained = q.get("points", len(correct)) if set(user_answers) == set(correct) else 0

            save_result_mongo(
                email=st.session_state.email,
                question_id=qid,
                user_answers=user_answers,
                correct_answers=correct,
                score=gained,
                topic_id=st.session_state.get("selected_topic_id"),
            )

            st.session_state.score += gained
            st.session_state.feedback = "✅ Correct!" if gained > 0 else "❌ Incorrect."

            st.session_state.answers.append({
                "question_id": qid,
                "user": user_answers,
                "correct": correct,
            })

            st.session_state.index += 1
            time.sleep(0.3)
            st.rerun()

    def render_results(self):
        st.success("🏁 Quiz complete!")
        total_points = sum(q.get("points", len(q.get("correct", []))) for q in st.session_state.quiz_questions)
        st.write(f"Your score: {st.session_state.score} / {total_points}")
        st.write("📊 Answer Summary:")
        st.json(st.session_state.answers)

        incorrect = [a for a in st.session_state.answers if set(a["user"]) != set(a["correct"])]
        if incorrect:
            st.markdown("## 🔍 Review Incorrect Answers")
            for entry in incorrect:
                qid = entry["question_id"]
                q = next((qq for qq in st.session_state.quiz_questions if qq.get("id") == qid), None)
                if not q:
                    continue

                st.markdown(f"### ❌ Question {qid}")
                st.write(q["text"])

                key_map = st.session_state.key_maps.get(qid, {})
                shuffled = st.session_state.shuffled_options.get(qid, {})
                correct_keys = [k for k, v in key_map.items() if v in entry["correct"]]
                user_keys = [k for k, v in key_map.items() if v in entry["user"]]

                correct_texts = [f"{k}. {shuffled.get(k, '')}" for k in correct_keys]
                user_texts = [f"{k}. {shuffled.get(k, '')}" for k in user_keys]

                st.markdown(f"**✅ Correct Answer(s):** {', '.join(correct_texts)}")
                st.markdown(f"**🧠 Your Answer(s):** {', '.join(user_texts)}")
                st.markdown("---")

        st.session_state.started = False

    def run(self):
        st.title("🧠 Quiz Training")

        topics = get_all_topics()
        if not topics:
            st.warning("🚫 No quizzes available. Please upload a question set in the Admin panel.")
            return

        self.render_settings()

        if st.session_state.started:
            in_progress = (
                st.session_state.index < len(st.session_state.quiz_questions)
                and self.get_time_remaining() > 0
            )
            if in_progress:
                st_autorefresh(interval=1000, limit=None, key="quiz_timer")

            if self.get_time_remaining() == 0:
                st.warning("⏱️ Time's up!")
                st.session_state.started = False
            elif st.session_state.index < len(st.session_state.quiz_questions):
                self.render_question()
            else:
                self.render_results()