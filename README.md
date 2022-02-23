# mtb-router

This project is intended to create the an API for Mountain Biking automatic map routing.

It should be based on a data source from MTB gpx files that will be used to supplement OSM with specific MTB data like path popularity.

Input : 
* Departure coordinates
* Destination coordintates

Output :
* GPX file or geoJSON

Should be written in python

## Principles

![Best MTB OSM Router (1)](https://user-images.githubusercontent.com/16464382/155356878-cc1885e1-cfb3-495d-8c4e-e2473377bfe4.jpg)

https://miro.com/app/board/uXjVONfUPfw=/?invite_link_id=416360118516

Should be using Docker containerisation

## Sample files

A file containing around 1200 GPX tracks from Isère and Rhône region in France is made available in an archive "sample-MTB-gpx-6938.zip"

## Dependencies

 - PostGIS
 - ogr2ogr
 - Brouter or Graphhopper
 
 
