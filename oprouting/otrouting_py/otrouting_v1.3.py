#!/usr/bin/python
#
# run script in the terminal
# > ./otrouting_v1.3.py
#
# run script in background
# https://janakiev.com/til/python-background/
# > nohup ./otrouting_v1.3.py &
# > ps ax | grep otrouting_v1.3.py
# > pkill -f otrouting_v1.3.py
#
# gandi cloud server parameter status:
#      2 coeurs / 1 Go RAM --> OK for small aera onlt like monaco andorra
#      2 coeurs / 2 Go RAM --> OK to import one or a few limited area like lorraine, midi-pyrenees, ...
#      2 coeurs / 4 Go RAM --> OK for large import
#
# to check import status from otrouting_master table:
# > SELECT id, status, title, timestamp, log FROM otrouting_master WHERE status != 'obsolete' ORDER BY timestamp DESC
# > SELECT id, status, title, timestamp, log FROM otrouting_master ORDER BY timestamp DESC
#
# v1.1 Julien SENTIER
#       in line with otrouting_getrouting_v1.3.sql
#
# v1.2 20/10/2020 Julien SENTIER
#       factor_mountainbike, factor_roadcycle, factor_car added to TABLE otrouting_ways 
#            sql> ALTER TABLE otrouting_ways ADD factor_mountainbike int;
#            sql> ALTER TABLE otrouting_ways ADD factor_roadcycle int;
#            sql> ALTER TABLE otrouting_ways ADD factor_car int;
#            sql> UPDATE otrouting_ways SET factor_mountainbike = factor_pedestrian;
#            sql> UPDATE otrouting_ways SET factor_roadcycle = factor_pedestrian;
#            sql> UPDATE otrouting_ways SET factor_car = factor_pedestrian;
#            sql> ALTER TABLE otrouting_ways ADD factorreverse_pedestrian int;
#            sql> ALTER TABLE otrouting_ways ADD factorreverse_mountainbike int;
#            sql> ALTER TABLE otrouting_ways ADD factorreverse_roadcycle int;
#            sql> ALTER TABLE otrouting_ways ADD factorreverse_car int;
#            sql> UPDATE otrouting_ways SET factor_mountainbike = factor_pedestrian, factor_roadcycle = factor_pedestrian, factor_car = factor_pedestrian, factorreverse_pedestrian = 1, factorreverse_mountainbike = 1, factorreverse_roadcycle = 1, factorreverse_car = 1 WHERE factorreverse_car IS NULL;
#        log added to TABLE otrouting_master
#            sql> ALTER TABLE otrouting_master ADD log text; 
#        addition of otrouting_ways INDEX for id_master, factor_perdestrian, factor_mountainbike, factor_roadcycle, factor_car 
#       in line with otrouting_getrouting_v1.4.sql
#
# v1.3 21/11/2020 Julien SENTIER
#         factor_pedestrian update with in particular the consideration of sidewalk
#         factor_mountainbike update with in particular the consideration of cycleway
#         factor_roadcycle update with in particular the consideration of cycleway
#         factor_car update
#       distance computed in meters
#        creation of working table _work_otrouting_osm_nodes_ninter
#        UPDATE of otrouting_points, table not dropped anymore
#        column lonmin lonmax latmin latmax geom_center deleted from otrouting_ways
#            sql> ALTER TABLE otrouting_ways DROP COLUMN lonmin;
#            sql> ALTER TABLE otrouting_ways DROP COLUMN lonmax;
#            sql> ALTER TABLE otrouting_ways DROP COLUMN latmin;
#            sql> ALTER TABLE otrouting_ways DROP COLUMN latmax;
#            sql> ALTER TABLE otrouting_ways DROP COLUMN geom_center;
#        add index otrouting_ways_geom_linestring
#        rename column otrouting_ways.dist_3857_m to otrouting_ways.dist_m
#            sql> ALTER TABLE otrouting_ways RENAME COLUMN dist_3857_m TO dist_m;
import sys
import psycopg2
import time
import math
import os
import subprocess

glob_scriptversion = 'ot_routing_v1.3.py'

glob_t_input = []
#http://download.geofabrik.de
#MONACO - ANDORRA ################################################
#glob_t_input.append(["europe", "andorra"])
#glob_t_input.append(["europe", "monaco"])
#FRANCE ##########################################################
#glob_t_input.append(["europe", "france", "alsace"])
#glob_t_input.append(["europe", "france", "aquitaine"])
#glob_t_input.append(["europe", "france", "auvergne"])
#glob_t_input.append(["europe", "france", "basse-normandie"])
#glob_t_input.append(["europe", "france", "bourgogne"])
#glob_t_input.append(["europe", "france", "bretagne"])
#glob_t_input.append(["europe", "france", "centre"])
#glob_t_input.append(["europe", "france", "champagne-ardenne"])
#glob_t_input.append(["europe", "france", "corse"])
#glob_t_input.append(["europe", "france", "franche-comte"])
#glob_t_input.append(["europe", "france", "guadeloupe"])
#glob_t_input.append(["europe", "france", "guyane"])
#glob_t_input.append(["europe", "france", "haute-normandie"])
#glob_t_input.append(["europe", "france", "ile-de-france"])
#glob_t_input.append(["europe", "france", "languedoc-roussillon"])
#glob_t_input.append(["europe", "france", "limousin"])
#glob_t_input.append(["europe", "france", "lorraine"])
#glob_t_input.append(["europe", "france", "martinique"])
#glob_t_input.append(["europe", "france", "mayotte"])
#glob_t_input.append(["europe", "france", "midi-pyrenees"])
#glob_t_input.append(["europe", "france", "nord-pas-de-calais"])
#glob_t_input.append(["europe", "france", "pays-de-la-loire"])
#glob_t_input.append(["europe", "france", "picardie"])
#glob_t_input.append(["europe", "france", "poitou-charentes"])
#glob_t_input.append(["europe", "france", "provence-alpes-cote-d-azur"])
#glob_t_input.append(["europe", "france", "reunion"])
glob_t_input.append(["europe", "france", "rhone-alpes"])
#BELGIUM LUXEMBOURG ##########################################################
#glob_t_input.append(["europe", "belgium"])
#glob_t_input.append(["europe", "luxembourg"])
#GERMANY ##########################################################
#glob_t_input.append(["europe", "germany", "baden-wuerttemberg"])
#glob_t_input.append(["europe", "germany", "rheinland-pfalz"])
#glob_t_input.append(["europe", "germany", "saarland"])
#SWITZERLAND ##########################################################
#glob_t_input.append(["europe", "switzerland"])
#ITALY ##########################################################
#glob_t_input.append(["europe", "italy", "nord-ovest"])
#SPAIN ##########################################################
#glob_t_input.append(["europe", "spain"])

