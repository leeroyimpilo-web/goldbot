from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://goldbot:goldbot@localhost:5432/goldbot"
    trading_mode: str = "research"
    live_trading_enabled: bool = False
    symbol: str = "XAUUSD"
    risk_per_trade: float = 0.0025
    daily_loss_limit: float = 0.01
    weekly_loss_limit: float = 0.025
    soft_drawdown_limit: float = 0.08
    hard_drawdown_limit: float = 0.10
    max_spread_ratio: float = 2.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
