from .default import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': Config
}

def get_config(config_name):
    return config_by_name.get(config_name, config_by_name['default'])

