import customtkinter as ctk


class CredentialsForm(ctk.CTkFrame):

    def __init__(self, master, auto_save_callback=None):

        super().__init__(master)

        # IMPORTANT:
        # This makes the frame resize properly
        self.grid_columnconfigure(0, weight=1)

        # Store auto-save callback for field changes
        self.auto_save_callback = auto_save_callback

        title = ctk.CTkLabel(
            self,
            text="Credentials",
            font=("Arial", 28, "bold")
        )

        title.grid(
            row=0,
            column=0,
            pady=(20, 30),
            sticky="w"
        )

        self.telegram_token = self.create_input(
            row=1,
            label="Telegram Bot Token"
        )

        self.telegram_chat_id = self.create_input(
            row=2,
            label="Telegram Chat ID"
        )

        self.symbol = self.create_input(
            row=3,
            label="Symbol",
            default="XAUUSDm"
        )

        self.candles = self.create_input(
            row=4,
            label="Number of Candles",
            default="41"
        )

        self.buy_threshold = self.create_input(
            row=5,
            label="Buy Threshold",
            default="16"
        )

        self.sell_threshold = self.create_input(
            row=6,
            label="Sell Threshold",
            default="16"
        )

        self.interval = self.create_input(
            row=7,
            label="Interval Minutes",
            default="1"
        )

        self.timezone = self.create_input(
            row=8,
            label="Timezone (e.g. Asia/Dhaka)",
            default="Asia/Dhaka"
        )

        # Backwards-compatible aliases expected by other modules
        self.bot_token = self.telegram_token
        self.chat_id = self.telegram_chat_id
        self.candle_count = self.candles
        self.interval_minutes = self.interval

        # IMPORTANT:
        # Extra bottom spacing for smaller screens
        spacer = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=120
        )

        spacer.grid(
            row=999,
            column=0,
            sticky="ew"
        )

    def create_input(self, row, label, default=""):

        lbl = ctk.CTkLabel(
            self,
            text=label
        )

        lbl.grid(
            row=(row * 2) - 1,
            column=0,
            sticky="w",
            pady=(5, 5)
        )

        entry = ctk.CTkEntry(
            self,
            height=42
        )

        entry.grid(
            row=(row * 2),
            column=0,
            sticky="ew",
            pady=(0, 15)
        )

        if default:
            entry.insert(0, default)

        # Bind to text change event for auto-save
        if self.auto_save_callback:
            entry.bind("<<Change>>", lambda e: self.auto_save_callback(show_feedback=False))

        return entry
