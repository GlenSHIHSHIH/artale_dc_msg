import tkinter as tk
import pyautogui

def update_position():
    x, y = pyautogui.position()
    position_label.config(text=f"滑鼠座標：({x}, {y})")
    root.after(100, update_position)  # 每 100 毫秒更新一次

root = tk.Tk()
root.title("滑鼠座標顯示器")

position_label = tk.Label(root, text="滑鼠座標：(0, 0)", font=("Arial", 16))
position_label.pack(padx=20, pady=20)

update_position()  # 啟動更新函數
root.mainloop()