glob_db = 'db_osm_routing'
glob_user = 'user'
glob_host = 'localhost'
glob_port = '5432'
glob_password = 'xxxxx'

#.pgpass TO BE CREATED 
# so as to avoid to use password in the osm2pgsql
# https://linuxandryan.wordpress.com/2013/03/07/creating-and-using-a-pgpass-file/
#> cd ~
#> touch .pgpass
#> nano .pgpass
#$ edit .pgpass and add the above line          
#    localhost:5432:db_osm_routing:user:xxxxx
#> chmod 0600 .pgpass

# EPSG_osm = '4326'
factor_osm = 10000000.0
# EPSG_otrouting = '3857'

def getfromdict(dict, key):
    keys = dict.keys()
    if key in keys:
        return dict[key]
    else:
        return None

def upload_data(input):
    #upload data from download.geofabrik.de

    txt = ""
    for j in range(len(input)):
        if txt != "":
            txt = txt+"/"
        txt = txt+input[j]

    cmd = ['wget', '-O', 
            txt.replace("/","_")+'-latest.osm.bz2',
            'http://download.geofabrik.de/'+txt+'-latest.osm.bz2']
    log("log.txt", '    > subprocess.check_output(' + str(cmd) + ')')
    log("log.txt", '        start: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    subprocess.check_output(cmd)
    log("log.txt", '        end: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))

    cmd = ['wget', '-O', 
            txt.replace("/","_")+'.poly',
            'http://download.geofabrik.de/'+txt+'.poly']
    log("log.txt", '    > subprocess.check_output(' + str(cmd) + ')')
    log("log.txt", '        start: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    subprocess.check_output(cmd)
    log("log.txt", '        end: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))

def clean_db():
    conn = psycopg2.connect("dbname="+glob_db+" user="+glob_user+" password="+glob_password+" host="+glob_host+" port="+glob_port)
    cur = conn.cursor()

    log("log.txt","    DROP TABLE IF EXISTS _work_otrouting_osm_nodes_ninter")
    cur.execute("DROP TABLE IF EXISTS _work_otrouting_osm_nodes_ninter")
    log("log.txt","    DROP TABLE IF EXISTS planet_osm_*")
    cur.execute("DROP TABLE IF EXISTS planet_osm_line")
    cur.execute("DROP TABLE IF EXISTS planet_osm_nodes")
    cur.execute("DROP TABLE IF EXISTS planet_osm_point")
    cur.execute("DROP TABLE IF EXISTS planet_osm_polygon")
    cur.execute("DROP TABLE IF EXISTS planet_osm_rels")
    cur.execute("DROP TABLE IF EXISTS planet_osm_roads")
    cur.execute("DROP TABLE IF EXISTS planet_osm_ways")

    conn.commit()
    cur.close()
    conn.close()

def read_osm_tag(tags, tValues):
    oReturn = {}
    oReturn["index"] = []
    if len(tValues) == 0:
        if tags != None:
            for i in range(0, len(tags), 2):
                oReturn[tags[i]] = tags[i+1].replace("'"," ")
                oReturn["index"].append(tags[i])
    else:    
        for i in range(0, len(tValues)):
                oReturn[tValues[i]] = None
                if tags != None:
                    index = -1
                    for ii in range(0, len(tags)):
                        if tags[ii] == tValues[i]:
                                index = ii
                                break;
                    if index >= 0 and index+1 < len(tags):
                            oReturn[tValues[i]] = tags[index+1].replace("'"," ")
                            oReturn["index"].append(tValues[i])
    return oReturn

def init():
    conn = psycopg2.connect("dbname="+glob_db+" user="+glob_user+" password="+glob_password+" host="+glob_host+" port="+glob_port)
    cur = conn.cursor()

    clean_db()

    sql = "CREATE EXTENSION IF NOT EXISTS postgis"
    log("log.txt", '    ' + sql)
    cur.execute(sql)
    cur.execute("SELECT postgis_full_version()    ")
    data = cur.fetchone()
    while data is not None:
        log("log.txt", '        ' + str(data))
        data = cur.fetchone()
    sql = "CREATE EXTENSION IF NOT EXISTS pgrouting"
    log("log.txt", '    ' + sql)
    cur.execute(sql)
    cur.execute("SELECT * FROM pgr_version()")
    data = cur.fetchone()
    while data is not None:
        log("log.txt", '        ' + str(data))
        data = cur.fetchone()

    log("log.txt", '    CREATE TABLE IF NOT EXISTS otrouting_master')
    cur.execute("CREATE TABLE IF NOT EXISTS otrouting_master(id  serial PRIMARY KEY, title text, status text, log text, timestamp int, geom_polygon geometry(MultiPolygon,3857));")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_master_status')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_master_status ON otrouting_master (status);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_master_geom_polygon')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_master_geom_polygon ON otrouting_master USING GIST (geom_polygon);")
    
    log("log.txt", '    CREATE TABLE IF NOT EXISTS otrouting_points')
    cur.execute("CREATE TABLE IF NOT EXISTS otrouting_points(idserial  bigserial PRIMARY KEY, id bigint, id_master int, geom_point geometry(Point,3857));")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_points_id')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_points_id ON otrouting_points (id);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_points_id_master')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_points_id_master ON otrouting_points (id_master);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_points_geom_point_gist')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_points_geom_point_gist ON otrouting_points USING GIST (geom_point);")

    log("log.txt", '    CREATE TABLE IF NOT EXISTS otrouting_ways')
    cur.execute("CREATE TABLE IF NOT EXISTS otrouting_ways(id  bigserial PRIMARY KEY, id_master int, geom_linestring geometry(Linestring,3857), source bigint, target bigint, dist_m int, factor_pedestrian int, factor_mountainbike int, factor_roadcycle int, factor_car int, factorreverse_pedestrian int, factorreverse_mountainbike int, factorreverse_roadcycle int, factorreverse_car int, tags text[]) ")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_ways_geom_center_gist')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_ways_geom_linestring_gist ON otrouting_ways USING GIST (geom_linestring);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_ways_id_master')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_ways_id_master ON otrouting_ways (id_master);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_ways_factor_pedestrian')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_ways_factor_pedestrian ON otrouting_ways (factor_pedestrian);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_ways_factor_mountainbike')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_ways_factor_mountainbike ON otrouting_ways (factor_mountainbike);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_ways_factor_roadcycle')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_ways_factor_roadcycle ON otrouting_ways (factor_roadcycle);")
    log("log.txt", '    CREATE INDEX IF NOT EXISTS otrouting_ways_factor_car')
    cur.execute("CREATE INDEX IF NOT EXISTS otrouting_ways_factor_car ON otrouting_ways (factor_car);")

    #working table remove at the end of the execution script
    log("log.txt", '    CREATE TABLE IF NOT EXISTS _work_otrouting_osm_nodes_ninter')
    cur.execute("CREATE TABLE IF NOT EXISTS _work_otrouting_osm_nodes_ninter(id bigint, geom_point geometry(Point,3857), ninter int, CONSTRAINT _work_otrouting_osm_nodes_ninter_pkey PRIMARY KEY (id)) ")

    conn.commit()
    cur.close()
    conn.close()

