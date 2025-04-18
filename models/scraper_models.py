from typing import Optional, Dict, Any
from pydantic import BaseModel

class Property(BaseModel):
    """Schema for property data"""
    address: str
    price: str
    area: Optional[str] = ""
    bedrooms: Optional[str] = ""
    energy_label: Optional[str] = ""
    furnished: Optional[str] = "false"
    including_bills: Optional[str] = "false"
    status: Optional[str] = "available"
    available_from: Optional[str] = ""
    url: Optional[str] = ""

class BrokerConfig:
    """Configuration for a broker"""
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get("name", "")
        self.domain = config.get("domain", "")
        self.url_template = config.get("url", "")
        self.listing_selector = config.get("listing_selector", "")
        self.next_button_selector = config.get("next_button_selector", "")
        self.cookie_modal_selector = config.get("cookie_modal_selector", "")
        self.fetch_detail_pages = config.get("fetch_detail_pages", False)
    
    def get_url(self, area: str) -> str:
        """Generate URL with the area parameter"""
        return self.url_template.replace("{area}", area)

class ScrapingResult:
    def __init__(self, broker_name: str):
        self.broker_name = broker_name
        self.success = False
        self.error_message = ""
        self.properties_found = 0
        self.properties_saved = 0
        self.time_taken = 0.0