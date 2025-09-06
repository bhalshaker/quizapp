import streamlit as st
import json
import random
import time

class QuizApp:
    def __init__(self, config):
        self.file_path = config["file_path"]
        self.duration_minutes = config["duration_minutes"]
        self.num_questions = config["num_questions"]
        self.training_mode = False
        self.randomize = True
        self.questions = self.load_questions()
        self.init_state()

    def load_questions(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

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
            "feedback": ""
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

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

        selected_questions = self.questions.copy()
        if self.randomize:
            random.shuffle(selected_questions)
        st.session_state.quiz_questions = selected_questions[:self.num_questions]
        st.session_state.start_time = time.time()
        st.session_state.end_time = st.session_state.start_time + self.duration_minutes * 60

    def get_time_remaining(self):
        return max(0, int(st.session_state.end_time - time.time()))

    def render_settings(self):
        st.sidebar.header("⚙️ Quiz Settings")
        self.num_questions = st.sidebar.number_input("Number of questions", 1, len(self.questions), self.num_questions)
        self.randomize = st.sidebar.checkbox("Randomize question order", value=True)
        self.training_mode = st.sidebar.checkbox("Training mode (show correct answers)", value=False)
        self.duration_minutes = st.sidebar.number_input("Quiz duration (minutes)", 1, 360, self.duration_minutes)

        if st.sidebar.button("Start Quiz"):
            self.start_quiz()

    def render_question(self):
        remaining = self.get_time_remaining()
        minutes, seconds = divmod(remaining, 60)
        st.markdown(f"⏳ **Time Remaining:** {minutes:02d}:{seconds:02d}")
        st.progress(remaining / (self.duration_minutes * 60))
        st.markdown(f"📘 You’ve answered {st.session_state.index} of {len(st.session_state.quiz_questions)} questions")

        if st.session_state.feedback:
            st.success(st.session_state.feedback) if "✅" in st.session_state.feedback else st.error(st.session_state.feedback)

        q = st.session_state.quiz_questions[st.session_state.index]
        st.header(f"Question {q['id']}")
        st.write(q["text"])

        if "image" in q:
            st.image(q["image"], caption=f"Image for Question {q['id']}", use_column_width=True)

        qid = q["id"]
        if qid not in st.session_state.shuffled_options:
            shuffled, key_map = self.shuffle_options(q["options"])
            st.session_state.shuffled_options[qid] = shuffled
            st.session_state.key_maps[qid] = key_map

        shuffled = st.session_state.shuffled_options[qid]
        key_map = st.session_state.key_maps[qid]
        display_options = {k: f"{k}. {v}" for k, v in shuffled.items()}

        selected_keys = []
        if q["type"] == "single":
            selected = st.radio("Choose one:", list(display_options.values()), key=f"q{st.session_state.index}")
            selected_key = selected.split(".")[0]
            user_answers = [key_map[selected_key]]
        else:
            st.markdown("Choose one or more:")
            for k, label in display_options.items():
                if st.checkbox(label, key=f"{st.session_state.index}_{k}"):
                    selected_keys.append(k)
            user_answers = [key_map[k] for k in selected_keys]

        if st.button("Submit Answer"):
            correct = q["correct"]
            if set(user_answers) == set(correct):
                st.session_state.score += q["points"]
                st.session_state.feedback = "✅ Correct!"
            else:
                st.session_state.feedback = "❌ Incorrect."

            if self.training_mode:
                correct_keys = [k for k, v in key_map.items() if v in correct]
                correct_texts = [f"{k}. {shuffled[k]}" for k in correct_keys]
                st.info(f"🎯 Correct answer(s): {', '.join(correct_texts)}")

            st.session_state.answers.append({
                "question_id": q["id"],
                "user": user_answers,
                "correct": correct
            })

            st.session_state.index += 1
            time.sleep(1)
            st.rerun()

    def render_results(self):
        st.success("🏁 Quiz complete!")
        st.write(f"Your score: {st.session_state.score} / {sum(q['points'] for q in st.session_state.quiz_questions)}")
        st.write("📊 Answer Summary:")
        st.json(st.session_state.answers)

        incorrect = [a for a in st.session_state.answers if set(a["user"]) != set(a["correct"])]
        if incorrect:
            st.markdown("## 🔍 Review Incorrect Answers")
            for entry in incorrect:
                qid = entry["question_id"]
                q = next(q for q in st.session_state.quiz_questions if q["id"] == qid)
                st.markdown(f"### ❌ Question {qid}")
                st.write(q["text"])

                correct_keys = [k for k, v in st.session_state.key_maps[qid].items() if v in entry["correct"]]
                correct_texts = [f"{k}. {st.session_state.shuffled_options[qid][k]}" for k in correct_keys]
                st.markdown(f"**✅ Correct Answer(s):** {', '.join(correct_texts)}")

                user_keys = [k for k, v in st.session_state.key_maps[qid].items() if v in entry["user"]]
                user_texts = [f"{k}. {st.session_state.shuffled_options[qid][k]}" for k in user_keys]
                st.markdown(f"**🧠 Your Answer(s):** {', '.join(user_texts)}")
                st.markdown("---")

        st.session_state.started = False

    def run(self):
        st.title("🧠 Quiz Training")
        self.render_settings()

        if st.session_state.started:
            if self.get_time_remaining() == 0:
                st.warning("⏱️ Time's up!")
                st.session_state.started = False
            elif st.session_state.index < len(st.session_state.quiz_questions):
                self.render_question()
            else:
                self.render_results()

        return None
