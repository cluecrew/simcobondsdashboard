import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import io

# Generated using ChatGPT, customized by Meridian Markets https://www.simcompanies.com/company/0/Meridian-Markets/     #

# ---------------- RISK TABLES ---------------- #

default_rates = {
    "AAA": 3.548, "AA+": 6.975, "AA": 7.138, "AA-": 8.120,
    "A+": 8.827, "A": 10.132, "A-": 11.126,
    "BBB+": 11.753, "BBB": 12.604, "BBB-": 12.707,
    "BB+": 15.543, "BB": 19.509, "BB-": 24.997,
    "B+": 25.435, "B": 25.305, "B-": 24.342,
    "C": 31.774, "D": 36.666
}

recovery_rates = {
    "AAA": 60,
    "AA+": 56,
    "AA": 52,
    "AA-": 48,
    "A+": 44,
    "A": 40,
    "A-": 36,
    "BBB+": 32,
    "BBB": 28,
    "BBB-": 24,
    "BB+": 20,
    "BB": 16,
    "BB-": 12,
    "B+": 4,
    "B": 4,
    "B-": 4,
    "C": 4,
    "D": 4
}

DATA_FILE = "bond_data.csv"

# ---------------- SORTING ---------------- #

def sort_column(col, reverse=False):
    items = []

    numeric_cols = {
        "Interest Rate",
        "Amount",
        "Callable (Days)",
        "Default Rate %",
        "Recovery rate %",
        "Recovery Value ($)"
    }

    rating_order = {
        "AAA": 18,
        "AA+": 17,
        "AA": 16,
        "AA-": 15,
        "A+": 14,
        "A": 13,
        "A-": 12,
        "BBB+": 11,
        "BBB": 10,
        "BBB-": 9,
        "BB+": 8,
        "BB": 7,
        "BB-": 6,
        "B+": 5,
        "B": 4,
        "B-": 3,
        "C": 2,
        "D": 1
    }

    for row in tree.get_children():
        val = tree.set(row, col)

        if col in numeric_cols:
            clean = str(val).replace("$", "").replace(",", "").replace("%", "").strip()
            try:
                sort_val = float(clean) if clean != "" else 0.0
            except:
                sort_val = 0.0
        elif col in {"Rating", "Rating at Purchase"}:
            sort_val = rating_order.get(str(val).strip(), 0)
        else:
            sort_val = str(val).lower()

        items.append((sort_val, row))

    items.sort(reverse=reverse)

    for idx, (_, row) in enumerate(items):
        tree.move(row, "", idx)

    tree.heading(col, command=lambda: sort_column(col, not reverse))


# ---------------- LOAD FROM TEXT (NEW) ---------------- #

def load_csv_from_text(text_data):
    global df

    cleaned = text_data.strip().splitlines()

    def parse_callable(s):
        s = s.lower()
        if "in" not in s:
            return 0
        try:
            part = s.split("in")[-1].strip()
            if "w" in part:
                return int(part.replace("w", "")) * 7
            if "d" in part:
                return int(part.replace("d", ""))
        except:
            return 0
        return 0

    rows = []
    i = 0

    try:
        while i < len(cleaned):
            line = cleaned[i].strip()

            if not line:
                i += 1
                continue

            company = line

            if i + 1 >= len(cleaned):
                break

            rating_line = cleaned[i + 1].strip()

            if "(" in rating_line:
                rating = rating_line.split("(")[0].strip()
                purchase_rating = rating_line.split("(")[1].split("when")[0].strip()
            else:
                rating = rating_line.strip()
                purchase_rating = rating_line.strip()

            interest_amount = cleaned[i + 2].strip() if i + 2 < len(cleaned) else ""
            callable_line = cleaned[i + 3].strip() if i + 3 < len(cleaned) else ""

            try:
                interest = float(interest_amount.split("%")[0].strip())
            except:
                interest = 0

            try:
                amount = float(interest_amount.split("$")[1].replace(",", "").strip())
            except:
                amount = 0

            callable_days = parse_callable(callable_line)

            rows.append({
                "Company": company,
                "Rating": rating,
                "Rating at Purchase": purchase_rating,
                "Interest Rate": interest,
                "Amount": amount,
                "Callable (Days)": callable_days
            })

            i += 4

    except Exception as e:
        messagebox.showerror("Parse Error", f"Failed parsing structured data:{e}")
        return

    df = pd.DataFrame(rows)

    df["Default Rate %"] = df["Rating"].map(default_rates).fillna(0)
    df["Recovery rate %"] = df["Rating at Purchase"].map(recovery_rates).fillna(0)

    df["Recovery Value ($)"] = df["Amount"] * (df["Recovery rate %"] / 100)

    refresh_table()


