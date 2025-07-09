import tkinter as tk
from tkinter import filedialog
import pygetwindow as gw
import pyautogui
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pyperclip
import time
import cv2
import numpy as np
import json
import os
import re

# 設定 tesseract.exe 路徑（依實際安裝位置調整）
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

scale_factor = 8

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def read_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            text_input.delete("1.0", tk.END)
            text_input.insert(tk.END, text)
        file_path_label.config(text=f"目前載入：{file_path}", fg="blue")

def save_settings():
    text = text_input.get("1.0", tk.END).strip()
    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if not path:
        return
    config = {
        "window_title": window_name_entry.get().strip(),
        "search_keywords": search_text_input.get("1.0", tk.END).strip().splitlines(),
        "text_file_path": path.replace(".json", ".txt")
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    with open(config["text_file_path"], "w", encoding="utf-8") as f:
        f.write(text)
    file_path_label.config(text=f"✅ 已儲存設定：{path}", fg="green")

def load_settings():
    path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        window_name_entry.delete(0, tk.END)
        window_name_entry.insert(0, config.get("window_title", ""))
        search_text_input.delete("1.0", tk.END)
        search_text_input.insert("1.0", "\n".join(config.get("search_keywords", [])))
        text_file = config.get("text_file_path")
        if os.path.exists(text_file):
            with open(text_file, "r", encoding="utf-8") as f:
                text_input.delete("1.0", tk.END)
                text_input.insert("1.0", f.read())
            file_path_label.config(text=f"✅ 匯入：{text_file}", fg="blue")
        else:
            file_path_label.config(text="⚠️ 找不到文字檔", fg="red")
    except Exception as e:
        file_path_label.config(text=f"❌ 匯入錯誤：{e}", fg="red")

def preprocess_image(img):
    img = img.convert("L")  # 灰階
    img = img.resize((img.width * scale_factor, img.height * scale_factor), Image.BICUBIC)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = img.filter(ImageFilter.MedianFilter())
    return img

def switch_and_paste():
    keyword = window_name_entry.get().strip().lower()
    search_keywords = [kw.strip().lower() for kw in search_text_input.get("1.0", tk.END).splitlines() if kw.strip()]
    to_paste = text_input.get("1.0", tk.END).strip()

    windows = [w for w in gw.getWindowsWithTitle("") if keyword in w.title.lower()]
    if not windows:
        print("❌ 找不到視窗")
        return

    win = windows[0]
    win.activate()
    time.sleep(1)

    left, top, width, height = win.left, win.top, win.width, win.height
    region = (left, top, width // 3, height)
    screenshot = pyautogui.screenshot(region=region)
    win_title_safe = safe_filename(win.title).replace(" ", "")
    debug_path = f"debug.png"
    # debug position 
    json_path = f"result_{win_title_safe}.json"
    # debug position png
    # screenshot_path = f"screenshot_{win_title_safe}.png"
    # screenshot.save(screenshot_path)

    img = preprocess_image(screenshot)
    config = "--oem 3 --psm 1"
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang='chi_tra', config=config)
    ocr_text = pytesseract.image_to_string(img, lang='chi_tra', config=config)
    # print("📋 OCR 全文：\n" + ocr_text)

    # 將字詞依行號分組，算出每行的邊界框
    lines = {}
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        if word == "":
            continue
        block = data['block_num'][i]
        par = data['par_num'][i]
        line = data['line_num'][i]
        key = (block, par, line)

        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        right = x + w
        bottom = y + h

        if key not in lines:
            lines[key] = {
                'words': [],
                'left': x,
                'top': y,
                'right': right,
                'bottom': bottom
            }
        else:
            # 更新行的邊界範圍（取最小 left/top，最大 right/bottom）
            lines[key]['left'] = min(lines[key]['left'], x)
            lines[key]['top'] = min(lines[key]['top'], y)
            lines[key]['right'] = max(lines[key]['right'], right)
            lines[key]['bottom'] = max(lines[key]['bottom'], bottom)

        lines[key]['words'].append(word)

    cv_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    # debug position 
    result_data = {"window_title": win.title, "match": []}
    found = False

    # 全螢幕截圖並畫紅框
    full_screenshot = pyautogui.screenshot()
    full_img = cv2.cvtColor(np.array(full_screenshot), cv2.COLOR_RGB2BGR)
    full_debug_path = f"full_debug.png"

    for key, info in lines.items():
        line_text = "".join(info['words']).lower().replace(" ", "")
        for keyword in search_keywords:
            if keyword in line_text:
                left_ = int(info['left'] / scale_factor)
                top_ = int(info['top'] / scale_factor)
                right_ = int(info['right'] / scale_factor)
                bottom_ = int(info['bottom'] / scale_factor)

                # print(f"畫框座標：{left_}, {top_}, {right_}, {bottom_}")

                cv2.rectangle(cv_img, (left_, top_), (right_, bottom_), (0, 0, 255),3)

                # 計算框中心全局座標
                global_x = left + left_ + (right_ - left_) // 2
                global_y = top + top_ + (bottom_ - top_) // 2
                # print(f"紅點座標：{global_x}, {global_y}")
                cv2.circle(full_img, (global_x, global_y), radius=10, color=(0, 0, 255), thickness=-1)
                # cv2.imshow("Red Rectangle", cv_img)

                # debug position 
                result_data["match"].append({
                    "keyword": keyword,
                    "line_text": line_text,
                    "relative_coords": {"x": left_, "y": top_, "w": right_ - left_, "h": bottom_ - top_},
                    "global_click": {"x": global_x, "y": global_y}
                })

                # print(f"Block {key[0]}, Par {key[1]}, Line {key[2]}: {line_text}")
                # print(f"keyword {keyword}")
                found = True

                pyautogui.click(global_x, global_y)
                time.sleep(10)
                pyperclip.copy(to_paste)
                time.sleep(3)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(2)
                pyautogui.press("enter")
                time.sleep(2)
                break

    cv2.imwrite(debug_path, cv_img)
    # debug position 
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    cv2.imwrite(full_debug_path, full_img)

    print("✅ 成功" if found else "❌ 無匹配")
    print(f"🔴 紅框圖：{debug_path}")
    print(f"🔴 全局紅框圖：{full_debug_path}")
    print(f"📝 匹配資訊：{json_path}")

def toggle_loop():
    global is_running, after_id
    if is_running:
        is_running = False
        run_button.config(text="執行")
        if after_id:
            root.after_cancel(after_id)
    else:
        is_running = True
        run_button.config(text="停止")
        run_loop()

def run_loop():
    global after_id
    if not is_running:
        return
    switch_and_paste()
    wait_time = float(wait_time_entry.get())
    after_id = root.after(int(wait_time * 1000), run_loop)


# GUI Layout
root = tk.Tk()
root.title("OCR 點擊貼上工具")

tk.Label(root, text="視窗標題（包含即可）：").pack()
window_name_entry = tk.Entry(root)
window_name_entry.pack()

tk.Label(root, text="搜尋文字（每行一筆）：").pack()
search_text_input = tk.Text(root, height=5)
search_text_input.pack()

tk.Label(root, text="等待秒數：").pack()
wait_time_entry = tk.Entry(root)
wait_time_entry.insert(0, "130")  # 預設 130 秒
wait_time_entry.pack()


frame = tk.Frame(root)
frame.pack()
tk.Button(frame, text="讀取文字檔", command=read_file).pack(side="left", padx=5)
tk.Button(frame, text="儲存設定", command=save_settings).pack(side="left", padx=5)
tk.Button(frame, text="載入設定", command=load_settings).pack(side="left", padx=5)

file_path_label = tk.Label(root, text="尚未載入檔案", fg="gray")
file_path_label.pack()

text_input = tk.Text(root, height=10)
text_input.pack()

# 控制狀態 flag 和排程 ID
is_running = False
after_id = None

run_button = tk.Button(root, text="執行", command=toggle_loop)
run_button.pack(pady=10)

root.mainloop()
