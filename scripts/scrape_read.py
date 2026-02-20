import urllib.request
import json
import time
import os

def fetch_douban_read_books(user_id, existing_ids=None):
    if existing_ids is None:
        existing_ids = set()
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
                
                new_books_this_batch = 0
                for item in interests:
                    subject = item.get('subject', {})
                    book_id = subject.get('id')
                    
                    if book_id in existing_ids:
                        print(f"  Found existing book {book_id}, stopping fetch.")
                        # We hit books we've already scraped, so we can stop entirely
                        break
                        
                    rating_obj = item.get('rating')
                    
                    all_interests.append({
                        'id': book_id,
                        'rating': rating_obj.get('value') if rating_obj else None
                    })
                    new_books_this_batch += 1
                
                print(f"  Got {new_books_this_batch} new items this batch.")
                
                # If we broke out of the for-loop early (didn't process all interests),
                # or if we didn't find any new books in this batch, we should stop the while loop
                if new_books_this_batch < len(interests):
                    print("Reached previously fetched books.")
                    break
                
                # Check if we should stop because we hit the total
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
    output_file = "data/read.json"
    
    # Load existing data to support incremental scraping
    existing_data = []
    existing_ids = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_ids = {item['id'] for item in existing_data if 'id' in item}
            print(f"Loaded {len(existing_data)} existing books.")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing {output_file}. Starting fresh.")
    else:
        print(f"No existing {output_file} found. Starting fresh.")
        
    results = fetch_douban_read_books(USER_ID, existing_ids)
    
    if results:
        # Prepend new results to existing data
        combined_data = results + existing_data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(results)} new books (Total: {len(combined_data)}) to {output_file}")
    else:
        print("No new books fetched. Data remains unchanged.")
