import sqlite3, feedparser, atexit
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Initialize scheduler for auto-refresh
scheduler = BackgroundScheduler()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def fetch_feed_articles(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        for entry in feed.entries[:15]:
            article = {
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', ''),
                'description': entry.get('summary', entry.get('description', 'No description')),
                'author': entry.get('author', 'Unknown'),
                'published': entry.get('published', '')
            }
            articles.append(article)
        return articles, None
    except Exception as e:
        return [], str(e)

def auto_fetch_all_feeds():
    """Auto-fetch all feeds every 30 minutes"""
    with app.app_context():
        print(f'🔄 Auto-fetching feeds at {datetime.now()}...')
        db = get_db()
        feeds_list = db.execute('SELECT * FROM feeds').fetchall()
        total_saved = 0
        for feed in feeds_list:
            articles, error = fetch_feed_articles(feed['url'])
            if not error:
                for article in articles:
                    try:
                        db.execute(
                            'INSERT INTO articles (feed_id, title, link, description, author, published_date) VALUES (?, ?, ?, ?, ?, ?)',
                            (feed['id'], article['title'], article['link'], article['description'], article['author'], article['published'])
                        )
                        total_saved += 1
                    except sqlite3.IntegrityError:
                        pass
                db.execute('UPDATE feeds SET last_fetched = CURRENT_TIMESTAMP WHERE id = ?', (feed['id'],))
        db.commit()
        print(f'✅ Auto-fetch completed! Added {total_saved} new articles')

# Schedule auto-fetch every 30 minutes
scheduler.add_job(func=auto_fetch_all_feeds, trigger="interval", minutes=30)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    db = get_db()
    articles = db.execute('''
        SELECT a.*, f.name as feed_name, f.category,
        CASE WHEN fav.id IS NOT NULL THEN 1 ELSE 0 END as is_favorite
        FROM articles a
        JOIN feeds f ON a.feed_id = f.id
        LEFT JOIN favorites fav ON a.id = fav.article_id
        ORDER BY a.fetched_at DESC
        LIMIT ?
    ''', (app.config['ARTICLES_PER_PAGE'],)).fetchall()
    
    feed_count = db.execute('SELECT COUNT(*) as count FROM feeds').fetchone()['count']
    article_count = db.execute('SELECT COUNT(*) as count FROM articles').fetchone()['count']
    favorite_count = db.execute('SELECT COUNT(*) as count FROM favorites').fetchone()['count']
    
    return render_template('index.html', articles=articles, feed_count=feed_count, 
                         article_count=article_count, favorite_count=favorite_count)

@app.route('/feeds')
def feeds():
    db = get_db()
    feeds_list = db.execute('''
        SELECT f.*, COUNT(a.id) as article_count
        FROM feeds f
        LEFT JOIN articles a ON f.id = a.feed_id
        GROUP BY f.id
        ORDER BY f.category, f.name
    ''').fetchall()
    return render_template('feeds.html', feeds=feeds_list)

@app.route('/favorites')
def favorites():
    db = get_db()
    articles = db.execute('''
        SELECT a.*, f.name as feed_name, f.category
        FROM articles a
        JOIN feeds f ON a.feed_id = f.id
        JOIN favorites fav ON a.id = fav.article_id
        ORDER BY fav.added_at DESC
    ''').fetchall()
    return render_template('favorites.html', articles=articles)

@app.route('/feeds/add', methods=['POST'])
def add_feed():
    name = request.form.get('name')
    url = request.form.get('url')
    category = request.form.get('category', 'Uncategorized')
    
    if not name or not url:
        flash('Both name and URL are required!', 'error')
        return redirect(url_for('feeds'))
    
    db = get_db()
    try:
        db.execute('INSERT INTO feeds (name, url, category) VALUES (?, ?, ?)', (name, url, category))
        db.commit()
        flash(f'Feed "{name}" added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('This feed URL already exists!', 'error')
    
    return redirect(url_for('feeds'))

@app.route('/feeds/<int:feed_id>/delete', methods=['POST'])
def delete_feed(feed_id):
    db = get_db()
    db.execute('DELETE FROM feeds WHERE id = ?', (feed_id,))
    db.commit()
    flash('Feed deleted successfully!', 'success')
    return redirect(url_for('feeds'))

@app.route('/feeds/<int:feed_id>/fetch', methods=['POST'])
def fetch_feed(feed_id):
    db = get_db()
    feed = db.execute('SELECT * FROM feeds WHERE id = ?', (feed_id,)).fetchone()
    
    if not feed:
        flash('Feed not found!', 'error')
        return redirect(url_for('feeds'))
    
    articles, error = fetch_feed_articles(feed['url'])
    
    if error:
        flash(f'Error fetching feed: {error}', 'error')
        return redirect(url_for('feeds'))
    
    saved_count = 0
    for article in articles:
        try:
            db.execute(
                'INSERT INTO articles (feed_id, title, link, description, author, published_date) VALUES (?, ?, ?, ?, ?, ?)',
                (feed_id, article['title'], article['link'], article['description'], article['author'], article['published'])
            )
            saved_count += 1
        except sqlite3.IntegrityError:
            pass
    
    db.execute('UPDATE feeds SET last_fetched = CURRENT_TIMESTAMP WHERE id = ?', (feed_id,))
    db.commit()
    
    flash(f'Fetched {saved_count} new articles from "{feed["name"]}"!', 'success')
    return redirect(url_for('feeds'))

@app.route('/feeds/<int:feed_id>/articles')
def feed_articles(feed_id):
    db = get_db()
    feed = db.execute('SELECT * FROM feeds WHERE id = ?', (feed_id,)).fetchone()
    
    if not feed:
        flash('Feed not found!', 'error')
        return redirect(url_for('feeds'))
    
    articles = db.execute('''
        SELECT a.*, 
        CASE WHEN fav.id IS NOT NULL THEN 1 ELSE 0 END as is_favorite
        FROM articles a
        LEFT JOIN favorites fav ON a.id = fav.article_id
        WHERE a.feed_id = ?
        ORDER BY a.fetched_at DESC
        LIMIT ?
    ''', (feed_id, app.config['ARTICLES_PER_PAGE'])).fetchall()
    
    return render_template('articles.html', feed=feed, articles=articles)

@app.route('/fetch-all', methods=['POST'])
def fetch_all():
    db = get_db()
    feeds_list = db.execute('SELECT * FROM feeds').fetchall()
    
    total_saved = 0
    for feed in feeds_list:
        articles, error = fetch_feed_articles(feed['url'])
        
        if not error:
            for article in articles:
                try:
                    db.execute(
                        'INSERT INTO articles (feed_id, title, link, description, author, published_date) VALUES (?, ?, ?, ?, ?, ?)',
                        (feed['id'], article['title'], article['link'], article['description'], article['author'], article['published'])
                    )
                    total_saved += 1
                except sqlite3.IntegrityError:
                    pass
            
            db.execute('UPDATE feeds SET last_fetched = CURRENT_TIMESTAMP WHERE id = ?', (feed['id'],))
    
    db.commit()
    flash(f'Fetched {total_saved} new articles from all feeds!', 'success')
    return redirect(url_for('index'))

@app.route('/article/<int:article_id>/favorite', methods=['POST'])
def toggle_favorite(article_id):
    db = get_db()
    
    # Check if already favorited
    existing = db.execute('SELECT id FROM favorites WHERE article_id = ?', (article_id,)).fetchone()
    
    if existing:
        db.execute('DELETE FROM favorites WHERE article_id = ?', (article_id,))
        db.commit()
        return jsonify({'status': 'removed', 'message': 'Removed from favorites'})
    else:
        try:
            db.execute('INSERT INTO favorites (article_id) VALUES (?)', (article_id,))
            db.commit()
            return jsonify({'status': 'added', 'message': 'Added to favorites'})
        except sqlite3.IntegrityError:
            return jsonify({'status': 'error', 'message': 'Error'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
