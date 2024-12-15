from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .hn import get_top_500_posts
from .rerank import PostRanker
from .main import format_posts_for_reranking

app = FastAPI(
    title="HackerNews Bio Ranker",
    description="API that ranks HackerNews stories based on user's bio and interests",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="src/static"), name="static")


class UserBio(BaseModel):
    bio: str = Field(..., min_length=1, max_length=2000)
    
    # Add validation to clean the input
    @validator('bio')
    def clean_bio(cls, v):
        if not v:
            raise ValueError('Bio cannot be empty')
        # Remove any problematic characters and normalize whitespace
        v = ' '.join(v.split())
        return v

class PostResponse(BaseModel):
    title: str
    url: Optional[str]
    hn_score: int
    relevance_score: float

class RankedPostsResponse(BaseModel):
    posts: List[PostResponse]

@app.get("/")
async def read_root():
    return FileResponse('src/static/index.html')

@app.post("/rank_posts", response_model=RankedPostsResponse)
async def rank_posts(user_bio: UserBio):
    try:
        # Log the received bio for debugging
        print(f"Received bio: {user_bio.bio}")
        
        # Get posts from HN
        posts = await get_top_500_posts()
        if not posts:
            raise HTTPException(status_code=503, detail="Failed to fetch posts from HackerNews")
        
        # Format posts for reranking
        passages = await format_posts_for_reranking(posts)
        
        # Initialize ranker
        ranker = PostRanker(max_length=512)
        
        # Rerank posts
        ranked_results = await ranker.rerank_posts(query=user_bio.bio, passages=passages)
        
        # Format response
        response_posts = [
            PostResponse(
                title=result["text"],
                url=result["meta"]["url"],
                hn_score=result["meta"]["score"],
                relevance_score=float(result["score"])
            )
            for result in ranked_results
        ]
        
        return RankedPostsResponse(posts=response_posts)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        # Attempt to read the body
        body = await request.body()
        print(f"Request body: {body.decode()}")
        
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 