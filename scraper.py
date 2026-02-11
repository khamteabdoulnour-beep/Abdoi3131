"""
محرك السحب من مواقع المانهوا العربية
يدعم: lekmanga.net, olympustaff.com, azoramoon.com
"""
import cloudscraper
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional, Tuple
import asyncio
import aiohttp
from urllib.parse import urljoin, quote
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MangaScraper:
    def __init__(self):
        # إنشاء scraper لتجاوز حماية Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        # إعدادات الطلبات
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    # ==================== دوال مساعدة ====================
    
    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """جلب الصفحة وتحليلها"""
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                logger.error(f"خطأ في جلب {url}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"استثناء في جلب {url}: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """تنظيف النص من المسافات الزائدة"""
        return ' '.join(text.split()) if text else ""
    
    # ==================== lekmanga.net ====================
    
    def search_lekmanga(self, query: str) -> List[Dict]:
        """البحث في مانجا ليك"""
        try:
            # رابط البحث
            search_url = f"https://lekmanga.net/?s={quote(query)}&post_type=wp-manga"
            soup = self._get_soup(search_url)
            
            if not soup:
                return []
            
            results = []
            # البحث عن نتائج
            manga_items = soup.find_all('div', class_='c-tabs-item__content')
            
            for item in manga_items[:10]:  # أول 10 نتائج
                try:
                    # الرابط والاسم
                    title_elem = item.find('div', class_='post-title').find('a')
                    if not title_elem:
                        continue
                    
                    title = self._clean_text(title_elem.text)
                    url = title_elem.get('href', '')
                    
                    # الصورة
                    img_elem = item.find('img')
                    image = img_elem.get('src', '') if img_elem else ''
                    
                    # التصنيفات
                    genres = []
                    genres_elem = item.find('div', class_='post-content_item')
                    if genres_elem:
                        genres = [g.text.strip() for g in genres_elem.find_all('a')]
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'image': image,
                        'genres': genres,
                        'source': 'lekmanga'
                    })
                except Exception as e:
                    logger.error(f"خطأ في parsing lekmanga: {e}")
                    continue
            
            return results
        except Exception as e:
            logger.error(f"خطأ في البحث في lekmanga: {e}")
            return []
    
    def get_manga_info_lekmanga(self, url: str) -> Optional[Dict]:
        """جلب معلومات المانهوا من مانجا ليك"""
        try:
            soup = self._get_soup(url)
            if not soup:
                return None
            
            # الاسم
            title_elem = soup.find('div', class_='post-title')
            title = self._clean_text(title_elem.text) if title_elem else "غير معروف"
            
            # الصورة
            image_elem = soup.find('div', class_='summary_image').find('img') if soup.find('div', class_='summary_image') else None
            image = image_elem.get('data-src', image_elem.get('src', '')) if image_elem else ''
            
            # الوصف
            desc_elem = soup.find('div', class_='summary__content')
            description = self._clean_text(desc_elem.text) if desc_elem else "لا يوجد وصف"
            
            # الحالة والنوع
            status = "مستمرة"
            manga_type = "مانهوا"
            
            info_items = soup.find_all('div', class_='post-content_item')
            for item in info_items:
                label = item.find('h5')
                if label:
                    label_text = label.text.strip()
                    value = item.find('div', class_='summary-content')
                    if value:
                        if 'الحالة' in label_text:
                            status = self._clean_text(value.text)
                        elif 'النوع' in label_text:
                            manga_type = self._clean_text(value.text)
            
            # الفصول
            chapters = []
            chapters_list = soup.find('ul', class_='main version-chap no-volumn')
            if chapters_list:
                for chapter in chapters_list.find_all('li', class_='wp-manga-chapter')[:20]:
                    try:
                        ch_link = chapter.find('a')
                        if ch_link:
                            ch_title = self._clean_text(ch_link.text)
                            ch_url = ch_link.get('href', '')
                            # رقم الفصل
                            ch_num = re.search(r'\d+\.?\d*', ch_title)
                            ch_num = ch_num.group() if ch_num else "?"
                            
                            chapters.append({
                                'number': ch_num,
                                'title': ch_title,
                                'url': ch_url
                            })
                    except:
                        continue
            
            return {
                'title': title,
                'image': image,
                'description': description,
                'status': status,
                'type': manga_type,
                'chapters': chapters,
                'source': 'lekmanga'
            }
        except Exception as e:
            logger.error(f"خطأ في جلب معلومات lekmanga: {e}")
            return None
    
    def get_chapter_images_lekmanga(self, url: str) -> List[str]:
        """جلب صور الفصل من مانجا ليك"""
        try:
            soup = self._get_soup(url)
            if not soup:
                return []
            
            images = []
            # البحث عن حاوية الصور
            container = soup.find('div', class_='reading-content')
            if container:
                for img in container.find_all('img'):
                    img_url = img.get('data-src', img.get('src', ''))
                    if img_url:
                        img_url = img_url.strip()
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        images.append(img_url)
            
            return images
        except Exception as e:
            logger.error(f"خطأ في جلب صور الفصل lekmanga: {e}")
            return []
    
    # ==================== olympustaff.com ====================
    
    def search_olympustaff(self, query: str) -> List[Dict]:
        """البحث في أولمبوس"""
        try:
            search_url = f"https://olympustaff.com/series?search={quote(query)}"
            soup = self._get_soup(search_url)
            
            if not soup:
                return []
            
            results = []
            # البحث عن العناصر
            manga_items = soup.find_all('div', class_='relative')
            
            for item in manga_items[:10]:
                try:
                    link = item.find('a')
                    if not link:
                        continue
                    
                    url = link.get('href', '')
                    if not url.startswith('http'):
                        url = 'https://olympustaff.com' + url
                    
                    # الصورة
                    img = link.find('img')
                    image = img.get('src', '') if img else ''
                    
                    # الاسم
                    title_elem = item.find('h3')
                    title = self._clean_text(title_elem.text) if title_elem else "غير معروف"
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'image': image,
                        'genres': [],
                        'source': 'olympustaff'
                    })
                except:
                    continue
            
            return results
        except Exception as e:
            logger.error(f"خطأ في البحث في olympustaff: {e}")
            return []
    
    def get_manga_info_olympustaff(self, url: str) -> Optional[Dict]:
        """جلب معلومات المانهوا من أولمبوس"""
        try:
            soup = self._get_soup(url)
            if not soup:
                return None
            
            # الاسم
            title_elem = soup.find('h1', class_='text-3xl')
            title = self._clean_text(title_elem.text) if title_elem else "غير معروف"
            
            # الصورة
            image_elem = soup.find('img', class_='rounded-lg')
            image = image_elem.get('src', '') if image_elem else ''
            
            # الوصف
            desc_elem = soup.find('div', class_='prose')
            description = self._clean_text(desc_elem.text) if desc_elem else "لا يوجد وصف"
            
            # المعلومات
            status = "مستمرة"
            manga_type = "مانهوا"
            
            info_divs = soup.find_all('div', class_='flex items-center')
            for div in info_divs:
                text = div.text
                if 'الحالة:' in text:
                    status = text.split(':')[-1].strip()
                elif 'النوع:' in text:
                    manga_type = text.split(':')[-1].strip()
            
            # الفصول
            chapters = []
            ch_container = soup.find('div', class_='space-y-2')
            if ch_container:
                for ch in ch_container.find_all('a')[:20]:
                    try:
                        ch_url = ch.get('href', '')
                        if not ch_url.startswith('http'):
                            ch_url = 'https://olympustaff.com' + ch_url
                        
                        ch_title = self._clean_text(ch.text)
                        ch_num = re.search(r'\d+\.?\d*', ch_title)
                        ch_num = ch_num.group() if ch_num else "?"
                        
                        chapters.append({
                            'number': ch_num,
                            'title': ch_title,
                            'url': ch_url
                        })
                    except:
                        continue
            
            return {
                'title': title,
                'image': image,
                'description': description,
                'status': status,
                'type': manga_type,
                'chapters': chapters,
                'source': 'olympustaff'
            }
        except Exception as e:
            logger.error(f"خطأ في جلب معلومات olympustaff: {e}")
            return None
    
    def get_chapter_images_olympustaff(self, url: str) -> List[str]:
        """جلب صور الفصل من أولمبوس"""
        try:
            soup = self._get_soup(url)
            if not soup:
                return []
            
            images = []
            # البحث عن جميع الصور في الصفحة
            all_images = soup.find_all('img')
            for img in all_images:
                src = img.get('src', '')
                # فلترة صور الفصل فقط (عادة تكون بصيغة رقمية)
                if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    if 'chapter' in src.lower() or 'upload' in src.lower():
                        images.append(src)
            
            return images
        except Exception as e:
            logger.error(f"خطأ في جلب صور الفصل olympustaff: {e}")
            return []
    
    # ==================== azoramoon.com ====================
    
    def search_azoramoon(self, query: str) -> List[Dict]:
        """البحث في أزورا"""
        try:
            search_url = f"https://azoramoon.com/series?search={quote(query)}"
            soup = self._get_soup(search_url)
            
            if not soup:
                return []
            
            results = []
            manga_items = soup.find_all('a', href=re.compile(r'/series/'))
            
            seen = set()
            for item in manga_items[:10]:
                try:
                    url = item.get('href', '')
                    if not url.startswith('http'):
                        url = 'https://azoramoon.com' + url
                    
                    if url in seen:
                        continue
                    seen.add(url)
                    
                    # الصورة
                    img = item.find('img')
                    image = img.get('src', '') if img else ''
                    
                    # الاسم
                    title_elem = item.find('div', class_=re.compile('font-bold|text-lg'))
                    title = self._clean_text(title_elem.text) if title_elem else "غير معروف"
                    
                    # التصنيفات
                    genres = []
                    genre_elems = item.find_all('div', class_=re.compile('badge|tag'))
                    genres = [g.text.strip() for g in genre_elems]
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'image': image,
                        'genres': genres,
                        'source': 'azoramoon'
                    })
                except:
                    continue
            
            return results
        except Exception as e:
            logger.error(f"خطأ في البحث في azoramoon: {e}")
            return []
    
    def get_manga_info_azoramoon(self, url: str) -> Optional[Dict]:
        """جلب معلومات المانهوا من أزورا"""
        try:
            soup = self._get_soup(url)
            if not soup:
                return None
            
            # الاسم
            title_elem = soup.find('h1', class_=re.compile('text-2xl|text-3xl'))
            title = self._clean_text(title_elem.text) if title_elem else "غير معروف"
            
            # الصورة
            image_elem = soup.find('img', class_=re.compile('rounded|cover'))
            image = image_elem.get('src', '') if image_elem else ''
            
            # الوصف
            desc_elem = soup.find('div', class_=re.compile('prose|description'))
            description = self._clean_text(desc_elem.text) if desc_elem else "لا يوجد وصف"
            
            # المعلومات
            status = "مستمرة"
            manga_type = "مانهوا"
            
            # الفصول
            chapters = []
            ch_links = soup.find_all('a', href=re.compile(r'/chapter-\d+'))
            
            seen = set()
            for ch in ch_links[:20]:
                try:
                    ch_url = ch.get('href', '')
                    if not ch_url.startswith('http'):
                        ch_url = 'https://azoramoon.com' + ch_url
                    
                    if ch_url in seen:
                        continue
                    seen.add(ch_url)
                    
                    ch_title = self._clean_text(ch.text)
                    ch_num = re.search(r'chapter-(\d+\.?\d*)', ch_url)
                    ch_num = ch_num.group(1) if ch_num else "?"
                    
                    chapters.append({
                        'number': ch_num,
                        'title': f"الفصل {ch_num}",
                        'url': ch_url
                    })
                except:
                    continue
            
            return {
                'title': title,
                'image': image,
                'description': description,
                'status': status,
                'type': manga_type,
                'chapters': chapters,
                'source': 'azoramoon'
            }
        except Exception as e:
            logger.error(f"خطأ في جلب معلومات azoramoon: {e}")
            return None
    
    def get_chapter_images_azoramoon(self, url: str) -> List[str]:
        """جلب صور الفصل من أزورا"""
        try:
            soup = self._get_soup(url)
            if not soup:
                return []
            
            images = []
            # البحث عن صور الفصل
            all_images = soup.find_all('img')
            for img in all_images:
                src = img.get('src', img.get('data-src', ''))
                if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    if 'chapter' in src.lower() or 'upload' in src.lower() or 'azoramoon' in src.lower():
                        images.append(src)
            
            return images
        except Exception as e:
            logger.error(f"خطأ في جلب صور الفصل azoramoon: {e}")
            return []
    
    # ==================== دوال عامة ====================
    
    def search_all(self, query: str) -> List[Dict]:
        """البحث في جميع المواقع"""
        all_results = []
        
        # البحث في مانجا ليك
        logger.info(f"البحث في مانجا ليك عن: {query}")
        results = self.search_lekmanga(query)
        all_results.extend(results)
        
        # البحث في أولمبوس
        logger.info(f"البحث في أولمبوس عن: {query}")
        results = self.search_olympustaff(query)
        all_results.extend(results)
        
        # البحث في أزورا
        logger.info(f"البحث في أزورا عن: {query}")
        results = self.search_azoramoon(query)
        all_results.extend(results)
        
        return all_results
    
    def get_manga_info(self, url: str, source: str) -> Optional[Dict]:
        """جلب معلومات المانهوا حسب المصدر"""
        if 'lekmanga' in source or 'lekmanga' in url:
            return self.get_manga_info_lekmanga(url)
        elif 'olympustaff' in url:
            return self.get_manga_info_olympustaff(url)
        elif 'azoramoon' in url:
            return self.get_manga_info_azoramoon(url)
        else:
            # محاولة تلقائية
            if 'lekmanga' in url:
                return self.get_manga_info_lekmanga(url)
            elif 'olympustaff' in url:
                return self.get_manga_info_olympustaff(url)
            elif 'azoramoon' in url:
                return self.get_manga_info_azoramoon(url)
        return None
    
    def get_chapter_images(self, url: str, source: str) -> List[str]:
        """جلب صور الفصل حسب المصدر"""
        if 'lekmanga' in source or 'lekmanga' in url:
            return self.get_chapter_images_lekmanga(url)
        elif 'olympustaff' in url:
            return self.get_chapter_images_olympustaff(url)
        elif 'azoramoon' in url:
            return self.get_chapter_images_azoramoon(url)
        else:
            # محاولة تلقائية
            if 'lekmanga' in url:
                return self.get_chapter_images_lekmanga(url)
            elif 'olympustaff' in url:
                return self.get_chapter_images_olympustaff(url)
            elif 'azoramoon' in url:
                return self.get_chapter_images_azoramoon(url)
        return []


# ==================== دوال غير متزامنة للبوت ====================

async def async_search_all(scraper: MangaScraper, query: str) -> List[Dict]:
    """بحث غير متزامن"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, scraper.search_all, query)

async def async_get_manga_info(scraper: MangaScraper, url: str, source: str) -> Optional[Dict]:
    """جلب معلومات غير متزامن"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, scraper.get_manga_info, url, source)

async def async_get_chapter_images(scraper: MangaScraper, url: str, source: str) -> List[str]:
    """جلب صور غير متزامن"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, scraper.get_chapter_images, url, source)
