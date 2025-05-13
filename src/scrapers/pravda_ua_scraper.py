import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os

BASE_URL = "https://www.pravda.com.ua/"
COUNTRY = "Ukraine"
LANGUAGE = "ua"
SOURCE_NAME = "pravda_ua"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_article(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)  
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        total_text = ""

        # Choose domain
        if "life.pravda.com.ua" in url:
            return scrape_life_pravda(soup)
        elif "epravda.com.ua" in url:
            return scrape_epravda(soup)
        elif "eurointegration.com.ua" in url:
            return scrape_eurointegration(soup)
        else:  # default
            return scrape_main_pravda(soup)

    except requests.exceptions.Timeout:
        print(f"Timeout while scraping article: {url}")
        return None, None, None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None, None

def scrape_main_pravda(soup):
    # Scraping for the main pravda.com.ua domain
    total_text = ""
    
    # Title
    try:
        title_tag = soup.find('h1', class_='post_title')
        title = title_tag.get_text(strip=True) if title_tag else None
    except Exception as e:
        print(f"Error getting title: {e}")
        title = None

    # Article body
    try:
        article_div = soup.find('div', class_='post_text')
        if article_div:
            # Get all elements in order
            for element in article_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                element_text = element.get_text(strip=True)
                if element_text:
                    # Add extra newlines for headers
                    if element.name.startswith('h'):
                        total_text += f"\n{element_text}\n"
                    else:
                        total_text += f"{element_text}\n"
    except Exception as e:
        print(f"Error getting article body: {e}")

    return title, None, total_text

def scrape_life_pravda(soup):
    
    total_text = ""
    
    # Title
    try:
        title_tag = soup.find('h1', class_='post_article_title')
        title = title_tag.get_text(strip=True) if title_tag else None
    except Exception as e:
        print(f"Error getting title: {e}")
        title = None

    # Article body
    try:
        article_div = soup.find('div', class_='post_article_text')
        if article_div:
            for element in article_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                element_text = element.get_text(strip=True)
                if element_text:
                    if element.name.startswith('h'):
                        total_text += f"\n{element_text}\n"
                    else:
                        total_text += f"{element_text}\n"
    except Exception as e:
        print(f"Error getting article body: {e}")

    return title, None, total_text

def scrape_epravda(soup):
     
    total_text = ""
    
    # Title
    try:
        title_tag = soup.find('h1', class_='post_article_title')
        title = title_tag.get_text(strip=True) if title_tag else None
    except Exception as e:
        print(f"Error getting title: {e}")
        title = None

    # Article body
    try:
        article_div = soup.find('div', class_='post_article_body')
        if article_div:
            for element in article_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                element_text = element.get_text(strip=True)
                if element_text:
                    if element.name.startswith('h'):
                        total_text += f"\n{element_text}\n"
                    else:
                        total_text += f"{element_text}\n"
    except Exception as e:
        print(f"Error getting article body: {e}")

    return title, None, total_text

def scrape_eurointegration(soup):
    
    total_text = ""
    
    # Title
    try:
        title_tag = soup.find('h1', class_='post__title')
        title = title_tag.get_text(strip=True) if title_tag else None
    except Exception as e:
        print(f"Error getting title: {e}")
        title = None

    # Article body
    try:
        article_div = soup.find('div', class_='post__text')
        if article_div:
            for element in article_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                element_text = element.get_text(strip=True)
                if element_text:
                    if element.name.startswith('h'):
                        total_text += f"\n{element_text}\n"
                    else:
                        total_text += f"{element_text}\n"
    except Exception as e:
        print(f"Error getting article body: {e}")

    return title, None, total_text

def _format_date_for_url(date):
    return date.strftime("%d%m%Y")

def _format_date_for_display(date):
    return date.strftime("%d-%m-%Y")

def collect_links_by_date(date):
    links = []
    date_str = _format_date_for_url(date)
    display_date = _format_date_for_display(date)
    url = f"{BASE_URL}archives/date_{date_str}/"
    print(f"\nScraping archive for {display_date}:")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)  # 20 sekund timeout
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        articles = soup.find_all("div", class_="article article_list")
        print(f"Found {len(articles)} articles for {display_date}")
        
        for a in articles:
            link_tag = a.find("a")
            if link_tag and link_tag.has_attr("href"):
                href = link_tag["href"]
                full_url = href if href.startswith("http") else BASE_URL + href
                links.append((full_url, display_date))
                print(f"  • {display_date} - {full_url}")
    except requests.exceptions.Timeout:
        print(f"Timeout while collecting links for {display_date}")
    except Exception as e:
        print(f"Error fetching links for {display_date}: {e}")
    
    print(f"\n Total links collected for {display_date}: {len(links)}")
    return links

def save_links_to_file(links, date, output_file):
    
    links_data = {
        "date": date.strftime("%d-%m-%Y"),
        "links": [{"url": url, "archive_date": date} for url, date in links],
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
        
        # Links scraping for the current date
        links = collect_links_by_date(current_date)
        
        # Saving links to a temporary file
        links_file = f"links_{_format_date_for_url(current_date)}.json"
        save_links_to_file(links, current_date, links_file)
        
        # Articles scraping for the current date
        day_articles = []
        for url, archive_date in links:
            print(f"Fetching article from {archive_date}:")
            print(f"URL: {url}")
            title, date, body = scrape_article(url)
            
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
        
        # Save articles to a temporary file
        articles_file = f"articles_{_format_date_for_url(current_date)}.json"
        save_articles_to_file(day_articles, articles_file)
        
        # Append today's articles to the main list
        all_articles.extend(day_articles)
        
        # Save all articles to the main file
        save_articles_to_file(all_articles, output_file)
        
        # Clean up temporary files
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
    output_file = input("Enter output file name (e.g., 'pravda_ua.json'): ").strip()

    if start_date and end_date and output_file:
        start = datetime.strptime(start_date, "%d%m%Y").date()
        end = datetime.strptime(end_date, "%d%m%Y").date()
        run_scraper(start, end, output_file)
    else:
        print("No dates or output file name provided.")
