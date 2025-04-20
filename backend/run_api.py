import uvicorn
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

if __name__ == "__main__":
    try:
        host = os.getenv('API_HOST', 'localhost')
        port = int(os.getenv('API_PORT', 8000))
        
        logger.info(f"Starting API server at http://{host}:{port}")
        logger.info("API Module Path: models.mongo_db:app")
        
        uvicorn.run(
            "models.mongo_db:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")