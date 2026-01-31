import os

# توکن ربات مادر
MOTHER_BOT_TOKEN = os.getenv("MOTHER_BOT_TOKEN", "توکن_تو_اینجا")

# آیدی مالک ربات مادر
OWNER_ID = int(os.getenv("OWNER_ID", 123456789))

# وب هوک
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-app-name.onrender.com")
