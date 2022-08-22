# launch graphhopper on http://localhost:8989
java -Ddw.graphhopper.datareader.file=rhone-alpes-latest.osm.pbf -jar *.jar server /srv/projects/mtb-router/graphhopper_config/config.yml;
osm2pgsql --slim -C 100 -d db_osm_routing -U user -H localhost -P 5432 /srv/projects/mtb-router/scripts/rhone-alpes-latest.osm.pbf