def update_master_start(input):
    conn = psycopg2.connect("dbname="+glob_db+" user="+glob_user+" password="+glob_password+" host="+glob_host+" port="+glob_port)
    cur = conn.cursor()
    cur2 = conn.cursor()

    title = ""
    for j in range(len(input)):
        if title != "":
            title = title+"_"
        title = title+input[j]

    #check if previous line and update status and clean otrouting_ways table
    sql = "SELECT id FROM otrouting_master WHERE title='"+title+"' ORDER BY timestamp DESC LIMIT 1"
    cur.execute(sql)
    data = cur.fetchone()
    while data is not None:
        sql = "UPDATE otrouting_master SET status='toBeDeleted' WHERE id="+str(data[0])
        cur2.execute(sql)
        data = cur.fetchone()

    #read poly data
    f = open(title+".poly", "r")
    arrayMultiPoly = []
    arrayPoly = []
    for row in f:
        if row[0] != ' ':
            if len(arrayPoly) > 0:
                arrayMultiPoly.append(arrayPoly)
                #print arrayPoly
                arrayPoly = []
        else:
            row = row.strip()
            tab = row.split('   ')
            tab[0] = float(tab[0])
            tab[1] = float(tab[1])
            arrayPoly.append(tab)

    #MULTILINESTRING((1 2,3 4),(3 4,4 5))
    #print arrayMultiPoly
    txt = "MULTIPOLYGON("
    boolFirst1 = True
    for multiPoly in arrayMultiPoly:
        if boolFirst1 == False:
            txt = txt+","
        else:
            boolFirst1 = False
        txt = txt + "(("
        boolFirst = True
        for poly in multiPoly:
            if boolFirst == False:
                txt = txt+","
            else:
                boolFirst = False
            txt = txt+str(poly[0])+' '+str(poly[1])
        txt = txt + ")"
    txt = txt + "))"
    txt_geom = "ST_Transform(ST_GeomFromText('"+txt+"', 4326), 3857)"    

    #add new row
    sql = "INSERT INTO otrouting_master (title, status, timestamp, geom_polygon) VALUES ('"+title+"','started', "+str(time.time())+", "+txt_geom+")"
    cur.execute(sql)

    sql = "SELECT id FROM otrouting_master WHERE title='"+title+"' ORDER BY id DESC LIMIT 1"
    cur.execute(sql)
    data = cur.fetchone()
    while data is not None:
        id_master = data[0]
        data = cur.fetchone()

    conn.commit()
    cur.close()
    cur2.close()
    conn.close()

    return id_master

