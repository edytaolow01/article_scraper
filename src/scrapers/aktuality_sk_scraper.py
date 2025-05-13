import json
import requests
from bs4 import BeautifulSoup
import re
import time
import os
from requests.exceptions import Timeout

# Configuration for running this file independently
BASE_URL = "https://www.aktuality.sk"
SEARCH_URL = "https://www.aktuality.sk/vyhladavanie/{page}/?search%5Btext%5D={query}&search%5Bzdroj%5D=spravy"
COUNTRY = "Slovakia"
LANGUAGE = "sk"
SOURCE_NAME = "aktuality.sk"
TIMEOUT = 20  

# User-Agent header to mimic a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}


def scrape_aktuality_sk(url):
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

        # Perex
        try:
            perex_div = soup.find('div', id='perex-id')
            if perex_div:
                perex_span = perex_div.find('span', itemprop='description')
                if perex_span:
                    perex = perex_span.get_text(strip=True)
                    total_text += f"{perex}\n\n"
        except Exception as e:
            print(f"Error getting perex: {e}")

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

        return title, None, total_text

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
    for page in range(1,4):
        url = SEARCH_URL.format(query=query, page=page)
        print(f"Scraping: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            articles = soup.find_all("li", class_="article-item")
            
            if not articles:
                print(f"No more results on page {page} for query '{query}'. Going to next query.")
                break
                
            for article in articles:
                # Scrapping link
                link_tag = article.find("a", class_="article-image")
                if not link_tag or not link_tag.get("href"):
                    continue
                    
                href = link_tag["href"]
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = BASE_URL + href
                
                # Scrapping date
                date_span = article.find("span", class_="article-time")
                if date_span:
                    date_text = date_span.get_text(strip=True)
                    # Format date to YYYY-MM-DD
                    try:
                        date_parts = date_text.split()[0].split('.')
                        if len(date_parts) == 3:
                            formatted_date = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
                        else:
                            formatted_date = None
                    except Exception as e:
                        print(f"Error formatting date: {e}")
                        formatted_date = None
                else:
                    formatted_date = None
                
                links.append({
                    "url": full_url,
                    "date": formatted_date
                })
                print(f"  • {full_url} ({formatted_date if formatted_date else 'no date'})")
                    
        except Timeout:
            print(f"Timeout after {TIMEOUT} seconds for {url}")
            break
        except Exception as e:
            print(f"Error fetching links: {e}")
            break
            
    print(f"\nTotal links collected: {len(links)}")
    return links


def save_links_to_file(links, query, output_file):
    
    links_data = {
        "query": query,
        "links": links,
        "count": len(links)
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(links_data, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(links)} links to {output_file}")


def save_articles_to_file(articles, output_file):
    """Zapisuje artykuły do pliku JSON"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(articles)} articles to {output_file}")


def run_scraper(queries, output_file):
    all_articles = []
    
    for query in queries:
        print(f"\n🎯 Query: '{query}'")
        
        # Sraping links
        urls_data = collect_links(query)
        
        # Saving links to a temporary file
        links_file = f"links_{query.replace(' ', '_')}.json"
        save_links_to_file(urls_data, query, links_file)
        
        # Scraping articles
        query_articles = []
        for url_data in urls_data:
            url = url_data["url"]
            print(f"Fetching article: {url}")
            start_time = time.time()
            title, _, body = scrape_aktuality_sk(url)
            
            # Check if the request timed out
            if time.time() - start_time > TIMEOUT:
                print(f"Timeout after {TIMEOUT} seconds for {url}, skipping this article")
                continue
                
            if not any([title, body]):
                print(f"No title or body found for {url}, skipping this article")
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
            if url_data["date"]:
                data["date"] = url_data["date"]
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
        
        # Remove temporary files
        try:
            os.remove(links_file)
            os.remove(articles_file)
        except Exception as e:
            print(f"Could not delete temporary files: {e}")

    print(f"\nEnd of scraping. All articles saved to {output_file} in data/raw/")


if __name__ == "__main__":
    queries = input("Enter search queries (comma-separated): ").split(",")
    queries = [q.strip() for q in queries if q.strip()]
    output_file = input("Enter output file name (e.g., 'aktuality_sk.json'): ").strip()

    if queries and output_file:
        run_scraper(queries, output_file)
    else:
        print("No queries or output file name provided.")
