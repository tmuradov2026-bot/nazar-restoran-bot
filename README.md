# 🍴 Telegram Restoran Bot — O'rnatish Qo'llanmasi

## Loyiha tuzilmasi

```
restaurant_bot/
├── bot.py                    ← Asosiy kirish nuqtasi
├── requirements.txt          ← Python kutubxonalari
├── Dockerfile                ← Cloud Run uchun konteyner
├── .env.example              ← Muhit o'zgaruvchilari namunasi
├── seed_data.py              ← Boshlang'ich ma'lumotlar yuklovchi
├── firebase-credentials.json ← Firebase kaliti (GitHubga YUKLAMANG!)
├── handlers/
│   ├── menu_handler.py       ← Menyu ko'rish
│   ├── order_handler.py      ← Buyurtma berish
│   ├── table_handler.py      ← Stol holati
│   └── admin_handler.py      ← Admin panel
└── services/
    └── firebase_service.py   ← Firebase Firestore operatsiyalari
```

---

## 1-qadam: Telegram Bot yaratish

1. Telegramda **@BotFather** ga yozing
2. `/newbot` buyrug'ini yuboring
3. Botingizga nom bering (masalan: `MyRestaurant Bot`)
4. Username bering (masalan: `myrestaurant_bot`)
5. Olingan **TOKEN**ni `.env` fayliga yozing

---

## 2-qadam: Firebase loyiha sozlash

1. [console.firebase.google.com](https://console.firebase.google.com) ga kiring
2. **"Add project"** → nom bering → yarating
3. **Firestore Database** → "Create database" → "Start in production mode"
4. **Project Settings** → **Service Accounts** tab
5. **"Generate new private key"** → JSON faylini yuklab oling
6. Faylni `firebase-credentials.json` deb saqlang (loyiha papkasiga)

### Firestore Security Rules (qoidalar):
Firebase Console → Firestore → Rules bo'limiga quyidagini qo'ying:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Faqat server (bot) kirishi mumkin — hamma yo'llar yopiq
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```
> Bot Admin SDK ishlatadi — bu qoidalar foydalanuvchi tarafidan kirishni bloklaydi.

---

## 3-qadam: Muhit o'zgaruvchilarini sozlash

```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:
```
TELEGRAM_BOT_TOKEN=1234567890:AAFxxxx...
ADMIN_USER_IDS=123456789          # Sizning Telegram ID'ingiz
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

**Telegram ID'ingizni bilish:** `@userinfobot` ga `/start` yuboring.

---

## 4-qadam: Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

---

## 5-qadam: Boshlang'ich ma'lumotlarni yuklash

```bash
python seed_data.py
```

Bu skript Firebase'ga quyidagilarni yuklaydi:
- 5 ta kategoriya (Sho'rvalar, Asosiy taomlar, Salatlar, Ichimliklar, Desertlar)
- 9 ta menyu elementi narxlari bilan
- 6 ta stol (2, 4, 6, 8 o'rinli)

---

## 6-qadam: Botni ishga tushirish (local test)

```bash
python bot.py
```

Bot polling rejimida ishga tushadi. Telegramdan `/start` yuboring.

---

## 7-qadam: Google Cloud Run'ga deploy qilish (production)

### GCP sozlash:
```bash
# Google Cloud CLI o'rnatilgan bo'lishi kerak
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Docker image qurish va yuklash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/restaurant-bot

# Cloud Run'ga deploy qilish
gcloud run deploy restaurant-bot \
  --image gcr.io/YOUR_PROJECT_ID/restaurant-bot \
  --platform managed \
  --region europe-west1 \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token \
  --set-env-vars ADMIN_USER_IDS=your_id \
  --set-env-vars WEBHOOK_URL=https://your-service-url.run.app \
  --allow-unauthenticated
```

### Webhook o'rnatish:
Cloud Run URL'ini olgandan so'ng, `.env` da `WEBHOOK_URL` ni yangilang va botni qayta deploy qiling.

---

## Bot imkoniyatlari

### Foydalanuvchilar uchun:
| Buyruq | Tavsif |
|--------|---------|
| `/start` | Bosh menyu (inline tugmalar bilan) |
| `/menu` | Kategoriyalar ro'yxati |
| `/tables` | Stollar holati (bo'sh/band) |
| `/myorders` | Mening buyurtmalarim |

### Admin uchun:
| Buyruq | Tavsif |
|--------|---------|
| `/admin` | Admin panel |
| Buyurtmalar tab | Barcha buyurtmalar, holat o'zgartirish |
| Stollar tab | Stol holati toggle (band/bo'sh) |
| Statistika tab | Daromad va buyurtmalar hisoboti |

---

## Savat (cart) ishlashi

Foydalanuvchi menyudan mahsulot tanlaydi → **"Buyurtma berish"** tugmasi → mahsulot savatga qo'shiladi (Telegram session'da saqlanadi) → **"Savatni ko'rish"** → **"Tasdiqlash"** → Firebase'ga yoziladi.

---

## Firebase kolleksiyalar sxemasi

```
categories/
  {id}: { name, emoji, order }

menu_items/
  {id}: { name, category_id, price, description, emoji,
          prep_time, available, is_spicy?, is_vegetarian? }

tables/
  {id}: { number, seats, status, location, occupied_by?, updated_at }

orders/
  {id}: { user_id, items[], table_id?, total_price,
          status, created_at, updated_at }

users/
  {user_id}: { user_id, username, full_name, last_seen }

reservations/
  {id}: { table_id, user_id, reservation_time, status, created_at }
```

---

## Kengaytirish imkoniyatlari

- 💳 **To'lov integratsiyasi** — Click, Payme API
- 📱 **SMS bildirishnoma** — Eskiz.uz yoki Playmobile
- 🗺 **Yetkazib berish** — Manzil so'rash va xaritada ko'rsatish
- 📊 **Batafsil hisobot** — Google Sheets yoki Looker Studio
- 🌐 **Web admin panel** — Firebase Hosting + React
- 🔔 **Real-time bildirishnomalar** — Admin botga yangi buyurtma kelganda xabar
