#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 10:20:53 2022

@author: lpeller
"""
import importlib.util
import subprocess
import script

def ___init___():
    #Import the otrouting_v1.3 script
    spec = importlib.util.spec_from_file_location(
        name="otrouting",  # note that ".test" is not a valid module name
        location="../oprouting/otrouting_py/otrouting_v1.3.py",
    )
    otrouting = importlib.util.module_from_spec(spec)

    #Fill db_osm_routing database
    #You can change maps region in /oprouting/otrouting_py/otrouting_v1.3.py
    spec.loader.exec_module(otrouting)
    
    

def ___main___():
    #Match the gpx files
    url = 'http://localhost:8989/match'
    path_gpx = '../GPX/sample-MTB-gpx-6938/'
    headers = {
        'Content-Type': 'application/gpx+xml',
    }
    params = {
        'profile': 'mtb',       #profile of the route (car, bike,...)
        'type': 'gpx',      #type of the outut element (gpx, json,...)
        'gpx.route': 'false',       #if true, output file will ountain the original route 
        'traversal_keys': 'true',
        #'max_visited_nodes': '200',      #default=1000, type=int, the limit we use to search a route from one gps entry to the other to avoid exploring the whole graph in case of disconnected subnetworks.
        'force_repair': 'false ',  
    }
    path_output = '../GPX/Matched_GPX/'
    host = 'localhost'
    db_name="db_osm_routing"
    user="user"
    password="xxxxx"
    table = "otrouting_ways"
    path_original = '../GPX/Original_GPX/'
    precision = 0.001 #preccision of the GPX accuracy detection in km
    script.match_GPX(url, path_gpx, params, headers, path_output)
    #Load the GPX files into the db_osm_routing database
    subprocess.call(['sh', 'data_loader.sh'])
    script.extraction_non_OSM(host, db_name, user, password, path_gpx, path_original, precision)
    script.ponderate(host, db_name, user, password, table)
    


#___init___()

#Start the graphhopper server

#___main___()
