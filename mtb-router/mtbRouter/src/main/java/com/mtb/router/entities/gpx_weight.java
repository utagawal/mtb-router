package com.mtb.router.entities;

import com.graphhopper.routing.ev.IntEncodedValue;
import com.graphhopper.routing.ev.IntEncodedValueImpl;
import lombok.AllArgsConstructor;
import lombok.Data;

import javax.persistence.*;


public class gpx_weight {

    public static Integer weight = 5;
    public static final String KEY = "gpx_weight";

    public static IntEncodedValue create() {
        return new IntEncodedValueImpl(KEY, 3, false);
    }

}
