-- v1.0 11/07/2019 Julien SENTIER
--       First version of the tool
-- v1.1 14/07/2019 Julien SENTIER
--       1m offset on the input coord to avoid to be at an intersection
-- v1.2 8/8/2019 Julien SENTIER
--       addition of parameter threeshold_segLength_m
-- v1.3 21/10/2021 Julien SENTIER
--       clean automatically _temp_otrouting_getrouteinfo table
--       consideration of ST_Intersects in sql WHERE requests
--       geom_center replaced by geom_linestring in sql WHERE requests (table otrouting_ways)
--       distance calculated in meters
-- v1.4 10/03/2022 Julien SENTIER
--       remobal of parameter threeshold_segLength_m

DROP FUNCTION IF EXISTS otrouting_getrouteinfo(TEXT[],double precision);
DROP TABLE IF EXISTS _temp_otrouting_getrouteinfo;
DROP TABLE IF EXISTS _variable_otrouting_getrouteinfo_closestway;
DROP TABLE IF EXISTS _variable_otrouting_closestpoint;
CREATE TABLE _temp_otrouting_getrouteinfo
(
    id bigserial PRIMARY KEY,
    geom_source geometry(Point,3857),
    geom_proj geometry(Point,3857),
    ids_way_source_target BIGINT[],
    dist DOUBLE PRECISION,
    tags text[],
    timestamp integer,
    token integer
);
CREATE TABLE _variable_otrouting_getrouteinfo_closestway
(
    id bigint, 
    dist FLOAT,
    geom_linestring geometry(LineString,3857),
    source bigint,
    target bigint,
    tags text[],
    factor_pedestrian integer
);
CREATE TABLE _variable_otrouting_closestpoint
(
    id bigint, 
    dist FLOAT
);

CREATE OR REPLACE FUNCTION otrouting_getrouteinfo(
    arraysources TEXT[], 
    threeshold_distProj_m FLOAT)
--RETURNS TABLE (seq integer, node bigint, edge bigint, lonlat TEXT[]) AS $$
RETURNS TABLE (
    geom_source TEXT, 
    geom_proj TEXT,
    ids_way_source_target BIGINT[],
    dist DOUBLE PRECISION,
    tags text[]
) AS $$
#variable_conflict use_column
DECLARE 
    point1 geometry(Point,3857);
    point1_4326 geometry(Point,4326);
    point11 geometry(Point,3857);
    point11_4326 geometry(Point,4326);
    point2 geometry(Point,3857);
    point3 geometry(Point,3857);
    linestring1 geometry(LineString,3857);
    linestring2 geometry(LineString,3857);
    tableway1 _variable_otrouting_getrouteinfo_closestway;
    tableway2 _variable_otrouting_getrouteinfo_closestway;
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
    lon1 FLOAT;
    lon2 FLOAT; 
    lon3 FLOAT;
    lat1 FLOAT;
    lat2 FLOAT;
    lat3 FLOAT;
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
    toto _temp_otrouting_points;
    i bigint;
    source bigint;
    text_source TEXT;
    target bigint;
    timestampNow integer;
    timestampMax integer;
    token_f integer;
    distProj FLOAT;
    dist FLOAT;
    dist_m FLOAT;
    dist_3852 FLOAT;
    coefdistmetersto3852 FLOAT;
    lonmin_loc INT;
    lonmax_loc INT;
    latmin_loc INT;
    latmax_loc INT;
    lon_middle INT;
    lat_middle INT;
    delta INT;
    t_id BIGINT[] = '{}';
    elmHasProj boolean;
