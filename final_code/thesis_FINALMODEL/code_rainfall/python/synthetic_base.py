# Gabriela Birardi
# EES393 Thesis Work
# 5/9/2023
# Advisor: Frank Pazzaglia
# EES Department Lehigh University

# This file is to simulate base level rainfall on the synthetic topography created with fastscape landlab component. 
# Must run this file in the Landlab python kernal to be able to use all of the landlab imports 

# PYTHON IMPORTS
import numpy as np #basic python library
import matplotlib.pyplot as plt #For plotting results
from matplotlib.pyplot import figure, legend, plot, show, title, xlabel, ylabel
import cv2 
from random import randint
import math

# LANDLAB COMPONENTS 
from landlab.components import DepressionFinderAndRouter #Pit filling
from landlab.components import PriorityFloodFlowRouter #Flow routing
from landlab.components import FlowAccumulator #FlowAccumulator 
from landlab.components import ChannelProfiler 
from landlab.components import SteepnessFinder
from landlab.components import ChiFinder
from landlab.components import ExponentialWeatherer
from landlab.components import DepthDependentDiffuser
from landlab.components import SpatialPrecipitationDistribution
from landlab.components import OverlandFlow
from landlab.components import PrecipitationDistribution

# SPACE COMPONENTS 
from landlab.components import Space #SPACE model
from landlab.components import SpaceLargeScaleEroder #basically SPACE 2.0 -- use this 
from landlab.components import FastscapeEroder #calculates the amount of erosion at each node
from landlab.components import SinkFillerBarnes #replaces pits with shallow gradients for draining

# LANDLAB UTILITIES 
from landlab import RasterModelGrid #Grid utility
from landlab import imshow_grid #For plotting results
from landlab.io import read_esri_ascii #to read in an ascii file
from landlab.io import read_asc_header #to read in the header of the ascii file
from landlab.io import write_esri_ascii 
from landlab.utils.flow__distance import calculate_flow__distance

## SETTING UP THE MODEL GRID
# GRID SPECS
ncols = 100
nrows = 100
cellsize = 10

# RETRIEVE TOPO FROM ASCII
topo_dem = "sample_topo2_topographic__elevation.txt" #the name of the ascii file
topo_path = topo_dem
topo_header = read_asc_header(open(topo_path, 'r'))
(mg, z) = read_esri_ascii(topo_path, name = 'topographic__elevation', halo = 0) #generating the new grid

# FIND OUTLET
open_nodes = mg.core_nodes
min_topo = mg['node']['topographic__elevation'].argmin()
min_topo_ID = open_nodes[min_topo]
outlet_id = mg.set_watershed_boundary_condition_outlet_id(min_topo_ID, mg['node']['topographic__elevation'], -9999)
outlet_id = min_topo_ID

# HYDROLOGICALLY FILL THE aDEM
sfb = SinkFillerBarnes(mg, surface=z, method='D8', fill_flat=False) #creating an instance of sinkfillerbarnes 
sfb.run_one_step() #This is important to ensure that your future flow routing will work properly. - run the sinkfiller barnes once

# CLOSE BOUNDARIES
mg.set_closed_boundaries_at_grid_edges(bottom_is_closed=True,left_is_closed=True,right_is_closed=True,top_is_closed=True)

# PLOT THE TOPOGRAPHY 
figelev = plt.figure()#Instantiate figure as empty plot
plot = plt.subplot()#Instantiate subplot as empty plot
imshow_grid(mg, 'topographic__elevation', var_name = 'Elevation', var_units=r'm', grid_units=('m', 'm'), cmap='terrain',color_for_background=None)

# ADDING SOIL FIELD
mg.add_zeros('node', 'soil__depth')
mg.at_node['soil__depth'][:] = 2  #Set 2 m of initial soil depth at core nodes

# ADDING BEDROCK FIELD
mg.add_zeros('bedrock__elevation', at='node')
mg.at_node["bedrock__elevation"][:] = mg.at_node["topographic__elevation"] - mg.at_node['soil__depth']

