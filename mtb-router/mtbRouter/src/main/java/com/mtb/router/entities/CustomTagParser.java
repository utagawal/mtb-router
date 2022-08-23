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
        int GPX = 5;

        if (way.hasTag(gpx_weight.KEY)) {
            String noRoutingPriority = way.getTag(gpx_weight.KEY);
        }
        encodedValue.setInt(false, edgeFlags, GPX);

        return edgeFlags;
    }



}
