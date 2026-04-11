[DjangoProject.com](https://www.djangoproject.com/)

Django framework for web develoment.

- Python based
- built-in admin panel ready to use
- easy integration with internal Sqlite or external database

## Working on Django by cloning a project from a repo (for Linux, see guide for Windows below)

1. git clone
2. cd project
3. python -m venv venv
4. activate venv
5. pip install -r requirements.txt
7. edit .env
8. python manage.py migrate
10. python manage.py runserver

Longer version:

1. Clone the repo to where you want it: ``git repo``.
2. Go to the project folder (it's the one with manage.py)
3. Create a virtual environment, for example ``python -m venv venv``
4. Activate virtual environment, for example ``source venv/bin/activate``
5. Install Django and dependencies inside virtual environment ``pip install -r requirements.txt``
6. Fill the .evn file with appropriate variables
7. Run migrations ``python manage.py migrate``
8. Run the development server ``python manage.py runserver``

Fill .env file with the appopriate information

In terminal, do ``python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`` and then copy this into the SECRET_KEY in .env file. This is only for your local project, so it could be also just some random string, but the SECRET_KEY cannot be empty. SECRET_KEY for production is only on the server.

ALLOWED_HOSTS need to be localhost,127.0.0.1 for you to be able to run the development server in your localhost

**The guide incomplete, need to add database info etc**

```
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1


DB_ENGINE=django.db.backends.postgresql
DB_NAME=youproject
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

## Django + PostgreSQL Setup Guide (for Windows, by ChatGPT, not tested by humans)

### Prerequisites

* PostgreSQL is already installed and running
* Git is installed
* Python is installed

---

### 1. Clone the repository

```bash
git clone <repo-url>
cd <repo-folder> 
```
repo-folder = the one with manage.py

---

### 2. Create and activate virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Django is included in requirements.txt.

---

### 4. Create the database and user (PostgreSQL)

Open **SQL Shell (psql)** and run:

```sql
CREATE DATABASE myproject;

CREATE USER myuser WITH PASSWORD 'mypassword';

ALTER ROLE myuser SET client_encoding TO 'utf8';
ALTER ROLE myuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE myuser SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE myproject TO myuser;
```

Exit:

```sql
\q
```

---

### 5. Set up environment variables

Copy the example file:

```bash
copy .env.example .env
```

Edit `.env` and set values:

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

SECRET_KEY=generate-your-own

DB_NAME=myproject
DB_USER=myuser
DB_PASSWORD=mypassword
DB_HOST=localhost
DB_PORT=5432
```

---

### 6. Apply migrations

```bash
python manage.py migrate
```

---

### 7. (Optional) Create superuser

```bash
python manage.py createsuperuser
```

---

### 8. Run development server

```bash
python manage.py runserver
```

Open in browser:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

#### Common Issues

#### PostgreSQL connection errors

* Ensure PostgreSQL service is running
* Check username/password in `.env`

#### psycopg2 issues

```bash
pip install psycopg2-binary
```
This shouldn't be an issue, though, because psycopg2-binary is included in the requirements.txt.

#### Bad Request (400)

* Check `ALLOWED_HOSTS` includes `localhost` and `127.0.0.1`

---

#### Notes

* Do NOT commit `.env`
* Ensure `venv/` is in `.gitignore`
* Each developer uses their own `.env`


## Django installation for own project (for Linux)

First, create a folder where you want to keep your project.

1. Create a virtual environment, for example

``python3 -m venv env``  

2. Activate environment:

``source env/bin/activate``

3. Check that you're using the pip in your virtual environment:

``which pip``

If you don't see env in the path, something's wrong (don't install Django until it's fixed).


4. Install Django

``pip install django`` 

### Creating a project

Activate virtual environment, and then:

``django-admin startproject yourproject yourdirectory`` 

(The directory structure is easy to get messy, so try to choose names that help you understand what is the project, what is the project folder, the apps etc.)


### Running the development server

Note: Never expose the development server to the public.

``python manage.py runserver``

Go to http://127.0.0.1:8000/ in your web browser. You should see the Django web page.


### Creating an admin user

``python manage.py createsuperuser``

Add your info and choose a password.

Make sure the development server is running and go to http://127.0.0.1:8000/admin/.

You should now be able to log in.

### Components of Django

#### models.py
https://docs.djangoproject.com/en/6.0/topics/db/models/

Models contain the fields for your data in the database. One model maps to one database table.

Models are Python subclasses of django.db.models.Model.

Django creates all models an auto-incrementing primary key. This can be overriden by specifying "primary_key = True" in one of the fields.

#### settings.py

Holds the settings for your database, time zone etc.

#### views.py

Views are Python functions that take a web request and return a web rensponse.

The response can be written in HTML in the function, or you can also create separate templates (html pages), that are rendered for the request.

#### Templates

Templates are (usually) HTML pages, that you can use to create your web pages in Django. When a view gets a specific request, it will render the approriate template.

Templates use Django template language https://docs.djangoproject.com/en/6.0/ref/templates/language/, which enables you to interact with the user and present information from the database.

You can also create a base HTML page with navigation bar etc, and then embed that to the other templates.



