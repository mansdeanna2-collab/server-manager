"""Flask extensions module to avoid circular imports."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

# Initialize Limiter globally so it can be accessed by routes
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=Config.RATELIMIT_STORAGE_URL
)
