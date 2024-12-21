from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
from fpdf import FPDF

# Koneksi SQLite
db = sqlite3.connect("quiz_bot.db", check_same_thread=False)
cursor = db.cursor()

# Buat tabel jika belum ada
cursor.execute("""
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    score INTEGER,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
db.commit()

# Data soal dan jawaban
questions = [
    {"question": "What is 2 + 2?", "answer": "4"},
    {"question": "What is the capital of France?", "answer": "Paris"},
    {"question": "What is the square root of 16?", "answer": "4"}
]

user_scores = {}  # Menyimpan status kuis pengguna

# Fungsi untuk memulai bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the Quiz Bot! Type /quiz to start the quiz.")

# Fungsi untuk memulai kuis
def quiz(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    user_scores[user] = {"current_question": 0, "score": 0}
    ask_question(update, user)

# Fungsi untuk menanyakan soal
def ask_question(update: Update, user):
    question_idx = user_scores[user]["current_question"]
    if question_idx < len(questions):
        question = questions[question_idx]["question"]
        update.message.reply_text(f"Question {question_idx + 1}: {question}")
    else:
        score = user_scores[user]["score"]
        save_score(user, score)
        update.message.reply_text(f"Quiz completed! Your score: {score}")
        user_scores.pop(user, None)

# Fungsi untuk memeriksa jawaban pengguna
def answer(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    if user not in user_scores:
        update.message.reply_text("Start the quiz first using /quiz.")
        return

    user_data = user_scores[user]
    question_idx = user_data["current_question"]
    user_answer = update.message.text.strip()
    correct_answer = questions[question_idx]["answer"]

    if user_answer.lower() == correct_answer.lower():
        user_data["score"] += 1

    user_data["current_question"] += 1
    ask_question(update, user)

# Fungsi untuk menyimpan skor ke database
def save_score(username, score):
    cursor.execute("INSERT INTO participants (username, score) VALUES (?, ?)", (username, score))
    db.commit()

# Fungsi untuk membuat laporan PDF
def report(update: Update, context: CallbackContext):
    cursor.execute("SELECT * FROM participants")
    results = cursor.fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Quiz Report", ln=True, align="C")

    for row in results:
        pdf.cell(200, 10, txt=f"Username: {row[1]}, Score: {row[2]}, Date: {row[3]}", ln=True)

    pdf_file = "quiz_report.pdf"
    pdf.output(pdf_file)

    update.message.reply_document(open(pdf_file, "rb"))

# Fungsi utama
def main():
    updater = Updater("YOUR_BOT_API_TOKEN", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("quiz", quiz))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, answer))
    dp.add_handler(CommandHandler("report", report))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
