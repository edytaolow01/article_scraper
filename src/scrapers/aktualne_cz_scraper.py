
import json
import requests
from bs4 import BeautifulSoup
import re
import os

BASE_URL = "https://www.aktualne.cz"
COUNTRY = "Czech Republic"
LANGUAGE = "cs"
SOURCE_NAME = "Aktualne.cz"

def scrape_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        total_text = ""

        # Title
        try:
            title_tag = soup.find('h1', class_='article-title')
            title = title_tag.get_text(strip=True) if title_tag else None
        except Exception as e:
            print(f"Error getting title: {e}")
            title = None

        # Date
        try:
            date_div = soup.find('div', class_='author__date')
            if date_div:
                date_text = date_div.get_text(strip=True)
                date_only = re.sub(r'\s+\d{1,2}:\d{2}', '', date_text)
                formatted_date = date_only.replace('.', '-').replace(' ', '')
            else:
                formatted_date = None
        except Exception as e:
            print(f"Error getting date: {e}")
            formatted_date = None

        # Intro
        try:
            intro = soup.find('div', class_='article__perex')
            if intro:
                total_text += intro.get_text(strip=True) + " "
        except Exception as e:
            print(f"Error getting intro: {e}")

        # Article body
        try:
            detail_divs = soup.find_all('div', class_='article__content')
            for div in detail_divs:
                for p in div.find_all('p'):
                    if not p.attrs:
                        total_text += p.get_text(strip=True) + " "
        except Exception as e:
            print(f"Error getting article body: {e}")

        return title, formatted_date, total_text

    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None, None

def collect_links(query):
    hrefs = set()
    search_url_template = f"https://www.aktualne.cz/hledani/?offset={{offset}}&query={query}"

    for i in range(1): # Adjust the range for more pages
        offset = i * 20
        url = search_url_template.format(offset=offset)
        print(f"Scraping: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            divs = soup.find_all("div", class_="timeline")

            if not divs:
                print(f"No more results for query '{query}'. Going to next query.")
                break

            for div in divs:
                links = div.find_all("a", href=True)
                for link in links:
                    href = link.get("href")
                    if href:
                        print(f"  • {href}")
                        hrefs.add(href)

        except Exception as e:
            print(f"Error with {url}: {e}")
            break

    print(f"Found {len(hrefs)} links for query '{query}'")
    return hrefs

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
        print(f"\n🎯 Query: '{query}'")
        
        # Collecting links
        urls = collect_links(query)
        
        # Saving links to a temporary file
        links_file = f"links_{query.replace(' ', '_')}.json"
        save_links_to_file(urls, query, links_file)
        
        # Scraping articles
        query_articles = []
        for url in urls:
            print(f"Fetching article: {url}")
            title, date, body = scrape_article(url)

            data = {
                "country": COUNTRY,
                "language": LANGUAGE,
                "source": SOURCE_NAME,
                "url": url,
                "query": query
            }

            if title:
                data["title"] = title
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
        
        # Save all articles to the final output file
        save_articles_to_file(all_articles, output_file)
        
        # Cleanup temporary files
        try:
            os.remove(links_file)
            os.remove(articles_file)
        except Exception as e:
            print(f"Error deleting temporary files: {e}")

    print(f"End of scraping. All articles saved to {output_file} in data/raw/")

if __name__ == "__main__":
    queries = input("Enter search queries (comma-separated): ").split(",")
    queries = [q.strip() for q in queries if q.strip()]
    output_file = input("Enter output file name (e.g., 'aktualne_cz.json'): ").strip()

    if queries and output_file:
        run_scraper(queries, output_file)
    else:
        print("No queries or output file name provided.")
