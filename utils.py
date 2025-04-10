import os
import json
import re
from bs4 import BeautifulSoup
from models import BrokerConfig
from typing import Optional, Dict, List
import httpx
from datetime import datetime
from urllib.parse import urljoin, urlparse

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
    os.makedirs(output_dir, exist_ok=True)
    debug_file = os.path.join(output_dir, f"debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    return debug_file

def save_properties_json(properties: list, broker_name: str, area: str, output_dir: str) -> str:
    """Save properties to JSON file and return the file path"""
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

def clean_energy_label(label: str) -> str:
    """
    Validate and clean energy label (A++, A+, A-G)
    Returns empty string if invalid
    """
    if not label:
        return ""
    
    # Convert to uppercase and remove whitespace
    label = str(label).upper().strip()
    
    # Check for valid energy labels
    valid_labels = ['A++', 'A+'] + list('ABCDEFG')
    return label if label in valid_labels else ""

def ensure_full_url(base_url: str, url: str) -> str:
    """Ensure URL is fully qualified by adding base URL if needed"""
    if not url:
        return ""
    
    # Check if URL is already absolute
    parsed_url = urlparse(url)
    if not parsed_url.netloc:
        # If URL is relative, join it with base URL
        return urljoin(base_url, url)
    return url

def clean_property_data(data: Dict, base_url: str = "") -> Dict:
    """Clean and validate property data according to schema requirements"""
    
    def clean_price(price: str) -> str:
        """Extract numbers from price string"""
        if not price:
            return ""
        numbers = re.findall(r'\d+', str(price))
        return numbers[0] if numbers else ""
    
    def clean_area(area: str) -> str:
        """Extract number from area string"""
        if not area:
            return ""
        numbers = re.findall(r'\d+', str(area))
        return numbers[0] if numbers else ""
    
    def clean_bedrooms(bedrooms: str) -> str:
        """Extract number from bedrooms string"""
        if not bedrooms:
            return ""
        numbers = re.findall(r'\d+', str(bedrooms))
        return numbers[0] if numbers else ""
    
    def clean_boolean(value: any) -> str:
        """Convert various boolean representations to 'true'/'false'"""
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            return 'true' if value.lower() in ['true', 'yes', '1', 'y'] else 'false'
        return 'false'
    
    def clean_status(status: str) -> str:
        """Validate status against allowed values"""
        valid_statuses = ['available', 'rented', 'option']
        status = str(status).lower() if status else 'available'
        return status if status in valid_statuses else 'available'
    
    def clean_date(date_str: str) -> str:
        """Validate and format date string"""
        if not date_str:
            return ""
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            return ""

    # Clean and validate each field
    cleaned_data = {
        "address": str(data.get("address", "")).strip(),
        "price": clean_price(data.get("price")),
        "area": clean_area(data.get("area")),
        "bedrooms": clean_bedrooms(data.get("bedrooms")),
        "energy_label": clean_energy_label(data.get("energy_label")),
        "furnished": clean_boolean(data.get("furnished")),
        "including_bills": clean_boolean(data.get("including_bills")),
        "status": clean_status(data.get("status")),
        "available_from": clean_date(data.get("available_from")),
        "url": ensure_full_url(base_url, str(data.get("url", "")).strip())
    }

    # Log warnings for missing required fields
    for field in ['address', 'price', 'url']:
        if not cleaned_data[field]:
            print(f"Warning: Missing or invalid {field}")

    return cleaned_data

async def save_properties_to_db(properties: List[Dict], broker_name: str) -> None:
    """Save properties to database via API endpoint"""
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    async with httpx.AsyncClient() as client:
        for prop in properties:
            if prop.get('error'):
                continue
            
            try:
                # Clean data before saving
                cleaned_prop = clean_property_data(prop)
                
                # Add broker name
                cleaned_prop['broker'] = broker_name
                
                # print(f"Sending cleaned data to API: {cleaned_prop}")
                response = await client.post(f"{api_url}/properties/", json=cleaned_prop)
                response.raise_for_status()
                print(f"✓ Saved property to database: {cleaned_prop['address']}")
                
            except Exception as e:
                print(f"✗ Error saving property to database: {str(e)}")
                print(f"Original property data: {prop}")