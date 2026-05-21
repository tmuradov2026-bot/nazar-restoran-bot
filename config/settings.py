"""
Sozlamalar - .env faylidan o'qiladi
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Bot sozlamalari ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# --- Admin foydalanuvchilar (Telegram ID lar) ---
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# --- Ma'lumotlar bazasi ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///restaurant.db")
# PostgreSQL uchun:
# DATABASE_URL = "postgresql://user:password@localhost:5432/restaurant_db"

# --- Restoran ma'lumotlari ---
RESTAURANT_NAME = os.getenv("RESTAURANT_NAME", "Mening Restoranim")
RESTAURANT_ADDRESS = os.getenv("RESTAURANT_ADDRESS", "Toshkent, Chilonzor tumani")
RESTAURANT_PHONE = os.getenv("RESTAURANT_PHONE", "+998 90 123 45 67")
RESTAURANT_WORKING_HOURS = os.getenv("WORKING_HOURS", "10:00 - 23:00")

# --- Stol sozlamalari ---
TOTAL_TABLES = int(os.getenv("TOTAL_TABLES", "10"))

# --- Buyurtma holatlari ---
class OrderStatus:
    PENDING = "kutilmoqda"
    CONFIRMED = "tasdiqlandi"
    PREPARING = "tayyorlanmoqda"
    READY = "tayyor"
    DELIVERED = "yetkazildi"
    CANCELLED = "bekor_qilindi"

# --- Menu kategoriyalari ---
DEFAULT_CATEGORIES = [
    "Salatlar",
    "Sho'rvalar",
    "Asosiy taomlar",
    "Ichimliklar",
    "Shirinliklar",
    "Fastfood",
]
