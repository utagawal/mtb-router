#!/bin/sh

cd /srv/projects/mtb-router

# Get OpenstreetMapData (sample dtat for Rhone Alpes only)
cd OSM
wget -O rhone-alpes-latest.osm.bz2 http://download.geofabrik.de/europe/france/rhone-alpes-latest.osm.bz2

# Import OSM data into PostGIS
osm2pgsql --slim -C 100 -d vagrant -U vagrant -W -H localhost -P 5432 rhone-alpes-latest.osm.bz2

# manual psawword entrey manadatory (vagrant), else possibility to use .pgpass


# Import GPX files form /GPX folders into PostGIS (tracks table)
cd ..
for FILE in ./GPX/*.gpx; do ogr2ogr -append -f PostgreSQL "PG:dbname=vagrant user=vagrant password=vagrant" $FILE tracks; done
