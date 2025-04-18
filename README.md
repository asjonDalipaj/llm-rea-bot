# Property Scraper

A modular web scraper for property listings using Crawl4AI and LLM extraction.

## Structure

The application is organized into several modules:

- `crawlai.py` - Main script that ties everything together
- `models.py` - Data models for properties and broker configurations
- `utils.py` - Helper functions for file operations and HTML cleaning
- `llm_strategy.py` - LLM extraction strategy configuration
- `scraper.py` - Core scraping functionality
- `requirements.txt` - Package dependencies
- `setup.py` - Simple setup script

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   Or use the setup script:
   ```
   python setup.py
   ```

2. Create a `.env` file with your API keys:
   ```
   # API Keys
   GROQ_API_KEY=your_groq_key
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key

   # LLM Settings
   LLM_PROVIDER=groq/llama-3.3-70b-versatile
   LLM_TEMPERATURE=0.1
   LLM_MAX_TOKENS=2000

   # Scraping Settings
   BROKER_NAME=YourHouse
   AREA=utrecht
   OUTPUT_DIR=output

   # Debug Settings
   DEBUG=False
   ```

## Usage

Basic usage:
```
python crawlai.py --area utrecht --broker YourHouse
```

With debug mode:
```
python crawlai.py --area amsterdam --broker YourHouse --debug
```

Specify listing limit:
```
python crawlai.py --area utrecht --limit 10
```

## Usage

Basic usage:
```
python crawlai.py --area utrecht --broker YourHouse
```

With debug mode:
```
python crawlai.py --area amsterdam --broker YourHouse --debug
```

Specify listing limit:
```
python crawlai.py --area utrecht --limit 10
```

## How It Works

1. The script loads the broker configuration from `utilities/brokers.json`
2. It fetches the property listing page specified by the broker and area
3. It identifies individual property listings using the provided CSS selector
4. It processes each listing one by one using LLM extraction
5. It saves the extracted data to a JSON file in the output directory