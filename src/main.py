import sys
import tkinter as tk
from tkinter import ttk
import nltk
import datetime
import re
import dateparser
import json
import os
import threading
import pandas as pd
from tkinter import filedialog

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Set the ttk theme to use the default theme
        self.style = ttk.Style(self)
        self.available_themes = self.style.theme_names()

        # Set the theme based on the platform
        self.selected_theme_map = {theme: index for index, theme in enumerate(self.available_themes)}
        self.selected_theme_value = tk.IntVar(self)
        self.selected_theme_value.set(self.selected_theme_map.get("default"))

        if sys.platform == "win32":
            self.style.theme_use("xpnative")
            self.selected_theme_value.set(self.selected_theme_map.get("xpnative"))
        elif sys.platform == "darwin":
            self.style.theme_use("aqua")
            self.selected_theme_value.set(self.selected_theme_map.get("aqua"))
        else:
            self.style.theme_use("clam")
            self.selected_theme_value.set(self.selected_theme_map.get("clam"))

        # Load the NLTK data in a separate thread
        self.loading_thread = threading.Thread(target=self.load_nltk_data)
        self.loading_thread.start()

        self.title("Python Expenses Tracker")
        self.geometry("1600x900")

        self.loading_label = ttk.Label(self, text="Loading NLTK data: ")
        self.loading_value = 0.0
        self.loading_start = datetime.datetime.now()

        self.loader_spinner = ttk.Progressbar(self, mode="indeterminate")

        # Wait for the thread to finish
        while self.loading_thread.is_alive():
            self.loading_value = (datetime.datetime.now() - self.loading_start).total_seconds()
            self.loader_spinner.pack(pady=10, padx=100, fill=tk.X, expand=True)
            self.loading_label.pack(pady=10, padx=10)
            self.loading_label.config(text="Loading NLTK data: {:.2f} seconds".format(self.loading_value))
            self.loader_spinner.step(0.1)
            self.update()

        self.loading_label.destroy()
        self.loader_spinner.destroy()
        self.total_loading_time = (datetime.datetime.now() - self.loading_start).total_seconds()

        print("NLTK data loaded in {:.2f} seconds".format(self.total_loading_time))
        
        # Create a menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # Add a "File" menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Add "Exit" option to the "File" menu
        self.file_menu.add_command(label="Exit", command=self.quit)

        # Add a "Export to Excel" option to the "File" menu
        self.file_menu.add_command(label="Export to Excel", command=lambda: self.export_to_excel())

        # Add a "Export to CSV" option to the "File" menu
        self.file_menu.add_command(label="Export to CSV", command=lambda: self.export_to_csv())

        # Add a "Themes" menu
        self.themes_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Theme", menu=self.themes_menu)

        # Add theme options to the "Themes" menu
        for index, theme in enumerate(self.available_themes):
            self.themes_menu.add_radiobutton(label=theme, command=lambda theme=theme: self.change_theme(theme), value=index, var=self.selected_theme_value)

        self.title_label = ttk.Label(self, text="Total expenses")
        self.title_label.pack(pady=10, padx=10, fill=tk.BOTH, side=tk.TOP)

        self.table = ttk.Treeview(self, columns=("Date", "Description", "Amount"), show="headings")
        self.table.heading("Date", text="Date")
        self.table.heading("Description", text="Description")
        self.table.heading("Amount", text="Amount")
        self.table.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.table, orient="vertical", command=self.table.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.table.configure(yscrollcommand=self.scrollbar.set)

        self.top_frame = tk.Frame(self)
        self.top_frame.pack(pady=10, padx=10, fill=tk.X)

        self.total_expense_value = 0.0
        self.total_label = ttk.Label(self.top_frame, text="Total expenses: ${:.2f}".format(self.total_expense_value))
        self.total_label.pack(pady=10, padx=10, fill=tk.X, side=tk.RIGHT, expand=True)

        self.middle_frame = tk.Frame(self)
        self.middle_frame.pack(pady=10, padx=10, fill=tk.X)

        self.daily_button = ttk.Button(self.middle_frame, text="Daily", command=self.display_daily_expenses)
        self.daily_button.pack(pady=10, padx=10, side=tk.LEFT)

        self.weekly_button = ttk.Button(self.middle_frame, text="Weekly", command=self.display_weekly_expenses)
        self.weekly_button.pack(pady=10, padx=10, side=tk.LEFT)

        self.monthly_button = ttk.Button(self.middle_frame, text="Monthly", command=self.display_monthly_expenses)
        self.monthly_button.pack(pady=10, padx=10, side=tk.LEFT)

        self.yearly_button = ttk.Button(self.middle_frame, text="Yearly", command=self.display_yearly_expenses)
        self.yearly_button.pack(pady=10, padx=10, side=tk.LEFT)

        self.all_button = ttk.Button(self.middle_frame, text="All", command=self.display_all_expenses)
        self.all_button.pack(pady=10, padx=10, side=tk.LEFT)

        self.from_label = ttk.Label(self.middle_frame, text="From:")
        self.from_label.pack(pady=10, padx=10, side=tk.LEFT)
        self.from_date_entry = ttk.Entry(self.middle_frame, width=10)
        self.from_date_entry.pack(pady=10, padx=10, side=tk.LEFT)

        self.to_label = ttk.Label(self.middle_frame, text="To:")
        self.to_label.pack(pady=10, padx=10, side=tk.LEFT)
        self.to_date_entry = ttk.Entry(self.middle_frame, width=10)
        self.to_date_entry.pack(pady=10, padx=10, side=tk.LEFT)
        
        self.date_range_button = ttk.Button(self.middle_frame, text="Date range", command=lambda: self.display_date_range_expenses(dateparser.parse(self.from_date_entry.get()), dateparser.parse(self.to_date_entry.get())))
        self.date_range_button.pack(pady=10, padx=10, side=tk.LEFT)

        self.remove_button = ttk.Button(self.middle_frame, text="Remove", command=self.remove_selected_expenses)
        self.remove_button.pack(pady=10, padx=10, side=tk.RIGHT)

        self.display_deleted_button = ttk.Button(self.middle_frame, text="Deleted", command=self.display_deleted_expenses)
        self.display_deleted_button.pack(pady=10, padx=10, side=tk.RIGHT)

        for expense in self.load_json_data():
            self.add_expense(expense["date"], expense["description"], expense["amount"])

        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(pady=10, padx=10, fill=tk.X)

        self.message_label = ttk.Label(self.bottom_frame, text="Type your expense message below")
        self.message_label.pack(pady=10, padx=10, fill=tk.X, side=tk.TOP)

        # Create an Entry widget for typing messages
        self.message_entry = ttk.Entry(self.bottom_frame, width=180)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.message_entry.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM, expand=True)

        self.display_all_expenses()

    def quit(self):
        super().quit()

    def save_file_as(self, extension, file_types):
        return filedialog.asksaveasfilename(defaultextension=extension, filetypes=file_types)

    def export_to_excel(self):
        row_list = []
        columns = ('Date', 'Description', 'Amount')
        for row in self.table.get_children():
            row_list.append(self.table.item(row)["values"])

        treeview_df = pd.DataFrame(row_list, columns = columns)
        treeview_df.to_excel(self.save_file_as("xlsx", [("Excel", "*.xlsx")]), index=False)

    def export_to_csv(self):
        row_list = []
        columns = ('Date', 'Description', 'Amount')
        for row in self.table.get_children():
            row_list.append(self.table.item(row)["values"])

        treeview_df = pd.DataFrame(row_list, columns = columns)
        treeview_df.to_csv(self.save_file_as("csv", [("CSV", "*.csv")]), index=False)

    def change_theme(self, theme_name):
        """Change the ttk theme."""
        self.style.theme_use(theme_name)
        self.selected_theme_value.set(self.selected_theme_map.get(theme_name))

    def clear_data_from_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

    def display_daily_expenses(self):
        self.clear_data_from_table()
        self.title_label.config(text="Daily expenses")
        self.displaying_deleted = False

        total_expense = 0.0
        for expense in self.load_json_data():
            if expense["date"] == datetime.date.today().strftime('%Y-%m-%d'):
                self.add_expense(expense["date"], expense["description"], expense["amount"])
                total_expense += float(expense["amount"])

        self.update_total_expense(total_expense)
        self.update_delete_button()

    def display_date_range_expenses(self, start_date, end_date):
        self.clear_data_from_table()
        self.title_label.config(text="Date range expenses")
        self.displaying_deleted = False

        total_expense = 0.0
        for expense in self.load_json_data():
            date = dateparser.parse(expense["date"])
            if date >= start_date and date <= end_date:
                self.add_expense(expense["date"], expense["description"], expense["amount"])
                total_expense += float(expense["amount"])

        self.update_total_expense(total_expense)
        self.update_delete_button()

    def display_weekly_expenses(self):
        self.clear_data_from_table()
        self.title_label.config(text="Weekly expenses")
        self.displaying_deleted = False

        total_expense = 0.0
        for expense in self.load_json_data():
            date = dateparser.parse(expense["date"])
            if date.isocalendar()[1] == datetime.date.today().isocalendar()[1]:
                self.add_expense(expense["date"], expense["description"], expense["amount"])
                total_expense += float(expense["amount"])

        self.update_total_expense(total_expense)
        self.update_delete_button()

    def display_monthly_expenses(self):
        self.clear_data_from_table()
        self.title_label.config(text="Monthly expenses")
        self.displaying_deleted = False

        total_expense = 0.0
        for expense in self.load_json_data():
            date = dateparser.parse(expense["date"])
            if date.month == datetime.date.today().month:
                self.add_expense(expense["date"], expense["description"], expense["amount"])
                total_expense += float(expense["amount"])

        self.update_total_expense(total_expense)
        self.update_delete_button()

    def display_yearly_expenses(self):
        self.clear_data_from_table()
        self.title_label.config(text="Yearly expenses")
        self.displaying_deleted = False

        total_expense = 0.0
        for expense in self.load_json_data():
            date = dateparser.parse(expense["date"])
            if date.year == datetime.date.today().year:
                self.add_expense(expense["date"], expense["description"], expense["amount"])
                total_expense += float(expense["amount"])

        self.update_total_expense(total_expense)
        self.update_delete_button()

    def display_all_expenses(self):
        self.clear_data_from_table()
        self.title_label.config(text="Total expenses")
        self.displaying_deleted = False

        total_expense = 0.0
        for expense in self.load_json_data():
            self.add_expense(expense["date"], expense["description"], expense["amount"])
            total_expense += float(expense["amount"])

        self.update_total_expense(total_expense)
        self.update_delete_button()

    def display_deleted_expenses(self):
        self.clear_data_from_table()
        self.title_label.config(text="Deleted expenses")
        self.displaying_deleted = True

        print("Deleted expenses")

        total_expense = 0.0
        for expense in self.load_deleted_json_data():
            #if expense["deleted"] == True:
            self.add_expense(expense["date"], expense["description"], expense["amount"])
            total_expense += float(expense["amount"])

        self.update_total_expense(total_expense)
        self.update_delete_button()

    def update_delete_button(self):
        if self.displaying_deleted:
            self.remove_button.config(text="Restore selected", command=self.restore_selected_expenses)
        else:
            self.remove_button.config(text="Remove selected", command=self.remove_selected_expenses)

    def load_nltk_data(self):
        # Download the NLTK data
        nltk.download("all")
        self.language_model = nltk.data.load("tokenizers/punkt/english.pickle")

    def send_message(self):
        message = self.message_entry.get()
        if message:
            date, description, amount = self.interpret_message(message)
            self.add_expense(date, description, amount)
            self.save_to_json(date, description, amount)

            self.message_entry.delete(0, tk.END)

    def update_total_expense(self, amount):
        self.total_expense_value = float(amount)
        self.total_label.config(text="Total expenses: ${:.2f}".format(self.total_expense_value))

    def add_expense(self, date, description, amount):
        self.table.insert("", tk.END, values=(date, description, amount))
        self.update_total_expense(self.total_expense_value + float(amount))

    def remove_selected_expenses(self):
        for selected_item in self.table.selection():
            date = self.table.item(selected_item)["values"][0]
            description = self.table.item(selected_item)["values"][1]
            amount = self.table.item(selected_item)["values"][2]

            self.remove_from_json(date, description, amount)
            self.table.delete(selected_item)
            self.update_total_expense(self.total_expense_value - float(amount))

    def restore_selected_expenses(self):
        for selected_item in self.table.selection():
            date = self.table.item(selected_item)["values"][0]
            description = self.table.item(selected_item)["values"][1]
            amount = self.table.item(selected_item)["values"][2]

            self.restore_deleted_from_json(date, description, amount)
            self.table.delete(selected_item)
            self.update_total_expense(self.total_expense_value - float(amount))

    def restore_deleted_from_json(self, date, description, amount):
        file_path = "expenses.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
        else:
            print("No data to restore")
            return
        
        for index, expense in enumerate(data):
            if expense["date"] == str(date) and expense["description"] == str(description) and expense["amount"] == str(amount):
                data[index]["deleted"] = False
                break

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def remove_from_json(self, date, description, amount):
        file_path = "expenses.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
        else:
            print("No data to remove")
            return
        
        for index, expense in enumerate(data):
            if expense["date"] == str(date) and expense["description"] == str(description) and expense["amount"] == str(amount):
                data[index]["deleted"] = True
                break

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def parse_date(self, tokens):
        parsed_value = None
        parsed_date = None

        new_tokens = []
        for token in tokens:
            if token == "last" or token == "next" or token == "this":
                token = token + " " + tokens[tokens.index(token) + 1]
            
            new_tokens.append(token)

        for token in new_tokens:
            parsed_value = token

            if token == "last night":
                token = "yesterday"

            date = dateparser.parse(token)

            print(token, date)
            
            if token.isdigit() and len(token) < 4:
                continue

            if token.isdigit() and (int(token) < 1900 or int(token) > 2100):
                continue

            #if token.contains("paid") or token.contains("spent") or token.contains("sent"):
            #    continue

            if date:
                if token == "I" or token == "spent" or token == "paid" or token == "sent" or token == "bar":
                    continue

                parsed_date = date.strftime('%Y-%m-%d')
                break

            print(parsed_value, date)

        print(parsed_date, parsed_value)

        if parsed_date:
            print(parsed_date, parsed_value)
            return parsed_date, parsed_value

        print(None, None)
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
            "I spent",
            "I paid",
            "I sent",
            "I paid for",
            "I spent for",
            "I sent for",
            "I paid $",
            "I spent $",
            "I sent $",
            "I paid for $",
            "I spent on",
            "I sent on",
            "I paid on",
            "$",
            "for $",
            "dollars",
            "dollar",
            "paid",
            "spent",
            "sent",
        ]

        for phrase in no_no_pharses:
            description = description.replace(phrase.casefold(), "").strip()

        no_no_pharses_at_end_or_start = [
            "on",
            "for",
            "to",
            "I",
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

        new_data = []
        for entry in data:
            if entry["deleted"] == False:
                new_data.append(entry)
        
        return new_data
    
    def load_deleted_json_data(self):
        file_path = "expenses.json"
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump([], file)

        with open(file_path, 'r') as file:
            data = json.load(file)

        new_data = []
        for entry in data:
            if entry["deleted"] == True:
                new_data.append(entry)

        return new_data

    def save_to_json(self, date, description, amount):
        file_path = "expenses.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
        else:
            data = []

            with open(file_path, 'w') as file:
                json.dump([], file)

        data.append({"date": date, "description": description, "amount": amount, "deleted": False})

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()