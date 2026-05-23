import customtkinter as ctk
import json


class TelegramInspector(ctk.CTkToplevel):

    def __init__(self, master, bot_service):

        super().__init__(master)

        self.title("Telegram Inspector")
        self.geometry("700x400")

        self.bot_service = bot_service

        txt = ctk.CTkTextbox(self, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)

        last = getattr(self.bot_service, "last_failed_telegram", None)

        if not last:
            txt.insert("0.0", "No failed telegram message recorded.")
        else:
            msg = last.get("message", "")
            details = last.get("details", {})

            content = "Last failed Telegram message:\n\n"
            content += msg + "\n\nDetails:\n"
            try:
                content += json.dumps(details, indent=2)
            except Exception:
                content += str(details)

            txt.insert("0.0", content)

        txt.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0,10))

        retry_btn = ctk.CTkButton(btn_frame, text="Retry Now", command=self._retry)
        retry_btn.pack(side="left", padx=8)

        close_btn = ctk.CTkButton(btn_frame, text="Close", command=self.destroy)
        close_btn.pack(side="right", padx=8)

    def _retry(self):

        if not self.bot_service:
            return

        success, details = self.bot_service.retry_last_telegram()

        if success:
            self.destroy()
        else:
            # show result in a small dialog
            dlg = ctk.CTkToplevel(self)
            dlg.title("Retry Result")
            txt = ctk.CTkTextbox(dlg)
            txt.pack(fill="both", expand=True, padx=10, pady=10)
            try:
                txt.insert("0.0", json.dumps(details, indent=2))
            except Exception:
                txt.insert("0.0", str(details))
            txt.configure(state="disabled")
