import os
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from models import Property
from urllib.parse import urljoin, urlparse

def create_extraction_instruction(html_fragment: str) -> str:
    """Create instruction prompt for LLM extraction"""
    instruction = f"""
    Extract these property fields from the HTML:
    - address: Full property address as text
    - price: Numbers only, monthly rent amount as string (e.g. "1250")
    - area: Numbers only, size of property as string (e.g. "75")
    - bedrooms: Numbers only! (e.g. "2")
    - energy_label: String only, Energy efficiency label as string (e.g. "A")
    - furnished: "true" or "false" as string
    - including_bills: "true" or "false" as string
    - status: Property status as string ("available", "rented", "option")
    - available_from: Availability date as string
    - url: The property detail page URL - IMPORTANT: Find the listing URL in the HTML (likely an <a> tag with href attribute)

    The HTML fragment is: 
    {html_fragment}

    Return a single JSON object with these fields. Keep all values as strings.
    """
    
    return instruction

def ensure_full_url(base_url: str, url: str) -> str:
    """Ensure the URL is fully qualified, adding the base URL if necessary."""
    if not url:
        return ""
        
    # Check if the URL is already absolute (has scheme and domain)
    parsed_url = urlparse(url)
    if not parsed_url.netloc:
        # Handle paths that start with or without a slash
        if url.startswith('/'):
            # Parse the base_url to get just the scheme and netloc
            parsed_base = urlparse(base_url)
            base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
            return f"{base_domain}{url}"
        else:
            # For URLs without leading slash, we need to join with base URL
            return urljoin(base_url, url)
    return url

def post_process_property_data(data, base_url):
    """Post-process the property data to ensure full URLs."""
    if isinstance(data, dict):
        if 'url' in data and data['url']:
            data['url'] = ensure_full_url(base_url, data['url'])
    elif isinstance(data, list):
        for item in data:
            post_process_property_data(item, base_url)
    return data

def get_llm_strategy(base_url: str, html_fragment: str = "") -> LLMExtractionStrategy:
    """Create LLM extraction strategy with proper configuration"""
    print("Creating LLM strategy...")

    # Get provider and API key from env
    provider = os.getenv('LLM_PROVIDER', 'groq/llama-3.1-8b-instant')
    api_token = os.getenv('GROQ_API_KEY') or os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')

    # Use optimized parameters according to best practices
    strategy = LLMExtractionStrategy(
        provider=provider,
        api_token=api_token,
        schema=Property.model_json_schema(),
        extraction_type="schema",
        instruction=create_extraction_instruction(html_fragment),
        chunk_token_threshold=1000,
        overlap_rate=0.05,
        apply_chunking=True,
        input_format="markdown",  # Use markdown for easier processing by LLM
        extra_args={
            "temperature": float(os.getenv('LLM_TEMPERATURE', 0.1)),
            "max_tokens": int(os.getenv('LLM_MAX_TOKENS', 2000))
        },
        post_process_fn=lambda data: post_process_property_data(data, base_url),
        verbose=bool(os.getenv('DEBUG', 'False').lower() == 'true')
    )

    print(f"LLM strategy created with provider: {provider}")
    return strategy