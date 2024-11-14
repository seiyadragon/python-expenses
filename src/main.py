import tkinter as tk
from tkinter import ttk
import nltk
import datetime
import re
import dateparser
import json
import os

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Python Expenses Tracker")
        self.geometry("800x600")

        self.table = ttk.Treeview(self, columns=("Date", "Description", "Amount"), show='headings', height=20)
        self.table.heading("Date", text="Date")
        self.table.heading("Description", text="Description")
        self.table.heading("Amount", text="Amount")
        self.table.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Create an Entry widget for typing messages
        self.message_entry = tk.Entry(self, width=80)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.message_entry.pack(pady=0, padx=10, fill=tk.X, expand=True, side=tk.BOTTOM)

        # Load the language model
        nltk.download("all")
        self.language_model = nltk.data.load("tokenizers/punkt/english.pickle")

        # Load the data from the JSON file
        self.load_json_data()

    def send_message(self):
        message = self.message_entry.get()
        if message:
            date, description, amount = self.interpret_message(message)
            self.add_expense(date, description, amount)
            self.save_to_json(date, description, amount)

            self.message_entry.delete(0, tk.END)

    def add_expense(self, date, description, amount):
        self.table.insert("", tk.END, values=(date, description, amount))

    def parse_date(self, tokens):
        last_token = tokens[0]
        parsed_value = None
        parsed_date = None

        for token in tokens:
            parsed_value = token
            date = dateparser.parse(token)
            
            if token.isdigit() and len(token) < 4:
                continue

            if str(token).casefold() == "last.".casefold() or str(token).casefold() == "next".casefold() or str(token).casefold() == "this".casefold():
                last_token = token
                continue

            if str(last_token).casefold() == "last".casefold() or str(last_token).casefold() == "next".casefold() or str(last_token).casefold() == "this".casefold():
                parsed_value = last_token + " " + token
                date = dateparser.parse(last_token + " " + token)

            if date:
                parsed_date = date.strftime('%Y-%m-%d')
                break

            print(parsed_value, date)

        print(parsed_date, parsed_value)

        if parsed_date:
            return parsed_date, parsed_value

        return None, None

    def interpret_message(self, message):
        tokens = nltk.word_tokenize(message)
        tagged = nltk.pos_tag(tokens)
        entities = nltk.ne_chunk(tagged)

        date_value, parsed_date_value = self.parse_date(tokens)
        description = []
        amount = None

        for subtree in entities:
            if isinstance(subtree, nltk.Tree):
                if subtree.label() == 'DATE':
                    date_value = " ".join([token for token, pos in subtree.leaves()])
                elif subtree.label() == 'MONEY':
                    amount = " ".join([token for token, pos in subtree.leaves()])
            else:
                description.append(subtree[0])

        description = " ".join(description)

        # Use today's date if no date is found
        if not date_value:
            date_value = datetime.date.today().strftime('%Y-%m-%d')

        # Try to extract amount if not found by NLTK
        if not amount:
            amount_match = re.search(r'\d+(\.\d{2})?', message)
            if amount_match:
                amount = amount_match.group()

        # If no amount is found, set a default value
        if not amount:
            amount = "0.00"

        # Heuristic to improve description extraction
        if date_value and date_value in description:
            description = description.replace(date_value, "").strip()

        if amount and amount in description:
            description = description.replace(amount, "").strip()
            
        if parsed_date_value and parsed_date_value in description:
            description = description.replace(parsed_date_value, "").strip()

        no_no_pharses = [
            "$",
            "for $",
            "dollars",
            "dollar",
            "paid",
            "i",
            "spent",
            "sent"
        ]

        for phrase in no_no_pharses:
            description = description.replace(phrase.casefold(), "").strip()

        no_no_pharses_at_end_or_start = [
            "on",
            "for",
            "to"
        ]

        for phrase in no_no_pharses_at_end_or_start:
            if description.startswith(phrase):
                description = description[len(phrase):].strip()
            if description.endswith(phrase):
                description = description[:-len(phrase)].strip()

        return date_value, description, amount

    def load_json_data(self):
        file_path = "expenses.json"
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump([], file)

        with open(file_path, 'r') as file:
            data = json.load(file)
            for entry in data:
                self.add_expense(entry["date"], entry["description"], entry["amount"])

    def save_to_json(self, date, description, amount):
        file_path = "expenses.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
        else:
            data = []

        data.append({"date": date, "description": description, "amount": amount})

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()