# -*- coding: utf-8 -*-
"""
Night Sky Bookstore - Final (MODIFIED FOR BOOK COVERS)
- UTF-8 safe
- Moving stars animation
- Centered windows
- Custom top bar for login, standard bar for main app
- Persistent JSON storage for users/books/orders
- Login & Signup windows
- **NEW: Book cover image handling using PIL/Pillow**
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, filedialog
import json
import os
import random
from typing import Any, Dict, List, Optional
from datetime import datetime
import sys
# Import for Image handling
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Dependency Error",
                         "Pillow (PIL) is required for image handling. Please install it with 'pip install Pillow'.")
    sys.exit(1)


# -------------------------
# File paths & defaults
# -------------------------
USERS_FILE = "users.json"
BOOKS_FILE = "books.json"
ORDERS_FILE = "orders.json"
# New folder for storing book covers
COVER_DIR = "book_covers"

DEFAULT_USERS = {"admin": {"password": "987654321", "blocked": False}}
DEFAULT_BOOKS = [{}]
DEFAULT_ORDERS: List[Dict[str, Any]] = []

# Ensure cover directory exists
if not os.path.exists(COVER_DIR):
    os.makedirs(COVER_DIR)

# -------------------------
# JSON helpers
# -------------------------
def load_json(path: str, default: Any):
    """Load JSON file, return default and recreate file if missing/corrupted."""
    if not os.path.exists(path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[WARN] Could not create {path}: {e}", file=sys.stderr)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to read {path}: {e}. Returning default.", file=sys.stderr)
        return default


def save_json(path: str, data: Any):
    """Save data to JSON file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("File Save Error", f"Failed to save {path}: {e}")


# -------------------------
# Models & DataManager
# -------------------------
class Book:
    # MODIFIED: Added cover_path
    def __init__(self, title: str, author: str, price: float, description: str,
                 cover_path: Optional[str] = None, book_id: Optional[str] = None):
        self.title = title
        self.author = author
        self.price = float(price)
        self.description = description
        self.cover_path = cover_path if cover_path else ""  # Ensure it's a string
        self.id = book_id or f"bk{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # MODIFIED: Included cover_path in to_dict
    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "title": self.title, "author": self.author, "price": self.price,
                "description": self.description, "cover_path": self.cover_path}

    # MODIFIED: Included cover_path in from_dict
    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        return cls(d["title"], d["author"], d.get("price", 0.0), d.get("description", ""),
                   d.get("cover_path", ""), d.get("id"))

    def __str__(self) -> str:
        # FIXED: Explicitly includes "Description: " prefix on the second line
        return (f"{self.title} by {self.author} - ₱{self.price:.2f}\n"
                f"Description: {self.description}")


class DataManager:
    """Persistent storage for users, books and orders."""

    def __init__(self):
        raw_users = load_json(USERS_FILE, DEFAULT_USERS)
        # normalize users into dict[str, dict]
        self.users: Dict[str, Dict[str, Any]] = {}
        for uname, val in raw_users.items():
            if isinstance(val, dict):
                self.users[uname] = {"password": val.get("password", ""), "blocked": bool(val.get("blocked", False))}
            else:
                # legacy format: string password
                self.users[uname] = {"password": str(val), "blocked": False}
        # ensure admin password
        if self.users.get("admin", {}).get("password") != "987654321":
            self.users["admin"] = {"password": "987654321", "blocked": False}
            self.save_users()

        # books
        raw_books = load_json(BOOKS_FILE, DEFAULT_BOOKS)
        self.books: List[Book] = []
        for b in raw_books:
            # ensure id and price normalized
            if "id" not in b:
                b["id"] = f"bk{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
            try:
                b["price"] = float(b.get("price", 0.0))
            except Exception:
                b["price"] = 0.0
            # NEW: ensure cover_path is present
            if "cover_path" not in b:
                b["cover_path"] = ""
            self.books.append(Book.from_dict(b))

        # orders
        self.orders: List[Dict[str, Any]] = load_json(ORDERS_FILE, DEFAULT_ORDERS)

    # users
    def save_users(self):
        save_json(USERS_FILE, self.users)

    def add_user(self, username: str, password: str) -> bool:
        if username in self.users:
            return False
        self.users[username] = {"password": password, "blocked": False}
        self.save_users()
        return True

    def delete_user(self, username: str) -> bool:
        if username in self.users and username != "admin":
            del self.users[username]
            self.save_users()
            return True
        return False

    def block_user(self, username: str) -> bool:
        if username in self.users and username != "admin":
            self.users[username]["blocked"] = True
            self.save_users()
            return True
        return False

    def unblock_user(self, username: str) -> bool:
        if username in self.users and username != "admin":
            self.users[username]["blocked"] = False
            self.save_users()
            return True
        return False

    def validate_login(self, username: str, password: str) -> bool:
        u = self.users.get(username)
        if not u:
            return False
        if u.get("blocked"):
            return False
        return u.get("password") == password

    # books
    def save_books(self):
        save_json(BOOKS_FILE, [b.to_dict() for b in self.books])

    def add_book(self, book: Book):
        self.books.append(book)
        self.save_books()

    # MODIFIED: Added cover_path parameter
    def update_book(self, book_id: str, title: str, author: str, price: float, description: str,
                    cover_path: str) -> bool:
        for b in self.books:
            if b.id == book_id:
                b.title = title
                b.author = author
                b.price = float(price)
                b.description = description
                b.cover_path = cover_path  # NEW: update cover path
                self.save_books()
                return True
        return False

    def delete_book(self, book_id: str) -> bool:
        before = len(self.books)
        self.books = [b for b in self.books if b.id != book_id]
        if len(self.books) != before:
            self.save_books()
            return True
        return False

    # orders
    def save_orders(self):
        save_json(ORDERS_FILE, self.orders)

    def add_order(self, username: str, items: List[Dict[str, Any]], total: float):
        order = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
            "username": username,
            "items": items,
            "total": float(total),
            "date": datetime.utcnow().isoformat()
        }
        self.orders.append(order)
        self.save_orders()

    def total_sales(self) -> float:
        return sum(o.get("total", 0.0) for o in self.orders)

    def reset_demo_data(self):
        """Reset demo data (books -> defaults, users -> admin only, orders -> empty)."""
        self.books = [Book.from_dict(b) for b in DEFAULT_BOOKS]
        self.users = {"admin": {"password": "987654321", "blocked": False}}
        self.orders = []
        self.save_books()
        self.save_users()
        self.save_orders()