# SETTING UP OUTLET ID 
mg.at_node['bedrock__elevation'][outlet_id] = 0
mg.at_node['topographic__elevation'][outlet_id] = 0
mg.at_node['soil__depth'][outlet_id] = 0
print(outlet_id)

# ADDING SURFACE WATER DEPTH
mg.add_zeros('surface_water__depth', at='node')

# ADDING SURFACE WATER DISCHARGE
mg["node"]["surface_water__discharge"] = np.zeros(mg.number_of_nodes)

#### PLOT THE TOPOGRAPHY 
figelev = plt.figure()#Instantiate figure as empty plot
plot = plt.subplot()#Instantiate subplot as empty plot
imshow_grid(mg, 'topographic__elevation', plot_name='Topographic Elevation', var_name = 'Elevation', var_units=r'm', grid_units=('km', 'km'), cmap='terrain',color_for_background=None)

## SETTING UP ALL OF THE COMPONENTS AND PARAMETERS 

# PARAMETERS FOR SPACE
K_sed = 0.0001# Lists for saving data01 # ADDED A 0 HERE 4/11
K_sp = 0.001
K_br = 0.0000001
F_f = 0.5
phi = 0.1 
H_star = 1.0
v_s = 5.0
m_sp = 0.5
n_sp = 1.0
sp_crit_sed = 50 
sp_crit_br = 100 

# SET MODEL TIME PARAM
sp_timestep = 1/365
uplift_rate = .001 # m/year
uplift_per_timestep = uplift_rate * sp_timestep
soil_rate = .00000000002739 #m/year
soil_per_per_timestep = .001*sp_timestep #0.00000273973 #1mm/year into m/hr


#INSTANTIATING COMPONENTS 
fr = PriorityFloodFlowRouter(mg, flow_metric='D8', suppress_out = True)

fa = FlowAccumulator(mg, flow_director='D8') 

df = DepressionFinderAndRouter(mg,pits = 'flow__sink_flag', reroute_flow = True) 

fsc = FastscapeEroder(mg, K_sp, m_sp, n_sp)

sp = SpaceLargeScaleEroder(mg, K_sed, K_br, F_f, phi, H_star, v_s, m_sp, n_sp, sp_crit_sed, sp_crit_br,discharge_field='surface_water__discharge')# K_sed, K_br, F_f, phi, H_star, v_s, m_sp, n_sp, sp_crit_sed, sp_crit_br 

expweath = ExponentialWeatherer(mg)

DDdiff = DepthDependentDiffuser(mg)

expweath.calc_soil_prod_rate()

np.allclose(mg.at_node['soil_production__rate'][mg.core_nodes], .0001)


## SETTING UP FIELDS TO STORE DATA
# this field is to view the change in topography 
mg.add_zeros('node', 'old__topo')
mg.add_zeros('node','change__topo')

## VARIABLES FOR OVERLAND FLOW AND PRECIP -- SEASONAL 

## OVERALL
model_total_years = 1 # (yrs)
rain_total_t =15 #8760 *1#(hrs) 3 make this for spring season actually 
model_total_t = 8760 * model_total_years #(hrs)
model_total_days = model_total_years*365

## WINTER 
winter_stm_avg_dur = 24
winter_interstm_avg_dur = 336*2
winter_stm_avg_int = .081026

## SPRING
spring_stm_avg_dur = 24
spring_interstm_avg_dur = 500
spring_stm_avg_int = .081026

## SUMMER
summer_stm_avg_dur = 24
summer_interstm_avg_dur = 200
summer_stm_avg_int = .081026
## FALL 
fall_stm_avg_dur = 24
fall_interstm_avg_dur = 336
fall_stm_avg_int = .081026

# INITIALIZE RAIN COMPONENTS 
of = OverlandFlow(mg, steep_slopes=True)
rain = PrecipitationDistribution(mg,mean_storm_duration=spring_stm_avg_dur, mean_interstorm_duration=spring_interstm_avg_dur,mean_storm_depth=spring_stm_avg_int, total_t=rain_total_t, delta_t=1.0)

