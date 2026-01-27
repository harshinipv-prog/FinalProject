from pymongo import MongoClient
from config.settings import settings

# Use settings.mongodb_uri and settings.mongodb_database
client = MongoClient(settings.mongodb_uri, tls=True)
db = client[settings.mongodb_database]

posts_collection = db["posts"]
pain_points_collection = db["pain_points"]

def save_posts(posts):
    if posts:
        try:
            posts_collection.insert_many(posts, ordered=False)
            print(f"✅ Saved {len(posts)} posts")
        except Exception as e:
            print(f"❌ Error saving posts: {e}")

def save_pain_point(pain_point):
    try:
        pain_points_collection.insert_one(pain_point)
        print(f"✅ Saved pain point {pain_point.get('post_id', '')}")
    except Exception as e:
        print(f"❌ Error saving pain point: {e}")
