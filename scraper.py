import os
import asyncio
import json
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from models import BrokerConfig
from utils import clean_html_fragment, save_debug_html, save_properties_json, parse_rate_limit_error
from llm_strategy import get_llm_strategy

class PropertyScraper:
    def __init__(self, broker: BrokerConfig, area: str, debug: bool = False):
        print("Initializing scraper...")
        self.broker = broker
        self.area = area
        self.debug = debug
        
        # Generate the full URL
        self.url = self.broker.get_url(area)
        print(f"Target URL: {self.url}")
        
        self.output_dir = os.getenv('OUTPUT_DIR', 'output')
        
        # Configure browser settings
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=self.debug
        )
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    async def process_listing(self, crawler, html_fragment: str) -> Optional[dict]:
        """Process a single listing with LLM"""
        try:
            # Simplify HTML to reduce size
            html_fragment = clean_html_fragment(html_fragment)
            
            # Create a temporary HTML file for the fragment
            temp_file = os.path.join(self.output_dir, f"temp_fragment_{datetime.now().timestamp()}.html")
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_fragment)
            
            print(f"Processing listing fragment ({len(html_fragment)} chars)")
            
            # Create specific extraction for this fragment
            llm_strategy = get_llm_strategy(html_fragment)
            
            # Configure fragment crawl
            crawl_config = CrawlerRunConfig(
                extraction_strategy=llm_strategy,
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=0,
                excluded_tags=[]
            )
            
            # Process the fragment using a file:// URL
            file_url = f"file://{os.path.abspath(temp_file)}"
            
            # Try with rate limit handling
            max_retries = 3
            current_retry = 0
            
            while current_retry < max_retries:
                try:
                    result = await crawler.arun(
                        url=file_url,
                        config=crawl_config
                    )
                    break  # Success, exit the retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    if "rate limit" in error_str or "ratelimit" in error_str:
                        # Parse the wait time if available
                        wait_time = parse_rate_limit_error(error_str)
                        
                        current_retry += 1
                        if current_retry < max_retries:
                            print(f"Rate limit reached. Waiting {wait_time:.1f} seconds before retry {current_retry}/{max_retries}...")
                            await asyncio.sleep(wait_time)
                        else:
                            print("Max retries reached due to rate limits.")
                            raise
                    else:
                        # Not a rate limit error, re-raise
                        raise
            
            # Clean up the temporary file
            os.remove(temp_file)
            
            if result.success and result.extracted_content:
                if isinstance(result.extracted_content, str):
                    try:
                        property_data = json.loads(result.extracted_content)
                        return property_data
                    except json.JSONDecodeError:
                        print(f"Failed to parse fragment result as JSON: {result.extracted_content[:100]}...")
                else:
                    return result.extracted_content
            
            return None
        except Exception as e:
            print(f"Error processing listing: {str(e)}")
            return None

    async def scrape(self, limit: int = 5) -> List[dict]:
        """Scrape property listings"""
        print("\n--- Starting scraping process ---")
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            start_time = datetime.now()
            
            try:
                # First, just get the HTML without LLM extraction
                print(f"\nFetching HTML from URL: {self.url}")
                basic_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    word_count_threshold=0,
                    excluded_tags=[]
                )
                
                initial_result = await crawler.arun(
                    url=self.url,
                    config=basic_config
                )

                if not initial_result.success:
                    print(f"Error fetching page: {initial_result.error_message}")
                    return []

                print(f"\nReceived HTML length: {len(initial_result.html)} characters")
                
                # Parse HTML to find property listings
                soup = BeautifulSoup(initial_result.html, 'html.parser')
                listings = soup.select(self.broker.listing_selector)
                print(f"\nFound {len(listings)} property listings using selector: {self.broker.listing_selector}")
                
                if not listings:
                    print("No listings found! Check the selector or page structure.")
                    # Save the full HTML for inspection
                    debug_file = save_debug_html(initial_result.html, self.output_dir)
                    print(f"Saved full HTML for debugging to: {debug_file}")
                    return []
                
                # Process each listing individually
                print("\nProcessing individual listings...")
                properties = []
                listing_count = min(len(listings), limit)
                
                for i, listing in enumerate(listings[:listing_count]):
                    print(f"\nProcessing listing {i+1}/{listing_count}")
                    
                    # Add delay between requests to avoid rate limits
                    if i > 0:
                        delay = 20  # 20 seconds between requests
                        print(f"Waiting {delay} seconds before processing next listing...")
                        await asyncio.sleep(delay)
                    
                    property_data = await self.process_listing(crawler, str(listing))
                    if property_data:
                        properties.append(property_data)
                        print(f"✓ Successfully extracted property data")
                    else:
                        print(f"✗ Failed to extract property data")
                
                print(f"\nSuccessfully processed {len(properties)}/{listing_count} properties")
                
                # Save results
                if properties:
                    filename = save_properties_json(
                        properties=properties,
                        broker_name=self.broker.name,
                        area=self.area,
                        output_dir=self.output_dir
                    )
                    print(f"Results saved to: {filename}")
                
                return properties

            except Exception as e:
                print(f"\nError during scraping: {str(e)}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
                return []
            finally:
                duration = (datetime.now() - start_time).total_seconds()
                print(f"\nTotal time taken: {duration:.2f} seconds")