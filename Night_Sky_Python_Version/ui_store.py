import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import os
from models import DataManager
from ui_core import NightSkyCanvas, center_window
from ui_admin import AdminPanel
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Dependency Error", "Pillow (PIL) is required. Install with 'pip install Pillow'.")
    sys.exit(1)

class OnlineBookstoreApp:
    def __init__(self, username: str, data_manager: DataManager, on_logout_callback):
        self.username = username
        self.dm = data_manager
        self.on_logout_callback = on_logout_callback
        self.admin_window = None

        self.root = tk.Tk()
        self.root.title(f"Night Sky Bookstore — Logged in as: {username}")
        center_window(self.root, 1300, 900)
        self.root.resizable(False, False)
        self.root.configure(bg="#0a0a23")

        self.bg = NightSkyCanvas(self.root, width=1300, height=900, star_count=100)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)

        top_controls = tk.Frame(self.root, bg="#0a0a23")
        top_controls.pack(side="top", fill="x", pady=5, padx=10)
        tk.Label(top_controls, text="", bg="#0a0a23").pack(side="left", expand=True)

        tk.Button(top_controls, text="Logout", command=self.logout, bg="#666", fg="white", bd=0, padx=8, pady=4).pack(side="right", padx=(0, 6))
        if username == "admin":
            tk.Button(top_controls, text="Admin Panel", command=self.open_admin_panel, bg="#e67e22", fg="white", bd=0, padx=8, pady=4).pack(side="right", padx=6)

        main_frame = tk.Frame(self.root, bg="#0a0a23")
        main_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        left_frame = tk.Frame(main_frame, bg="#1e1e3f")
        left_frame.place(relx=0, rely=0, relwidth=0.59, relheight=1)
        tk.Label(left_frame, text="Available Books:", fg="white", bg="#1e1e3f", font=("Arial", 14, "bold")).pack(anchor="w", padx=8, pady=(8, 0))

        book_display_frame = tk.Frame(left_frame, bg="#1e1e3f")
        book_display_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self.books_canvas = tk.Canvas(book_display_frame, bg="#1e1e3f", highlightthickness=0)
        self.books_canvas.pack(side="left", fill="both", expand=True)
        book_scrollbar = tk.Scrollbar(book_display_frame, orient="vertical", command=self.books_canvas.yview)
        book_scrollbar.pack(side="right", fill="y")
        self.books_canvas.configure(yscrollcommand=book_scrollbar.set)
        self.tile_container = tk.Frame(self.books_canvas, bg="#1e1e3f")
        self.books_canvas_window = self.books_canvas.create_window((0, 0), window=self.tile_container, anchor="nw")

        self.tile_container.bind("<Configure>", lambda e: self.books_canvas.configure(scrollregion=self.books_canvas.bbox("all")))
        self.books_canvas.bind("<Configure>", lambda e: self.books_canvas.itemconfig(self.books_canvas_window, width=e.width))

        for w in [self.books_canvas, self.tile_container]:
            w.bind("<MouseWheel>", self._on_mousewheel)
            w.bind("<Button-4>", self._on_mousewheel)
            w.bind("<Button-5>", self._on_mousewheel)

        self.selected_book_id = None
        self.selected_tile = None
        self.image_references = {}

        details_frame = tk.Frame(left_frame, bg="#1e1e3f")
        details_frame.pack(fill="x", padx=8, pady=(2, 8))
        self.book_details = scrolledtext.ScrolledText(details_frame, height=5, bg="#2a2a4a", fg="white", font=("Arial", 12), state="disabled")
        self.book_details.pack(fill="x")

        btn_frame = tk.Frame(left_frame, bg="#1e1e3f")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(btn_frame, text="Add to Cart", command=self.add_to_cart, bg="#4a90e2", fg="white").pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="Refresh", command=self.refresh_book_list, bg="#4a90e2", fg="white").pack(side="left")

        right_frame = tk.Frame(main_frame, bg="#1e1e3f")
        right_frame.place(relx=0.60, rely=0, relwidth=0.40, relheight=1)
        tk.Label(right_frame, text="Shopping Cart:", fg="white", bg="#1e1e3f", font=("Arial", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 0))
        self.cart_listbox = tk.Listbox(right_frame, bg="#2a2a4a", fg="white", selectbackground="#4a90e2", font=("Arial", 12))
        self.cart_listbox.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        total_frame = tk.Frame(right_frame, bg="#1e1e3f")
        total_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.total_label = tk.Label(total_frame, text="Total: ₱0.00", fg="white", bg="#1e1e3f", font=("Arial", 12, "bold"))
        self.total_label.pack(side="left")

        cart_btn_frame = tk.Frame(right_frame, bg="#1e1e3f")
        cart_btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(cart_btn_frame, text="Remove Selected", command=self.remove_cart_item, bg="#4a90e2", fg="white").pack(side="left", padx=(0, 6))
        tk.Button(cart_btn_frame, text="Clear Cart", command=self.clear_cart, bg="#4a90e2", fg="white").pack(side="left", padx=(0, 6))
        tk.Button(cart_btn_frame, text="Checkout", command=self.checkout, bg="#2ecc71", fg="white").pack(side="left", padx=(10, 0))

        self.cart = []
        self.refresh_book_list()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _on_mousewheel(self, event):
        if sys.platform.startswith('win') or sys.platform.startswith('darwin'):
            self.books_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4: self.books_canvas.yview_scroll(-1, "units")
        elif event.num == 5: self.books_canvas.yview_scroll(1, "units")

    def refresh_book_list(self):
        for widget in self.tile_container.winfo_children(): widget.destroy()
        self.image_references.clear()
        self.selected_book_id = None
        self.selected_tile = None
        self.book_details.config(state="normal")
        self.book_details.delete("1.0", tk.END)
        self.book_details.config(state="disabled")

        books_per_row, tile_width, tile_height = 4, 150, 250
        cover_height = int(tile_height * 0.7)

        for i, book in enumerate(self.dm.books):
            tile = tk.Frame(self.tile_container, width=tile_width, height=tile_height, bg="#1e1e3f", bd=1, relief="solid", highlightbackground="white", highlightthickness=1)
            tile.grid(row=i // books_per_row, column=i % books_per_row, padx=10, pady=10, sticky="nsew")
            tile.grid_propagate(False)

            cover_frame = tk.Frame(tile, bg="#2a2a4a", width=tile_width - 10, height=cover_height)
            cover_frame.pack(pady=(5, 0))
            cover_frame.pack_propagate(False)

            cover_label = tk.Label(cover_frame, text="Cover\n(Image Not Loaded)", fg="#777", bg="#2a2a4a", font=("Arial", 10))
            cover_label.place(relx=0.5, rely=0.5, anchor="center")

            if book.cover_path and os.path.exists(book.cover_path):
                try:
                    img = Image.open(book.cover_path)
                    ratio = min((tile_width - 10) / img.size[0], cover_height / img.size[1])
                    photo = ImageTk.PhotoImage(img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.Resampling.LANCZOS))
                    self.image_references[book.id] = photo
                    cover_label.config(text="", image=photo, bg="#2a2a4a")
                except Exception as e:
                    cover_label.config(text="Cover\n(Load Error)", fg="#e74c3c")
            else:
                cover_label.config(text="Cover\n(No Image)", fg="#777")

            title_label = tk.Label(tile, text=f"{book.title}", fg="white", bg="#1e1e3f", font=("Arial", 9, "bold"), wraplength=tile_width - 10, justify="center")
            title_label.pack(fill="x", padx=5, pady=(2, 0))
            price_label = tk.Label(tile, text=f"₱{book.price:.2f}", fg="#2ecc71", bg="#1e1e3f", font=("Arial", 10, "bold"))
            price_label.pack(fill="x", padx=5, pady=(0, 5))

            click_handler = lambda e, index=i, tile_ref=tile: self.on_book_select(index, tile_ref)
            for item in [tile, cover_frame, title_label, price_label, cover_label]:
                item.bind("<Button-1>", click_handler)

        self.tile_container.update_idletasks()
        self.books_canvas.config(scrollregion=self.books_canvas.bbox("all"))
        self.update_cart_display()

    def on_book_select(self, index, tile_ref):
        if self.selected_tile: self.selected_tile.config(bg="#1e1e3f", highlightbackground="white", highlightthickness=1)
        self.selected_book_id = self.dm.books[index].id
        self.selected_tile = tile_ref
        self.selected_tile.config(bg="#4a90e2", highlightbackground="cyan", highlightthickness=2)
        
        self.book_details.config(state="normal")
        self.book_details.delete("1.0", tk.END)
        self.book_details.insert(tk.END, str(self.dm.books[index]))
        self.book_details.config(state="disabled")

    def add_to_cart(self):
        if not self.selected_book_id: return messagebox.showwarning("Warning", "Select a book first.")
        book = next((b for b in self.dm.books if b.id == self.selected_book_id), None)
        if not book: return messagebox.showerror("Error", "Selected book not found.")
        
        for item in self.cart:
            if item["book"].id == book.id:
                item["quantity"] += 1
                break
        else:
            self.cart.append({"book": book, "quantity": 1})
        self.update_cart_display()

    def remove_cart_item(self):
        sel = self.cart_listbox.curselection()
        if not sel: return messagebox.showwarning("Warning", "Select a cart item to remove.")
        if self.cart[sel[0]]["quantity"] > 1: self.cart[sel[0]]["quantity"] -= 1
        else: self.cart.pop(sel[0])
        self.update_cart_display()

    def clear_cart(self):
        if not self.cart: return
        if messagebox.askyesno("Confirm", "Clear all items from cart?"):
            self.cart.clear()
            self.update_cart_display()

    def update_cart_display(self):
        self.cart_listbox.delete(0, tk.END)
        total = sum(item["book"].price * item["quantity"] for item in self.cart)
        for item in self.cart:
            self.cart_listbox.insert(tk.END, f"{item['book'].title} (x{item['quantity']}) - ₱{item['book'].price * item['quantity']:.2f}")
        self.total_label.config(text=f"Total: ₱{total:.2f}")

    def checkout(self):
        if not self.cart: return messagebox.showwarning("Warning", "Your cart is empty.")
        total = sum(item["book"].price * item["quantity"] for item in self.cart)
        items = [{"id": i["book"].id, "title": i["book"].title, "author": i["book"].author, "price": i["book"].price, "quantity": i["quantity"]} for i in self.cart]
        self.dm.add_order(self.username, items, total)
        if messagebox.askyesno("Confirm Purchase", f"Proceed to purchase?\nTotal: ₱{total:.2f}"):
            self.cart.clear()
            self.update_cart_display()
            messagebox.showinfo("Purchase Successful", f"Thank you!\nTotal paid: ₱{total:.2f}")
            if self.admin_window and hasattr(self.admin_window, "refresh_all"): self.admin_window.refresh_all()

    def open_admin_panel(self):
        if self.username != "admin": return messagebox.showerror("Forbidden", "Admin panel is only for admin user.")
        if self.admin_window and getattr(self.admin_window, "win", None) and tk.Toplevel.winfo_exists(self.admin_window.win):
            try: return self.admin_window.win.lift()
            except Exception: pass
        self.admin_window = AdminPanel(self.dm, parent=self.root, refresh_callback=self.refresh_book_list)

    def logout(self):
        if messagebox.askyesno("Logout", "Log out and return to login screen?"):
            try:
                if self.admin_window and getattr(self.admin_window, "win", None) and tk.Toplevel.winfo_exists(self.admin_window.win):
                    self.admin_window.win.destroy()
            except Exception: pass
            self.root.destroy()
            self.on_logout_callback()

    def run(self): self.root.mainloop()

class ProfileWindow:
    def __init__(self, username: str, dm: DataManager, parent):
        self.dm = dm
        self.win = tk.Toplevel(parent)
        self.win.title("Profile")
        self.win.geometry("420x320")
        self.win.configure(bg="#0a0a23")

        tk.Label(self.win, text=f"Profile: {username}", font=("Arial", 14, "bold"), bg="#0a0a23", fg="white").pack(pady=8)
        tk.Label(self.win, text="Registered users:", font=("Arial", 10), bg="#0a0a23", fg="white").pack(anchor="w", padx=8)
        users_box = scrolledtext.ScrolledText(self.win, height=10, bg="#1e1e3f", fg="white")
        users_box.pack(fill="both", expand=True, padx=8, pady=6)

        for u in sorted(self.dm.users.keys()):
            users_box.insert(tk.END, f"{u}{' (blocked)' if self.dm.users[u].get('blocked') else ''}\n")
        users_box.config(state="disabled")
        tk.Button(self.win, text="Close", command=self.win.destroy).pack(pady=6)