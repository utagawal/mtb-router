package com.mtb.router.entities;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.logging.Level;
import java.util.logging.Logger;

public class JavaPostgreSqlRetrieve {

    public static int GetGPXWeight(int id, long wayid) {

        String url = "jdbc:postgresql://localhost:5432/test";
        String user = "postgres";
        String password = "postgres";
        int cal = 0;

        try (Connection con = DriverManager.getConnection(url, user, password);
             PreparedStatement pst = con.prepareStatement("SELECT gpx_weight FROM otrouting_ways where id =" + wayid);
             ResultSet rs = pst.executeQuery()) {

            while (rs.next()) {
                cal = rs.getInt(1);
            }

        } catch (SQLException ex) {

            Logger lgr = Logger.getLogger(JavaPostgreSqlRetrieve.class.getName());
            lgr.log(Level.SEVERE, ex.getMessage(), ex);
        }

        return cal;
    }
    public static void main(String[] args) {

        String url = "jdbc:postgresql://localhost:5432/test";
        String user = "postgres";
        String password = "postgres";

        try (Connection con = DriverManager.getConnection(url, user, password);
             PreparedStatement pst = con.prepareStatement("SELECT gpx_weight FROM otrouting_ways where id = 1");
             ResultSet rs = pst.executeQuery()) {

            while (rs.next()) {
                int cal = rs.getInt(1);
                System.out.print(cal);
            }

        } catch (SQLException ex) {

            Logger lgr = Logger.getLogger(JavaPostgreSqlRetrieve.class.getName());
            lgr.log(Level.SEVERE, ex.getMessage(), ex);
        }

    }
}
