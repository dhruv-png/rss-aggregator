import sqlite3, os

def init_database():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rss_aggregator.db')
    connection = sqlite3.connect(db_path)
    
    with open('schema.sql', 'r') as f:
        connection.executescript(f.read())
    
    cursor = connection.cursor()
    
    sample_feeds = [
        # News
        ('BBC News - World', 'http://feeds.bbci.co.uk/news/world/rss.xml', 'News'),
        ('Reuters Top News', 'https://feeds.reuters.com/reuters/topNews', 'News'),
        ('The Guardian', 'https://www.theguardian.com/world/rss', 'News'),
        ('CNN Top Stories', 'http://rss.cnn.com/rss/edition.rss', 'News'),
        
        # Technology
        ('TechCrunch', 'https://techcrunch.com/feed/', 'Technology'),
        ('Hacker News', 'https://news.ycombinator.com/rss', 'Technology'),
        ('The Verge', 'https://www.theverge.com/rss/index.xml', 'Technology'),
        ('Wired', 'https://www.wired.com/feed/rss', 'Technology'),
        
        # Science & Space
        ('NASA Breaking News', 'https://www.nasa.gov/rss/dyn/breaking_news.rss', 'Science'),
        ('Space.com News', 'https://www.space.com/feeds/latest-news.xml', 'Science'),
        ('Science Daily', 'https://www.sciencedaily.com/rss/all.xml', 'Science'),
        
        # Programming
        ('Python.org News', 'https://www.python.org/feeds/news.rss/', 'Programming'),
        ('GitHub Blog', 'https://github.blog/feed/', 'Programming'),
        ('Stack Overflow Blog', 'https://stackoverflow.blog/feed/', 'Programming'),
        ('Dev.to', 'https://dev.to/feed', 'Programming'),
        ('Medium - Programming', 'https://medium.com/feed/tag/programming', 'Programming'),
    ]
    
    cursor.executemany(
        'INSERT INTO feeds (name, url, category) VALUES (?, ?, ?)',
        sample_feeds
    )
    
    connection.commit()
    connection.close()
    
    print(f'✅ Database initialized with {len(sample_feeds)} feeds!')

if __name__ == '__main__':
    init_database()
