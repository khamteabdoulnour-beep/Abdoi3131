"""
ملف تشغيل سريع للبوت
للاستخدام: python start.py
"""
import os
import sys

def check_token():
    """التحقق من وجود التوكن"""
    token = os.getenv('BOT_TOKEN')
    
    if not token or token == 'ضع_توكن_البوت_هنا':
        print("=" * 60)
        print("❌ لم يتم العثور على توكن البوت!")
        print("=" * 60)
        print("\n📋 الخطوات:")
        print("1. احصل على توكن من @BotFather في تلجرام")
        print("2. ضع التوكن في ملف config.py")
        print("3. أو استخدم: set BOT_TOKEN=توكنك (Windows)")
        print("   أو: export BOT_TOKEN=توكنك (Linux/Mac)")
        print("\n" + "=" * 60)
        return False
    
    return True

def install_requirements():
    """تثبيت المتطلبات"""
    print("📦 جاري تثبيت المكتبات...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt -q")
    print("✅ تم تثبيت المكتبات!\n")

def main():
    """الدالة الرئيسية"""
    print("🤖 بوت المانهوا العربي")
    print("=" * 60)
    
    # تثبيت المتطلبات
    try:
        import telegram
    except ImportError:
        install_requirements()
    
    # التحقق من التوكن
    if not check_token():
        sys.exit(1)
    
    print("🚀 جاري تشغيل البوت...\n")
    
    # تشغيل البوت
    import bot
    bot.main()

if __name__ == "__main__":
    main()
