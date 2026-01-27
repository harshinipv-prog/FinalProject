from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from database.operations import (
    get_posts,
    get_pain_points,
    get_statistics,
    search_posts
)

router = APIRouter()


@router.get("/posts")
async def get_all_posts(
    limit: int = Query(100, ge=1, le=500, description="Max posts to return"),
    skip: int = Query(0, ge=0, description="Posts to skip (pagination)"),
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    Get all posts with optional filters
    
    Example:
        GET /api/v1/posts?limit=50&subreddit=developersIndia
    """
    posts = get_posts(
        limit=limit,
        skip=skip,
        subreddit=subreddit,
        category=category,
        pain_points_only=False
    )
    
    return {
        "count": len(posts),
        "posts": posts,
        "pagination": {
            "limit": limit,
            "skip": skip,
            "has_more": len(posts) == limit
        }
    }


@router.get("/pain-points")
async def get_all_pain_points(
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = Query(None, description="Filter by category (Career, Finance, etc.)"),
    min_score: int = Query(0, ge=0, description="Minimum upvote score"),
):
    """
    Get pain points with filters
    
    Example:
        GET /api/v1/pain-points?category=Career&min_score=10
    """
    pain_points = get_pain_points(
        limit=limit,
        category=category,
        min_score=min_score
    )
    
    return {
        "count": len(pain_points),
        "pain_points": pain_points
    }


@router.get("/pain-points/categories")
async def get_categories():
    """Get all available pain point categories"""
    from scraper.keywords import PAIN_CATEGORIES
    
    return {
        "categories": list(PAIN_CATEGORIES.keys()),
        "total": len(PAIN_CATEGORIES)
    }


@router.get("/pain-points/top")
async def get_top_pain_points(
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = None
):
    """
    Get top pain points by engagement (score + comments)
    
    Example:
        GET /api/v1/pain-points/top?limit=10&category=Career
    """
    pain_points = get_pain_points(limit=100, category=category)
    
    # Sort by engagement score
    for point in pain_points:
        point['engagement_score'] = point['score'] + (point['num_comments'] * 2)
    
    sorted_points = sorted(pain_points, key=lambda x: x['engagement_score'], reverse=True)
    
    return {
        "count": len(sorted_points[:limit]),
        "top_pain_points": sorted_points[:limit]
    }


@router.get("/statistics")
async def get_stats():
    """
    Get database statistics
    
    Example:
        GET /api/v1/statistics
    """
    stats = get_statistics()
    return stats


@router.get("/search")
async def search(
    q: str = Query(..., min_length=3, description="Search query"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search posts by text
    
    Example:
        GET /api/v1/search?q=job%20search&limit=20
    """
    posts = search_posts(query=q, limit=limit)
    
    return {
        "query": q,
        "count": len(posts),
        "results": posts
    }


@router.get("/subreddits")
async def get_subreddits():
    """Get list of tracked subreddits"""
    from scraper.keywords import TARGET_SUBREDDITS
    
    return {
        "subreddits": TARGET_SUBREDDITS,
        "total": len(TARGET_SUBREDDITS)
    }


@router.get("/opportunities")
async def get_opportunities(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get business opportunities based on pain points
    (Aggregated view of high-frequency pain points)
    """
    pain_points = get_pain_points(limit=200, min_score=5)
    
    # Group by category
    category_counts = {}
    for point in pain_points:
        cat = point.get('category', 'Other')
        if cat not in category_counts:
            category_counts[cat] = {
                'category': cat,
                'count': 0,
                'total_score': 0,
                'sample_posts': []
            }
        category_counts[cat]['count'] += 1
        category_counts[cat]['total_score'] += point['score']
        if len(category_counts[cat]['sample_posts']) < 3:
            category_counts[cat]['sample_posts'].append({
                'title': point['title'],
                'score': point['score'],
                'url': point['url']
            })
    
    # Calculate opportunity score
    opportunities = []
    for cat, data in category_counts.items():
        opportunities.append({
            'category': cat,
            'pain_points_count': data['count'],
            'average_score': round(data['total_score'] / data['count'], 2),
            'opportunity_score': round((data['count'] * data['total_score']) / 100, 2),
            'sample_posts': data['sample_posts']
        })
    
    # Sort by opportunity score
    opportunities = sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True)
    
    return {
        "count": len(opportunities[:limit]),
        "opportunities": opportunities[:limit]
    }