from django.core.management.base import BaseCommand
from martyrs.models import Martyr
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re
import time


class Command(BaseCommand):
    help = 'Fetch persecution data from external sources via web scraping'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Specific source name to scrape (acn, opendoors, csw, release)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting data fetch...')
        
        sources = self.get_scraping_sources()
        
        if options['source']:
            sources = [s for s in sources if s['name'].lower() == options['source'].lower()]
        
        for source in sources:
            try:
                self.scrape_source(source)
                time.sleep(2)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error scraping {source["name"]}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('Data fetch completed.'))

    def get_scraping_sources(self):
        return [
            {
                'name': 'ACN',
                'url': 'https://acnuk.org/news/',
                'parser': 'parse_acn',
            },
            {
                'name': 'OpenDoors',
                'url': 'https://www.opendoorsuk.org/news/',
                'parser': 'parse_opendoors',
            },
            {
                'name': 'CSW',
                'url': 'https://www.csw.org.uk/latest.htm',
                'parser': 'parse_csw',
            },
            {
                'name': 'ReleaseInternational',
                'url': 'https://releaseinternational.org/news/',
                'parser': 'parse_release',
            },
            {
                'name': 'Persecution',
                'url': 'https://www.persecution.com/news/',
                'parser': 'parse_generic',
            },
            {
                'name': 'VoiceOfTheMartyrs',
                'url': 'https://www.vomcanada.com/news/',
                'parser': 'parse_generic',
            },
        ]

    def scrape_source(self, source):
        self.stdout.write(f'Scraping {source["name"]}...')
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(source['url'], headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            parser_method = getattr(self, source['parser'])
            parser_method(soup, source['url'], source['name'], headers)
                
        except requests.RequestException as e:
            self.stdout.write(
                self.style.WARNING(f'Failed to fetch {source["url"]}: {str(e)}')
            )
    
    def fetch_article_content(self, article_url, headers):
        try:
            response = requests.get(article_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            content_selectors = [
                'article .content',
                'article .post-content',
                '.article-content',
                '.entry-content',
                'main article',
                'article',
                '.content',
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    paragraphs = content_elem.find_all('p')
                    text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(text) > 50:
                        return text[:1000]
            
            paragraphs = soup.find_all('p', limit=10)
            text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return text[:1000] if text else None
            
        except:
            return None

    def parse_acn(self, soup, base_url, source_name, headers):
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in str(x).lower() or 'news' in str(x).lower() or 'post' in str(x).lower()), limit=20)
        
        if not articles:
            articles = soup.select('article, .article, .news-item, .post, [class*="article"], [class*="news"]')[:20]
        
        for article in articles:
            try:
                title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and ('title' in str(x).lower() if x else False))
                if not title_elem:
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                
                title = title_elem.get_text(strip=True) if title_elem else None
                if not title or len(title) < 5:
                    continue
                
                link_elem = article.find('a', href=True)
                article_url = urljoin(base_url, link_elem['href']) if link_elem else base_url
                
                date_elem = article.find(['time', '.date', '[class*="date"]', '[datetime]'])
                date_str = None
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                if not date_str:
                    date_elem = article.find(string=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'))
                    if date_elem:
                        date_str = date_elem.strip()
                
                date = self.parse_date(date_str) if date_str else datetime.now().date()
                
                desc_elem = article.find(['p', '.excerpt', '.summary', '[class*="excerpt"]', '[class*="summary"]'])
                description = desc_elem.get_text(strip=True) if desc_elem else title
                
                country = self.extract_country_from_text(title + ' ' + description)
                
                name = self.extract_name_from_title(title)
                
                if not Martyr.objects.filter(source_url=article_url).exists():
                    Martyr.objects.create(
                        name=name,
                        country=country,
                        date=date,
                        source_url=article_url,
                        description=description[:1000]
                    )
                    self.stdout.write(f'  Added: {name} - {country}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  Error parsing ACN article: {str(e)}')
                )
                continue

    def parse_opendoors(self, soup, base_url, source_name, headers):
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('story' in str(x).lower() or 'article' in str(x).lower() or 'post' in str(x).lower()), limit=20)
        
        if not articles:
            articles = soup.select('article, .story, .article, .post, [class*="story"], [class*="article"]')[:20]
        
        for article in articles:
            try:
                title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and ('title' in str(x).lower() if x else False))
                if not title_elem:
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                
                title = title_elem.get_text(strip=True) if title_elem else None
                if not title or len(title) < 5:
                    continue
                
                link_elem = article.find('a', href=True)
                article_url = urljoin(base_url, link_elem['href']) if link_elem else base_url
                
                date_elem = article.find(['time', '.date', '[class*="date"]', '[datetime]'])
                date_str = None
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                if not date_str:
                    date_elem = article.find(string=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'))
                    if date_elem:
                        date_str = date_elem.strip()
                
                date = self.parse_date(date_str) if date_str else datetime.now().date()
                
                desc_elem = article.find(['p', '.excerpt', '.summary', '[class*="excerpt"]', '[class*="summary"]'])
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                if article_url != base_url and len(description) < 100:
                    full_content = self.fetch_article_content(article_url, headers)
                    if full_content:
                        description = full_content
                
                if not description:
                    description = title
                
                if self.is_good_news(title, description):
                    continue
                
                country = self.extract_country_from_text(title + ' ' + description)
                
                name = self.extract_name_from_title(title)
                
                if name.lower() in ['news', 'latest', 'update', 'report', 'listen', 'prayer alert'] or len(name) < 5:
                    continue
                
                if not Martyr.objects.filter(source_url=article_url).exists():
                    Martyr.objects.create(
                        name=name,
                        country=country,
                        date=date,
                        source_url=article_url,
                        description=description[:1000]
                    )
                    self.stdout.write(f'  Added: {name} - {country}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  Error parsing OpenDoors article: {str(e)}')
                )
                continue

    def parse_csw(self, soup, base_url, source_name, headers):
        articles = soup.find_all(['article', 'div', 'li'], class_=lambda x: x and ('news' in str(x).lower() or 'article' in str(x).lower() or 'item' in str(x).lower()), limit=20)
        
        if not articles:
            articles = soup.select('article, .news, .article, .item, [class*="news"], [class*="article"]')[:20]
        
        for article in articles:
            try:
                title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=lambda x: x and ('title' in str(x).lower() if x else False))
                if not title_elem:
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
                
                title = title_elem.get_text(strip=True) if title_elem else None
                if not title or len(title) < 5:
                    continue
                
                link_elem = article.find('a', href=True)
                if not link_elem and title_elem.name == 'a':
                    link_elem = title_elem
                
                article_url = urljoin(base_url, link_elem['href']) if link_elem else base_url
                
                date_elem = article.find(['time', '.date', '[class*="date"]', '[datetime]'])
                date_str = None
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                if not date_str:
                    date_elem = article.find(string=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'))
                    if date_elem:
                        date_str = date_elem.strip()
                
                date = self.parse_date(date_str) if date_str else datetime.now().date()
                
                desc_elem = article.find(['p', '.excerpt', '.summary', '[class*="excerpt"]', '[class*="summary"]'])
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                if article_url != base_url and len(description) < 100:
                    full_content = self.fetch_article_content(article_url, headers)
                    if full_content:
                        description = full_content
                
                if not description:
                    description = title
                
                if self.is_good_news(title, description):
                    continue
                
                country = self.extract_country_from_text(title + ' ' + description)
                
                name = self.extract_name_from_title(title)
                
                if name.lower() in ['news', 'latest', 'update', 'report', 'listen', 'prayer alert'] or len(name) < 5:
                    continue
                
                if not Martyr.objects.filter(source_url=article_url).exists():
                    Martyr.objects.create(
                        name=name,
                        country=country,
                        date=date,
                        source_url=article_url,
                        description=description[:1000]
                    )
                    self.stdout.write(f'  Added: {name} - {country}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  Error parsing CSW article: {str(e)}')
                )
                continue

    def parse_release(self, soup, base_url, source_name, headers):
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('news' in str(x).lower() or 'article' in str(x).lower() or 'post' in str(x).lower()), limit=20)
        
        if not articles:
            articles = soup.select('article, .news, .article, .post, [class*="news"], [class*="article"]')[:20]
        
        for article in articles:
            try:
                title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and ('title' in str(x).lower() if x else False))
                if not title_elem:
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                
                title = title_elem.get_text(strip=True) if title_elem else None
                if not title or len(title) < 5:
                    continue
                
                link_elem = article.find('a', href=True)
                article_url = urljoin(base_url, link_elem['href']) if link_elem else base_url
                
                date_elem = article.find(['time', '.date', '[class*="date"]', '[datetime]'])
                date_str = None
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                if not date_str:
                    date_elem = article.find(string=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'))
                    if date_elem:
                        date_str = date_elem.strip()
                
                date = self.parse_date(date_str) if date_str else datetime.now().date()
                
                desc_elem = article.find(['p', '.excerpt', '.summary', '[class*="excerpt"]', '[class*="summary"]'])
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                if article_url != base_url and len(description) < 100:
                    full_content = self.fetch_article_content(article_url, headers)
                    if full_content:
                        description = full_content
                
                if not description:
                    description = title
                
                if self.is_good_news(title, description):
                    continue
                
                country = self.extract_country_from_text(title + ' ' + description)
                
                name = self.extract_name_from_title(title)
                
                if name.lower() in ['news', 'latest', 'update', 'report', 'listen', 'prayer alert'] or len(name) < 5:
                    continue
                
                if not Martyr.objects.filter(source_url=article_url).exists():
                    Martyr.objects.create(
                        name=name,
                        country=country,
                        date=date,
                        source_url=article_url,
                        description=description[:1000]
                    )
                    self.stdout.write(f'  Added: {name} - {country}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  Error parsing Release International article: {str(e)}')
                )
                continue

    def parse_generic(self, soup, base_url, source_name, headers):
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in str(x).lower() or 'news' in str(x).lower() or 'post' in str(x).lower() or 'story' in str(x).lower()), limit=20)
        
        if not articles:
            articles = soup.select('article, .article, .news-item, .post, .story, [class*="article"], [class*="news"]')[:20]
        
        for article in articles:
            try:
                title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and ('title' in str(x).lower() if x else False))
                if not title_elem:
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                
                title = title_elem.get_text(strip=True) if title_elem else None
                if not title or len(title) < 10:
                    continue
                
                if self.is_good_news(title, ''):
                    continue
                
                link_elem = article.find('a', href=True)
                article_url = urljoin(base_url, link_elem['href']) if link_elem else base_url
                
                date_elem = article.find(['time', '.date', '[class*="date"]', '[datetime]'])
                date_str = None
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                if not date_str:
                    date_elem = article.find(string=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'))
                    if date_elem:
                        date_str = date_elem.strip()
                
                date = self.parse_date(date_str) if date_str else datetime.now().date()
                
                desc_elem = article.find(['p', '.excerpt', '.summary', '[class*="excerpt"]', '[class*="summary"]'])
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                if article_url != base_url and len(description) < 100:
                    full_content = self.fetch_article_content(article_url, headers)
                    if full_content:
                        description = full_content
                
                if not description:
                    description = title
                
                if self.is_good_news(title, description):
                    continue
                
                country = self.extract_country_from_text(title + ' ' + description)
                
                name = self.extract_name_from_title(title)
                
                if name.lower() in ['news', 'latest', 'update', 'report', 'listen', 'prayer alert'] or len(name) < 5:
                    continue
                
                if not Martyr.objects.filter(source_url=article_url).exists():
                    Martyr.objects.create(
                        name=name,
                        country=country,
                        date=date,
                        source_url=article_url,
                        description=description[:1000]
                    )
                    self.stdout.write(f'  Added: {name} - {country}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  Error parsing {source_name} article: {str(e)}')
                )
                continue

    def is_good_news(self, title, description):
        good_news_keywords = [
            'released', 'freed', 'acquitted', 'exonerated', 'cleared',
            'rejoice', 'celebration', 'victory', 'success', 'good news',
            'thankful', 'grateful', 'praise god', 'answered prayer',
            'coming out of prison', 'set free', 'liberated'
        ]
        
        combined_text = (title + ' ' + description).lower()
        for keyword in good_news_keywords:
            if keyword in combined_text:
                return True
        return False

    def extract_country_from_text(self, text):
        countries = [
            'North Korea', 'Saudi Arabia', 'United Arab Emirates', 'Central African Republic',
            'Democratic Republic of Congo', 'South Africa', 'French Guiana',
            'Nigeria', 'Pakistan', 'India', 'China', 'Afghanistan',
            'Somalia', 'Libya', 'Yemen', 'Eritrea', 'Sudan', 'Iraq', 'Syria',
            'Iran', 'Egypt', 'Bangladesh', 'Vietnam', 'Myanmar', 'Laos',
            'Maldives', 'Turkmenistan', 'Uzbekistan', 'Kazakhstan',
            'Tajikistan', 'Nepal', 'Bhutan', 'Sri Lanka', 'Indonesia', 'Malaysia',
            'Brunei', 'Turkey', 'Azerbaijan', 'Algeria', 'Tunisia', 'Morocco',
            'Mauritania', 'Mali', 'Niger', 'Chad', 'Ethiopia', 'Kenya', 'Tanzania',
            'Uganda', 'Rwanda', 'Burundi', 'Cameroon',
            'Congo', 'Angola', 'Mozambique',
            'Zimbabwe', 'Botswana', 'Namibia', 'Madagascar',
            'Comoros', 'Djibouti', 'Lebanon', 'Jordan', 'Palestine', 'Israel',
            'Qatar', 'Kuwait', 'Bahrain', 'Oman',
            'Philippines', 'Thailand', 'Cambodia', 'Mongolia', 'Russia',
            'Ukraine', 'Belarus', 'Kyrgyzstan', 'Armenia', 'Georgia',
            'Albania', 'Bosnia', 'Serbia', 'Croatia', 'Bulgaria', 'Romania',
            'Greece', 'Cyprus', 'Malta', 'Venezuela', 'Colombia', 'Peru',
            'Ecuador', 'Bolivia', 'Paraguay', 'Brazil', 'Argentina', 'Chile',
            'Uruguay', 'Mexico', 'Guatemala', 'Honduras', 'El Salvador',
            'Nicaragua', 'Costa Rica', 'Panama', 'Cuba', 'Haiti', 'Jamaica',
            'Trinidad', 'Guyana', 'Suriname'
        ]
        
        text_lower = ' ' + text.lower() + ' '
        for country in countries:
            country_lower = country.lower()
            if ' ' + country_lower + ' ' in text_lower or text_lower.startswith(country_lower + ' ') or text_lower.endswith(' ' + country_lower):
                return country
        
        return 'Unknown'

    def extract_name_from_title(self, title):
        generic_words = {'news', 'latest', 'update', 'report', 'story', 'article', 
                        'persecution', 'christian', 'church', 'pastor', 'priest',
                        'kidnapped', 'killed', 'murdered', 'arrested', 'detained',
                        'chinese', 'russian', 'anti', 'suicide', 'webinar'}
        
        words = title.split()
        filtered_words = [w for w in words if w.lower() not in generic_words and len(w) > 2]
        
        if not filtered_words:
            return title[:50] if len(title) > 50 else title
        
        patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',
        ]
        
        title_text = ' '.join(filtered_words)
        for pattern in patterns:
            match = re.search(pattern, title_text)
            if match:
                name = match.group(1)
                if len(name) > 5 and len(name) < 50 and name.lower() not in generic_words:
                    return name
        
        if len(filtered_words) >= 2:
            potential_name = ' '.join(filtered_words[:3])
            if len(potential_name) > 5 and len(potential_name) < 60:
                return potential_name
        
        return title[:50] if len(title) > 50 else title

    def parse_date(self, date_str):
        if not date_str:
            return datetime.now().date()
        
        date_str = date_str.strip()
        
        formats = [
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%d %B %Y',
            '%d %b %Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:19], fmt).date()
            except:
                continue
        
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if match:
            day, month, year = match.groups()
            if len(year) == 2:
                year = '20' + year if int(year) < 50 else '19' + year
            try:
                return datetime(int(year), int(month), int(day)).date()
            except:
                pass
        
        return datetime.now().date()
