# Self-Hosted RSS News Aggregator

A privacy-friendly, self-hosted RSS news aggregator web app in a single portable container.

## Quick Start

git clone https://github.com/dhruv-png/rss-aggregator.git
cd rss-aggregator
docker build -t rss-aggregator:latest .
docker run -d --name rss-aggregator -p 5000:5000 -v $(pwd)/data:/app/data rss-aggregator:latest

text
Then open [http://localhost:5000](http://localhost:5000) in your browser.

Or pull directly:
docker pull dhruv-png/rss-aggregator:latest
docker run -d --name rss-rss -p 5000:5000 -v $(pwd)/data:/app/data dhruv-png/rss-aggregator:latest

text

## Features

- Add, manage, and remove RSS/Atom feeds
- Fetch and aggregate articles from multiple sources
- Bookmark/favorite your favorite articles
- Auto-refreshes feeds in the background
- Responsive user interface
- Data is persistent with Docker volume

## Configuration

- All configs are in `config.py`
- Persistent DB at `/app/data`
- Uses port 5000

## Useful Links

- GitHub: https://github.com/dhruv-png/rss-aggregator
- DockerHub: https://hub.docker.com/r/dhruv-png/rss-aggregator

## License

MIT
