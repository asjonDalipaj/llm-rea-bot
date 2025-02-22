#!/usr/bin/env python
import os
import asyncio
import argparse
from dotenv import load_dotenv
from pathlib import Path

from models import BrokerConfig
from utils import load_brokers_config, get_broker_config
from scraper import PropertyScraper

# Load environment variables
load_dotenv()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Property scraper using Crawl4AI')
    parser.add_argument('--area', type=str, help='Area to search (e.g., utrecht, amsterdam)')
    parser.add_argument('--broker', type=str, help='Broker name from configuration (specify "all" to scrape all brokers)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--max-price', type=int, default=2000, 
                        help='Maximum price for filtering (used by some brokers)')
    return parser.parse_args()

async def scrape_single_broker(broker, area, max_price, debug):
    """Scrape a single broker"""
    print(f"\n=== Scraping broker: {broker.name} ===")
    
    # Replace max_price placeholder if present in the URL
    if '{max_price}' in broker.url_template:
        broker.url_template = broker.url_template.replace('{max_price}', str(max_price))
    
    # Initialize and run scraper
    scraper = PropertyScraper(
        broker=broker,
        area=area,
        debug=debug
    )
    
    results = await scraper.scrape()
    
    print(f"\n--- {broker.name} Scraping Summary ---")
    print(f"Area: {area}")
    print(f"Total properties scraped: {len(results) if results else 0}")
    
    return results

async def main():
    """Main entry point"""
    args = parse_arguments()
    
    try:
        # Load configurations
        config_path = os.path.join("utilities", "brokers.json")
        brokers_config = load_brokers_config(config_path)
        
        # Get area and max price
        area = args.area or os.getenv('AREA', 'utrecht')
        max_price = args.max_price or int(os.getenv('MAX_PRICE', '2000'))
        
        # Check if we should scrape all brokers
        if args.broker and args.broker.lower() == 'all':
            print(f"Scraping ALL brokers for area: {area}")
            
            all_results = []
            
            # Loop through all brokers in the config
            for broker_config in brokers_config.get('brokers', []):
                broker = BrokerConfig(broker_config)
                try:
                    results = await scrape_single_broker(
                        broker=broker,
                        area=area,
                        max_price=max_price,
                        debug=args.debug
                    )
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    print(f"Error scraping broker {broker.name}: {str(e)}")
                    if args.debug:
                        import traceback
                        traceback.print_exc()
                    
                # Add a delay between brokers to prevent any rate limiting issues
                print("Waiting 30 seconds before scraping next broker...")
                await asyncio.sleep(30)
            
            print("\n=== Overall Scraping Summary ===")
            print(f"Total properties scraped across all brokers: {len(all_results)}")
            
        else:
            # Get specific broker
            broker_name = args.broker or os.getenv('BROKER_NAME')
            broker = get_broker_config(broker_name, brokers_config)
            
            if not broker:
                raise ValueError(f"Broker '{broker_name}' not found in configuration")
            
            print(f"Using broker: {broker.name}, area: {area}")
            
            # Scrape single broker
            await scrape_single_broker(
                broker=broker,
                area=area,
                max_price=max_price,
                debug=args.debug
            )
        
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())