# ARRAYS FOR STORING DATA
storm_time_data = []
interstorm_time_data = []
storm_amt_data = []

## SETTING UP THE VARIABLES FOR TIME LOOPING 
# LOOP ITERATION VARIABLES
model_elapsed_time = 0 
model_elapsed_years = 0
model_total_years = 30
model_time = 0

model_elapsed_days = 0 

start_year = 4 # this is to help skip saving data for the first 5 years 

# SEASONONAL LOOPING
winter_t_hrs = 89 * 24
winter_elapsed_hrs = 0

spring_t_hrs = 92 * 24
spring_elapsed_hrs = 0

summer_t_hrs = 93 * 24
summer_elapsed_hrs =0

fall_t_hrs=90 * 24
fall_elapsed_hrs = 0

title_yr = 1


## RUN THE MODEL
while model_elapsed_years < model_total_years:#over the years
    for x in range(1,5): # this is to loops tho the different seasons and change the interstorm durations 
        if x ==1:#it is winter
            stm_avg_dur = winter_stm_avg_dur
            interstm_avg_dur = winter_interstm_avg_dur
            stm_avg_int = winter_stm_avg_int
            t_hrs = winter_t_hrs
            elapsed_hrs = 0
            model_hrs = winter_t_hrs
            print("---------IN WINTER-------Year "+str(model_elapsed_years)+"------------")
        
        elif x ==2: #it is spring 
            stm_avg_dur = spring_stm_avg_dur
            interstm_avg_dur = spring_interstm_avg_dur
            stm_avg_int = spring_stm_avg_int
            t_hrs = spring_t_hrs
            print("---------IN SPRING-------Year "+str(model_elapsed_years)+"------------")
            
        elif x ==3:
            stm_avg_dur = summer_stm_avg_dur
            interstm_avg_dur = summer_interstm_avg_dur
            stm_avg_int = summer_stm_avg_int
            t_hrs = summer_t_hrs
            print("---------IN SUMMER-------Year "+str(model_elapsed_years)+"------------")
            
        elif x == 4:
            stm_avg_dur = fall_stm_avg_dur
            interstm_avg_dur = fall_interstm_avg_dur
            stm_avg_int = fall_stm_avg_int
            t_hrs = fall_t_hrs
            print("---------IN FALL-------Year "+str(model_elapsed_years)+"------------")
          
        if model_elapsed_years == 1:
            mg.at_node["old__topo"][:] = mg.at_node["topographic__elevation"] 
 
        # INITIALIZE COMPONENTS FOR THE SEASON
        mg.delete_field(loc='grid',name= 'rainfall__flux')
        rain = PrecipitationDistribution(mg,mean_storm_duration=stm_avg_dur, mean_interstorm_duration=interstm_avg_dur,mean_storm_depth=stm_avg_int, total_t=t_hrs,delta_t=1.0)
        of = OverlandFlow(mg, steep_slopes=True)

        # ARRAYS FOR STORING DATA ABOUT RAIN AND STORMS 
        stm_dur=[]
        interstm_dur=[]
        num_stm = 0
        int_pattern=[]

        ## GET STORM INFO FIRST
        first = False
        second = False
        rain.seed_generator(seedval=1)
        for (storm_t, interstorm_t) in rain.yield_storms():  # storm lengths in hrs
            for x in range(int(storm_t)):
                int_pattern.append(mg.at_grid['rainfall__flux']) #add intensity for duration of the storm
            for x in range(int(interstorm_t)):
                int_pattern.append(int(0.0)) #eno intensity during interstorm period
        
            stm_dur.append(storm_t)
            interstm_dur.append(interstorm_t)
            num_stm+=1
            storm_amt_data.append(num_stm)
        if x ==1:
            first_stm_hydro_t = stm_dur[0] + interstm_dur[0]
            print(first_stm_hydro_t)
            print("length of int_pattern " + str(len(int_pattern)))
            
        elapsed_hrs = 0
        while elapsed_hrs <= len(int_pattern):
            of.dt = of.calc_time_step() # variable time step calculated by the component
            mg.at_node['bedrock__elevation'][mg.core_nodes] += (uplift_rate*(1/8760)*of.dt)  #adding uplift to the bedrock
            mg.at_node['bedrock__elevation'][mg.core_nodes] -= (soil_rate*(1/8760)*of.dt)#adding uplift to the bedrock
            mg.at_node['soil__depth'][mg.core_nodes] += (soil_rate*(1/8760)*of.dt)#adding uplift to the bedrock
            mg.at_node['topographic__elevation'][mg.core_nodes]+= uplift_rate*(1/8760)*of.dt  #adding uplift to the bedrock

            DDdiff.run_one_step((1/8760)*of.dt) 
            of.rainfall_intensity = int_pattern[int(elapsed_hrs)]
            of.run_one_step(dt=of.dt)
            
            elapsed_hrs += of.dt # add to the elapsed time 
            
        fr.run_one_step()
        sp.run_one_step(dt = 0.25) # this is run every season -- more stable timestep 
        elapsed_hrs = 0
    if model_elapsed_years ==start_year:#save current topo as old topo
        mg.at_node["old__topo"][:] = mg.at_node["topographic__elevation"] 
    if model_elapsed_years > start_year: # now you can start saving all of the data
        mg.at_node["change__topo"][:] = (mg.at_node["topographic__elevation"] - mg.at_node['old__topo']) # calculating the change in topography and saving it
        mg.at_node['change__topo'][outlet_id] = mg.at_node['change__topo'][outlet_id+1]  # this is so make sure outlet is not messing up the data
        
        # PLOT THE TOPOGRAPHY CHANGE & SAVE THE FIGURES 
        figelev = plt.figure()#Instantiate figure as empty plot
        plot = plt.subplot()#Instantiate subplot as empty plot
        imshow_grid(mg,'change__topo', vmin = -4,vmax = 5, var_name = 'Elevation Change', var_units=r'm', grid_units=('m', 'm'), cmap='terrain',color_for_background=None)
        fname = "exp/sample_base/sample_base_change_topo"+ str(model_elapsed_years) +"_yrs"+".png"# location and name to save png  
        figelev.savefig(fname, dpi='figure', format=None)
        plt.close(figelev)
        
        # TOPO ELEV IMG AND SAVE
        figelev = plt.figure()#Instantiate figure as empty plot
        plot = plt.subplot()#Instantiate subplot as empty plot
        imshow_grid(mg,'topographic__elevation', var_name = 'Elevation', var_units=r'm', grid_units=('m', 'm'), cmap='terrain',color_for_background=None)
        fname = "exp/sample_base/sample_base_topo"+ str(model_elapsed_years) +"_yrs"+".png" # location and name to save png 
        figelev.savefig(fname, dpi='figure', format=None)
        plt.close(figelev)

        # SED FLUX IMG AND SAVE
        figelev = plt.figure()#Instantiate figure as empty plot
        plot = plt.subplot()#Instantiate subplot as empty plot
        imshow_grid(mg,'sediment__flux', vmin = -5E-5, vmax = 0,var_name = 'Sediment Flux ($m^3$)', grid_units=('m', 'm'), cmap='terrain',color_for_background=None)
        fname = "exp/sample_base/sample_base_sed_flux"+ str(model_elapsed_years) +"_yrs"+".png" # location and name to save png 
        figelev.savefig(fname, dpi='figure', format=None)
        plt.close(figelev)
        title_yr+=1 # for the title 

    model_elapsed_years +=1

## EXPORT THE MODEL GRID TO BE IMPORTED FOR THE HURRICANE
grid_fields_to_save = ["topographic__elevation"]
fname ="sample_increasing_int_topo.txt" # name and location to save too 
write_esri_ascii(fname, mg, grid_fields_to_save)
