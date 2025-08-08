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

    sql = """
    CREATE OR REPLACE FUNCTION get_tag(tags text[], key text)
    RETURNS text AS $$
    DECLARE
        val text;
    BEGIN
        FOR i IN 1..array_length(tags, 1) BY 2 LOOP
            IF tags[i] = key THEN
                RETURN tags[i+1];
            END IF;
        END LOOP;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """
    cur.execute(sql)

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
    style = r"D:\Utilisateur\Louis Peller\STAGE\osm2pgsql-bin\default.style" #osm2pgsql default.style file location, used with windows
    cmd = ['osm2pgsql', '--slim', '-C', '100', '-d', 'db_osm_routing', '-U', 'user', '-H', 'localhost', '-P', '5432', '-S', style, 'rhone-alpes-latest.osm.bz2']
    #cmd = ['osm2pgsql','--slim', '-C', '100', '-d', glob_db, '-U', glob_user, '-H', glob_host, '-P', glob_port, temp_path]
    log("log.txt", '    > subprocess.check_output(' + str(cmd) + ')')
    log("log.txt", '        start: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))
    subprocess.check_output(cmd)
    log("log.txt", '        end: '+str(time.strftime("%Y-%m-%d %H:%M:%S")))


def process_osm_data_sql(id_master):
    conn = psycopg2.connect("dbname="+glob_db+" user="+glob_user+" password="+glob_password+" host="+glob_host+" port="+glob_port)
    cur = conn.cursor()

    log("log.txt", '    TRUNCATE _work_otrouting_osm_nodes_ninter')
    cur.execute("TRUNCATE _work_otrouting_osm_nodes_ninter")

    log("log.txt", "    Populating _work_otrouting_osm_nodes_ninter table")
    sql = """
    INSERT INTO _work_otrouting_osm_nodes_ninter (id, geom_point, ninter)
    WITH all_nodes AS (
        SELECT unnest(nodes) as node_id
        FROM planet_osm_ways
        WHERE tags -> 'highway' IS NOT NULL
    )
    SELECT
        n.id,
        ST_Transform(ST_SetSRID(ST_MakePoint(n.lon / 10000000.0, n.lat / 10000000.0), 4326), 3857),
        counts.ninter
    FROM
        planet_osm_nodes n
    JOIN
        (SELECT node_id, count(*) as ninter FROM all_nodes GROUP BY node_id) as counts ON n.id = counts.node_id;
    """
    cur.execute(sql)

    log("log.txt", "    DELETE from otrouting_points")
    cur.execute("DELETE FROM otrouting_points WHERE id_master = %s", (id_master,))

    log("log.txt", "    Populating otrouting_points table")
    sql = """
    INSERT INTO otrouting_points (id, id_master, geom_point)
    SELECT
        id,
        %s,
        geom_point
    FROM
        _work_otrouting_osm_nodes_ninter
    WHERE ninter > 1;
    """
    cur.execute(sql, (id_master,))

    log("log.txt", "    DELETE from otrouting_ways")
    cur.execute("DELETE FROM otrouting_ways WHERE id_master = %s", (id_master,))

    log("log.txt", "    Populating otrouting_ways table")
    sql = """
    WITH ways_with_geom AS (
        SELECT
            w.osm_id,
            w.tags,
            w.nodes,
            (SELECT ST_MakeLine(n.geom_point ORDER BY u.ord)
             FROM unnest(w.nodes) WITH ORDINALITY AS u(node_id, ord)
             JOIN _work_otrouting_osm_nodes_ninter n ON n.id = u.node_id
            ) as geom
        FROM
            planet_osm_ways w
        WHERE
            w.tags -> 'highway' IS NOT NULL
    ),
    split_ways AS (
        SELECT
            w.osm_id,
            w.tags,
            w.nodes,
            (ST_Dump(
                ST_Split(w.geom, (SELECT ST_Collect(geom_point) FROM otrouting_points WHERE id_master = %s))
            )).geom as geom
        FROM
            ways_with_geom w
    )
    INSERT INTO otrouting_ways (id_master, geom_linestring, source, target, dist_m, factor_pedestrian, factor_mountainbike, factor_roadcycle, factor_car, factorreverse_pedestrian, factorreverse_mountainbike, factorreverse_roadcycle, factorreverse_car, tags)
    SELECT
        %s,
        s.geom,
        ST_StartPoint(s.geom),
        ST_EndPoint(s.geom),
        ST_Length(s.geom),
        CASE
            WHEN get_tag(s.tags, 'highway') IN ('motorway_link', 'motorway', 'bus_guideway', 'escape', 'raceway') THEN 0
            WHEN get_tag(s.tags, 'highway') IN ('trunk', 'trunk_link') THEN
                CASE WHEN get_tag(s.tags, 'sidewalk') IS NOT NULL AND get_tag(s.tags, 'sidewalk') != 'no' THEN 100 * 1.15^4 ELSE 0 END
            WHEN get_tag(s.tags, 'highway') IN ('primary', 'primary_link') THEN
                CASE WHEN get_tag(s.tags, 'sidewalk') IS NOT NULL AND get_tag(s.tags, 'sidewalk') != 'no' THEN 1 ELSE 100 * 1.15^3 END
            WHEN get_tag(s.tags, 'highway') IN ('secondary', 'secondary_link') THEN
                CASE WHEN get_tag(s.tags, 'sidewalk') IS NOT NULL AND get_tag(s.tags, 'sidewalk') != 'no' THEN 1 ELSE 100 * 1.15^2 END
            WHEN get_tag(s.tags, 'highway') IN ('tertiary', 'tertiary_link', 'unclassified') THEN
                CASE WHEN get_tag(s.tags, 'sidewalk') IS NOT NULL AND get_tag(s.tags, 'sidewalk') != 'no' THEN 1 ELSE 100 * 1.15 END
            WHEN get_tag(s.tags, 'highway') = 'track' THEN 100 * 1.15^-1
            WHEN get_tag(s.tags, 'highway') IN ('cycleway', 'bridleway') THEN
                CASE WHEN get_tag(s.tags, 'foot') IS NOT NULL AND get_tag(s.tags, 'foot') != 'no' THEN 100 * 1.15^-1 ELSE 0 END
            WHEN get_tag(s.tags, 'highway') IN ('pedestrian', 'footway', 'path') THEN 100 * 1.15^-2
            ELSE 100
        END AS factor_pedestrian,
        CASE
            WHEN get_tag(s.tags, 'highway') IN ('motorway_link', 'motorway', 'bus_guideway', 'corridor', 'escape', 'raceway') THEN 0
            WHEN get_tag(s.tags, 'highway') = 'steps' THEN 100 * 1.15^15
            WHEN get_tag(s.tags, 'highway') IN ('trunk', 'trunk_link') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 0 END
            WHEN get_tag(s.tags, 'highway') IN ('pedestrian', 'bridleway', 'footway') THEN
                CASE WHEN get_tag(s.tags, 'bicycle') IS NOT NULL AND get_tag(s.tags, 'bicycle') != 'no' THEN 100 ELSE 0 END
            WHEN get_tag(s.tags, 'highway') IN ('primary', 'primary_link') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 100 * 1.15^3 END
            WHEN get_tag(s.tags, 'highway') IN ('secondary', 'secondary_link') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 100 * 1.15^2 END
            WHEN get_tag(s.tags, 'highway') IN ('tertiary', 'tertiary_link', 'unclassified') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 100 * 1.15 END
            WHEN get_tag(s.tags, 'highway') IN ('track', 'cycleway', 'path') THEN 100 * 1.15^-1
            ELSE 100
        END AS factor_mountainbike,
        CASE
            WHEN get_tag(s.tags, 'highway') IN ('motorway_link', 'motorway', 'bus_guideway', 'corridor', 'escape', 'raceway', 'steps') THEN 0
            WHEN get_tag(s.tags, 'highway') IN ('trunk', 'trunk_link') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 0 END
            WHEN get_tag(s.tags, 'highway') IN ('pedestrian', 'bridleway', 'footway') THEN
                CASE WHEN get_tag(s.tags, 'bicycle') IS NOT NULL AND get_tag(s.tags, 'bicycle') != 'no' THEN 100 ELSE 0 END
            WHEN get_tag(s.tags, 'highway') IN ('primary', 'primary_link') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 100 * 1.15^2 END
            WHEN get_tag(s.tags, 'highway') IN ('secondary', 'secondary_link') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 100 * 1.15^1.5 END
            WHEN get_tag(s.tags, 'highway') IN ('tertiary', 'tertiary_link', 'unclassified') THEN
                CASE WHEN (get_tag(s.tags, 'cycleway lane') IS NOT NULL AND get_tag(s.tags, 'cycleway lane') != 'no') OR (get_tag(s.tags, 'cycleway tracks') IS NOT NULL AND get_tag(s.tags, 'cycleway tracks') != 'no') THEN 100 * 1.15^-1 ELSE 100 * 1.15 END
            WHEN get_tag(s.tags, 'highway') IN ('track', 'path') THEN
                CASE
                    WHEN get_tag(s.tags, 'surface') IN ('paved', 'asphalt', 'concrete', 'metal', 'wood') THEN 100
                    WHEN get_tag(s.tags, 'surface') IN ('concrete:lanes', 'concrete:plates', 'paving_stones', 'sett') THEN 100 * 1.15^2
                    WHEN get_tag(s.tags, 'surface') IN ('unhewn_cobblestone', 'cobblestone', 'compacted', 'fine_gravel') THEN 100 * 1.15^10
                    ELSE 100
                END
            WHEN get_tag(s.tags, 'highway') = 'cycleway' THEN 100 * 1.15^-1
            ELSE 100
        END AS factor_roadcycle,
        CASE
            WHEN get_tag(s.tags, 'highway') IN ('steps', 'pedestrian', 'path', 'bridleway', 'cycleway', 'footway', 'bus_guideway', 'corridor') THEN 0
            WHEN get_tag(s.tags, 'highway') = 'track' THEN 100 * 1.15^15
            WHEN get_tag(s.tags, 'highway') IN ('motorway_link', 'motorway') THEN 100 * 1.15^-2
            WHEN get_tag(s.tags, 'highway') IN ('trunk', 'trunk_link') THEN 100 * 1.15^-1.5
            WHEN get_tag(s.tags, 'highway') IN ('primary', 'primary_link') THEN 100 * 1.15^-1
            WHEN get_tag(s.tags, 'highway') IN ('secondary', 'secondary_link') THEN 100 * 1.15^-0.6
            WHEN get_tag(s.tags, 'highway') IN ('tertiary', 'tertiary_link') THEN 100 * 1.15^-0.3
            WHEN get_tag(s.tags, 'highway') = 'unclassified' THEN 100
            WHEN get_tag(s.tags, 'highway') = 'residential' THEN 100 * 1.15
            WHEN get_tag(s.tags, 'highway') = 'living_street' THEN 100 * 1.15^2
            ELSE 100
        END AS factor_car,
        1, 1, 1, 1, s.tags
    FROM split_ways s;
    """
    cur.execute(sql, (id_master, id_master))


    conn.commit()
    cur.close()
    conn.close()

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
        log("log.txt", "read osm data and populate database" + " - " +str(glob_t_input[i])+" "+str(i+1)+"/"+str(len(glob_t_input)))
        log("log.txt", "------------------------------------------------------------------------------")
        log("log.txt", str(time.strftime("%Y-%m-%d %H:%M:%S")))
        process_osm_data_sql(id_master)

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
