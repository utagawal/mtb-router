package com.mtb.router.entities;

import com.graphhopper.reader.ReaderWay;
import com.graphhopper.routing.ev.IntEncodedValue;
import com.graphhopper.routing.util.parsers.TagParser;
import com.graphhopper.storage.IntsRef;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.logging.Level;
import java.util.logging.Logger;

public class CustomTagParser implements TagParser {

    private IntEncodedValue encodedValue;

    public CustomTagParser(IntEncodedValue encodedValue) {
        this.encodedValue = encodedValue;
    }
    @Override
    public IntsRef handleWayTags(IntsRef edgeFlags, ReaderWay way, IntsRef relationFlags) {

        String url = "jdbc:postgresql://localhost:5432/test";
        String user = "postgres";
        String password = "postgres";

        try (Connection con = DriverManager.getConnection(url, user, password);
             PreparedStatement pst = con.prepareStatement("select * from otrouting_ways");
             ResultSet rs = pst.executeQuery()) {

            while (rs.next()) {

                System.out.print(rs.getInt(1));
                System.out.print(": ");
                System.out.println(rs.getString(2));
            }

        } catch (SQLException ex) {

            Logger lgr = Logger.getLogger(CustomTagParser.class.getName());
            lgr.log(Level.SEVERE, ex.getMessage(), ex);
        }

        int GPX = 5; // here we set the value for the gpx_weight encoded value

        if (way.hasTag(gpx_weight.KEY)) {
            encodedValue.setInt(false, edgeFlags, 1);
        }
        encodedValue.setInt(false, edgeFlags, GPX);

        return edgeFlags;
    }



}
