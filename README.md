# mtb-router
Router

This project is intended to create the an API for Mountain Biking automatic map routing.

It should be based on a data source from MTB gpx files that will be used to supplement OSM with specific MTB data like path popularity.

Input : 
* Departure coordinates
* Destination coordintates

Output :
* GPX file or geoJSON

## Principles

![flowchart](Best MTB OSM Router(1).jpg)
https://miro.com/app/board/uXjVONfUPfw=/?invite_link_id=416360118516

## Dependencies

 - PostGIS
 - ogr2ogr
 - Brouter or Graphhopper
 
 
