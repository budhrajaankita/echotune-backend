# echotune-backend

## 1. Setup

### 1.1 Prerequisites

- Python 3.10
- PostgreSQL
- pip
- Virtual environment

### 1.2 Setup Steps

#### 1.2.1 Clone the Repository

```bash
git clone https://github.com/budhrajaankita/echotune-backend.git
```

#### 1.2.2 Create and Activate a Virtual Environment

- Navigate to the project directory and create a virtual environment:

```bash
python3 -m venv env
```

- Activate the virtual environment:

On macOS or Linux:

```bash
source env/bin/activate
```

On Windows:

```cmd
env\Scripts\activate.bat
```

#### 1.2.3 Install Required Python Packages

- Install all dependencies listed in the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

#### 1.2.4 Database Setup

- PostgreSQL Configuration
  - Ensure PostgreSQL is installed and running on your system. Create the necessary database and user (role):

```sql
CREATE DATABASE echotune_db;
CREATE USER echotune WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE echotune_db TO echotune;
```

#### 1.2.5 Apply Database Migrations

- With the virtual environment activated and database configured, apply the migrations to set up the database schema:

```bash
python manage.py migrate
```

#### 1.2.6 Run the Development Server

- Start the Django development server:

```bash
python manage.py runserver
```

The server should be running at `http://127.0.0.1:8000/`.
