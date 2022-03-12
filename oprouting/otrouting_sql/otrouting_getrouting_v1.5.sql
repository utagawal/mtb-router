-- v1.3 Julien SENTIER
--       in line with otrouting_v1.1.py
-- v1.4 20/10/2020 Julien SENTIER
--       add routingtype parameter: pedestrian / mountainbike / roadcycle / car value
--       in line with otrouting_v1.2.py
-- v1.5 21/11/2021 Julien SENTIER
--       update limite for boundary box for djikstra call (10000m replaced by min(10000,max(300,dist(source,target)/2))
--       limite for boundary box for closest way set to 100m 
--       introduction of coefdistmetersto3852 to consider distance in meters to be in line with otrouting_v1.3 distance
--       consideration of ST_Intersects in sql WHERE requests
--       geom_center replaced by geom_linestring in sql WHERE requests (table otrouting_ways)
--       dist_3857_m renamed to dist_m
--
-- see test expression at the end
--
DROP FUNCTION IF EXISTS otrouting_getrouting(double precision,double precision,double precision,double precision);
DROP TABLE IF EXISTS _variable_otrouting_closestway;
DROP TABLE IF EXISTS _variable_otrouting_closestpoint;
DROP TABLE IF EXISTS _temp_otrouting_points;
DROP TABLE IF EXISTS _temp_otrouting_ways;
DROP TABLE IF EXISTS _temp_notice;
CREATE TABLE _temp_notice
(
    id bigserial PRIMARY KEY,
    notice text
);
CREATE TABLE _variable_otrouting_closestway
(
    id bigint, 
    dist FLOAT,
    geom_linestring geometry(LineString,3857),
    source bigint,
    target bigint,
    factor_pedestrian integer,
    factor_mountainbike integer,
    factor_roadcycle integer,
    factor_car integer,
    factorreverse_pedestrian integer,
    factorreverse_mountainbike integer,
    factorreverse_roadcycle integer,
    factorreverse_car integer
);
CREATE TABLE _variable_otrouting_closestpoint
(
    id bigint, 
    dist FLOAT
);
CREATE TABLE _temp_otrouting_points
(
    id bigserial PRIMARY KEY,
    geom_point geometry(Point,3857),
    timestamp integer,
    token integer
);
CREATE TABLE _temp_otrouting_ways
(
    id bigserial PRIMARY KEY,
    geom_linestring geometry(LineString,3857),
    source bigint,
    target bigint,
    dist_m integer,
    factor_pedestrian integer,
    factor_mountainbike integer,
    factor_roadcycle integer,
    factor_car integer,
    factorreverse_pedestrian integer,
    factorreverse_mountainbike integer,
    factorreverse_roadcycle integer,
    factorreverse_car integer,
    timestamp integer,
    token integer
);

CREATE OR REPLACE FUNCTION otrouting_getrouting(
    lon1 FLOAT, 
    lat1 FLOAT,
    lon2 FLOAT, 
    lat2 FLOAT,
    routingtype TEXT)
--RETURNS TABLE (seq integer, node bigint, edge bigint, lonlat TEXT[]) AS $$
RETURNS TABLE (lonlat text[]) AS $$
#variable_conflict use_column
DECLARE 
    point1 geometry(Point,3857);
    point1_4326 geometry(Point,4326);
    point11 geometry(Point,3857);
    point11_4326 geometry(Point,4326);
    point2 geometry(Point,3857);
    point2_4326 geometry(Point,4326);
    point3 geometry(Point,3857);
    linestring1 geometry(LineString,3857);
    linestring2 geometry(LineString,3857);
    tableway1 _variable_otrouting_closestway;
    tableway2 _variable_otrouting_closestway;
    tablepoint1 _variable_otrouting_closestpoint;
    count INT;
    proj1 geometry(Point,3857);
    proj1_linestring geometry(LineString,3857);
    proj2 geometry(Point,3857);
    proj12_multilinestring geometry(MultiLineString,3857);
    proj2_linestring geometry(LineString,3857);
    text1 TEXT;
    text11 TEXT;
    text22 TEXT;
    text_tab1 TEXT[] = '{}';
    text_tab2 TEXT[] = '{}';
    point1_tab1 FLOAT[] = '{}';
    point2_tab1 FLOAT[] = '{}';
    proj1_tab1 FLOAT[] = '{}';
    proj2_tab1 FLOAT[] = '{}';
    proj1split_tab1 FLOAT[] = '{}';
    proj2split_tab1 FLOAT[] = '{}';
    flot_tab1 FLOAT[] = '{}';
    djikstra_out TEXT[] = '{}';
    djikstra_out_edges bigint[] = '{}';
    lonlat_out TEXT[] = '{}';
    text4 TEXT[];
    var_r record;
    a integer[] = array[1,2,3];
    i bigint;
    source bigint;
    text_source TEXT;
    target bigint;
    timestampNow integer;
    timestampMax integer;
    token_f integer;
    dist FLOAT;
    dist_m FLOAT;
    dist_3852 FLOAT;
    coefdistmetersto3852 FLOAT;
    lonmin_loc INT;
    lonmax_loc INT;
    latmin_loc INT;
    latmax_loc INT;
    lonmin_loc2 INT;
    lonmax_loc2 INT;
    latmin_loc2 INT;
    latmax_loc2 INT;
    lon_middle INT;
    lat_middle INT;
    delta INT;
    t_id BIGINT[] = '{}';
BEGIN
    DELETE FROM _temp_notice;
    -- get timestamp and token
    timestampNow := EXTRACT(EPOCH FROM NOW())::integer;
    token_f := random() * 100000000::integer ;
    -- RAISE NOTICE'timestampNow: %', timestampNow;
    -- RAISE NOTICE'token: %', token_f;
    -- RAISE NOTICE'';

    -- define postGIS STRATING and ENDING point
    SELECT INTO point1_4326 ST_GeomFromText('POINT(' || lon1 || ' ' || lat1 || ')',4326);
    SELECT INTO point1 ST_Transform(point1_4326,3857);
    SELECT INTO point2_4326 ST_GeomFromText('POINT(' || lon2 || ' ' || lat2 || ')',4326);
    SELECT INTO point2 ST_Transform(point2_4326,3857);

    -- RAISE NOTICE'Start: %', ST_AsText(ST_Transform(point1,4326));
    -- RAISE NOTICE'End: %', ST_AsText(ST_Transform(point2,4326));
    -- RAISE NOTICE'';
    -- RAISE NOTICE'Start3857: %', ST_AsText(point1);
    -- RAISE NOTICE'End3857: %', ST_AsText(point2);
    -- RAISE NOTICE'';

    SELECT title FROM otrouting_master WHERE ST_Contains(geom_polygon, point1) AND status='completed' INTO text11;
    SELECT title FROM otrouting_master WHERE ST_Contains(geom_polygon, point2) AND status='completed' INTO text22;
    -- RAISE NOTICE'Start area: %', text11;
    -- RAISE NOTICE'End area: %', text22;
    -- RAISE NOTICE'';

    SELECT INTO point11 ST_GeomFromText('POINT(' || ST_X(point1)+100 || ' ' || ST_Y(point1)+100 || ')',3857);
    SELECT INTO point11_4326 ST_Transform(point11,4326);
    SELECT INTO dist_m ST_DistanceSphere(point1_4326, point11_4326);
    SELECT INTO dist_3852 ST_Distance(point1, point11);
    SELECT INTO coefdistmetersto3852 dist_3852/dist_m;
    -- RAISE NOTICE'dist_m: %', dist_m;
    -- RAISE NOTICE'dist_3852: %', dist_3852;
    -- RAISE NOTICE'coefdistmetersto3852: %', coefdistmetersto3852;
    -- RAISE NOTICE'';

    IF text11 IS NOT NULL AND text22 IS NOT NULL THEN
        -- get distance between start and end
        dist := ST_Distance(point2, point1);
        -- RAISE NOTICE'dist Strat to End: %', dist;
        -- RAISE NOTICE'';
        
        -- get closest ways
        -- define boundary box for get closest way request
        lonmin_loc := LEAST(ST_X(point1),ST_X(point1))-100*coefdistmetersto3852;
        lonmax_loc := GREATEST(ST_X(point1),ST_X(point1))+100*coefdistmetersto3852;
        latmin_loc := LEAST(ST_Y(point1),ST_Y(point1))-100*coefdistmetersto3852;
        latmax_loc := GREATEST(ST_Y(point1),ST_Y(point1))+100*coefdistmetersto3852;
        lonmin_loc2 := LEAST(ST_X(point2),ST_X(point2))-100*coefdistmetersto3852;
        lonmax_loc2 := GREATEST(ST_X(point2),ST_X(point2))+100*coefdistmetersto3852;
        latmin_loc2 := LEAST(ST_Y(point2),ST_Y(point2))-100*coefdistmetersto3852;
        latmax_loc2 := GREATEST(ST_Y(point2),ST_Y(point2))+100*coefdistmetersto3852;
        IF routingtype = 'pedestrian' THEN
            SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point1) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway1 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc, latmin_loc, lonmax_loc, latmax_loc, 3857)) AND factor_pedestrian > 0 ORDER BY dist ASC LIMIT 1;
            SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point2) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway2 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc2, latmin_loc2, lonmax_loc2, latmax_loc2, 3857)) AND factor_pedestrian > 0 ORDER BY dist ASC LIMIT 1;
        ELSEIF routingtype = 'mountainbike' THEN
            SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point1) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway1 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc, latmin_loc, lonmax_loc, latmax_loc, 3857)) AND factor_mountainbike > 0 ORDER BY dist ASC LIMIT 1;
            SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point2) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway2 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc2, latmin_loc2, lonmax_loc2, latmax_loc2, 3857)) AND factor_mountainbike > 0 ORDER BY dist ASC LIMIT 1;
        ELSEIF routingtype = 'roadcycle' THEN
             SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point1) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway1 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc, latmin_loc, lonmax_loc, latmax_loc, 3857)) AND factor_roadcycle > 0 ORDER BY dist ASC LIMIT 1;
            SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point2) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway2 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc2, latmin_loc2, lonmax_loc2, latmax_loc2, 3857)) AND factor_roadcycle > 0 ORDER BY dist ASC LIMIT 1;
        ELSEIF routingtype = 'car' THEN
            SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point1) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway1 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc, latmin_loc, lonmax_loc, latmax_loc, 3857)) AND factor_car > 0 ORDER BY dist ASC LIMIT 1;
            SELECT  otrouting_ways.id AS id, 
                    ST_Distance(otrouting_ways.geom_linestring, point2) AS dist, 
                    otrouting_ways.geom_linestring,
                    otrouting_ways.source,
                    otrouting_ways.target,
                    otrouting_ways.factor_pedestrian,
                    otrouting_ways.factor_mountainbike,
                    otrouting_ways.factor_roadcycle,
                    otrouting_ways.factor_car,
                    otrouting_ways.factorreverse_pedestrian,
                    otrouting_ways.factorreverse_mountainbike,
                    otrouting_ways.factorreverse_roadcycle,
                    otrouting_ways.factorreverse_car
                INTO tableway2 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc2, latmin_loc2, lonmax_loc2, latmax_loc2, 3857)) AND factor_car > 0 ORDER BY dist ASC LIMIT 1;
        END IF;

        --get projection
        SELECT ST_ClosestPoint(tableway1.geom_linestring, point1) INTO proj1;
        SELECT ST_ClosestPoint(tableway2.geom_linestring, point2) INTO proj2;
        -- RAISE NOTICE'Start proj: %', ST_AsText(ST_Transform(proj1,4326));
        -- RAISE NOTICE'End proj: %', ST_AsText(ST_Transform(proj2,4326));
        -- RAISE NOTICE'';
        -- RAISE NOTICE'dist Start to Start proj: %', ST_Distance(point1, proj1);
        -- RAISE NOTICE'dist End to End proj: %', ST_Distance(point2, proj2);
        -- RAISE NOTICE'';


        IF proj1 IS NOT NULL AND proj2 IS NOT NULL THEN
            ------------------------------------------------------------
            --split starting and ending edges
            --convert point1 geom to coord array------------------------
            text1 := ST_AsText(point1);
            text1 := replace(replace(text1,'POINT(',''),')','');
            text_tab1 := regexp_split_to_array(text1,  E'\\s+');
            point1_tab1[1] := CAST (text_tab1[1] AS FLOAT);
            point1_tab1[2] := CAST (text_tab1[2] AS FLOAT);
            --convert point2 geom to coord array-------------------------
            text1 := ST_AsText(point2);
            text1 := replace(replace(text1,'POINT(',''),')','');
            text_tab1 := regexp_split_to_array(text1,  E'\\s+');
            point2_tab1[1] := CAST (text_tab1[1] AS FLOAT);
            point2_tab1[2] := CAST (text_tab1[2] AS FLOAT);
            --convert proj1 geom to coord array----------------------------
            text1 := ST_AsText(proj1);
            text1 := replace(replace(text1,'POINT(',''),')','');
            text_tab1 := regexp_split_to_array(text1,  E'\\s+');
            proj1_tab1[1] := CAST (text_tab1[1] AS FLOAT);
            proj1_tab1[2] := CAST (text_tab1[2] AS FLOAT);
            --convert proj2 geom to coord array----------------------------
            text1 := ST_AsText(proj2);
            text1 := replace(replace(text1,'POINT(',''),')','');
            text_tab1 := regexp_split_to_array(text1,  E'\\s+');
            proj2_tab1[1] := CAST (text_tab1[1] AS FLOAT);
            proj2_tab1[2] := CAST (text_tab1[2] AS FLOAT);
            --compute projsplit coord for split linestring ----------------
            IF ST_Distance(point1, proj1) > 1 THEN
                proj1split_tab1[1] = point1_tab1[1] + (proj1_tab1[1] - point1_tab1[1])*(tableway1.dist+0.1)/tableway1.dist;
                proj1split_tab1[2] = point1_tab1[2] + (proj1_tab1[2] - point1_tab1[2])*(tableway1.dist+0.1)/tableway1.dist;
                text11 := CAST(point1_tab1[1] AS TEXT) || ' ' || CAST (point1_tab1[2] AS TEXT) || ',' || CAST (proj1split_tab1[1] AS TEXT) || ' ' || CAST (proj1split_tab1[2] AS TEXT);
            ELSE
                text11 := CAST(proj1_tab1[1]+1 AS TEXT) || ' ' || CAST (proj1_tab1[2]+1 AS TEXT) || ',' || CAST (proj1_tab1[1]-1 AS TEXT) || ' ' || CAST (proj1_tab1[2]-1 AS TEXT);
            END IF;
            IF ST_Distance(point2, proj2) > 1 THEN
                proj2split_tab1[1] = point2_tab1[1] + (proj2_tab1[1] - point2_tab1[1])*(tableway2.dist+0.1)/tableway2.dist;
                proj2split_tab1[2] = point2_tab1[2] + (proj2_tab1[2] - point2_tab1[2])*(tableway2.dist+0.1)/tableway2.dist;
                text22 := CAST(point2_tab1[1] AS TEXT) || ' ' || CAST (point2_tab1[2] AS TEXT) || ',' || CAST (proj2split_tab1[1] AS TEXT) || ' ' || CAST (proj2split_tab1[2] AS TEXT);
            ELSE
                text22 := CAST(proj2_tab1[1]+1 AS TEXT) || ' ' || CAST (proj2_tab1[2]+1 AS TEXT) || ',' || CAST (proj2_tab1[1]-1 AS TEXT) || ' ' || CAST (proj2_tab1[2]-1 AS TEXT);
            END IF;
            --create proj_linestring ----------------------------------------
            proj1_linestring := ST_GeomFromText('LINESTRING(' || text11 || ')',3857);
            proj2_linestring := ST_GeomFromText('LINESTRING(' || text22 || ')',3857);
            proj12_multilinestring := ST_GeomFromText('MULTILINESTRING(('|| text11 
                                                                        || '),(' 
                                                                        || text22 
                                                      || '))',3857);
            -- -- RAISE NOTICE'starting edge: %', tableway1.id;
            INSERT INTO _temp_notice (notice) VALUES ('starting edge: ' || tableway1.id::text);
            -- -- RAISE NOTICE'ending edge: %', tableway2.id;
            INSERT INTO _temp_notice (notice) VALUES ('ending edge: ' || tableway2.id::text);
            SELECT geom_linestring FROM otrouting_ways WHERE id = tableway1.id INTO linestring1;
            SELECT geom_linestring FROM otrouting_ways WHERE id = tableway2.id INTO linestring2;

            ---- RAISE NOTICE'';
            ---- RAISE NOTICE'Start edge: %', ST_AsText(ST_Transform(linestring1,4326));
            ---- RAISE NOTICE'End edge: %', ST_AsText(ST_Transform(linestring2,4326));
            ---- RAISE NOTICE'';

            IF (tableway1.id != tableway2.id) THEN
                -- RAISE NOTICE'starting and ending point on different edges';
                -- RAISE NOTICE'';
                --split linestring closest to the starting point----------------------------------------------------------
                text1 := ST_AsText(ST_CollectionExtract(ST_Split(tableway1.geom_linestring, proj1_linestring),2));
                text1 := replace(replace(text1,'MULTILINESTRING((',''),'))','');
                text_tab1 := string_to_array(text1,  '),(');
                IF array_upper(text_tab1, 1) > 1 THEN
                    source = tableway1.source;
                    FOR i IN 1 .. array_upper(text_tab1, 1) LOOP
                        IF i < array_upper(text_tab1, 1) THEN
                            --add last point (intersection point) of the linestring into 
                            text_tab2 := string_to_array(text_tab1[i],  ',');
                            point3 := ST_GeomFromText('POINT(' || text_tab2[array_upper(text_tab2, 1)] || ')', 3857);
                            INSERT INTO _temp_otrouting_points(geom_point, timestamp, token) VALUES (point3, timestampNow, token_f);
                            SELECT -_temp_otrouting_points.id INTO target FROM _temp_otrouting_points WHERE geom_point = point3 AND token = token_f;
                        ELSE
                            target = tableway1.target;
                        END IF;
                        --insert split linestring into _temp_otrouting_ways

                        linestring1 := ST_GeomFromText('LINESTRING(' || text_tab1[i] || ')', 3857);
                        INSERT INTO _temp_otrouting_ways    (geom_linestring, source, target, dist_m,
                            factor_pedestrian, factor_mountainbike, factor_roadcycle, factor_car,
                            factorreverse_pedestrian, factorreverse_mountainbike, factorreverse_roadcycle, factorreverse_car,
                            timestamp, token) 
                            VALUES (linestring1, source, target, ST_Length(linestring1)/coefdistmetersto3852,
                            tableway1.factor_pedestrian, tableway1.factor_mountainbike, tableway1.factor_roadcycle, tableway1.factor_car,
                            tableway1.factorreverse_pedestrian, tableway1.factorreverse_mountainbike, tableway1.factorreverse_roadcycle, tableway1.factorreverse_car,
                            timestampNow,   token_f);
                        source := target;
                    END LOOP;
                END IF;
                --split linestring closest to the ending point----------------------------------------------------------
                text1 := ST_AsText(ST_CollectionExtract(ST_Split(tableway2.geom_linestring, proj2_linestring),2));
                text1 := replace(replace(text1,'MULTILINESTRING((',''),'))','');
                text_tab1 := string_to_array(text1,  '),(');
                IF array_upper(text_tab1, 1) > 1 THEN
                    source = tableway2.source;
                    FOR i IN 1 .. array_upper(text_tab1, 1) LOOP
                        IF i < array_upper(text_tab1, 1) THEN
                            --add last point (intersection point) of the linestring into 
                            text_tab2 := string_to_array(text_tab1[i],  ',');
                            point3 := ST_GeomFromText('POINT(' || text_tab2[array_upper(text_tab2, 1)] || ')', 3857);
                            INSERT INTO _temp_otrouting_points(geom_point, timestamp, token) VALUES (point3, timestampNow, token_f);
                            SELECT -_temp_otrouting_points.id INTO target FROM _temp_otrouting_points WHERE geom_point = point3  AND token = token_f;
                        ELSE
                            target = tableway2.target;
                        END IF;
                        --insert split linestring into _temp_otrouting_ways
                        linestring1 := ST_GeomFromText('LINESTRING(' || text_tab1[i] || ')', 3857);
                        INSERT INTO _temp_otrouting_ways    (geom_linestring,   source, target, dist_m,
                            factor_pedestrian, factor_mountainbike, factor_roadcycle, factor_car,
                            factorreverse_pedestrian, factorreverse_mountainbike, factorreverse_roadcycle, factorreverse_car,
                            timestamp, token) 
                            VALUES (linestring1, source, target, ST_Length(linestring1)/coefdistmetersto3852,
                            tableway2.factor_pedestrian, tableway2.factor_mountainbike, tableway2.factor_roadcycle, tableway2.factor_car,
                            tableway2.factorreverse_pedestrian, tableway2.factorreverse_mountainbike, tableway2.factorreverse_roadcycle, tableway2.factorreverse_car,
                            timestampNow, token_f);
                        source := target;
                    END LOOP;
                END IF;
            ELSE
                -- RAISE NOTICE'starting and ending point on same edge';
                -- RAISE NOTICE'';
                text1 := ST_AsText(ST_CollectionExtract(ST_Split(tableway1.geom_linestring, proj12_multilinestring),2));
                ---- RAISE NOTICE'%', text1;
                text1 := replace(replace(text1,'MULTILINESTRING((',''),'))','');
                text_tab1 := string_to_array(text1,  '),(');
                IF array_upper(text_tab1, 1) > 1 THEN
                    source = tableway1.source;
                    FOR i IN 1 .. array_upper(text_tab1, 1) LOOP
                        IF i < array_upper(text_tab1, 1) THEN
                            --add last point (intersection point) of the linestring into 
                            text_tab2 := string_to_array(text_tab1[i],  ',');
                            point3 := ST_GeomFromText('POINT(' || text_tab2[array_upper(text_tab2, 1)] || ')', 3857);
                            INSERT INTO _temp_otrouting_points(geom_point, timestamp, token) VALUES (point3, timestampNow, token_f);
                            SELECT -_temp_otrouting_points.id INTO target FROM _temp_otrouting_points WHERE geom_point = point3 AND token = token_f;
                        ELSE
                            target = tableway1.target;
                        END IF;
                        --insert split linestring into _temp_otrouting_ways
                        linestring1 := ST_GeomFromText('LINESTRING(' || text_tab1[i] || ')', 3857);
                        INSERT INTO _temp_otrouting_ways (geom_linestring, source, target, dist_m,
                            factor_pedestrian, factor_mountainbike, factor_roadcycle, factor_car,
                            factorreverse_pedestrian, factorreverse_mountainbike, factorreverse_roadcycle, factorreverse_car,
                            timestamp, token) 
                            VALUES (linestring1, source, target, ST_Length(linestring1)/coefdistmetersto3852,
                            tableway1.factor_pedestrian, tableway1.factor_mountainbike, tableway1.factor_roadcycle, tableway1.factor_car, 
                            tableway1.factorreverse_pedestrian, tableway1.factorreverse_mountainbike, tableway1.factorreverse_roadcycle, tableway1.factorreverse_car,    
                            timestampNow, token_f);
                        source := target;
                    END LOOP;
                END IF;
                
                ---- RAISE NOTICE'another_fun(%)', array_upper(text_tab1);
                --FOR i IN 0 .. array_upper(text_tab1, 1)
                --LOOP
                --  -- RAISE NOTICE'%', text_tab1[i];      -- single quotes!
                -- END LOOP;
            END IF;
            --GET source and target for pgr call
            SELECT id, ST_Distance(_temp_otrouting_points.geom_point, proj1) AS dist INTO tablepoint1 FROM _temp_otrouting_points WHERE token = token_f ORDER BY dist ASC LIMIT 1;
            IF tablepoint1.dist IS NULL OR tablepoint1.dist > 1.0 THEN
                --SELECT id, ST_Distance(otrouting_points.geom_point, proj1) AS dist INTO tablepoint1 FROM otrouting_points WHERE ST_Distance(otrouting_points.geom_point, proj1) < 1.0 ORDER BY dist ASC LIMIT 1;
                SELECT id, ST_Distance(otrouting_points.geom_point, proj1) AS dist INTO tablepoint1 FROM otrouting_points WHERE ST_Intersects(otrouting_points.geom_point, ST_MakeEnvelope(lonmin_loc, latmin_loc, lonmax_loc, latmax_loc, 3857)) ORDER BY dist ASC LIMIT 1;
                source := tablepoint1.id;
            ELSE
                source := -tablepoint1.id;
            END IF;
            SELECT id, ST_Distance(_temp_otrouting_points.geom_point, proj2) AS dist INTO tablepoint1 FROM _temp_otrouting_points WHERE token = token_f ORDER BY dist ASC LIMIT 1;
            IF tablepoint1.dist IS NULL OR tablepoint1.dist > 1.0 THEN
                --SELECT id, ST_Distance(otrouting_points.geom_point, proj2) AS dist INTO tablepoint1 FROM otrouting_points WHERE ST_Distance(otrouting_points.geom_point, proj2) < 1.0 ORDER BY dist ASC LIMIT 1;
                SELECT id, ST_Distance(otrouting_points.geom_point, proj2) AS dist INTO tablepoint1 FROM otrouting_points WHERE ST_Intersects(otrouting_points.geom_point, ST_MakeEnvelope(lonmin_loc2, latmin_loc2, lonmax_loc2, latmax_loc2, 3857)) ORDER BY dist ASC LIMIT 1;
                target := tablepoint1.id;
            ELSE
                target := -tablepoint1.id;
            END IF;
            
            IF source IS NOT NULL AND target IS NOT NULL THEN

                -- define boundary border length
                SELECT INTO dist_m ST_DistanceSphere(point1_4326, point2_4326)/2;
                dist_m := GREATEST(300,dist_m);
                dist_m := LEAST(10000,dist_m);
                -- RAISE NOTICE 'dist_m for djikstra call boundary box definition: %', dist_m;

                -- define boundary box for djikstra call
                lonmin_loc := LEAST(ST_X(point1),ST_X(point2)) - dist_m*coefdistmetersto3852;
                lonmax_loc := GREATEST(ST_X(point1),ST_X(point2)) + dist_m*coefdistmetersto3852;
                latmin_loc := LEAST(ST_Y(point1),ST_Y(point2)) - dist_m*coefdistmetersto3852;
                latmax_loc := GREATEST(ST_Y(point1),ST_Y(point2)) + dist_m*coefdistmetersto3852;

                -- RAISE NOTICE'Run djikstra';
                -- RAISE NOTICE'';

                text1:= 'WHERE ST_Intersects(geom_linestring, ST_MakeEnvelope(' || lonmin_loc || ', ' || latmin_loc || ', ' || lonmax_loc || ', ' || latmax_loc || ', 3857))';
                IF routingtype = 'pedestrian' THEN
                    SELECT ARRAY(
                                SELECT edge FROM pgr_dijkstra('
                                    SELECT id, source, target, dist_m*factor_pedestrian AS cost, dist_m*factor_pedestrian*factorreverse_pedestrian AS reverse_cost FROM otrouting_ways ' || text1 || ' AND factor_pedestrian > 0
                                    UNION 
                                    SELECT -id AS id, source, target, dist_m*factor_pedestrian AS cost, dist_m*factor_pedestrian*factorreverse_pedestrian AS reverse_cost FROM _temp_otrouting_ways WHERE token=' || token_f , source, target, true)
                               ) INTO djikstra_out_edges; 
                ELSEIF routingtype = 'mountainbike' THEN
                    SELECT ARRAY(
                                SELECT edge FROM pgr_dijkstra('
                                    SELECT id, source, target, dist_m*factor_mountainbike AS cost, dist_m*factor_mountainbike*factorreverse_mountainbike AS reverse_cost FROM otrouting_ways ' || text1 || ' AND factor_mountainbike > 0
                                    UNION 
                                    SELECT -id AS id, source, target, dist_m*factor_mountainbike AS cost, dist_m*factor_mountainbike*factorreverse_mountainbike AS reverse_cost FROM _temp_otrouting_ways WHERE token=' || token_f , source, target, true)
                               ) INTO djikstra_out_edges; 
                ELSEIF routingtype = 'roadcycle' THEN
                    SELECT ARRAY(
                                SELECT edge FROM pgr_dijkstra('
                                    SELECT id, source, target, dist_m*factor_roadcycle AS cost, dist_m*factor_roadcycle*factorreverse_roadcycle AS reverse_cost FROM otrouting_ways ' || text1 || ' AND factor_roadcycle > 0
                                    UNION 
                                    SELECT -id AS id, source, target, dist_m*factor_roadcycle AS cost, dist_m*factor_roadcycle*factorreverse_roadcycle AS reverse_cost FROM _temp_otrouting_ways WHERE token=' || token_f , source, target, true)
                               ) INTO djikstra_out_edges; 
               ELSEIF routingtype = 'car' THEN
                    SELECT ARRAY(
                                SELECT edge FROM pgr_dijkstra('
                                    SELECT        id, source, target, dist_m*factor_car AS cost, dist_m*factor_car*factorreverse_car AS reverse_cost FROM otrouting_ways ' || text1 || ' AND factor_car > 0
                                    UNION 
                                    SELECT -id AS id, source, target, dist_m*factor_car AS cost, dist_m*factor_car*factorreverse_car AS reverse_cost FROM _temp_otrouting_ways WHERE token=' || token_f , source, target, true)
                               ) INTO djikstra_out_edges; 
                END IF;

                -- RAISE NOTICE'Prepare return request';
                -- RAISE NOTICE'';
                IF source > 0 THEN
                    SELECT replace(replace(ST_AsText(ST_Transform(geom_point,4326)),'POINT(',''),')','') INTO text_source FROM otrouting_points WHERE id=source;
                ELSE
                    SELECT replace(replace(ST_AsText(ST_Transform(geom_point,4326)),'POINT(',''),')','') INTO text_source FROM _temp_otrouting_points WHERE id=-source;
                END IF;
                lonlat_out := array_append(lonlat_out, text_source);
                IF array_upper(djikstra_out_edges, 1) IS NOT NULL THEN
                    FOR i IN 1 .. array_upper(djikstra_out_edges, 1)-1 LOOP
                        --get text
                        IF djikstra_out_edges[i] < 0 THEN
                            SELECT replace(replace(ST_AsText(ST_Transform(geom_linestring,4326)),'LINESTRING(',''),')','') FROM _temp_otrouting_ways WHERE id = -djikstra_out_edges[i] INTO text1;
                        ELSE
                            SELECT replace(replace(ST_AsText(ST_Transform(geom_linestring,4326)),'LINESTRING(',''),')','') FROM otrouting_ways WHERE id = djikstra_out_edges[i] INTO text1;
                        END IF;

                        text_tab1 := string_to_array(text1,',');
                        ---- RAISE NOTICE'n: %', text_tab1;
                        IF text_tab1[1] = text_source THEN
                            FOR j IN 2 .. array_upper(text_tab1, 1) LOOP
                                lonlat_out := array_append(lonlat_out, text_tab1[j]);
                                text_source := text_tab1[j];
                                ---- RAISE NOTICE'lonlat_out: %', text_source;
                            END LOOP;
                        ELSE
                            FOR j IN 2..array_upper(text_tab1, 1) LOOP
                                lonlat_out := array_append(lonlat_out, text_tab1[1 + array_upper(text_tab1, 1) - j]);
                                text_source := text_tab1[1 + array_upper(text_tab1, 1) - j];
                                ---- RAISE NOTICE'lonlat_out: %', text_source;
                            END LOOP;
                        END IF;
                    END LOOP;
                END IF;

                -- RAISE NOTICE'Run return request';
                -- RAISE NOTICE'';
                RETURN QUERY SELECT string_to_array(UNNEST(lonlat_out),' ')::text[] AS lonlat;
            END IF;
        END IF;
    END IF;

    -- clean temp tables
    -- RAISE NOTICE'Clean temp table';
    -- RAISE NOTICE'';
    timestampMax := timestampNow-5*60;
    DELETE FROM _temp_otrouting_ways WHERE token = token_f OR timestamp < timestampMax;
    DELETE FROM _temp_otrouting_points WHERE token = token_f OR  timestamp < timestampMax;
END; $$
LANGUAGE plpgsql;

--test on same edge
--SELECT * FROM otrouting_getrouting(1.73670359630932, 42.5435625682116, 1.7361028051342, 42.5436100890435)
--SELECT * FROM otrouting_getrouting(1.7361028051342, 42.5436100890435, 1.73670359630932, 42.5435625682116)
--test on different edges
--SELECT * FROM otrouting_getrouting(1.73670359630932, 42.5435625682116, 1.7358052810252, 42.54356918667);
SELECT * FROM otrouting_getrouting(1.7358052810252, 42.54356918667, 1.73470359630932, 42.5435625682116, 'pedestrian');
--SELECT * FROM otrouting_getrouting(1.5445232391357, 42.513016912355, 1.5441155433655, 42.512502858992, 'car')

