""" 
This code is for testing the SPACE landlab components that have already been developed
For EES 393 Research
@date_created 2/5/22
@date_last_modified 2/5/22

"""

"""Imports for libraries and components"""
import numpy as np #basic python package
import matplotlib.pyplot as plt # For plotting results

#Landlab component Imports
from landlab.components import DepressionFinderAndRouter #For pit filling
from landlab.components import FlowRouter #Flow router
from landlab.components import Space #SPACE model

##Import Landlab utilities
from landlab import RasterModelGrid #grid unitily
from landlab import imshow_grid #For plotting results
#%matplotlib inline

"""Now defining the model domains and the initial conditions"""
#Set grid parameters
num_rows = 20
num_columns = 20
node_spacing = 100.0

#Instantiate the model
mg = RasterModelGrid((num_rows, num_columns), node_spacing)

#add field ' topographic elevation' to the grid
mg.add_zeros('node', 'topographic_elevation')

#set constant random seed for consistent topographic roughness
np.random.seed(seed = 5000)

## Create initial model topography
#plane tilted towards the lower−left corner 
topo = mg.node_y/100000 + mg.node_x/100000

#topographic roughness
random_noise = np.random.rand(len(mg.node_y)) /1000 #impose topography values on model grid
mg['node']['topographic__elevation'] += (topo + random_noise) 

#Add field 'soil__depth' to the grid
mg.add_zeros('node', 'soil__depth')

#Set 2 m of initial soil depth at core nodes
mg.at_node['soil__depth'][mg.core_nodes] = 2.0 #meters 

#Add field 'bedrock__elevation' to the grid
mg.add_zeros('bedrock__elevation', at='node')

#Sum 'soil__depth' and 'bedrock__elevation'
#to yield 'topographic elevation'
mg.at_node['bedrock__elevation'][:] = mg.at_node['topographic__elevation'] 
mg.at_node['topographic__elevation'][:] += mg.at_node['soil__depth']


""" Set the boundary Conditions"""
#Close all model boundary edges
mg.set_closed_boundaries_at_grid_edges(bottom_is_closed=True,
                                       left_is_closed=True,
                                       right_is_closed=True,
                                       top_is_closed=True)

#Set lower-left (southwest) corner as an open boundary
mg.set_watershed_boundary_condition_outlet_id(0,mg['node']['topographic__elevation'], -9999.)

"""Initialize the SPACE component and other components"""
#Instantiate flow router
fr = FlowRouter(mg)

#Instantiate depression finder and router; optional
df = DepressionFinderAndRouter(mg)

#Instantiate SPACE model with chosen parameters
sp = Space(mg, K_sed=0.01, K_br=0.001, 
           F_f=0., phi=0., H_star=1., v_s=5.0, m_sp=0.5, n_sp=1.0,
           sp_crit_sed=0, sp_crit_br=0, method='simple_stream_power')

"""Run the time loop"""
#Set model timestep
timestep = 1.0 #years

#Set elapsed time to zero
elapsed_time = 0 #years

#Set timestep count to zero
count = 0

#Set model run time
run_time = 500 #years

#Array to save sediment flux values
sed_flux = np.zeros(int(run_time // timestep))
while elapsed_time < run_time: #time units of years
    #Run the flow router
    fr.run_one_step()
    
    #Run the depression finder and router; optional
    df.map_depressions()
    
    #Get list of nodes in depressions; only
    #used if using DepressionFinderAndRouter
    flooded = np.where(df.flood_status==3)[0]
    sp.run_one_step(dt = timestep, flooded_nodes=flooded)
    
    #Save sediment flux value to array
    sed_flux[count] = mg.at_node['sediment__flux'][0]
    
    #Add to value of elapsed time
    elapsed_time += timestep
    
    #Increase timestep count
    count += 1

"""Visualization code"""

"""Sediment Flux Map"""
#Instantiate figure
fig = plt.figure()

#Instantiate subplot
plot = plt.subplot()

#Show sediment flux map
imshow_grid(mg, 'sediment__flux', plot_name='Sediment flux', var_name = 'Sediment flux', var_units=r'm$^3$/yr', grid_units=('m', 'm'), cmap='terrain')


#Export figure to image
fig.savefig('sediment_flux_map.eps')

"""Sedimentograph"""
#Instantiate figure
fig = plt.figure()

#Instantiate subplot
sedfluxplot = plt.subplot()

#Plot data
sedfluxplot.plot(np.arange(500),sed_flux, color = 'k', linewidth = 3)

#Add axis labels
sedfluxplot.set_xlabel('Time [yr]')
sedfluxplot.set_ylabel(r'Sediment flux [m$^3$/yr]')

#Export figure to image
fig.savefig('sedimentograph.eps')
