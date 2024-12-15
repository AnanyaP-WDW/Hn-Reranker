from .hn import get_top_500_posts
from .rerank import PostRanker

async def format_posts_for_reranking(posts):
    formatted_passages = [
        {
            "id": i,
            "text": post["title"],
            "meta": {
                "url": post["url"],
                "score": post["score"],
                "type": post["type"]
            }
        }
        for i, post in enumerate(posts)
    ]
    return formatted_passages

async def main():
    # Get posts from HN
    posts = await get_top_500_posts()
    
    # Format posts for reranking
    passages = await format_posts_for_reranking(posts)
    
    # Initialize ranker
    ranker = PostRanker(max_length=512)  # Increased max_length to handle longer texts
    
    # Example query - replace with actual user's interests
    query = """I am interested in AI, large language models, and technology applied 
    to solving real-world problems in medicine, healthcare and Biotechnology."""
    
    # Rerank posts
    ranked_results = await ranker.rerank_posts(query=query, passages=passages)
    
    # Print top 10 results
    print("\nTop 10 Most Relevant Posts:")
    print("-" * 50)
    for i, result in enumerate(ranked_results[:10], 1):
        print(f"\n{i}. Score: {result['score']:.3f}")
        print(f"Title: {result['text']}")
        print(f"URL: {result['meta']['url']}")
        print(f"HN Score: {result['meta']['score']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
