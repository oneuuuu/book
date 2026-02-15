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
        for row in reader:
            if not row or len(row) < 6:
                continue
            book_id = row[0].strip()
            if not book_id.isdigit():
                continue
            if book_id in seen_ids:
                continue
            seen_ids.add(book_id)
            score = float(row[1].strip()) if row[1].strip() else 0.0
            rating = float(row[2].strip()) if row[2].strip() else 0.0
            votes = int(float(row[3].strip())) if row[3].strip() else 0
            date = row[4].strip()
            title = row[5].strip()
            items.append(
                {
                    "id": int(book_id),
                    "score": score,
                    "rating": rating,
                    "ratingCount": votes,
                    "date": date,
                    "title": title,
                    "url": f"https://book.douban.com/subject/{book_id}/",
                    "img": "",
                }
            )
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="books.txt")
    parser.add_argument("--output", default="books.json")
    args = parser.parse_args()

    items = parse_books(args.input)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "source": args.input,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
