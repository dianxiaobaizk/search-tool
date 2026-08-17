# =========================================================
# 自动搜索工具 - 图形界面版 (CustomTkinter)
# 支持深色/亮色一键切换，并记住上次的选择
# =========================================================

import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
import threading
import webbrowser
import re
import json
import os

# ---------- 配置文件（保存主题偏好） ----------
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, "search_config.json")

def load_theme_preference():
    """加载上次保存的主题偏好"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("theme", "dark")
    except:
        return "dark"

def save_theme_preference(theme):
    """保存主题偏好"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"theme": theme}, f)
    except:
        pass

# ---------- 加载主题 ----------
initial_theme = load_theme_preference()
ctk.set_appearance_mode(initial_theme)
ctk.set_default_color_theme("blue")

# ---------- 主应用 ----------
class SearchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🔍 自动搜索工具")
        self.geometry("700x600")
        self.minsize(600, 400)

        # 当前主题
        self.current_theme = initial_theme

        # ---------- 标题栏（含主题切换按钮） ----------
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=30, pady=(20, 5))

        title_label = ctk.CTkLabel(top_frame, text="🔍 自动搜索工具", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(side="left")

        # 主题切换按钮
        self.theme_btn = ctk.CTkButton(
            top_frame,
            text="☀️ 亮色" if self.current_theme == "dark" else "🌙 深色",
            width=80,
            height=32,
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="right")

        # ---------- 输入框 + 搜索按钮 ----------
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=30, pady=10)

        self.entry = ctk.CTkEntry(input_frame, placeholder_text="输入搜索关键词...", height=40, font=ctk.CTkFont(size=16))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.start_search())

        self.search_btn = ctk.CTkButton(input_frame, text="🔍 搜索", command=self.start_search, height=40, width=100)
        self.search_btn.pack(side="right")

        # ---------- 结果显示区域 ----------
        self.textbox = ctk.CTkTextbox(self, wrap="word", font=ctk.CTkFont(size=14))
        self.textbox.pack(fill="both", expand=True, padx=20, pady=20)
        self.textbox.insert("1.0", "💡 输入关键词，点击搜索，结果将显示在这里...\n")
        self.textbox.insert("end", "双击任意链接可自动在浏览器中打开。\n")

        # 底部提示
        hint = ctk.CTkLabel(self, text="💡 双击任意链接可自动在浏览器中打开", text_color="gray")
        hint.pack(pady=5)

        # 绑定双击事件
        self.textbox.bind("<Double-Button-1>", self.open_selected_url)

    # ---------- 主题切换 ----------
    def toggle_theme(self):
        """切换深色/亮色主题"""
        if self.current_theme == "dark":
            ctk.set_appearance_mode("light")
            self.current_theme = "light"
            self.theme_btn.configure(text="🌙 深色")
        else:
            ctk.set_appearance_mode("dark")
            self.current_theme = "dark"
            self.theme_btn.configure(text="☀️ 亮色")
        # 保存偏好
        save_theme_preference(self.current_theme)

    # ---------- 开始搜索 ----------
    def start_search(self):
        keyword = self.entry.get().strip()
        if not keyword:
            self.textbox.insert("end", "⚠️ 请输入关键词\n")
            self.textbox.see("end")
            return

        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", f"⏳ 正在搜索 \"{keyword}\" ...\n")
        self.textbox.see("end")

        self.search_btn.configure(state="disabled", text="搜索中...")

        thread = threading.Thread(target=self.do_search, args=(keyword,), daemon=True)
        thread.start()

    # ---------- 执行搜索 ----------
    def do_search(self, keyword):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        search_url = f"https://www.bing.com/search?q={keyword}"

        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            self.textbox.insert("end", f"❌ 请求失败: {e}\n")
            self.after(0, self.finish_search)
            return

        soup = BeautifulSoup(resp.text, "lxml")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if href.startswith("http") and len(text) > 3 and "microsoft" not in href.lower():
                if "https://www.bing.com/ck/a?!" in href:
                    continue
                if href not in [x["url"] for x in links]:
                    links.append({"title": text[:100], "url": href})

        self.textbox.delete("1.0", "end")
        if not links:
            self.textbox.insert("1.0", "😅 没有找到结果，换关键词试试吧。\n")
        else:
            result_text = f"✅ 找到 {len(links)} 条结果:\n\n"
            for i, item in enumerate(links[:20], start=1):
                result_text += f"{i}. {item['title']}\n   📎 {item['url']}\n\n"
            self.textbox.insert("1.0", result_text)

        self.after(0, self.finish_search)

    def finish_search(self):
        self.search_btn.configure(state="normal", text="🔍 搜索")

    # ---------- 双击打开链接 ----------
    def open_selected_url(self, event):
        try:
            selected = self.textbox.get("sel.first", "sel.last")
            if "http" in selected:
                urls = re.findall(r'https?://[^\s]+', selected)
                if urls:
                    webbrowser.open(urls[0])
                    return
            index = self.textbox.index("@0,0")
            line = self.textbox.get(f"{index} linestart", f"{index} lineend")
            urls = re.findall(r'https?://[^\s]+', line)
            if urls:
                webbrowser.open(urls[0])
        except Exception:
            pass

# ---------- 入口 ----------
if __name__ == "__main__":
    app = SearchApp()
    app.mainloop()