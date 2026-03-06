import urllib.request
import json
import time
import os
import csv

def fetch_douban_read_books(user_id, read_existing_ids=None):
    if read_existing_ids is None:
        read_existing_ids = set()
    """
    Scrape "read" books for a given Douban user ID using the Rexxar API.
    """
    base_url = f"https://m.douban.com/rexxar/api/v2/user/{user_id}/interests"
    headers = {
        'Referer': 'https://m.douban.com/mine/',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.31(0x18001f30) NetType/WIFI Language/zh_CN',
    }
    
    all_interests = []
    new_book_details = {} # id -> details
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
                    
                    if book_id in read_existing_ids:
                        print(f"  Found existing book {book_id}, stopping fetch.")
                        # We hit books we've already scraped, so we can stop entirely
                        break
                        
                    # Collect/Update book details for all books not in read_existing_ids
                    title = subject.get('title', '')
                    book_rating_obj = subject.get('rating', {})
                    book_rating_val = book_rating_obj.get('value', 0.0) if book_rating_obj else 0.0
                    book_rating_count = book_rating_obj.get('count', 0) if book_rating_obj else 0
                    authors = subject.get('author', [])
                    author = ', '.join(authors) if authors else ''
                    
                    new_book_details[book_id] = {
                        'ID': book_id,
                        'Rating': book_rating_val,
                        'Votes': book_rating_count,
                        'Title': title,
                        'Author': author
                    }
                            
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
            
    return all_interests, new_book_details

if __name__ == "__main__":
    USER_ID = os.environ.get("DOUBAN_USER_ID")
    if not USER_ID:
        print("Please set the DOUBAN_USER_ID environment variable.")
        exit(1)
    output_file = "data/read.json"
    
    # Load existing data to support incremental scraping
    existing_data = []
    read_existing_ids = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                read_existing_ids = {item['id'] for item in existing_data if 'id' in item}
            print(f"Loaded {len(existing_data)} existing books.")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing {output_file}. Starting fresh.")
    else:
        print(f"No existing {output_file} found. Starting fresh.")
        
    douban_csv_file = "data/douban.csv"
    douban_data = [] # List of dicts
    fieldnames = ['ID', 'Rating', 'Votes', 'Title', 'Author']
    
    if os.path.exists(douban_csv_file):
        with open(douban_csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames if reader.fieldnames else fieldnames
            for row in reader:
                douban_data.append(row)
        print(f"Loaded {len(douban_data)} books from douban.csv.")
    else:
        print(f"No existing {douban_csv_file} found.")
        
    results, new_book_details = fetch_douban_read_books(USER_ID, read_existing_ids)
    
    if results:
        # Update douban.csv with latest details for newly fetched books
        # Build index for quick lookup
        douban_index = {row['ID']: i for i, row in enumerate(douban_data)}
        
        for bid, details in new_book_details.items():
            if bid in douban_index:
                # Update existing entry
                idx = douban_index[bid]
                douban_data[idx].update({
                    'Rating': str(details['Rating']),
                    'Votes': str(details['Votes']),
                    'Title': details['Title'],
                    'Author': details['Author']
                })
            else:
                # Add new entry
                douban_data.append({
                    'ID': str(bid),
                    'Rating': str(details['Rating']),
                    'Votes': str(details['Votes']),
                    'Title': details['Title'],
                    'Author': details['Author']
                })
        
        # Write updated douban.csv
        with open(douban_csv_file, 'w', encoding='utf-8', newline='') as f:
            if 'Author' not in fieldnames:
                fieldnames.append('Author')
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(douban_data)
        print(f"Updated {douban_csv_file} with latest details for {len(new_book_details)} books.")

        # Prepend new results to existing data
        combined_data = results + existing_data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(results)} new books (Total: {len(combined_data)}) to {output_file}")
    else:
        print("No new books fetched. Data remains unchanged.")
