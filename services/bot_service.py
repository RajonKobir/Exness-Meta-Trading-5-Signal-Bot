import importlib
import threading
import time
import random
from datetime import datetime, timedelta, timezone

from core.mt5_connector import MT5Connector

# zoneinfo is preferred for timezone handling (Python 3.9+)
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

try:
    pytz = importlib.import_module("pytz")
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


def _candle_get(candle, key, default=None):
    if candle is None:
        return default

    if isinstance(candle, dict):
        return candle.get(key, default)

    if hasattr(candle, "get"):
        try:
            return candle.get(key, default)
        except Exception:
            pass

    if hasattr(candle, "dtype") and getattr(candle, "dtype") is not None:
        try:
            names = getattr(candle.dtype, "names", None)
            if names and key in names:
                return candle[key]
        except Exception:
            pass

    try:
        return getattr(candle, key, default)
    except Exception:
        pass

    try:
        return candle[key]
    except Exception:
        pass

    return default


class BotService:

    def __init__(
        self,
        report_panel,
        database=None,
        telegram_service=None,
        timezone=None
    ):

        self.report_panel = report_panel
        self.database = database
        self.telegram_service = telegram_service
        self.timezone = timezone or "Asia/Dhaka"

        self.running = False

        self.thread = None

        self.mt5 = MT5Connector()
        self.last_failed_telegram = None
        self.failure_callback = None

    # ==========================================
    # START BOT
    # ==========================================

    def start(
        self,
        symbol,
        candle_count,
        interval_minutes,
        buy_threshold=16,
        sell_threshold=16
    ):

        # prevent double click
        if self.running:

            self.report_panel.log_warning(
                "Bot is already running."
            )

            return

        self.running = True

        self.thread = threading.Thread(
            target=self.run_loop,
            args=(
                symbol,
                candle_count,
                interval_minutes,
                buy_threshold,
                sell_threshold
            ),
            daemon=True
        )

        self.thread.start()

    def set_failure_callback(self, cb):

        self.failure_callback = cb

    def determine_signal(self, buy_count, sell_count, buy_threshold, sell_threshold):
        """Determines buy/sell signals from counts and thresholds.

        Returns a tuple (buy_signal: bool, sell_signal: bool, signal_name: str|None)
        """
        try:
            bt = int(buy_threshold)
        except Exception:
            bt = int(16)

        try:
            st = int(sell_threshold)
        except Exception:
            st = int(16)

        # Signal if count <= threshold (less than or equal)
        buy_signal = buy_count <= bt
        sell_signal = sell_count <= st

        if sell_signal and buy_signal:
            signal_name = "BUY/SELL"
        elif sell_signal:
            signal_name = "SELL"
        elif buy_signal:
            signal_name = "BUY"
        else:
            signal_name = None

        return buy_signal, sell_signal, signal_name

    def retry_last_telegram(self):

        if not self.last_failed_telegram:
            return False, {"error": "No last failed telegram to retry."}

        if not self.telegram_service:
            return False, {"error": "No telegram service configured."}

        message = self.last_failed_telegram.get("message")

        try:
            resp = self.telegram_service.send_message(message)

            if isinstance(resp, tuple):
                success, details = resp
            else:
                success = bool(resp)
                details = None

            if success:

                self.report_panel.log_success("Telegram retry succeeded.")

                # persist
                if self.database:
                    try:
                        self.database.insert_message(message)
                        self.report_panel.log_success("Message saved to database.")
                    except Exception as e:
                        self.report_panel.log_error(f"Database save failed: {str(e)}")

                # clear last failed
                self.last_failed_telegram = None

                if self.failure_callback:
                    try:
                        self.failure_callback(None)
                    except Exception:
                        pass

                return True, details

            else:

                # update last failed details
                self.last_failed_telegram["details"] = details

                if self.failure_callback:
                    try:
                        self.failure_callback(self.last_failed_telegram)
                    except Exception:
                        pass

                return False, details

        except Exception as e:

            return False, {"error": str(e)}

    # ==========================================
    # STOP BOT
    # ==========================================

    def stop(self):

        self.running = False

        try:
            self.mt5.shutdown()
        except:
            pass

        self.report_panel.set_status(
            "Bot stopped."
        )

        self.report_panel.clear_timer()

        self.report_panel.log_warning(
            "Bot stopped by user."
        )

    # ==========================================
    # MAIN LOOP
    # ==========================================

    def run_loop(
        self,
        symbol,
        candle_count,
        interval_minutes,
        buy_threshold,
        sell_threshold
    ):

        try:

            # ======================================
            # CONNECT MT5
            # ======================================

            self.report_panel.set_status(
                "Trying to connect to MetaTrader 5..."
            )

            self.report_panel.log(
                "Connecting to MT5 terminal..."
            )

            result = self.mt5.connect()

            # support both dict and bool response
            if isinstance(result, dict):

                success = result.get("success", False)
                message = result.get(
                    "message",
                    "Connection failed."
                )

            else:

                success = bool(result)
                message = (
                    "Connected successfully."
                    if success else
                    "Connection failed."
                )

            if not success:

                self.report_panel.set_status(
                    message
                )

                self.report_panel.log_error(
                    message
                )

                self.running = False

                return

            # ======================================
            # ACCOUNT INFO
            # ======================================

            account = self.mt5.get_account_info()

            if not account:

                self.report_panel.set_status(
                    "MT5 connected but no account logged in."
                )

                self.report_panel.log_error(
                    "Please login to your Exness MT5 account first."
                )

                self.running = False

                return

            self.report_panel.set_status(
                f"Connected to account: {account.login}"
            )

            self.report_panel.log_success(
                f"Connected to account: {account.login}"
            )

            # ======================================
            # ITERATION LOOP
            # ======================================

            while self.running:

                # ==================================
                # COLLECT CANDLES
                # ==================================

                self.report_panel.log(
                    f"Collecting latest "
                    f"{candle_count} candles for {symbol}..."
                )

                candles = self.mt5.get_candles(
                    symbol,
                    candle_count
                )

                if candles is None or (hasattr(candles, '__len__') and len(candles) == 0):

                    self.report_panel.log_error(
                        "Failed to collect candle data."
                    )

                else:

                    buy_count = 0
                    sell_count = 0

                    # ==============================
                    # PROCESS CANDLES
                    # ==============================

                    for candle in candles:
                        # Prefer an explicit per-candle "signal" field when present.
                        # This supports inputs like:
                        # { ..., "signal": "SELL" }
                        sig = None
                        try:
                            sig = str(_candle_get(candle, "signal", "")).upper()
                        except Exception:
                            sig = None

                        if sig == "BUY":
                            buy_count += 1
                        elif sig == "SELL":
                            sell_count += 1
                        else:
                            # Fallback to legacy open/close comparison when no
                            # explicit signal is provided.
                            try:
                                open_val = _candle_get(candle, "open")
                                close_val = _candle_get(candle, "close")
                                if open_val is not None and close_val is not None:
                                    if close_val > open_val:
                                        buy_count += 1
                                    elif close_val < open_val:
                                        sell_count += 1
                            except Exception:
                                # ignore malformed candle entries
                                pass

                    # ==============================
                    # DETERMINE SIGNAL
                    # ==============================

                    # A BUY signal should occur when the number of buy (green)
                    # candles meets or exceeds the configured buy threshold.
                    # Likewise, a SELL signal should occur when the number of
                    # sell (red) candles meets or exceeds the sell threshold.
                    buy_signal, sell_signal, signal_name = self.determine_signal(
                        buy_count,
                        sell_count,
                        buy_threshold,
                        sell_threshold
                    )

                    has_signal = bool(signal_name)
                    signal_text = signal_name if signal_name else "NO SIGNAL"

                    # Debug: log counts, thresholds and evaluated booleans so
                    # it's clear why a particular signal was chosen.
                    # try:
                    #     debug_msg = (
                    #         f"DEBUG: buy_count={buy_count}, sell_count={sell_count}, "
                    #         f"buy_threshold={buy_threshold}, sell_threshold={sell_threshold}, "
                    #         f"buy_signal={buy_signal}, sell_signal={sell_signal}"
                    #     )
                    #     self.report_panel.log_below_last_report(debug_msg)
                    # except Exception:
                    #     pass

                    self.report_panel.add_candle_report(
                        total=candle_count,
                        green=buy_count,
                        red=sell_count,
                        signal=signal_name
                    )

                    if signal_name:

                        # determine timestamp in configured timezone
                        tz_name = getattr(self, "timezone", "Asia/Dhaka") or "Asia/Dhaka"
                        tz = _resolve_timezone(tz_name)
                        if tz is None:
                            tz = timezone(timedelta(hours=6))
                            tz_name = "Asia/Dhaka"

                        ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

                        def parse_time(value):
                            if isinstance(value, datetime):
                                return value
                            if not value:
                                return None
                            try:
                                return datetime.fromisoformat(str(value))
                            except Exception:
                                try:
                                    return datetime.strptime(
                                        str(value), "%Y-%m-%d %H:%M:%S"
                                    )
                                except Exception:
                                    return None

                        latest_candle = candle
                        try:
                            latest_candle = max(
                                candles,
                                key=lambda item: (
                                    parse_time(_candle_get(item, "time"))
                                    or datetime.min
                                )
                            )
                        except Exception:
                            latest_candle = candle

                        latest_time = _candle_get(latest_candle, "time")
                        parsed_time = parse_time(latest_time)
                        if parsed_time is not None:
                            if parsed_time.tzinfo is None:
                                parsed_time = parsed_time.replace(tzinfo=tz)
                            signal_time = parsed_time.astimezone(tz).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        else:
                            signal_time = ts

                        price = _candle_get(latest_candle, "close")
                        if price is None:
                            price = _candle_get(latest_candle, "open")

                        if isinstance(price, (int, float)):
                            price_text = f"{price:.3f}"
                        else:
                            price_text = str(price)

                        telegram_message = (
                            f"{signal_name} SIGNAL\n\n"
                            f"Symbol: {symbol}\n"
                            f"Signal Time: {signal_time}\n"
                            f"Sent: {ts} ({tz_name})\n"
                            f"Price: {price_text}\n"
                            f"BUY Candles: {buy_count}\n"
                            f"SELL Candles: {sell_count}\n"
                            f"Total Candles: {candle_count}"
                        )

                        self.report_panel.log_success(
                            f"{signal_name} signal matched."
                        )

                        if not self.telegram_service:
                            self.report_panel.log_warning(
                                "Telegram disabled; running in local/report-only mode."
                            )
                        else:
                            telegram_sent = False
                            telegram_details = None

                            try:
                                resp = self.telegram_service.send_message(
                                    telegram_message
                                )

                                if isinstance(resp, tuple):
                                    telegram_sent, telegram_details = resp
                                else:
                                    telegram_sent = bool(resp)
                                    telegram_details = None

                            except Exception as e:
                                telegram_sent = False
                                telegram_details = {"error": str(e)}
                                self.report_panel.log_error(
                                    f"Telegram error: {str(e)}"
                                )

                            if telegram_sent:
                                self.report_panel.log_success(
                                    "Telegram message sent successfully."
                                )

                                if self.database:
                                    try:
                                        self.database.insert_message(
                                            telegram_message
                                        )
                                        self.report_panel.log_success(
                                            "Message saved to database."
                                        )
                                    except Exception as e:
                                        self.report_panel.log_error(
                                            f"Database save failed: {str(e)}"
                                        )

                            else:
                                details_text = ""

                                try:
                                    if telegram_details:
                                        if "status_code" in telegram_details:
                                            details_text = (
                                                f" HTTP {telegram_details.get('status_code')}"
                                            )

                                        if telegram_details.get("text"):
                                            details_text += (
                                                f" - {telegram_details.get('text')[:200]}"
                                            )

                                        if telegram_details.get("error"):
                                            details_text = (
                                                f" Error: {telegram_details.get('error')}"
                                            )
                                except Exception:
                                    details_text = ""

                                self.last_failed_telegram = {
                                    "message": telegram_message,
                                    "details": telegram_details
                                }

                                try:
                                    if self.failure_callback:
                                        self.failure_callback(self.last_failed_telegram)
                                except Exception:
                                    pass

                                self.report_panel.log_below_last_report(
                                    f"ERROR: Failed to send Telegram message.{details_text}"
                                )

                    else:
                        self.report_panel.log(
                            "No signal matched criteria."
                        )

                # ==================================
                # COUNTDOWN TIMER
                # ==================================

                total_seconds = int(interval_minutes) * 60

                while (
                    total_seconds > 0 and
                    self.running
                ):

                    mins = total_seconds // 60
                    secs = total_seconds % 60

                    self.report_panel.set_timer(
                        f"{mins:02}:{secs:02}"
                    )

                    time.sleep(1)

                    total_seconds -= 1

            # ======================================
            # LOOP ENDED
            # ======================================

            self.report_panel.clear_timer()

            self.report_panel.set_status(
                "Bot stopped."
            )

        except Exception as e:

            self.running = False

            self.report_panel.clear_timer()

            self.report_panel.set_status(
                "Bot crashed."
            )

            self.report_panel.log_error(
                f"Bot runtime error: {str(e)}"
            )
