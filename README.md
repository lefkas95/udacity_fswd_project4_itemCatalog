# Item Catalog

## Description

This project serves an item catalog as a web application. It shows different categories and items assigned to them. At the main page you
ca see the latest added items. Additionally it is possible to login using a google account in order to create new items. It is also possible to
edit or delete self added items.

The project also holds a script to create a proper database and another script which loads initial data into the database (see section 'Run it').

## Requirements

Please install the following programs (if not done before) in order to be able to use the item catalog:

* Vagrant - Deployment tool (https://www.vagrantup.com/)
* VirtualBox - A virtual maschine (https://www.virtualbox.org/)

## Run it

In order to run the program you will have to setup the database behind. First start the VM:
Go into the `vagrant` folder and execute the command `vagrant up`. Afterwards connect to the VM using `vagrant ssh`.

Now navigate to the project folder using `cd /vagrant/catalog` and set up the database with the command `python database_setup.py`.
Afterwards load the initial data using `python loadData.py`. Now you can start the application with the command `python application.py`.

There must be an active postgresql database on the machine in order to work!
In order to enable a login via OAuth with Google register a web app at developer.google.com, define `http://localhost:5000` as Authorised JavaScript origins
and `http://localhost:5000/postmessage` as Authorised redirect URIs. Afterwards download the credentials and store the JSON file in the project-folder
(same level as `application.py`) with the name `client_secrets.json`.
You can now access the application via a web browser under `http://localhost/5000`

## API Endpoints

The application also has the following endpoints to fetch JSON data from the app:

* `http://localhost:5000/api/categories` - Shows all categories
* `http://localhost:5000/api/categories/<<category name>>/items` - Shows all items assigned to a given category
* `http://localhost:5000/api/categories/<<category name>>/items/<<item name>>` - shows detail information about a given item