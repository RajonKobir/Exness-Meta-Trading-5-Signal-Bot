import customtkinter as ctk

from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.history_screen import HistoryScreen

from database.database import Database


class App(ctk.CTk):

    def __init__(self):

        super().__init__()

        # ==========================================
        # WINDOW SETTINGS
        # ==========================================

        self.title(
            "MT5 Telegram Signal Bot"
        )

        self.geometry("1400x900")

        self.minsize(1000, 700)

        ctk.set_appearance_mode("dark")

        ctk.set_default_color_theme("blue")

        # ==========================================
        # GRID
        # ==========================================

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ==========================================
        # DATABASE
        # ==========================================

        self.database = Database()

        # ==========================================
        # DASHBOARD SCREEN
        # ==========================================

        self.dashboard = DashboardScreen(
            self,
            self.open_history,
            self.database
        )

        self.dashboard.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        # ==========================================
        # WINDOW CLOSE EVENT
        # ==========================================

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    # ==========================================
    # OPEN HISTORY WINDOW
    # ==========================================

    def open_history(self):

        try:

            rows = self.database.get_messages()
            tz = getattr(self.dashboard, "current_timezone", "Asia/Dhaka") or "Asia/Dhaka"

            history = HistoryScreen(
                self,
                rows,
                database=self.database,
                timezone=tz
            )

            history.grab_set()

            history.focus()

        except Exception as e:

            # show error in report panel
            self.dashboard.reports.log_error(
                f"Failed to open history: {str(e)}"
            )

    # ==========================================
    # APP CLOSE
    # ==========================================

    def on_close(self):

        try:

            # stop running bot safely
            if hasattr(
                self.dashboard,
                "bot_running"
            ):

                self.dashboard.bot_running = False

            # shutdown mt5 safely
            if hasattr(
                self.dashboard,
                "mt5"
            ):

                try:
                    self.dashboard.mt5.shutdown()
                except:
                    pass

        except:
            pass

        self.destroy()