# Final Working Code Repository 

Gabriela Birardi Senior Thesis  
Spring 2023  
Advisor: Frank Pazzaglia (EES Department)  

## Description

Here are the files for the final code that I used to complete my senior thesis project. There are different files for simualting reainfall over as many years as entered and code for simulating hurricane level events. For my thesis they were run in the rainfall first then experieneces the hurricanes. 

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Folders Overview](#Folders)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

## Installation

To be able to run the files you need to download the developer version of LandLab (https://landlab.readthedocs.io/en/master/development/install/index.html). Make sure to keep it updated. All of this code was created using the IDE Visual Studio Code but any other IDE should work as well, you just need to make sure that when you run a file it is done in the landlab_dev kernel. (your install could create a different name but if your compiler is unable to identify the component imports then it is likely that you are not running in the correct kernel or the install was messed up). You will also need to have the most updated of Python installed on your computer. All of the code is written in Python but it is located in juptyer notebook files. 

## Usage

There are 2 main types of files here: ones that simulate the hurricane events and produce hydrographs and then those that run rainfall for the watershed for the alloted time of years. The process is that the watershed is run with the determined conditions for a given amount of years and then exported to another file to simulate the hurricane events. There are also different files set up to use a real Alexauken Creek watershed or the synthetic topography created using Fastscape component of landlab. To read more about the components for landlab and how to use them visit: https://landlab.readthedocs.io/en/master/reference/components/index.html 


## Folders 
- images : is where all the images produced in the coe are saved to
- topography : is where all the ascii and text files for topography importing and exporting are saved
- code_storms : code for simulating the hurricane level storms
- code_rainfall : code for simulating the rainfall

## Acknowledgments

I talked with several other eople more familiar with landlab as I was learning how to use it. Charlie Shobe who is currently at West Virginia University was very helpful in understanding the SPACE component which he helped create. Also from Tulane University, Laurent Roberge and Nicole Gasparini were helpful in understanding overland flow , rainfall and combining the components. 

## Contact

My personal email is gsbirardi@gmail.com if you have any questions or you can also find and contact me on LinkedIn.  
  
Original GitHub repo link: 

## Tips
Here are just some random useful tips I learned
- use 'print(mg.fields())' to print out all the field that exist 
