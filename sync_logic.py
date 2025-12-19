from datetime import datetime
import json
import mysql.connector
from db_connector import get_db_connection
from api_handler import parse_google_books_data,get_book_data_from_api




def search_and_sync_book_by_isbn(isbn):
    """
    Core function to check DB, check cache, call API, and sync data into 
    Book, Author, and Book_Author tables in a single transaction.
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    book_found_in_db = False

    try:
        # --- A. Check if Book already exists in the local DB (Book table) ---
        cursor.execute("SELECT isbn FROM Book WHERE isbn = %s", (isbn,))
        if cursor.fetchone():
            print(f"Book with ISBN {isbn} already exists in the local DB.")
            book_found_in_db = True
            return True

        # --- B. Check API Cache for a recent response ---
        raw_api_response = None
        
        cursor.execute("SELECT api_response, cached_at FROM Api_Cache WHERE isbn = %s", (isbn,))
        cache_data = cursor.fetchone()

        if cache_data:
            cache_json, cached_at = cache_data
            
            # Check if cache is fresh (e.g., less than 7 days old)
            cache_freshness_days = 7
            if (datetime.now() - cached_at).days < cache_freshness_days:
                print("Cache hit: Using fresh cached API response.")
                # The JSON object from MySQL connector often needs to be loaded if it's a string
                raw_api_response = json.loads(cache_json) 
            else:
                print("Cache found but stale. Will call API.")

        # --- C. Call API if not found or cache is stale ---
        if not raw_api_response:
            print("Cache miss. Calling Google Books API...")
            raw_data_item = get_book_data_from_api(isbn) 
            
            if not raw_data_item:
                print("Could not retrieve book data from API.")
                return False

            # Cache the raw response for future use
            raw_api_response_str = json.dumps(raw_data_item)
            
            # Using INSERT ... ON DUPLICATE KEY UPDATE to handle potential race conditions
            cache_sql = """
            INSERT INTO Api_Cache (isbn, api_response, cached_at) 
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE api_response = VALUES(api_response), cached_at = NOW();
            """
            cursor.execute(cache_sql, (isbn, raw_api_response_str))
            
            # Set the response for processing
            raw_api_response = raw_data_item


        # --- D. Process and Sync (The Transactional Part) ---
        
        # 1. Parse the necessary fields
        book_info = parse_google_books_data(raw_api_response)
        if not book_info:
            conn.rollback()
            return False

        # 2. Insert into Book Table
        print(f"Syncing book: {book_info['title']}")
        book_sql = """
        INSERT INTO Book (isbn, title, publisher, publication_year, total_copies, available_copies)
        VALUES (%s, %s, %s, %s, 0, 0)
        """
        cursor.execute(book_sql, (
            isbn, 
            book_info['title'], 
            book_info['publisher'], 
            book_info['publication_year']
        ))
        
        # 3. Handle Authors (Loop through all authors)
        for author_name in book_info['authors']:
            # a. Check if Author exists and get ID (using a stored procedure logic)
            author_check_sql = "SELECT author_id FROM Author WHERE author_name = %s"
            cursor.execute(author_check_sql, (author_name,))
            result = cursor.fetchone()
            
            author_id = None
            if result:
                # Author exists
                author_id = result[0]
            else:
                # b. Author does NOT exist, insert new author
                author_insert_sql = "INSERT INTO Author (author_name) VALUES (%s)"
                cursor.execute(author_insert_sql, (author_name,))
                author_id = cursor.lastrowid # Get the ID of the newly inserted row

            # c. Link Book and Author in the Junction Table
            link_sql = """
            INSERT INTO Book_Author (isbn, author_id)
            VALUES (%s, %s)
            """
            cursor.execute(link_sql, (isbn, author_id))

        # 4. Commit the Transaction
        conn.commit()
        print(f"SUCCESS: Book {isbn} and all authors synced to DB.")
        return True

    except mysql.connector.Error as err:
        print(f"Database error during sync process: {err}")
        # Rollback all changes if any error occurs
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()

def search_available_books(search_term: str):
    """
    Searches books by ISBN or Title that have available copies.
    Returns:
        A list of dictionaries [{'isbn': ..., 'title': ...}] or an empty list.
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True) 
    books = []
    search_pattern = f"%{search_term}%" # Pattern for LIKE search
    
    try:
        query = """
        SELECT isbn, title, available_copies
        FROM Book
        WHERE available_copies > 0 
          AND (isbn LIKE %s OR title LIKE %s)
        LIMIT 20 -- Limit results for speed
        """
        cursor.execute(query, (search_pattern, search_pattern))
        books = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Database error fetching available books: {err}")

    finally:
        cursor.close()
        conn.close()
        return books
