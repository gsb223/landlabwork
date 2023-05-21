# Gabriela Birardi
# EES393 Thesis Work
# 5/9/2023
# Advisor: Frank Pazzaglia
# EES Department Lehigh University 

# This code is to simulate different hurricane level events on the ALexauken Creek and synthetic watershed
# Based on workflows from landlab official tutorials : https://landlab.readthedocs.io/en/master/user_guide/tutorials.html 

# PYTHON IMPORTS
import copy
import numpy as np
from matplotlib import pyplot as plt


# LANDLAB IMPORTS
from landlab import imshow_grid
from landlab.components import OverlandFlow, FlowAccumulator
from landlab.io import read_esri_ascii

### SETTING UP THE MODEL GRID

# Change the flags to choose the intensity of the storm and on which type of topgraphy it is being run on 
basin_flag = "IncrInt"  # "IncrInt" for a increased rainfall topography or "BaseInt" for the basefall level topography
storm_flag = "50Year"  # " 10Year" for 10-year reccurent storm or "50Year" for 50-year recurrant storm

# # Node locations for alexauken
# outlet = 1770
# midstream = 2872
# upstream = 3885

# #node locations for the synthetic topography
# outlet = 404
# midstream = 3218
# upstream = 2211

## these locations can be swapped for the ones in the following if statements based on which topography is being used


# Now based on the flag the correct topography will be imported 
if basin_flag == "BaseInt":
    # the watershed_dem can be changes to the alexauken or the synthetic topography-- right now it is set up for the alexauken creek watershed
    watershed_dem = "alex_reg_int_topo.txt" #file name and location of the ascii file to be read in containing topography values
    (rmg, z) = read_esri_ascii(watershed_dem, name="topographic__elevation")
    #setting up the locations with the Node ID number for the outlet, midstream and upstream locations
    outlet_node_to_sample = 1770 
    outlet_link_to_sample = rmg.links_at_node[outlet_node_to_sample][3]
    print(outlet_link_to_sample)
    upstream_node_to_sample = 3885 
    upstream_link_to_sample = rmg.links_at_node[upstream_node_to_sample][3]
    print(upstream_link_to_sample)
    midstream_node_to_sample = 2872 
    midstream_link_to_sample = rmg.links_at_node[midstream_node_to_sample][3]
    print(midstream_link_to_sample)
else:
    watershed_dem = "alex_increasing_int_topo.txt"  #file name and location of the ascii file to be read in containing topography values
    #setting up the locations with the Node ID number for the outlet, midstream and upstream locations
    (rmg, z) = read_esri_ascii(watershed_dem, name="topographic__elevation")
    outlet_node_to_sample = 1770 
    outlet_link_to_sample = rmg.links_at_node[outlet_node_to_sample][3]
    print(outlet_link_to_sample)
    upstream_node_to_sample = 3885 
    upstream_link_to_sample = rmg.links_at_node[upstream_node_to_sample][3]
    print(upstream_link_to_sample)
    midstream_node_to_sample = 2872 
    midstream_link_to_sample = rmg.links_at_node[midstream_node_to_sample][3]
    print(midstream_link_to_sample)
    
### RUN FLOW ROUTING 
# This will detect the drainage area and chanel
fr = FlowAccumulator(rmg)  # Instantiate flow router
fr.run_one_step()

### SETTING UP STORM INTENSITY AND DURATION

rmg.set_watershed_boundary_condition(z) #set up boundary around the model grid

# instantiate OverlandFlow component
rmg.add_zeros("surface_water__depth", at="node")
of = OverlandFlow(rmg, alpha=0.45, steep_slopes=True)

#Based on the flag chose the depth and intensity of the hurricane event. Duration of storm does not change and is 24 hrs long
if storm_flag == "10Year":
    starting_precip_mmhr = 5.0
    starting_precip_ms = 0.000001469 
    storm_duration = 86400
elif storm_flag == "50Year":
    starting_precip_mmhr = 5.29
    starting_precip_ms = 0.00000225483# 0.194818 m over 24 hr
    storm_duration = 86400 
    
# PLOT THE LOCATIONS OF OUTLET, UPSTREAM AND MIDSTREAM
plt.figure(1)
imshow_grid(rmg, z) 
plt.plot(rmg.node_x[outlet_node_to_sample], rmg.node_y[outlet_node_to_sample], "yo")
plt.plot(rmg.node_x[upstream_node_to_sample], rmg.node_y[upstream_node_to_sample], "bo")
plt.plot(rmg.node_x[midstream_node_to_sample], rmg.node_y[midstream_node_to_sample], "go")

### SIMULATE THE HURRICANE
# time variables
elapsed_time = 0.0  #(s)
model_run_time = 86400+20000  #(s) - adding 20000 to see after storm 

#variables for info storage
discharge_at_outlet = []
discharge_upstream = []
discharge_midstream = []
hydrograph_time = []

#set up needed fields
rmg["node"]["surface_water__discharge"] = np.zeros(rmg.number_of_nodes)

### LOOP TO RUN IT 
while elapsed_time < model_run_time:
    
    of.dt = of.calc_time_step()#adaptive time stepping 

    # add rainfall to the model grid only during the duration of the storm 
    if elapsed_time < (storm_duration):
        of.rainfall_intensity = starting_precip_ms
    else:  #no more rainfall 
        of.rainfall_intensity = 0.0

    of.run_one_step()  #generate the overland flow

    #saving time and discharge values 
    q = rmg.at_link["surface_water__discharge"]
    discharge_at_outlet.append(np.abs(q[outlet_link_to_sample]) * rmg.dx )
    discharge_upstream.append(np.abs(q[upstream_link_to_sample]) * rmg.dx )
    discharge_midstream.append(np.abs(q[midstream_link_to_sample]) * rmg.dx)

    #add to the elapsed time based on the overland flow created timestep
    elapsed_time += of.dt
    
    
### CREATING THE HYDROGRAPHS 

#set up the figure and subplot
plot = plt.figure()
hydro = plt.subplot()

#calculate equilibrium discharges first
outlet_eq_q = starting_precip_ms * rmg.at_node["drainage_area"][outlet_node_to_sample]
midstream_eq_q = (starting_precip_ms * rmg.at_node["drainage_area"][midstream_node_to_sample])
upstream_eq_q = (starting_precip_ms * rmg.at_node["drainage_area"][upstream_node_to_sample])

#now plot those equil discharges
plt.axhline(y=outlet_eq_q, color='y', linestyle='--',label="outlet eq Q")
plt.axhline(y=midstream_eq_q, color='g', linestyle='--',label="midstream eq Q")
plt.axhline(y=upstream_eq_q, color='b', linestyle='--', label="upstream eq Q")

# plot the actual hydrograph lines
hydro.plot(hydrograph_time, discharge_at_outlet, "y-", label="outlet")
hydro.plot(hydrograph_time, discharge_midstream, "g-", label="midstream")
hydro.plot(hydrograph_time, discharge_upstream, "b-", label="upstream")

# plot the end of the storm
hydro.plot([storm_duration, storm_duration], [0, 100], "k-", linewidth=2, label="storm end")

# add labels and formatting 
plt.ylabel("Discharge (cms)")
plt.xlabel("Time (seconds)")
plt.legend(loc="upper left")
title_text = "Hydrographs"
plt.title(title_text)
plt.axis([0, 20000, 0, 0.5]) 