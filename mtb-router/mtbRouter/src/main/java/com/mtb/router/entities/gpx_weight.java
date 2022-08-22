package com.mtb.router.entities;

import com.graphhopper.routing.ev.IntEncodedValue;
import com.graphhopper.routing.ev.IntEncodedValueImpl;
import lombok.AllArgsConstructor;
import lombok.Data;

import javax.persistence.*;

@Data
@AllArgsConstructor
@Entity
@Table(name = "otrouting_ways")
public class gpx_weight {
    @Id @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id")
    public static Long id;

    @Column(name = "gpx_weight")
    public static Integer weight;
    public static final String KEY = "gpx_weight";

    public static IntEncodedValue create() {
        return new IntEncodedValueImpl(KEY, 16, false);
    }

}
