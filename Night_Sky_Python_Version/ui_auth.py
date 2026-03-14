import tkinter as tk
from tkinter import messagebox
from ui_core import NightSkyCanvas, center_window, make_draggable
from models import DataManager

class LoginWindow:
    def __init__(self, dm: DataManager, on_login_success):
        self.dm = dm
        self.on_login_success = on_login_success
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        center_window(self.root, 800, 600)
        self.root.configure(bg="#0a0a23")

        NightSkyCanvas(self.root, width=800, height=600, star_count=90).place(x=0, y=0, relwidth=1, relheight=1)

        top_bar = tk.Frame(self.root, bg="#0a0a23")
        top_bar.place(relx=0, rely=0, relwidth=1, height=36)
        drag_label = tk.Label(top_bar, text="  Night Sky Bookstore", fg="white", bg="#0a0a23", font=("Arial", 10, "bold"))
        drag_label.pack(side="left", padx=(6, 0))
        make_draggable(self.root, drag_label)
        tk.Button(top_bar, text="Exit", command=self.root.destroy, bg="#e74c3c", fg="white", bd=0).pack(side="right", padx=6, pady=4)

        frame = tk.Frame(self.root, bg="#0a0a23")
        frame.place(relx=0.5, rely=0.52, anchor="center")

        tk.Label(frame, text="Welcome to Night Sky Bookstore", font=("Arial", 18, "bold"), fg="white", bg="#0a0a23").grid(row=0, column=0, columnspan=2, pady=(10, 20))
        tk.Label(frame, text="Username:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=1, column=0, sticky="e", padx=(0, 10))
        self.username_entry = tk.Entry(frame, font=("Arial", 16), width=30, bg="#1e1e3f", fg="white", insertbackground="white")
        self.username_entry.grid(row=1, column=1, pady=8)

        tk.Label(frame, text="Password:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=2, column=0, sticky="e", padx=(0, 10))
        self.password_entry = tk.Entry(frame, show="*", font=("Arial", 16), width=30, bg="#1e1e3f", fg="white", insertbackground="white")
        self.password_entry.grid(row=2, column=1, pady=8)

        btn_frame = tk.Frame(frame, bg="#0a0a23")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        tk.Button(btn_frame, text="Login", width=14, bg="#4a90e2", fg="white", font=("Arial", 12, "bold"), command=self.login).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Sign Up", width=14, bg="#4a90e2", fg="white", font=("Arial", 12, "bold"), command=self.open_signup).pack(side="left", padx=10)

        self.root.bind("<Return>", lambda e: self.login())
        self.username_entry.focus()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter username and password.")
            return
        if self.dm.validate_login(username, password):
            self.root.destroy()
            self.on_login_success(username)
        else:
            user = self.dm.users.get(username)
            if user and user.get("blocked"):
                messagebox.showerror("Blocked", "This account is blocked. Contact admin.")
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")

    def open_signup(self): SignupWindow(self.dm, self.root)
    def run(self): self.root.mainloop()

class SignupWindow:
    def __init__(self, dm: DataManager, parent_root):
        self.dm, self.parent_root = dm, parent_root
        self.win = tk.Toplevel(parent_root)
        self.win.overrideredirect(True)
        center_window(self.win, 800, 600)
        self.win.configure(bg="#0a0a23")
        self.win.grab_set()

        NightSkyCanvas(self.win, width=800, height=600, star_count=90).place(x=0, y=0, relwidth=1, relheight=1)

        top_bar = tk.Frame(self.win, bg="#0a0a23")
        top_bar.place(relx=0, rely=0, relwidth=1, height=36)
        drag_label = tk.Label(top_bar, text="  Create Account", fg="white", bg="#0a0a23", font=("Arial", 10, "bold"))
        drag_label.pack(side="left", padx=(6, 0))
        make_draggable(self.win, drag_label)
        tk.Button(top_bar, text="Exit", command=self.win.destroy, bg="#e74c3c", fg="white", bd=0).pack(side="right", padx=6, pady=4)

        frame = tk.Frame(self.win, bg="#0a0a23")
        frame.place(relx=0.5, rely=0.52, anchor="center")
        tk.Label(frame, text="Create Account", font=("Arial", 18, "bold"), fg="white", bg="#0a0a23").grid(row=0, column=0, columnspan=2, pady=(10, 20))

        tk.Label(frame, text="Username:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=1, column=0, sticky="e", padx=(0, 10))
        self.username_entry = tk.Entry(frame, font=("Arial", 18), width=30, bg="#1e1e3f", fg="white")
        self.username_entry.grid(row=1, column=1, pady=8)

        tk.Label(frame, text="Password (min 6 chars):", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=2, column=0, sticky="e", padx=(0, 10))
        self.password_entry = tk.Entry(frame, show="*", font=("Arial", 18), width=30, bg="#1e1e3f", fg="white")
        self.password_entry.grid(row=2, column=1, pady=8)

        tk.Label(frame, text="Confirm Password:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=3, column=0, sticky="e", padx=(0, 10))
        self.confirm_entry = tk.Entry(frame, show="*", font=("Arial", 18), width=30, bg="#1e1e3f", fg="white")
        self.confirm_entry.grid(row=3, column=1, pady=8)

        btn_frame = tk.Frame(frame, bg="#0a0a23")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        tk.Button(btn_frame, text="Sign Up", width=14, bg="#4a90e2", fg="white", font=("Arial", 12, "bold"), command=self.signup).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancel", width=14, bg="#666", fg="white", font=("Arial", 12, "bold"), command=self.win.destroy).pack(side="left", padx=10)
        self.username_entry.focus()

    def signup(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()
        if not username or not password or not confirm:
            messagebox.showwarning("Warning", "Please fill all fields.")
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.")
            return
        if username == "admin":
            messagebox.showerror("Error", "Cannot create or override admin account.")
            return
        if self.dm.add_user(username, password):
            messagebox.showinfo("Success", "Account created! You can now log in.")
            self.win.destroy()
        else:
            messagebox.showerror("Error", "Username already taken.")