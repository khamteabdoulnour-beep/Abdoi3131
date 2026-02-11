"""
ملف الإعدادات - ضع هنا التوكن والإعدادات
"""
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# ==================== إعدادات البوت ====================
# احصل على توكن البوت من @BotFather في تلجرام
BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")

# معرف الأدمن (اختياري - للإشعارات)
ADMIN_ID = os.getenv("ADMIN_ID", "")

# ==================== إعدادات الاستضافة ====================
# المنفذ للاستضافة (Render يستخدم المنفذ من متغير البيئة)
PORT = int(os.getenv("PORT", 8080))

# ==================== إعدادات المواقع ====================
# روابط المواقع المدعومة
SITES = {
    "lekmanga": {
        "name": "مانجا ليك",
        "base_url": "https://lekmanga.net",
        "enabled": True
    },
    "olympustaff": {
        "name": "أولمبوس",
        "base_url": "https://olympustaff.com",
        "enabled": True
    },
    "azoramoon": {
        "name": "أزورا مانجا",
        "base_url": "https://azoramoon.com",
        "enabled": True
    }
}

# ==================== إعدادات التحميل ====================
# عدد الصور في كل دفعة (لتجنب حظر التلجرام)
BATCH_SIZE = 10

# تأخير بين الرسائل (بالثواني)
DELAY_BETWEEN_MESSAGES = 1.5

# الحد الأقصى لحجم الصورة (بالميجابايت)
MAX_IMAGE_SIZE_MB = 20

# ==================== إعدادات التخزين المؤقت ====================
# تفعيل التخزين المؤقت
ENABLE_CACHE = True

# مدة التخزين المؤقت (بالدقائق)
CACHE_DURATION = 30
