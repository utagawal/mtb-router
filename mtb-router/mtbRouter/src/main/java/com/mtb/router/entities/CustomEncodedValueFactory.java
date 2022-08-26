package com.mtb.router.entities;

import com.graphhopper.routing.ev.*;


public class CustomEncodedValueFactory implements EncodedValueFactory {

    @Override
    public EncodedValue create(String encodedValueString) {

        final EncodedValue enc;
        String name = encodedValueString.split("\\|")[0];

        if (name.isEmpty())
            throw new IllegalArgumentException("To load EncodedValue a name is required. " + encodedValueString);
        if(gpx_weight.KEY.equals(name)) {
            enc = gpx_weight.create();
        }
        else if (Roundabout.KEY.equals(name)) {
            enc = Roundabout.create();
        } else if (GetOffBike.KEY.equals(name)) {
            enc = GetOffBike.create();
        } else if (RoadClass.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(RoadClass.KEY, RoadClass.class);
        } else if (RoadClassLink.KEY.equals(name)) {
            enc = new SimpleBooleanEncodedValue(RoadClassLink.KEY);
        } else if (RoadEnvironment.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(RoadEnvironment.KEY, RoadEnvironment.class);
        } else if (RoadAccess.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(RoadAccess.KEY, RoadAccess.class);
        } else if (MaxSpeed.KEY.equals(name)) {
            enc = MaxSpeed.create();
        } else if (MaxWeight.KEY.equals(name)) {
            enc = MaxWeight.create();
        } else if (MaxHeight.KEY.equals(name)) {
            enc = MaxHeight.create();
        } else if (MaxWidth.KEY.equals(name)) {
            enc = MaxWidth.create();
        } else if (MaxAxleLoad.KEY.equals(name)) {
            enc = MaxAxleLoad.create();
        } else if (MaxLength.KEY.equals(name)) {
            enc = MaxLength.create();
        } else if (Surface.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(Surface.KEY, Surface.class);
        } else if (Smoothness.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(Smoothness.KEY, Smoothness.class);
        } else if (Toll.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(Toll.KEY, Toll.class);
        } else if (TrackType.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(TrackType.KEY, TrackType.class);
        } else if (BikeNetwork.KEY.equals(name) || FootNetwork.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(name, RouteNetwork.class);
        } else if (Hazmat.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(Hazmat.KEY, Hazmat.class);
        } else if (HazmatTunnel.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(HazmatTunnel.KEY, HazmatTunnel.class);
        } else if (HazmatWater.KEY.equals(name)) {
            enc = new EnumEncodedValue<>(HazmatWater.KEY, HazmatWater.class);
        } else if (Lanes.KEY.equals(name)) {
            enc = Lanes.create();
        } else if (MtbRating.KEY.equals(name)) {
            enc = MtbRating.create();
        } else if (HikeRating.KEY.equals(name)) {
            enc = HikeRating.create();
        } else if (HorseRating.KEY.equals(name)) {
            enc = HorseRating.create();
        } else if (Country.KEY.equals(name)) {
            enc = Country.create();
        } else if (name.endsWith(Subnetwork.key(""))) {
            enc = new SimpleBooleanEncodedValue(name);
        } else {
            throw new IllegalArgumentException("DefaultEncodedValueFactory cannot find EncodedValue " + name);
        }
        return enc;
    }

}

