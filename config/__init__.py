import os 
from .default import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    testing=TestingConfig,
    default=DevelopmentConfig
)

def get_config(config_name=None):

    env_config_name = os.environ.get('FLASK_ENV', 'development').lower()
    selected_config_name = config_name or env_config_name
    return config_by_name.get(selected_config_name, config_by_name['default'])

