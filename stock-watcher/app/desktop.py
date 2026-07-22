from __future__ import annotations

import asyncio
import logging
import threading
import webbrowser
from datetime import datetime
from tkinter import END, BOTH, LEFT, RIGHT, X, Y, W, E, N, S, StringVar, messagebox
from tkinter import ttk
import tkinter as tk

from .config import load_settings, refresh_settings, save_settings
from .monitor import check_all, check_one
from .notifier import send_whatsapp
from .storage import (
    add_target,
    delete_target,
    get_target,
    list_targets,
    recent_events,
    update_target,
)

logger = logging.getLogger(__name__)


STATUS_ZH = {
    "pending": "未檢查",
    "buyable": "可購買",
    "unavailable": "不可買",
    "no_match": "無關鍵字",
    "error": "錯誤",
}


class StockWatcherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Stock Watcher｜貨品上架追蹤")
        self.geometry("980x720")
        self.minsize(860, 620)
        self.configure(bg="#102018")

        self._checking = False
        self._auto_job: str | None = None
        self.settings = load_settings()

        self._setup_style()
        self._build_ui()
        self.refresh_list()
        self.refresh_events()
        self._update_status_bar()
        self._schedule_auto_check()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        bg = "#102018"
        panel = "#163028"
        ink = "#e8f2ec"
        muted = "#9bb5a8"
        accent = "#3dd68c"

        style.configure(".", background=bg, foreground=ink, fieldbackground=panel)
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground=ink, font=("Microsoft JhengHei UI", 10))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=("Microsoft JhengHei UI", 9))
        style.configure("Panel.TLabel", background=panel, foreground=ink, font=("Microsoft JhengHei UI", 10))
        style.configure("Title.TLabel", background=bg, foreground=ink, font=("Microsoft JhengHei UI", 22, "bold"))
        style.configure("Sub.TLabel", background=bg, foreground=muted, font=("Microsoft JhengHei UI", 10))
        style.configure("TButton", font=("Microsoft JhengHei UI", 10), padding=6)
        style.configure("Accent.TButton", font=("Microsoft JhengHei UI", 10, "bold"), padding=8)
        style.configure("TEntry", fieldbackground="#0b1612", foreground=ink, insertcolor=ink)
        style.configure("TLabelframe", background=panel, foreground=ink)
        style.configure("TLabelframe.Label", background=panel, foreground=ink, font=("Microsoft JhengHei UI", 11, "bold"))
        style.configure(
            "Treeview",
            background="#0b1612",
            foreground=ink,
            fieldbackground="#0b1612",
            rowheight=28,
            font=("Microsoft JhengHei UI", 10),
        )
        style.configure("Treeview.Heading", background=panel, foreground=ink, font=("Microsoft JhengHei UI", 10, "bold"))
        style.map("Treeview", background=[("selected", accent)], foreground=[("selected", "#062015")])
        style.map("Accent.TButton", background=[("active", accent)])

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky=EW, pady=(0, 12))
        ttk.Label(header, text="Stock Watcher", style="Title.TLabel").pack(anchor=W)
        ttk.Label(
            header,
            text="同時監控多個網頁。偵測到自訂關鍵字同可購買時，會把購買連結傳到 WhatsApp。",
            style="Sub.TLabel",
        ).pack(anchor=W, pady=(4, 0))

        toolbar = ttk.Frame(root)
        toolbar.grid(row=1, column=0, sticky=EW, pady=(0, 10))
        ttk.Button(toolbar, text="立即全部檢查", style="Accent.TButton", command=self.check_all_now).pack(side=LEFT)
        ttk.Button(toolbar, text="WhatsApp 設定", command=self.open_settings).pack(side=LEFT, padx=(8, 0))
        ttk.Button(toolbar, text="測試 WhatsApp", command=self.test_whatsapp).pack(side=LEFT, padx=(8, 0))
        self.status_var = StringVar(value="")
        ttk.Label(toolbar, textvariable=self.status_var, style="Muted.TLabel").pack(side=RIGHT)

        body = ttk.Frame(root)
        body.grid(row=2, column=0, sticky=NSEW)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        form_box = ttk.Labelframe(body, text="加入監控網頁", padding=12)
        form_box.grid(row=0, column=0, sticky=NSEW, padx=(0, 10))

        self.name_var = StringVar()
        self.url_var = StringVar()
        self.keywords_var = StringVar()
        self.buyable_var = StringVar()
        self.sold_out_var = StringVar()

        self._form_row(form_box, 0, "名稱（可選）", self.name_var)
        self._form_row(form_box, 1, "監控網址 *", self.url_var)
        self._form_row(form_box, 2, "自訂關鍵字（逗號分隔）", self.keywords_var)
        self._form_row(form_box, 3, "可購買字詞（可留空）", self.buyable_var)
        self._form_row(form_box, 4, "售罄字詞（可留空）", self.sold_out_var)
        ttk.Button(form_box, text="開始監控", style="Accent.TButton", command=self.add_watch).grid(
            row=5, column=0, columnspan=2, sticky=EW, pady=(12, 0)
        )
        ttk.Label(
            form_box,
            text="提示：關鍵字例如「限量, 特別色」。可購買預設含「加入購物車 / Buy Now」等。",
            style="Panel.TLabel",
            wraplength=280,
        ).grid(row=6, column=0, columnspan=2, sticky=W, pady=(10, 0))

        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky=NSEW)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        right.columnconfigure(0, weight=1)

        list_box = ttk.Labelframe(right, text="監控清單", padding=8)
        list_box.grid(row=0, column=0, sticky=NSEW, pady=(0, 10))
        list_box.rowconfigure(0, weight=1)
        list_box.columnconfigure(0, weight=1)

        columns = ("name", "status", "keywords", "message")
        self.tree = ttk.Treeview(list_box, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="名稱")
        self.tree.heading("status", text="狀態")
        self.tree.heading("keywords", text="關鍵字")
        self.tree.heading("message", text="最近結果")
        self.tree.column("name", width=140, stretch=False)
        self.tree.column("status", width=80, stretch=False)
        self.tree.column("keywords", width=140, stretch=False)
        self.tree.column("message", width=280, stretch=True)
        scroll = ttk.Scrollbar(list_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky=NSEW)
        scroll.grid(row=0, column=1, sticky=NS)

        actions = ttk.Frame(list_box)
        actions.grid(row=1, column=0, columnspan=2, sticky=EW, pady=(8, 0))
        ttk.Button(actions, text="檢查選取", command=self.check_selected).pack(side=LEFT)
        ttk.Button(actions, text="開啟網頁", command=self.open_selected).pack(side=LEFT, padx=(6, 0))
        ttk.Button(actions, text="暫停/恢復", command=self.toggle_selected).pack(side=LEFT, padx=(6, 0))
        ttk.Button(actions, text="刪除", command=self.delete_selected).pack(side=LEFT, padx=(6, 0))

        event_box = ttk.Labelframe(right, text="最近動態（只會通知可購買）", padding=8)
        event_box.grid(row=1, column=0, sticky=NSEW)
        event_box.rowconfigure(0, weight=1)
        event_box.columnconfigure(0, weight=1)
        self.events = tk.Text(
            event_box,
            height=10,
            wrap="word",
            bg="#0b1612",
            fg="#e8f2ec",
            insertbackground="#e8f2ec",
            relief="flat",
            font=("Microsoft JhengHei UI", 9),
        )
        self.events.grid(row=0, column=0, sticky=NSEW)
        self.events.configure(state="disabled")

    def _form_row(self, parent: ttk.Labelframe, row: int, label: str, variable: StringVar) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky=W, pady=4)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky=EW, pady=4, padx=(8, 0))
        parent.columnconfigure(1, weight=1)

    def _selected_id(self) -> str | None:
        sel = self.tree.selection()
        if not sel:
            return None
        return sel[0]

    def refresh_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for target in list_targets():
            name = target.name + ("" if target.enabled else "（已暫停）")
            status = STATUS_ZH.get(target.last_status, target.last_status)
            keywords = ", ".join(target.keywords) if target.keywords else "—"
            message = target.last_message or "尚未檢查"
            self.tree.insert(
                "",
                END,
                iid=target.id,
                values=(name, status, keywords, message),
            )

    def refresh_events(self) -> None:
        lines: list[str] = []
        for event in recent_events(40):
            when = event.get("at", "")
            try:
                when = datetime.fromisoformat(when).strftime("%m-%d %H:%M:%S")
            except Exception:
                pass
            notified = "｜已通知" if event.get("notified") else ""
            status = STATUS_ZH.get(event.get("status", ""), event.get("status", ""))
            lines.append(
                f"[{when}] {event.get('name')} · {status}{notified}\n"
                f"  {event.get('message', '')}\n"
            )
        text = "\n".join(lines) if lines else "暫時未有紀錄。加入網頁後按「立即全部檢查」。"
        self.events.configure(state="normal")
        self.events.delete("1.0", END)
        self.events.insert("1.0", text)
        self.events.configure(state="disabled")

    def _update_status_bar(self) -> None:
        self.settings = load_settings()
        ready = bool(self.settings.whatsapp_phone and self.settings.whatsapp_api_key) or bool(
            self.settings.twilio_account_sid and self.settings.twilio_auth_token
        )
        phone = self.settings.whatsapp_phone or "未設定"
        if len(phone) > 6:
            phone = phone[:3] + "****" + phone[-2:]
        state = "WhatsApp 已設定" if ready else "WhatsApp 未設定"
        self.status_var.set(f"{state} · {phone} · 每 {self.settings.check_interval_seconds} 秒檢查")

    def add_watch(self) -> None:
        url = self.url_var.get().strip()
        if not url.startswith(("http://", "https://")):
            messagebox.showerror("網址錯誤", "網址必須以 http:// 或 https:// 開頭")
            return
        add_target(
            {
                "name": self.name_var.get().strip(),
                "url": url,
                "keywords": self.keywords_var.get(),
                "buyable_keywords": self.buyable_var.get(),
                "sold_out_keywords": self.sold_out_var.get(),
                "enabled": True,
            }
        )
        self.name_var.set("")
        self.url_var.set("")
        self.keywords_var.set("")
        self.buyable_var.set("")
        self.sold_out_var.set("")
        self.refresh_list()

    def delete_selected(self) -> None:
        target_id = self._selected_id()
        if not target_id:
            messagebox.showinfo("提示", "請先選取一個監控項目")
            return
        if not messagebox.askyesno("確認刪除", "確定刪除呢個監控項目？"):
            return
        delete_target(target_id)
        self.refresh_list()
        self.refresh_events()

    def toggle_selected(self) -> None:
        target_id = self._selected_id()
        if not target_id:
            messagebox.showinfo("提示", "請先選取一個監控項目")
            return
        target = get_target(target_id)
        if not target:
            return
        update_target(target_id, {"enabled": not target.enabled})
        self.refresh_list()

    def open_selected(self) -> None:
        target_id = self._selected_id()
        if not target_id:
            messagebox.showinfo("提示", "請先選取一個監控項目")
            return
        target = get_target(target_id)
        if target:
            webbrowser.open(target.url)

    def check_selected(self) -> None:
        target_id = self._selected_id()
        if not target_id:
            messagebox.showinfo("提示", "請先選取一個監控項目")
            return
        target = get_target(target_id)
        if not target:
            return
        self._run_async(check_one(target), done_message="已完成單項檢查")

    def check_all_now(self) -> None:
        self._run_async(check_all(only_enabled=True), done_message="已完成全部檢查")

    def test_whatsapp(self) -> None:
        async def _send():
            return await send_whatsapp(
                "✅ Stock Watcher 測試訊息\n如果你收到呢條，WhatsApp 通知已設定成功。"
            )

        def on_done(result):
            ok, detail = result
            if ok:
                messagebox.showinfo("WhatsApp", detail)
            else:
                messagebox.showerror("WhatsApp", detail)

        self._run_async(_send(), on_done=on_done)

    def open_settings(self) -> None:
        SettingsDialog(self, on_saved=self._on_settings_saved)

    def _on_settings_saved(self) -> None:
        refresh_settings()
        self.settings = load_settings()
        self._update_status_bar()
        self._schedule_auto_check()

    def _schedule_auto_check(self) -> None:
        if self._auto_job is not None:
            try:
                self.after_cancel(self._auto_job)
            except Exception:
                pass
        interval_ms = max(15, self.settings.check_interval_seconds) * 1000

        def tick() -> None:
            if not self._checking:
                self._run_async(check_all(only_enabled=True), silent=True)
            self._auto_job = self.after(interval_ms, tick)

        self._auto_job = self.after(interval_ms, tick)

    def _run_async(self, coro, *, done_message: str | None = None, on_done=None, silent: bool = False) -> None:
        if self._checking:
            if not silent:
                messagebox.showinfo("忙碌中", "而家已經有檢查進行緊，請稍等。")
            return
        self._checking = True
        if not silent:
            self.status_var.set("檢查中…")

        def worker() -> None:
            try:
                result = asyncio.run(coro)
            except Exception as exc:
                logger.exception("Background task failed")
                self.after(0, lambda: self._async_failed(str(exc), silent=silent))
                return
            self.after(0, lambda: self._async_done(result, done_message, on_done, silent))

        threading.Thread(target=worker, daemon=True).start()

    def _async_done(self, result, done_message, on_done, silent: bool) -> None:
        self._checking = False
        self.refresh_list()
        self.refresh_events()
        self._update_status_bar()
        if on_done:
            on_done(result)
        elif done_message and not silent:
            messagebox.showinfo("完成", done_message)

    def _async_failed(self, error: str, *, silent: bool) -> None:
        self._checking = False
        self._update_status_bar()
        if not silent:
            messagebox.showerror("錯誤", error)

    def _on_close(self) -> None:
        if self._auto_job is not None:
            try:
                self.after_cancel(self._auto_job)
            except Exception:
                pass
        self.destroy()


