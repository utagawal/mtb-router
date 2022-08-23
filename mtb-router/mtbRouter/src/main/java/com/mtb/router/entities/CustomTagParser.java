package com.mtb.router.entities;

import com.graphhopper.reader.ReaderWay;
import com.graphhopper.routing.ev.IntEncodedValue;
import com.graphhopper.routing.util.parsers.TagParser;
import com.graphhopper.storage.IntsRef;

import static com.mtb.router.entities.JavaPostgreSqlRetrieve.GetGPXWeight;


public class CustomTagParser implements TagParser {

    private IntEncodedValue encodedValue;

    public CustomTagParser(IntEncodedValue encodedValue) {
        this.encodedValue = encodedValue;
    }
    @Override
    public IntsRef handleWayTags(IntsRef edgeFlags, ReaderWay way, IntsRef relationFlags) {
        int GPX = 1;

        if (way.hasTag("tunnel")){
            GPX = GetGPXWeight(1);
            //GPX = 4;
        }
        if (GPX != 1){
            encodedValue.setInt(false, edgeFlags, GPX);
        }


        return edgeFlags;
    }



}
