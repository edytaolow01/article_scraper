# Article Scraper

Article Scraper is a web scraping tool designed to extract news articles from various online sources across six countries: Poland, Ukraine, Czech Republic, Slovakia, Hungary, and Russia (one news outlet per country).

The scraper supports both keyword-based and archive-based extraction, depending on the structure of each website. The system is currently verified to work as of May 13, 2025, but future changes to the structure of the target websites may require updates to the scraper.

## Key Features

- Scrapes news articles from six predefined country-specific sources.
- Allows extension: simply add your custom scraper logic to src/scrapers/ and modify main.py accordingly.
- Supports both keyword and date-based article collection.
- Adjustable scraping depth via the collect_link function.

  
## Important Notes

- Website Changes: The scraper may stop working if the target websites update their HTML structure.
- VPN Requirements: Some sources (e.g., iz.ru) may require a VPN depending on your geographical location.
- Customization: You can fine-tune the number of pages scraped per query by modifying the collect_link function in your code.

## Prerequisites

- Python 3.12.7 version (other may do not work!)
- Conda (optioally Miniconda or Anaconda)


## Installation

**1. Clone the repository**:
   ```bash
   git clone https://github.com/your_username/article_scraper.git
   cd article_sraper
```

**a) if creating conda environment:**

  Create Conda environment:
  
  ```bash
  conda env create -f environment.yml
```

Activate Conda environment:

  ```bash
  conda activate article_scraper
```

**b) otherwise:**

```bash
pip install -r requirements.txt
```

 ## 2. Mind to start main.py from artcle_scraper directory

  ```bash
  python main.py
```
