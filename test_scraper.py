"""
ملف اختبار محرك السحب
للاستخدام: python test_scraper.py
"""
from scraper import MangaScraper
import json

def test_search():
    """اختبار البحث"""
    print("🧪 اختبار البحث...")
    scraper = MangaScraper()
    
    query = "solo"
    print(f"🔍 البحث عن: {query}\n")
    
    results = scraper.search_all(query)
    
    print(f"✅ تم العثور على {len(results)} نتيجة\n")
    
    for i, manga in enumerate(results[:5], 1):
        print(f"{i}. {manga['title']}")
        print(f"   📍 المصدر: {manga['source']}")
        print(f"   🔗 الرابط: {manga['url']}")
        print()
    
    return results

def test_manga_info(url: str, source: str):
    """اختبار جلب معلومات المانهوا"""
    print(f"\n🧪 اختبار جلب معلومات المانهوا...")
    print(f"🔗 الرابط: {url}\n")
    
    scraper = MangaScraper()
    info = scraper.get_manga_info(url, source)
    
    if info:
        print(f"✅ تم جلب المعلومات بنجاح\n")
        print(f"📖 العنوان: {info['title']}")
        print(f"📝 الوصف: {info['description'][:200]}...")
        print(f"📊 الحالة: {info['status']}")
        print(f"📚 عدد الفصول: {len(info['chapters'])}")
        print(f"\nأول 5 فصول:")
        for ch in info['chapters'][:5]:
            print(f"  - الفصل {ch['number']}: {ch['url']}")
    else:
        print("❌ فشل جلب المعلومات")
    
    return info

def test_chapter_images(url: str, source: str):
    """اختبار جلب صور الفصل"""
    print(f"\n🧪 اختبار جلب صور الفصل...")
    print(f"🔗 الرابط: {url}\n")
    
    scraper = MangaScraper()
    images = scraper.get_chapter_images(url, source)
    
    if images:
        print(f"✅ تم العثور على {len(images)} صورة\n")
        print("أول 5 صور:")
        for img in images[:5]:
            print(f"  - {img}")
    else:
        print("❌ لم يتم العثور على صور")
    
    return images

def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🤖 اختبار بوت المانهوا العربي")
    print("=" * 60)
    
    # اختبار البحث
    results = test_search()
    
    if results:
        # اختبار جلب معلومات
        test_manga = results[0]
        info = test_manga_info(test_manga['url'], test_manga['source'])
        
        if info and info['chapters']:
            # اختبار جلب صور الفصل
            test_chapter = info['chapters'][0]
            test_chapter_images(test_chapter['url'], test_manga['source'])
    
    print("\n" + "=" * 60)
    print("✅ اكتمل الاختبار")
    print("=" * 60)

if __name__ == "__main__":
    main()