def update_master_complete(input):
    conn = psycopg2.connect("dbname="+glob_db+" user="+glob_user+" password="+glob_password+" host="+glob_host+" port="+glob_port)
    cur = conn.cursor()
    cur2 = conn.cursor()

    title = ""
    for j in range(len(input)):
        if title != "":
            title = title+"_"
        title = title+input[j]



    log("log.txt", "    UPDATE otrouting_master table new row")
    sql = "SELECT id FROM otrouting_master WHERE title='"+title+"' AND status='started'"
    cur.execute(sql)
    data = cur.fetchone()
    while data is not None:
        #generate log for otrouting master table
        log_ = ""
        sql = "SELECT COUNT(*) AS count FROM otrouting_ways WHERE id_master="+str(data[0])
        cur2.execute(sql)
        data2 = cur2.fetchone()
        if data2 is not None:
            log_ = log_ + 'imported with ' + glob_scriptversion
            log_ = log_  + '\n' + str(data2[0]) + ' rows inserted into TABLE otrouting_ways'

        sql = "SELECT COUNT(*) AS count FROM otrouting_points WHERE id_master="+str(data[0])
        cur2.execute(sql)
        data2 = cur2.fetchone()
        if data2 is not None:
            log_ = log_  + '\n' + str(data2[0]) + ' rows inserted into TABLE otrouting_points'

        sql = "UPDATE otrouting_master SET status='completed', log='"+log_+"' WHERE id="+str(data[0])
        cur2.execute(sql)
        data = cur.fetchone()
        log("log.txt", "        log:")
        log("log.txt", log_)

    log("log.txt", "    Delete obsolete data from otrouting_ways and otrouting_points TABLE")
    sql = "SELECT id FROM otrouting_master WHERE title='"+title+"' AND status='toBeDeleted'"
    cur.execute(sql)
    data = cur.fetchone()
    while data is not None:
        sql = "DELETE FROM otrouting_ways WHERE id_master="+str(data[0])
        log("log.txt", "        "+sql)
        cur2.execute(sql)
        sql = "DELETE FROM otrouting_points WHERE id_master="+str(data[0])
        log("log.txt", "        "+sql)
        cur2.execute(sql)
        sql = "UPDATE otrouting_master SET status='obsolete' WHERE id="+str(data[0])
        log("log.txt", "        "+sql)
        cur2.execute(sql)
        data = cur.fetchone()

    log("log.txt", "    VACUUM ANALYZE otrouting_ways")
    cur.execute("END TRANSACTION;")
    cur.execute("VACUUM ANALYZE otrouting_ways;")
    log("log.txt", "    VACUUM ANALYZE otrouting_points")
    cur.execute("VACUUM ANALYZE otrouting_points;")

    conn.commit()
    cur.close()
    cur2.close()
    conn.close()

def log(file, txt, boolNewFile=False):
    if boolNewFile:
        f = open(file, "w")
        f.close()
    f = open(file, "a")
    f.write(txt+"\n")
    f.close()
    print(txt)

