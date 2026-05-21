"""
Ma'lumotlar bazasi modellari - SQLAlchemy ORM
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session olish."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Barcha jadvallarni yaratish."""
    Base.metadata.create_all(bind=engine)
    _seed_initial_data()


def _seed_initial_data():
    """Boshlang'ich ma'lumotlarni kiritish."""
    from config.settings import TOTAL_TABLES, DEFAULT_CATEGORIES
    db = SessionLocal()
    try:
        # Kategoriyalar
        if db.query(Category).count() == 0:
            for cat_name in DEFAULT_CATEGORIES:
                db.add(Category(name=cat_name))
            db.commit()

        # Stollar
        if db.query(Table).count() == 0:
            for i in range(1, TOTAL_TABLES + 1):
                db.add(Table(number=i, capacity=4, is_available=True))
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed xatosi: {e}")
    finally:
        db.close()


# ─── Modellar ───────────────────────────────────────────────

class User(Base):
    """Telegram foydalanuvchilari."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user")


class Category(Base):
    """Menu kategoriyalari."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    emoji = Column(String(10), default="🍽️")
    is_active = Column(Boolean, default=True)

    items = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    """Menu taomlar."""
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="items")
    order_items = relationship("OrderItem", back_populates="menu_item")


class Table(Base):
    """Restoran stollari."""
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, nullable=False)
    capacity = Column(Integer, default=4)
    is_available = Column(Boolean, default=True)
    description = Column(String(200), nullable=True)

    orders = relationship("Order", back_populates="table")


class Order(Base):
    """Buyurtmalar."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True)
    status = Column(String(50), default="kutilmoqda")
    total_price = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    table = relationship("Table", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Buyurtmadagi taomlar."""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
