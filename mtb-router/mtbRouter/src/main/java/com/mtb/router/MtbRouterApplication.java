package com.mtb.router;



import com.graphhopper.http.CORSFilter;
import com.graphhopper.navigation.NavigateResource;
import com.mtb.router.cli.ImportCommand;
import com.mtb.router.cli.MatchCommand;
import com.mtb.router.http.GraphHopperBundle;
import com.mtb.router.http.RealtimeBundle;
import com.mtb.router.resources.RootResource;
import io.dropwizard.Application;
import io.dropwizard.assets.AssetsBundle;
import io.dropwizard.setup.Bootstrap;
import io.dropwizard.setup.Environment;

import javax.servlet.DispatcherType;
import java.util.EnumSet;

//@SpringBootApplication
public class MtbRouterApplication extends Application<GraphHopperServerConfiguration> {
    public static void main(String[] args) throws Exception {
        new MtbRouterApplication().run(args);
        //SpringApplication.run(MtbRouterApplication.class, args);
    }
    @Override
    public void initialize(Bootstrap<GraphHopperServerConfiguration> bootstrap) {

        bootstrap.addBundle(new GraphHopperBundle());
        bootstrap.addBundle(new RealtimeBundle());
        bootstrap.addCommand(new ImportCommand());
        bootstrap.addCommand(new MatchCommand());
        bootstrap.addBundle(new AssetsBundle("/com/graphhopper/maps/", "/maps/", "index.html"));
        // see this link even though its outdated?! // https://www.webjars.org/documentation#dropwizard
        bootstrap.addBundle(new AssetsBundle("/META-INF/resources/webjars", "/webjars/", null, "webjars"));
    }

    @Override
    public void run(GraphHopperServerConfiguration configuration, Environment environment) {
        environment.jersey().register(new RootResource());
        environment.jersey().register(NavigateResource.class);
        environment.servlets().addFilter("cors", CORSFilter.class).addMappingForUrlPatterns(EnumSet.allOf(DispatcherType.class), false, "*");
    }
}