BEGIN
    DELETE FROM _temp_notice;
    -- get timestamp and token
    timestampNow := EXTRACT(EPOCH FROM NOW())::integer;
    token_f := random() * 100000000::integer ;
    --RAISE NOTICE 'timestampNow: %', timestampNow;
    --RAISE NOTICE 'token: %', token_f;
    --RAISE NOTICE '';

    FOR i IN 1 .. array_upper(arraysources, 1) LOOP
        RAISE NOTICE '';
        RAISE NOTICE 'i: %', i;
        IF i = 1 THEN
            --compute coefdistmetersto3852

            point1 := ST_Transform(ST_GeomFromText(arraysources[i],4326),3857);
            point11 := ST_GeomFromText('POINT(' || ST_X(point1)+100 || ' ' || ST_Y(point1)+100 || ')',3857);
            point1_4326 := ST_Transform(point1,4326);
            point11_4326 := ST_Transform(point11,4326);
            dist_m := ST_DistanceSphere(point1_4326, point11_4326);
            dist_3852 := ST_Distance(point1, point11);
            coefdistmetersto3852 := dist_3852/dist_m;
            RAISE NOTICE 'coefdistmetersto3852: %', coefdistmetersto3852;
        END IF;

        point1 := ST_Transform(ST_GeomFromText(arraysources[i],4326),3857);
        lon1 := ST_X(point1);
        lat1 := ST_Y(point1);
        point2 := ST_Transform(ST_GeomFromText(arraysources[i-1],4326),3857);
        lon2 := ST_X(point2);
        lat2 := ST_Y(point2);

        IF i > 1 THEN
            dist := ST_Distance(point1, point2)/coefdistmetersto3852;
            --dist := ST_Distance(
            --    ST_GeographyFromText(arraysources[i-1]), -- Los Angeles (LAX)
            --    ST_GeographyFromText(arraysources[i])     -- Paris (CDG)
            --);
        ELSE
            dist := 0.0;
        END IF;

        RAISE NOTICE '1 (i): %', arraysources[i];
        RAISE NOTICE '2 (i-1): %', arraysources[i-1];
        RAISE NOTICE 'dist: %', dist;

        point3 := point1;
        IF dist > 0 THEN
            dist_3852 := ST_Distance(point1, point2);
            lon3 := lon1 + (lon2-lon1) * 1 / dist_3852;
            lat3 := lat1 + (lat2-lat1) * 1 / dist_3852;
            point3 := ST_GeomFromText('POINT('  || lon3  || ' '  || lat3 || ')',3857);
        END IF;
        

        -- get closest ways
        lonmin_loc := LEAST(ST_X(point1),ST_X(point1))-1.1*threeshold_distProj_m*coefdistmetersto3852;
        lonmax_loc := GREATEST(ST_X(point1),ST_X(point1))+1.1*threeshold_distProj_m*coefdistmetersto3852;
        latmin_loc := LEAST(ST_Y(point1),ST_Y(point1))-1.1*threeshold_distProj_m*coefdistmetersto3852;
        latmax_loc := GREATEST(ST_Y(point1),ST_Y(point1))+1.1*threeshold_distProj_m*coefdistmetersto3852;
        SELECT  otrouting_ways.id AS id, 
                ST_Distance(otrouting_ways.geom_linestring, point3) AS dist, 
                otrouting_ways.geom_linestring,
                otrouting_ways.source,
                otrouting_ways.target,
                otrouting_ways.tags,
                otrouting_ways.factor_pedestrian
            INTO tableway1 FROM otrouting_ways WHERE ST_Intersects(otrouting_ways.geom_linestring, ST_MakeEnvelope(lonmin_loc, latmin_loc, lonmax_loc, latmax_loc, 3857)) AND factor_pedestrian > 0 ORDER BY dist ASC LIMIT 1;
        SELECT ST_ClosestPoint(tableway1.geom_linestring, point3) INTO proj1;

        --RAISE NOTICE 'Point: %', ST_AsText(ST_Transform(point1,4326));
        --RAISE NOTICE 'Proj: %', ST_AsText(ST_Transform(proj1,4326));
        
    	
        IF proj1 IS NOT NULL THEN
	       elmHasProj := TRUE;
            distProj := ST_Distance(point3, proj1)/coefdistmetersto3852;
            --RAISE NOTICE 'DistProj: %', distProj;
            IF distProj  > threeshold_distProj_m THEN
                proj1 := NULL;
                tableway1 := NULL;
            END IF;
    	ELSE
            proj1 := NULL;
            tableway1 := NULL;
        END IF;
        INSERT INTO _temp_otrouting_getrouteinfo (geom_source, geom_proj, ids_way_source_target, dist, tags, timestamp, token) VALUES (
                point1, 
                proj1,  
                ARRAY[tableway1.id, tableway1.source, tableway1.target],
                dist,
                tableway1.tags,
            timestampNow, token_f);
        --RAISE NOTICE '';
    END LOOP;

    RETURN QUERY SELECT ST_AsText(ST_Transform(geom_source,4326)), ST_AsText(ST_Transform(geom_proj,4326)), ids_way_source_target, dist, tags FROM _temp_otrouting_getrouteinfo WHERE token = token_f ORDER BY id ASC;

    -- clean temp tables
    -- RAISE NOTICE 'Clean temp table';
    -- RAISE NOTICE '';
    timestampMax := timestampNow-5*60;
    DELETE FROM _temp_otrouting_getrouteinfo WHERE token = token_f OR timestamp < timestampMax;

