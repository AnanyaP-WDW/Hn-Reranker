## solution optimizing dev time

### Thought process and decisions
1) get id's of top 500 posts in hacker rank fornt page
2) concurrently fetch detialed post data for each id - semaphore + chunking to prevent overwhelming the hn api. Connection pooling with aiohttp, retry logic for failed requests, controlled concurrency (50 simultaneous requests), and chunk processing (50 posts at a time with 100ms delays) to balance between speed and API rate limits while maintaining reliability.
3) re-rank the hn posts - model should be small and fast - cannot let the user wait very long - using flahrank lib + cross-encoder model (deafault model - https://huggingface.co/cross-encoder/ms-marco-TinyBERT-L-2 -model size 4 mb) - outputs softmax probs (better than just comparing cosine distances)
4) right now the solution only uses post headings to re-rank.(logic - the heading tells the essence of the post; since objective is to optimize dev time this decision saved time on scraping static and dynamic sites, and picking a good representative text for each post since model context size is limited - downside: will def affect the goodnes of ranking) 
5) ouput results with probs


### further improvements
1) scraping each static and dyanmic site in the post - picking a good representative text and using this to rereank
2) latency
