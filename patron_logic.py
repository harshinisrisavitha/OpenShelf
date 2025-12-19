# patron_logic.py
import mysql.connector
from db_connector import get_db_connection

def register_patron(first_name: str, last_name: str, email: str) -> bool:
    """
    Inserts a new patron record into the Patron table.
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    success = False
    
    try:
        # Check if email already exists (assuming UNIQUE constraint on email)
        check_sql = "SELECT patron_id FROM Patron WHERE email = %s"
        cursor.execute(check_sql, (email,))
        if cursor.fetchone():
            print(f"ERROR: Patron with email {email} already exists.")
            return False

        # Insert new patron
        insert_sql = """
        INSERT INTO Patron (first_name, last_name, email)
        VALUES (%s, %s, %s)
        """
        cursor.execute(insert_sql, (first_name, last_name, email))
        
        # Commit the transaction
        conn.commit()
        new_id = cursor.lastrowid
        print(f"SUCCESS: New Patron registered with ID: {new_id}")
        success = True

    except mysql.connector.Error as err:
        print(f"Database error during patron registration: {err}")
        conn.rollback()
        success = False

    finally:
        cursor.close()
        conn.close()
        return success
    

def find_patron_by_email(email: str):
    """
    Looks up a patron by email and returns their ID, name, and current loan count.
    
    Returns:
        A tuple (patron_id, first_name, last_name, loan_count) or None if not found.
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True) # Use dictionary=True for easier column access
    patron_data = None
    
    try:
        # Step 1: Find the Patron ID and Name
        patron_sql = "SELECT patron_id, first_name, last_name FROM Patron WHERE email = %s"
        cursor.execute(patron_sql, (email,))
        patron_info = cursor.fetchone()
        
        if not patron_info:
            return None # Patron not found
            
        patron_id = patron_info['patron_id']
        
        # Step 2: Count their active loans
        loan_sql = "SELECT COUNT(loan_id) as active_loans FROM Loan WHERE patron_id = %s AND return_date IS NULL"
        cursor.execute(loan_sql, (patron_id,))
        loan_count = cursor.fetchone()['active_loans']
        
        # Step 3: Combine and return all data
        patron_data = {
            'patron_id': patron_id,
            'first_name': patron_info['first_name'],
            'last_name': patron_info['last_name'],
            'active_loans': loan_count
        }

    except mysql.connector.Error as err:
        print(f"Database error during patron lookup: {err}")
        patron_data = None

    finally:
        cursor.close()
        conn.close()
        return patron_data
