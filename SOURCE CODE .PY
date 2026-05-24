import customtkinter as ctk
import os
import json
import threading
import time
import random
import string
import shutil
import requests
import platform
import ctypes
import qrcode
import pytz
import psutil
import pyperclip
from datetime import datetime
from tkinter import filedialog, messagebox, ImageTk
from PIL import Image
from plyer import notification

# --- AYARLAR VE YARDIMCILAR ---
APP_NAME = "SmartLife Assistant"
TODO_FILE = "todo.json"
NOTES_FILE = "notes.json"
BUDGET_FILE = "budget.json"
WEATHER_API_KEY = "319734a5f078e4f72e037b9c12d27890"

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_json(filepath, default):
    if not os.path.exists(filepath): return default
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- MODÜLLER ---

class TodoModule(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.todos = load_json(TODO_FILE, [])
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Yapılacaklar Listesi", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)
        self.entry = ctk.CTkEntry(self, placeholder_text="Yeni görev ekle...")
        self.entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self, text="Ekle", command=self.add_todo).grid(row=1, column=1, padx=20)
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Görevler")
        self.scroll.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)

    def add_todo(self):
        if t := self.entry.get():
            self.todos.append({"task": t, "done": False})
            save_json(TODO_FILE, self.todos)
            self.entry.delete(0, 'end')
            self.refresh_list()

    def refresh_list(self):
        for w in self.scroll.winfo_children(): w.destroy()
        for i, t in enumerate(self.todos):
            f = ctk.CTkFrame(self.scroll)
            f.pack(fill="x", pady=2)
            cb = ctk.CTkCheckBox(f, text=t["task"], command=lambda x=i: self.toggle(x))
            if t["done"]: cb.select()
            cb.pack(side="left", padx=10)
            ctk.CTkButton(f, text="Sil", width=60, command=lambda x=i: self.delete(x)).pack(side="right", padx=10)

    def toggle(self, i): self.todos[i]["done"] = not self.todos[i]["done"]; save_json(TODO_FILE, self.todos)
    def delete(self, i): self.todos.pop(i); save_json(TODO_FILE, self.todos); self.refresh_list()

class PomodoroModule(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.work_time, self.break_time = 25*60, 5*60
        self.current_time, self.is_running, self.is_work = self.work_time, False, True
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Pomodoro", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)
        self.time_label = ctk.CTkLabel(self, text="25:00", font=ctk.CTkFont(size=60, weight="bold"))
        self.time_label.grid(row=1, column=0, pady=40)
        self.start_btn = ctk.CTkButton(self, text="Başlat", command=self.toggle)
        self.start_btn.grid(row=2, column=0, pady=10)
        ctk.CTkButton(self, text="Sıfırla", fg_color="gray", command=self.reset).grid(row=3, column=0, pady=10)

    def toggle(self):
        self.is_running = not self.is_running
        self.start_btn.configure(text="Durdur" if self.is_running else "Başlat")
        if self.is_running: threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while self.is_running and self.current_time > 0:
            time.sleep(1)
            self.current_time -= 1
            m, s = divmod(self.current_time, 60)
            self.time_label.configure(text=f"{m:02d}:{s:02d}")
        if self.current_time == 0:
            self.is_work = not self.is_work
            self.current_time = self.work_time if self.is_work else self.break_time
            notification.notify(title="Pomodoro", message="Süre doldu!")
            self.reset()

    def reset(self): self.is_running = False; self.current_time = self.work_time; self.time_label.configure(text="25:00"); self.start_btn.configure(text="Başlat")

class MusicModule(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Medya Kontrolü", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)
        f = ctk.CTkFrame(self)
        f.grid(row=1, column=0, pady=20)
        ctk.CTkButton(f, text="-", width=50, command=lambda: self.send(0xAE)).pack(side="left", padx=5)
        ctk.CTkButton(f, text="🔇", width=50, command=lambda: self.send(0xAD)).pack(side="left", padx=5)
        ctk.CTkButton(f, text="+", width=50, command=lambda: self.send(0xAF)).pack(side="left", padx=5)
        m = ctk.CTkFrame(self, fg_color="transparent")
        m.grid(row=2, column=0, pady=20)
        ctk.CTkButton(m, text="⏮", width=60, command=lambda: self.send(0xB1)).pack(side="left", padx=10)
        ctk.CTkButton(m, text="⏯", width=80, command=lambda: self.send(0xB3)).pack(side="left", padx=10)
        ctk.CTkButton(m, text="⏭", width=60, command=lambda: self.send(0xB0)).pack(side="left", padx=10)

    def send(self, code):
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)

class ParentalModule(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Ebeveyn Kontrolü", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)
        self.pw = ctk.CTkEntry(self, show="*", placeholder_text="Acil Kapatma Şifresi (1234)")
        self.pw.grid(row=1, column=0, padx=20, pady=10)
        ctk.CTkButton(self, text="Sistemi Kapat", fg_color="red", command=self.shutdown).grid(row=2, column=0, pady=10)

    def shutdown(self):
        if self.pw.get() == "1234":
            try: ctypes.windll.user32.ExitWindowsEx(0x00000008, 0x00000000); os.system("shutdown -s -t 0")
            except: os.system("shutdown -s -t 0")
        else: messagebox.showerror("Hata", "Yanlış Şifre!")

# --- ANA UYGULAMA ---

class SmartLifeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.side = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.side.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.side, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        self.nav = ctk.CTkScrollableFrame(self.side, fg_color="transparent")
        self.nav.pack(fill="both", expand=True, padx=5)
        if hasattr(self.nav, "_label"): self.nav._label.destroy()

        self.btns = []
        menus = [("Yapılacaklar", 0), ("Pomodoro", 1), ("Medya", 2), ("Ebeveyn", 3)]
        for i, (txt, idx) in enumerate(menus):
            b = ctk.CTkButton(self.nav, text=txt, fg_color="transparent", anchor="w", command=lambda x=idx: self.show(x))
            b.pack(fill="x", pady=1)
            self.btns.append(b)

        self.cont = ctk.CTkFrame(self, fg_color="transparent")
        self.cont.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.cont.grid_columnconfigure(0, weight=1)
        self.cont.grid_rowconfigure(0, weight=1)

        self.mods = [TodoModule(self.cont), PomodoroModule(self.cont), MusicModule(self.cont), ParentalModule(self.cont)]
        self.show(0)

    def show(self, idx):
        for m in self.mods: m.grid_forget()
        for b in self.btns: b.configure(fg_color="transparent")
        self.mods[idx].grid(row=0, column=0, sticky="nsew")
        self.btns[idx].configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        # Simple animation
        self.mods[idx].grid_configure(pady=(40, 0))
        def anim(p):
            if p > 0: self.mods[idx].grid_configure(pady=(p-4, 0)); self.after(10, lambda: anim(p-4))
        anim(40)

if __name__ == "__main__":
    app = SmartLifeApp()
    app.mainloop()
