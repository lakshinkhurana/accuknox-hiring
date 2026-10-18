import os
import sqlite3
import sys
from typing import Any, Dict, List
import requests

DEFAULT_API_URL = "https://openlibrary.org/search.json"
DEFAULT_DB_PATH = "books_data.db"
DEFAULT_SEARCH_TOPIC = "artificial intelligence"
DEFAULT_LIMIT = 10
REQUEST_TIMEOUT_SECONDS = 15


def fetch_books_from_api(
    query: str = DEFAULT_SEARCH_TOPIC,
    limit: int = DEFAULT_LIMIT,
    api_url: str = DEFAULT_API_URL,
) -> List[Dict[str, Any]]:
    #List of dictionaries containing parsed book attributes.
    params = {"q": query, "limit": limit}
    headers = {"User-Agent": "AccuKnox-Assessment-Client/1.0"}

    print(f"[+] Fetching up to {limit} books for topic '{query}' from API...")
    try:
        response = requests.get(
            api_url, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        print("[-] Error: Request timed out while connecting to the API.", file=sys.stderr)
        return []
    except requests.exceptions.RequestException as exc:
        print(f"[-] Network/API error: {exc}", file=sys.stderr)
        return []
    except ValueError as exc:
        print(f"[-] Failed to parse JSON response: {exc}", file=sys.stderr)
        return []

    raw_docs = data.get("docs", [])
    extracted_books: List[Dict[str, Any]] = []

    for item in raw_docs:
        title = item.get("title", "Untitled").strip()
        authors = item.get("author_name", [])
        author = authors[0].strip() if authors else "Unknown"
        pub_year = item.get("first_publish_year")

        extracted_books.append(
            {
                "title": title,
                "author": author,
                "publication_year": int(pub_year) if pub_year else None,
            }
        )

    print(f"[+] Successfully retrieved and parsed {len(extracted_books)} books.")
    return extracted_books


def init_database(db_path: str = DEFAULT_DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                publication_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_book UNIQUE (title, author, publication_year)
            );
            """
        )
        conn.commit()
    print(f"[+] Database initialized at '{db_path}'.")


def store_books(books: List[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> int:
    if not books:
        print("[!] No book records to store.")
        return 0

    insert_query = """
        INSERT OR IGNORE INTO books (title, author, publication_year)
        VALUES (?, ?, ?);
    """

    records = [
        (book["title"], book["author"], book["publication_year"]) for book in books
    ]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        initial_count = cursor.execute("SELECT COUNT(*) FROM books;").fetchone()[0]
        cursor.executemany(insert_query, records)
        conn.commit()
        final_count = cursor.execute("SELECT COUNT(*) FROM books;").fetchone()[0]

    inserted_count = final_count - initial_count
    print(
        f"[+] Stored {inserted_count} new record(s) in database (Total records in DB: {final_count})."
    )
    return inserted_count


def display_stored_books(db_path: str = DEFAULT_DB_PATH) -> None:
    if not os.path.exists(db_path):
        print(f"[-] Database file '{db_path}' not found.", file=sys.stderr)
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, author, publication_year, created_at
            FROM books
            ORDER BY id ASC;
            """
        )
        rows = cursor.fetchall()

    if not rows:
        print("No books found in the database.")
        return

    print("\n" + "=" * 90)
    print(f"{'Stored in SQLite':^90}")
    print("=" * 90)
    header = f"{'ID':<4} | {'Title':<42} | {'Author':<24} | {'Year':<6} | {'Created At'}"
    print(header)
    print("-" * 90)

    for row in rows:
        book_id, title, author, year, created_at = row
        truncated_title = (title[:39] + "...") if len(title) > 42 else title
        truncated_author = (author[:21] + "...") if len(author) > 24 else author
        year_str = str(year) if year is not None else "N/A"
        print(
            f"{book_id:<4} | {truncated_title:<42} | {truncated_author:<24} | {year_str:<6} | {created_at}"
        )

    print("=" * 90 + "\n")


def main() -> None:
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_DB_PATH)
    init_database(db_file)#initialision
    books = fetch_books_from_api(query=DEFAULT_SEARCH_TOPIC, limit=DEFAULT_LIMIT)
    if books:
        store_books(books, db_file)
    display_stored_books(db_file)#display

if __name__ == "__main__":
    main()
