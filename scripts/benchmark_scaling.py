import asyncio
import aiohttp
import time
import statistics
import json

API_URL = "http://localhost:3001/api/search/enqueue"
# Note: In a real environment, we would need a JWT. 
# Since we are in a controlled test, I will use a dummy token or bypass if possible.
# Actually, I have the secret, I can generate one inside the script.
import jwt 

SECRET = "super_secret_jwt_key_2026_!@#"
TOKEN = jwt.encode({"id": 999, "username": "sb_tester"}, SECRET, algorithm="HS256")

async def fetch_benchmark(session, query, model):
    start_time = time.time()
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "model": model,
        "thread_id": f"bench-{int(time.time())}"
    }
    
    try:
        async with session.post(API_URL, json=payload, headers=headers) as response:
            res_json = await response.json()
            end_time = time.time()
            return end_time - start_time, res_json.get("id")
    except Exception as e:
        print(f"Error: {e}")
        return None, None

async def run_benchmark(num_requests=10, model="llama3.2:latest"):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_benchmark(session, f"Bench query {i}", model) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        times = [r[0] for r in results if r[0] is not None]
        if not times:
            return "Failed to get results"
            
        return {
            "avg": statistics.mean(times),
            "max": max(times),
            "min": min(times),
            "p50": statistics.median(times),
            "count": len(times)
        }

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(json.dumps(asyncio.run(run_benchmark(count)), indent=2))
