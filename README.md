# Purpose
<p>This repo will be for the CSE 545 Team #3 Software Security course project</p>
<p>jvutukur - first push</p>
<p>garrettgutierrezasu- second push</p>

# Environment
* Operating System: Ubuntu 14.04 LTS
* Framework: Django 1.10
* Language: Python 2.7.12
* Database: MySQL Community Server 2.7.15

# Install Python
1. Install required packages
  * sudo apt-get install build-essential checkinstall
  * sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev

2. Download Python
  * cd /usr/src
  * wget https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz

3. Extract downloaded package
  * tar xzf Python-2.7.12.tgz

4. Compile Python Source
  * cd Python-2.7.12
  * sudo ./configure
  * sudo make altinstall

5. Check Python version
  * python2.7 -V

# Install PIP
  * sudo apt-get install python-pip python-dev build-essential
  * sudo pip install --upgrade pip
  * sudo pip install --upgrade virtualenv

# Install MySQL
1. Download deb for 2.7.15
  * wget http://dev.  * mysql.com/get/mysql-apt-config_0.6.0-1_all.de

2. Install using dpkg
  * sudo dpkg -i mysql-apt-config_0.6.0-1_all.deb

3. Update System
  * sudo apt-get update

4. Install MySQL Server
  * sudo apt-get install mysql-server

5. Create root password

6. Optional: configure secure installation
  * sudo mysql_secure_installation

7. Check status
  * service mysql status

8. Install connection for Django client
  * sudo apt-get install python-dev libmysqlclient-dev
  * pip install MySQL-python

# How to clone repository
1. Go to directory where you want you project to live
  * cd <path>/<destination_folder>
  * Ex: cd home/GitHub

2. Clone the repository
  * git clone https://github.com/jgutbub/CSE_545

# How I set up the project
1. Create django project
  * django-admin startproject group3_sbs
  * cd group3_sbs

2. Create the login application within project
  * python manage.py startapp login

3. Install new application
  1. Open group3_sbs/group3_sbs/settings.py
  2. Go to variable INSTALLED_APPS
  3. Add 'login', at end of list before ]

4. Setup database connection
  1. Create database in MySQL
    1. Login using username and password
      * mysql -u <USERNAME> -P
      * Enter password when prompted
    2. CREATE DATABASE group3_sbs;
    3. quit;
  2. Open group3_sbs/group3_sbs/settings.py
  3. Go to variable DATABASES
  4. Change it to look like the following:
    * DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'group3_sbs',
        'USER': 'root',
        'PASSWORD': '<YOUR_PASSWORD>',
        'HOST': 'localhost',
        'PORT': 3306'',
    }
  }

5. Configure cookie settings
  1. Open group3_sbs/group3_sbs/settings.py
  2. Add the following to the bottom of the file:
    * SESSION_COOKIE_AGE = 600
    * SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    * SESSION_SAVE_EVERY_REQUEST = True

6. Create templates for holding HTML files. Django looks for a folder called templates in your app and uses the additional appname folder to prevent confusion from different HTML files.
  1. cd group3_sbs/login
  2. mkdir -p templates/login
    * Add html files to group3_sbs/login/templates/login
    * For this example, I added signin.html

7. Create static for holding static files (e.g. .css, images, .js).
  1. cd group3_sbs/login
  2. mkdir -p static/login
    * Add css files here
  3. mkdir -p static/login/images
    * Add images here
  4. mkdir -p static/login/js
    * Add js files here

8. Render views views
  1. Open group3_sbs/login/views.py
    * A function can be used to create a view
  2. Import necessary libraries
    * from django.http import HttpResponse, Http404, HttpResponseRedirect
      * from django.template import loader
      * from django.shortcuts import render
      * from django.urls import reverse
      * from django.contrib.auth.models import User
      * from django.contrib.auth import authenticate, login, logout
      * from django.contrib.auth.decorators import login_required, user_passes_test
  3. Create default view
    * def index(request):
      * if request.user.is_authenticated:
        * return HttpResponse('You are already logged in')
      * else:
        * return render(request, 'login/signin.html)

9. Route views to a URI
  1. Open group3_sbs/group3_sbs/urls.py
    * All routing for this project is done here
    * Add url(r'^login/', include('login.urls')), in the urlpatterns variable
  2. Open group3_sbs/login/urls.py
  3. Give the urls a namespace
    * Add app_name='login' one line above variable url_patterns
  4. Make URL for index by making URL pattens look like this:
    * urlpatterns = [
      url(r'^$', views.index, name='signin'),
    ]

10. Create user
  1. python manage.py shell
    * from django.contrib.auth.models import User
    * user = User.objects.create_user(username="<USERNAME>", email="<EMAIL>", password="<PASSWORD>")
    * user.save()
    * exit()

11. Make database tables
  1. python manage.py makemigrations
  2. python manage.py migrate

12. Run the server
  1. cd group3_sbs
  2. python manage.py runserver 8000

11. Open localhost:8000/login in your web browser

# To be continued
