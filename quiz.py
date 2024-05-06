import tkinter as tk
from tkinter import messagebox
import mysql.connector

class Quiz:
    def __init__(self, questions, username):
        self.questions = questions
        self.current_question = 0
        self.score = 0
        self.username = username

    def check_answer(self, choice):
        correct_answer = self.questions[self.current_question]["answer"]
        if choice == correct_answer:
            self.score += 1
            messagebox.showinfo("Correct", "Your answer is correct!")
        else:
            messagebox.showinfo("Incorrect", "Your answer is incorrect!")

        self.current_question += 1
        if self.current_question < len(self.questions):
            self.display_question()
        else:
            self.save_score_to_database()
            self.display_score()

    def display_question(self):
        question = self.questions[self.current_question]["question"]
        choices = self.questions[self.current_question]["choices"]

        question_label.config(text=question)
        for i, choice in enumerate(choices):
            choice_buttons[i].config(text=choice)

    def save_score_to_database(self):
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="quiz"
        )
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS Scores (username VARCHAR(255), score INT)")
        cursor.execute("INSERT INTO Scores (username, score) VALUES (%s, %s)", (self.username, self.score))
        conn.commit()
        conn.close()

    def display_score(self):
        messagebox.showinfo("Quiz completed", f"Hello {self.username}!\nYour score: {self.score}/{len(self.questions)}")
        root.destroy()

def see_highest_scores():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="quiz"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT username, score FROM Scores WHERE score = (SELECT MAX(score) FROM Scores)")
    results = cursor.fetchall()
    if results:
        highest_scores_info = "\n".join(f"{username}: {score}" for username, score in results)
        messagebox.showinfo("Top Highest Scores", highest_scores_info)
    else:
        messagebox.showinfo("Top Highest Scores", "No scores recorded yet.")
    conn.close()

def start_quiz():
    username = username_entry.get()
    if username.strip() == "":
        messagebox.showwarning("Warning", "Please enter a username.")
    else:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="quiz"
            )
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Scores (username, score) VALUES (%s, 0)", (username,))
            conn.commit()

            # Retrieve quiz questions from the database
            cursor.execute("SELECT * FROM Questions")
            questions_data = cursor.fetchall()
            questions = [{"question": data[1], "choices": data[2].split(','), "answer": data[3]} for data in questions_data]

            conn.close()

            username_entry.config(state="disabled")
            quiz = Quiz(questions, username)
            quiz.display_question()
            for i, button in enumerate(choice_buttons):
                button.config(command=lambda i=i: quiz.check_answer(questions[quiz.current_question]["choices"][i]))
        except mysql.connector.IntegrityError:
            messagebox.showwarning("Warning", "Username already used.")

# Create the quiz window
root = tk.Tk()
root.title("Quiz Game")

# Username Entry
username_label = tk.Label(root, text="Enter your username:")
username_label.pack(pady=10)
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

# Start Button
start_button = tk.Button(root, text="Start Quiz", command=start_quiz)
start_button.pack(pady=5)

# See Highest Scores Button
highest_scores_button = tk.Button(root, text="See the top highest scores", command=see_highest_scores)
highest_scores_button.pack(pady=5)

# Create question label
question_label = tk.Label(root, text="", font=("Helvetica", 16), wraplength=400)
question_label.pack(pady=20)

# Create choice buttons
choice_buttons = []
for _ in range(4):  # Assuming there are always 4 choices for each question
    button = tk.Button(root, text="", font=("Helvetica", 12), width=30)
    choice_buttons.append(button)
    button.pack(pady=5)

# Run the main event loop
root.mainloop()