# -------------------------
# Night sky canvas with moving stars
# -------------------------
class Star:
    """Simple star particle with position and speed for animation."""

    def __init__(self, width: int, height: int):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height * 0.6)  # keep stars upper area
        self.size = random.randint(1, 3)
        # small horizontal drift and tiny vertical wobble
        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.05, 0.05)
        self.brightness = random.uniform(0.6, 1.0)
        # small flicker phase
        self.phase = random.uniform(0, 2 * 3.14159)


class NightSkyCanvas(tk.Canvas):
    """Canvas that animates stars and draws a moon. No bookshelf (removed)."""

    def __init__(self, parent, width: int = 900, height: int = 700, bg: str = "#0a0a23", star_count: int = 80,
                 **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.star_count = star_count
        self.stars: List[Star] = []
        self.star_items: List[int] = []
        self._running = False
        self._init_stars()
        self.bind("<Configure>", self._on_configure)
        # draw initial frame
        self._start_animation()

    def _on_configure(self, event):
        # update size and recreate stars scaled to new size
        try:
            self.width = max(1, event.width)
            self.height = max(1, event.height)
        except Exception:
            pass
        # don't recreate the entire field every resize to avoid flicker; adjust positions if absolutely necessary
        if len(self.stars) < max(10, int(self.star_count * 0.5)):
            self._init_stars()

    def _init_stars(self):
        self.stars = [Star(self.width, self.height) for _ in range(self.star_count)]
        # clear any existing drawn items
        for iid in getattr(self, "star_items", []):
            try:
                self.delete(iid)
            except Exception:
                pass
        self.star_items = []
        # one-time moon draw handled in animate frame

    def draw_static(self):
        """Draw static elements: moon."""
        self.delete("static")
        # moon (left upper corner)
        mx = int(self.width * 0.12)
        my = int(self.height * 0.08)
        r = int(min(self.width, self.height) * 0.06)
        # full moon
        self.create_oval(mx, my, mx + 2 * r, my + 2 * r, fill="#FFD700", outline="", tags="static")
        # crescent cutout
        self.create_oval(mx + int(r * 0.3), my, mx + 2 * r + int(r * 0.3), my + 2 * r, fill=self["bg"], outline="",
                         tags="static")

    def _animate(self):
        """Single animation frame: move stars slightly and redraw."""
        if not self._running:
            return
        # move stars
        self.delete("star")
        # draw stars
        for s in self.stars:
            # update position
            s.x += s.vx
            s.y += s.vy
            # flicker effect
            s.phase += 0.1
            flick = (0.5 + 0.5 * (random.random())) * s.brightness
            # wrap-around horizontally
            if s.x < 0:
                s.x = self.width
            elif s.x > self.width:
                s.x = 0
            # keep vertical bounds in upper area
            if s.y < 0:
                s.y = 0
            elif s.y > self.height * 0.6:
                s.y = self.height * 0.6
            # draw as oval with varied size
            size = max(1, s.size + (0 if random.random() > 0.95 else 0))
            color_intensity = int(200 * flick) + 55
            color_hex = f"#{color_intensity:02x}{color_intensity:02x}{color_intensity:02x}"
            self.create_oval(s.x, s.y, s.x + size, s.y + size, fill=color_hex, outline="", tags="star")
        # static elements
        self.draw_static()
        # schedule next frame
        self.after(90, self._animate)

    def _start_animation(self):
        if self._running:
            return
        self._running = True
        self._animate()

    def _stop_animation(self):
        self._running = False


# -------------------------
# Window helpers: center & draggable
# -------------------------
def center_window(window, width: int, height: int):
    """Center a tkinter window on the screen."""
    window.update_idletasks()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    x = int((sw - width) / 2)
    y = int((sh - height) / 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def make_draggable(window, widget):
    """Make a widget act as drag handle for the given window."""

    def start_move(event):
        window._drag_x = event.x
        window._drag_y = event.y

    def stop_move(event):
        window._drag_x = None
        window._drag_y = None

    def do_move(event):
        try:
            x = event.x_root - window._drag_x
            y = event.y_root - window._drag_y
            window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    widget.bind("<Button-1>", start_move)
    widget.bind("<ButtonRelease-1>", stop_move)
    widget.bind("<B1-Motion>", do_move)


# -------------------------
# Login & Signup windows
# -------------------------
class LoginWindow:
    def __init__(self, dm: DataManager, on_login_success):
        self.dm = dm
        self.on_login_success = on_login_success
        # root without native decorations
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        win_w, win_h = 800, 600
        center_window(self.root, win_w, win_h)
        self.root.configure(bg="#0a0a23")

        # background canvas (animated stars)
        self.canvas = NightSkyCanvas(self.root, width=win_w, height=win_h, star_count=90)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # top custom bar (drag + exit)
        top_bar = tk.Frame(self.root, bg="#0a0a23")
        top_bar.place(relx=0, rely=0, relwidth=1, height=36)
        drag_label = tk.Label(top_bar, text="  Night Sky Bookstore", fg="white", bg="#0a0a23",
                              font=("Arial", 10, "bold"))
        drag_label.pack(side="left", padx=(6, 0))
        make_draggable(self.root, drag_label)
        exit_btn = tk.Button(top_bar, text="Exit", command=self.root.destroy, bg="#e74c3c", fg="white", bd=0)
        exit_btn.pack(side="right", padx=6, pady=4)

        # login frame
        frame = tk.Frame(self.root, bg="#0a0a23")
        frame.place(relx=0.5, rely=0.52, anchor="center")

        # Change font size from 14 to 18 for the Welcome title
        tk.Label(frame, text="Welcome to Night Sky Bookstore", font=("Arial", 18, "bold"), fg="white",
                 bg="#0a0a23").grid(row=0, column=0, columnspan=2, pady=(10, 20))  # <-- MODIFIED: size and pady

        # Change font size for Username/Password labels
        tk.Label(frame, text="Username:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=1, column=0,
                                                                                             sticky="e", padx=(0,
                                                                                                               10))  # <-- MODIFIED: size and padx
        # Change font size for Username/Password entries
        self.username_entry = tk.Entry(frame, font=("Arial", 16), width=30, bg="#1e1e3f", fg="white",
                                       insertbackground="white")  # <-- MODIFIED: size and width
        self.username_entry.grid(row=1, column=1, pady=8)  # <-- MODIFIED: pady

        # Change font size for Password label
        tk.Label(frame, text="Password:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=2, column=0,
                                                                                             sticky="e", padx=(0,
                                                                                                               10))  # <-- MODIFIED: size and padx
        # Change font size for Password entry
        self.password_entry = tk.Entry(frame, show="*", font=("Arial", 16), width=30, bg="#1e1e3f", fg="white",
                                       insertbackground="white")  # <-- MODIFIED: size and width
        self.password_entry.grid(row=2, column=1, pady=8)  # <-- MODIFIED: pady

        btn_frame = tk.Frame(frame, bg="#0a0a23")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))  # <-- MODIFIED: pady
        # Increase button width/padding (or rely on wider text/font)
        tk.Button(btn_frame, text="Login", width=14, bg="#4a90e2", fg="white", font=("Arial", 12, "bold"),
                  command=self.login).pack(side="left", padx=10)  # <-- MODIFIED: width and font
        tk.Button(btn_frame, text="Sign Up", width=14, bg="#4a90e2", fg="white", font=("Arial", 12, "bold"),
                  command=self.open_signup).pack(side="left", padx=10)  # <-- MODIFIED: width and font

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

    def open_signup(self):
        SignupWindow(self.dm, self.root)

    def run(self):
        self.root.mainloop()


