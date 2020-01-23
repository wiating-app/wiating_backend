from .wiating_backend import create_app
from .config import DefaultConfig


app = create_app(config=DefaultConfig())
