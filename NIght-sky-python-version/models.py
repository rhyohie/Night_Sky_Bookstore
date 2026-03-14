import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from config import *

def load_json(path: str, default: Any):
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
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save {path}: {e}")

class Book:
    def __init__(self, title: str, author: str, price: float, description: str,
                 cover_path: Optional[str] = None, book_id: Optional[str] = None):
        self.title = title
        self.author = author
        self.price = float(price)
        self.description = description
        self.cover_path = cover_path if cover_path else ""
        self.id = book_id or f"bk{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "title": self.title, "author": self.author, "price": self.price,
                "description": self.description, "cover_path": self.cover_path}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        return cls(d["title"], d["author"], d.get("price", 0.0), d.get("description", ""),
                   d.get("cover_path", ""), d.get("id"))

    def __str__(self) -> str:
        return (f"{self.title} by {self.author} - ₱{self.price:.2f}\n"
                f"Description: {self.description}")

class DataManager:
    def __init__(self):
        raw_users = load_json(USERS_FILE, DEFAULT_USERS)
        self.users: Dict[str, Dict[str, Any]] = {}
        for uname, val in raw_users.items():
            if isinstance(val, dict):
                self.users[uname] = {"password": val.get("password", ""), "blocked": bool(val.get("blocked", False))}
            else:
                self.users[uname] = {"password": str(val), "blocked": False}
        if self.users.get("admin", {}).get("password") != "987654321":
            self.users["admin"] = {"password": "987654321", "blocked": False}
            self.save_users()

        raw_books = load_json(BOOKS_FILE, DEFAULT_BOOKS)
        self.books: List[Book] = []
        for b in raw_books:
            if "id" not in b:
                b["id"] = f"bk{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
            try:
                b["price"] = float(b.get("price", 0.0))
            except Exception:
                b["price"] = 0.0
            if "cover_path" not in b:
                b["cover_path"] = ""
            self.books.append(Book.from_dict(b))

        self.orders: List[Dict[str, Any]] = load_json(ORDERS_FILE, DEFAULT_ORDERS)

    def save_users(self): save_json(USERS_FILE, self.users)
    def add_user(self, username: str, password: str) -> bool:
        if username in self.users: return False
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
        if not u or u.get("blocked"): return False
        return u.get("password") == password

    def save_books(self): save_json(BOOKS_FILE, [b.to_dict() for b in self.books])
    def add_book(self, book: Book):
        self.books.append(book)
        self.save_books()
    def update_book(self, book_id: str, title: str, author: str, price: float, description: str, cover_path: str) -> bool:
        for b in self.books:
            if b.id == book_id:
                b.title = title
                b.author = author
                b.price = float(price)
                b.description = description
                b.cover_path = cover_path
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

    def save_orders(self): save_json(ORDERS_FILE, self.orders)
    def add_order(self, username: str, items: List[Dict[str, Any]], total: float):
        order = {"id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"), "username": username,
                 "items": items, "total": float(total), "date": datetime.utcnow().isoformat()}
        self.orders.append(order)
        self.save_orders()
    def total_sales(self) -> float:
        return sum(o.get("total", 0.0) for o in self.orders)

    def reset_demo_data(self):
        self.books = [Book.from_dict(b) for b in DEFAULT_BOOKS]
        self.users = {"admin": {"password": "987654321", "blocked": False}}
        self.orders = []
        self.save_books()
        self.save_users()
        self.save_orders()