class SignupWindow:
    def __init__(self, dm: DataManager, parent_root):
        self.dm = dm
        self.parent_root = parent_root
        self.win = tk.Toplevel(parent_root)
        self.win.overrideredirect(True)
        win_w, win_h = 800, 600
        center_window(self.win, win_w, win_h)
        self.win.configure(bg="#0a0a23")
        self.win.grab_set()

        self.canvas = NightSkyCanvas(self.win, width=win_w, height=win_h, star_count=90)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        top_bar = tk.Frame(self.win, bg="#0a0a23")
        top_bar.place(relx=0, rely=0, relwidth=1, height=36)
        drag_label = tk.Label(top_bar, text="  Create Account", fg="white", bg="#0a0a23", font=("Arial", 10, "bold"))
        drag_label.pack(side="left", padx=(6, 0))
        make_draggable(self.win, drag_label)
        exit_btn = tk.Button(top_bar, text="Exit", command=self.win.destroy, bg="#e74c3c", fg="white", bd=0)
        exit_btn.pack(side="right", padx=6, pady=4)

        frame = tk.Frame(self.win, bg="#0a0a23")
        frame.place(relx=0.5, rely=0.52, anchor="center")
        # Change font size from 14 to 18 for the Create Account title
        tk.Label(frame, text="Create Account", font=("Arial", 18, "bold"), fg="white", bg="#0a0a23").grid(row=0,
                                                                                                          column=0,
                                                                                                          columnspan=2,
                                                                                                          pady=(10,
                                                                                                                20))  # <-- MODIFIED: size and pady

        # Change font size for Username label
        tk.Label(frame, text="Username:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=1, column=0,
                                                                                             sticky="e", padx=(0,
                                                                                                               10))  # <-- MODIFIED: size and padx
        # Change font size for Username entry
        self.username_entry = tk.Entry(frame, font=("Arial", 18), width=30, bg="#1e1e3f",
                                       fg="white")  # <-- MODIFIED: size and width
        self.username_entry.grid(row=1, column=1, pady=8)  # <-- MODIFIED: pady

        # Change font size for Password label
        tk.Label(frame, text="Password (min 6 chars):", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=2,
                                                                                                           column=0,
                                                                                                           sticky="e",
                                                                                                           padx=(0,
                                                                                                                 10))  # <-- MODIFIED: size and padx
        # Change font size for Password entry
        self.password_entry = tk.Entry(frame, show="*", font=("Arial", 18), width=30, bg="#1e1e3f",
                                       fg="white")  # <-- MODIFIED: size and width
        self.password_entry.grid(row=2, column=1, pady=8)  # <-- MODIFIED: pady

        # Change font size for Confirm Password label
        tk.Label(frame, text="Confirm Password:", fg="white", bg="#0a0a23", font=("Arial", 14)).grid(row=3, column=0,
                                                                                                     sticky="e",
                                                                                                     padx=(0,
                                                                                                           10))  # <-- MODIFIED: size and padx
        # Change font size for Confirm Password entry
        self.confirm_entry = tk.Entry(frame, show="*", font=("Arial", 18), width=30, bg="#1e1e3f",
                                      fg="white")  # <-- MODIFIED: size and width
        self.confirm_entry.grid(row=3, column=1, pady=8)  # <-- MODIFIED: pady

        btn_frame = tk.Frame(frame, bg="#0a0a23")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))  # <-- MODIFIED: pady
        # Increase button width/padding (or rely on wider text/font)
        tk.Button(btn_frame, text="Sign Up", width=14, bg="#4a90e2", fg="white", font=("Arial", 12, "bold"),
                  command=self.signup).pack(side="left", padx=10)  # <-- MODIFIED: width and font
        tk.Button(btn_frame, text="Cancel", width=14, bg="#666", fg="white", font=("Arial", 12, "bold"),
                  command=self.win.destroy).pack(side="left", padx=10)  # <-- MODIFIED: width and font

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


