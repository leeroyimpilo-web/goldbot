from dataclasses import asdict, dataclass
from typing import Any
from app.config import settings


@dataclass
class MT5Status:
    available: bool
    initialized: bool
    terminal_connected: bool
    symbol: str
    message: str


class MT5Gateway:
    def __init__(self) -> None:
        self.mt5: Any | None = None

    def _load(self) -> bool:
        try:
            import MetaTrader5 as mt5  # type: ignore
        except ImportError:
            return False
        self.mt5 = mt5
        return True

    def status(self) -> dict:
        if not self._load():
            return asdict(MT5Status(False, False, False, settings.symbol, "MetaTrader5 package not installed."))

        initialized = bool(self.mt5.initialize())
        if not initialized:
            return asdict(MT5Status(True, False, False, settings.symbol, f"Initialize failed: {self.mt5.last_error()}"))

        terminal = self.mt5.terminal_info()
        connected = bool(terminal and terminal.connected)
        return asdict(MT5Status(True, True, connected, settings.symbol, "MT5 connected." if connected else "MT5 terminal offline."))

    def account_snapshot(self) -> dict:
        if not self._load() or not self.mt5.initialize():
            return {"available": False}
        account = self.mt5.account_info()
        if account is None:
            return {"available": False, "error": str(self.mt5.last_error())}
        return {
            "available": True,
            "login": account.login,
            "server": account.server,
            "currency": account.currency,
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "margin_free": account.margin_free,
        }

    def tick(self) -> dict:
        if not self._load() or not self.mt5.initialize():
            return {"available": False}
        tick = self.mt5.symbol_info_tick(settings.symbol)
        if tick is None:
            return {"available": False, "error": f"No tick for {settings.symbol}"}
        return {"available": True, "symbol": settings.symbol, "bid": tick.bid, "ask": tick.ask, "last": tick.last, "time_msc": tick.time_msc}
