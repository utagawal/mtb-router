package com.mtb.router.entities;

import com.graphhopper.reader.ReaderWay;
import com.graphhopper.routing.ev.IntEncodedValue;
import com.graphhopper.routing.util.parsers.TagParser;
import com.graphhopper.storage.IntsRef;

public class CustomTagParser implements TagParser {

    private IntEncodedValue encodedValue;

    public CustomTagParser(IntEncodedValue encodedValue) {
        this.encodedValue = gpx_weight.create();
    }


    @Override
    public IntsRef handleWayTags(IntsRef edgeFlags, ReaderWay way, IntsRef relationFlags) {
        if (way.hasTag(gpx_weight.KEY)) {
            encodedValue.setInt(false, edgeFlags, gpx_weight.weight);
        }

        if (way.getId() == gpx_weight.id){
            encodedValue.setInt(false, edgeFlags, gpx_weight.weight);
        }
        return edgeFlags;
    }



}
