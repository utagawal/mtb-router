#!/bin/sh
cd /srv/projects/mtb-router

# Load the GPX files in the db_osm_routing postgres database
for FILE in ./GPX/Matched_GPX/*.gpx; do ogr2ogr -skipfailures -update -append -f "PostgreSQL"  PG:"host="localhost" user="user" dbname="db_osm_routing" password="xxxxx"" $FILE ; done

