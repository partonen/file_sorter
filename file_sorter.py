import os
import shutil
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import time
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

# Настройки
DEFAULT_SORT_INTERVAL = 86400  # 24 часа по умолчанию
LOG_FILE = "sort_log.txt"

def log_action(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def sort_files(desktop_path, enable_compression=True):
    try:
        files = [f for f in os.listdir(desktop_path) if os.path.isfile(os.path.join(desktop_path, f))]
        for file in files:
            ext = file.split(".")[-1] if "." in file else "others"
            folder_path = os.path.join(desktop_path, ext)
            os.makedirs(folder_path, exist_ok=True)
            
            file_path = os.path.join(desktop_path, file)
            new_path = os.path.join(folder_path, file)
            shutil.move(file_path, new_path)
            log_action(f"Moved: {file} -> {folder_path}")
            
            if enable_compression:
                zip_path = os.path.join(folder_path, ext + ".zip")
                with zipfile.ZipFile(zip_path, 'a') as zipf:
                    zipf.write(new_path, file)
                os.remove(new_path)
                log_action(f"Archived: {file} -> {zip_path}")
    except Exception as e:
        log_action(f"Error: {str(e)}")

def auto_sort():
    global next_run
    while True:
        sort_files(desktop_path.get(), enable_compression.get())
        next_run = time.time() + sort_interval.get()
        for _ in range(sort_interval.get(), 0, -1):
            time.sleep(1)
            update_timer()

def start_auto_sort():
    thread = Thread(target=auto_sort, daemon=True)
    thread.start()
    messagebox.showinfo("Автоматическая сортировка", "Автоматическая сортировка запущена!")

def manual_sort():
    sort_files(desktop_path.get(), enable_compression.get())
    messagebox.showinfo("Сортировка завершена", "Файлы отсортированы!")

def create_image():
    image = Image.new('RGB', (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill=(0, 0, 255))
    return image

def show_settings():
    root.deiconify()

def exit_program():
    tray_icon.stop()
    root.quit()

def setup_tray():
    global tray_icon
    menu = (
        item('Открыть', show_settings),
        item('Сортировать', lambda: sort_files(desktop_path.get(), enable_compression.get())),
        item('Выход', exit_program)
    )
    tray_icon = pystray.Icon("file_sorter", create_image(), menu=menu)
    tray_icon.run()

def update_timer():
    remaining = max(0, int(next_run - time.time()))
    timer_label.config(text=f"Следующая сортировка через: {remaining} сек")
    root.after(1000, update_timer)

# GUI
root = tk.Tk()
root.title("Сортировщик файлов")
root.geometry("400x250")
root.protocol("WM_DELETE_WINDOW", lambda: root.withdraw())

desktop_path = tk.StringVar()
desktop_path.set(os.path.expanduser("~/Desktop"))

enable_compression = tk.BooleanVar()
enable_compression.set(True)

sort_interval = tk.IntVar()
sort_interval.set(DEFAULT_SORT_INTERVAL)

next_run = time.time() + DEFAULT_SORT_INTERVAL

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

label = ttk.Label(frame, text="Выберите папку для сортировки:")
label.pack()

entry = ttk.Entry(frame, textvariable=desktop_path, width=50)
entry.pack()

btn_browse = ttk.Button(frame, text="Обзор", command=lambda: desktop_path.set(filedialog.askdirectory()))
btn_browse.pack()

chk_compress = ttk.Checkbutton(frame, text="Сжимать файлы в ZIP", variable=enable_compression)
chk_compress.pack()

interval_label = ttk.Label(frame, text="Интервал сортировки (сек):")
interval_label.pack()
interval_entry = ttk.Entry(frame, textvariable=sort_interval)
interval_entry.pack()

timer_label = ttk.Label(frame, text="Следующая сортировка через: 0 сек")
timer_label.pack()

btn_sort = ttk.Button(frame, text="Отсортировать сейчас", command=manual_sort)
btn_sort.pack()

btn_auto_sort = ttk.Button(frame, text="Запустить авто-сортировку", command=start_auto_sort)
btn_auto_sort.pack()

update_timer()
Thread(target=setup_tray, daemon=True).start()
root.mainloop()