import customtkinter as ctk

from tkinter import ttk

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


class HistoryScreen(ctk.CTkToplevel):

    def __init__(self, master, rows=None, database=None, timezone="Asia/Dhaka"):
        super().__init__(master)

        self.timezone_name = timezone or "Asia/Dhaka"
        self._timezone = _resolve_timezone(self.timezone_name)

        super().__init__(master)

        self.title("Telegram Message History")

        self.geometry("1400x800")

        self.rows = rows or []

        self.database = database

        self.current_page = 1

        self.per_page = 15

        # ==========================================
        # TITLE
        # ==========================================

        title = ctk.CTkLabel(
            self,
            text="MESSAGE HISTORY",
            font=("Arial", 34, "bold")
        )

        title.pack(pady=20)

        # ==========================================
        # TABLE FRAME
        # ==========================================

        self.table_frame = ctk.CTkFrame(self)

        self.table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        # ==========================================
        # TABLE STYLE
        # ==========================================

        style = ttk.Style()

        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#1e1e1e",
            foreground="white",
            rowheight=42,
            fieldbackground="#1e1e1e",
            bordercolor="#444",
            borderwidth=1,
            font=("Arial", 12)
        )

        style.configure(
            "Treeview.Heading",
            background="#2b2b2b",
            foreground="white",
            relief="flat",
            font=("Arial", 13, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#22577A")]
        )

        # ==========================================
        # TABLE
        # ==========================================

        columns = (
            "id",
            "date",
            "message"
        )

        self.tree = ttk.Treeview(
            self.table_frame,
            columns=columns,
            show="headings"
        )

        self.tree.heading(
            "id",
            text="ID",
            anchor="center"
        )

        self.tree.heading(
            "date",
            text="Date",
            anchor="center"
        )

        self.tree.heading(
            "message",
            text="Message",
            anchor="w"
        )

        self.tree.column(
            "id",
            width=100,
            anchor="center"
        )

        self.tree.column(
            "date",
            width=250,
            anchor="center"
        )

        self.tree.column(
            "message",
            width=1200,
            minwidth=400,
            anchor="w",
            stretch=True
        )

        self.tree.configure(
            selectmode="extended"
        )

        # ==========================================
        # CONTROL BAR
        # ==========================================

        self.control_frame = ctk.CTkFrame(self)

        self.control_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        self.select_all_btn = ctk.CTkButton(
            self.control_frame,
            text="SELECT ALL",
            width=140,
            command=self.select_all_rows
        )

        self.select_all_btn.pack(
            side="left",
            padx=(0, 10)
        )

        self.clear_selection_btn = ctk.CTkButton(
            self.control_frame,
            text="CLEAR SELECTION",
            width=180,
            command=self.clear_selection
        )

        self.clear_selection_btn.pack(
            side="left",
            padx=(0, 10)
        )

        self.delete_selected_btn = ctk.CTkButton(
            self.control_frame,
            text="DELETE SELECTED",
            width=180,
            fg_color="#d11a2a",
            hover_color="#a80f1d",
            command=self.delete_selected_rows
        )

        self.delete_selected_btn.pack(
            side="left",
            padx=(0, 10)
        )

        # ==========================================
        # STRIPED ROWS
        # ==========================================

        self.tree.tag_configure(
            "oddrow",
            background="#1f1f1f"
        )

        self.tree.tag_configure(
            "evenrow",
            background="#2b2b2b"
        )

        # ==========================================
        # SCROLLBAR
        # ==========================================

        y_scrollbar = ttk.Scrollbar(
            self.table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        x_scrollbar = ttk.Scrollbar(
            self.table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        self.tree.pack(
            side="top",
            fill="both",
            expand=True
        )

        x_scrollbar.pack(
            side="bottom",
            fill="x"
        )

        y_scrollbar.pack(
            side="right",
            fill="y"
        )

        # ==========================================
        # PAGINATION
        # ==========================================

        self.pagination_frame = ctk.CTkFrame(self)

        self.pagination_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        self.prev_btn = ctk.CTkButton(
            self.pagination_frame,
            text="PREVIOUS",
            width=140,
            command=self.previous_page
        )

        self.prev_btn.pack(
            side="left",
            padx=10,
            pady=10
        )

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text=""
        )

        self.page_label.pack(
            side="left",
            expand=True
        )

        self.next_btn = ctk.CTkButton(
            self.pagination_frame,
            text="NEXT",
            width=140,
            command=self.next_page
        )

        self.next_btn.pack(
            side="right",
            padx=10,
            pady=10
        )

        # ==========================================
        # INITIAL LOAD
        # ==========================================

        self.load_table()

    # ==========================================
    # LOAD TABLE
    # ==========================================

    def load_table(self):

        for item in self.tree.get_children():

            self.tree.delete(item)

        start = (self.current_page - 1) * self.per_page

        end = start + self.per_page

        page_rows = self.rows[start:end]

        for index, row in enumerate(page_rows):

            tag = "evenrow"

            if index % 2 == 0:

                tag = "oddrow"

            # convert DB timestamp (assumed UTC string) to display TZ when available
            display_date = row.get("date", "")
            if display_date and self._timezone:
                try:
                    dt = datetime.strptime(display_date, "%Y-%m-%d %H:%M:%S")
                    dt = dt.replace(tzinfo=timezone.utc).astimezone(self._timezone)
                    display_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    display_date = row.get("date", "")

            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    display_date,
                    row["message"]
                ),
                tags=(tag,)
            )

        total_pages = max(
            1,
            (len(self.rows) + self.per_page - 1)
            // self.per_page
        )

        self.page_label.configure(
            text=f"Page {self.current_page} of {total_pages}"
        )

    # ==========================================
    # NEXT PAGE
    # ==========================================

    def next_page(self):

        total_pages = max(
            1,
            (len(self.rows) + self.per_page - 1)
            // self.per_page
        )

        if self.current_page < total_pages:

            self.current_page += 1

            self.load_table()

    # ==========================================
    # SELECT ALL ROWS
    # ==========================================

    def select_all_rows(self):

        self.tree.selection_set(self.tree.get_children())

    # ==========================================
    # CLEAR SELECTION
    # ==========================================

    def clear_selection(self):

        self.tree.selection_remove(self.tree.selection())

    # ==========================================
    # DELETE SELECTED ROWS
    # ==========================================

    def delete_selected_rows(self):

        selected = self.tree.selection()

        if not selected:
            return

        ids_to_delete = []

        for item in selected:
            row_values = self.tree.item(item).get("values", [])
            if row_values:
                ids_to_delete.append(row_values[0])

        if not ids_to_delete:
            return

        if self.database:
            try:
                self.database.delete_messages(ids_to_delete)
            except Exception as e:
                return

        self.rows = [
            row for row in self.rows
            if row["id"] not in ids_to_delete
        ]

        total_pages = max(
            1,
            (len(self.rows) + self.per_page - 1) // self.per_page
        )

        if self.current_page > total_pages:
            self.current_page = total_pages

        self.load_table()

    # ==========================================
    # PREVIOUS PAGE
    # ==========================================

    def previous_page(self):

        if self.current_page > 1:

            self.current_page -= 1

            self.load_table()