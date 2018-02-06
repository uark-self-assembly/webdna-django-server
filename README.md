# WebDNA Django Server

This repository holds the Django Server running the WebDNA backend. It is an open-source project under active development at the University of Arkansas.

WebDNA is a user-centric software designed around the [oxDNA](https://dna.physics.ox.ac.uk/index.php/Main_Page) simulation software. This API serves as the view to a managed simulation environment, featuring user accounts, custom data manipulation (via Python scripts), and much more.

## For the Developers

We'll outline here what all is needed to get this server up and running on your machine.
There are two main components (so far):<br>
1. A PostgreSQL database server
2. This Django API

We'll set these things up in that order!

### PostgreSQL Database Server
1. First, install the PostgreSQL DB server on your machine. Depending on your machine, follow the instructions here to install <b>version 9.5 or 9.6</b>:
  * [macOS](https://www.codementor.io/engineerapart/getting-started-with-postgresql-on-mac-osx-are8jcopb)
  * [Windows](https://www.postgresql.org/download/windows/)
2. When you install PostgreSQL, make sure to create a database called "webdna" by running the following commands as a superuser in the psql prompt:
```
CREATE DATABASE webdna;
```
3. We will then create a "schema" to keep all of our WebDNA tables organized. Run:
```
CREATE SCHEMA webdna;
```
4. Now, run the following command to support UUIDs on this database:
```
CREATE EXTENSION "uuid-ossp";
```
5. Create a role (i.e. a "user") on your PSQL database called "django_server" by running the following command as a superuser in the psql prompt:
```
CREATE ROLE django_server WITH LOGIN PASSWORD 'dJAngO#SerVe!!!Pa$#!1*';
```
After that, run the following command to grant this user permissions to modify databases
```
GRANT ALL PRIVILEGES ON DATABASE webdna TO django_server;
```
Finally, grant usage of the webdna schema to the django_server user
```
GRANT USAGE ON SCHEMA webdna TO django_server;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA webdna TO django_server;
```
6. Refer to the database definitions in the [WebDNA Database Definitions Repository](https://gitlab.com/webdna/database-definition).
  You'll need to run the commands in those database definition files in the database according to the README in that repository. Continue with the steps here once you've done that.

### Django API
Well, to be honest, PostgreSQL was the hard part, because everybody has a different machine, but this is a bit easier. First, make sure you've got PyCharm Professional installed. If not, you can definitely still run this Python project, but for our team, we're sticking to an IDE that makes the development process a breeze.

1. Clone this repository to a conveniently located directory on your machine.
2. Open up PyCharm, click "Open Project", and open the cloned directory.
3. Pull up the Settings window: "File > Configure > Settings".
4. Go to the "Project: webdna_server" tab, then click "Project Interpreter".
5. If you don't have a project interpreter selected at the top, go ahead and select the Python interpreter on your system.
6. Click the green "+" button and search for/install the following packages:
  * Django
  * djangorestframework
  * psycopg2
7. Create a new configuration by clicking the "Configurations" drop-down in the top right.
  * In the configuration window, click the "+" on the far left and select "Django server".
  * Then, change the "Host" to "localhost". I would also name the configuration something pretty, like "Run Server".
8. All set! You should be able to click the big green "Run" button at the top right. Run a sample command in [Postman](https://www.getpostman.com/):

<img src="https://i.imgur.com/UEM00Kd.png" alt="Postman Example" style="width: 600px;" align="middle"/>

<br><br>
