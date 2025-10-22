"""Environment variable management using python-dotenv."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def env(key: str, default=None):
    """
    Get environment variable value.
    
    Args:
        key: Environment variable name
        default: Default value if key not found
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)

