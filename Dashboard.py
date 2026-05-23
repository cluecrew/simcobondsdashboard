import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk

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
    "AAA": 60, "AA+": 56, "AA": 52, "AA-": 48,
    "A+": 44, "A": 40, "A-": 36,
    "BBB+": 32, "BBB": 28, "BBB-": 24,
    "BB+": 20, "BB": 16, "BB-": 12,
    "B+": 4, "B": 4, "B-": 4, "C": 4, "D": 4
}

DATA_FILE = "bond_data.csv"
BACKGROUND_FILE = "background.png"

# ---------------- SORTING ---------------- #

def sort_column(col, reverse=False):
    items = []

    numeric_cols = {
        "Interest Rate", "Amount", "Callable (Days)",
        "Default Rate %", "Recovery rate %", "Recovery Value ($)"
    }

    rating_order = {
        "AAA": 18, "AA+": 17, "AA": 16, "AA-": 15,
        "A+": 14, "A": 13, "A-": 12,
        "BBB+": 11, "BBB": 10, "BBB-": 9,
        "BB+": 8, "BB": 7, "BB-": 6,
        "B+": 5, "B": 4, "B-": 3,
        "C": 2, "D": 1
    }

    for row in tree.get_children():
        val = tree.set(row, col)

        if col in numeric_cols:
            clean = str(val).replace("$", "").replace(",", "").replace("%", "").strip()
            try:
                sort_val = float(clean) if clean else 0.0
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


# ---------------- LOAD ---------------- #

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
            rating_line = cleaned[i + 1].strip()

            if "(" in rating_line:
                rating = rating_line.split("(")[0].strip()
                purchase_rating = rating_line.split("(")[1].split("when")[0].strip()
            else:
                rating = rating_line.strip()
                purchase_rating = rating_line.strip()

            interest_amount = cleaned[i + 2].strip()
            callable_line = cleaned[i + 3].strip()

            try:
                interest = float(interest_amount.split("%")[0].strip())
                amount = float(interest_amount.split("$")[1].replace(",", "").strip())
            except:
                interest = 0
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
        messagebox.showerror("Parse Error", str(e))
        return

    df = pd.DataFrame(rows)

    df["Default Rate %"] = df["Rating"].map(default_rates).fillna(0)
    df["Recovery rate %"] = df["Rating at Purchase"].map(recovery_rates).fillna(0)
    df["Recovery Value ($)"] = df["Amount"] * (df["Recovery rate %"] / 100)

    refresh_table()


def auto_load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            load_csv_from_text(f.read())


# ---------------- TABLE ---------------- #

def refresh_table():
    for r in tree.get_children():
        tree.delete(r)

    for _, row in df.iterrows():
        tree.insert("", "end", values=(
            row["Company"],
            row["Rating"],
            row["Rating at Purchase"],
            f"{row['Interest Rate']:.2f}%",
            f"${row['Amount']:,.0f}",
            row["Callable (Days)"],
            f"{row['Default Rate %']:.2f}%",
            f"{row['Recovery rate %']:.2f}%",
            f"${row['Recovery Value ($)']:,.0f}"
        ))

    update_summary()


# ---------------- SUMMARY ---------------- #

def update_summary():
    total = df["Amount"].sum() if not df.empty else 0
    callable_amt = df[df["Callable (Days)"] <= 0]["Amount"].sum() if not df.empty else 0
    recovery = df["Recovery Value ($)"].sum() if not df.empty else 0
    bond_count = len(df)
    avg_bond = total / bond_count if bond_count > 0 else 0

    weighted_risk_amount = (
        (df["Default Rate %"] / 100 * (df["Amount"] - df["Recovery Value ($)"])).sum()
        if not df.empty else 0
    )

    risk_pct = (weighted_risk_amount / total * 100) if total > 0 else 0

    lbl_total.config(text=f"${total:,.0f}")
    lbl_callable.config(text=f"${callable_amt:,.0f}")
    lbl_recovery.config(text=f"${recovery:,.0f}")
    lbl_weighted_risk.config(text=f"${weighted_risk_amount:,.0f} ({risk_pct:.2f}%)")
    lbl_avg_bond.config(text=f"${avg_bond:,.0f}")
    lbl_bond_count.config(text=f"{bond_count:,}")

    buckets = {
        0: df[df["Callable (Days)"] <= 0]["Amount"].sum() if not df.empty else 0,
        1: df[df["Callable (Days)"] == 1]["Amount"].sum() if not df.empty else 0,
        2: df[df["Callable (Days)"] == 2]["Amount"].sum() if not df.empty else 0,
        3: df[df["Callable (Days)"] == 3]["Amount"].sum() if not df.empty else 0,
        4: df[df["Callable (Days)"] == 4]["Amount"].sum() if not df.empty else 0,
        5: df[df["Callable (Days)"] == 5]["Amount"].sum() if not df.empty else 0,
        6: df[df["Callable (Days)"] == 6]["Amount"].sum() if not df.empty else 0,
        7: df[df["Callable (Days)"] == 7]["Amount"].sum() if not df.empty else 0,
        14: df[df["Callable (Days)"] > 7]["Amount"].sum() if not df.empty else 0
    }

    for i, key in enumerate([0, 1, 2, 3, 4, 5, 6, 7, 14]):
        callable_day_labels[i].config(text=f"${buckets[key]:,.0f}")


