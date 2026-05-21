"""
Firebase Firestore bilan ishlash uchun servis
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Optional


class FirebaseService:
    """Firebase Firestore operatsiyalari"""

    def __init__(self):
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    # ─────────────── MENYU ───────────────

    def get_categories(self) -> list:
        """Barcha kategoriyalarni olish"""
        cats = self.db.collection("categories").order_by("order").stream()
        return [{"id": c.id, **c.to_dict()} for c in cats]

    def get_menu_items(self, category_id: Optional[str] = None) -> list:
        """Menyu elementlarini olish"""
        q = self.db.collection("menu_items").where("available", "==", True)
        if category_id:
            q = q.where("category_id", "==", category_id)
        return [{"id": i.id, **i.to_dict()} for i in q.stream()]

    def get_menu_item(self, item_id: str) -> Optional[dict]:
        """Bitta menyu elementini olish"""
        doc = self.db.collection("menu_items").document(item_id).get()
        return {"id": doc.id, **doc.to_dict()} if doc.exists else None

    def add_menu_item(self, data: dict) -> str:
        """Yangi menyu elementi qo'shish"""
        data["created_at"] = datetime.now()
        data["available"] = True
        ref = self.db.collection("menu_items").add(data)
        return ref[1].id

    def update_menu_item(self, item_id: str, data: dict) -> bool:
        """Menyu elementini yangilash"""
        data["updated_at"] = datetime.now()
        self.db.collection("menu_items").document(item_id).update(data)
        return True

    def delete_menu_item(self, item_id: str) -> bool:
        """Menyu elementini o'chirish (soft delete)"""
        self.db.collection("menu_items").document(item_id).update(
            {"available": False, "deleted_at": datetime.now()}
        )
        return True

    # ─────────────── STOLLAR ───────────────

    def get_all_tables(self) -> list:
        """Barcha stollarni olish"""
        tables = self.db.collection("tables").order_by("number").stream()
        return [{"id": t.id, **t.to_dict()} for t in tables]

    def get_table(self, table_id: str) -> Optional[dict]:
        """Bitta stolni olish"""
        doc = self.db.collection("tables").document(table_id).get()
        return {"id": doc.id, **doc.to_dict()} if doc.exists else None

    def update_table_status(self, table_id: str, status: str, user_id: Optional[int] = None) -> bool:
        """Stol holatini yangilash: 'available' | 'occupied' | 'reserved'"""
        data = {"status": status, "updated_at": datetime.now()}
        if user_id:
            data["occupied_by"] = user_id
        elif status == "available":
            data["occupied_by"] = None
        self.db.collection("tables").document(table_id).update(data)
        return True

    def reserve_table(self, table_id: str, user_id: int, reservation_time: datetime) -> str:
        """Stolni band qilish"""
        data = {
            "table_id": table_id,
            "user_id": user_id,
            "reservation_time": reservation_time,
            "status": "confirmed",
            "created_at": datetime.now()
        }
        ref = self.db.collection("reservations").add(data)
        self.update_table_status(table_id, "reserved", user_id)
        return ref[1].id

    # ─────────────── BUYURTMALAR ───────────────

    def create_order(self, user_id: int, items: list, table_id: Optional[str] = None) -> str:
        """Yangi buyurtma yaratish"""
        total = sum(item["price"] * item["quantity"] for item in items)
        data = {
            "user_id": user_id,
            "items": items,
            "table_id": table_id,
            "total_price": total,
            "status": "pending",   # pending → confirmed → preparing → ready → delivered
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        ref = self.db.collection("orders").add(data)
        return ref[1].id

    def get_order(self, order_id: str) -> Optional[dict]:
        """Bitta buyurtmani olish"""
        doc = self.db.collection("orders").document(order_id).get()
        return {"id": doc.id, **doc.to_dict()} if doc.exists else None

    def get_user_orders(self, user_id: int, limit: int = 10) -> list:
        """Foydalanuvchi buyurtmalarini olish"""
        orders = (self.db.collection("orders")
                  .where("user_id", "==", user_id)
                  .order_by("created_at", direction=firestore.Query.DESCENDING)
                  .limit(limit)
                  .stream())
        return [{"id": o.id, **o.to_dict()} for o in orders]

    def get_all_orders(self, status: Optional[str] = None, limit: int = 50) -> list:
        """Barcha buyurtmalarni olish (admin uchun)"""
        q = self.db.collection("orders").order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )
        if status:
            q = q.where("status", "==", status)
        return [{"id": o.id, **o.to_dict()} for o in q.limit(limit).stream()]

    def update_order_status(self, order_id: str, status: str) -> bool:
        """Buyurtma holatini yangilash"""
        self.db.collection("orders").document(order_id).update({
            "status": status,
            "updated_at": datetime.now()
        })
        return True

    # ─────────────── FOYDALANUVCHILAR ───────────────

    def save_user(self, user_id: int, username: str, full_name: str) -> None:
        """Foydalanuvchi ma'lumotlarini saqlash"""
        self.db.collection("users").document(str(user_id)).set({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "last_seen": datetime.now()
        }, merge=True)

    def is_admin(self, user_id: int) -> bool:
        """Foydalanuvchi admin ekanligini tekshirish"""
        admin_ids = os.getenv("ADMIN_USER_IDS", "").split(",")
        return str(user_id) in [a.strip() for a in admin_ids]
