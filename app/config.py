import os
#import env
def get_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    return int(value)
def get_required_env(name: str):
    env = os.getenv(name)

    if not env:
        raise RuntimeError(f"Missing required enviromental variable: {name}")

    return env

api_key = get_required_env("API_KEY")

# DB
postgres_db = os.getenv("POSTGRES_DB", "weather")
postgres_user = os.getenv("POSTGRES_USER", "web")
postgres_password = get_required_env("POSTGRES_PASSWORD")
postgres_host = os.getenv("POSTGRES_HOST", "db")
postgres_port = get_int("POSTGRES_PORT", 5432)

database_url = (
    f"postgresql+psycopg://{postgres_user}:"
    f"{postgres_password}@{postgres_host}:"
    f"{postgres_port}/{postgres_db}"
)