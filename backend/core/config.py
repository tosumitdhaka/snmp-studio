import os
from pathlib import Path


class Settings:
    # Base paths
    BASE_DIR   = Path(__file__).parent.parent.resolve()
    DATA_DIR   = BASE_DIR / "data"
    MIB_DIR    = DATA_DIR / "mibs"
    CONFIG_DIR = DATA_DIR / "configs"
    LOG_DIR    = DATA_DIR / "logs"

    # SNMP Settings
    SNMP_PORT  = int(os.getenv("SNMP_PORT",  "1061"))
    COMMUNITY  = os.getenv("SNMP_COMMUNITY", "public")
    TRAP_PORT  = int(os.getenv("TRAP_PORT",  "1162"))

    # File paths
    CUSTOM_DATA_FILE = CONFIG_DIR / "custom_data.json"
    SECRETS_FILE     = CONFIG_DIR / "secrets.json"
    STATS_FILE       = CONFIG_DIR / "stats.json"
    TRAPS_FILE       = DATA_DIR   / "traps.jsonl"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE  = LOG_DIR / "app.log"

    # Application metadata  (E1 fix: all read from env, not hardcoded)
    APP_NAME        = os.getenv("APP_NAME",        "Trishul SNMP Studio")
    APP_VERSION     = os.getenv("APP_VERSION",     "1.2.3")
    APP_AUTHOR      = os.getenv("APP_AUTHOR",      "Sumit Dhaka")
    APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "Network Management & SNMP Utilities")

    # Security
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # seconds

    # Auto-start flags (Part A)
    # Set to false in .env to disable auto-start on container boot
    AUTO_START_SIMULATOR     = os.getenv("AUTO_START_SIMULATOR",     "true").lower() == "true"
    AUTO_START_TRAP_RECEIVER = os.getenv("AUTO_START_TRAP_RECEIVER", "true").lower() == "true"

    def __init__(self):
        # Ensure directories exist
        self.DATA_DIR.mkdir(exist_ok=True)
        self.MIB_DIR.mkdir(exist_ok=True)
        self.CONFIG_DIR.mkdir(exist_ok=True)
        self.LOG_DIR.mkdir(exist_ok=True)

        # Create default files if they don't exist
        if not self.CUSTOM_DATA_FILE.exists():
            self.CUSTOM_DATA_FILE.write_text('{}')

        if not self.SECRETS_FILE.exists():
            import json
            self.SECRETS_FILE.write_text(json.dumps(
                {"username": "admin", "password": "admin123"}, indent=2
            ))

        if not self.TRAPS_FILE.exists():
            self.TRAPS_FILE.touch()


settings = Settings()


class AppMeta:
    # BUG-3 fix: read from settings instance (post-env-injection)
    NAME        = settings.APP_NAME
    VERSION     = settings.APP_VERSION
    AUTHOR      = settings.APP_AUTHOR
    DESCRIPTION = settings.APP_DESCRIPTION


meta = AppMeta()
