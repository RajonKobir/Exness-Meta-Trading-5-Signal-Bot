import MetaTrader5 as mt5


class MT5Connector:

    def connect(self):

        initialized = mt5.initialize()

        if not initialized:

            return {
                "success": False,
                "message": f"MT5 initialize failed: {mt5.last_error()}"
            }

        account = mt5.account_info()

        if account is None:

            return {
                "success": False,
                "message": "MetaTrader5 opened but account is not logged in."
            }

        return {
            "success": True,
            "message": f"Connected to account: {account.login}"
        }

    def shutdown(self):

        mt5.shutdown()

    def get_account_info(self):

        try:
            return mt5.account_info()
        except Exception:
            return None

    def get_candles(self, symbol, count):

        try:
            rates = mt5.copy_rates_from_pos(
                symbol,
                mt5.TIMEFRAME_M1,
                0,
                int(count)
            )

            return rates

        except Exception:

            return None
