# Book Search

A simple yet powerful tool to search, filter, and sort books from Douban and Goodreads.

![UI Preview](screenshot.png)

## Features

- **Flexible Querying**: Supports custom field filtering with a simple syntax (e.g., `c:>5000 r:>=8.5`).
- **Dynamic Sorting**: Sort results by rating or rating count.
- **Multi-Source**: Toggle between Douban, Goodreads, or everything.
- **Responsive Design**: Optimized for different screen sizes with a clean, modern UI.

## How to use

1. Enter filtering rules in the **Filter** input box.
   - Format: `field:operatorValue`
   - Fields: `c` (rating count), `r` (rating), `t` (title), `a` (author)
   - Operators: `:` (equal), `>`, `<`, `>=`, `<=`
   - Examples: `c:>10000 r:>9.0 t:Great`, `a:Tolstoy r:>=4.0`
2. Select your **Sort** mode (Rating or Count).
3. Select your **Source** (All, Douban, or Goodreads).
4. Click the **Search** button to view results.

## Local Development

1. Clone the repository.
2. Before running the site, you need to generate `books.json` from the CSV datasets using the provided Python script:
```bash
python3 parse_books.py
```
This will process `douban.csv` and `goodreads.csv` and create the `books.json` file required by the web app.

3. Open `index.html` with a local server (e.g., `live-server`).

## Data Sources

This project uses data from:
- [Douban-books-2020](https://github.com/yuzhounh/Douban-books-2020)
- [Goodreads Scraping Dataset](https://www.kaggle.com/datasets/auregen/goodreads-scraping) (Kaggle)

---

Developed with ❤️
