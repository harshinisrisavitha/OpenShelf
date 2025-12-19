import mysql.connector

# --- 1. Configuration Dictionary ---
DB_CONFIG = {
    "host": "localhost",
    "user": "library_user",
    "password": "strongpassword",
    "database": "library_management_db"
}

def get_db_connection():
    """
    Attempts to establish a connection to the MySQL database 
    and returns the connection object.
    """
    try:
        # **kwargs unpacks the DB_CONFIG dictionary into keyword arguments**
        conn = mysql.connector.connect(**DB_CONFIG)
        
        if conn.is_connected():
            print("Database Connection Status: SUCCESS")
            # You can also get cursor here if you want to reuse it:
            # cursor = conn.cursor()
            return conn
        else:
            print("Database Connection Status: FAILED (Unknown Error)")
            return None

    except mysql.connector.Error as e:
        # This block catches specific MySQL errors (e.g., wrong password, DB not running)
        print("\n--- DATABASE CONNECTION ERROR ---")
        if e.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("ERROR: Access denied. Check your 'user' or 'password' in DB_CONFIG.")
        elif e.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("ERROR: Database does not exist. Check 'database' name.")
        else:
            print(f"ERROR: {e}")
        print("---------------------------------")
        return None


if __name__ == "__main__":
    # 1. Attempt to connect
    db_conn = get_db_connection()
    
    if db_conn:
        try:
            # 2. Connection is successful, now test a simple query
            cursor = db_conn.cursor()
            
            #cursor->control structure used to iterate over and process individual rows of data from a result set.
            
            # Simple query to check the patron table
            cursor.execute("SELECT * FROM Patron")
            patrons = cursor.fetchall()
            
            print(f"\nSuccessfully retrieved {len(patrons)} patrons:")
            for patron in patrons:
                print(patron)
                
        except mysql.connector.Error as err:
            print(f"Error during query execution: {err}")
            
        finally:
            # 3. Always close the cursor and connection when done
            if 'cursor' in locals() and cursor:
                cursor.close()
            db_conn.close()
            print("\nDatabase connection closed.")
    else:
        print("\nFailed to connect. Cannot proceed with application logic.")

