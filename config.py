import os
class Config:
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rss_aggregator.db')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    ARTICLES_PER_PAGE = 20
    MAX_FEEDS = 50