class SettingsDialog(tk.Toplevel):
    def __init__(self, master: StockWatcherApp, on_saved) -> None:
        super().__init__(master)
        self.title("WhatsApp 設定")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.on_saved = on_saved
        self.settings = load_settings()

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="CallMeBot WhatsApp（個人免費）", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky=W
        )
        ttk.Label(
            frame,
            text="1) 將 +34 644 21 99 47 存入通訊錄\n"
            "2) 傳送：I allow callmebot to send me messages\n"
            "3) 把收到的 API key 填下面",
            style="Muted.TLabel",
            justify=LEFT,
        ).grid(row=1, column=0, columnspan=2, sticky=W, pady=(6, 12))

        self.phone = StringVar(value=self.settings.whatsapp_phone)
        self.api_key = StringVar(value=self.settings.whatsapp_api_key)
        self.interval = StringVar(value=str(self.settings.check_interval_seconds))

        ttk.Label(frame, text="電話（國際格式，例如 85291234567）").grid(row=2, column=0, sticky=W)
        ttk.Entry(frame, textvariable=self.phone, width=36).grid(row=2, column=1, sticky=EW, pady=4)
        ttk.Label(frame, text="CallMeBot API Key").grid(row=3, column=0, sticky=W)
        ttk.Entry(frame, textvariable=self.api_key, width=36, show="*").grid(row=3, column=1, sticky=EW, pady=4)
        ttk.Label(frame, text="檢查間隔（秒，最少 15）").grid(row=4, column=0, sticky=W)
        ttk.Entry(frame, textvariable=self.interval, width=36).grid(row=4, column=1, sticky=EW, pady=4)

        btns = ttk.Frame(frame)
        btns.grid(row=5, column=0, columnspan=2, sticky=E, pady=(14, 0))
        ttk.Button(btns, text="取消", command=self.destroy).pack(side=RIGHT)
        ttk.Button(btns, text="儲存", style="Accent.TButton", command=self.save).pack(side=RIGHT, padx=(0, 8))

        self.bind("<Return>", lambda _e: self.save())
        self.phone_entry_focus()

    def phone_entry_focus(self) -> None:
        self.after(50, lambda: self.focus_force())

    def save(self) -> None:
        try:
            interval = int(self.interval.get().strip())
            if interval < 15:
                raise ValueError
        except ValueError:
            messagebox.showerror("設定錯誤", "檢查間隔必須係 15 或以上嘅整數")
            return

        updated = self.settings.model_copy(
            update={
                "whatsapp_phone": self.phone.get().strip().lstrip("+").replace(" ", ""),
                "whatsapp_api_key": self.api_key.get().strip(),
                "check_interval_seconds": interval,
            }
        )
        save_settings(updated)
        refresh_settings()
        self.on_saved()
        messagebox.showinfo("已儲存", "設定已儲存。")
        self.destroy()


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = StockWatcherApp()
    app.mainloop()
