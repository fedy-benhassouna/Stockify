import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import csv
from urllib.parse import urljoin, urlparse
import re

class YahooFinanceStockNewsScraper:
    def __init__(self):
        self.base_url = "https://finance.yahoo.com/topic/stock-market-news/"
        self.news_url = "https://finance.yahoo.com/topic/stock-market-news/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Stock-related keywords to filter articles
        self.stock_keywords = [
            'stock', 'stocks', 'share', 'shares', 'equity', 'trading', 'market',
            'earnings', 'revenue', 'profit', 'loss', 'nasdaq', 'nyse', 'dow',
            'sp 500', 's&p 500', 'bull', 'bear', 'rally', 'sell-off', 'selloff',
            'ipo', 'dividend', 'buyback', 'acquisition', 'merger', 'outlook',
            'guidance', 'analyst', 'rating', 'upgrade', 'downgrade', 'target',
            'quarterly', 'financial', 'results', 'beat', 'miss', 'estimate',
            'wall street', 'investors', 'investment', 'portfolio', 'volatility',
            'tech stocks', 'big tech', 'blue chip', 'penny stock', 'growth stock'
            ,'trump', 'biden', 'fed', 'interest rates', 'inflation', 'recession',
            'chinese stocks', 'emerging markets', 'forex', 'currency', 'commodities',
            'oil', 'gold', 'silver', 'bitcoin', 'cryptocurrency', 'crypto', 'blockchain',
            'etf', 'exchange traded fund', 'mutual fund', 'hedge fund', 'private equity'
        ]
        
        # Time-related keywords that indicate recent/breaking news
        self.recent_keywords = [
            'today', 'yesterday', 'this week', 'latest', 'breaking', 'just',
            'now', 'recent', 'current', 'live', 'update', 'alert', 'flash',
            'minutes ago', 'hours ago', 'this morning', 'afternoon', 'evening'
        ]

    def is_stock_related(self, title, summary=""):
        """
        Check if an article is stock-related based on title and summary
        
        Args:
            title (str): Article title
            summary (str): Article summary
            
        Returns:
            bool: True if article is stock-related
        """
        text_to_check = (title + " " + summary).lower()
        
        # Check for stock-related keywords
        for keyword in self.stock_keywords:
            if keyword in text_to_check:
                return True
        
        # Check for ticker symbols (e.g., AAPL, MSFT, TSLA)
        ticker_pattern = r'\b[A-Z]{2,5}\b'
        if re.search(ticker_pattern, title.upper()):
            return True
            
        return False



    def get_stock_news_articles(self, max_articles=20, recent_only=True):
        """
        Scrape stock-related news articles from Yahoo Finance
        
        Args:
            max_articles (int): Maximum number of articles to scrape
            recent_only (bool): Filter for recent/breaking news only
            
        Returns:
            list: List of dictionaries containing stock article information
        """
        try:
            response = self.session.get(self.news_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Find article containers using the current Yahoo Finance structure
            story_items = soup.select('li.stream-item.story-item')
            
            found_links = set()
            
            for item in story_items:
                if len(articles) >= max_articles:
                    break
                
                # Find the main article link
                link_elem = item.select_one('a.subtle-link.fin-size-small.titles')
                if not link_elem:
                    continue
                
                href = link_elem.get('href')
                if not href:
                    continue
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                elif not href.startswith('http'):
                    continue
                else:
                    full_url = href
                
                # Skip if we've already found this link
                if full_url in found_links:
                    continue
                found_links.add(full_url)
                
                # Only include Yahoo Finance articles
                if 'finance.yahoo.com' not in full_url:
                    continue
                
                # Get title from h3 element
                title_elem = link_elem.select_one('h3.clamp')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if not title:
                    continue
                
                # Get summary from p element within the same link
                summary = ""
                summary_elem = link_elem.select_one('p.clamp')
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)
                
                # Look for publication time in the container
                published_time = ""
                time_elem = item.select_one('time')
                if time_elem:
                    published_time = time_elem.get_text(strip=True)
                
                # Filter for stock-related articles
                if not self.is_stock_related(title, summary):
                    continue
                # Look for publication source and time from the publishing container
                source = ""
                published_time = ""

                publishing_elem = item.select_one('div.publishing')
                if publishing_elem:
                    publishing_text = publishing_elem.get_text(strip=True)
                    # Split by bullet (•) to get source and time
                    if '•' in publishing_text:
                        parts = publishing_text.split('•')
                        if len(parts) == 2:
                            source = parts[0].strip()
                            published_time = parts[1].strip()
                    else:
                        published_time = publishing_text  # fallback if source not present

              
                
                article_data = {
    'title': title,
    'url': full_url,
    'summary': summary,
    'published_time': published_time,
    'source': source,
    'scraped_at': datetime.now().isoformat(),
    'is_stock_related': True,
}

                
                # Get image URL if available, otherwise use a random default image
                default_images = [
                    "https://s.yimg.com/ny/api/res/1.2/JxL9.0xNg7f9krljH7d4NA--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTU5MDtjZj13ZWJw/https://media.zenfs.com/en/coindesk_75/4c28b0f43fae0efb59246f499c318734",
                    "https://s.yimg.com/ny/api/res/1.2/PmVoZe_Q_pEHipzsRASVDw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTc5NztjZj13ZWJw/https://media.zenfs.com/en/schaeffers_investment_research_24/87520bff28a27dddbc87a199813a45e4",
                    "https://s.yimg.com/ny/api/res/1.2/smvyJMz4zaQhjrVuk.7Dbg--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTU5MDtjZj13ZWJw/https://media.zenfs.com/en/coindesk_75/3e89817523d81e47bf7ea80988b1882c",
                    "https://s.yimg.com/ny/api/res/1.2/yXq8y4VNkrtt.fdJW1cocw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTU0MA--/https://media.zenfs.com/en/the_daily_upside_435/f5f7c2f0ae577e29c80d57e26a95f4a6"
                ]

                img_elem = item.select_one('img')
                img_src = img_elem.get('src') if img_elem and img_elem.get('src') else None

                if not img_src:
                    import random
                    img_src = random.choice(default_images)

                article_data['image_url'] = img_src


                
                articles.append(article_data)
            
            # Fallback: try alternative selectors if no articles found
            if not articles:
                print("Trying fallback selectors...")
                fallback_selectors = [
                    'h3 a[href*="finance.yahoo.com"]',
                    'a[href*="/news/"]',
                    '.stream-item a'
                ]
                
                for selector in fallback_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        if len(articles) >= max_articles:
                            break
                            
                        href = element.get('href')
                        if not href:
                            continue
                            
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            full_url = urljoin(self.base_url, href)
                        elif not href.startswith('http'):
                            continue
                        else:
                            full_url = href
                        
                        # Skip if we've already found this link
                        if full_url in found_links:
                            continue
                        found_links.add(full_url)
                        
                        # Only include Yahoo Finance articles
                        if 'finance.yahoo.com' not in full_url:
                            continue
                        
                        title = element.get_text(strip=True)
                        if not title:
                            continue
                        
                        # Filter for stock-related articles
                        if not self.is_stock_related(title):
                            continue
                        
                        article_data = {
                            'title': title,
                            'url': full_url,
                            'summary': '',
                            'published_time': '',
                            'scraped_at': datetime.now().isoformat(),
                            'is_stock_related': True,                        }
                        
                        articles.append(article_data)
                    
                    if len(articles) >= max_articles:
                        break
            
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return []
        except Exception as e:
            print(f"Error parsing news: {e}")
            return []

    def get_article_content(self, article_url):
        """
        Get full content of a specific article
        
        Args:
            article_url (str): URL of the article
            
        Returns:
            dict: Article content including title, body, author, etc.
        """
        try:
            response = self.session.get(article_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article details
            article_content = {
                'url': article_url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Title
            title_selectors = [
                'h1[data-test-locator="headline"]',
                'h1.caas-title-wrapper',
                'h1',
                '.caas-title-wrapper h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    article_content['title'] = title_elem.get_text(strip=True)
                    break
            
            # Article body
            body_selectors = [
                '.caas-body',
                '[data-test-locator="ArticleBody"]',
                '.article-body',
                '.caas-content-wrapper'
            ]
            
            for selector in body_selectors:
                body_elem = soup.select_one(selector)
                if body_elem:
                    # Get all paragraph text
                    paragraphs = body_elem.find_all('p')
                    article_content['body'] = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    break
            
            # Author
            author_selectors = [
                '[data-test-locator="AuthorName"]',
                '.caas-author-byline',
                '.author-name'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    article_content['author'] = author_elem.get_text(strip=True)
                    break
            
            # Publication date
            date_selectors = [
                'time[datetime]',
                '[data-test-locator="PublishDate"]',
                '.caas-attr-time-style'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    datetime_attr = date_elem.get('datetime')
                    if datetime_attr:
                        article_content['published_date'] = datetime_attr
                    else:
                        article_content['published_date'] = date_elem.get_text(strip=True)
                    break
            
            return article_content
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching article {article_url}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing article {article_url}: {e}")
            return None

    def save_to_json(self, articles, filename='yahoo_finance_stock_news.json'):
        """Save articles to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

    def save_to_csv(self, articles, filename='yahoo_finance_stock_news.csv'):
        """Save articles to CSV file"""
        try:
            if not articles:
                print("No articles to save")
                return
            
            fieldnames = ['title', 'url', 'summary', 'published_time', 'source', 'image_url',
              'is_stock_related', 'scraped_at']

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for article in articles:
                    # Only write fields that exist in fieldnames
                    row = {key: article.get(key, '') for key in fieldnames}
                    writer.writerow(row)
            
            print(f"Saved {len(articles)} stock articles to {filename}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    def get_breaking_stock_news(self, max_articles=10):
        """
        Get only the most recent breaking stock news
        
        Args:
            max_articles (int): Maximum number of articles to get
            
        Returns:
            list: List of breaking stock news articles
        """
        print("Fetching breaking stock news...")
        articles = self.get_stock_news_articles(max_articles=50, recent_only=True)
        
        # Sort by recency indicators and limit results
        breaking_news = []
        for article in articles:
            title_lower = article['title'].lower()
            summary_lower = article.get('summary', '').lower()
            
            # Prioritize articles with strong breaking news indicators
            breaking_indicators = ['breaking', 'just', 'alert', 'flash', 'live', 
                                 'minutes ago', 'hours ago', 'now', 'today']
            
            priority_score = 0
            for indicator in breaking_indicators:
                if indicator in title_lower or indicator in summary_lower:
                    priority_score += 1
            
            article['priority_score'] = priority_score
            breaking_news.append(article)
        
        # Sort by priority score and return top articles
        breaking_news.sort(key=lambda x: x['priority_score'], reverse=True)
        return breaking_news[:max_articles]

def main():
    """Main function to run the stock news scraper"""
    scraper = YahooFinanceStockNewsScraper()
    
    print("Scraping Yahoo Finance for latest stock news...")
    
    # Option 1: Get recent stock news (recommended)
    stock_articles = scraper.get_stock_news_articles(max_articles=15, recent_only=True)
    
    if stock_articles:
        print(f"Found {len(stock_articles)} recent stock articles")
        
        # Display articles
        print("\nLatest Stock News Articles:")
        for i, article in enumerate(stock_articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url'][:80]}...")
            if article.get('summary'):
                print(f"   Summary: {article['summary'][:150]}...")
            if article.get('published_time'):
                print(f"   Published: {article['published_time']}")

        # Save to files
        scraper.save_to_json(stock_articles, 'yahoo_finance_stock_news.json')
        scraper.save_to_csv(stock_articles, 'yahoo_finance_stock_news.csv')
        
        
        # Optional: Get full content for first article
        if stock_articles:
            print(f"\nGetting full content for first article...")
            first_article_content = scraper.get_article_content(stock_articles[0]['url'])
            if first_article_content:
                print(f"Full article title: {first_article_content.get('title', 'N/A')}")
                print(f"Author: {first_article_content.get('author', 'N/A')}")
                print(f"Published: {first_article_content.get('published_date', 'N/A')}")
                if 'body' in first_article_content:
                    print(f"Body preview: {first_article_content['body'][:300]}...")
        
    else:
        print("No recent stock articles found.")
        print("This could mean:")
        print("1. The website structure has changed")
        print("2. No recent stock news matches the filters")
        print("3. Network/connection issues")
        
        # Try without recent_only filter
        print("\nTrying without recent news filter...")
        all_stock_articles = scraper.get_stock_news_articles(max_articles=10, recent_only=False)
        if all_stock_articles:
            print(f"Found {len(all_stock_articles)} total stock articles (any time)")
            for i, article in enumerate(all_stock_articles[:3], 1):
                print(f"{i}. {article['title']}")

if __name__ == "__main__":
    main()
