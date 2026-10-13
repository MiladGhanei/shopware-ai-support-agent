import os

from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SHOPWARE_URL = os.getenv("SHOPWARE_URL")
SHOPWARE_ACCESS_ID = os.getenv("SHOPWARE_ACCESS_ID")
SHOPWARE_SECRET_ACCESS_KEY = os.getenv("SHOPWARE_SECRET_ACCESS_KEY")

required_settings = {
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "SHOPWARE_URL": SHOPWARE_URL,
    "SHOPWARE_ACCESS_ID": SHOPWARE_ACCESS_ID,
    "SHOPWARE_SECRET_ACCESS_KEY": SHOPWARE_SECRET_ACCESS_KEY,
}

missing_settings = [name for name, value in required_settings.items() if not value]

if missing_settings:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing_settings)}"
    )
