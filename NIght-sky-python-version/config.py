import os
from typing import Any, Dict, List

# --- NEW DIRECTORIES ---
DATA_DIR = "data"
COVER_DIR = "book_covers"

# --- UPDATED FILE PATHS ---
USERS_FILE = os.path.join(DATA_DIR, "users.json")
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")

DEFAULT_USERS = {"admin": {"password": "987654321", "blocked": False}}
DEFAULT_BOOKS = [{}]
DEFAULT_ORDERS: List[Dict[str, Any]] = []

# Auto-create the folders if they are missing
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(COVER_DIR):
    os.makedirs(COVER_DIR)