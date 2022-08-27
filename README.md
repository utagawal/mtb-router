# mtb-router

This project is intended to create  an API for Mountain Biking **automatic** map routing.

It should be based on a data source from MTB gpx files that will be used to supplement OSM with specific MTB data like path popularity.

Input :
* Departure coordinates
* Destination coordintates

Output :
* GPX file or geoJSON

Should be written in python

## Installation guide

- **Preparing the Database containing the OSM ways Data**

*This part is based on the otrouting installation guides, located in oprouting/.docx*

* install postgre, postgis, pgrouting :
https://proyectosbeta.net/2018/05/postgis-2-4-en-ubuntu-18-04-lts-bionic-beaver/
https://www.howtoinstall.me/ubuntu/18-04/postgresql-10-pgrouting/
```
apt update
apt install postgresql-10 postgresql-10-postgis-2.4 postgresql-10-postgis-scripts
apt install postgresql-10-pgrouting
```
* Create super user and db
https://docs.postgresql.fr/8.2/app-createuser.html
```
sudo -u postgres createuser -s -P user
# Enter password for new role: xxxxx
#Enter it again: xxxxx
sudo -u postgres createdb -O user db_osm
psql -h localhost -U user db_osm
# Password for user user: xxxxx
```
* Install phppgadmin
https://www.howtoforge.com/tutorial/ubuntu-postgresql-installation/#step-install-postgresql-phppgadmin-and-all-dependencies
Configure Apache Web Server
```
apt install phppgadmin
cd /etc/apache2/conf-available/
nano phppgadmin.conf
```
Configure phpPgAdmin
```
cd /etc/phppgadmin/
nano config.inc.php
```
Find the line '$conf['extra_login_security'] = true;' and change the value to 'false' so you can login to phpPgAdmin with user postgres.

restart the PostgreSQL and Apache2 services
```
systemctl restart postgresql
systemctl restart apache2
```
Open phppgadmin
https://www.opentraveller.net/phppgadmin/ or http://localhost/phppgadmin/
```
user: user
pwd: xxxxx
```
* Add postgis and pgrouting extension to db
Open db:
```
psql -h localhost -U user db_osm
# Password for user user: xxxxx

CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
```

- **OSM Data Import**

* Upload OSM Data
Upload osm.bz2 (for the oprouting part) and osm.pbf (used by graphhopper) file from http://download.geofabrik.de/
Example: http://download.geofabrik.de/europe/andorra-latest.osm.bz2
http://download.geofabrik.de/europe/andorra-latest.osm.pbf
```
wget -O andorra-latest.osm.bz2 "http://download.geofabrik.de/europe/andorra-latest.osm.bz2"
```
Place the .pbf file in *mtb-router/*, and the .bz2 file in *scripts/* and in *oprouting/otrouting_py/*.
* Install osm2pgsql
```
apt-get install osm2pgsql
```
Import osm data to db_osm db
```
osm2pgsql --slim -C 100 -d db_osm -U user -W -H localhost -P 5432 andorra-latest.osm.bz2
# Password: xxxxx
```
Configure .pgpass file so as to avoid to use password in the osm2pgsql line
https://linuxandryan.wordpress.com/2013/03/07/creating-and-using-a-pgpass-file/
```
cd ~
touch .pgpass
nano .pgpass
localhost:5432:db_osm:user:xxxxx
chmod 0600 .pgpass
osm2pgsql --slim -C 100 -d db_osm -U user -H localhost -P 5432 andorra-latest.osm.bz2
```
* Create db_osm_routing postgresql data base with postgis and pgrouting extension
```
sudo -u postgres createdb -O user db_osm_routing
psql -h localhost -U user db_osm
# Password for user user: xxxxx
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
```

- **Python**

The following extension are used:
```
import sys
import psycopg2
import time
import math
import os
import subprocess
import glob
import unicodedata
import importlib.util
import requests
import gpxpy
```
* Configure *oprouting/otrouting_py/otrouting_v1.3.py* by editing the following values:
Identification parameters to connect the database
```
glob_db = 'db_osm_routing'
glob_user = 'user'
glob_host = 'localhost'
glob_port = '5432'
glob_password = 'xxxxx'
```
A table of osm input data to be imported, data will be imported from http://download.geofabrik.de
osm input data shall be formatted as presented below:
```
http://download.geofabrik.de/europe/andorra.html →  ["europe", "andorra"]
glob_t_input = []
#http://download.geofabrik.de
#MONACO - ANDORRA ######################
glob_t_input.append(["europe", "andorra"])
#glob_t_input.append(["europe", "monaco"])
#FRANCE ###################################
#glob_t_input.append(["europe", "france", "alsace"])
#glob_t_input.append(["europe", "france", "aquitaine"])
#glob_t_input.append(["europe", "france", "auvergne"])
#glob_t_input.append(["europe", "france", "basse-normandie"])
```
* Configure the `scripts/___main___.py` file:
In the `___main___()` function, you can edit the following parameters:
url : the url to get the graphhopper mapmatching API (finishes with */match*)
precision : mtb-router also calculates the accuracy of graphhopper's map-matching API, by checking how far the original GPX is located from the OSM ways, within a buffer around the map matched GPX. The precision parameter is the distance around which mtb-router will look for the GPX route from the OSM way.
* Configure the `scripts/data_loader.sh` by editing the mtb-router location.

- **Initialize mtb-router**
Open `scripts/___main___.py`, uncomment the `___init___()` line and launch the script.

- **Configure the graphhopper server**
[Graphhopper developper documentation](https://github.com/graphhopper/graphhopper/blob/5.x/docs/core/quickstart-from-source.md)
Other informations are avaliable with the [Graphhopper documentation](https://github.com/graphhopper/graphhopper)
Change the module classpath with `mtbRouter`
use `com.mtb.router.MtbRouterApplication` as main class
Follow the documentation to start the Server.

- **Calculate the GPX weights**
Open `scripts/___main___.py`, uncomment the `___main___()` line and launch the script.

- **Calculate the GPX weights**


## Principles

![Best MTB OSM Router (2)](https://user-images.githubusercontent.com/16464382/158050010-ffe51e2e-8ae4-41ef-9e9d-bc3a23a7d2b0.jpg)

https://miro.com/app/board/uXjVONfUPfw=/?invite_link_id=416360118516

Should be using Docker containerisation

## Sample files

A file containing around 1200 GPX tracks from Isère and Rhône region in France is made available in an archive "sample-MTB-gpx-6938.zip"

## Dependencies

 - [PostGIS](https://github.com/utagawal/mtb-router/wiki/postgre-postgis-installation-and-OSM-data-import)
 - ogr2ogr
 - [Graphhopper](https://github.com/graphhopper/graphhopper)
