import os
import json
import re
from bs4 import BeautifulSoup
from models import BrokerConfig
from typing import Optional, Dict, List
import httpx

def clean_url(url: str) -> str:
    """Clean a URL by removing angle brackets and other unwanted characters"""
    if not url:
        return ""
    
    # Remove angle brackets and any HTML-like formatting
    url = url.replace('<', '').replace('>', '')
    
    # Handle cases where there are quotes around the URL
    url = url.strip('"\'')
    
    # Remove spaces that might be present
    url = url.strip()
    
    # Remove any markdown formatting like [text](url)
    markdown_match = re.search(r'\[(.*?)\]\((.*?)\)', url)
    if markdown_match:
        url = markdown_match.group(2)
    
    return url

def load_brokers_config(config_path: str) -> Dict:
    """Load broker configurations from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Loaded {len(data.get('brokers', []))} brokers from config")
            return data
    except Exception as e:
        print(f"Error loading brokers config: {str(e)}")
        return {"brokers": []}

def get_broker_config(broker_name: str, brokers_config: Dict) -> Optional[BrokerConfig]:
    """Get broker configuration by name"""
    if not broker_name:
        # Default to first broker if none specified
        if brokers_config.get("brokers"):
            return BrokerConfig(brokers_config["brokers"][0])
        return None
        
    for broker in brokers_config.get("brokers", []):
        if broker.get("name", "").lower() == broker_name.lower():
            return BrokerConfig(broker)
    return None

def clean_html_fragment(html: str) -> str:
    """Clean and simplify HTML to reduce token usage"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unnecessary elements that don't contain property information
        for tag in soup.find_all(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()
            
        # Remove most attributes except essential ones
        for tag in soup.find_all():
            attrs_to_keep = ['class', 'id', 'href', 'src']
            for attr in list(tag.attrs.keys()):
                if attr not in attrs_to_keep:
                    del tag[attr]
        
        # Remove empty divs and spans
        for tag in soup.find_all(['div', 'span']):
            if not tag.text.strip() and not tag.find_all():
                tag.decompose()
        
        return str(soup)
    except Exception as e:
        print(f"Error cleaning HTML: {str(e)}")
        return html

def save_debug_html(html: str, output_dir: str) -> str:
    """Save HTML for debugging and return the file path"""
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    debug_file = os.path.join(output_dir, f"debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    return debug_file

def save_properties_json(properties: list, broker_name: str, area: str, output_dir: str) -> str:
    """Save properties to JSON file and return the file path"""
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"properties_{broker_name}_{area}_{timestamp}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(properties, f, indent=2, ensure_ascii=False)
    
    return filename

def parse_rate_limit_error(error_str: str) -> float:
    """Parse wait time from rate limit error message"""
    wait_time_match = re.search(r'try again in (\d+\.?\d*)s', error_str.lower())
    return float(wait_time_match.group(1)) if wait_time_match else 30

async def save_properties_to_db(properties: List[Dict], broker_name: str) -> None:
    """Save properties to database via API endpoint"""
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    async with httpx.AsyncClient() as client:
        for prop in properties:
            if prop.get('error'):
                continue
            
            try:
                response = await client.post(
                    f"{api_url}/properties/",
                    json={
                        "address": prop.get('address'),
                        "price": prop.get('price'),
                        "area": prop.get('area'),
                        "bedrooms": prop.get('bedrooms'),
                        "energy_label": prop.get('energy_label'),
                        "furnished": prop.get('furnished', 'false').lower() == 'true',
                        "including_bills": prop.get('including_bills', 'false').lower() == 'true',
                        "status": prop.get('status'),
                        "available_from": prop.get('available_from'),
                        "url": prop.get('url'),
                        "broker": broker_name
                    }
                )
                response.raise_for_status()
                print(f"✓ Saved property to database: {prop.get('address')}")
            except Exception as e:
                print(f"✗ Error saving property to database: {str(e)}")