import tkinter as tk
from tkinter import simpledialog, scrolledtext, filedialog, messagebox
import os
from models import DataManager, Book

class BookEditDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, initial=None):
        self.initial = initial
        self.cover_path = initial[4] if initial and len(initial) > 4 else ""
        super().__init__(parent, title=title)

    def select_cover(self):
        filetypes = (('Image files', '*.jpg *.jpeg *.png'), ('All files', '*.*'))
        filepath = filedialog.askopenfilename(title="Select Book Cover", initialdir=os.getcwd(), filetypes=filetypes)
        if filepath:
            self.cover_path = filepath

    def body(self, master):
        tk.Label(master, text="Title:").grid(row=0, column=0, sticky="w")
        self.title_var = tk.Entry(master, width=60)
        self.title_var.grid(row=0, column=1, pady=4, columnspan=2)
        tk.Label(master, text="Author:").grid(row=1, column=0, sticky="w")
        self.author_var = tk.Entry(master, width=60)
        self.author_var.grid(row=1, column=1, pady=4, columnspan=2)
        tk.Label(master, text="Price:").grid(row=2, column=0, sticky="w")
        self.price_var = tk.Entry(master, width=20)
        self.price_var.grid(row=2, column=1, sticky="w", pady=4, columnspan=2)
        tk.Label(master, text="Description:").grid(row=3, column=0, sticky="nw")
        self.desc_text = scrolledtext.ScrolledText(master, width=60, height=8)
        self.desc_text.grid(row=3, column=1, pady=4, columnspan=2)

        tk.Label(master, text="Cover Photo:").grid(row=4, column=0, sticky="w")
        self.select_btn = tk.Button(master, text="Select Cover File", command=self.select_cover)
        self.select_btn.grid(row=4, column=1, sticky="w", pady=4, columnspan=2)

        if self.initial:
            title, author, price, desc, cover_path = self.initial
            self.title_var.insert(0, title)
            self.author_var.insert(0, author)
            self.price_var.insert(0, price)
            self.desc_text.insert("1.0", desc)
            if cover_path: self.cover_path = cover_path
        return self.title_var

    def apply(self):
        title, author, price = self.title_var.get().strip(), self.author_var.get().strip(), self.price_var.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        if not title or not author or not price:
            messagebox.showerror("Invalid", "Title, author, and price are required.")
            self.result = None
            return
        self.result = (title, author, price, description, self.cover_path)

