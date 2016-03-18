import os


class Config(object):
    db_conn = 'postgresql+psycopg2://public:C@ntH@ck@localhost/twitsense'
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.urandom(32)
    SQLALCHEMY_DATABASE_URI = db_conn


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
