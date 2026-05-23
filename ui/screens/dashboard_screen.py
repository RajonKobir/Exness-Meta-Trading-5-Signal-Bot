import customtkinter as ctk

from ui.components.credentials_form import CredentialsForm
from ui.components.button_panel import ButtonPanel
from ui.components.report_panel import ReportPanel

from core.mt5_connector import MT5Connector
from services.telegram_service import TelegramService
from services.bot_service import BotService
from services.settings_manager import save_settings, load_settings
from ui.components.telegram_inspector import TelegramInspector


class DashboardScreen(ctk.CTkFrame):

    def __init__(
        self,
        master,
        history_callback,
        database
    ):

        super().__init__(master)

        # ==========================================
        # VARIABLES
        # ==========================================

        self.database = database
        self.current_timezone = "Asia/Dhaka"

        self.bot_running = False

        self.mt5 = MT5Connector()

        # ==========================================
        # MAIN LAYOUT
        # ==========================================

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_scroll = ctk.CTkScrollableFrame(
            self
        )

        self.main_scroll.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.main_scroll.grid_columnconfigure(
            0,
            weight=1
        )

        self.main_scroll.grid_columnconfigure(
            1,
            weight=1
        )

        # ==========================================
        # LEFT SIDE
        # ==========================================

        self.left = ctk.CTkFrame(
            self.main_scroll
        )

        self.left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10, 5),
            pady=10
        )

        self.left.grid_columnconfigure(
            0,
            weight=3
        )

        self.left.grid_columnconfigure(
            1,
            weight=1
        )

        # ==========================================
        # CREDENTIALS
        # ==========================================

        self.credentials_container = ctk.CTkFrame(
            self.left
        )

        self.credentials_container.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
            pady=20
        )

        self.credentials = CredentialsForm(
            self.credentials_container,
            auto_save_callback=self.save_settings
        )

        self.credentials.pack(
            fill="x",
            expand=True,
            padx=20,
            pady=20
        )

        # ==========================================
        # ACTIONS
        # ==========================================

        self.actions_frame = ctk.CTkFrame(
            self.left,
            width=260,
            height=500
        )

        self.actions_frame.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(10, 0),
            pady=20
        )

        self.actions_frame.grid_propagate(False)
        self.actions_frame.pack_propagate(False)

        self.actions_container = ctk.CTkFrame(
            self.actions_frame,
            fg_color="transparent"
        )

        self.actions_container.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.buttons = ButtonPanel(
            self.actions_container,
            history_callback
        )

        self.buttons.pack(
            fill="x",
            expand=True
        )

        self.buttons.start_btn.configure(
            command=self.start_bot
        )

        self.buttons.stop_btn.configure(
            command=self.stop_bot
        )

        self.buttons.set_stopped_state()

        # wire extra button actions
        self.buttons.save_btn.configure(command=self.save_settings)
        self.buttons.retry_btn.configure(command=self.open_telegram_inspector)

        # ==========================================
        # RIGHT SIDE
        # ==========================================

        self.right = ctk.CTkFrame(
            self.main_scroll
        )

        self.right.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 10),
            pady=10
        )

        self.reports = ReportPanel(
            self.right,
            timezone=self.current_timezone
        )

        self.reports.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # load persisted settings if present
        self.load_settings()

        # ==========================================
        # RESPONSIVE
        # ==========================================

        self.bind(
            "<Configure>",
            self.on_resize
        )

    # ==========================================
    # START BOT
    # ==========================================

    def start_bot(self):

        # prevent multiple clicks
        if self.bot_running:

            self.safe_log(
                "Bot is already running."
            )

            return

        # do not alter button layout before validation to avoid UI shift

        # ======================================
        # VALIDATION
        # ======================================

        bot_token = self.credentials.bot_token.get().strip()
        chat_id = self.credentials.chat_id.get().strip()
        symbol = self.credentials.symbol.get().strip()

        # Telegram credentials are optional — allow bot to run without them
        if not bot_token or not chat_id:

            self.safe_status("Telegram disabled: messages will not be sent (credentials missing).")

            self.safe_log(
                "Telegram credentials missing; running in local/report-only mode."
            )

        if not symbol:

            self.safe_status("Missing credentials: Trading symbol is required.")

            self.safe_log(
                "Trading symbol is required."
            )

            self.buttons.set_stopped_state()

            self.buttons.unlock_buttons()

            return

        try:

            candle_count = int(
                self.credentials.candle_count.get()
            )

            interval = int(
                self.credentials.interval_minutes.get()
            )

            buy_threshold = int(
                self.credentials.buy_threshold.get()
            )

            sell_threshold = int(
                self.credentials.sell_threshold.get()
            )

        except:

            self.safe_status("Invalid numeric input in settings.")

            self.safe_log(
                "Numeric fields contain invalid values."
            )

            self.buttons.set_stopped_state()

            self.buttons.unlock_buttons()

            return

        # ======================================
        # START BOT SERVICE
        # Delegate the loop, MT5 handling and timer to BotService
        # ======================================

        self.safe_log("Starting bot service...")

        telegram = None

        if bot_token and chat_id:

            telegram = TelegramService(
                bot_token,
                chat_id
            )

        # timezone selection (optional)
        try:
            tz = self.credentials.timezone.get().strip() or "Asia/Dhaka"
        except Exception:
            tz = "Asia/Dhaka"

        self.current_timezone = tz
        self.reports.set_timezone(tz)

        # create bot service and start the loop
        self.bot_service = BotService(
            report_panel=self.reports,
            database=self.database,
            telegram_service=telegram,
            timezone=tz
        )

        try:

            self.bot_service.start(
                symbol=symbol,
                candle_count=candle_count,
                interval_minutes=interval,
                buy_threshold=buy_threshold,
                sell_threshold=sell_threshold
            )

        except Exception as e:

            self.safe_status("Failed to start bot service.")

            self.safe_log(f"Bot service start error: {str(e)}")

            self.buttons.set_stopped_state()

            self.buttons.unlock_buttons()

            return

        # mark running and update buttons
        self.bot_running = True

        self.buttons.set_running_state()

        # connect failure callback so Dashboard can enable retry
        try:
            self.bot_service.set_failure_callback(self.handle_telegram_failure)
        except Exception:
            pass

        # reset retry button initially
        self.buttons.disable_retry()


    # ==========================================
    # STOP BOT
    # ==========================================

    def stop_bot(self):

        if not self.bot_running:
            return

        self.bot_running = False

        # stop bot service if running
        try:
            if hasattr(self, "bot_service") and self.bot_service:
                self.bot_service.stop()
        except Exception as e:
            self.safe_log(f"Error stopping bot service: {str(e)}")

        self.safe_status("Bot stopped.")
        self.buttons.set_stopped_state()
        self.buttons.unlock_buttons()
        self.buttons.disable_retry()
        self.buttons.set_connection_status(False)

    # ==========================================
    # SAFE UI
    # ==========================================

    def safe_log(self, text):

        self.after(
            0,
            lambda:
            self.reports.log(text)
        )

    def safe_status(self, text):

        self.after(
            0,
            lambda:
            self.reports.set_status(text)
        )

    def safe_log_below(self, text):

        self.after(
            0,
            lambda:
            self.reports.log_below_last_report(text)
        )

    # ==========================================
    # RESPONSIVE
    # ==========================================

    def on_resize(self, event):

        width = self.winfo_width()

        # ======================================
        # MOBILE
        # ======================================

        if width < 1100:

            self.left.grid(
                row=0,
                column=0,
                columnspan=2,
                sticky="nsew"
            )

            self.right.grid(
                row=1,
                column=0,
                columnspan=2,
                sticky="nsew"
            )

        # ======================================
        # DESKTOP
        # ======================================

        else:

            self.left.grid(
                row=0,
                column=0,
                sticky="nsew"
            )

            self.right.grid(
                row=0,
                column=1,
                sticky="nsew"
            )

    # ==========================================
    # SETTINGS PERSISTENCE
    # ==========================================

    def save_settings(self, show_feedback=True):

        timezone_value = self.credentials.timezone.get().strip() or "Asia/Dhaka"
        self.current_timezone = timezone_value
        try:
            self.reports.set_timezone(timezone_value)
        except Exception:
            pass
        settings = {
            "bot_token": self.credentials.bot_token.get().strip(),
            "chat_id": self.credentials.chat_id.get().strip(),
            "symbol": self.credentials.symbol.get().strip(),
            "candle_count": self.credentials.candle_count.get().strip(),
            "buy_threshold": self.credentials.buy_threshold.get().strip(),
            "sell_threshold": self.credentials.sell_threshold.get().strip(),
            "interval": self.credentials.interval_minutes.get().strip(),
            "timezone": timezone_value
        }

        result = save_settings(settings)

        if show_feedback:
            if result is True:
                self.safe_status("Settings saved.")
                self.safe_log("Settings persisted to disk.")
            else:
                message = result[1] if isinstance(result, tuple) else str(result)
                self.safe_status("Failed to save settings.")
                self.safe_log(f"Settings save error: {message}")

    def load_settings(self):

        data = load_settings()

        if not data:
            return

        try:
            if data.get("bot_token") is not None:
                self.credentials.bot_token.delete(0, "end")
                self.credentials.bot_token.insert(0, data.get("bot_token", ""))

            if data.get("chat_id") is not None:
                self.credentials.chat_id.delete(0, "end")
                self.credentials.chat_id.insert(0, data.get("chat_id", ""))

            if data.get("symbol") is not None:
                self.credentials.symbol.delete(0, "end")
                self.credentials.symbol.insert(0, data.get("symbol", ""))

            if data.get("candle_count") is not None:
                self.credentials.candle_count.delete(0, "end")
                self.credentials.candle_count.insert(0, data.get("candle_count", ""))

            if data.get("buy_threshold") is not None:
                self.credentials.buy_threshold.delete(0, "end")
                self.credentials.buy_threshold.insert(0, data.get("buy_threshold", ""))

            if data.get("sell_threshold") is not None:
                self.credentials.sell_threshold.delete(0, "end")
                self.credentials.sell_threshold.insert(0, data.get("sell_threshold", ""))

            if data.get("interval") is not None:
                self.credentials.interval_minutes.delete(0, "end")
                self.credentials.interval_minutes.insert(0, data.get("interval", ""))

            if data.get("timezone") is not None:
                tz = data.get("timezone", "Asia/Dhaka") or "Asia/Dhaka"
                self.credentials.timezone.delete(0, "end")
                self.credentials.timezone.insert(0, tz)
                self.current_timezone = tz
                self.reports.set_timezone(tz)

            self.safe_status("Settings loaded.")
            self.safe_log("Loaded saved settings.")

        except Exception as e:
            self.safe_log(f"Failed to load settings: {str(e)}")

    def open_telegram_inspector(self):

        if not hasattr(self, "bot_service") or not self.bot_service:
            self.safe_log("No bot service available for Telegram inspection.")
            return

        try:
            TelegramInspector(self, self.bot_service)
        except Exception as e:
            self.safe_log(f"Failed to open Telegram inspector: {str(e)}")
