[DjangoProject.com](https://www.djangoproject.com/)

Django framework for web develoment.

- Python based
- built-in admin panel ready to use
- easy integration with internal Sqlite or external database

### Django installation

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



