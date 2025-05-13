
import json
import requests
from bs4 import BeautifulSoup
import re
import time
import os
from requests.exceptions import Timeout

# SOURCE CONFIGURATION
BASE_URL = "https://iz.ru/"
SEARCH_URL = "https://iz.ru/search?type=0&prd=0&from={page}&text={query}&date_from=&date_to=2022-02-24&sort=0"
COUNTRY = "Russia"
LANGUAGE = "rus"
SOURCE_NAME = "iz.ru"
TIMEOUT = 20  # timeout 

# User-Agent header to mimic a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}


def srape_iz_ru(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        total_text = ""

        # Title
        try:
            title_tag = soup.find('h1', itemprop="headline")
            title = title_tag.get_text(strip=True) if title_tag else None
        except Exception as e:
            print(f"Error getting title: {e}")
            title = None

        # Date
        try:
            time_tag = soup.find('time')
            if time_tag and time_tag.has_attr('datetime'):
                raw_date = time_tag['datetime']  # np. '2025-05-02T22:47:00Z'
                match = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw_date)
                if match:
                    year, month, day = match.groups()
                    formatted_date = f"{day}-{month}-{year}"
                else:
                    formatted_date = None
            else:
                formatted_date = None
        except Exception as e:
            print(f"Error getting date: {e}")
            formatted_date = None

        # Article body
        try:
            detail_divs = soup.find_all('div', itemprop='articleBody')
            for div in detail_divs:
                for element in div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    if not element.attrs:
                        element_text = element.get_text(strip=True)
                        if element.name.startswith('h'):
                            total_text += f"\n{element_text}\n"
                        else:
                            total_text += f"{element_text}\n"
        except Exception as e:
            print(f"Error getting article body: {e}")

        return title, formatted_date, total_text

    except Timeout:
        print(f"Timeout after {TIMEOUT} seconds for {url}")
        return None, None, None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None, None


def collect_links(query):
    links = []
    for page in range(0, 30, 10):
        url = SEARCH_URL.format(query=query, page=page)
        print(f"Scraping: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            articles = soup.find_all("div", class_="view-search__title")
            for div in articles:
                a = div.find("a")
                if a and a.get("href"):
                    href = a["href"]
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = BASE_URL.rstrip("/") + "/" + href.lstrip("/")
                    links.append(full_url)
        except Timeout:
            print(f"Timeout after {TIMEOUT} seconds for {url}")
            break
        except Exception as e:
            print(f"Error fetching links: {e}")
            break
    return links


def save_links_to_file(links, query, output_file):
     
    links_data = {
        "query": query,
        "links": list(links),
        "count": len(links)
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(links_data, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(links)} links to {output_file}")


def save_articles_to_file(articles, output_file):
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(articles)} articles to {output_file}")


def run_scraper(queries, output_file):
    all_articles = []
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        # Links scraping
        urls = collect_links(query)
        
        # Saving links to a temporary file
        links_file = f"links_{query.replace(' ', '_')}.json"
        save_links_to_file(urls, query, links_file)
        
        # Scraping articles
        query_articles = []
        for url in urls:
            print(f"Fetching article: {url}")
            start_time = time.time()
            title, date, body = srape_iz_ru(url)
            
            # Check for timeout
            if time.time() - start_time > TIMEOUT:
                print(f"Timeout after {TIMEOUT} seconds for {url}")
                continue
                
            if not any([title, date, body]):
                print(f"No data found for {url}")
                continue

            data = {
                "country": COUNTRY,
                "language": LANGUAGE,
                "source": SOURCE_NAME,
                "url": url,
                "query": query
            }

            if title:
                data["header"] = title
            if date:
                data["date"] = date
            if body:
                data["article_body"] = body

            query_articles.append(data)
        
        # Save articles to a temporary file
        articles_file = f"articles_{query.replace(' ', '_')}.json"
        save_articles_to_file(query_articles, articles_file)
        
        # Adding to the main list
        all_articles.extend(query_articles)
        
        # Save all articles to the main file
        save_articles_to_file(all_articles, output_file)
        
        # Cleanup temporary files
        try:
            os.remove(links_file)
            os.remove(articles_file)
        except Exception as e:
            print(f"Could not delete temporary files: {e}")

    print(f"\nEnd of scraping. All articles saved to {output_file} in data/raw/")


if __name__ == "__main__":
    queries = input("Enter search queries (comma-separated): ").split(",")
    queries = [q.strip() for q in queries if q.strip()]
    output_file = input("Enter output file name (e.g., 'iz_ru.json'): ").strip()

    if queries and output_file:
        run_scraper(queries, output_file)
    else:
        print("No queries or output file name provided.")
