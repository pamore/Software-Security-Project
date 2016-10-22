# Purpose
<p>This repo will be for the CSE 545 Team 3 Software Security course project</p>
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
  * wget http://dev.mysql.com/get/mysql-apt-config_0.6.0-1_all.deb

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

# Auto Install Using Pip requirements.txts
* pip install -r requirements.txt

# Do the following sections if you choose not to use the requirements.txt

## Install Django
* sudo pip install django

## Install Django Templated email
* sudo pip install django-templated-email

## Install Django-Axes
* sudo pip install django-axes
  * See https://django-axes.readthedocs.io
  * Make sure to make migrations and then migrate after installing and setting up database scheme.

## Install PKI Dependencies
* sudo apt-get install python-m2crypto
  * See http://sheogora.blogspot.com/2012/03/m2crypto-for-python-x509-certificates.html or https://www.heikkitoivonen.net/m2crypto/api/

## Install Easy PDF
* pip install django-easy-pdf
* pip install "xhtml2pdf>=0.0.6" "reportlab>=2.7,<3"
  * See https://media.readthedocs.org/pdf/django-easy-pdf/latest/django-easy-pdf.pdf
  * See http://django-easy-pdf.readthedocs.io/en/stable/
  * See https://groups.google.com/forum/#!topic/django-users/0MUrSRh6fnQ

# How to clone repository
1. Go to directory where you want you project to live
     cd <path>/<destination_folder>
     Ex: cd home/GitHub

2. Clone the repository
     git clone https://github.com/jgutbub/CSE_545

     # How to Host Django on Apache using Ubuntu 14.04 LTS
     ## Create a virtualenv
     1. Install virtualenv


               sudo pip install virtualenv



     2. Create a virtualenv in the project folder assuming you have installed all pip and sudo apt-get packages globally


               cd CSE_545/group3_sbs
               virtualenv group3_sbs_projectenv --system-site-packages


     3. Enter the virutalenv if needed


               source group3_sbs_projectenv/bin/activate


     4. Exit from the virtualenv


               deactivate


     ## Collect Django Static Files
     1. Edit the static root where the files will be copied if needed


               vim CSE_545/group3_sbs/groupe_sbs/settings.py
               STATIC_ROOT = '/DESITNATION_OF_COLLECTED_FILES'


     2. Collect files


               python manage.py collect static


     3. Make the log files executable for some reason


               chmod -R 777 CSE_545/group3_sbs/logs/


     ## Setup Mod_wsgi
     1. Install mod_wsgi for python 2.7


               sudo apt-get install libapache2-mod-wsgi



     ## Setup Apache
     1. Check hostname


               hostname


     2. Update System


               sudo apt-get update && sudo apt-get upgrade


     3. Install Apache


               sudo apt-get install apache2 apache2-doc apache2-utils


     4. Edit Apache Config settings if needed


               cd /etc/apache2/
               vim apache2.conf


     5. Edit the sites_enabled


               cd /etc/apache2/sites-enabled/
               vim 000-default.conf
               Alias /static /home/garrett/Documents/GitHub/CSE_545/group3_sbs/static
               <Directory /home/garrett/Documents/GitHub/CSE_545/group3_sbs/static>
                        Require all granted
               </Directory>
               <Directory /home/garrett/Documents/GitHub/CSE_545/group3_sbs/log>
                        Require all granted
               </Directory>
               <Directory /home/garrett/Documents/GitHub/CSE_545/group3_sbs/group3_sbs>
                       <Files wsgi.py>
                               Require all granted
                       </Files>
               </Directory>
               WSGIDaemonProcess group3_sbs python-path=/home/garrett/Documents/GitHub/CSE_545/group3_sbs:/home/garrett/Documents/GitHub/CE_545/group3_sbs/group3_sbs_projectenv/lib/python2.7/site-packages
               WSGIProcessGroup group3_sbs
               WSGIScriptAlias / /home/garrett/Documents/GitHub/CSE_545/group3_sbs/group3_sbs/wsgi.py
