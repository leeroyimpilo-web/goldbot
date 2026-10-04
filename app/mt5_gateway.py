from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

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

    def _ready(self) -> bool:
        return bool(self._load() and self.mt5.initialize())

    def status(self) -> dict:
        if not self._load():
            return asdict(
                MT5Status(
                    False,
                    False,
                    False,
                    settings.symbol,
                    "MetaTrader5 package not installed.",
                )
            )

        initialized = bool(self.mt5.initialize())
        if not initialized:
            return asdict(
                MT5Status(
                    True,
                    False,
                    False,
                    settings.symbol,
                    f"Initialize failed: {self.mt5.last_error()}",
                )
            )

        terminal = self.mt5.terminal_info()
        connected = bool(terminal and terminal.connected)
        return asdict(
            MT5Status(
                True,
                True,
                connected,
                settings.symbol,
                "MT5 connected." if connected else "MT5 terminal offline.",
            )
        )

    def account_snapshot(self) -> dict:
        if not self._ready():
            return {"available": False}
        account = self.mt5.account_info()
        if account is None:
            return {"available": False, "error": str(self.mt5.last_error())}
        trade_mode_map = {
            getattr(self.mt5, "ACCOUNT_TRADE_MODE_DEMO", -1): "demo",
            getattr(self.mt5, "ACCOUNT_TRADE_MODE_CONTEST", -2): "contest",
            getattr(self.mt5, "ACCOUNT_TRADE_MODE_REAL", -3): "real",
        }
        return {
            "available": True,
            "login": account.login,
            "server": account.server,
            "currency": account.currency,
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "margin_free": account.margin_free,
            "trade_mode": trade_mode_map.get(account.trade_mode, "unknown"),
        }

    def tick(self) -> dict:
        if not self._ready():
            return {"available": False}
        tick = self.mt5.symbol_info_tick(settings.symbol)
        if tick is None:
            return {"available": False, "error": f"No tick for {settings.symbol}"}
        return {
            "available": True,
            "symbol": settings.symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "time_msc": tick.time_msc,
        }

    def _timeframe(self, name: str) -> int:
        mapping = {
            "M1": self.mt5.TIMEFRAME_M1,
            "M5": self.mt5.TIMEFRAME_M5,
            "M15": self.mt5.TIMEFRAME_M15,
            "M30": self.mt5.TIMEFRAME_M30,
            "H1": self.mt5.TIMEFRAME_H1,
            "H4": self.mt5.TIMEFRAME_H4,
            "D1": self.mt5.TIMEFRAME_D1,
        }
        if name not in mapping:
            raise ValueError(f"Unsupported timeframe: {name}")
        return mapping[name]

    def bars(self, timeframe: str, count: int) -> pd.DataFrame:
        if not self._ready():
            return pd.DataFrame()
        if count <= 0:
            raise ValueError("count must be positive")

        rates = self.mt5.copy_rates_from_pos(
            settings.symbol,
            self._timeframe(timeframe),
            1,
            count,
        )
        if rates is None or len(rates) == 0:
            return pd.DataFrame()

        frame = pd.DataFrame(rates)
        frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
        return frame.sort_values("time").reset_index(drop=True)

    def symbol_specs(self) -> dict:
        if not self._ready():
            return {"available": False}
        info = self.mt5.symbol_info(settings.symbol)
        if info is None:
            return {"available": False, "error": f"Symbol info unavailable for {settings.symbol}"}
        if not info.visible:
            self.mt5.symbol_select(settings.symbol, True)
        return {
            "available": True,
            "digits": info.digits,
            "point": info.point,
            "trade_contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step": info.volume_step,
            "trade_stops_level": info.trade_stops_level,
        }

    def recent_median_spread(self, points: int = 250) -> float | None:
        if not self._ready():
            return None

        start = datetime.now(timezone.utc) - timedelta(hours=2)
        ticks = self.mt5.copy_ticks_from(
            settings.symbol,
            start,
            points,
            self.mt5.COPY_TICKS_INFO,
        )
        if ticks is None or len(ticks) == 0:
            current = self.mt5.symbol_info_tick(settings.symbol)
            if current is None:
                return None
            return float(current.ask - current.bid)

        frame = pd.DataFrame(ticks)
        spreads = (frame["ask"] - frame["bid"]).loc[lambda s: s > 0]
        if spreads.empty:
            return None
        return float(spreads.median())

    def loss_per_lot(self, side: str, entry: float, stop: float) -> float:
        if not self._ready():
            raise RuntimeError("MT5 unavailable")
        order_type = (
            self.mt5.ORDER_TYPE_BUY if side == "buy" else self.mt5.ORDER_TYPE_SELL
        )
        result = self.mt5.order_calc_profit(
            order_type,
            settings.symbol,
            1.0,
            entry,
            stop,
        )
        if result is None:
            raise RuntimeError(f"order_calc_profit failed: {self.mt5.last_error()}")
        return abs(float(result))

    def check_market_order(self, plan: Any) -> dict:
        if not self._ready():
            return {"ok": False, "reason": "mt5_unavailable"}

        order_type = (
            self.mt5.ORDER_TYPE_BUY if plan.side == "buy" else self.mt5.ORDER_TYPE_SELL
        )
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": settings.symbol,
            "volume": float(plan.volume),
            "type": order_type,
            "price": float(plan.entry),
            "sl": float(plan.stop),
            "tp": float(plan.target),
            "deviation": 20,
            "magic": 260100,
            "comment": f"GoldBot {plan.strategy_version}",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        result = self.mt5.order_check(request)
        if result is None:
            return {
                "ok": False,
                "reason": "order_check_returned_none",
                "last_error": str(self.mt5.last_error()),
            }
        payload = result._asdict()
        return {
            "ok": int(payload.get("retcode", -1)) == 0,
            "retcode": payload.get("retcode"),
            "comment": payload.get("comment"),
            "margin": payload.get("margin"),
            "margin_free": payload.get("margin_free"),
            "margin_level": payload.get("margin_level"),
        }


    def send_market_order(self, plan: Any) -> dict:
        if not self._ready():
            return {"ok": False, "reason": "mt5_unavailable"}

        order_type = (
            self.mt5.ORDER_TYPE_BUY if plan.side == "buy" else self.mt5.ORDER_TYPE_SELL
        )
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": settings.symbol,
            "volume": float(plan.volume),
            "type": order_type,
            "price": float(plan.entry),
            "sl": float(plan.stop),
            "tp": float(plan.target),
            "deviation": 20,
            "magic": 260100,
            "comment": f"GoldBot {plan.strategy_version}",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        result = self.mt5.order_send(request)
        if result is None:
            return {
                "ok": False,
                "reason": "order_send_returned_none",
                "last_error": str(self.mt5.last_error()),
            }

        payload = result._asdict()
        success_codes = {
            getattr(self.mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(self.mt5, "TRADE_RETCODE_PLACED", 10008),
            getattr(self.mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010),
        }
        retcode = int(payload.get("retcode", -1))
        return {
            "ok": retcode in success_codes,
            "retcode": retcode,
            "comment": payload.get("comment"),
            "order": payload.get("order"),
            "deal": payload.get("deal"),
            "volume": payload.get("volume"),
            "price": payload.get("price"),
            "request_id": payload.get("request_id"),
        }


    def open_positions(self) -> list[dict]:
        if not self._ready():
            return []
        positions = self.mt5.positions_get(symbol=settings.symbol)
        if positions is None:
            return []
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "volume": p.volume,
                "type": p.type,
                "side": "buy"
                if p.type == getattr(self.mt5, "POSITION_TYPE_BUY", 0)
                else "sell",
                "price_open": p.price_open,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "magic": p.magic,
                "comment": p.comment,
                "time": p.time,
                "time_msc": getattr(p, "time_msc", 0),
            }
            for p in positions
        ]

    def latest_completed_bar_time(self, timeframe: str = "M15") -> str | None:
        frame = self.bars(timeframe, 1)
        if frame.empty:
            return None
        return frame.iloc[-1]["time"].isoformat()


    def ticks_range(self, start: datetime, end: datetime) -> pd.DataFrame:
        if not self._ready():
            return pd.DataFrame()
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("Tick range must use timezone-aware datetimes")
        if end <= start:
            raise ValueError("Tick range end must be after start")

        ticks = self.mt5.copy_ticks_range(
            settings.symbol,
            start.astimezone(timezone.utc),
            end.astimezone(timezone.utc),
            self.mt5.COPY_TICKS_ALL,
        )
        if ticks is None or len(ticks) == 0:
            return pd.DataFrame()

        frame = pd.DataFrame(ticks)
        if "time_msc" in frame.columns:
            frame["timestamp_utc"] = pd.to_datetime(frame["time_msc"], unit="ms", utc=True)
        else:
            frame["timestamp_utc"] = pd.to_datetime(frame["time"], unit="s", utc=True)
        frame["spread"] = frame["ask"] - frame["bid"]
        frame["mid"] = (frame["ask"] + frame["bid"]) / 2.0
        return frame.sort_values("timestamp_utc").reset_index(drop=True)


    def spread_percentile(self, current_spread: float, points: int = 250) -> float:
        if not self._ready():
            return 50.0

        start = datetime.now(timezone.utc) - timedelta(hours=2)
        ticks = self.mt5.copy_ticks_from(
            settings.symbol,
            start,
            points,
            self.mt5.COPY_TICKS_INFO,
        )
        if ticks is None or len(ticks) == 0:
            return 50.0

        frame = pd.DataFrame(ticks)
        spreads = (frame["ask"] - frame["bid"]).loc[lambda s: s > 0]
        if spreads.empty:
            return 50.0
        return float((spreads <= current_spread).mean() * 100.0)


    def modify_position_sl_tp(self, ticket: int, sl: float, tp: float) -> dict:
        if not self._ready():
            return {"ok": False, "reason": "mt5_unavailable"}

        request = {
            "action": self.mt5.TRADE_ACTION_SLTP,
            "position": int(ticket),
            "symbol": settings.symbol,
            "sl": float(sl),
            "tp": float(tp),
            "magic": 260100,
            "comment": "GoldBot risk management",
        }
        result = self.mt5.order_send(request)
        if result is None:
            return {
                "ok": False,
                "reason": "modify_returned_none",
                "last_error": str(self.mt5.last_error()),
            }
        payload = result._asdict()
        retcode = int(payload.get("retcode", -1))
        return {
            "ok": retcode == getattr(self.mt5, "TRADE_RETCODE_DONE", 10009),
            "retcode": retcode,
            "comment": payload.get("comment"),
        }

    def close_position(self, position: dict) -> dict:
        if not self._ready():
            return {"ok": False, "reason": "mt5_unavailable"}

        tick = self.mt5.symbol_info_tick(settings.symbol)
        if tick is None:
            return {"ok": False, "reason": "tick_unavailable"}

        if position["side"] == "buy":
            order_type = self.mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = self.mt5.ORDER_TYPE_BUY
            price = tick.ask

        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": settings.symbol,
            "position": int(position["ticket"]),
            "volume": float(position["volume"]),
            "type": order_type,
            "price": float(price),
            "deviation": 20,
            "magic": 260100,
            "comment": "GoldBot managed exit",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        result = self.mt5.order_send(request)
        if result is None:
            return {
                "ok": False,
                "reason": "close_returned_none",
                "last_error": str(self.mt5.last_error()),
            }
        payload = result._asdict()
        retcode = int(payload.get("retcode", -1))
        success_codes = {
            getattr(self.mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(self.mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010),
        }
        return {
            "ok": retcode in success_codes,
            "retcode": retcode,
            "comment": payload.get("comment"),
            "deal": payload.get("deal"),
            "price": payload.get("price"),
        }


    def recent_closed_goldbot_deals(self, days: int = 30) -> list[dict]:
        if not self._ready():
            return []

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=max(1, days))
        deals = self.mt5.history_deals_get(start, end)
        if deals is None:
            return []

        deal_entry_out = getattr(self.mt5, "DEAL_ENTRY_OUT", 1)
        deal_entry_out_by = getattr(self.mt5, "DEAL_ENTRY_OUT_BY", 3)
        results = []
        for d in deals:
            if d.symbol != settings.symbol:
                continue
            if int(getattr(d, "magic", 0)) != 260100:
                continue
            if int(getattr(d, "entry", -1)) not in {deal_entry_out, deal_entry_out_by}:
                continue

            net = (
                float(getattr(d, "profit", 0.0))
                + float(getattr(d, "commission", 0.0))
                + float(getattr(d, "swap", 0.0))
                + float(getattr(d, "fee", 0.0))
            )
            results.append(
                {
                    "ticket": int(d.ticket),
                    "position_id": int(getattr(d, "position_id", 0)),
                    "time": int(d.time),
                    "time_msc": int(getattr(d, "time_msc", 0)),
                    "price": float(d.price),
                    "volume": float(d.volume),
                    "net_profit": net,
                    "comment": str(getattr(d, "comment", "")),
                }
            )

        return sorted(results, key=lambda x: (x["time_msc"], x["ticket"]))
