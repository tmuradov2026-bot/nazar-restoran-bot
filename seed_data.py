"""
Boshlang'ich ma'lumotlarni Firebase'ga yuklash
Faqat bir marta ishlatiladi: python seed_data.py
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()


def seed():
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json"))
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Kategoriyalar
    categories = [
        {"name": "Sho'rvalar", "emoji": "🍲", "order": 1},
        {"name": "Asosiy taomlar", "emoji": "🍖", "order": 2},
        {"name": "Salatlar", "emoji": "🥗", "order": 3},
        {"name": "Ichimliklar", "emoji": "🥤", "order": 4},
        {"name": "Desertlar", "emoji": "🍰", "order": 5},
    ]
    cat_ids = {}
    for cat in categories:
        ref = db.collection("categories").add(cat)
        cat_ids[cat["name"]] = ref[1].id
        print(f"✅ Kategoriya: {cat['name']}")

    # Menyu elementlari
    menu_items = [
        # Sho'rvalar
        {"name": "Mastava", "category_id": cat_ids["Sho'rvalar"], "price": 25000,
         "description": "Guruchli o'zbek sho'rvasi", "emoji": "🍲", "prep_time": 15, "available": True},
        {"name": "Lag'mon", "category_id": cat_ids["Sho'rvalar"], "price": 30000,
         "description": "Qo'lda tortilgan lag'mon", "emoji": "🍜", "prep_time": 20, "available": True},
        # Asosiy taomlar
        {"name": "Osh (palov)", "category_id": cat_ids["Asosiy taomlar"], "price": 45000,
         "description": "Samarqand uslubida tayyorlangan palov", "emoji": "🍚", "prep_time": 25, "available": True},
        {"name": "Shashlik", "category_id": cat_ids["Asosiy taomlar"], "price": 55000,
         "description": "Tandirda pishirilgan mol shashlik", "emoji": "🍖", "prep_time": 30,
         "is_spicy": False, "available": True},
        {"name": "Manti", "category_id": cat_ids["Asosiy taomlar"], "price": 35000,
         "description": "Qo'y go'shtli manti (10 dona)", "emoji": "🥟", "prep_time": 30, "available": True},
        # Salatlar
        {"name": "Achichuk", "category_id": cat_ids["Salatlar"], "price": 15000,
         "description": "Pomidor va piyozdan tayyorlangan salat", "emoji": "🥗",
         "is_vegetarian": True, "prep_time": 5, "available": True},
        # Ichimliklar
        {"name": "Ko'k choy", "category_id": cat_ids["Ichimliklar"], "price": 8000,
         "description": "Yuqori sifatli ko'k choy (choynak)", "emoji": "🍵",
         "is_vegetarian": True, "prep_time": 5, "available": True},
        {"name": "Limonад", "category_id": cat_ids["Ichimliklar"], "price": 12000,
         "description": "Uy qurilmali limonad", "emoji": "🥤",
         "is_vegetarian": True, "prep_time": 3, "available": True},
        # Desertlar
        {"name": "Chak-chak", "category_id": cat_ids["Desertlar"], "price": 20000,
         "description": "An'anaviy o'zbek shirinligi", "emoji": "🍯",
         "is_vegetarian": True, "prep_time": 5, "available": True},
    ]
    for item in menu_items:
        db.collection("menu_items").add(item)
        print(f"  ✅ Menyu: {item['name']}")

    # Stollar
    tables = [
        {"number": 1, "seats": 2, "status": "available", "location": "Ichki zal"},
        {"number": 2, "seats": 4, "status": "available", "location": "Ichki zal"},
        {"number": 3, "seats": 4, "status": "available", "location": "Ichki zal"},
        {"number": 4, "seats": 6, "status": "available", "location": "VIP xona"},
        {"number": 5, "seats": 8, "status": "available", "location": "Tashqi ayvon"},
        {"number": 6, "seats": 2, "status": "available", "location": "Tashqi ayvon"},
    ]
    for t in tables:
        db.collection("tables").add(t)
        print(f"  ✅ Stol: #{t['number']} ({t['seats']} o'rin)")

    print("\n🎉 Ma'lumotlar muvaffaqiyatli yuklandi!")


if __name__ == "__main__":
    seed()
