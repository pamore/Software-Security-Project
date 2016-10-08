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

# Install Django
* sudo pip install django

# Install Django-Axes
* sudo pip install django-axes
  * See https://django-axes.readthedocs.io
  * Make sure to make migrations and then migrate after installing and setting up database scheme.

# Install PKI Dependencies
* sudo apt-get install python-m2crypto
  * See http://sheogora.blogspot.com/2012/03/m2crypto-for-python-x509-certificates.html or https://www.heikkitoivonen.net/m2crypto/api/

# How to clone repository
1. Go to directory where you want you project to live
  * cd <path>/<destination_folder>
  * Ex: cd home/GitHub

2. Clone the repository
  * git clone https://github.com/jgutbub/CSE_545
