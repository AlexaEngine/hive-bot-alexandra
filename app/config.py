import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables
FMCSA_API_KEY = os.environ.get('FMCSA_API_KEY')
MONGO_CLIENT = os.environ.get('MONGO_CLIENT')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
TELEGRAM_API_KEY = os.environ.get('TELEGRAM_API_KEY')
MAX_TOKENS_LIMIT = 350

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Equipment type multipliers
EQUIPMENT_TYPE_MULTIPLIERS = {
    'V': 1, 'PO': 1, 'FO': 0.8, 'R': 1.2, 'VM': 1.7, 'RM': 2.2, 'F': 0.8, 'FM': 1.5
}
