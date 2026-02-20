import urllib.request
import json
import time
import os

def fetch_douban_read_books(user_id):
    """
    Scrape "read" books for a given Douban user ID using the Rexxar API.
    """
    base_url = f"https://m.douban.com/rexxar/api/v2/user/{user_id}/interests"
    headers = {
        'Referer': 'https://m.douban.com/mine/',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.31(0x18001f30) NetType/WIFI Language/zh_CN',
    }
    
    all_interests = []
    start = 0
    count = 50
    total = None
    
    print("Starting to fetch read books...")
    
    while True:
        url = f"{base_url}?type=book&status=done&count={count}&start={start}&for_mobile=1"
        print(f"Fetching batch (start={start})... (Current total collected: {len(all_interests)})")
        
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    print(f"Error fetching data: {response.status}")
                    break
                
                res_content = response.read().decode('utf-8')
                data = json.loads(res_content)
                
                if total is None:
                    total = data.get('total', 0)
                    print(f"API reports total items: {total}")
                
                interests = data.get('interests', [])
                
                if not interests:
                    print("No more interests found.")
                    break
                
                for item in interests:
                    subject = item.get('subject', {})
                    rating_obj = item.get('rating')
                    
                    all_interests.append({
                        'id': subject.get('id'),
                        'rating': rating_obj.get('value') if rating_obj else None
                    })
                
                print(f"  Got {len(interests)} items this batch.")
                
                # Check if we should stop
                if len(all_interests) >= total:
                    print(f"Reached API reported total: {total}")
                    break
                
                # Increment start. Douban API's start is offset-based.
                # We use start += count to ensure we move to the next window.
                start += count
                
                # Delay to avoid being blocked
                time.sleep(1)
                
        except Exception as e:
            print(f"An error occurred: {e}")
            break
            
    return all_interests

if __name__ == "__main__":
    USER_ID = os.environ.get("DOUBAN_USER_ID")
    if not USER_ID:
        print("Please set the DOUBAN_USER_ID environment variable.")
        exit(1)
    results = fetch_douban_read_books(USER_ID)
    
    if results:
        output_file = "read.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(results)} books to {output_file}")
    else:
        print("No results fetched.")
