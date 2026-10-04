from dataclasses import dataclass


@dataclass(frozen=True)
class MarketSnapshot:
    h1_close: float
    h1_ema200: float
    h1_ema50: float
    h1_ema50_six_bars_ago: float
    m15_close: float
    m15_atr14: float
    m15_adx14: float
    donchian_high20: float
    donchian_low20: float


@dataclass(frozen=True)
class StrategySignal:
    side: str
    reason: str
    breakout_level: float
    atr: float


class MTFBreakoutV1:
    name = "mtf_breakout"
    version = "mtf_breakout_v1"
    adx_threshold = 22.0
    breakout_buffer_atr = 0.05

    def generate(self, market: MarketSnapshot) -> StrategySignal | None:
        buffer = self.breakout_buffer_atr * market.m15_atr14

        long_trend = (
            market.h1_close > market.h1_ema200
            and market.h1_ema50 > market.h1_ema50_six_bars_ago
        )
        if (
            long_trend
            and market.m15_adx14 > self.adx_threshold
            and market.m15_close > market.donchian_high20 + buffer
        ):
            return StrategySignal("buy", "H1 uptrend + M15 breakout", market.donchian_high20, market.m15_atr14)

        short_trend = (
            market.h1_close < market.h1_ema200
            and market.h1_ema50 < market.h1_ema50_six_bars_ago
        )
        if (
            short_trend
            and market.m15_adx14 > self.adx_threshold
            and market.m15_close < market.donchian_low20 - buffer
        ):
            return StrategySignal("sell", "H1 downtrend + M15 breakout", market.donchian_low20, market.m15_atr14)

        return None
