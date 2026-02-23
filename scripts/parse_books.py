import argparse
import csv
import json
from datetime import datetime, timezone


def parse_douban(path, read_info=None):
    if read_info is None:
        read_info = {}  # title -> set of ids
    
    items = []
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.reader(f, skipinitialspace=True)
        next(reader, None)  # skip header: ID,Rating,Votes,Title
        for row in reader:
            if not row or len(row) < 4:
                continue
            book_id = int(row[0].strip())
            if not book_id:
                continue
            try:
                rating = float(row[1].strip()) if row[1].strip() else 0.0
                votes = int(float(row[2].strip())) if row[2].strip() else 0
                title = row[3].strip()
            except (ValueError, IndexError):
                continue
            
            # Skip if title matches a read book but ID does not match any of its read IDs
            if title in read_info and book_id not in read_info[title]:
                continue
                
            items.append({"i": book_id, "r": round(rating, 2), "c": votes, "t": title})
    return items


def parse_goodreads(path):
    items = []
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book_id = row.get("id", "").strip()
            if not book_id:
                continue
            try:
                rating_str = row.get("rating", "0").strip()
                if not rating_str or rating_str.upper() == "N/A":
                    rating = 0.0
                else:
                    rating = float(rating_str)
                rating = round(rating * 2, 2)  # convert 5-base to 10-base
                
                num_ratings_str = row.get("num_ratings", "0").replace(",", "").strip()
                if not num_ratings_str or num_ratings_str.upper() == "N/A":
                    num_ratings = 0
                else:
                    num_ratings = int(float(num_ratings_str))
                
                title = row.get("title", "").strip()
                author = row.get("author", "").strip()
            except (ValueError, IndexError):
                continue
            item = {"i": book_id, "r": rating, "c": num_ratings, "t": title}
            if author:
                item["a"] = author
            items.append(item)
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--douban", default="data/douban.csv")
    parser.add_argument("--goodreads", default="data/goodreads.csv")
    parser.add_argument("--read", default="data/read.json")
    parser.add_argument("--output", default="data/books.json")
    args = parser.parse_args()

    # Build title -> set of IDs for read books
    read_info = {}
    read_ids = set()
    try:
        with open(args.read, "r", encoding="utf-8") as f:
            read_data = json.load(f)
            read_ids = {int(item["id"]) for item in read_data if "id" in item}
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
        pass

    if read_ids:
        with open(args.douban, "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.reader(f, skipinitialspace=True)
            next(reader, None)
            for row in reader:
                if not row or len(row) < 4:
                    continue
                try:
                    bid = int(row[0].strip())
                    title = row[3].strip()
                    if bid in read_ids:
                        if title not in read_info:
                            read_info[title] = set()
                        read_info[title].add(bid)
                except (ValueError, IndexError):
                    continue

    douban_items = parse_douban(args.douban, read_info)
    goodreads_items = parse_goodreads(args.goodreads)

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "douban": douban_items,
        "goodreads": goodreads_items,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Douban: {len(douban_items)} books, Goodreads: {len(goodreads_items)} books")
    print(f"Written to {args.output}")


if __name__ == "__main__":
    main()