class AdminPanel:
    def __init__(self, dm: DataManager, parent, refresh_callback=None):
        self.dm = dm
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.win = tk.Toplevel(parent)
        self.win.title("Admin Panel")
        self.win.geometry("920x600")
        self.win.configure(bg="#0a0a23")
        self.win.minsize(820, 520)

        left = tk.Frame(self.win, bg="#1e1e3f")
        left.place(relx=0.01, rely=0.01, relwidth=0.48, relheight=0.98)
        tk.Label(left, text="Books Management", fg="white", bg="#1e1e3f", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.books_listbox = tk.Listbox(left, bg="#2a2a4a", fg="white", selectbackground="#4a90e2")
        self.books_listbox.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        
        book_btn_frame = tk.Frame(left, bg="#1e1e3f")
        book_btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(book_btn_frame, text="Add Book", command=self.add_book_dialog, bg="#2ecc71", fg="white").pack(side="left", padx=6)
        tk.Button(book_btn_frame, text="Edit Selected", command=self.edit_book_dialog, bg="#4a90e2", fg="white").pack(side="left", padx=6)
        tk.Button(book_btn_frame, text="Delete Selected", command=self.delete_selected_book, bg="#e74c3c", fg="white").pack(side="left", padx=6)

        right = tk.Frame(self.win, bg="#1e1e3f")
        right.place(relx=0.50, rely=0.01, relwidth=0.49, relheight=0.98)
        tk.Label(right, text="Registered Users", fg="white", bg="#1e1e3f", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.users_listbox = tk.Listbox(right, height=6, bg="#2a2a4a", fg="white", selectbackground="#4a90e2")
        self.users_listbox.pack(fill="x", padx=8, pady=(4, 8))
        
        user_btn_frame = tk.Frame(right, bg="#1e1e3f")
        user_btn_frame.pack(fill="x", padx=8)
        tk.Button(user_btn_frame, text="Block", command=self.block_selected_user, bg="#f39c12", fg="white").pack(side="left", padx=4)
        tk.Button(user_btn_frame, text="Unblock", command=self.unblock_selected_user, bg="#27ae60", fg="white").pack(side="left", padx=4)
        tk.Button(user_btn_frame, text="Delete", command=self.delete_selected_user, bg="#e74c3c", fg="white").pack(side="left", padx=4)

        tk.Label(right, text="Orders (latest first)", fg="white", bg="#1e1e3f", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.orders_text = scrolledtext.ScrolledText(right, height=12, state="disabled", bg="#2a2a4a", fg="white")
        self.orders_text.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        sales_frame = tk.Frame(right, bg="#1e1e3f")
        sales_frame.pack(fill="x", padx=8, pady=(4, 8))
        tk.Label(sales_frame, text="Total Sales:", fg="white", bg="#1e1e3f", font=("Arial", 11, "bold")).pack(side="left")
        self.total_sales_label = tk.Label(sales_frame, text="₱0.00", fg="white", bg="#1e1e3f", font=("Arial", 11, "bold"))
        self.total_sales_label.pack(side="left", padx=8)

        admin_btn_frame = tk.Frame(right, bg="#1e1e3f")
        admin_btn_frame.pack(fill="x", padx=8, pady=(4, 8))
        tk.Button(admin_btn_frame, text="Refresh", command=self.refresh_all, bg="#4a90e2", fg="white").pack(side="left", padx=6)
        tk.Button(admin_btn_frame, text="Export Orders Report", command=self.export_orders_report, bg="#4a90e2", fg="white").pack(side="left", padx=6)
        tk.Button(admin_btn_frame, text="Reset Demo Data", command=self.reset_demo_data, bg="#e67e22", fg="white").pack(side="left", padx=6)

        self.refresh_all()

    def refresh_books_listbox(self):
        self.books_listbox.delete(0, tk.END)
        for b in self.dm.books:
            cover_status = " [Cover]" if b.cover_path else ""
            self.books_listbox.insert(tk.END, f"{b.title} — {b.author} — ₱{b.price:.2f}{cover_status}")

    def add_book_dialog(self):
        dlg = BookEditDialog(self.win, title="Add Book", initial=("", "", "0.00", "", ""))
        if dlg.result:
            title, author, price, description, cover_path = dlg.result
            try: pricef = float(price)
            except ValueError:
                messagebox.showerror("Invalid Price", "Price must be a number.")
                return
            self.dm.add_book(Book(title, author, pricef, description, cover_path=cover_path))
            messagebox.showinfo("Added", f"Book '{title}' added.")
            self.refresh_all()
            if self.refresh_callback: self.refresh_callback()

    def edit_book_dialog(self):
        sel = self.books_listbox.curselection()
        if not sel:
            messagebox.showwarning("Select Book", "Select a book to edit.")
            return
        book = self.dm.books[sel[0]]
        dlg = BookEditDialog(self.win, title="Edit Book", initial=(book.title, book.author, str(book.price), book.description, book.cover_path))
        if dlg.result:
            title, author, price, description, cover_path = dlg.result
            try: pricef = float(price)
            except ValueError:
                messagebox.showerror("Invalid Price", "Price must be a number.")
                return
            if self.dm.update_book(book.id, title, author, pricef, description, cover_path):
                messagebox.showinfo("Updated", f"Book '{title}' updated.")
                self.refresh_all()
                if self.refresh_callback: self.refresh_callback()
            else: messagebox.showerror("Error", "Failed to update book.")

    def delete_selected_book(self):
        sel = self.books_listbox.curselection()
        if not sel: return
        book = self.dm.books[sel[0]]
        if messagebox.askyesno("Confirm Delete", f"Delete '{book.title}'?"):
            if self.dm.delete_book(book.id):
                messagebox.showinfo("Deleted", f"Book '{book.title}' deleted.")
                self.refresh_all()
                if self.refresh_callback: self.refresh_callback()
            else: messagebox.showerror("Error", "Could not delete book.")

    def refresh_users_display(self):
        self.users_listbox.delete(0, tk.END)
        for u in sorted(self.dm.users.keys()):
            blocked_flag = " (blocked)" if self.dm.users[u].get("blocked") else ""
            self.users_listbox.insert(tk.END, f"{u}{blocked_flag}")

    def get_selected_username(self):
        sel = self.users_listbox.curselection()
        return self.users_listbox.get(sel[0]).split(" ")[0] if sel else None

    def block_selected_user(self):
        username = self.get_selected_username()
        if not username: return
        if username == "admin": return messagebox.showerror("Forbidden", "Cannot block admin.")
        if self.dm.block_user(username):
            messagebox.showinfo("Blocked", f"User '{username}' blocked.")
            self.refresh_all()

    def unblock_selected_user(self):
        username = self.get_selected_username()
        if not username: return
        if username == "admin": return messagebox.showerror("Forbidden", "Admin is always unblocked.")
        if self.dm.unblock_user(username):
            messagebox.showinfo("Unblocked", f"User '{username}' unblocked.")
            self.refresh_all()

    def delete_selected_user(self):
        username = self.get_selected_username()
        if not username: return
        if username == "admin": return messagebox.showerror("Forbidden", "Cannot delete admin.")
        if messagebox.askyesno("Confirm Delete", f"Delete user '{username}'? This cannot be undone."):
            if self.dm.delete_user(username):
                messagebox.showinfo("Deleted", f"User '{username}' deleted.")
                self.refresh_all()
            else: messagebox.showerror("Error", "Could not delete user.")

    def refresh_orders_display(self):
        self.orders_text.config(state="normal")
        self.orders_text.delete("1.0", tk.END)
        if not self.dm.orders:
            self.orders_text.insert(tk.END, "No orders yet.\n")
        else:
            for o in reversed(self.dm.orders):
                self.orders_text.insert(tk.END, f"Order ID: {o['id']}\nUser: {o['username']}  Date: {o['date']}  Total: ₱{o['total']:.2f}\nItems:\n")
                for it in o["items"]:
                    self.orders_text.insert(tk.END, f"  - {it['title']} by {it['author']} x{it['quantity']} - ₱{it['price']:.2f}\n")
                self.orders_text.insert(tk.END, "-" * 48 + "\n")
        self.orders_text.config(state="disabled")

    def refresh_total_sales(self):
        self.total_sales_label.config(text=f"₱{self.dm.total_sales():.2f}")

    def refresh_all(self):
        self.refresh_books_listbox()
        self.refresh_users_display()
        self.refresh_orders_display()
        self.refresh_total_sales()

    def export_orders_report(self):
        if not self.dm.orders: return messagebox.showinfo("No Orders", "There are no orders to export.")
        try:
            with open("orders_report.txt", "w", encoding="utf-8") as f:
                for o in reversed(self.dm.orders):
                    f.write(f"Order ID: {o['id']}\nUser: {o['username']}  Date: {o['date']}  Total: ₱{o['total']:.2f}\nItems:\n")
                    for it in o["items"]:
                        f.write(f"  - {it['title']} by {it['author']} x{it['quantity']} - ₱{it['price']:.2f}\n")
                    f.write("-" * 48 + "\n")
            messagebox.showinfo("Exported", f"Orders exported to orders_report.txt")
        except Exception as e: messagebox.showerror("Export Failed", f"Could not write report: {e}")

    def reset_demo_data(self):
        if messagebox.askyesno("Reset Demo Data", "Reset books, remove all users except admin, and clear orders?"):
            self.dm.reset_demo_data()
            messagebox.showinfo("Reset", "Demo data restored.")
            self.refresh_all()
            if self.refresh_callback: self.refresh_callback()