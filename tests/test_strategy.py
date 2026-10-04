from app.strategy import MTFBreakoutV1, MarketSnapshot


def test_long_breakout_signal():
    market = MarketSnapshot(
        h1_close=3000,
        h1_ema200=2950,
        h1_ema50=2990,
        h1_ema50_six_bars_ago=2975,
        m15_close=3010,
        m15_atr14=10,
        m15_adx14=25,
        donchian_high20=3008,
        donchian_low20=2960,
    )
    signal = MTFBreakoutV1().generate(market)
    assert signal is not None
    assert signal.side == "buy"
