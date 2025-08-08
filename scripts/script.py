#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 16:51:07 2022

@author: lpeller
"""

import requests
import subprocess
import gpxpy
#import gpxtools as gpxt
import glob
import os
import time
import unicodedata
import importlib.util 
import psycopg2



#Recuperation et lancement de Graphhopper en local :

#Map Matching d'un fichier .GPX :
def map_matching(url, path_gpx, params, headers, path_output):
    """
    Parameters
    ----------
    url : STRING
        Url of match Graphhopper API
    path_gpx : STRING
        Path to original .gpx file
    params : DICTIONARY
        Parameters of the map matching API
    headers : DICTIONARY
        Headers of the POST request
    path_output : STRING
        Output to store the mapmatched GPX file

    Returns
    -------
    GPX mapmatched file at the outout path
    """
    with open(path_gpx) as f:
        data = f.read().replace('\n', ' ')
        data = data.replace("'", ' ')
        data = data.replace("’", ' ')
        data = data.replace("–", ' ')
        data = unicodedata.normalize('NFD', data)
        data = u"".join([c for c in data if not unicodedata.combining(c)])
    data = data.encode('utf-8')
    
    res= requests.post(url, params=params, headers=headers, data=data)
    f = open(path_output, 'w')
    f.write(res.text)
    f.close()


def match_GPX(url, path_gpx, params, headers, path_output):
    """

    Parameters
    ----------
    url : STRING
        Url of match Graphhopper API
    path_gpx : STRING
        Path to original .gpx file
    params : DICTIONARY
        Parameters of the map matching API
    headers : DICTIONARY
        Headers of the POST request
    path_output : STRING
        Output to store the mapmatched GPX file

    Returns
    -------
    All GPX mapmatched file from the path_gpx location at the outout path

    """
    iteration = 0
    nb_files = str(len(glob.glob( os.path.join(path_gpx,'*.gpx'))))
    print('Starting Mapmatching process: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    for gpx in glob.glob( os.path.join(path_gpx,'*.gpx') ):
        iteration +=1
        output = path_output + gpx.split('/')[-1].split('.')[0] + '_matched.gpx'
        map_matching(url, str(gpx), params, headers, str(output))
        print('Matched GPX file : ' + gpx.split('/')[-1].split('.')[0] + '   ' + str(iteration) + '/' + nb_files)
    print('End: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    print(nb_files + ' GPX files matched.')
        
def segmentation(url, path_gpx, params, headers, path_output): #tentative de traitement par segmentation des traces pour le problème des traces passant par des chemins non reconnus par OSM
    """

    Parameters
    ----------
    url : STRING
        Url of match Graphhopper API
    path_gpx : STRING
        Path to original .gpx file
    params : DICTIONARY
        Parameters of the map matching API
    headers : DICTIONARY
        Headers of the POST request
    path_output : STRING
        Output to store the mapmatched GPX file

    Returns
    -------
    GPX mapmatched file at the outout path, for every segment --- Unused

    """
    gpx_file = open(path_gpx, 'r')
    gpx_data = gpxpy.parse(gpx_file)
    print(gpx_data)
    gpx_out = gpx = gpxpy.gpx.GPX()
    # Create the output GPX:
    gpx_track_out = gpxpy.gpx.GPXTrack()
    gpx_out.tracks.append(gpx_track_out)
    gpx_segment_out = gpxpy.gpx.GPXTrackSegment()
    gpx_track_out.segments.append(gpx_segment_out)
    #Snap every segment to the OSM ways
    for track in gpx_data.tracks:
        for segment in track.segments:
            for i in range(1, len(segment.points)):
                gpx = gpxpy.gpx.GPX()
                # Create a temporary GPX file
                gpx_track = gpxpy.gpx.GPXTrack()
                gpx.tracks.append(gpx_track)
                gpx_segment = gpxpy.gpx.GPXTrackSegment()
                gpx_track.segments.append(gpx_segment)
                # Add the two points of the segment to the temporary GPX file
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(segment.points[i-1].latitude, segment.points[i-1].longitude, elevation=segment.points[i-1].elevation))
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(segment.points[i].latitude, segment.points[i].longitude, elevation=segment.points[i].elevation))
                print(gpx_segment.points)
                
                '''gpx_temp = open('temp/temp.gpx', 'w')
                gpx_temp.write(gpx.to_xml())
                gpx_temp.close()
                #Write the output GPX file
                gpx_temp_file = open('temp/match_temp.gpx', 'r')
                gpx_temp_data = gpxpy.parse(gpx_temp_file)
                point_b = gpx_temp_data.tracks[0].segments[0].points[1]
                point_a = gpx_temp_data.tracks[0].segments[0].points[0]
                gpx_segment_out.points.append(gpxpy.gpx.GPXTrackPoint(point_a.latitude, point_a.longitude, elevation=point_a.elevation))
                gpx_segment_out.points.append(gpxpy.gpx.GPXTrackPoint(point_b.latitude, point_b.longitude, elevation=point_b.elevation))'''
    gpx_file.close()
    gpx_file = open('test_match.gpx', 'w')
    gpx_file.write(gpx_out.to_xml())
    gpx_file.close()

def extraction_non_OSM(host, db_name, user, password, path_gpx, path_original, precision = 0.001):
    '''
    

    Parameters
    ----------
    host : STRING
        host adress
    db_name : STRING
        name of the database containing the OSM ways
    user : STRING
        db username
    password : STRING
        db user password
    path_gpx : STRING
        Path to original  and unmodified .gpx file
    path_original : STRING
        Path to store the GPX original files that were encoded in UTF-8 format

    Returns
    -------
    CSV file segments_hors_osm.csv filled with the GPX routes names, the part of them that is too far from the map matched file, and the accuracy rate.

    '''
    print('Formating gpx files to UTF8 : '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    for filename in os.scandir(path_gpx):
        if filename.is_file():
            with open(filename.path) as f:
                data = f.read().replace('\n', ' ')
                data = data.replace("'", ' ')
                data = data.replace("’", ' ')
                data = data.replace("–", ' ')
                data = data.replace("&apos;", ' ')
                data = unicodedata.normalize('NFD', data)
                data = u"".join([c for c in data if not unicodedata.combining(c)])
            output = path_original + filename.name.split('.')[0] + '_corrected.gpx'
            data = data.encode('utf-8')
            f = open(output, 'w')
            f.write(str(data)[2:][:-2])
            f.close()
    print('Connecting to database'+ db_name +': '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    conn = psycopg2.connect(
        host=host,
        database=db_name,
        user=user,
        password=password)
    cursor = conn.cursor()
    print('Filling database with the original GPX files : '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    cursor.execute("DROP TABLE IF EXISTS gpx_origine")
    os.system('for FILE in ../GPX/Original_GPX/*.gpx; do ogr2ogr -skipfailures -update -append -f "PostgreSQL"  PG:"host="localhost" user="user" dbname="db_osm_routing" password="xxxxx"" -nlt MULTILINESTRING -nln gpx_origine $FILE ; done')

    print('Searching for segments that that are too far from the map matched GPX file : '+str(time.strftime("%Y-%m-%d %H:%M:%S")))

    query = """
    SELECT
        gpx.ogc_fid,
        gpx.name,
        ST_Length(ST_Difference(gpx.wkb_geometry, buffer.geom)) / ST_Length(gpx.wkb_geometry) as accuracy,
        ST_AsEWKT(ST_Difference(gpx.wkb_geometry, buffer.geom)) as remaining_geometry
    FROM
        gpx_origine AS gpx
    JOIN
        (SELECT name, ST_Buffer(wkb_geometry, %s) as geom FROM tracks) AS buffer
    ON
        gpx.name = buffer.name;
    """

    cursor.execute(query, (precision,))
    results = cursor.fetchall()

    with open("../GPX/segments_hors_osm.csv",'w') as f:
        f.write('id_origine,name,accuracy,remaining geometry\n')
        for row in results:
            f.write(','.join(map(str, row)) + '\n')

    conn.close()
    print('Finished searching for segments: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))

        
    
    
    
def ponderate(host, db_name, user, password, table):
    '''
    

    Parameters
    ----------
    host : STRING
        host adress
    db_name : STRING
        name of the database containing the OSM ways
    user : STRING
        db username
    password : STRING
        db user password
    table : STRING
        Table containing the OSM ways

    Returns
    -------
    Adds the gpx_weiht to the osm ways, ie. the nuber of times each way is taken by a gpx route

    '''
    print('Connecting to database'+ db_name +': '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    conn = psycopg2.connect(
        host=host,
        database=db_name,
        user=user,
        password=password)
    cursor = conn.cursor()
    print('Updating column gpx_weight : '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    query = ('ALTER TABLE '+ table +' ADD COLUMN IF NOT EXISTS gpx_weight INT DEFAULT 0')    #Creating the weight column
    cursor.execute(query)
    conn.commit()

    print('Starting weighting process: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))

    update_query = f"""
    WITH way_weights AS (
        SELECT
            ways.id,
            count(tracks.ogc_fid) as weight
        FROM
            {table} AS ways
        JOIN
            tracks ON ST_Within(ST_Transform(ways.geom_linestring, 4326), ST_Buffer(tracks.wkb_geometry, 0.00003))
        GROUP BY
            ways.id
    )
    UPDATE
        {table}
    SET
        gpx_weight = way_weights.weight
    FROM
        way_weights
    WHERE
        {table}.id = way_weights.id;
    """

    cursor.execute(f"UPDATE {table} SET gpx_weight = 0;")
    cursor.execute(update_query)
    conn.commit()

    conn.close()
    print('Weighting process finished: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))



def construct_view(host, db_name, user, password, table):
    '''
    Building a view from the database containing the gpx files, used to load graphhopper from a database  --- unused
    '''

    print('Connecting to database'+ db_name +': '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    conn = psycopg2.connect(
        host=host,
        database=db_name,
        user=user,
        password=password)
    cursor = conn.cursor()
    print('Creating temporary table gh_temp: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    query = ('CREATE TABLE IF NOT EXISTS gh_temp (osm_id BIGINT, name TEXT, highway TEXT, maxspeed TEXT, oneway TEXT, cycleway TEXT, bycycle_road TEXT, motorroad TEXT, incline TEXT, "mtb:scale" TEXT, "mtb:scale:uphill" TEXT, surface TEXT, gpx_weight TEXT, geom geometry(LineString,4326));')
    cursor.execute(query)
    conn.commit()
    query = ('SELECT id, geom_linestring, tags, gpx_weight FROM ' + table)
    cursor.execute(query)
    l_way = cursor.fetchall()
    k=0
    print('Filling table gh_temp: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    for way in l_way:
        #tags to create, see https://wiki.openstreetmap.org/wiki/Map_features
        name=0
        highway = 0             #str
        maxspeed = 0            #str
        oneway = 0              #boolean
        cycleway = 0            #str
        bycycle_road = 0        #boolean
        motorroad = 0           #boolean : The motorroad tag is used to describe highways that have motorway-like access restrictions but that are not a motorway. 
        incline = 0             #Number % | ° | up | down : Incline steepness as percents ("5%") or degrees ("20°"). Positive/negative values indicate movement upward/downwards in the direction of the way. 
        mtb_scale = 0           #mb:scale  :  Applies to highway=path and highway=track. A classification scheme for mtb trails (few inclination and downhill). Between 0 (easiest) and 6 (hard)
        mtb_scale_uphill = 0    #mtb:scale:uphill : A classification scheme for mtb trails for going uphill if there is significant inclination. Between 0 (easiest) and 5 (impossible)
        surface = 0             #str
        
        columns = 'osm_id'
        values = str(way[0])
        k+=1
        print(k)
        for i in range(0, len(way[2])):
            if way[2][i] == 'name' and name==0 and i+1<len(way[2]):
                name = 1
                columns +=', name'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'highway' and highway==0 and i+1<len(way[2]):
                highway = 1
                columns +=', highway'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'maxspeed' and maxspeed==0 and i+1<len(way[2]):
                maxspeed = 1
                columns +=', maxspeed'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'oneway' and oneway==0 and i+1<len(way[2]):
                oneway = 1
                columns +=', oneway'
                if way[2][i+1] == 'alternating' or way[2][i+1] == 'reversible' or way[2][i+1] == 'hamlet':
                    values+= ", 'no'"
                else:
                    values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'cycleway' and way[2][i-1] != 'highway' and cycleway==0 and i+1<len(way[2]):
                cycleway = 1
                columns +=', cycleway'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'bycycle_road' and bycycle_road==0 and i+1<len(way[2]):
                bycycle_road = 1
                columns +=', bycycle_road'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'motorroad' and motorroad==0 and i+1<len(way[2]):
                motorroad = 1
                columns +=', motorroad'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'incline' and incline==0 and i+1<len(way[2]):
                incline = 1
                columns +=', incline'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == '"mtb:scale"' and mtb_scale==0 and i+1<len(way[2]):
                mtb_scale = 1
                columns +=', "mtb:scale"'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == '"mtb:scale:uphill"' and mtb_scale_uphill==0 and i+1<len(way[2]):
                mtb_scale_uphill = 1
                columns +=', "mtb:scale:uphill"'
                values+=", '"+way[2][i+1]+"'"
            if way[2][i] == 'surface' and surface==0 and i+1<len(way[2]):
                surface = 1
                columns +=', surface'
                values+=", '"+way[2][i+1]+"'"
        columns+= ', gpx_weight, geom'
        values+= ", "+ str(way[3]) + ", ST_Transform('" + str(way[1]) + "',4326)"
        query = ('INSERT INTO gh_temp('+columns+') VALUES('+values+')')
        cursor.execute(query)
        conn.commit()
    print('Creating view gh_view: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    query = ("CREATE VIEW gh_view (osm_id,maxspeed,oneway,fclass,name, "+'"mtb:scale:uphill"'+", gpx_weight, highway, cycleway, bycycle_road, motorroad, incline, "+'"mtb:scale"'+", surface, geom )as select osm_id,maxspeed,oneway,highway, name, "+'"mtb:scale:uphill"'+", gpx_weight, highway, cycleway, bycycle_road, motorroad, incline, "+'"mtb:scale"'+", surface, ST_TRANSFORM(geom,4326) from gh_temp;")
    cursor.execute(query)
    conn.commit()
    conn.close()
    return l_way

#-------------------- TEST VALUES -----------------------
url = 'http://localhost:8989/match'
path_gpx = '../GPX/sample-MTB-gpx-6938/'
headers = {
    'Content-Type': 'application/gpx+xml',
}
params = {
    'profile': 'mtb_c',       #profile of the route (car, bike,...)
    'type': 'gpx',      #type of the outut element (gpx, json,...)
    'gpx.route': 'false',       #if true, output file will ountain the original route 
    'traversal_keys': 'true',
    #'max_visited_nodes': '200',      #default=1000, type=int, the limit we use to search a route from one gps entry to the other to avoid exploring the whole graph in case of disconnected subnetworks.
    'force_repair': 'false ',  
}
path_output = '../GPX/Matched_GPX/'
path_original = '../GPX/Original_GPX/'

host="localhost"
db_name="db_osm_routing"
user="user"
password="xxxxx"
table = "otrouting_ways"


gpx_file = '../GPX/sample-MTB-gpx-6938/utgtrack-20.gpx'