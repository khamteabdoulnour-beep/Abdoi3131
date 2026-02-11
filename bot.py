"""
بوت تلجرام لسحب المانهوا من المواقع العربية
الأوامر:
/start - بدء البوت
/search - البحث عن مانهوا
/manga - عرض معلومات المانهوا
/chapter - قراءة فصل
/help - المساعدة
"""
import logging
import asyncio
from typing import Dict, List
from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

from config import BOT_TOKEN, BATCH_SIZE, DELAY_BETWEEN_MESSAGES
from scraper import MangaScraper, async_search_all, async_get_manga_info, async_get_chapter_images

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء محرك السحب
scraper = MangaScraper()

# حالات المحادثة
SEARCHING, SELECTING_MANGA, SELECTING_CHAPTER = range(3)

# تخزين مؤقت للمستخدمين
user_data_cache: Dict[int, Dict] = {}

# ==================== دوال مساعدة ====================

def get_source_name(url: str) -> str:
    """تحديد اسم المصدر من الرابط"""
    if 'lekmanga' in url:
        return "مانجا ليك"
    elif 'olympustaff' in url:
        return "أولمبوس"
    elif 'azoramoon' in url:
        return "أزورا"
    return "غير معروف"

def truncate_text(text: str, max_length: int = 4000) -> str:
    """تقصير النص الطويل"""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

