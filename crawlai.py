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
    parser.add_argument('--broker', type=str, help='Broker name from configuration')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--limit', type=int, default=5, help='Maximum number of listings to process')
    return parser.parse_args()

async def main():
    """Main entry point"""
    args = parse_arguments()
    
    try:
        # Load configurations
        config_path = os.path.join("utilities", "brokers.json")
        brokers_config = load_brokers_config(config_path)
        
        # Get broker config
        broker_name = args.broker or os.getenv('BROKER_NAME')
        broker = get_broker_config(broker_name, brokers_config)
        
        if not broker:
            raise ValueError(f"Broker '{broker_name}' not found in configuration")
        
        # Get area
        area = args.area or os.getenv('AREA', 'utrecht')
        
        print(f"Using broker: {broker.name}, area: {area}")
        
        # Initialize and run scraper
        scraper = PropertyScraper(
            broker=broker,
            area=area,
            debug=args.debug
        )
        
        results = await scraper.scrape(limit=args.limit)
        
        print("\n--- Scraping Summary ---")
        print(f"Broker: {broker.name}")
        print(f"Area: {area}")
        print(f"Total properties scraped: {len(results) if results else 0}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())