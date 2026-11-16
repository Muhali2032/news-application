# News Application

## 1. Project Overview

The News Application is a Django-based web application that allows readers to access articles written by independent journalists and publishers. It supports three user roles: Readers, Editors and Journalists.

The application provides article management, editorial approval, publisher and journalist subscriptions, newsletters and a REST API.

The project uses Django, Django REST Framework and MariaDB.

## 2. User Roles

| Role | Responsibilities |
|---|---|
| Reader | View approved articles and newsletters and access subscribed content through the API. |
| Journalist | Create and manage articles and create or manage their own newsletters. |
| Editor | Review and approve articles, manage articles and create or manage newsletters. |

## 3. Main Features

- User authentication and role-based access.
- Article creation, viewing, editing and deletion.
- Editorial approval before articles are published.
- Support for independent journalists and publisher-associated articles.
- Publisher and journalist subscription relationships.
- Newsletter creation and management.
- Email notification processing for readers subscribed to an article's journalist or publisher, using Django's console email backend for development.
- Local API webhook integration that receives a request when an article is approved.
- REST API with token authentication.
- Automated tests for important application workflows.

## 4. Database Design

The application uses four main models:

- **User:** Extends Django's AbstractUser and includes a role field and subscription relationships.
- **Publisher:** Stores publisher information and links editors and journalists to publications.
- **Article:** Stores article content, author, optional publisher, creation date and approval status.
- **Newsletter:** Stores newsletter information and links curated articles to the newsletter.

MariaDB is used as the configured database.

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
├── screenshots/
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

- Python
- Django
- Django REST Framework
- MariaDB
- Docker Desktop (if using the provided MariaDB container configuration)

### Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install project dependencies:

```bash
pip install -r requirements.txt
```
Create a `.env` file in the project root with the following environment variables:

- `DJANGO_SECRET_KEY`: A securely generated Django secret key.

Generate a new key using:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- `DB_PASSWORD`: The password for the MariaDB database user.

The application is configured to connect to MariaDB using:

- Database name: `news_application`
- Database user: `news_user`
- Host: `127.0.0.1`
- Port: `3307`

Ensure MariaDB is running and the database and user have been created before applying migrations. The `.env` file contains sensitive information and must never be committed to GitHub.

Apply database migrations:

```bash
python manage.py migrate
```

Run system checks:

```bash
python manage.py check
```

Start the development server:

```bash
python manage.py runserver
```

Open the application at:

`http://127.0.0.1:8000/`

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
