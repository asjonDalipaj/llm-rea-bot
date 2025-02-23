import os
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from models import Property

def create_extraction_instruction(is_single_listing: bool = False) -> str:
    """Create instruction prompt for LLM extraction"""
    if is_single_listing:
        return """
        Extract these property fields from the HTML:
        - address: Property address
        - price: Number only
        - area: Number only
        - bedrooms: Number only
        - energy_label: Letter A-G
        - furnished: "true"/"false"
        - including_bills: "true"/"false"
        - status: "available"/"rented"/"option"
        - available_from: YYYY-MM-DD
        - utl: Property URL

        Return a single JSON object.
        """
    else:
        return """
        For each property listing, extract:
        - address: Property address
        - price: Number only
        - area: Number only
        - bedrooms: Number only
        - energy_label: Letter A-G
        - furnished: "true"/"false"
        - including_bills: "true"/"false"
        - status: "available"/"rented"/"option"
        - available_from: YYYY-MM-DD
        - utl: Property URL

        Return a JSON array of objects.
        """

def get_llm_strategy(html_fragment: str = "") -> LLMExtractionStrategy:
    """Create LLM extraction strategy with proper configuration"""
    print("Creating LLM strategy...")
    
    # Get provider and API key from env
    provider = os.getenv('LLM_PROVIDER', 'groq/llama-3.1-8b-instant')
    api_token = os.getenv('GROQ_API_KEY') or os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
    
    # Construct extraction instruction - keep it concise to reduce tokens
    instruction = create_extraction_instruction(bool(html_fragment))

    # Use smaller token thresholds to avoid rate limits
    strategy = LLMExtractionStrategy(
        provider=provider,
        api_token=api_token,
        schema=Property.model_json_schema(),
        extraction_type="schema",
        instruction=instruction,
        chunk_token_threshold=800,  # Reduced from 1500
        overlap_rate=0.05,  # Reduced from 0.1
        apply_chunking=True,
        input_format="html",
        extra_args={
            "temperature": float(os.getenv('LLM_TEMPERATURE', 0.1)),
            "max_tokens": int(os.getenv('LLM_MAX_TOKENS', 2000))  # Reduced from 4000
        }
    )
    
    print(f"LLM strategy created with provider: {provider}")
    return strategy