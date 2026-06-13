import os


class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'bbuser')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'bbpassword')
    DB_NAME = os.environ.get('DB_NAME', 'bloodbank')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


class TestingConfig:
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'test-secret-key'
    DB_HOST = 'localhost'
    DB_USER = 'test'
    DB_PASSWORD = 'test'
    DB_NAME = 'test'
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    BYPASS_LOGIN = True


class ProductionConfig:
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_HOST = os.environ.get('DB_HOST')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')


config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
