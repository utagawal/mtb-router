package com.mtb.router.entities;

import com.graphhopper.routing.ev.*;
import com.graphhopper.routing.util.TransportationMode;
import com.graphhopper.routing.util.parsers.*;

import static com.graphhopper.util.Helper.toLowerCase;

public class CustomTagParserFactory implements TagParserFactory {
    @Override
    public TagParser create(EncodedValueLookup lookup, String name) {
        name = name.trim();
        if (!name.equals(toLowerCase(name)))
            throw new IllegalArgumentException("Use lower case for TagParsers: " + name);
        if (gpx_weight.KEY.equals(name))
            return new CustomTagParser(lookup.getIntEncodedValue(gpx_weight.KEY));
        else if (Roundabout.KEY.equals(name))
            return new OSMRoundaboutParser(lookup.getBooleanEncodedValue(Roundabout.KEY));
        else if (name.equals(RoadClass.KEY))
            return new OSMRoadClassParser(lookup.getEnumEncodedValue(RoadClass.KEY, RoadClass.class));
        else if (name.equals(RoadClassLink.KEY))
            return new OSMRoadClassLinkParser(lookup.getBooleanEncodedValue(RoadClassLink.KEY));
        else if (name.equals(RoadEnvironment.KEY))
            return new OSMRoadEnvironmentParser(lookup.getEnumEncodedValue(RoadEnvironment.KEY, RoadEnvironment.class));
        else if (name.equals(RoadAccess.KEY))
            return new OSMRoadAccessParser(lookup.getEnumEncodedValue(RoadAccess.KEY, RoadAccess.class), OSMRoadAccessParser.toOSMRestrictions(TransportationMode.CAR));
        else if (name.equals(MaxSpeed.KEY))
            return new OSMMaxSpeedParser(lookup.getDecimalEncodedValue(MaxSpeed.KEY));
        else if (name.equals(MaxWeight.KEY))
            return new OSMMaxWeightParser(lookup.getDecimalEncodedValue(MaxWeight.KEY));
        else if (name.equals(MaxHeight.KEY))
            return new OSMMaxHeightParser(lookup.getDecimalEncodedValue(MaxHeight.KEY));
        else if (name.equals(MaxWidth.KEY))
            return new OSMMaxWidthParser(lookup.getDecimalEncodedValue(MaxWidth.KEY));
        else if (name.equals(MaxAxleLoad.KEY))
            return new OSMMaxAxleLoadParser(lookup.getDecimalEncodedValue(MaxAxleLoad.KEY));
        else if (name.equals(MaxLength.KEY))
            return new OSMMaxLengthParser(lookup.getDecimalEncodedValue(MaxLength.KEY));
        else if (name.equals(Surface.KEY))
            return new OSMSurfaceParser(lookup.getEnumEncodedValue(Surface.KEY, Surface.class));
        else if (name.equals(Smoothness.KEY))
            return new OSMSmoothnessParser(lookup.getEnumEncodedValue(Smoothness.KEY, Smoothness.class));
        else if (name.equals(Toll.KEY))
            return new OSMTollParser(lookup.getEnumEncodedValue(Toll.KEY, Toll.class));
        else if (name.equals(TrackType.KEY))
            return new OSMTrackTypeParser(lookup.getEnumEncodedValue(TrackType.KEY, TrackType.class));
        else if (name.equals(Hazmat.KEY))
            return new OSMHazmatParser(lookup.getEnumEncodedValue(Hazmat.KEY, Hazmat.class));
        else if (name.equals(HazmatTunnel.KEY))
            return new OSMHazmatTunnelParser(lookup.getEnumEncodedValue(HazmatTunnel.KEY, HazmatTunnel.class));
        else if (name.equals(HazmatWater.KEY))
            return new OSMHazmatWaterParser(lookup.getEnumEncodedValue(HazmatWater.KEY, HazmatWater.class));
        else if (name.equals(Lanes.KEY))
            return new OSMLanesParser(lookup.getIntEncodedValue(Lanes.KEY));
        else if (name.equals(MtbRating.KEY))
            return new OSMMtbRatingParser(lookup.getIntEncodedValue(MtbRating.KEY));
        else if (name.equals(HikeRating.KEY))
            return new OSMHikeRatingParser(lookup.getIntEncodedValue(HikeRating.KEY));
        else if (name.equals(HorseRating.KEY))
            return new OSMHorseRatingParser(lookup.getIntEncodedValue(HorseRating.KEY));
        else if (name.equals(Country.KEY))
            return new CountryParser(lookup.getEnumEncodedValue(Country.KEY, Country.class));
        return null;
    }
}
