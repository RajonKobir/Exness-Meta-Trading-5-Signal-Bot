import customtkinter as ctk


class ButtonPanel(ctk.CTkFrame):

    def __init__(
        self,
        master,
        history_callback
    ):

        super().__init__(
            master,
            corner_radius=15
        )

        # ==========================================
        # CONFIG
        # ==========================================

        self.configure(
            fg_color="transparent"
        )

        # ==========================================
        # TITLE
        # ==========================================

        title = ctk.CTkLabel(
            self,
            text="Actions",
            font=("Arial", 28, "bold")
        )

        title.pack(
            pady=(10, 25)
        )

        # ==========================================
        # START BUTTON
        # ==========================================

        self.start_btn = ctk.CTkButton(
            self,
            text="START BOT",
            height=48,
            corner_radius=10,
            font=("Arial", 14, "bold")
        )

        self.start_btn.pack(
            fill="x",
            pady=8,
            padx=5
        )

        # ==========================================
        # STOP BUTTON
        # ==========================================

        self.stop_btn = ctk.CTkButton(
            self,
            text="STOP BOT",
            height=48,
            fg_color="#d11a2a",
            hover_color="#a80f1d",
            corner_radius=10,
            font=("Arial", 14, "bold"),
            state="disabled"
        )

        self.stop_btn.pack(
            fill="x",
            pady=8,
            padx=5
        )

        # ==========================================
        # HISTORY BUTTON
        # ==========================================

        self.history_btn = ctk.CTkButton(
            self,
            text="MESSAGE HISTORY",
            height=48,
            corner_radius=10,
            font=("Arial", 14, "bold"),
            command=history_callback
        )

        self.history_btn.pack(
            fill="x",
            pady=8,
            padx=5
        )

        # ==========================================
        # SAVE SETTINGS BUTTON
        # ==========================================

        self.save_btn = ctk.CTkButton(
            self,
            text="SAVE SETTINGS",
            height=48,
            corner_radius=10,
            font=("Arial", 14, "bold")
        )

        self.save_btn.pack(
            fill="x",
            pady=8,
            padx=5
        )

        # ==========================================
        # RETRY TELEGRAM BUTTON (disabled by default)
        # ==========================================

        self.retry_btn = ctk.CTkButton(
            self,
            text="RETRY TELEGRAM",
            height=40,
            corner_radius=10,
            font=("Arial", 12, "bold"),
            state="disabled"
        )

        self.retry_btn.pack(
            fill="x",
            pady=(6, 8),
            padx=5
        )

        # ==========================================
        # STATUS LABEL
        # ==========================================

        self.status_label = ctk.CTkLabel(
            self,
            text="Bot Status: Stopped",
            font=("Arial", 13),
            text_color="#bdbdbd"
        )

        self.status_label.pack(
            pady=(20, 5)
        )

        # internal running flag for state management
        self._is_running = False

    # ==========================================
    # BUTTON STATE HELPERS
    # ==========================================

    def disable_start(self):

        # disable the start button but keep its label to avoid layout shifts
        self.start_btn.configure(
            state="disabled"
        )

        self.status_label.configure(
            text="Bot Status: Running"
        )

    def enable_start(self):

        self.start_btn.configure(
            state="normal",
            text="START BOT"
        )

        self.status_label.configure(
            text="Bot Status: Stopped"
        )

    def enable_stop(self):

        self.stop_btn.configure(
            state="normal"
        )

    def disable_stop(self):

        self.stop_btn.configure(
            state="disabled"
        )

    # ==========================================
    # FULL RUNNING MODE
    # ==========================================

    def set_running_state(self):

        self._is_running = True

        self.disable_start()
        self.enable_stop()

    # ==========================================
    # FULL STOPPED MODE
    # ==========================================

    def set_stopped_state(self):

        self._is_running = False

        self.enable_start()
        self.disable_stop()

    # ==========================================
    # TEMPORARY LOCK
    # ==========================================

    def lock_buttons(self):

        self.start_btn.configure(
            state="disabled"
        )

        self.stop_btn.configure(
            state="disabled"
        )

        self.history_btn.configure(
            state="disabled"
        )

        self.save_btn.configure(
            state="disabled"
        )

    # ==========================================
    # UNLOCK BUTTONS
    # ==========================================

    def unlock_buttons(self):

        self.history_btn.configure(
            state="normal"
        )

        self.save_btn.configure(
            state="normal"
        )

        if self._is_running:

            self.stop_btn.configure(
                state="normal"
            )

        else:

            self.start_btn.configure(
                state="normal"
            )

    # ==========================================
    # RETRY BUTTON HELPERS
    # ==========================================

    def enable_retry(self):

        self.retry_btn.configure(state="normal")

    def disable_retry(self):

        self.retry_btn.configure(state="disabled")

    # ==========================================
    # SHOW CONNECTION STATUS
    # ==========================================

    def set_connection_status(
        self,
        connected,
        account_id=None
    ):

        if connected:

            text = (
                f"Connected to MT5 "
                f"(Account: {account_id})"
            )

            color = "#4caf50"

        else:

            text = "Disconnected from MT5"

            color = "#ff5555"

        self.status_label.configure(
            text=text,
            text_color=color
        )