# ---------------- PASTE IMPORT (NEW UX) ---------------- #

def import_raw_data():
    popup = tk.Toplevel(root)
    popup.title("Paste CSV Data")
    popup.geometry("600x400")
    popup.lift()
    popup.focus_force()

    txt = tk.Text(popup)
    txt.pack(fill="both", expand=True)

    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=5)

    def load_pasted():
        try:
            data = txt.get("1.0", tk.END).strip()

            if not data:
                messagebox.showwarning("Empty", "No data pasted.")
                return

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                f.write(data)

            load_csv_from_text(data)

            popup.destroy()
            messagebox.showinfo("Success", "Data imported and saved successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def close_popup():
        popup.destroy()

    # Buttons (explicit save button label)
    tk.Button(btn_frame, text="Save & Load Data", command=load_pasted).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancel", command=close_popup).pack(side="left", padx=5)

    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.protocol("WM_DELETE_WINDOW", close_popup)


def auto_load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                load_csv_from_text(f.read())
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to auto-load data: {e}")


# ---------------- TABLE REFRESH ---------------- #

def refresh_table():
    for r in tree.get_children():
        tree.delete(r)

    for _, row in df.iterrows():
        tree.insert("", "end", values=(
            row["Company"],
            row["Rating"],
            row["Rating at Purchase"],
            row["Interest Rate"],
            f"{row['Amount']:,.0f}",
            row["Callable (Days)"],
            f"{row['Default Rate %']:.2f}%",
            f"{row['Recovery rate %']:.2f}%",
            f"${row['Recovery Value ($)']:,.0f}"
        ))

    update_summary()


# ---------------- SUMMARY ---------------- #

def update_summary():
    total = df["Amount"].sum()
    callable_amt = df[df["Callable (Days)"] <= 0]["Amount"].sum()
    recovery = df["Recovery Value ($)"].sum()
    bond_count = len(df)
    avg_bond = total / bond_count if bond_count > 0 else 0

    lbl_total.config(text=f"${total:,.0f}")
    lbl_callable.config(text=f"${callable_amt:,.0f}")
    lbl_recovery.config(text=f"${recovery:,.0f}")
    lbl_avg_bond.config(text=f"${avg_bond:,.0f}")
    lbl_bond_count.config(text=f"{bond_count:,}")


# ---------------- UI ---------------- #

root = tk.Tk()
root.title("Bond Risk Dashboard (Paste Import Mode)")
root.geometry("1250x750")

df = pd.DataFrame()

columns = [
    "Company",
    "Rating",
    "Rating at Purchase",
    "Interest Rate",
    "Amount",
    "Callable (Days)",
    "Default Rate %",
    "Recovery rate %",
    "Recovery Value ($)"
]

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Paste Raw CSV Data", command=import_raw_data).pack()

frame = tk.Frame(root)
frame.pack()

lbl_total = tk.Label(frame, text="$0", font=("Arial", 12, "bold"))
lbl_callable = tk.Label(frame, text="$0", font=("Arial", 12, "bold"))
lbl_recovery = tk.Label(frame, text="$0", font=("Arial", 12, "bold"))
lbl_avg_bond = tk.Label(frame, text="$0", font=("Arial", 12, "bold"))
lbl_bond_count = tk.Label(frame, text="0", font=("Arial", 12, "bold"))

for i, (t, l) in enumerate([
    ("Total Outstanding", lbl_total),
    ("Callable", lbl_callable),
    ("Recovery Value", lbl_recovery),
    ("Average Bond Amount", lbl_avg_bond),
    ("Total Bond Count", lbl_bond_count)
]):
    tk.Label(frame, text=t).grid(row=0, column=i, padx=20)
    l.grid(row=1, column=i, padx=20)

frame_table = tk.Frame(root)
frame_table.pack(fill="both", expand=True)

tree = ttk.Treeview(frame_table, columns=columns, show="headings")

for c in columns:
    tree.heading(c, text=c, command=lambda _c=c: sort_column(_c))
    tree.column(c, width=150, anchor="center")

scroll = ttk.Scrollbar(frame_table, command=tree.yview)
tree.configure(yscrollcommand=scroll.set)

scroll.pack(side="right", fill="y")
tree.pack(fill="both", expand=True)

auto_load_data()

root.mainloop()
