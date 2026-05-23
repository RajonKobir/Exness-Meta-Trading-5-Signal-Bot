import customtkinter as ctk
from datetime import datetime

from datetime import datetime, timedelta, timezone

# prefer stdlib zoneinfo when available (Python 3.9+)
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

try:
    import pytz
except Exception:
    pytz = None


def _resolve_timezone(timezone_name):
    if not timezone_name:
        return timezone(timedelta(hours=6))

    tz_name = str(timezone_name).strip()
    if tz_name.lower() in ("asia/dhaka", "dhaka", "bdt", "bgt"):
        return timezone(timedelta(hours=6))

    if ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            pass

    if pytz is not None:
        try:
            return pytz.timezone(tz_name)
        except Exception:
            pass

    return timezone(timedelta(hours=6))


class ReportPanel(ctk.CTkFrame):

    def __init__(self, master, timezone="Asia/Dhaka"):
        super().__init__(master)
        self.timezone_name = timezone or "Asia/Dhaka"
        self._timezone = _resolve_timezone(self.timezone_name)

        # ==========================================
        # GRID CONFIG
        # ==========================================

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ==========================================
        # TITLE
        # ==========================================

        title = ctk.CTkLabel(
            self,
            text="LIVE REPORTS",
            font=("Arial", 32, "bold")
        )

        title.grid(
            row=0,
            column=0,
            pady=(20, 10)
        )

        # ==========================================
        # STATUS SECTION
        # ==========================================

        self.status_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            height=84
        )

        self.status_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 15)
        )

        # Prevent the status_frame from changing size when its child labels update
        # This avoids the UI 'shaking' when the timer text appears or changes.
        self.status_frame.grid_propagate(False)

        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_rowconfigure(0, minsize=30)
        self.status_frame.grid_rowconfigure(1, minsize=28)

        # ------------------------------------------
        # STATUS LABEL
        # ------------------------------------------

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status: Idle",
            anchor="w",
            justify="left",
            font=("Arial", 15, "bold"),
            wraplength=400
        )

        self.status_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=15,
            pady=(12, 5)
        )

        # ------------------------------------------
        # TIMER LABEL
        # ------------------------------------------

        self.timer_label = ctk.CTkLabel(
            self.status_frame,
            text="Next query in: --",
            anchor="w",
            justify="left",
            font=("Arial", 14),
            wraplength=400
        )

        self.timer_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 12)
        )

        # ==========================================
        # REPORT LOG BOX
        # ==========================================

        self.textbox = ctk.CTkTextbox(
            self,
            font=("Consolas", 14),
            corner_radius=12,
            wrap="word"
        )

        self.textbox.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 20)
        )

        # make readonly initially
        self.textbox.configure(state="disabled")

        # internal tracker for where the most recent report was inserted
        self._last_report_length = 0

        self.log("Application started")

    def set_timezone(self, timezone_name):
        self.timezone_name = timezone_name or "Asia/Dhaka"
        self._timezone = _resolve_timezone(self.timezone_name)

    def _format_timestamp(self):
        if self._timezone is not None:
            return datetime.now(self._timezone).strftime("%H:%M:%S")
        return datetime.now().strftime("%H:%M:%S")

    # ==========================================
    # STATUS UPDATE
    # ==========================================

    def set_status(self, message):

        def update():
            self.status_label.configure(
                text=f"Status: {message}"
            )

        self.after(0, update)

    # ==========================================
    # TIMER UPDATE
    # ==========================================

    def set_timer(self, value):

        def update():
            # supports:
            # 59
            # "59"
            # "00:59"

            if isinstance(value, int):

                mins = value // 60
                secs = value % 60

                formatted = f"{mins:02}:{secs:02}"

            else:

                formatted = str(value)

            self.timer_label.configure(
                text=f"Next query in: {formatted}"
            )

        self.after(0, update)

    # ==========================================
    # CLEAR TIMER
    # ==========================================

    def clear_timer(self):

        def update():
            self.timer_label.configure(
                text="Next query in: --"
            )

        self.after(0, update)

    # ==========================================
    # LOGGING
    # ==========================================

    def log(self, message):

        def update():
            timestamp = self._format_timestamp()

            log_message = (
                f"\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"[{timestamp}] {message}\n"
            )

            self.textbox.configure(state="normal")

            # insert on TOP
            self.textbox.insert(
                "1.0",
                log_message
            )

            self.textbox.configure(state="disabled")

        self.after(0, update)

    # ==========================================
    # ADD CANDLE REPORT
    # ==========================================

    def add_candle_report(
        self,
        total,
        green,
        red,
        signal=None
    ):

        def update():
            timestamp = self._format_timestamp()

            signal_text = signal if signal else "NO SIGNAL"

            report = (
                f"\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"[{timestamp}] MARKET REPORT\n\n"
                f"Total Candles : {total}\n"
                f"BUY Candles   : {green}\n"
                f"SELL Candles  : {red}\n"
                f"Result        : {signal_text}\n"
            )

            self.textbox.configure(state="normal")

            # newest report always on top
            self.textbox.insert(
                "1.0",
                report
            )

            # remember how many characters the last report contains so
            # callers can insert related messages directly below it
            try:
                self._last_report_length = len(report)
            except Exception:
                self._last_report_length = 0

            self.textbox.configure(state="disabled")

        self.after(0, update)

    def log_below_last_report(self, message):

        def update():
            # Inserts a message immediately after the most recent report
            if self._last_report_length > 0:

                index = f"1.0+{self._last_report_length}c"

            else:

                index = "1.0"

            timestamp = self._format_timestamp()

            log_message = (
                f"[{timestamp}] {message}\n"
            )

            self.textbox.configure(state="normal")

            self.textbox.insert(index, log_message)

            self.textbox.configure(state="disabled")

        self.after(0, update)

    # ==========================================
    # SUCCESS MESSAGE
    # ==========================================

    def log_success(self, message):

        self.log(f"SUCCESS: {message}")

    # ==========================================
    # ERROR MESSAGE
    # ==========================================

    def log_error(self, message):

        self.log(f"ERROR: {message}")

    # ==========================================
    # WARNING MESSAGE
    # ==========================================

    def log_warning(self, message):

        self.log(f"WARNING: {message}")