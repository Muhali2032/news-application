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
- Email notification processing for readers subscribed to an article's journalist or publisher.
- Webhook integration when an article is approved.
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

Configure the required environment variables in a local `.env` file. Do not commit this file or share its credentials.

The database settings must match the MariaDB database configuration.

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
python manage.py test news -v 2
```

The tests cover role-based access, article creation and approval, subscriptions, newsletter operations and notification integration.

## 9. Security and Configuration

- Environment variables are used for sensitive configuration.
- Token authentication is configured for the REST API.
- Role-based permissions restrict access to protected operations.
- The `.env` file and local database backups must not be included in public submissions.

## 10. Design Documentation

The `docs/` directory is intended to contain the system design diagrams and supporting technical documentation.
