import numpy as np #basic python library
import matplotlib.pyplot as plt #For plotting results
from matplotlib.pyplot import figure, legend, plot, show, title, xlabel, ylabel, ylim
import cv2 
import glob

## Import Landlab components
from landlab.components import DepressionFinderAndRouter #Pit filling
from landlab.components import PriorityFloodFlowRouter #Flow routing
from landlab.components import FlowAccumulator #FlowAccumulator 
from landlab.components import ChannelProfiler 
from landlab.components import SteepnessFinder
from landlab.components import ChiFinder

#SPACE model
from landlab.components import Space #SPACE model
from landlab.components import SpaceLargeScaleEroder #basically SPACE 2.0 -- use this 
from landlab.components import FastscapeEroder #calculates the amount of erosion at each node
from landlab.components import StreamPowerEroder
from landlab.components import SinkFillerBarnes #replaces pits with shallow gradients for draining

## Import Landlab utilities
from landlab import RasterModelGrid #Grid utility
from landlab import imshow_grid #For plotting results
from landlab.io import read_esri_ascii #to read in an ascii file
from landlab.io import read_asc_header #to read in the header of the ascii file

"""Setting up the raster model grid"""
#Set grid parameters
num_rows = 40
num_columns = 40
node_spacing = 50.00
node_next_to_outlet = num_columns + 1


#Set Model Time Parameters
timestep = 1.0
run_time = 10 #years
sp_interval = 1

uplift_rate = .001 # m/year
uplift_per_timestep = uplift_rate * timestep

#Instantiate model grid
mg = RasterModelGrid((num_rows, num_columns), node_spacing)


#Set constant random seed for consistent topographic roughness
np.random.seed(seed = 5000)

#Add field ’topographic elevation’ to the grid
mg.add_zeros('node', 'topographic__elevation')

#topographic roughness
#random_noise = np.random.rand(len(mg.node_y)) /1000 #impose topography values on model grid


#Add field 'soil__depth' to the grid
mg.add_zeros('node', 'soil__depth')

#Set 2 m of initial soil depth at core nodes
mg.at_node['soil__depth'][mg.core_nodes] = 2.0 #meters 

#Add field 'bedrock__elevation' to the grid
mg.add_zeros('bedrock__elevation', at='node')

#Sum 'soil__depth' and 'bedrock__elevation' to yield 'topographic elevation'
mg.at_node["bedrock__elevation"] += (mg.node_y / 10. + mg.node_x / 10. + np.random.rand(len(mg.node_y)) / 10.0)

mg.at_node["topographic__elevation"][:] = mg.at_node["bedrock__elevation"]
mg.at_node["bedrock__elevation"][:] = mg.at_node["topographic__elevation"] - mg.at_node["soil__depth"]
#mg.at_node["topographic__elevation"][:] += mg.at_node["soil__depth"]

#Close all model boundary edges
mg.set_closed_boundaries_at_grid_edges(bottom_is_closed=True,left_is_closed=True,right_is_closed=True,top_is_closed=True)
outlet_node = mg.set_watershed_boundary_condition_outlet_id(0,mg['node']['topographic__elevation'], -9999.)
print(outlet_node)

"""Instantiate all of the components"""
#Parameters for SPACE and Fastscape
K_sed = 0.01
K_sp = 0.001
K_br = 0.001
F_f = 0.0
phi = 0.0
H_star = 1.0
v_s = 5.0
m_sp = 0.5
n_sp = 1.0
sp_crit_sed = 0
sp_crit_br = 0

#Instantiate the Flow accumulator
fr = PriorityFloodFlowRouter(mg, flow_metric='D8', suppress_out = True)

#Instantiate the Flow accumulator
fa = FlowAccumulator(mg, flow_director='D8') 

#Instantiate the depressionfinder and router as df
df = DepressionFinderAndRouter(mg,pits = 'flow__sink_flag', reroute_flow = True) 

#instantiate the fascape eroder as fsc 
fsc = FastscapeEroder(mg, K_sp, m_sp, n_sp)  

#Instantiate SPACE model with chosen parameters as sp
sp = SpaceLargeScaleEroder(mg, K_sed, K_br, F_f, phi, H_star, v_s, m_sp, n_sp, sp_crit_sed, sp_crit_br)

spe = StreamPowerEroder(mg, K_sp = K_sp)

"""Run Fastscape to get a base DEM at steady state"""

#below are old tries with adding uplift (having an + does not work (idk why))
#mg.at_node['bedrock__elevation'][:] += uplift_per_timestep  #adding uplift to the bedrock
    #mg.at_node['topographic__elevation'][:]= mg.at_node['bedrock__elevation'] + mg.at_node['soil__depth'] #changing the elevation to account for the uplift
    #mg.at_node["topographic__elevation"][0] -= 0.001 # Uplift
    #mg.at_node["bedrock__elevation"][0] -= 0.001 # Uplift

fsc_img_interval = np.arange(100000, 80000000, 100000) #creates a numpy array with numbers in the interval of 1000 between 1 and the 100000
#run for 80 million years total to reach steady state
fsc_tot_time = 10000000
fsc_elapsed_time = 0
fsc_timestep = 100
fsc_steps = fsc_tot_time / fsc_timestep

for x in range(10):
    while fsc_elapsed_time < fsc_tot_time:
        
        fa.run_one_step()
        #df.map_depressions()
        fsc.run_one_step(dt = fsc_timestep)

        if fsc_elapsed_time in fsc_img_interval: #if you are at the correct interval to retrieve a photo from 
            print(fsc_elapsed_time)
                #Instantiate figure as empty plot
            fig = plt.figure()
                #Instantiate subplot as empty plot
            plot= plt.subplot()
                #Create a topographic elevation plot that shows the elevation of the landscape in diff colors - using landlab utility imshow_grid
            imshow_grid(mg,"topographic__elevation", plot_name='Topographic Elevation', var_name = 'Elevation', var_units=r'm', grid_units=('m', 'm'), cmap='terrain',color_for_background=None)
            fig.savefig("C:/Users/gsbir/Documents/Github/landlabwork/testing_code/fsc_topo_images/fsc_topo_" + str(fsc_elapsed_time) + ".png")
            plt.close()
            
        fsc_elapsed_time += fsc_timestep
        #mg.at_node["topographic__elevation"][0] -= 0.001 # Uplift
        #mg.at_node["bedrock__elevation"][0] -= 0.001 # Uplift
        mg.at_node["topographic__elevation"][0] -= 0.001 #add uplift
        #mg.at_node["bedrock__elevation"][0] -= 0.001 #add uplift
        #fa.run_one_step()
        
    #produce the video with all of the pngs

    fsc_topo_image_list = []
    fsc_topo_size = None
    for file in glob.glob('C:/Users/gsbir/Documents/Github/landlabwork/testing_code/fsc_topo_images/*.png'):
        img = cv2.imread(file)
        height, width, layers = img.shape
        fsc_topo_size = (width, height)
        fsc_topo_image_list.append(img)

    fsc_topo_out = cv2.VideoWriter('fsc_topo_video30milpy.mp4',cv2.VideoWriter_fourcc(*'mp4'), 15, fsc_topo_size)
    for i in range(len(fsc_topo_image_list)):
        fsc_topo_out.write(fsc_topo_image_list[i])
    fsc_topo_out.release()
    





