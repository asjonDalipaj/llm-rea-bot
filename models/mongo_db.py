from fastapi import FastAPI, HTTPException, Query
from mongoengine import connect, disconnect, Q
from .mongo_models import PropertyListing
from typing import List, Optional
from pydantic import BaseModel
import os

app = FastAPI(title="Property Scraper API")

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/property_scraper')

@app.on_event("startup")
def connect_db():
    connect(host=MONGO_URI)

@app.on_event("shutdown")
def disconnect_db():
    disconnect()

# Pydantic models for request/response
class PropertyBase(BaseModel):
    address: str | None = None
    price: str | None = None
    area: str | None = None
    bedrooms: str | None = None
    energy_label: str | None = None
    furnished: bool = False
    including_bills: bool = False
    status: str | None = None
    available_from: str | None = None
    url: str
    broker: str

    class Config:
        from_attributes = True

# API endpoints
@app.post("/properties/", response_model=PropertyBase)
async def create_property(property: PropertyBase):
    try:
        # Convert Pydantic model to MongoDB document
        property_doc = PropertyListing(
            address=property.address,
            price=property.price,
            area=property.area,
            bedrooms=property.bedrooms,
            energy_label=property.energy_label,
            furnished=property.furnished,
            including_bills=property.including_bills,
            status=property.status,
            available_from=property.available_from,
            url=property.url,
            broker=property.broker
        )
        
        # Save to MongoDB (upsert based on URL)
        existing = PropertyListing.objects(url=property.url).first()
        if existing:
            for key, value in property.model_dump().items():
                setattr(existing, key, value)
            existing.save()
            return property
        else:
            property_doc.save()
            return property
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/properties/", response_model=List[PropertyBase])
async def search_properties(
    address: Optional[str] = Query(None, description="Search by address"),
    broker: Optional[str] = Query(None, description="Filter by broker"),
    limit: int = Query(10, gt=0, le=100, description="Maximum number of results")
):
    """
    Search properties with optional filters:
    - address: Case-insensitive partial match
    - broker: Exact match
    - limit: Maximum number of results to return
    """
    try:
        # Build query
        query = Q()
        if address:
            query &= Q(address__icontains=address)
        if broker:
            query &= Q(broker=broker)

        # Execute query
        properties = PropertyListing.objects(query).limit(limit)
        
        # Convert to response model
        return [PropertyBase.model_validate(prop.to_mongo()) for prop in properties]
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/properties/{property_url}", response_model=PropertyBase)
async def get_property(property_url: str):
    try:
        property = PropertyListing.objects(url=property_url).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
        return PropertyBase.model_validate(property.to_mongo())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))