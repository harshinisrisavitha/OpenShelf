# main.py
import sys
# Import all necessary functions from your existing modules
from sync_logic import search_and_sync_book_by_isbn
from loan_logic import checkout_book, return_book
# Assuming you implement view_report in this file or a separate report_logic.py
from db_connector import get_db_connection 
import mysql.connector

# --- Function to implement the report logic using your Views ---
def view_report(view_name: str):
    """Retrieves and prints data from a specified SQL View."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    
    try:
        # Use a parameterized query for safety, even if just calling a VIEW name
        query = f"SELECT * FROM {view_name}"
        cursor.execute(query)
        
        results = cursor.fetchall()
        if not results:
            print(f"--- REPORT: {view_name} ---")
            print("No data found for this report.")
            return

        # Get column names for the header
        headers = [i[0] for i in cursor.description]
        print("\n--- REPORT: {} ---".format(view_name))
        
        # Simple dynamic printing (adjust formatting as needed)
        print(" | ".join(headers))
        print("-" * (len(" | ".join(headers)) + 5 * len(headers))) 

        for row in results:
            print(" | ".join(str(item) for item in row))
            
    except mysql.connector.Error as err:
        print(f"Error querying view {view_name}: {err}")
        
    finally:
        cursor.close()
        conn.close()

# --- Main Application Menu ---

def print_main_menu():
    """Displays the options available to the user."""
    print("\n==============================================")
    print("      📚 Library Management System (CLI) 📚")
    print("==============================================")
    print("1. Add New Book (Sync by ISBN)")
    print("2. Check Out Book")
    print("3. Return Book")
    print("4. View Reports")
    print("5. Exit")
    print("----------------------------------------------")

def handle_reports_menu():
    """Handles the sub-menu for viewing reports."""
    while True:
        print("\n--- REPORTS MENU ---")
        print("A. View Current Loans (V_CURRENT_LOANS)")
        print("B. View Overdue Books (V_OVERDUE_BOOKS)")
        print("C. View Popular Books (V_POPULAR_BOOKS)")
        print("D. View Patron History (V_PATRON_HISTORY)")
        print("Z. Back to Main Menu")
        
        choice = input("Enter report choice: ").upper()
        
        if choice == 'A':
            view_report("V_CURRENT_LOANS")
        elif choice == 'B':
            view_report("V_OVERDUE_BOOKS")
        elif choice == 'C':
            view_report("V_POPULAR_BOOKS")
        elif choice == 'D':
            # Note: Patron History usually requires an ID input
            patron_id = input("Enter Patron ID for history: ")
            view_report(f"V_PATRON_HISTORY WHERE patron_id = {patron_id}")
        elif choice == 'Z':
            break
        else:
            print("Invalid report choice.")

def main():
    """The main application loop."""
    while True:
        print_main_menu()
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            # Add Book
            isbn = input("Enter ISBN to sync: ")
            search_and_sync_book_by_isbn(isbn.strip())
            
        elif choice == '2':
            # Checkout Book
            isbn = input("Enter ISBN to checkout: ")
            patron_id = input("Enter Patron ID: ")
            try:
                checkout_book(isbn.strip(), int(patron_id))
            except ValueError:
                print("Invalid Patron ID. Must be a number.")

        elif choice == '3':
            # Return Book
            isbn = input("Enter ISBN to return: ")
            patron_id = input("Enter Patron ID: ")
            try:
                return_book(isbn.strip(), int(patron_id))
            except ValueError:
                print("Invalid Patron ID. Must be a number.")
                
        elif choice == '4':
            # View Reports
            handle_reports_menu()

        elif choice == '5':
            # Exit
            print("Exiting Library Management System. Goodbye!")
            sys.exit(0)
            
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()