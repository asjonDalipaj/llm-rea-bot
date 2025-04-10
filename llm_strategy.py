import os
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from models import Property
from urllib.parse import urljoin, urlparse

def create_extraction_instruction(html_fragment: str) -> str:
    """Create instruction prompt for LLM extraction"""
    instruction = f"""
    Extract the following property details from the provided HTML fragment. 
    Return a single JSON object with these fields, keeping all values as strings:

    - **address**: Full property address (e.g., "123 Main St, City, Country").
    - **price**: Monthly rent amount as a number string (e.g., "1250").
    - **area**: Property size in square meters as a number string (e.g., "75").
    - **bedrooms**: Number of bedrooms as a number string (e.g., "2").
    - **energy_label**: Energy efficiency label (e.g., "A").
    - **furnished**: "true" or "false" (whether the property is furnished).
    - **including_bills**: "true" or "false" (whether bills are included).
    - **status**: Property status (e.g., "available", "rented", "option").
    - **available_from**: Availability date (e.g., "2025-04-01").
    - **url**: The property detail page URL (extract from an <a> tag with an href attribute).

    HTML fragment:
    {html_fragment}
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
        verbose=bool(os.getenv('DEBUG', 'False').lower() == 'true')
    )

    print(f"LLM strategy created with provider: {provider}")
    return strategy