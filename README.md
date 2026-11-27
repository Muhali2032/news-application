# News Application

## 1. Project Overview

The News Application is a Django-based web application that allows readers to access articles written by independent journalists and publishers. It supports three user roles: Readers, Editors and Journalists.

The application provides article management, editorial approval, publisher and journalist subscriptions, newsletters and a REST API.

The project uses Django, Django REST Framework and MySQL.

## 2. User Roles

| Role | Responsibilities |
|---|---|
| Reader | View approved articles and newsletters and access subscribed content through the API. |
| Journalist | Create and manage independent articles, submit publisher articles for editorial approval, and create or manage their own newsletters. |
| Editor | Create and manage publishers, assign editors and journalists, review publisher articles, manage articles and create or manage newsletters. |

## 3. Main Features

- User authentication and role-based access.
- Article creation, viewing, editing and deletion.
- Independent journalist articles can be published immediately; publisher-associated articles require editorial approval.
- Support for independent journalists and publisher-associated articles.
- Publisher and journalist subscription relationships.
- Newsletter creation and management.
- Email notification processing for readers subscribed to an article's journalist or publisher, using Django's console email backend for development.
- Local API webhook integration that receives a request when an article is approved.
- REST API with token authentication.
- Automated tests for important application workflows.

### Publisher management and article publishing

1. Register an account and select the **Editor** role.
2. Log in as the Editor and open **Manage Publishers** in the navigation bar.
3. Select **Create Publisher**, enter the publisher name and description, and assign registered Editors and Journalists where applicable.
4. Save the Publisher. The Editor who creates it is automatically assigned to manage it.
5. The Editor can return to **Manage Publishers** to update the Publisher and its assigned members.
6. A Journalist can create an article and leave the Publisher field blank to publish it independently and immediately.
7. To submit an article for a publication, the Journalist selects an assigned Publisher. The article then remains pending until an Editor reviews and approves it.

Only Editors can create and manage Publishers. Journalists can submit articles only to Publishers to which they have been assigned.

## 4. Database Design

The application uses four main models:

- **User:** Extends Django's AbstractUser and includes a role field and subscription relationships.
- **Publisher:** Stores publisher information and links editors and journalists to publications.
- **Article:** Stores article content, author, optional publisher, creation date and approval status.
- **Newsletter:** Stores newsletter information and links curated articles to the newsletter.

MySQL is used as the configured database.

## 5. Application Structure

```text
news_application_project/
├── news/
│   ├── migrations/
│   ├── templates/
│   │   ├── news/
│   │   └── registration/
│   ├── admin.py
│   ├── api_urls.py
│   ├── api_views.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── news_project/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/
├── manage.py
├── requirements.txt
└── README.md
```

## 6. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/token/` | Obtain an authentication token |
| GET | `/api/articles/` | List approved articles |
| POST | `/api/articles/` | Create an article |
| GET | `/api/articles/subscribed/` | Retrieve articles from subscribed journalists and publishers |
| GET | `/api/articles/<id>/` | Retrieve an article |
| PUT | `/api/articles/<id>/` | Update an article |
| DELETE | `/api/articles/<id>/` | Delete an article |
| POST | `/api/articles/<id>/approve/` | Approve an article |
| GET | `/api/newsletters/` | List newsletters |
| POST | `/api/newsletters/` | Create a newsletter |
| GET | `/api/newsletters/<id>/` | Retrieve a newsletter |
| PUT | `/api/newsletters/<id>/` | Update a newsletter |
| DELETE | `/api/newsletters/<id>/` | Delete a newsletter |
| POST | `/api/approved/` | Receive an approved-article webhook |

API access is controlled through token authentication and role-based permissions.

## 7. Installation and Setup

### Requirements

- Python 3
- Django
- Django REST Framework
- MySQL
- Git
- A running MySQL server

### Step 1: Clone the Repository

Open a terminal and clone the GitHub repository:

```bash
git clone https://github.com/Muhali2032/news-application.git
```

Enter the project directory:

```bash
cd news-application
```

### Step 2: Create and Activate a Virtual Environment

Create a virtual environment inside the project directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### Step 3: Install Project Dependencies

Upgrade pip and install the required packages:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create your local environment file by copying the example file:

```bash
cp .env.example .env
```

Open `.env` and replace the example values with your own credentials:

- `DJANGO_SECRET_KEY`: A securely generated Django secret key.
- `DB_NAME`: The database name (`news_application` by default).
- `DB_USER`: The database username (`news_user` by default).
- `DB_PASSWORD`: The password you choose for the `news_user` database account.

Generate a Django secret key using:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key into the `DJANGO_SECRET_KEY` value in `.env`.

Do not commit `.env` to GitHub because it contains sensitive information. The `.env.example` file is provided as a template and should be included in the repository.

### Step 5: Create the Database and Database User

Make sure your MySQL server is running.

Log in to the database as the administrator:

```bash
mysql -u root -p
```

Enter your MySQL root password when prompted.

For a fresh installation, run the following SQL commands to create the application database and user. If the database or user already exists, do not recreate it; verify the existing configuration and permissions instead.

```sql
CREATE DATABASE news_application
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'news_user'@'127.0.0.1'
IDENTIFIED BY 'your_database_password';

GRANT ALL PRIVILEGES ON news_application.*
TO 'news_user'@'127.0.0.1';

FLUSH PRIVILEGES;
```

Replace `your_database_password` with the password you selected for the database user. Use that same password as the `DB_PASSWORD` value in your `.env` file.

The database settings in `news_project/settings.py` are configured as follows:

- Database name: `news_application`
- Database user: `news_user`
- Host: `127.0.0.1`
- Port: `3306`

If you use a different database name or username, update `DB_NAME` or `DB_USER` in your `.env` file to match.

Exit the database console:

```sql
EXIT;
```

### Step 6: Apply Database Migrations

Create the database tables by running:

```bash
python manage.py migrate
```

### Step 7: Run Django System Checks

Check that the project configuration is valid:

```bash
python manage.py check
```

### Step 8: Start the Development Server

Run the application:

```bash
python manage.py runserver
```

Open the application in your browser:

http://127.0.0.1:8000/


## 8. Running Automated Tests

Run the application tests using:

```bash
python manage.py test
```

The automated tests cover role-based access, article creation and approval, subscriptions, newsletter operations, and mocked notification integrations.

## 9. Security and Configuration

- Environment variables are used for sensitive configuration.
- Token authentication is configured for the REST API.
- Role-based permissions restrict access to protected operations.
- The `.env` file and local database backups must not be included in public submissions.

## 10. Design Documentation

The system design documentation is available in `docs/system_design.md`.

It includes:

- Use-case diagram showing the interactions between Readers, Editors and Journalists.
- Sequence diagram illustrating the article approval and notification process.
- Class diagram showing the main models and their relationships.

These diagrams provide an overview of the system structure, user interactions and database relationships.
