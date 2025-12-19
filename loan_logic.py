# loan_logic.py
from datetime import datetime, timedelta
import mysql.connector
from db_connector import get_db_connection

# Define the standard loan period (e.g., 14 days)
LOAN_PERIOD_DAYS = 14 

def checkout_book(isbn: str, patron_id: int) -> bool:
    """
    Handles the process of lending a book to a patron. 
    Requires a transactional update to both Book and Loan tables.
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    success = False

    try:
        # Start the transaction
        conn.start_transaction() 
        
        # 1. Verify Book Availability (SELECT FOR UPDATE locks the row)
        # This prevents two users from checking out the last copy simultaneously.
        check_book_sql = """
        SELECT available_copies, total_copies FROM Book WHERE isbn = %s FOR UPDATE
        """
        cursor.execute(check_book_sql, (isbn,))
        book_data = cursor.fetchone()

        if not book_data:
            print(f"FAILURE: Book with ISBN {isbn} not found.")
            conn.rollback()
            return False

        available, total = book_data
        
        if available <= 0:
            print(f"FAILURE: Book {isbn} is currently out of stock (0 copies available).")
            conn.rollback()
            return False

        # 2. Decrement available_copies
        new_available = available - 1
        update_book_sql = """
        UPDATE Book SET available_copies = %s WHERE isbn = %s
        """
        cursor.execute(update_book_sql, (new_available, isbn))
        
        # 3. Create the Loan Record
        checkout_date = datetime.now().date()
        due_date = checkout_date + timedelta(days=LOAN_PERIOD_DAYS)
        
        insert_loan_sql = """
        INSERT INTO Loan (isbn, patron_id, checkout_date, due_date, return_date)
        VALUES (%s, %s, %s, %s, NULL)
        """
        cursor.execute(insert_loan_sql, (isbn, patron_id, checkout_date, due_date))

        # 4. Commit the Transaction
        conn.commit()
        print(f"SUCCESS: Book {isbn} checked out by Patron {patron_id}. Due: {due_date}")
        success = True

    except mysql.connector.Error as err:
        print(f"Database error during checkout: {err}")
        conn.rollback() # Rollback everything if any step fails
        success = False

    finally:
        cursor.close()
        conn.close()
        return success


FINE_RATE_PER_DAY = 0.25 # Define the fine rate

def return_book(isbn: str, patron_id: int) -> bool:
    """
    Handles the book return process, including fine calculation and recording.
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    success = False
    return_date = datetime.now().date()
    
    try:
        conn.start_transaction() 

        # 1. Find the active loan and its due_date (return_date IS NULL)
        find_loan_sql = """
        SELECT loan_id, due_date FROM Loan 
        WHERE isbn = %s AND patron_id = %s AND return_date IS NULL 
        LIMIT 1 FOR UPDATE
        """
        cursor.execute(find_loan_sql, (isbn, patron_id))
        loan_record = cursor.fetchone()
        
        if not loan_record:
            print(f"FAILURE: No active loan found for ISBN {isbn} by Patron {patron_id}.")
            conn.rollback()
            return False
        
        loan_id, due_date = loan_record
        
        # --- FINE CALCULATION LOGIC ---
        days_late = (return_date - due_date).days
        
        if days_late > 0:
            fine_amount = days_late * FINE_RATE_PER_DAY
            print(f"NOTICE: Book is {days_late} days overdue. Fine of ${fine_amount:.2f} recorded.")
            
            # 2. Insert Fine Record
            fine_sql = """
            INSERT INTO Fine (loan_id, fine_amount, fine_date, payment_date)
            VALUES (%s, %s, %s, NULL)
            """
            cursor.execute(fine_sql, (loan_id, fine_amount, return_date))

        # 3. Update the Loan record with the return date (Always happens)
        update_loan_sql = """
        UPDATE Loan SET return_date = %s WHERE loan_id = %s
        """
        cursor.execute(update_loan_sql, (return_date, loan_id))

        # 4. Increment available_copies in the Book table (Always happens)
        update_book_sql = """
        UPDATE Book SET available_copies = available_copies + 1 WHERE isbn = %s
        """
        cursor.execute(update_book_sql, (isbn,))

        # 5. Commit the Transaction
        conn.commit()
        print(f"SUCCESS: Book {isbn} returned by Patron {patron_id}.")
        success = True

    except mysql.connector.Error as err:
        print(f"Database error during return process: {err}")
        conn.rollback()
        success = False

    finally:
        cursor.close()
        conn.close()
        return success
    


def get_patron_active_loans(patron_id: int):
    """
    Retrieves the ISBN and title for all books currently checked out by a patron.
    
    Returns:
        A list of dictionaries [{'isbn': ..., 'title': ...}] or an empty list.
    """
    conn = get_db_connection()
    if not conn:
        return []

    # Use dictionary=True for easy access to column names (isbn, title)
    cursor = conn.cursor(dictionary=True) 
    loans = []
    
    try:
        # We join Loan and Book to get the title
        query = """
        SELECT L.isbn, B.title
        FROM Loan L
        JOIN Book B ON L.isbn = B.isbn
        WHERE L.patron_id = %s AND L.return_date IS NULL
        """
        cursor.execute(query, (patron_id,))
        loans = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Database error fetching active loans: {err}")

    finally:
        cursor.close()
        conn.close()
        return loans
