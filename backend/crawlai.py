#!/usr/bin/env python
import os
import asyncio
import argparse
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

from models import BrokerConfig, ScrapingResult
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
    parser.add_argument('--max-price', type=int, default=3000, 
                        help='Maximum price for filtering (used by some brokers)')
    return parser.parse_args()

async def scrape_single_broker(broker, area, max_price, debug) -> ScrapingResult:
    """Scrape a single broker"""
    result = ScrapingResult(broker.name)
    start_time = datetime.now()
    
    try:
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
        
        properties = await scraper.scrape()
        
        # Record results
        result.success = True
        result.properties_found = len(properties) if properties else 0
        result.properties_saved = len([p for p in properties if not p.get('error')])
        result.time_taken = (datetime.now() - start_time).total_seconds()
        
        print(f"\n--- {broker.name} Scraping Summary ---")
        print(f"Area: {area}")
        print(f"Total properties scraped: {result.properties_saved}")
        
    except Exception as e:
        result.success = False
        result.error_message = str(e)
        print(f"Error scraping broker {broker.name}: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()
            
    return result

def save_scraping_report(results, output_dir):
    """Save scraping results to a report file"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_file = output_path / f"scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with report_file.open('w') as f:
        for result in results:
            f.write(f"Broker: {result.broker_name}\n")
            f.write(f"Success: {result.success}\n")
            f.write(f"Properties Found: {result.properties_found}\n")
            f.write(f"Properties Saved: {result.properties_saved}\n")
            f.write(f"Time Taken: {result.time_taken} seconds\n")
            if not result.success:
                f.write(f"Error: {result.error_message}\n")
            f.write("\n")
    
    return report_file

async def main():
    """Main entry point"""
    args = parse_arguments()
    
    try:
        # Load configurations
        config_path = os.path.join("utilities", "brokers.json")
        brokers_config = load_brokers_config(config_path)
        
        # Get area and max price
        area = args.area or os.getenv('AREA', 'utrecht')
        max_price = args.max_price or int(os.getenv('MAX_PRICE', '3000'))
        
        scraping_results = []
        
        # Check if we should scrape all brokers
        if args.broker and args.broker.lower() == 'all':
            print(f"Scraping ALL brokers for area: {area}")
            
            # Loop through all brokers in the config
            for broker_config in brokers_config.get('brokers', []):
                broker = BrokerConfig(broker_config)
                result = await scrape_single_broker(
                    broker=broker,
                    area=area,
                    max_price=max_price,
                    debug=args.debug
                )
                scraping_results.append(result)
                
                # Add delay between brokers
                if not result.success:
                    print("Waiting 30 seconds before next broker...")
                    await asyncio.sleep(30)
                    
        else:
            # Get specific broker
            broker_name = args.broker or os.getenv('BROKER_NAME')
            broker = get_broker_config(broker_name, brokers_config)
            
            if not broker:
                raise ValueError(f"Broker '{broker_name}' not found in configuration")
            
            result = await scrape_single_broker(
                broker=broker,
                area=area,
                max_price=max_price,
                debug=args.debug
            )
            scraping_results.append(result)
        
        # Save scraping report
        report_file = save_scraping_report(scraping_results, 'output')
        print(f"\nScraping report saved to: {report_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())