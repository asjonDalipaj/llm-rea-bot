import os
import logging
import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LXMLWebScrapingStrategy
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from models import BrokerConfig, Property
from utils import save_properties_json, parse_rate_limit_error, clean_url
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
        
        # Make sure broker.domain is a full URL
        if self.broker.domain and not self.broker.domain.startswith(('http://', 'https://')):
            self.broker.domain = f"https://{self.broker.domain}"
        
        print(f"Using domain: {self.broker.domain}")
        
        self.output_dir = os.getenv('OUTPUT_DIR', 'output')
        
        # Configure browser settings
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=self.debug
        )
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def create_listings_extraction_schema(self):
        """Create a schema to extract the listings"""
        return {
            "name": "PropertyListings",
            "baseSelector": self.broker.listing_selector,
            "fields": [
                {
                    "name": "html_content",
                    "type": "html"  # Extract the full HTML for each listing
                },
                {
                    "name": "listing_url",
                    "selector": "a",
                    "type": "attribute",
                    "attribute": "href",
                    "default": ""
                }
            ],
            "overlap": 0.5  # Apply 50% overlap between listings
        }

    async def process_listing(self, crawler, listing_html: str, listing_url: str = "") -> Optional[Dict]:
        """Process a single listing with LLM"""
        try:
            # Create LLM strategy with broker domain
            llm_strategy = get_llm_strategy(self.broker.domain, listing_html)
            
            # Create crawler configuration
            config = CrawlerRunConfig(
                extraction_strategy=llm_strategy,
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=0,
                excluded_tags=["script", "style", "noscript", "source", "img"],
                remove_overlay_elements=True
            )
            
            # Handle rate limiting
            max_retries = 3
            current_retry = 0
            
            while current_retry < max_retries:
                try:
                    # Use raw_html instead of temporary file
                    result = await crawler.arun(
                        raw_html=listing_html,
                        url=self.broker.domain,  # Used for resolving relative URLs
                        config=config
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    if "rate limit" in error_str or "ratelimit" in error_str:
                        wait_time = parse_rate_limit_error(error_str)
                        
                        current_retry += 1
                        if current_retry < max_retries:
                            print(f"Rate limit reached. Waiting {wait_time:.1f} seconds before retry {current_retry}/{max_retries}...")
                            await asyncio.sleep(wait_time)
                        else:
                            print("Max retries reached due to rate limits.")
                            raise
                    else:
                        raise
            
            # Process the result
            if result.success and result.extracted_content:
                if isinstance(result.extracted_content, str):
                    try:
                        property_data = json.loads(result.extracted_content)
                        
                        # Handle case where LLM returns a list instead of a single object
                        if isinstance(property_data, list):
                            if property_data:
                                property_data = property_data[0]  # Take first item
                            else:
                                print("LLM returned an empty list")
                                return {"error": True, "message": "LLM returned empty list"}
                        
                        # Check if the property already has a URL
                        if listing_url:
                            property_data['url'] = self.broker.domain + listing_url
                            print(f"Assigned new URL from listing_url: {property_data['url']}")
                            cleaned_url = clean_url(property_data['url'])
                            property_data['url'] = cleaned_url
                            print(f"Cleaned - {property_data['url']}")
                        
                        # Add error field for tracking
                        property_data['error'] = False
                        return property_data
                    except json.JSONDecodeError:
                        print(f"Failed to parse result as JSON: {result.extracted_content[:100]}...")
                        # Save failed extraction for debugging
                        debug_file = os.path.join(self.output_dir, f"failed_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(result.extracted_content)
                        print(f"Saved failed extraction for debugging to: {debug_file}")
                        return {"error": True, "message": "JSON parsing error"}
                else:
                    return result.extracted_content
            
            return {"error": True, "message": "Extraction failed"}
        except Exception as e:
            print(f"Error processing listing: {str(e)}")
            return {"error": True, "message": str(e)}
    
    async def scrape(self, limit: int = 1) -> List[Dict]:
        """Scrape property listings"""
        print("\n--- Starting scraping process ---")
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            start_time = datetime.now()
            
            try:
                # Step 1: Use schema-based extraction to get all listings
                listings_schema = self.create_listings_extraction_schema()
                listings_strategy = JsonCssExtractionStrategy(listings_schema)
                
                # Configure the main page crawl
                main_config = CrawlerRunConfig(
                    extraction_strategy=listings_strategy,
                    cache_mode=CacheMode.BYPASS,
                    word_count_threshold=0,
                    excluded_tags=["script", "style", "noscript"],
                    remove_overlay_elements=True,
                    scraping_strategy=LXMLWebScrapingStrategy()  # Use faster LXML strategy
                )
                
                # Fetch the main listings page with schema-based extraction
                try:
                    initial_result = await crawler.arun(
                        url=self.url,
                        config=main_config
                    )
                except Exception as e:
                    print(f"Error during initial crawl: {str(e)}")
                    return []

                if not initial_result.success:
                    print(f"Error fetching page: {initial_result.error_message}")
                    return []

                # Parse the extracted content (listings)
                if not initial_result.extracted_content:
                    print("No listings extracted")
                    return []
                
                listings_data = json.loads(initial_result.extracted_content)
                print(f"\nFound {len(listings_data)} property listings using selector: {self.broker.listing_selector}")
                
                if not listings_data:
                    print("No listings found! Check the selector or page structure.")
                    # Save debug info
                    debug_file = os.path.join(self.output_dir, f"debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(initial_result.html)
                    print(f"Saved full HTML for debugging to: {debug_file}")
                    return []
                
                # Step 2: Process each listing individually
                print("\nProcessing individual listings...")
                properties = []
                listing_count = min(len(listings_data), limit)
                
                for i, listing in enumerate(listings_data[:listing_count]):
                    print(f"\nProcessing listing {i+1}/{listing_count}")
                    
                    # Add delay between requests to avoid rate limits
                    if i > 0:
                        delay = 20  # 20 seconds between requests
                        print(f"Waiting {delay} seconds before processing next listing...")
                        await asyncio.sleep(delay)
                    
                    # Get the HTML content and URL of this listing
                    listing_html = listing.get("html_content", "")
                    listing_url = listing.get("listing_url", "")
                    
                    if not listing_html:
                        print("Empty listing HTML, skipping")
                        continue
                    
                    property_data = await self.process_listing(crawler, listing_html, listing_url)
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