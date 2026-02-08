import urllib.request
import json
import html
import random
import sys
import argparse
import tkinter as tk
from tkinter import messagebox


def fetch_gk_questions(amount=10):
	url = f"https://opentdb.com/api.php?amount={amount}&category=9&type=multiple"
	with urllib.request.urlopen(url, timeout=10) as resp:
		data = json.loads(resp.read().decode())

	if data.get("response_code") != 0:
		raise RuntimeError("OpenTDB returned an error or no questions available")

	questions = []
	for item in data["results"]:
		q = html.unescape(item["question"])
		correct = html.unescape(item["correct_answer"])
		incorrect = [html.unescape(i) for i in item["incorrect_answers"]]
		choices = incorrect + [correct]
		random.shuffle(choices)
		questions.append({
			"question": q,
			"choices": choices,
			"answer": correct,
		})

	return questions


def save_json(questions, filename="questions.json"):
	with open(filename, "w", encoding="utf8") as f:
		json.dump(questions, f, ensure_ascii=False, indent=2)


def run_quiz(questions, auto=False):
	results = []
	for i, q in enumerate(questions, start=1):
		print(f"{i}. {q['question']}")
		for idx, choice in enumerate(q["choices"]):
			print(f"   {chr(65+idx)}. {choice}")

		if auto:
			print(f"(Auto) Correct answer: {q['answer']}\n")
			results.append({"question": q["question"], "user": None, "correct": q["answer"], "correct_bool": False})
			continue

		while True:
			ans = input("Your answer (A-D), 'show' to reveal, Enter to skip: ").strip()
			if ans == "":
				print("-- skipped --\n")
				results.append({"question": q["question"], "user": None, "correct": q["answer"], "correct_bool": False})
				break
			if ans.lower() == "show":
				print(f"Answer: {q['answer']}\n")
				results.append({"question": q["question"], "user": None, "correct": q["answer"], "correct_bool": False})
				break
			if len(ans) >= 1 and ans[0].upper() in "ABCD":
				idx = ord(ans[0].upper()) - 65
				if 0 <= idx < len(q["choices"]):
					user_choice = q["choices"][idx]
					correct_bool = user_choice == q["answer"]
					results.append({"question": q["question"], "user": user_choice, "correct": q["answer"], "correct_bool": correct_bool})
					print("Correct!\n" if correct_bool else "Incorrect.\n")
					break
			print("Invalid input. Try again.")

	# Summary
	correct_count = sum(1 for r in results if r["user"] is not None and r["correct_bool"])
	total_answered = sum(1 for r in results if r["user"] is not None)
	print("=== Quiz Summary ===")
	print(f"Total questions: {len(results)}")
	print(f"Answered: {total_answered}")
	print(f"Correct: {correct_count}\n")

	for i, r in enumerate(results, start=1):
		user = r["user"] if r["user"] is not None else "(no answer/revealed)"
		print(f"{i}. {r['question']}")
		print(f"   Your answer: {user}")
		print(f"   Correct answer: {r['correct']}\n")


class QuizGUI:
	def __init__(self, root, questions):
		self.root = root
		self.questions = questions
		self.index = 0
		self.results = []

		self.root.title("GK Quiz")
		self.question_var = tk.StringVar()
		self.choice_var = tk.StringVar()

		self.question_label = tk.Label(root, textvariable=self.question_var, wraplength=600, justify="left")
		self.question_label.pack(padx=10, pady=10)

		self.choices_frame = tk.Frame(root)
		self.choices_frame.pack(padx=10, pady=5)

		self.choice_buttons = []
		for i in range(4):
			rb = tk.Radiobutton(self.choices_frame, text="", variable=self.choice_var, value=str(i), anchor="w", justify="left")
			rb.pack(fill="x", padx=5, pady=2)
			self.choice_buttons.append(rb)

		btn_frame = tk.Frame(root)
		btn_frame.pack(padx=10, pady=10)

		self.submit_btn = tk.Button(btn_frame, text="Submit", command=self.on_submit)
		self.submit_btn.grid(row=0, column=0, padx=5)
		self.show_btn = tk.Button(btn_frame, text="Show Answer", command=self.on_show)
		self.show_btn.grid(row=0, column=1, padx=5)
		self.next_btn = tk.Button(btn_frame, text="Next", command=self.on_next)
		self.next_btn.grid(row=0, column=2, padx=5)

		self.load_question()

	def load_question(self):
		if self.index >= len(self.questions):
			self.finish()
			return
		q = self.questions[self.index]
		self.question_var.set(f"{self.index+1}. {q['question']}")
		self.choice_var.set("")
		for i, choice in enumerate(q['choices']):
			if i < len(self.choice_buttons):
				self.choice_buttons[i].config(text=f"{chr(65+i)}. {choice}", state="normal")
			else:
				# ignore extra choices
				pass
		# hide any unused buttons
		for j in range(len(q['choices']), len(self.choice_buttons)):
			self.choice_buttons[j].config(text="", state="disabled")

	def on_submit(self):
		q = self.questions[self.index]
		val = self.choice_var.get()
		if val == "":
			messagebox.showinfo("No answer", "Please select an option or click Show Answer to reveal.")
			return
		idx = int(val)
		user_choice = q['choices'][idx]
		correct_bool = user_choice == q['answer']
		self.results.append({"question": q['question'], "user": user_choice, "correct": q['answer'], "correct_bool": correct_bool})
		messagebox.showinfo("Result", "Correct!" if correct_bool else f"Incorrect. Correct: {q['answer']}")

	def on_show(self):
		q = self.questions[self.index]
		messagebox.showinfo("Answer", f"Correct answer:\n{q['answer']}")
		self.results.append({"question": q['question'], "user": None, "correct": q['answer'], "correct_bool": False})

	def on_next(self):
		# ensure if user didn't submit or show, we count as skipped
		if len(self.results) <= self.index:
			q = self.questions[self.index]
			self.results.append({"question": q['question'], "user": None, "correct": q['answer'], "correct_bool": False})
		self.index += 1
		if self.index < len(self.questions):
			self.load_question()
		else:
			self.finish()

	def finish(self):
		correct_count = sum(1 for r in self.results if r.get('user') is not None and r.get('correct_bool'))
		answered = sum(1 for r in self.results if r.get('user') is not None)
		summary = f"Total: {len(self.results)}\nAnswered: {answered}\nCorrect: {correct_count}"
		messagebox.showinfo("Quiz Finished", summary)
		# save results
		with open('results.json', 'w', encoding='utf8') as f:
			json.dump(self.results, f, ensure_ascii=False, indent=2)
		self.root.quit()


def main():
	parser = argparse.ArgumentParser(description="Fetch GK questions and run a quiz")
	parser.add_argument("amount", nargs="?", type=int, default=10, help="Number of questions to fetch")
	parser.add_argument("--auto", action="store_true", help="Auto-show answers (non-interactive, useful for testing)")
	parser.add_argument("--gui", action="store_true", help="Run a simple GUI quiz using Tkinter")
	args = parser.parse_args()

	qs = fetch_gk_questions(args.amount)
	save_json(qs)
	print(f"Fetched {len(qs)} questions and saved to questions.json\n")
	if args.gui:
		root = tk.Tk()
		app = QuizGUI(root, qs)
		root.mainloop()
	else:
		run_quiz(qs, auto=args.auto)


if __name__ == "__main__":
	main()
