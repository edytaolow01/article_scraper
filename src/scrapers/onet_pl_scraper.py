import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os

BASE_URL = "https://wiadomosci.onet.pl/"
COUNTRY = "Poland"
LANGUAGE = "pl"
SOURCE_NAME = "onet_pl"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_article(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)  
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        total_text = ""
        
        # Title
        try:
            title = soup.find("h1", {"class": "mainTitle"})
            title_text = title.get_text(strip=True) if title else None
        except Exception as e:
            print(f"Error getting title: {e}")
            title_text = None

        # Subtitle
        try:
            subtitle = soup.find("div", {"id": "lead"})
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""
            if subtitle_text:
                total_text += f"{subtitle_text}\n\n"
        except Exception as e:
            print(f"Error getting subtitle: {e}")

        # Article body
        try:
            article_body = soup.find("div", {"id": "detail"})
            if article_body:
                paragraphs = article_body.find_all("p", {"class": "hyphenate narrow"})
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text:
                        total_text += f"{text}\n"
        except Exception as e:
            print(f"Error getting article body: {e}")

        return title_text, None, total_text

    except requests.exceptions.Timeout:
        print(f"Timeout while scraping article: {url}")
        return None, None, None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None, None

def _format_date_for_url(date):
    return date.strftime("%Y-%m-%d")

def _format_date_for_display(date):
    return date.strftime("%d-%m-%Y")

def collect_links_by_date(date):
    links = []
    date_str = _format_date_for_url(date)
    display_date = _format_date_for_display(date)
    
    url = f"{BASE_URL}archiwum/{date_str}"
    print(f"\n🔍 Scraping archive for {display_date}:")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)  
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find all links to articles
        articles = soup.find_all("a", class_="itemTitle")
        print(f"Found {len(articles)} articles for {display_date}")
        
        for article in articles:
            if article.has_attr("href"):
                href = article["href"]
                full_url = href if href.startswith("http") else BASE_URL + href
                links.append((full_url, display_date))
                print(f"  • {display_date} - {full_url}")
                
    except requests.exceptions.Timeout:
        print(f"Timeout while collecting links for {display_date}")
    except Exception as e:
        print(f"Error fetching links for {display_date}: {e}")
    
    print(f"\nTotal links collected for {display_date}: {len(links)}")
    return links

def save_links_to_file(links, date, output_file):
    
    links_data = {
        "date": date.strftime("%d-%m-%Y"),
        "links": [{"url": url, "date": date} for url, date in links],
        "count": len(links)
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(links_data, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(links)} links to {output_file}")

def save_articles_to_file(articles, output_file):
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(articles)} articles to {output_file}")

def run_scraper(start_date, end_date, output_file):
    all_articles = []
    
    current_date = start_date
    while current_date <= end_date:
        print(f"\nProcessing date: {_format_date_for_display(current_date)}")
        
        # Link scraping for the current date
        links = collect_links_by_date(current_date)
        
        # Saving links to a temporary file
        links_file = f"links_{_format_date_for_url(current_date)}.json"
        save_links_to_file(links, current_date, links_file)
        
        # Scraping articles
        day_articles = []
        for url, archive_date in links:
            print(f"Fetching article from {archive_date}:")
            print(f"URL: {url}")
            title, date, body = scrape_article(url)
            print("Title", title)
            print("Body", body)
            
            data = {
                "country": COUNTRY,
                "language": LANGUAGE,
                "source": SOURCE_NAME,
                "url": url,
                "date": archive_date
            }
            
            if title:
                data["title"] = title
            if date:
                data["date"] = date
            if body:
                data["article_body"] = body
                
            day_articles.append(data)
        
        # Saving articles to a temporary file
        articles_file = f"articles_{_format_date_for_url(current_date)}.json"
        save_articles_to_file(day_articles, articles_file)
        
        # Appending articles to the main list
        all_articles.extend(day_articles)
        
        # Saving all articles to the main file
        save_articles_to_file(all_articles, output_file)
        
        # Cleaning up temporary files
        try:
            os.remove(links_file)
            os.remove(articles_file)
        except Exception as e:
            print(f"Error deleting temporary files: {e}")
        
        current_date += timedelta(days=1)
        
    print(f"\nEnd of scraping. All articles saved to {output_file} in data/raw/")

if __name__ == "__main__":
    start_date = input("Enter start date (DDMMYYYY): ").strip()
    end_date = input("Enter end date (DDMMYYYY): ").strip()
    output_file = input("Enter output file name (e.g., 'onet_pl.json'): ").strip()

    if start_date and end_date and output_file:
        start = datetime.strptime(start_date, "%d%m%Y").date()
        end = datetime.strptime(end_date, "%d%m%Y").date()
        run_scraper(start, end, output_file)
    else:
        print("No dates or output file name provided.")