END; $$
LANGUAGE plpgsql;

--SELECT * FROM otrouting_getrouteinfo(ARRAY['POINT(1.533258 42.513852)','POINT(1.533126 42.513875)','POINT(1.533071 42.513891)','POINT(1.532866 42.513952)','POINT(1.532835 42.513968)'], 30.0);


-- SELECT * FROM otrouting_getrouteinfo(ARRAY['POINT(1.533258 42.513852)','POINT(1.533126 42.513875)','POINT(1.533071 42.513891)','POINT(1.532866 42.513952)','POINT(1.532835 42.513968)','POINT(1.532615 42.514078)','POINT(1.532543 42.514114)','POINT(1.53238 42.514221)','POINT(1.532344 42.514245)','POINT(1.53223 42.514352)','POINT(1.532188 42.514392)','POINT(1.532145 42.514433)','POINT(1.532054 42.514525)','POINT(1.531737 42.514888)','POINT(1.531554 42.515041)','POINT(1.531554 42.515041)','POINT(1.531316 42.515232)','POINT(1.531483 42.515317)','POINT(1.531604 42.51533)','POINT(1.531638 42.515305)','POINT(1.532087 42.514968)','POINT(1.532609 42.514709)','POINT(1.532743 42.51466)','POINT(1.533024 42.514599)','POINT(1.533202 42.514556)','POINT(1.533306 42.514563)','POINT(1.533359 42.514586)','POINT(1.533382 42.514603)','POINT(1.533408 42.514629)','POINT(1.533415 42.514669)','POINT(1.533384 42.514717)','POINT(1.533327 42.514749)','POINT(1.533147 42.5148)','POINT(1.532998 42.514831)','POINT(1.533159 42.514857)','POINT(1.533358 42.51489)','POINT(1.533545 42.514899)','POINT(1.533649 42.514901)','POINT(1.533757 42.514901)','POINT(1.53387 42.514913)','POINT(1.533908 42.514873)','POINT(1.533922 42.514856)','POINT(1.53394 42.514831)','POINT(1.533981 42.514799)','POINT(1.534048 42.514771)','POINT(1.534117 42.514717)','POINT(1.534157 42.514706)','POINT(1.53418 42.514713)','POINT(1.534192 42.514724)','POINT(1.53421 42.51476)','POINT(1.534234 42.514785)','POINT(1.534253 42.5148)','POINT(1.534291 42.514791)','POINT(1.534304 42.514776)','POINT(1.534318 42.51477)','POINT(1.534326 42.514777)','POINT(1.534325 42.514794)','POINT(1.534311 42.51482)','POINT(1.534316 42.514846)','POINT(1.534337 42.514861)','POINT(1.534368 42.514868)','POINT(1.534419 42.514871)','POINT(1.534475 42.514863)','POINT(1.534524 42.514832)','POINT(1.534596 42.51477)','POINT(1.534647 42.514742)','POINT(1.534684 42.514743)','POINT(1.534713 42.51477)','POINT(1.534719 42.5148)','POINT(1.534723 42.514846)','POINT(1.534738 42.514876)','POINT(1.53477 42.514889)','POINT(1.534818 42.514884)','POINT(1.534892 42.514862)','POINT(1.534989 42.514833)','POINT(1.535106 42.514812)','POINT(1.535107 42.514812)','POINT(1.535235 42.514801)','POINT(1.53534 42.514798)','POINT(1.535401 42.514801)','POINT(1.535482 42.514801)','POINT(1.535568 42.514777)','POINT(1.535719 42.514736)','POINT(1.535899 42.514698)','POINT(1.536128 42.514661)','POINT(1.536324 42.514633)','POINT(1.536508 42.514616)','POINT(1.537297 42.514512)','POINT(1.53774 42.514451)','POINT(1.537986 42.514421)','POINT(1.538236 42.514402)','POINT(1.538369 42.514404)','POINT(1.538537 42.514386)','POINT(1.538676 42.514351)','POINT(1.538777 42.514265)','POINT(1.53884 42.514197)','POINT(1.538935 42.514129)','POINT(1.538998 42.51408)','POINT(1.539052 42.513981)','POINT(1.539239 42.513819)','POINT(1.539333 42.513732)','POINT(1.53943 42.513625)','POINT(1.539445 42.513588)','POINT(1.539414 42.51356)','POINT(1.539398 42.513526)','POINT(1.539367 42.513471)','POINT(1.539342 42.513447)','POINT(1.539286 42.51343)','POINT(1.539181 42.513414)','POINT(1.539085 42.513381)','POINT(1.53902 42.513338)','POINT(1.538982 42.513318)','POINT(1.538935 42.513349)','POINT(1.538837 42.5134)','POINT(1.538781 42.5134)','POINT(1.538725 42.513426)','POINT(1.538657 42.513384)','POINT(1.53853 42.513274)','POINT(1.538477 42.513209)','POINT(1.538443 42.513149)','POINT(1.538392 42.513088)','POINT(1.538377 42.51305)','POINT(1.538378 42.513013)','POINT(1.538392 42.512969)','POINT(1.53843 42.512919)','POINT(1.538491 42.512886)','POINT(1.538619 42.512873)','POINT(1.538663 42.512872)','POINT(1.538728 42.512869)','POINT(1.538899 42.512794)','POINT(1.538978 42.512749)','POINT(1.539045 42.51272)','POINT(1.539136 42.512688)','POINT(1.539199 42.512678)','POINT(1.539277 42.51265)','POINT(1.53932 42.512637)','POINT(1.539345 42.512616)','POINT(1.539159 42.512632)','POINT(1.539014 42.512472)','POINT(1.539137 42.512382)','POINT(1.539314 42.512285)','POINT(1.539229 42.512251)','POINT(1.539006 42.512344)','POINT(1.538939 42.512405)','POINT(1.538884 42.512455)','POINT(1.538733 42.512581)','POINT(1.538487 42.512657)','POINT(1.538447 42.512662)','POINT(1.53799 42.512726)','POINT(1.537569 42.512809)','POINT(1.537224 42.512878)','POINT(1.537078 42.512907)','POINT(1.537021 42.512853)','POINT(1.536895 42.512748)','POINT(1.536847 42.512649)','POINT(1.536752 42.512511)','POINT(1.536752 42.512511)','POINT(1.536652 42.512414)','POINT(1.536513 42.512382)','POINT(1.536401 42.512477)','POINT(1.536294 42.512537)','POINT(1.536199 42.512576)','POINT(1.536032 42.512624)','POINT(1.535861 42.512666)','POINT(1.535736 42.512697)','POINT(1.535696 42.512698)','POINT(1.535623 42.512698)','POINT(1.535505 42.512698)','POINT(1.535299 42.512716)','POINT(1.535229 42.512732)','POINT(1.535161 42.512763)','POINT(1.535118 42.512782)','POINT(1.534634 42.513033)','POINT(1.53457 42.513066)','POINT(1.534462 42.513113)','POINT(1.53424 42.513209)','POINT(1.534194 42.513251)','POINT(1.53415 42.513292)','POINT(1.534059 42.513407)','POINT(1.534015 42.513496)','POINT(1.533941 42.513615)','POINT(1.533836 42.513692)','POINT(1.533669 42.513763)','POINT(1.53334 42.513838)','POINT(1.53333 42.51384)','POINT(1.533258 42.513852)'], 30.0);
SELECT * FROM otrouting_getrouteinfo(ARRAY['POINT(1.533258 42.513852)','POINT(1.533126 42.513875)','POINT(1.533071 42.513891)'], 30.0);
