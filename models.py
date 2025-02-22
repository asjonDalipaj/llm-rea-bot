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

class BrokerConfig:
    """Configuration for a broker"""
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get("name", "")
        self.domain = config.get("domain", "")
        self.url_template = config.get("url", "")
        self.listing_selector = config.get("listing_selector", "")
        self.next_button_selector = config.get("next_button_selector", "")
        self.cookie_modal_selector = config.get("cookie_modal_selector", "")
    
    def get_url(self, area: str) -> str:
        """Generate URL with the area parameter"""
        return self.url_template.replace("{area}", area)