# ==================== الأوامر الأساسية ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء"""
    welcome_text = """
🎌 *أهلاً بك في بوت المانهوا العربي!* 🎌

أنا بوت متخصص في سحب المانهوا من أفضل المواقع العربية:
• 📚 [مانجا ليك](https://lekmanga.net)
• 🏛️ [أولمبوس](https://olympustaff.com)
• 🌙 [أزورا مانجا](https://azoramoon.com)

*الأوامر المتاحة:*
🔍 /search `اسم المانهوا` - للبحث
📖 /manga `الرابط` - معلومات المانهوا
📄 /chapter `رابط الفصل` - قراءة فصل
❓ /help - المساعدة

*مثال:*
`/search Solo Leveling`
`/manga https://lekmanga.net/manga/solo-leveling/`

⚡️ *البوت يتجاوز الحماية ويدعم جميع أنواع المانهوا!*
    """
    
    keyboard = [
        [InlineKeyboardButton("🔍 بحث سريع", switch_inline_query_current_chat="")],
        [InlineKeyboardButton("📚 قائمة المواقع", callback_data="sites_list")],
        [InlineKeyboardButton("❓ كيفية الاستخدام", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    help_text = """
📖 *دليل استخدام البوت* 📖

*1️⃣ البحث عن مانهوا:*
أرسل: `/search اسم المانهوا`
مثال: `/search Solo Leveling`

*2️⃣ عرض معلومات المانهوا:*
أرسل: `/manga رابط المانهوا`
مثال: `/manga https://lekmanga.net/manga/solo-leveling/`

*3️⃣ قراءة فصل:*
أرسل: `/chapter رابط الفصل`
مثال: `/chapter https://lekmanga.net/manga/solo-leveling/chapter-1/`

*💡 نصائح:*
• يمكنك استخدام زر "بحث سريع" في القائمة
• البوت يرسل الصور على دفعات لتجنب الحظر
• انتظر قليلاً بين الطلبات
• إذا واجهت مشكلة، جرب رابطاً من موقع آخر

*⚠️ ملاحظات:*
• بعض الفصول قد تكون محمية ولا يمكن سحبها
• حجم الصور الكبيرة قد يتطلب وقتًا أطول
• البوت مجاني ويُحسّن باستمرار

*للدعم والاقتراحات:* @YourUsername
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ==================== البحث ====================

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البحث"""
    query = ' '.join(context.args)
    
    if not query:
        await update.message.reply_text(
            "❌ *يرجى إدخال اسم المانهوا للبحث*\n\n"
            "مثال: `/search Solo Leveling`",
            parse_mode='Markdown'
        )
        return
    
    # إرسال رسالة الانتظار
    wait_message = await update.message.reply_text(
        f"🔍 *جاري البحث عن:* `{query}`\n"
        f"⏳ هذا قد يستغرق بضع ثواني...",
        parse_mode='Markdown'
    )
    
    try:
        # البحث في جميع المواقع
        results = await async_search_all(scraper, query)
        
        if not results:
            await wait_message.edit_text(
                f"❌ *لم يتم العثور على نتائج لـ:* `{query}`\n\n"
                f"💡 *نصائح:*\n"
                f"• تأكد من كتابة الاسم بشكل صحيح\n"
                f"• جرب اسمًا آخر بالإنجليزية\n"
                f"• استخدم كلمات مفتاحية مختلفة",
                parse_mode='Markdown'
            )
            return
        
        # حفظ النتائج في الذاكرة
        user_id = update.effective_user.id
        user_data_cache[user_id] = {'search_results': results}
        
        # عرض النتائج
        text = f"✅ *تم العثور على {len(results)} نتيجة:*\n\n"
        
        keyboard = []
        for i, manga in enumerate(results[:10], 1):
            source_emoji = {"lekmanga": "📚", "olympustaff": "🏛️", "azoramoon": "🌙"}
            emoji = source_emoji.get(manga['source'], "📖")
            source_name = get_source_name(manga['url'])
            
            text += f"{i}. {emoji} *{manga['title']}*\n"
            text += f"   📍 المصدر: {source_name}\n"
            if manga['genres']:
                text += f"   🏷️ {', '.join(manga['genres'][:3])}\n"
            text += "\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{i}. {manga['title'][:30]}...",
                    callback_data=f"manga_{i-1}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔍 بحث جديد", callback_data="new_search")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await wait_message.edit_text(
            truncate_text(text),
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        await wait_message.edit_text(
            f"❌ *حدث خطأ أثناء البحث*\n\n"
            f"السبب: `{str(e)}`\n\n"
            f"🔄 حاول مرة أخرى لاحقاً",
            parse_mode='Markdown'
        )

# ==================== معلومات المانهوا ====================

async def manga_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر عرض معلومات المانهوا"""
    url = ' '.join(context.args)
    
    if not url:
        await update.message.reply_text(
            "❌ *يرجى إدخال رابط المانهوا*\n\n"
            "مثال: `/manga https://lekmanga.net/manga/solo-leveling/`",
            parse_mode='Markdown'
        )
        return
    
    # التحقق من صحة الرابط
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ *الرابط غير صالح*\n"
            "تأكد من أن الرابط يبدأ بـ http:// أو https://",
            parse_mode='Markdown'
        )
        return
    
    # إرسال رسالة الانتظار
    wait_message = await update.message.reply_text(
        "📖 *جاري جلب معلومات المانهوا...*\n"
        "⏳ انتظر قليلاً...",
        parse_mode='Markdown'
    )
    
    try:
        # تحديد المصدر
        source = get_source_name(url)
        
        # جلب المعلومات
        manga_info = await async_get_manga_info(scraper, url, source)
        
        if not manga_info:
            await wait_message.edit_text(
                "❌ *تعذر جلب معلومات المانهوا*\n\n"
                "💡 *الأسباب المحتملة:*\n"
                "• الرابط غير صحيح\n"
                "• الموقع محمي ولا يمكن الوصول إليه\n"
                "• المانهوا غير متوفرة\n\n"
                "🔄 جرب رابطاً من موقع آخر",
                parse_mode='Markdown'
            )
            return
        
        # حفظ البيانات
        user_id = update.effective_user.id
        user_data_cache[user_id] = {
            'manga_info': manga_info,
            'manga_url': url
        }
        
        # إعداد الرسالة
        text = f"""
📖 *{manga_info['title']}*

📍 *المصدر:* {source}
📊 *الحالة:* {manga_info['status']}
🏷️ *النوع:* {manga_info['type']}
📚 *عدد الفصول:* {len(manga_info['chapters'])}

📝 *الوصف:*
{truncate_text(manga_info['description'], 500)}

*اختر فصلاً للقراءة:*
        """
        
        # إعداد أزرار الفصول
        keyboard = []
        chapters = manga_info['chapters'][:15]  # أول 15 فصل
        
        for i in range(0, len(chapters), 3):
            row = []
            for ch in chapters[i:i+3]:
                row.append(
                    InlineKeyboardButton(
                        f"📄 {ch['number']}",
                        callback_data=f"chapter_{ch['url']}"
                    )
                )
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton("🔍 بحث جديد", callback_data="new_search"),
            InlineKeyboardButton("📖 قائمة المانهوا", callback_data="back_to_manga")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال الصورة مع النص
        if manga_info['image']:
            try:
                await wait_message.delete()
                await update.message.reply_photo(
                    photo=manga_info['image'],
                    caption=truncate_text(text),
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except:
                await wait_message.edit_text(
                    truncate_text(text),
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await wait_message.edit_text(
                truncate_text(text),
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"خطأ في جلب معلومات المانهوا: {e}")
        await wait_message.edit_text(
            f"❌ *حدث خطأ:* `{str(e)}`\n\n"
            f"🔄 حاول مرة أخرى",
            parse_mode='Markdown'
        )

# ==================== قراءة الفصل ====================

async def chapter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر قراءة الفصل"""
    url = ' '.join(context.args)
    
    if not url:
        await update.message.reply_text(
            "❌ *يرجى إدخال رابط الفصل*\n\n"
            "مثال: `/chapter رابط_الفصل`",
            parse_mode='Markdown'
        )
        return
    
    await send_chapter(update, context, url)

async def send_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """إرسال صور الفصل"""
    # إرسال رسالة الانتظار
    wait_message = await update.message.reply_text(
        "📄 *جاري تحميل الفصل...*\n"
        "⏳ قد يستغرق هذا بعض الوقت...",
        parse_mode='Markdown'
    )
    
    try:
        # تحديد المصدر
        source = get_source_name(url)
        
        # جلب صور الفصل
        images = await async_get_chapter_images(scraper, url, source)
        
        if not images:
            await wait_message.edit_text(
                "❌ *لم يتم العثور على صور في هذا الفصل*\n\n"
                "💡 *الأسباب المحتملة:*\n"
                "• الفصل محمي ويتطلب تسجيل دخول\n"
                "• الصور محملة بشكل ديناميكي\n"
                "• هيكل الموقع تغير\n\n"
                "🔄 جرب فصلاً آخر أو موقعاً مختلفاً",
                parse_mode='Markdown'
            )
            return
        
        await wait_message.edit_text(
            f"✅ *تم العثور على {len(images)} صورة*\n"
            f"📤 *جاري الإرسال...*",
            parse_mode='Markdown'
        )
        
        # إرسال الصور على دفعات
        total_images = len(images)
        sent = 0
        
        for i in range(0, total_images, BATCH_SIZE):
            batch = images[i:i+BATCH_SIZE]
            
            for img_url in batch:
                try:
                    await update.message.reply_photo(
                        photo=img_url,
                        caption=f"📄 صفحة {sent + 1}/{total_images}" if sent == 0 else f"📄 {sent + 1}",
                        parse_mode='Markdown'
                    )
                    sent += 1
                    await asyncio.sleep(0.5)  # تأخير بسيط
                except Exception as e:
                    logger.error(f"خطأ في إرسال الصورة {img_url}: {e}")
                    continue
            
            await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # حذف رسالة الانتظار
        await wait_message.delete()
        
        # رسالة النهاية
        await update.message.reply_text(
            f"✅ *تم إرسال {sent}/{total_images} صورة*\n\n"
            f"🔍 /search للبحث عن مانهوا جديد\n"
            f"📖 /manga لعرض معلومات المانهوا",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الفصل: {e}")
        await wait_message.edit_text(
            f"❌ *حدث خطأ:* `{str(e)}`",
            parse_mode='Markdown'
        )

# ==================== معالجات الأزرار ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "new_search":
        await query.edit_message_text(
            "🔍 *أرسل اسم المانهوا للبحث*\n\n"
            "مثال: `/search Solo Leveling`",
            parse_mode='Markdown'
        )
    
    elif data == "sites_list":
        sites_text = """
📚 *المواقع المدعومة:*

1️⃣ *مانجا ليك* (lekmanga.net)
   • مكتبة ضخمة من المانهوا
   • تحديثات سريعة
   • 📚 مانجا، مانهاو، مانهوا

2️⃣ *أولمبوس* (olympustaff.com)
   • ترجمات احترافية
   • فصول عالية الجودة
   • 🏛️ مانهوا صينية وكورية

3️⃣ *أزورا مانجا* (azoramoon.com)
   • مانجا وروايات
   • واجهة سهلة
   • 🌙 مانجا يابانية وكورية

🔍 استخدم /search للبحث في جميع المواقع
        """
        await query.edit_message_text(sites_text, parse_mode='Markdown')
    
    elif data == "help":
        await help_command(update, context)
    
    elif data.startswith("manga_"):
        # عرض معلومات المانهوا المختارة
        try:
            index = int(data.split("_")[1])
            user_cache = user_data_cache.get(user_id, {})
            results = user_cache.get('search_results', [])
            
            if index < len(results):
                manga = results[index]
                # محاكاة أمر /manga
                context.args = [manga['url']]
                await manga_command(update, context)
            else:
                await query.edit_message_text(
                    "❌ *انتهت صلاحية النتائج*\n"
                    "🔍 أرسل /search للبحث مرة أخرى",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"خطأ في معالج manga_: {e}")
    
    elif data.startswith("chapter_"):
        # إرسال الفصل
        try:
            url = data.replace("chapter_", "")
            # محاكاة أمر /chapter
            context.args = [url]
            await chapter_command(update, context)
        except Exception as e:
            logger.error(f"خطأ في معالج chapter_: {e}")

# ==================== معالج الرسائل ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    text = update.message.text
    
    # إذا كان الرابط
    if text.startswith(('http://', 'https://')):
        if '/chapter' in text.lower():
            context.args = [text]
            await chapter_command(update, context)
        else:
            context.args = [text]
            await manga_command(update, context)
    else:
        # معاملة كبحث
        context.args = text.split()
        await search_command(update, context)

# ==================== التشغيل الرئيسي ====================

def main():
    """الدالة الرئيسية"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("manga", manga_command))
    application.add_handler(CommandHandler("chapter", chapter_command))
    
    # معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # معالج الرسائل
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل البوت
    logger.info("🚀 جاري تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
