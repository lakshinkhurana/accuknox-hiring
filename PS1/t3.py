import csv
import os
import sqlite3
import sys
from typing import Any, Dict, List, Tuple

DEFAULT_CSV_PATH = "users.csv"
DEFAULT_DB_PATH = "users_data.db"

def init_database(db_path: str = DEFAULT_DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT DEFAULT 'Member',
                signup_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
    print(f"[+] Database initialized at '{db_path}'.")

def read_from_csv(csv_path: str = DEFAULT_CSV_PATH) -> List[Dict[str, str]]:
    if not os.path.exists(csv_path):
        print(f"[-] CSV file not found at: '{csv_path}'", file=sys.stderr)
        return []
    valid_users: List[Dict[str, str]] = []
    print(f"[+] Reading user data from CSV: '{csv_path}'...")
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        row_num = 1
        for row in reader:
            row_num += 1
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()
            role = row.get("role", "Member").strip() or "Member"
            signup_date = row.get("signup_date", "").strip()
            # basic validation
            if not name or not email:
                print(f"[!] Warning: Row {row_num} missing required name/email. Skipping.")
                continue
            if "@" not in email or "." not in email.split("@")[-1]:
                print(f"[!] Warning: Row {row_num} has invalid email '{email}'. Skipping.")
                continue
            valid_users.append(
                {
                    "name": name,
                    "email": email,
                    "role": role,
                    "signup_date": signup_date,
                }
            )
    print(f"[+] Successfully parsed {len(valid_users)} valid user record(s) from CSV.")
    return valid_users

def import_users_to_db(
    users: List[Dict[str, str]], db_path: str = DEFAULT_DB_PATH
) -> Tuple[int, int]:
    if not users:
        print("[!] No users to import.")
        return 0, 0
    insert_query = """
        INSERT OR IGNORE INTO users (name, email, role, signup_date)
        VALUES (?, ?, ?, ?);
    """
    records = [
        (user["name"], user["email"], user["role"], user["signup_date"])
        for user in users
    ]
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        initial_count = cursor.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
        cursor.executemany(insert_query, records)
        conn.commit()
        final_count = cursor.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
    inserted_count = final_count - initial_count
    skipped_count = len(users) - inserted_count
    print(
        f"[+] Imported {inserted_count} new user(s) into database. "
        f"({skipped_count} skipped as duplicates/already existing. Total users in DB: {final_count})."
    )
    return inserted_count, skipped_count

def display_stored_users(db_path: str = DEFAULT_DB_PATH) -> None:
    if not os.path.exists(db_path):
        print(f"[-] Database file '{db_path}' not found.", file=sys.stderr)
        return
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, email, role, signup_date, created_at
            FROM users
            ORDER BY id ASC;
            """
        )
        rows = cursor.fetchall()
    if not rows:
        print("[!] No user records found in database.")
        return
    print("\n" + "=" * 92)
    print(f"{'STORED USERS IN SQLITE DATABASE':^92}")
    print("=" * 92)
    header = f"{'ID':<4} | {'Name':<22} | {'Email':<30} | {'Role':<18} | {'Signup Date'}"
    print(header)
    print("-" * 92)
    for row in rows:
        user_id, name, email, role, signup_date, _ = row
        print(
            f"{user_id:<4} | {name:<22} | {email:<30} | {role:<18} | {signup_date or 'N/A'}"
        )
    print("=" * 92 + "\n")

def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(base_dir, DEFAULT_CSV_PATH)
    db_file = os.path.join(base_dir, DEFAULT_DB_PATH)
    # db setup
    init_database(db_file)
    users = read_from_csv(csv_file)
    if users:
        import_users_to_db(users, db_file)
    display_stored_users(db_file)

if __name__ == "__main__":
    main()