# -------------------------
# Start of main application window (OnlineBookstoreApp)
# -------------------------
class OnlineBookstoreApp:
    def __init__(self, username: str, data_manager: DataManager):
        self.username = username
        self.dm = data_manager
        self.admin_window = None

        # main window - with native decorations, centered
        self.root = tk.Tk()
        self.root.title(f"Night Sky Bookstore — Logged in as: {username}")

        # --- MODIFIED: Set fixed window size to 1000x800 and disable resizing ---
        win_w, win_h = 1300, 900
        center_window(self.root, win_w, win_h)
        self.root.resizable(False, False)
        # --- END MODIFICATION ---

        self.root.configure(bg="#0a0a23")



        # background animated canvas (stars + moon)
        self.bg = NightSkyCanvas(self.root, width=win_w, height=win_h, star_count=100)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)

        # Top controls frame
        top_controls = tk.Frame(self.root, bg="#0a0a23")
        top_controls.pack(side="top", fill="x", pady=5, padx=10)

        # Spacer to push buttons to the right
        tk.Label(top_controls, text="", bg="#0a0a23").pack(side="left", expand=True)

        logout_btn = tk.Button(top_controls, text="Logout", command=self.logout, bg="#666", fg="white", bd=0, padx=8,
                               pady=4)
        logout_btn.pack(side="right", padx=(0, 6))

        if username == "admin":
            admin_btn = tk.Button(top_controls, text="Admin Panel", command=self.open_admin_panel, bg="#e67e22",
                                  fg="white", bd=0, padx=8, pady=4)
            admin_btn.pack(side="right", padx=6)

        # main content frame
        main_frame = tk.Frame(self.root, bg="#0a0a23")
        main_frame.pack(side="top", fill="both", expand=True, padx=10,
                        pady=(0, 10))

        # Left: Book list & details
        left_frame = tk.Frame(main_frame, bg="#1e1e3f")
        left_frame.place(relx=0, rely=0, relwidth=0.59, relheight=1)
        tk.Label(left_frame, text="Available Books:", fg="white", bg="#1e1e3f", font=("Arial", 14, "bold")).pack(
            anchor="w", padx=8, pady=(8, 0))

        # Scrollable Tile View for books
        book_display_frame = tk.Frame(left_frame, bg="#1e1e3f")
        book_display_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Canvas for scrolling
        self.books_canvas = tk.Canvas(book_display_frame, bg="#1e1e3f", highlightthickness=0)
        self.books_canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        book_scrollbar = tk.Scrollbar(book_display_frame, orient="vertical", command=self.books_canvas.yview)
        book_scrollbar.pack(side="right", fill="y")

        # Configure canvas to use the scrollbar
        self.books_canvas.configure(yscrollcommand=book_scrollbar.set)

        # Inner frame to hold the actual book tiles
        self.tile_container = tk.Frame(self.books_canvas, bg="#1e1e3f")

        # Add the inner frame to the canvas
        self.books_canvas_window = self.books_canvas.create_window((0, 0), window=self.tile_container, anchor="nw")

        # Bind events for scrolling and resizing
        self.tile_container.bind("<Configure>", self._on_tile_container_configure)
        self.books_canvas.bind("<Configure>", self._on_books_canvas_resize)

        self.books_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.books_canvas.bind("<Button-4>", self._on_mousewheel)
        self.books_canvas.bind("<Button-5>", self._on_mousewheel)

        # IMPORTANT: Also bind to the inner container so scrolling works when the mouse is over a book tile
        self.tile_container.bind("<MouseWheel>", self._on_mousewheel)
        self.tile_container.bind("<Button-4>", self._on_mousewheel)
        self.tile_container.bind("<Button-5>", self._on_mousewheel)
        # ---------------------------------------------

        # State tracking for the new tile display
        self.selected_book_id = None

        # State tracking for the new tile display
        self.selected_book_id = None
        self.selected_tile = None
        # NEW: Store image references to prevent garbage collection
        self.image_references = {}

        details_frame = tk.Frame(left_frame, bg="#1e1e3f")
        details_frame.pack(fill="x", padx=8, pady=(2, 8))
        self.book_details = scrolledtext.ScrolledText(details_frame, height=5, bg="#2a2a4a", fg="white",
                                                      font=("Arial", 12), state="disabled")
        self.book_details.pack(fill="x")

        btn_frame = tk.Frame(left_frame, bg="#1e1e3f")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(btn_frame, text="Add to Cart", command=self.add_to_cart, bg="#4a90e2", fg="white").pack(side="left",
                                                                                                          padx=(0, 6))
        tk.Button(btn_frame, text="Refresh", command=self.refresh_book_list, bg="#4a90e2", fg="white").pack(side="left")

        # Right: Cart & Actions (create cart UI)
        right_frame = tk.Frame(main_frame, bg="#1e1e3f")
        right_frame.place(relx=0.60, rely=0, relwidth=0.40, relheight=1)
        tk.Label(right_frame, text="Shopping Cart:", fg="white", bg="#1e1e3f", font=("Arial", 11, "bold")).pack(
            anchor="w", padx=8, pady=(8, 0))
        self.cart_listbox = tk.Listbox(right_frame, bg="#2a2a4a", fg="white", selectbackground="#4a90e2",
                                       font=("Arial", 12))
        self.cart_listbox.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        total_frame = tk.Frame(right_frame, bg="#1e1e3f")
        total_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.total_label = tk.Label(total_frame, text="Total: ₱0.00", fg="white", bg="#1e1e3f",
                                    font=("Arial", 12, "bold"))
        self.total_label.pack(side="left")

        cart_btn_frame = tk.Frame(right_frame, bg="#1e1e3f")
        cart_btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(cart_btn_frame, text="Remove Selected", command=self.remove_cart_item, bg="#4a90e2", fg="white").pack(
            side="left", padx=(0, 6))
        tk.Button(cart_btn_frame, text="Clear Cart", command=self.clear_cart, bg="#4a90e2", fg="white").pack(
            side="left", padx=(0, 6))
        tk.Button(cart_btn_frame, text="Checkout", command=self.checkout, bg="#2ecc71", fg="white").pack(side="left",
                                                                                                         padx=(10, 0))

        # initialize cart and populate books
        self.cart = []
        self.refresh_book_list()

        # ensure proper close
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _on_tile_container_configure(self, event):
        """Update the scroll region when the inner frame size changes."""
        self.books_canvas.configure(scrollregion=self.books_canvas.bbox("all"))

    def _on_books_canvas_resize(self, event):
        """Make the inner frame expand to the width of the canvas."""
        self.books_canvas.itemconfig(self.books_canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel events for smooth scrolling across platforms."""
        # Windows/macOS handle the event with event.delta (typically +/- 120)
        if sys.platform.startswith('win') or sys.platform.startswith('darwin'):
            self.books_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Linux uses Button-4 and Button-5 events (handled by separate bindings)
        elif event.num == 4:
            self.books_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.books_canvas.yview_scroll(1, "units")

    def refresh_book_list(self):
        """Reload the book tiles from DataManager books and display them in a grid."""
        for widget in self.tile_container.winfo_children():
            widget.destroy()

        # Clear image references before refreshing
        self.image_references.clear()

        self.selected_book_id = None
        self.selected_tile = None
        self.book_details.config(state="normal")
        self.book_details.delete("1.0", tk.END)
        self.book_details.config(state="disabled")

        books_per_row = 4
        tile_width = 150
        tile_height = 250
        cover_height = int(tile_height * 0.7)
        padding_x = 10
        padding_y = 10

        for i, book in enumerate(self.dm.books):
            row = i // books_per_row
            col = i % books_per_row

            tile = tk.Frame(self.tile_container, width=tile_width, height=tile_height, bg="#1e1e3f", bd=1,
                            relief="solid", highlightbackground="white", highlightthickness=1)
            tile.grid(row=row, column=col, padx=padding_x, pady=padding_y, sticky="nsew")
            tile.grid_propagate(False)

            cover_frame = tk.Frame(tile, bg="#2a2a4a", width=tile_width - 10, height=cover_height)
            cover_frame.pack(pady=(5, 0))
            cover_frame.pack_propagate(False)  # Important to fix size for image

            cover_label = tk.Label(cover_frame, text="Cover\n(Image Not Loaded)", fg="#777", bg="#2a2a4a",
                                   font=("Arial", 10))
            cover_label.place(relx=0.5, rely=0.5, anchor="center")

            # NEW: Image Loading Logic
            if book.cover_path and os.path.exists(book.cover_path):
                try:
                    # Load and resize image
                    img = Image.open(book.cover_path)
                    # Maintain aspect ratio for resize
                    img_w, img_h = img.size
                    ratio = min((tile_width - 10) / img_w, cover_height / img_h)
                    new_w = int(img_w * ratio)
                    new_h = int(img_h * ratio)

                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    # Store the reference
                    self.image_references[book.id] = photo

                    cover_label.config(text="", image=photo, bg="#2a2a4a")
                except Exception as e:
                    print(f"Error loading image for {book.title}: {e}")
                    cover_label.config(text="Cover\n(Load Error)", fg="#e74c3c")
            else:
                cover_label.config(text="Cover\n(No Image)", fg="#777")


            title_text = f"{book.title}"
            price_text = f"₱{book.price:.2f}"

            title_label = tk.Label(tile, text=title_text, fg="white", bg="#1e1e3f", font=("Arial", 9, "bold"),
                                   wraplength=tile_width - 10, justify="center")
            title_label.pack(fill="x", padx=5, pady=(2, 0))

            price_label = tk.Label(tile, text=price_text, fg="#2ecc71", bg="#1e1e3f", font=("Arial", 10, "bold"))
            price_label.pack(fill="x", padx=5, pady=(0, 5))

            tile.book_id = book.id
            tile.book_index = i
            click_handler = lambda e, index=i, tile_ref=tile: self.on_book_select(index, tile_ref)
            tile.bind("<Button-1>", click_handler)
            cover_frame.bind("<Button-1>", click_handler)
            title_label.bind("<Button-1>", click_handler)
            price_label.bind("<Button-1>", click_handler)
            cover_label.bind("<Button-1>", click_handler)

        self.tile_container.update_idletasks()
        self.books_canvas.config(scrollregion=self.books_canvas.bbox("all"))
        self.update_cart_display()

    def on_book_select(self, index, tile_ref):
        """Handle book tile selection and update details pane."""
        if self.selected_tile:
            self.selected_tile.config(bg="#1e1e3f", highlightbackground="white",
                                      highlightthickness=1)

        self.selected_book_id = self.dm.books[index].id
        self.selected_tile = tile_ref
        self.selected_tile.config(bg="#4a90e2", highlightbackground="cyan",
                                  highlightthickness=2)

        book = self.dm.books[index]
        self.book_details.config(state="normal")
        self.book_details.delete("1.0", tk.END)
        self.book_details.insert(tk.END, str(book))
        self.book_details.config(state="disabled")

    def add_to_cart(self):
        if not self.selected_book_id:
            messagebox.showwarning("Warning", "Select a book first.")
            return

        selected_book = None
        for book in self.dm.books:
            if book.id == self.selected_book_id:
                selected_book = book
                break

        if not selected_book:
            messagebox.showerror("Error", "Selected book not found.")
            return

        for item in self.cart:
            if item["book"].id == selected_book.id:
                item["quantity"] += 1
                break
        else:
            self.cart.append({"book": selected_book, "quantity": 1})
        self.update_cart_display()

    def remove_cart_item(self):
        sel = self.cart_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a cart item to remove.")
            return
        idx = sel[0]
        item = self.cart[idx]
        if item["quantity"] > 1:
            item["quantity"] -= 1
        else:
            self.cart.pop(idx)
        self.update_cart_display()

    def clear_cart(self):
        if not self.cart:
            messagebox.showinfo("Cart", "Cart is already empty.")
            return
        if messagebox.askyesno("Confirm", "Clear all items from cart?"):
            self.cart.clear()
            self.update_cart_display()
            messagebox.showinfo("Cart Cleared", "Your cart has been emptied.")

    def update_cart_display(self):
        self.cart_listbox.delete(0, tk.END)
        total = 0.0
        for item in self.cart:
            book = item["book"]
            qty = item["quantity"]
            line_total = book.price * qty
            total += line_total
            self.cart_listbox.insert(tk.END, f"{book.title} (x{qty}) - ₱{line_total:.2f}")
        self.total_label.config(text=f"Total: ₱{total:.2f}")

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Warning", "Your cart is empty.")
            return
        total = sum(item["book"].price * item["quantity"] for item in self.cart)
        items_payload = []
        for item in self.cart:
            items_payload.append({
                "id": item["book"].id,
                "title": item["book"].title,
                "author": item["book"].author,
                "price": item["book"].price,
                "quantity": item["quantity"]
            })
        self.dm.add_order(self.username, items_payload, total)
        if messagebox.askyesno("Confirm Purchase", f"Proceed to purchase?\nTotal: ₱{total:.2f}"):
            self.cart.clear()
            self.update_cart_display()
            messagebox.showinfo("Purchase Successful", f"Thank you for your purchase!\nTotal paid: ₱{total:.2f}")
            try:
                if self.admin_window and hasattr(self.admin_window, "refresh_all"):
                    self.admin_window.refresh_all()
            except Exception:
                pass

    def open_profile(self):
        ProfileWindow(self.username, self.dm, self.root)

    def open_admin_panel(self):
        if self.username != "admin":
            messagebox.showerror("Forbidden", "Admin panel is only for admin user.")
            return
        if self.admin_window and getattr(self.admin_window, "win",
                                         None) and tk.Toplevel.winfo_exists(self.admin_window.win):
            try:
                self.admin_window.win.lift()
                return
            except Exception:
                pass
        self.admin_window = AdminPanel(self.dm, parent=self.root, refresh_callback=self.refresh_book_list)

    def logout(self):
        if messagebox.askyesno("Logout", "Log out and return to login screen?"):
            try:
                if self.admin_window and getattr(self.admin_window, "win",
                                                 None) and tk.Toplevel.winfo_exists(self.admin_window.win):
                    self.admin_window.win.destroy()
            except Exception:
                pass
            self.root.destroy()
            main()

    def run(self):
        self.root.mainloop()


# -------------------------
# Profile Window
# -------------------------
class ProfileWindow:
    def __init__(self, username: str, dm: DataManager, parent):
        self.dm = dm
        self.win = tk.Toplevel(parent)
        self.win.title("Profile")
        self.win.geometry("420x320")
        self.win.configure(bg="#0a0a23")
        self.win.minsize(300, 250)

        tk.Label(self.win, text=f"Profile: {username}", font=("Arial", 14, "bold"), bg="#0a0a23", fg="white").pack(
            pady=8)
        tk.Label(self.win, text="Registered users (admin view):", font=("Arial", 10), bg="#0a0a23", fg="white").pack(
            anchor="w", padx=8)
        users_box = scrolledtext.ScrolledText(self.win, height=10, bg="#1e1e3f", fg="white")
        users_box.pack(fill="both", expand=True, padx=8, pady=6)

        for u in sorted(self.dm.users.keys()):
            blocked_flag = " (blocked)" if self.dm.users[u].get("blocked") else ""
            users_box.insert(tk.END, f"{u}{blocked_flag}\n")
        users_box.config(state="disabled")
        tk.Button(self.win, text="Close", command=self.win.destroy).pack(pady=6)


# -------------------------
# Admin Panel
# -------------------------
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

        # Left - Books
        left = tk.Frame(self.win, bg="#1e1e3f")
        left.place(relx=0.01, rely=0.01, relwidth=0.48, relheight=0.98)
        tk.Label(left, text="Books Management", fg="white", bg="#1e1e3f", font=("Arial", 12, "bold")).pack(anchor="w",
                                                                                                           padx=8,
                                                                                                           pady=(8,
                                                                                                                 2))
        self.books_listbox = tk.Listbox(left, bg="#2a2a4a", fg="white", selectbackground="#4a90e2")
        self.books_listbox.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        book_btn_frame = tk.Frame(left, bg="#1e1e3f")
        book_btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(book_btn_frame, text="Add Book", command=self.add_book_dialog, bg="#2ecc71", fg="white").pack(
            side="left", padx=6)
        tk.Button(book_btn_frame, text="Edit Selected", command=self.edit_book_dialog, bg="#4a90e2", fg="white").pack(
            side="left", padx=6)
        tk.Button(book_btn_frame, text="Delete Selected", command=self.delete_selected_book, bg="#e74c3c",
                  fg="white").pack(side="left", padx=6)

        # Right - Users & Orders
        right = tk.Frame(self.win, bg="#1e1e3f")
        right.place(relx=0.50, rely=0.01, relwidth=0.49, relheight=0.98)
        tk.Label(right, text="Registered Users", fg="white", bg="#1e1e3f", font=("Arial", 12, "bold")).pack(anchor="w",
                                                                                                            padx=8,
                                                                                                            pady=(8,
                                                                                                                  2))
        self.users_listbox = tk.Listbox(right, height=6, bg="#2a2a4a", fg="white", selectbackground="#4a90e2")
        self.users_listbox.pack(fill="x", padx=8, pady=(4, 8))
        user_btn_frame = tk.Frame(right, bg="#1e1e3f")
        user_btn_frame.pack(fill="x", padx=8)
        tk.Button(user_btn_frame, text="Block", command=self.block_selected_user, bg="#f39c12", fg="white").pack(
            side="left", padx=4)
        tk.Button(user_btn_frame, text="Unblock", command=self.unblock_selected_user, bg="#27ae60", fg="white").pack(
            side="left", padx=4)
        tk.Button(user_btn_frame, text="Delete", command=self.delete_selected_user, bg="#e74c3c", fg="white").pack(
            side="left", padx=4)

        tk.Label(right, text="Orders (latest first)", fg="white", bg="#1e1e3f", font=("Arial", 12, "bold")).pack(
            anchor="w", padx=8, pady=(8, 2))
        self.orders_text = scrolledtext.ScrolledText(right, height=12, state="disabled", bg="#2a2a4a", fg="white")
        self.orders_text.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        sales_frame = tk.Frame(right, bg="#1e1e3f")
        sales_frame.pack(fill="x", padx=8, pady=(4, 8))
        tk.Label(sales_frame, text="Total Sales:", fg="white", bg="#1e1e3f", font=("Arial", 11, "bold")).pack(
            side="left")
        self.total_sales_label = tk.Label(sales_frame, text="₱0.00", fg="white", bg="#1e1e3f",
                                          font=("Arial", 11, "bold"))
        self.total_sales_label.pack(side="left", padx=8)

        admin_btn_frame = tk.Frame(right, bg="#1e1e3f")
        admin_btn_frame.pack(fill="x", padx=8, pady=(4, 8))
        tk.Button(admin_btn_frame, text="Refresh", command=self.refresh_all, bg="#4a90e2", fg="white").pack(side="left",
                                                                                                            padx=6)
        tk.Button(admin_btn_frame, text="Export Orders Report", command=self.export_orders_report, bg="#4a90e2",
                  fg="white").pack(side="left", padx=6)
        tk.Button(admin_btn_frame, text="Reset Demo Data", command=self.reset_demo_data, bg="#e67e22",
                  fg="white").pack(side="left", padx=6)

        # initial population
        self.refresh_all()

    def refresh_books_listbox(self):
        self.books_listbox.delete(0, tk.END)
        for b in self.dm.books:
            cover_status = " [Cover]" if b.cover_path else ""
            self.books_listbox.insert(tk.END, f"{b.title} — {b.author} — ₱{b.price:.2f}{cover_status}")

    def add_book_dialog(self):
        # MODIFIED: Pass empty cover_path
        dlg = BookEditDialog(self.win, title="Add Book", initial=("", "", "0.00", "", ""))
        if dlg.result:
            title, author, price, description, cover_path = dlg.result
            try:
                pricef = float(price)
            except ValueError:
                messagebox.showerror("Invalid Price", "Price must be a number.")
                return
            # MODIFIED: Use cover_path
            new_book = Book(title, author, pricef, description, cover_path=cover_path)
            self.dm.add_book(new_book)
            messagebox.showinfo("Added", f"Book '{title}' added.")
            self.refresh_all()
            if self.refresh_callback:
                self.refresh_callback()

    def edit_book_dialog(self):
        sel = self.books_listbox.curselection()
        if not sel:
            messagebox.showwarning("Select Book", "Select a book to edit.")
            return
        book = self.dm.books[sel[0]]
        # MODIFIED: Pass existing cover_path
        dlg = BookEditDialog(self.win, title="Edit Book",
                             initial=(book.title, book.author, str(book.price), book.description, book.cover_path))
        if dlg.result:
            title, author, price, description, cover_path = dlg.result
            try:
                pricef = float(price)
            except ValueError:
                messagebox.showerror("Invalid Price", "Price must be a number.")
                return
            # MODIFIED: Pass cover_path to update_book
            updated = self.dm.update_book(book.id, title, author, pricef, description, cover_path)
            if updated:
                messagebox.showinfo("Updated", f"Book '{title}' updated.")
                self.refresh_all()
                if self.refresh_callback:
                    self.refresh_callback()
            else:
                messagebox.showerror("Error", "Failed to update book.")

    def delete_selected_book(self):
        sel = self.books_listbox.curselection()
        if not sel:
            messagebox.showwarning("Select Book", "Select a book to delete.")
            return
        book = self.dm.books[sel[0]]
        confirm = messagebox.askyesno("Confirm Delete", f"Delete '{book.title}'?")
        if confirm:
            deleted = self.dm.delete_book(book.id)
            if deleted:
                messagebox.showinfo("Deleted", f"Book '{book.title}' deleted.")
                self.refresh_all()
                if self.refresh_callback:
                    self.refresh_callback()
            else:
                messagebox.showerror("Error", "Could not delete book.")

    def refresh_users_display(self):
        self.users_listbox.delete(0, tk.END)
        for u in sorted(self.dm.users.keys()):
            blocked_flag = " (blocked)" if self.dm.users[u].get("blocked") else ""
            self.users_listbox.insert(tk.END, f"{u}{blocked_flag}")

    def get_selected_username(self):
        sel = self.users_listbox.curselection()
        if not sel:
            return None
        text = self.users_listbox.get(sel[0])
        username = text.split(" ")[0]
        return username

    def block_selected_user(self):
        username = self.get_selected_username()
        if not username:
            messagebox.showwarning("Select User", "Select a user to block.")
            return
        if username == "admin":
            messagebox.showerror("Forbidden", "Cannot block admin.")
            return
        if self.dm.block_user(username):
            messagebox.showinfo("Blocked", f"User '{username}' blocked.")
            self.refresh_all()

    def unblock_selected_user(self):
        username = self.get_selected_username()
        if not username:
            messagebox.showwarning("Select User", "Select a user to unblock.")
            return
        if username == "admin":
            messagebox.showerror("Forbidden", "Admin is always unblocked.")
            return
        if self.dm.unblock_user(username):
            messagebox.showinfo("Unblocked", f"User '{username}' unblocked.")
            self.refresh_all()

    def delete_selected_user(self):
        username = self.get_selected_username()
        if not username:
            messagebox.showwarning("Select User", "Select a user to delete.")
            return
        if username == "admin":
            messagebox.showerror("Forbidden", "Cannot delete admin.")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Delete user '{username}'? This cannot be undone.")
        if confirm:
            if self.dm.delete_user(username):
                messagebox.showinfo("Deleted", f"User '{username}' deleted.")
                self.refresh_all()
            else:
                messagebox.showerror("Error", "Could not delete user.")

    def refresh_orders_display(self):
        self.orders_text.config(state="normal")
        self.orders_text.delete("1.0", tk.END)
        if not self.dm.orders:
            self.orders_text.insert(tk.END, "No orders yet.\n")
        else:
            for o in reversed(self.dm.orders):
                self.orders_text.insert(tk.END, f"Order ID: {o['id']}\n")
                self.orders_text.insert(tk.END,
                                        f"User: {o['username']}  Date: {o['date']}  Total: ₱{o['total']:.2f}\n")
                self.orders_text.insert(tk.END, "Items:\n")
                for it in o["items"]:
                    self.orders_text.insert(tk.END,
                                            f"  - {it['title']} by {it['author']} x{it['quantity']} - ₱{it['price']:.2f}\n")
                self.orders_text.insert(tk.END, "-" * 48 + "\n")
        self.orders_text.config(state="disabled")

    def refresh_total_sales(self):
        total = self.dm.total_sales()
        self.total_sales_label.config(text=f"₱{total:.2f}")

    def refresh_all(self):
        self.refresh_books_listbox()
        self.refresh_users_display()
        self.refresh_orders_display()
        self.refresh_total_sales()

    def export_orders_report(self):
        if not self.dm.orders:
            messagebox.showinfo("No Orders", "There are no orders to export.")
            return
        try:
            filename = "orders_report.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for o in reversed(self.dm.orders):
                    f.write(f"Order ID: {o['id']}\n")
                    f.write(f"User: {o['username']}  Date: {o['date']}  Total: ₱{o['total']:.2f}\n")
                    f.write("Items:\n")
                    for it in o["items"]:
                        f.write(
                            f"  - {it['title']} by {it['author']} x{it['quantity']} - ₱{it['price']:.2f}\n")
                    f.write("-" * 48 + "\n")
            messagebox.showinfo("Exported", f"Orders exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write report: {e}")

    def reset_demo_data(self):
        confirm = messagebox.askyesno("Reset Demo Data",
                                      "Reset books, remove all users except admin, and clear orders?")
        if confirm:
            self.dm.reset_demo_data()
            messagebox.showinfo("Reset", "Demo data restored.")
            self.refresh_all()
            if self.refresh_callback:
                self.refresh_callback()


# -------------------------
# Dialog: Book edit/add
# -------------------------
import os  # Ensure you have os imported at the top of your file for os.path.basename


class BookEditDialog(simpledialog.Dialog):
    # MODIFIED: Added cover_path to initial tuple
    def __init__(self, parent, title=None, initial=None):
        # initial now expects (title, author, price, description, cover_path)
        self.initial = initial
        self.cover_path = initial[4] if initial and len(initial) > 4 else ""
        super().__init__(parent, title=title)

    def select_cover(self):
        """Opens a file dialog to select a book cover image."""
        filetypes = (
            ('Image files', '*.jpg *.jpeg *.png'),
            ('All files', '*.*')
        )
        # Use initialdir=COVER_DIR if you want to start the dialog in the cover folder
        filepath = filedialog.askopenfilename(
            title="Select Book Cover",
            initialdir=os.getcwd(),
            filetypes=filetypes
        )
        if filepath:
            # We don't copy the file yet, just store the full path for now
            # In a production app, you would copy the file to COVER_DIR and store the relative path
            self.cover_path = filepath
            # REMOVED: self.cover_label.config(text=os.path.basename(filepath), fg="white")

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

        # NEW: Cover Photo fields
        tk.Label(master, text="Cover Photo:").grid(row=4, column=0, sticky="w")
        self.select_btn = tk.Button(master, text="Select Cover File", command=self.select_cover)
        self.select_btn.grid(row=4, column=1, sticky="w", pady=4)
        # REMOVED: self.cover_label = tk.Label(master, text="No file selected.", fg="yellow")
        # REMOVED: self.cover_label.grid(row=4, column=2, sticky="w", padx=10)

        # Adjusting column span for the button since the label is gone
        self.select_btn.grid(row=4, column=1, sticky="w", pady=4, columnspan=2)

        if self.initial:
            title, author, price, desc, cover_path = self.initial
            self.title_var.insert(0, title)
            self.author_var.insert(0, author)
            self.price_var.insert(0, price)
            self.desc_text.insert("1.0", desc)
            if cover_path:
                self.cover_path = cover_path
                # REMOVED: self.cover_label.config(text=os.path.basename(cover_path), fg="white")
        return self.title_var

    def apply(self):
        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        price = self.price_var.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        if not title or not author or not price:
            messagebox.showerror("Invalid", "Title, author, and price are required.")
            self.result = None
            return
        # MODIFIED: Include cover_path in result
        self.result = (title, author, price, description, self.cover_path)


# -------------------------
# Entrypoint
# -------------------------
def main():
    dm = DataManager()

    def on_login_success(username: str):
        app = OnlineBookstoreApp(username, dm)
        app.run()

    login = LoginWindow(dm, on_login_success)
    login.run()


if __name__ == "__main__":
    main()