import argparse
import csv
import json
from datetime import datetime, timezone


def parse_books(path):
    items = []
    seen_ids = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f, skipinitialspace=True)
        headers = next(reader, None)
        # books.csv format: ID,Rating,Votes,Title
        for row in reader:
            if not row or len(row) < 4:
                continue
            book_id = int(row[0].strip())
            if book_id in seen_ids:
                continue
            seen_ids.add(book_id)
            
            try:
                rating = float(row[1].strip()) if row[1].strip() else 0.0
                votes = int(float(row[2].strip())) if row[2].strip() else 0
                title = row[3].strip()
            except (ValueError, IndexError):
                continue

            items.append(
                {
                    "i": book_id,
                    "r": rating,
                    "c": votes,
                    "t": title,
                    "u": f"https://book.douban.com/subject/{book_id}/",
                }
            )
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="books.csv")
    parser.add_argument("--output", default="books.json")
    args = parser.parse_args()

    items = parse_books(args.input)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "source": args.input,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))


if __name__ == "__main__":
    main()
