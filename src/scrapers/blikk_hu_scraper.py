import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os

BASE_URL = "https://www.blikk.hu/"
COUNTRY = "Hungary"
LANGUAGE = "hu"
SOURCE_NAME = "blikk_hu"


# User-Agent header to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_article(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        total_text = ""
        
        # Title
        try:
            title_section = soup.find('section', class_='title')
            if title_section:
                title_tag = title_section.find('h1')
                title = title_tag.get_text(strip=True) if title_tag else None
            else:
                title = None
        except Exception as e:
            print(f"Error getting title: {e}")
            title = None

        # Article body
        try:
            article = soup.find('article', class_='space-y-6')
            if article:
                # Get all paragraphs and headers from main article
                for element in article.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                    element_text = element.get_text(strip=True)
                    if element_text:
                        if element.name.startswith('h'):
                            total_text += f"\n{element_text}\n"
                        else:
                            total_text += f"{element_text}\n"
                
                # Get content from promotion frame if exists
                promotion_frame = article.find('div', class_='promotion_frame')
                if promotion_frame:
                    for element in promotion_frame.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                        element_text = element.get_text(strip=True)
                        if element_text:
                            if element.name.startswith('h'):
                                total_text += f"\n{element_text}\n"
                            else:
                                total_text += f"{element_text}\n"
        except Exception as e:
            print(f"Error getting article body: {e}")

        return title, None, total_text

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
    page_num = 0
    
    while True:
        url = f"{BASE_URL}archivum/online?date={date_str}&page={page_num}"
        print(f"\nScraping archive for {display_date}, page {page_num}:")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find article list 
            article_list = soup.find("ul", class_="flex flex-col gap-4")
            if not article_list:
                print(f"No more articles found on page {page_num}")
                break
                
            # Find every link in "li" elements
            articles = article_list.find_all("li", class_="pb-3 md:pb-4 border-b border-b-gray-400")
            print(f"Found {len(articles)} articles on page {page_num}")
            
            for article in articles:
                link = article.find("a")
                if link and link.has_attr("href"):
                    href = link["href"]
                    links.append((href, display_date))
                    print(f"  • {display_date} - {href}")
            
            page_num += 1
            
        except Exception as e:
            print(f"Error fetching links for {display_date}, page {page_num}: {e}")
            break
    
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
    
    print(f" Saved {len(links)} links to {output_file}")

def save_articles_to_file(articles, output_file):
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    
    print(f" Saved {len(articles)} articles to {output_file}")

def run_scraper(start_date, end_date, output_file):
    all_articles = []
    
    current_date = start_date
    while current_date <= end_date:
        print(f"\nProcessing date: {_format_date_for_display(current_date)}")
        
        # Collecting links for the current date
        links = collect_links_by_date(current_date)
        
        # Saving links to a temporary file
        links_file = f"links_{_format_date_for_url(current_date)}.json"
        save_links_to_file(links, current_date, links_file)
        
        # Scraping articles for the current date
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
        
        # Adding to the main list
        all_articles.extend(day_articles)
        
        # Save all articles to the main file
        save_articles_to_file(all_articles, output_file)
        
        # Delete temporary files
        try:
            os.remove(links_file)
            os.remove(articles_file)
        except Exception as e:
            print(f"Could not delete temporary files: {e}")
        
        current_date += timedelta(days=1)
        
    print(f"\End of scraping. All articles saved to {output_file} in data/raw/")

def get_date(prompt):
    while True:
        date_input = input(f"{prompt} (YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(date_input, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid format. Please use YYYY-MM-DD.")

if __name__ == "__main__":

    # Saving dates with validation
    start_date = get_date("Enter start date")
    end_date = get_date("Enter end date")
    output_file = input("Enter output file name (e.g., 'blikk_hu.json'): ").strip()

    if output_file:  # Check if the output file name is not empty
        run_scraper(start_date, end_date, output_file)
    else:
        print(" Output file name cannot be empty!")
