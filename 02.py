import os
import time
import glob
import sys
import datetime
from seleniumbase import SB
import tkinter as tk
from PIL import Image, ImageTk


# --- 1. 自動路徑偵測 (確保圖片與打包相容) ---
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# --- 2. 基礎配置 (改為通用路徑) ---
VERSION = "2.4"
DEVELOPER = "蘇小偉"
TODAY_DATE = datetime.date.today().strftime("%Y-%m-%d")
TARGET_URL = "https://bb.sustech.edu.cn/"
USER_DATA_DIR = os.path.abspath("bb_session_profile")

# 【關鍵修改】：自動獲取目前使用者的「下載」資料夾，確保在任何電腦都能跑
FINAL_SAVE_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "BB_Downloads_by_Su")

if not os.path.exists(FINAL_SAVE_DIR):
    os.makedirs(FINAL_SAVE_DIR)


# --- 3. 核心功能 ---

def wait_for_downloads(download_dir, timeout=30):
    print("\n⏳ 正在確認下載進度...", end="", flush=True)
    time.sleep(3)
    start_time = time.time()
    while time.time() - start_time < timeout:
        crdownloads = [f for f in glob.glob(os.path.join(download_dir, "*.crdownload"))]
        if not crdownloads:
            print(" ✅ 全部下載完成！")
            return
        print(".", end="", flush=True)
        time.sleep(2)
    print(" ⚠️ 檢查完畢。")


def scan_and_download(sb, is_auto=False):
    print(f"\n📂 [掃描] {sb.get_current_url()[:50]}...")
    sb.switch_to_default_content()
    sb.sleep(1.5)
    for frame in ['iframe#contentFrame', 'iframe#container', 'iframe#mainFrame']:
        if sb.is_element_present(frame):
            sb.switch_to_frame(frame)
            break

    links = sb.find_elements("a")
    valid_links = []
    seen = set()
    for link in links:
        try:
            href = link.get_attribute("href")
            if href and any(k in href for k in ["bbcswebdav", "xid-", "pid-", "content"]):
                clean_url = href.lower().split('?')[0]
                if not (clean_url.endswith(".htm") or clean_url.endswith(".html")):
                    if href not in seen:
                        seen.add(href)
                        valid_links.append(href)
        except:
            continue

    if not valid_links:
        print("ℹ️ 無文件。")
        return

    for url in valid_links:
        try:
            sb.execute_script(
                f"var a=document.createElement('a'); a.href='{url}'; a.download=''; document.body.appendChild(a); a.click();")
            sb.sleep(0.8)
        except:
            continue

    sb.sleep(3)
    if not is_auto:
        wait_for_downloads(FINAL_SAVE_DIR)
        os.startfile(FINAL_SAVE_DIR)


def auto_all_weeks(sb):
    print("\n🌟 [全自動模式] 啟動...")
    sb.switch_to_default_content()
    # 完整關鍵字：包含簡繁中文、英文
    target_keywords = ["week", "lab", "assignment", "resource", "content", "chapter", "週", "周", "第", "实验", "作业",
                       "章"]
    menu_items = sb.find_elements("#courseMenuPalette_contents li a")
    links_to_visit = [item.text for item in menu_items if any(k in item.text.lower() for k in target_keywords)]

    if not links_to_visit:
        print("❌ 未識別到目錄。")
        return

    for name in links_to_visit:
        print(f"\n➡️ 前往: {name}")
        try:
            sb.switch_to_default_content()
            sb.click(f'#courseMenuPalette_contents li a:contains("{name}")')
            sb.sleep(3)
            scan_and_download(sb, is_auto=True)
        except:
            continue

    print("\n🎉 任務結束！")
    wait_for_downloads(FINAL_SAVE_DIR)
    os.startfile(FINAL_SAVE_DIR)


# --- 4. GUI 介面 (置頂 + Pillow) ---

def main():
    root = tk.Tk()
    root.title(f"BB 下載助手 v{VERSION}")
    root.geometry("400x650")
    root.configure(bg="#ffffff")
    root.attributes("-topmost", True)

    img_path = get_resource_path("dove.png")
    try:
        pil_img = Image.open(img_path)
        pil_img = pil_img.resize((180, 180), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        tk.Label(root, image=tk_img, bg="#ffffff").pack(pady=15)
        root.tk_img = tk_img
    except:
        tk.Label(root, text="🕊️", font=("Arial", 50), bg="#ffffff").pack(pady=20)

    tk.Label(root, text=f"開發者：{DEVELOPER}", font=("Microsoft JhengHei", 16, "bold"), bg="#ffffff").pack()
    tk.Label(root, text=f"版本：{VERSION} | 日期：{TODAY_DATE}", font=("Arial", 10), bg="#ffffff", fg="#2196F3").pack()

    # 顯示下載路徑讓使用者安心
    path_label = tk.Label(root, text=f"下載至：下載/BB_Downloads_by_Su", font=("Microsoft JhengHei", 8), bg="#ffffff",
                          fg="gray")
    path_label.pack(pady=5)

    with SB(uc=False, user_data_dir=USER_DATA_DIR) as sb:
        sb.driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow", "downloadPath": FINAL_SAVE_DIR
        })
        sb.open(TARGET_URL)

        btn_style = {"font": ("Microsoft JhengHei", 12, "bold"), "fg": "white", "width": 25, "height": 2}
        tk.Button(root, text="🚀 下載當前頁 (按 1)", bg="#4CAF50", **btn_style,
                  command=lambda: scan_and_download(sb)).pack(pady=10)
        tk.Button(root, text="🌪️ 全自動下載所有週次", bg="#2196F3", **btn_style,
                  command=lambda: auto_all_weeks(sb)).pack(pady=10)

        def quit_all():
            root.destroy()
            sys.exit()

        tk.Button(root, text="🛑 結束並關閉程式 (按 Q)", bg="#f44336", font=("Microsoft JhengHei", 10), fg="white",
                  width=20, command=quit_all).pack(pady=20)

        root.bind('1', lambda e: scan_and_download(sb))
        root.bind('q', lambda e: quit_all())
        root.protocol("WM_DELETE_WINDOW", quit_all)
        root.mainloop()


if __name__ == "__main__":
    main()