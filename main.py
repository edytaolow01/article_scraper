from src.scrapers.aktualne_cz_scraper import run_scraper as run_cz_scraper
from src.scrapers.iz_ru_scraper import run_scraper as run_iz_ru_scraper
from src.scrapers.aktuality_sk_scraper import run_scraper as run_aktuality_sk_scraper
from src.scrapers.pravda_ua_scraper import run_scraper
from src.scrapers.blikk_hu_scraper import run_scraper as run_blikk_hu_scraper
from src.scrapers.onet_pl_scraper import run_scraper as run_onet_pl_scraper
from datetime import datetime
from src.utils.deduplication import remove_duplicates_from_file


# You can expand this dictionary with more countries and scrapers
SCRAPER_OPTIONS = {
    "Czech Republic": {
        "aktualne.cz": {"function": run_cz_scraper, "mode": "by_query"}
    },
    "Russia": {
        "iz.ru": {"function": run_iz_ru_scraper, "mode": "by_query"}
    },
    "Ukraine": {
        "pravda.ua": {"function": run_scraper, "mode": "by_date"}
    },
    "Slovakia": {
        "aktuality.sk": {"function": run_aktuality_sk_scraper, "mode": "by_query"}
    },
    "Hungary": {
        "blikk.hu": {"function": run_blikk_hu_scraper, "mode": "by_date"}
    },
    "Poland": {
        "onet.pl": {"function": run_onet_pl_scraper, "mode": "by_date"}
    }
}


def select_country():
    print("Select a country:")
    countries = list(SCRAPER_OPTIONS.keys())
    for i, country in enumerate(countries, 1):
        print(f"{i}. {country}")
    choice = input("Enter number: ")
    try:
        return countries[int(choice) - 1]
    except (IndexError, ValueError):
        print("Invalid selection.")
        return None


def select_source(country):
    print(f"Select a news source for {country}:")
    sources = list(SCRAPER_OPTIONS[country].keys())
    for i, source in enumerate(sources, 1):
        print(f"{i}. {source}")
    choice = input("Enter number: ")
    try:
        return sources[int(choice) - 1]
    except (IndexError, ValueError):
        print("Invalid selection.")
        return None


def get_queries():
    print("Enter your search queries separated by commas (e.g., atom, nuclear energy, uranium):")
    user_input = input("→ ").strip()
    return [q.strip() for q in user_input.split(",") if q.strip()]


def get_date(prompt):
    while True:
        date_input = input(f"{prompt} (YYYY-MM-DD): ")
        try:
            return datetime.strptime(date_input, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid format. Please use YYYY-MM-DD.")


def get_date_range():
    print("Enter the date range for scraping:")
    start_date = get_date("Start date")
    end_date = get_date("End date")
    return start_date, end_date


def main():
    print("Article Scraper has just started!")

    country = select_country()
    if not country:
        return

    source = select_source(country)
    if not source:
        return

    scraper_info = SCRAPER_OPTIONS[country][source]
    scraper_function = scraper_info["function"]
    scraper_mode = scraper_info["mode"]

    output_file = f"data/raw/{source.replace('.', '_')}_output.json"

    if scraper_mode == "by_date":
        start_date, end_date = get_date_range()
        scraper_function(start_date, end_date, output_file)
    else:
        queries = get_queries()
        if not queries:
            print("No queries provided.")
            return
        scraper_function(queries, output_file)

    print(f"Results saved to {output_file}")

    # Now ask if duplicates should be removed
    choice = input("Do you want to remove duplicate entries by 'url'? (y/n): ").strip().lower()
    if choice == "y":
        remove_duplicates_from_file(output_file)
        print("Done")


if __name__ == "__main__":
    main()