def osm2pgsql(input):
    txt = ""
    for j in range(len(input)):
        if txt != "":
            txt = txt+"/"
        txt = txt+input[j]

    #cmd = ['osm2pgsql', '--slim', '-C', '100', '-d', 'db_osm_routing', '-U', 'user', '-W', '-H', 'localhost', '-P', '5432', txt.replace("/","_")+'-latest.osm.bz2']
    cmd = ['osm2pgsql','--slim', '-C', '4096', '-d', glob_db, '-U', glob_user, '-H', glob_host, '-P', glob_port, '/srv/projects/mtb-router/scripts/rhone-alpes-latest.osm.pbf']
    log("log.txt", '    > subprocess.check_output(' + str(cmd) + ')')
    log("log.txt", '        start: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    subprocess.check_output(cmd)
    log("log.txt", '        end: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))

def create_points(id_master):
    log("log.txt", '    Connect DataBase')
    conn = psycopg2.connect("dbname="+glob_db+" user="+glob_user+" password="+glob_password+" host="+glob_host+" port="+glob_port)
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur3 = conn.cursor()

    #count number of rows to be read
    cur.execute("SELECT COUNT(*) FROM planet_osm_ways")
    data=cur.fetchone()
    n_rows = data[0]
    log("log.txt", "    " + str(n_rows) + " entries in planet_osm_ways table")
    log("log.txt", "    select planet_osm_ways table entries")
    cur.execute("SELECT nodes, tags FROM planet_osm_ways")
    log("log.txt", "    START PROCESSING")
    last_pc = -1
    i_row = 0
    time0 = time.time()
    while True:
        i_row = i_row + 1
        #if i_row == 10:
        #    break
        if int(i_row*1.0/n_rows * 100) > last_pc:
            last_pc = int(i_row*1.0/n_rows * 100)
            log("log.txt", "        " + str(last_pc) + ' %   -   ' + str(int(time.time() - time0)) + "s")
        data = cur.fetchone()
        if str(data).strip() == "None":
            #all line have been read
            break
        osmTags = read_osm_tag(data[1], ["highway"])
        if "highway" in osmTags["index"]:
            tNodes = data[0]
            for i in range(0, len(tNodes)):
                if i == 0 or i == len(tNodes)-1:
                    #starting or ending of the way
                    delta_ninter = 2
                else:
                    delta_ninter = 1
                cur2.execute("SELECT ninter FROM _work_otrouting_osm_nodes_ninter WHERE id="+str(tNodes[i]))
                data2 = cur2.fetchone()
                if str(data2).strip() == "None":
                    #nodes does not exists
                    cur2.execute("SELECT id, lon, lat FROM planet_osm_nodes WHERE id="+str(tNodes[i]))
                    data2=cur2.fetchone()
                    geom = str(data2[1]/factor_osm) + " " + str(data2[2]/factor_osm)

                    sql = "INSERT INTO _work_otrouting_osm_nodes_ninter (id, geom_point, ninter) VALUES("+str(data2[0])+", ST_Transform(ST_PointFromText('POINT("+geom+")', 4326), 3857), "+str(delta_ninter)+")"
                    cur2.execute(sql)

                    if delta_ninter > 1:
                        # this node is a new intersection or extremity of a way, add it in otrouting_points
                        sql = "INSERT INTO otrouting_points (id, id_master, geom_point) VALUES("+str(tNodes[i])+", "+str(id_master)+", ST_Transform(ST_PointFromText('POINT("+geom+")', 4326), 3857))"
                        cur2.execute(sql)
                else:
                    ninter = data2[0]
                    if ninter <= 1 and ninter + delta_ninter > 1:
                        # this node is a new intersection or extremity of a way, add it in otrouting_points
                        sql = "INSERT INTO otrouting_points (id, id_master, geom_point) VALUES("+str(tNodes[i])+", "+str(id_master)+", ST_Transform(ST_PointFromText('POINT("+geom+")', 4326), 3857))"
                        cur2.execute(sql)
                    ninter = ninter + delta_ninter
                    #DEBUG
                    #if(tNodes[i] == 51413854 or tNodes[i] == 51414015):
                    #    print(str(tNodes[i]) + '  :'+str(tNodes))
                    cur2.execute("UPDATE _work_otrouting_osm_nodes_ninter SET ninter="+str(ninter)+" WHERE id="+str(tNodes[i]))
    
    conn.commit()
    cur.close()
    cur2.close()
    cur3.close()
    conn.close()
    
    log("log.txt", "    ALL ROWS READ IN " + str(int(time.time() - time0)) + "s")

def add_geom_linestring(cur3, osmTags, tLonLat, source, target, dist, id_master):

    geom = ''
    for i in range(len(tLonLat)): 
        lonlat = tLonLat[i]
        if geom != '':
            geom = geom + ','
        geom = geom + lonlat[0] + ' ' + lonlat[1]
    
    tgeom = geom.split(',')
    if len(tgeom) > 1:
        geom = "LINESTRING("+geom+")"

        #https://wiki.openstreetmap.org/wiki/Key:highway
        #https://wiki.openstreetmap.org/wiki/OSM_tags_for_routing/Access_restrictions
        #https://wiki.openstreetmap.org/wiki/Key:oneway
        coef = 1.15

        #########################################################
        factor_pedestrian = 100
        factorreverse_pedestrian = 1
        #########################################################
        if getfromdict(osmTags, "highway") in ["motorway_link", "motorway", "bus_guideway", "escape", "raceway"]:
            factor_pedestrian = 0
        elif getfromdict(osmTags, "highway") in ["trunk",     "trunk_link"]:
            #check access restriction exception
            if getfromdict(osmTags, "sidewalk") is not None and  getfromdict(osmTags, "sidewalk") != "no":
                factor_pedestrian = factor_pedestrian*coef**4
            else:
                factor_pedestrian = 0
        elif getfromdict(osmTags, "highway") in ["primary",    "primary_link"]:
            #check if sidewalk
            if getfromdict(osmTags, "sidewalk") is not None and  getfromdict(osmTags, "sidewalk") != "no":
                factor_pedestrian = 1
            else:
                factor_pedestrian = factor_pedestrian*coef**3
        elif getfromdict(osmTags, "highway") in ["secondary", "secondary_link"]:
            #check if sidewalk
            if getfromdict(osmTags, "sidewalk") is not None and  getfromdict(osmTags, "sidewalk") != "no":
                factor_pedestrian = 1
            else:
                factor_pedestrian = factor_pedestrian*coef**2
        elif getfromdict(osmTags, "highway") in ["tertiary", "tertiary_link", "unclassified"]:
            #check if sidewalk
            if getfromdict(osmTags, "sidewalk") is not None and  getfromdict(osmTags, "sidewalk") != "no":
                factor_pedestrian = 1
            else:
                factor_pedestrian = factor_pedestrian*coef
        elif getfromdict(osmTags, "highway") in ["track"]:
            factor_pedestrian = factor_pedestrian*coef**-1
        elif getfromdict(osmTags, "highway") in ["cycleway", "bridleway"]:
            #check access restriction exception
            if getfromdict(osmTags, "foot") is not None and  getfromdict(osmTags, "foot") != "no":
                factor_pedestrian = factor_pedestrian*coef**-1
            else:
                factor_pedestrian = 0
        elif getfromdict(osmTags, "highway") in ["pedestrian", "footway", "path"]:
            factor_pedestrian = factor_pedestrian*coef**-2
        factor_pedestrian = int(factor_pedestrian)

        #########################################################
        factor_mountainbike = 100
        factorreverse_mountainbike = 1
        #########################################################
        #check highway
        if getfromdict(osmTags, "highway") in ["motorway_link", "motorway", "bus_guideway", "corridor", "escape", "raceway"]:
            factor_mountainbike = 0
        elif getfromdict(osmTags, "highway") in ["steps"]:
            factor_mountainbike = factor_mountainbike*coef**15
        elif getfromdict(osmTags, "highway") in ["trunk",     "trunk_link"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_mountainbike = factor_mountainbike*coef**-1
            else:
                factor_mountainbike = 0
        elif getfromdict(osmTags, "highway") in ["pedestrian", "bridleway", "footway"]:
            #check access restriction exception
            if getfromdict(osmTags, "bicycle") is not None and  getfromdict(osmTags, "bicycle") != "no":
                factor_mountainbike = factor_mountainbike*1
            else:
                factor_mountainbike = 0
        elif getfromdict(osmTags, "highway") in ["primary",    "primary_link"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_mountainbike = factor_mountainbike*coef**-1
            else:
                factor_mountainbike = factor_mountainbike*coef**3
        elif getfromdict(osmTags, "highway") in ["secondary", "secondary_link"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_mountainbike = factor_mountainbike*coef**-1
            else:
                factor_mountainbike = factor_mountainbike*coef**2
        elif getfromdict(osmTags, "highway") in ["tertiary", "tertiary_link", "unclassified"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_mountainbike = factor_mountainbike*coef**-1
            else:
                factor_mountainbike = factor_mountainbike*coef
        elif getfromdict(osmTags, "highway") in ["track", "cycleway", "path"]:
            factor_mountainbike = factor_mountainbike*coef**-1
        # check mtb_scale and sac_scale
        if getfromdict(osmTags, "mtb:scale") is not None: # mtb:scale applies to highway=path and highway=track
            factor_mountainbike = factor_mountainbike*coef**-2
        elif getfromdict(osmTags, "sac_scale") is not None:
            if getfromdict(osmTags, "sac_scale") in ["mountain_hiking"]:
                factor_mountainbike = factor_mountainbike*coef
            elif getfromdict(osmTags, "sac_scale") in ["demanding_mountain_hiking"]:
                factor_mountainbike = factor_mountainbike*coef**3
            else:
                factor_mountainbike = factor_mountainbike*0
        factor_mountainbike = int(factor_mountainbike)
        #
        if getfromdict(osmTags, "highway") in ["motorway_link", "motorway", "trunk_link", "primary_link", "secondary_link", "tertiary_link"]:
            factorreverse_mountainbike = -1
        elif getfromdict(osmTags, "junction") == 'roundabout':
            factorreverse_mountainbike = -1
        elif getfromdict(osmTags, "oneway") == 'yes':
            if getfromdict(osmTags, "oneway:bicycle") == 'no':
                factorreverse_mountainbike = 1
            else:
                factorreverse_mountainbike = -1


        #########################################################
        factor_roadcycle = 100
        factorreverse_roadcycle = 1
        #########################################################
        #check highway
        if getfromdict(osmTags, "highway") in ["motorway_link", "motorway", "bus_guideway", "corridor", "escape", "raceway"]:
            factor_roadcycle = 0
        elif getfromdict(osmTags, "highway") in ["steps"]:
            factor_roadcycle = 0
        elif getfromdict(osmTags, "highway") in ["trunk",     "trunk_link"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_roadcycle = factor_roadcycle*coef**-1
            else:
                factor_roadcycle = 0
        elif getfromdict(osmTags, "highway") in ["pedestrian", "bridleway", "footway"]:
            #check access restriction exception
            if getfromdict(osmTags, "bicycle") is not None and  getfromdict(osmTags, "bicycle") != "no":
                factor_roadcycle = factor_roadcycle*1
            else:
                factor_roadcycle = 0
        elif getfromdict(osmTags, "highway") in ["primary",    "primary_link"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_roadcycle = factor_roadcycle*coef**-1
            else:
                factor_roadcycle = factor_roadcycle*coef**2
        elif getfromdict(osmTags, "highway") in ["secondary", "secondary_link"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_roadcycle = factor_roadcycle*coef**-1
            else:
                factor_roadcycle = factor_roadcycle*coef**1.5
        elif getfromdict(osmTags, "highway") in ["tertiary", "tertiary_link", "unclassified"]:
            #check cycleway lane / cycleway tracks
            if (getfromdict(osmTags, "cycleway lane") is not None and  getfromdict(osmTags, "cycleway lane") != "no") or (getfromdict(osmTags, "cycleway tracks") is not None and  getfromdict(osmTags, "cycleway tracks") != "no"):
                factor_roadcycle = factor_roadcycle*coef**-1
            else:
                factor_roadcycle = factor_roadcycle*coef**1
        elif getfromdict(osmTags, "highway") in ["track", "path"]:
            if getfromdict(osmTags, "surface") in ["paved", "asphalt", "concrete", "metal", "wood"]:
                factor_roadcycle = factor_roadcycle
            elif getfromdict(osmTags, "surface") in ["concrete:lanes", "concrete:plates", "paving_stones", "sett"]:
                factor_roadcycle = factor_roadcycle*coef**2
            elif getfromdict(osmTags, "surface") in ["unhewn_cobblestone", "cobblestone", "    compacted", "fine_gravel"]:
                factor_roadcycle = factor_roadcycle*coef**10
            else:
                factor_roadcycle = factor_roadcycle
        elif getfromdict(osmTags, "highway") in ["cycleway"]:
            factor_roadcycle = factor_roadcycle*coef**-1
        factor_roadcycle = int(factor_roadcycle)
        #
        if getfromdict(osmTags, "highway") in ["motorway_link", "motorway", "trunk_link", "primary_link", "secondary_link", "tertiary_link"]:
            factorreverse_roadcycle = -1
        elif getfromdict(osmTags, "junction") == 'roundabout':
            factorreverse_roadcycle = -1
        elif getfromdict(osmTags, "oneway") == 'yes':
            if getfromdict(osmTags, "oneway:bicycle") == 'no':
                factorreverse_roadcycle = 1
            else:
                factorreverse_roadcycle = -1

        #########################################################
        factor_car = 100
        factorreverse_car = 1
        #########################################################
        #check highway
        if getfromdict(osmTags, "highway") in ["steps", "pedestrian", "path", "bridleway", "cycleway", "footway", "bus_guideway", "corridor"]:
            factor_car = 0
        elif getfromdict(osmTags, "highway") in ["track"]:
            factor_car = factor_car*coef**15
        elif getfromdict(osmTags, "highway") in ["motorway_link", "motorway"]:
            factor_car = factor_car*coef**-2
        elif getfromdict(osmTags, "highway") in ["trunk", "trunk_link"]:
            factor_car = factor_car*coef**-1.5
        elif getfromdict(osmTags, "highway") in ["primary", "primary_link"]:
            factor_car = factor_car*coef**-1
        elif getfromdict(osmTags, "highway") in ["secondary", "secondary_link"]:
            factor_car = factor_car*coef**-0.6
        elif getfromdict(osmTags, "highway") in ["tertiary", "tertiary_link"]:
            factor_car = factor_car*coef**-0.3
        elif getfromdict(osmTags, "highway") in ["undefined"]:
            factor_car = factor_car*1
        elif getfromdict(osmTags, "highway") in ["residential"]:
            factor_car = factor_car*coef
        elif getfromdict(osmTags, "highway") in ["living_street"]:
            factor_car = factor_car*coef**2
        #speed
        defaultspeed = {}
        defaultspeed["default"] = 30
        defaultspeed["track"] = 20
        defaultspeed["motorway"] = 130
        defaultspeed["motorway_link"] = 130
        defaultspeed["trunk"] = 110
        defaultspeed["trunk_link"] = 110
        defaultspeed["primary"] = 80
        defaultspeed["primary_link"] = 80
        defaultspeed["secondary"] = 80
        defaultspeed["secondary_link"] = 80
        defaultspeed["tertiary"] = 60
        defaultspeed["tertiary_link"] = 60
        defaultspeed["undefined"] = 60
        defaultspeed["residential"] = 50
        defaultspeed["living_street"] = 30
        maxspeed = 9999
        if getfromdict(osmTags, "maxspeed") is not None:
            tmaxspeed = getfromdict(osmTags, "maxspeed").split(' ')
            if len(tmaxspeed) == 1:
                maxspeed = tmaxspeed[0]
            elif len(tmaxspeed) >= 2:
                if tmaxspeed[1] == 'mph':
                    maxspeed = tmaxspeed[0]*1,60934
        # correction temporaire d'un bug rencontré avec maxspeed qui est parfois un string
        try:
            float(maxspeed)
        except ValueError:
            maxspeed = 9999
        if getfromdict(osmTags, "highway") in defaultspeed.keys():
            speed = min(defaultspeed[getfromdict(osmTags, "highway")],float(maxspeed))
        else:
            speed = min(defaultspeed["default"],float(maxspeed))
        factor_car = factor_car*90/speed
        factor_car = int(factor_car)
        #
        if getfromdict(osmTags, "highway") in ["motorway_link", "motorway", "trunk_link", "primary_link", "secondary_link", "tertiary_link"]:
            factorreverse_car = -1
        elif getfromdict(osmTags, "junction") == 'roundabout':
            factorreverse_car = -1
        elif getfromdict(osmTags, "oneway") == 'yes':
            factorreverse_car = -1

        #print dist
        txt_tags = "ARRAY ["
        for i in range(0, len(osmTags["index"])):
            if i > 0:
                txt_tags = txt_tags + ","
            tag = osmTags["index"][i]
            txt_tags = txt_tags + "'" + tag + "','" + osmTags[tag] + "'"
        txt_tags = txt_tags+"]"
        sql = "INSERT INTO otrouting_ways (id_master, geom_linestring, source, target, dist_m, factor_pedestrian, factor_mountainbike, factor_roadcycle, factor_car, factorreverse_pedestrian, factorreverse_mountainbike, factorreverse_roadcycle, factorreverse_car, tags) VALUES("+str(id_master)+", ST_GeomFromText('"+geom+"',3857), "+str(source)+", "+str(target)+", "+str(int(dist))+", "+str(factor_pedestrian)+", "+str(factor_mountainbike)+", "+str(factor_roadcycle)+", "+str(factor_car)+", "+str(factorreverse_pedestrian)+", "+str(factorreverse_mountainbike)+", "+str(factorreverse_roadcycle)+", "+str(factorreverse_car)+", " + txt_tags + ")"
        #print(sql)
        cur3.execute(sql)

        sql = "SELECT id FROM otrouting_ways ORDER BY id DESC LIMIT 1"
        cur3.execute(sql)
        data3 = cur3.fetchone()
        id = data3[0]
        #print("    id_db: " + str(id))

def create_ways(id_master):
    conn = psycopg2.connect("dbname="+glob_db+" user="+glob_user+" password="+glob_password+" host="+glob_host+" port="+glob_port)
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur3 = conn.cursor()

    #count number of rows to be read
    cur.execute("SELECT COUNT(*) FROM planet_osm_ways")
    data=cur.fetchone()
    n_rows = data[0]
    log("log.txt", "    " + str(n_rows) + " entries in planet_osm_ways table")
    log("log.txt", "    select planet_osm_ways table entries")
    cur.execute("SELECT nodes, tags FROM planet_osm_ways")
    log("log.txt", "    START PROCESSING")
    last_pc = -1
    i_row = 0
    i_geom = 1
    time0 = time.time()
    while True:
        i_row = i_row + 1
        #if i_row == 10:
        #    break
        if int(i_row*1.0/n_rows * 100) > last_pc:
            last_pc = int(i_row*1.0/n_rows * 100)
            log("log.txt", "        " + str(last_pc) + ' %   -   ' + str(int(time.time() - time0)) + "s" )
        data = cur.fetchone()
        if str(data).strip() == "None":
            #all line have been read
            break
        #check if data corresponds to highway
        osmTags = read_osm_tag(data[1], [])
        if "highway" in osmTags["index"]:
            # get nodes data from _work_otrouting_osm_nodes_ninter table
            sql = "SELECT id, ST_AsText(geom_point) AS geom, ninter FROM _work_otrouting_osm_nodes_ninter WHERE id IN ("
            tNodes = data[0]
            #DEBUG
            #if i_row == 2411:
            #    print(str(tNodes))
            for i in range(0, len(tNodes)):
                if i > 0:
                        sql = sql + ","
                sql = sql + str(tNodes[i])
                #if tNodes[i] == 51413854 or tNodes[i] == 51414015:
                #    print(str(tNodes[i]) + ' :' + str(tNodes))
            sql = sql + ")"
            cur2.execute(sql)
            dictNodes = {}
            while True:
                data2 = cur2.fetchone()
                if str(data2).strip() != "None":
                    id_geom = data2[0]
                    geom_point = data2[1]
                    geom_point = geom_point.replace("POINT(","")
                    geom_point = geom_point.replace(")","")
                    ninter = data2[2]
                    dictNodes[str(id_geom)] = {}
                    dictNodes[str(id_geom)]['ninter'] = ninter
                    dictNodes[str(id_geom)]['geom_point'] = geom_point
                else:
                    break
            #
            for i in range(0, len(tNodes)):
                #DEBUG
                #if i_row == 2411:
                #    print("      id_node,ninter: " + str(tNodes[i]) + ',' + str(dictNodes[str(tNodes[i])]['ninter']))
                if i == 0:
                    # if first point
                    source = tNodes[i] 
                    tLonLat = []
                    dist = 0
                    lonlat = dictNodes[str(tNodes[i])]['geom_point'].split(' ')
                    tLonLat.append(lonlat)
                else:
                    lonlat = dictNodes[str(tNodes[i])]['geom_point'].split(' ')
                    
                    #lonlat1 = tLonLat[len(tLonLat)-1]
                    #lonlat0 = tLonLat[len(tLonLat)-2]
                    #dist2 = ((float(lonlat1[0])-float(lonlat0[0]))**2+(float(lonlat1[1])-float(lonlat0[1]))**2)**0.5
                    
                    lonlat1 = lonlat3857to4326(lonlat)
                    lonlat0 = lonlat3857to4326(tLonLat[len(tLonLat)-1])
                    dist2 = getdistancefromlonlat4326(lonlat1, lonlat0)

                    tLonLat.append(lonlat)
                    dist = dist + dist2
                    if dictNodes[str(tNodes[i])]['ninter'] > 1:
                        target = tNodes[i]
                        add_geom_linestring(cur3, osmTags, tLonLat, source, target, dist, id_master)
                        #reinit geom for next edge
                        tLonLat = []
                        source = tNodes[i]
                        dist = 0
                        tLonLat.append(lonlat)

    log("log.txt", "    ALL ROWS READ IN " + str(int(time.time() - time0)) + "s")
    
    conn.commit()
    cur.close()
    cur2.close()
    cur3.close()
    conn.close()

def lonlat3857to4326(lonlat3857):
    lonlat4326 = [0,0]
    #formula from https://gist.github.com/onderaltintas/6649521
    lonlat4326[0] = float(lonlat3857[0]) *  180 / 20037508.34 ;
    lonlat4326[1] = math.atan(math.exp(float(lonlat3857[1]) * math.pi / 20037508.34)) * 360 / math.pi - 90;
    return lonlat4326

def getdistancefromlonlat4326(lonlat1, lonlat2):
    #check distance
    theta1 = float(lonlat1[0]) * 3.1415 / 180.0
    theta2 = float(lonlat2[0]) * 3.1415 / 180.0
    phi1 = float(lonlat1[1]) * 3.1415 / 180.0
    phi2 = float(lonlat2[1]) * 3.1415 / 180.0
    Rt = 6371000.0 #earth radius in meters
    Rtheta = Rt * math.cos((phi1 + phi2) / 2)
    lengthPhi = abs(phi2 - phi1) * Rt
    lengthTheta = abs(theta2 - theta1) * Rtheta
    geodesicLengthApprox_m = math.pow(math.pow(lengthTheta, 2) + math.pow(lengthPhi, 2), 0.5)
    
    return geodesicLengthApprox_m

def _____main_____():
    
    log("log.txt", "",True)

    # list all inputs
    for i in range(len(glob_t_input)): 
        log("log.txt", str(i+1) + " - " + str(glob_t_input[i]))

    for i in range(len(glob_t_input)): 
        log("log.txt",'')    
        log("log.txt",'')    
        log("log.txt",'')    

        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", "deal with "+str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")

        log("log.txt", "initialisation")
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        init()

        log("log.txt", "")
        log("log.txt", "upload data from download.geofabrik.de" + " - " +str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        #upload_data(glob_t_input[i])

        log("log.txt", "")
        log("log.txt", "update master database" + " - "+str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        id_master = update_master_start(glob_t_input[i])

        log("log.txt", "")
        log("log.txt", "import osm data with osm2pgsql" + " - " +str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        osm2pgsql(glob_t_input[i])

        log("log.txt", "")
        log("log.txt", "read osm data and populate _work_otrouting_osm_nodes_ninter table" + " - " +str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        create_points(id_master)

        log("log.txt", "")
        log("log.txt", "read osm data and populate otrouting_ways table" + " - " +str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        create_ways(id_master)

        log("log.txt", "")
        log("log.txt", "update master database" + " - " +str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        update_master_complete(glob_t_input[i])

        log("log.txt", "")
        log("log.txt", "clean database" + " - " +str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        clean_db()

         #cmd = 'wget  -O  '+txt.replace("/","_")+'-latest.osm.bz2 "http://download.geofabrik.de/'+txt+'-latest.osm.bz2"'
         #print(cmd)
         #cmd = 'wget  -O  '+txt.replace("/","_")+'.poly "http://download.geofabrik.de/'+txt+'.poly"'
        #print subprocess.check_output([cmd.split(' ')])
        #os.system(cmd)
        #cmd = cmd.split('  ')
        #print subprocess.call(["ls"])
        log("log.txt",'')
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))    
        log("log.txt",'')    
        log("log.txt",'')    
        log("log.txt",'')    

_____main_____()
