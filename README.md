# 📚 OpenShelf (DBMS Project)

**OpenShelf (DBMS Project)** is a modern **Library Management System** built with a clean API-first approach. It allows seamless management of books, users, and transactions while being scalable, modular, and developer-friendly.

Designed for learning, showcasing backend skills, and real-world extensibility — not just another CRUD toy.

---

## ✨ Features

* 📖 Book management (add, update, delete, search)
* 👤 User/member management
* 🔄 Issue & return tracking
* 🔍 Search and filter support
* 🌐 RESTful API design
* 🗄️ Database-backed persistence
* 🎯 Clean, modular project structure

---

## 🛠️ Tech Stack

* **Backend:** Python (Flask-based API)
* **Database:** MySQL
* **DB Connectivity:** mysql-connector-python
* **API Style:** REST
* **Frontend (optional):** Streamlit
* **Version Control:** Git & GitHub

---

## 🗄️ Database Details

The project uses **MySQL 8.x** as the relational database. The schema is designed with proper normalization, primary keys, foreign keys, views, and constraints to ensure data integrity and real-world usability.

---

### 📌 Database Name

```sql
library_management_db
```

---

### 👤 Database User

A dedicated MySQL user is created for the application:

```text
Username: library_user
Host: localhost
Privileges: ALL on library_management_db
```

---

### 📚 Core Tables

#### 1️⃣ `Book`

Stores book metadata and inventory information.

| Column           | Type             | Description                |
| ---------------- | ---------------- | -------------------------- |
| isbn             | VARCHAR(13) (PK) | Unique book identifier     |
| title            | VARCHAR(255)     | Book title                 |
| publication_year | YEAR             | Year of publication        |
| publisher        | VARCHAR(100)     | Publisher name             |
| total_copies     | INT              | Total copies owned         |
| available_copies | INT              | Copies currently available |

---

#### 2️⃣ `Author`

Stores unique authors.

| Column      | Type         | Description       |
| ----------- | ------------ | ----------------- |
| author_id   | INT (PK)     | Author identifier |
| author_name | VARCHAR(150) | Author name       |

---

#### 3️⃣ `Book_Author`

Implements **many-to-many** relationship between books and authors.

| Column    | Type                 | Description   |
| --------- | -------------------- | ------------- |
| isbn      | VARCHAR(13) (PK, FK) | Linked book   |
| author_id | INT (PK, FK)         | Linked author |

---

#### 4️⃣ `Patron`

Stores library member details.

| Column     | Type         | Description          |
| ---------- | ------------ | -------------------- |
| patron_id  | INT (PK)     | Member ID            |
| first_name | VARCHAR(50)  | First name           |
| last_name  | VARCHAR(50)  | Last name            |
| email      | VARCHAR(100) | Unique email address |

---

#### 5️⃣ `Loan`

Tracks book issue and return transactions.

| Column        | Type             | Description          |
| ------------- | ---------------- | -------------------- |
| loan_id       | INT (PK)         | Loan transaction ID  |
| isbn          | VARCHAR(13) (FK) | Issued book          |
| patron_id     | INT (FK)         | Borrowing patron     |
| checkout_date | DATE             | Date of issue        |
| due_date      | DATE             | Due date             |
| return_date   | DATE             | NULL if not returned |

---

#### 6️⃣ `Fine`

Stores overdue fine information.

| Column       | Type         | Description       |
| ------------ | ------------ | ----------------- |
| fine_id      | INT (PK)     | Fine ID           |
| loan_id      | INT (FK)     | Related loan      |
| fine_amount  | DECIMAL(5,2) | Fine amount       |
| fine_date    | DATE         | Date fine applied |
| payment_date | DATE         | NULL until paid   |

---

#### 7️⃣ `Api_Cache`

Caches external API responses (e.g., book metadata).

| Column       | Type             | Description         |
| ------------ | ---------------- | ------------------- |
| isbn         | VARCHAR(13) (PK) | Book ISBN           |
| api_response | JSON             | Cached API response |
| cached_at    | DATETIME         | Cache timestamp     |

---

### 👁️ Database Views

The following **views** are created for simplified querying and reporting:

* **`V_CURRENT_LOANS`** → Active (non-returned) book loans
* **`V_OVERDUE_BOOKS`** → Loans past due date with overdue days
* **`V_POPULAR_BOOKS`** → Books ordered by borrow count
* **`V_PATRON_HISTORY`** → Complete borrowing history per patron
* **`V_OUTSTANDING_FINES`** → Unpaid fines with patron and book details

------|------|------------|
| book_id | INT (PK) | Unique book identifier |
| title | VARCHAR | Book title |
| author | VARCHAR | Author name |
| category | VARCHAR | Genre / category |
| available | BOOLEAN | Availability status |

#### 2️⃣ `patrons`

Stores library member information.

| Column    | Type     | Description      |
| --------- | -------- | ---------------- |
| patron_id | INT (PK) | Unique member ID |
| name      | VARCHAR  | Member name      |
| email     | VARCHAR  | Contact email    |

#### 3️⃣ `loans`

Tracks issued and returned books.

| Column      | Type     | Description         |
| ----------- | -------- | ------------------- |
| loan_id     | INT (PK) | Loan transaction ID |
| book_id     | INT (FK) | Issued book         |
| patron_id   | INT (FK) | Borrowing member    |
| issue_date  | DATE     | Issue date          |
| return_date | DATE     | Return date         |

---

## 📂 Project Structure

````text
DBMS_PROJECT/
│
├── app.py              # Main application entry point
├── main.py             # Alternative runner / testing entry
├── app1.py             # Experimental / backup app file
│
├── api_handler.py      # API route handling & request logic
├── db_connector.py     # Database connection & configuration
├── patron_logic.py     # Library member (patron) operations
├── loan_logic.py       # Issue / return / loan tracking logic
├── sync_logic.py       # Data consistency & sync handling
│
├── __pycache__/        # Python cache files
└── README.md
---

## 🚀 Getting Started

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/OpenShelf (DBMS Project).git
cd OpenShelf (DBMS Project)
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Database

* Create the database
* Update credentials in `db_connector.py`

### 4️⃣ Run the Server

```bash
python app.py
```

Server will start locally 🚀

---

## 🔌 API Endpoints (Sample)

| Method | Endpoint      | Description         |
| ------ | ------------- | ------------------- |
| GET    | `/books`      | Fetch all books     |
| POST   | `/books`      | Add a new book      |
| PUT    | `/books/{id}` | Update book details |
| DELETE | `/books/{id}` | Remove a book       |

---

## 📈 Future Enhancements

* 🔐 Authentication & role-based access
* 📊 Analytics dashboard
* 📚 Book recommendations
* ☁️ Cloud deployment
* 📱 Frontend UI expansion

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.
Feel free to fork this repo and submit a PR.

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 💡 Why OpenShelf (DBMS Project)?

Because good systems are built like good libraries:
structured, accessible, and meant to grow.

Happy coding 🚀
