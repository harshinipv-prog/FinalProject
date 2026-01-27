import praw
from datetime import datetime
from typing import List, Dict

from config.settings import settings
from database.operations import save_posts
from scraper.keywords import TARGET_SUBREDDITS


class RedditScraper:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        print("✅ Reddit API initialized")

    def scrape_subreddit(self, subreddit_name: str, limit: int = None) -> List[Dict]:
        if limit is None:
            limit = settings.max_posts_per_subreddit

        posts = []

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            for submission in subreddit.hot(limit=limit):
                post_data = {
                    "post_id": submission.id,
                    "subreddit": subreddit_name,
                    "title": submission.title,
                    "content": submission.selftext,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "created_utc": datetime.utcfromtimestamp(submission.created_utc),
                    "url": f"https://www.reddit.com{submission.permalink}",
                    "scraped_at": datetime.utcnow(),
                    "source": "reddit_raw"
                }
                posts.append(post_data)

            if posts:
                save_posts(posts)
                print(f"✅ Scraped & saved {len(posts)} posts from r/{subreddit_name}")
            else:
                print(f"⚠️ No posts found in r/{subreddit_name}")

        except Exception as e:
            print(f"❌ Error scraping r/{subreddit_name}: {e}")

        return posts

    def scrape_all_subreddits(self, subreddits: List[str] = None):
        if subreddits is None:
            subreddits = TARGET_SUBREDDITS

        total_posts = 0

        for subreddit_name in subreddits:
            posts = self.scrape_subreddit(subreddit_name)
            total_posts += len(posts)

        print(f"📊 Finished scraping {len(subreddits)} subreddits")
        print(f"📦 Total posts scraped: {total_posts}")

