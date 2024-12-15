# get id of top 500 posts from hacker news api -> async req to  https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty
# this will return a list of ids
# then for each id, make an async req to https://hacker-news.firebaseio.com/v0/item/{id}.json?print=pretty
# this will return a dict of post data -> 
# then we can use the answer ai reranker to rerank the posts

import aiohttp
from aiohttp import ClientError, TCPConnector, ClientTimeout
import asyncio
from asyncio import TimeoutError
import time


async def get_top_500_posts_aiohttp():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty") as response:
                response.raise_for_status()
                return await response.json()
    except ClientError as e:
        print(f"An error occurred: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# get title,url score and type from post data
async def get_post_data(session, id, max_retries=3):
    timeout = ClientTimeout(total=10)  # 10 seconds timeout
    for attempt in range(max_retries):
        try:
            async with session.get(
                f"https://hacker-news.firebaseio.com/v0/item/{id}.json?print=pretty",
                timeout=timeout
            ) as response:
                response.raise_for_status()
                post_data = await response.json()
                return {
                    "title": post_data.get("title"),
                    "url": post_data.get("url"),
                    "score": post_data.get("score"),
                    "type": post_data.get("type")
                }
        except (ClientError, TimeoutError) as e:
            if attempt == max_retries - 1:
                print(f"Failed after {max_retries} attempts for id {id}: {e}")
                return None
            await asyncio.sleep(1)  # Wait before retrying

# get top 500 posts, for each post, get the title,url,score and type and store in a list
async def get_top_500_posts():
    try:
        top_500_posts = await get_top_500_posts_aiohttp()
        if top_500_posts is None:
            raise ValueError("Failed to retrieve top 500 posts")
        
        # Increase concurrent connections and requests
        semaphore = asyncio.Semaphore(50)  # Increased to 50 concurrent requests
        
        # Create a single session for all requests with increased limits
        connector = TCPConnector(limit=100, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            async def get_post_with_semaphore(post_id):
                async with semaphore:
                    return await get_post_data(session, post_id)
            
            # Process in smaller chunks with delays to prevent overwhelming
            chunk_size = 50
            delay_between_chunks = 0.1  # 100ms delay between chunks
            post_data_list = []
            
            for i in range(0, len(top_500_posts), chunk_size):
                chunk = top_500_posts[i:i + chunk_size]
                tasks = [get_post_with_semaphore(post_id) for post_id in chunk]
                chunk_results = await asyncio.gather(*tasks)
                post_data_list.extend([post for post in chunk_results if post is not None])
                await asyncio.sleep(delay_between_chunks)  # Small delay between chunks
        
        return post_data_list
    except ValueError as e:
        print(f"ValueError: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

# create a main function to run the above functions
async def main():
    #time the function
    start_time = time.time()
    post_data_list = await get_top_500_posts()
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    print(post_data_list)
    print("-"*50)
    print(len(post_data_list))
    print("-"*50)
    print(end_time - start_time)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


