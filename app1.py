# app.py
import streamlit as st
import pandas as pd
import mysql.connector

# --- Import ALL necessary functions ---
from sync_logic import search_and_sync_book_by_isbn,search_available_books
from loan_logic import checkout_book, return_book,get_patron_active_loans
from patron_logic import register_patron, find_patron_by_email # Assuming both are here
from db_connector import get_db_connection

# --- Utility Functions ---

def display_report_results(view_name: str, query_filter: str = ""):
    """Queries a SQL View or table and displays the result in a Streamlit dataframe."""
    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed. Cannot fetch report.")
        return

    try:
        # Use a safe query construction
        query = f"SELECT * FROM {view_name} {query_filter}"
        
        # Use pd.read_sql for clean data retrieval
        df = pd.read_sql(query, conn)
        
        if df.empty:
            st.info(f"The {view_name.replace('V_', '').replace('_', ' ').title()} report is currently empty.")
        else:
            st.dataframe(df, use_container_width=True)

    except mysql.connector.Error as err:
        st.error(f"Error querying view {view_name}: {err}")
    finally:
        if conn:
            conn.close()

def get_db_metrics():
    """Fetches key metrics for the Dashboard and Sidebar."""
    conn = get_db_connection()
    if not conn: return {'TotalBooks': 0, 'Issued': 0, 'Overdue': 0, 'Patrons': 0}
    
    metrics = {}
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT IFNULL(SUM(total_copies), 0) FROM Book")
        metrics['TotalBooks'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(loan_id) FROM Loan WHERE return_date IS NULL")
        metrics['Issued'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT patron_id) FROM Patron")
        metrics['Patrons'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM V_OVERDUE_BOOKS")
        metrics['Overdue'] = cursor.fetchone()[0]
        
    except Exception as e:
        print(f"Error fetching metrics: {e}")
    finally:
        if conn: conn.close()
    
    return metrics

# --- Streamlit Setup & Sidebar ---

st.set_page_config(
    page_title="LMS: Library Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

metrics = get_db_metrics()

st.sidebar.title("📚 Library System")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "📘 Books", "👤 Patrons", "🔄 Loans", "📊 Reports"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Quick Stats")
st.sidebar.metric("Total Inventory", metrics['TotalBooks'])
st.sidebar.metric("Books Issued", metrics['Issued'])
st.sidebar.metric("Active Patrons", metrics['Patrons'])
st.sidebar.metric("Overdue Alerts", metrics['Overdue'], delta=metrics['Overdue'], delta_color="inverse")

st.sidebar.markdown("---")


# -----------------------------------------------------------------------------
# 🏠 1. DASHBOARD PAGE
# -----------------------------------------------------------------------------

if page == "🏠 Dashboard":
    st.title("Dashboard: Library Overview")

    # Key metrics (cards)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Inventory", metrics['TotalBooks'])
    col2.metric("Active Loans", metrics['Issued'])
    col3.metric("Registered Patrons", metrics['Patrons'])
    col4.metric("🚨 Overdue Books", metrics['Overdue'], delta_color="inverse")

    st.markdown("---")

    st.subheader("Critical Alert: Overdue Books (Top 5)")
    display_report_results("V_OVERDUE_BOOKS", "LIMIT 5")
    
    st.markdown("---")
    
    st.subheader("Recent Checkout Activity")
    display_report_results("V_CURRENT_LOANS", "ORDER BY checkout_date DESC LIMIT 5")


# -----------------------------------------------------------------------------
# 📘 2. BOOKS PAGE
# -----------------------------------------------------------------------------

elif page == "📘 Books":
    st.title("Book Management")

    st.subheader("Add New Book & Inventory (ISBN Sync)")
    col_isbn, col_copy = st.columns([2, 1])
    
    with col_isbn:
        isbn_input = st.text_input("ISBN (10 or 13 digits)", key="isbn_sync").strip()
    with col_copy:
        copies_input = st.number_input("Copies to Add", min_value=1, value=1, key="copies_count")
        
    submitted = st.button("Sync & Add Inventory")
    
    if submitted and isbn_input:
        with st.spinner(f"Syncing book metadata for {isbn_input}..."):
            if search_and_sync_book_by_isbn(isbn_input):
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        # Update inventory directly after successful sync
                        update_sql = """
                        UPDATE Book
                        SET total_copies = total_copies + %s, available_copies = available_copies + %s
                        WHERE isbn = %s
                        """
                        cursor.execute(update_sql, (copies_input, copies_input, isbn_input))
                        conn.commit()
                        st.success(f"✅ Successfully synced '{isbn_input}' and added {copies_input} copies to inventory!")
                    except Exception as e:
                        st.error(f"Failed to update inventory: {e}")
                    finally:
                        conn.close()
            else:
                st.error("❌ Failed to sync book metadata.")

    st.markdown("---")
    st.subheader("Current Book Inventory")
    display_report_results("Book", "ORDER BY title ASC")


# -----------------------------------------------------------------------------
# 👤 3. PATRONS PAGE
# -----------------------------------------------------------------------------

elif page == "👤 Patrons":
    st.title("Patron Management")

    tab_reg, tab_view = st.tabs(["➕ Register New Patron", "📋 View All Patrons"])
    
    with tab_reg:
        st.subheader("Patron Registration Form")
        with st.form("patron_registration_form"):
            reg_first_name = st.text_input("First Name")
            reg_last_name = st.text_input("Last Name")
            reg_email = st.text_input("Email Address (Unique)")
            
            register_button = st.form_submit_button("REGISTER PATRON")
            
            if register_button:
                if reg_first_name and reg_last_name and reg_email:
                    if register_patron(reg_first_name.strip(), reg_last_name.strip(), reg_email.strip()):
                        st.success(f"🎉 Success! Patron {reg_first_name} {reg_last_name} registered.")
                    else:
                        st.error("❌ Registration failed. Check if the email already exists or DB is running.")
                else:
                    st.warning("Please fill in all required fields.")

    with tab_view:
        st.subheader("All Registered Patrons")
        display_report_results("Patron", "ORDER BY last_name ASC")


# -----------------------------------------------------------------------------
# 🔄 4. LOANS PAGE
# -----------------------------------------------------------------------------

elif page == "🔄 Loans":
    st.title("Loan Operations (Issue, Return, Fines)")
    
    tab_issue, tab_return, tab_active = st.tabs(["📤 Issue Book", "📥 Return Book", "💸 Outstanding Fines"])
    
    # --- ISSUE BOOK TAB (Patron Lookup + Checkout) ---
    with tab_issue:
        st.subheader("1. Find Patron by Email")

        # Initialize session state for the patron lookup result
        if 'patron_info' not in st.session_state:
            st.session_state['patron_info'] = None
        # Initialize session state for the book search query (persists across runs)
        if 'checkout_book_search_val' not in st.session_state:
            st.session_state['checkout_book_search_val'] = ''

        # --- LOOKUP FORM (Only handles the email lookup) ---
        with st.form("patron_lookup_form_final"):
            lookup_email = st.text_input("Enter Patron Email", key="lookup_email_final", value=st.session_state.get('lookup_email_val', '')).strip()
            st.session_state['lookup_email_val'] = lookup_email # Keep email value after submit

            lookup_button = st.form_submit_button("FIND PATRON")
            
            if lookup_button and lookup_email:
                info = find_patron_by_email(lookup_email)
                st.session_state['patron_info'] = info
                if info:
                    # Store email for updates if found
                    info['email'] = lookup_email
                    st.session_state['patron_info'] = info
                
        # --- CHECKOUT ACTION (OUTSIDE the lookup form) ---
        
        if st.session_state['patron_info']:
            info = st.session_state['patron_info']
            
            st.success(f"Patron Found: {info['first_name']} {info['last_name']}")
            
            col1_m, col2_m = st.columns(2)
            with col1_m:
                st.metric(label="Patron ID", value=info['patron_id'])
            with col2_m:
                st.metric(label="Active Loans", value=info['active_loans'])
            
            st.markdown("---")
            st.subheader("2. Complete Checkout Transaction")
            
            # --- Dynamic Book Search Input ---
            st.session_state['checkout_book_search_val'] = st.text_input(
                "Search Book by Title or ISBN:", 
                key="checkout_book_search", 
                value=st.session_state['checkout_book_search_val']
            ).strip()
            
            # Perform the search dynamically based on the input
            available_books = search_available_books(st.session_state['checkout_book_search_val'])

            # --- Checkout Form (Uses search results) ---
            with st.form("checkout_transaction_form"): 
                st.write(f"Issuing book to Patron ID: **{info['patron_id']}**")

                if not available_books:
                    book_options = ["(No available books found matching search)"]
                    book_map = {}
                else:
                    # Map the display string to the actual ISBN
                    book_options = [
                        f"{book['title']} (ISBN: {book['isbn']}) | Copies: {book['available_copies']}"
                        for book in available_books
                    ]
                    book_map = {
                        option: book['isbn'] 
                        for option, book in zip(book_options, available_books)
                    }

                # Select box for the user to pick from the results
                selected_book_display = st.selectbox(
                    "Choose Book to Issue",
                    book_options,
                    key="selected_book_to_issue"
                )
                
                checkout_button = st.form_submit_button("CHECK OUT BOOK (Transaction)") 
                
                if checkout_button and selected_book_display != "(No available books found matching search)":
                    co_isbn = book_map.get(selected_book_display)
                    
                    if co_isbn and checkout_book(co_isbn, info['patron_id']):
                        st.success(f"🎉 Success! Book checked out: {co_isbn}.")
                        # Update metrics and rerun using the stored email
                        st.session_state['patron_info'] = find_patron_by_email(info['email']) 
                        st.rerun() 
                    else:
                        st.warning("Checkout failed. Check inventory or patron status.")
                elif checkout_button:
                    st.error("Please select a valid book with available copies.")
        
        elif lookup_button and not st.session_state.get('patron_info'):
            st.error("❌ Patron not found with that email.")


    with tab_return:
        st.subheader("Handle Book Return")
        
        # --- Step 1: Input Patron ID ---
        with st.form("return_patron_lookup_form"):
            ret_patron_id = st.number_input(
                "1. Enter Patron ID", 
                min_value=1, 
                step=1, 
                key="ret_patron_id_lookup"
            )
            lookup_loans_button = st.form_submit_button("Find Books on Loan")

        # --- Step 2: Display and Select Book (Only runs after button is clicked) ---
        
        if lookup_loans_button:
            # Fetch the list of active loans
            active_loans = get_patron_active_loans(int(ret_patron_id))

            if not active_loans:
                st.info(f"Patron ID {ret_patron_id} has no active loans or does not exist.")
            else:
                # Store the loans and the patron ID in session state for the return form
                st.session_state['active_loans'] = active_loans
                st.session_state['return_patron_id'] = ret_patron_id
                st.success(f"{len(active_loans)} book(s) found on loan for Patron ID {ret_patron_id}.")
        
        # --- Step 3: The Return Form (Always visible if loans are found) ---
        
        if 'active_loans' in st.session_state and st.session_state['active_loans']:
            st.markdown("---")
            st.subheader("2. Select Book to Return")

            # Create a list of display strings (Title - ISBN) for the dropdown
            loan_options = [
                f"{loan['title']} (ISBN: {loan['isbn']})"
                for loan in st.session_state['active_loans']
            ]
            
            selected_loan_display = st.selectbox(
                "Choose the Book to Return",
                loan_options,
                key="selected_loan_key"
            )
            
            # The chosen ISBN is extracted from the display string
            # Finds the ISBN portion: (ISBN: XXXXXXXXXXXXX) and extracts the number
            selected_isbn = selected_loan_display.split(' (ISBN: ')[1].rstrip(')')

            return_button = st.button("CONFIRM RETURN TRANSACTION", key="final_return_button")
            
            if return_button:
                patron_id_to_return = st.session_state['return_patron_id']

                if return_book(selected_isbn, int(patron_id_to_return)):
                    st.success(f"📘 Success! Book '{selected_loan_display}' returned by Patron {patron_id_to_return}.")
                    # Clear session state and rerun to update the list immediately
                    del st.session_state['active_loans'] 
                    st.rerun() 
                else:
                    st.error("Return failed. Please check the database connection.")
        # End of tab_return

    # --- OUTSTANDING FINES TAB ---
    with tab_active:
        st.subheader("Outstanding Fines Report")
        display_report_results("V_OUTSTANDING_FINES")
        
        # --- Fine Payment Action ---
        st.markdown("---")
        st.caption("Future feature: Implement fine payment logic here.")


# -----------------------------------------------------------------------------
# 📊 5. REPORTS PAGE
# -----------------------------------------------------------------------------

elif page == "📊 Reports":
    st.title("System Reports")

    report_option = st.selectbox(
        "Select a Specific Report to View",
        [
            "V_CURRENT_LOANS", 
            "V_OVERDUE_BOOKS", 
            "V_OUTSTANDING_FINES",
            "V_POPULAR_BOOKS", 
            "V_PATRON_HISTORY"
        ]
    )
    
    report_filter = ""
    if report_option == "V_PATRON_HISTORY":
        patron_id = st.number_input("Enter Patron ID for History (Optional)", min_value=1, step=1, key="report_patron_id")
        if patron_id:
            report_filter = f"WHERE patron_id = {patron_id}"

    if st.button(f"Generate Report: {report_option}", use_container_width=True):
        display_report_results(report_option, report_filter)