def import_raw_data():
    popup = tk.Toplevel(root)
    popup.title("Paste CSV Data")
    popup.geometry("600x400")
    popup.lift()
    popup.focus_force()

    txt = tk.Text(
        popup,
        bg="#111111",
        fg="white",
        insertbackground="white",
        font=("Consolas", 10)
    )
    txt.pack(fill="both", expand=True)

    btn_frame = tk.Frame(popup, bg="#111111")
    btn_frame.pack(fill="x", pady=5)

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

    tk.Button(btn_frame, text="Save & Load Data", command=load_pasted).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancel", command=popup.destroy).pack(side="left", padx=5)

    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.protocol("WM_DELETE_WINDOW", popup.destroy)


# ---------------- UI ---------------- #

root = tk.Tk()
root.title("Bond Risk Dashboard")
root.geometry("1250x800")

# ---------------- BACKGROUND IMAGE ---------------- #

# ---------------- DYNAMIC BACKGROUND IMAGE ---------------- #

bg_label = None
bg_original = None

if os.path.exists(BACKGROUND_FILE):

    bg_original = Image.open(BACKGROUND_FILE)

    bg_label = tk.Label(root)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    def resize_background(event):
        global bg_photo

        width = max(event.width, 1)
        height = max(event.height, 1)

        resized = bg_original.resize((width, height))

        bg_photo = ImageTk.PhotoImage(resized)

        bg_label.config(image=bg_photo)

    root.bind("<Configure>", resize_background)

else:
    root.configure(bg="#111111")

df = pd.DataFrame()

# ---------------- STYLES ---------------- #

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#1b1b1b",
    foreground="white",
    fieldbackground="#1b1b1b",
    rowheight=28,
    bordercolor="#333333",
    borderwidth=0
)

style.configure(
    "Treeview.Heading",
    background="#222222",
    foreground="white",
    font=("Arial", 10, "bold")
)

style.map(
    "Treeview",
    background=[("selected", "#2a82da")]
)

# ---------------- TOP BUTTON ---------------- #

top_button_frame = tk.Frame(root, bg="#111111")
top_button_frame.pack(pady=10)

tk.Button(
    top_button_frame,
    text="Paste Raw CSV Data",
    command=import_raw_data,
    bg="#222222",
    fg="white",
    activebackground="#333333",
    activeforeground="white",
    font=("Arial", 10, "bold")
).pack()

# ---------------- KPI SUMMARY ---------------- #

frame = tk.Frame(root, bg="#111111")
frame.pack(pady=5)

metric_style = {
    "font": ("Arial", 12, "bold"),
    "bg": "#111111",
    "fg": "#00ff99"
}

lbl_total = tk.Label(frame, text="$0", **metric_style)
lbl_callable = tk.Label(frame, text="$0", **metric_style)
lbl_recovery = tk.Label(frame, text="$0", **metric_style)
lbl_avg_bond = tk.Label(frame, text="$0", **metric_style)
lbl_bond_count = tk.Label(frame, text="0", **metric_style)
lbl_weighted_risk = tk.Label(frame, text="$0", **metric_style)

for i, (t, l) in enumerate([
    ("Total Outstanding", lbl_total),
    ("Callable", lbl_callable),
    ("Recovery Value", lbl_recovery),
    ("Weighted Risk Amount", lbl_weighted_risk),
    ("Average Bond Amount", lbl_avg_bond),
    ("Total Bond Count", lbl_bond_count)
]):
    tk.Label(
        frame,
        text=t,
        bg="#111111",
        fg="white",
        font=("Arial", 10)
    ).grid(row=0, column=i, padx=20)

    l.grid(row=1, column=i, padx=20)

# ---------------- CALLABLE BREAKOUT ---------------- #

callable_day_labels = []

callable_frame = tk.Frame(root, bg="#111111")
callable_frame.pack(pady=10)

labels = [
    "Day 0", "Day 1", "Day 2", "Day 3", "Day 4",
    "Day 5", "Day 6", "~ 7 Days", "After 1 Week"
]

for i, text in enumerate(labels):
    tk.Label(
        callable_frame,
        text=text,
        bg="#111111",
        fg="white",
        font=("Arial", 9)
    ).grid(row=1, column=i, padx=10)

    lbl = tk.Label(
        callable_frame,
        text="$0",
        font=("Arial", 11, "bold"),
        bg="#111111",
        fg="#00ff99"
    )
    lbl.grid(row=2, column=i, padx=10)
    callable_day_labels.append(lbl)

# ---------------- TABLE ---------------- #

columns = [
    "Company", "Rating", "Rating at Purchase", "Interest Rate", "Amount",
    "Callable (Days)", "Default Rate %", "Recovery rate %", "Recovery Value ($)"
]

frame_table = tk.Frame(root, bg="#111111")
frame_table.pack(fill="both", expand=True, padx=20, pady=10)

tree = ttk.Treeview(frame_table, columns=columns, show="headings")

for c in columns:
    tree.heading(c, text=c, command=lambda _c=c: sort_column(_c))
    tree.column(c, width=140, anchor="center")

scroll = ttk.Scrollbar(frame_table, command=tree.yview)
tree.configure(yscrollcommand=scroll.set)

scroll.pack(side="right", fill="y")
tree.pack(fill="both", expand=True)

auto_load_data()

root.mainloop()
