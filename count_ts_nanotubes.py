from email.errors import InvalidMultipartContentTransferEncodingDefect
import os
import pandas as pd
import numpy as np

def is_in(tube: np.array, full_tube: np.array):
    '''given a sub tube (RE or SE) and a full tube, 
    returns True if the sub tube box is located in the full tube box
    else returns False'''
    pad = 3
    if (tube[0] >= (full_tube[0] - pad)) and (tube[1] >= (full_tube[1] - pad)) and (tube[2] <= (full_tube[2] + pad)) and (tube[3] <= (full_tube[3] + pad)):
        return True
    else:
        return False

def contains_SE_tube(full_tube: np.array, SE_tube_locations: np.array):
    '''given a full tube, and all of the SE tube locations,
    returns True if there is a SE tube in the full tube location
    else returns False'''
    for SE_tube in SE_tube_locations:
        if is_in(SE_tube, full_tube):
            return True
    
    return False

def contains_RE_tube(full_tube: np.array, RE_tube_locations: np.array):
    '''given a full tube, and all of the SE tube locations,
    returns True if there is a SE tube in the full tube location
    else returns False'''
    for RE_tube in RE_tube_locations:
        if is_in(RE_tube, full_tube):
            return True
    
    return False

#change and get current working directory (cwd)
os.chdir('{}\Images\{}'.format(os.getcwd(), input('Input the directory path to folder of images to analyze from the Images folder: ')))
cwd = os.getcwd()

base_folders = os.listdir(cwd)

location_data = {}
for folder in base_folders:
    #get list of data file names
    data_files = (os.listdir('{}\{}\Location Data'.format(cwd, folder)))
    location_data[folder] = {}
    for data_type in data_files:
        excel_data = pd.read_excel('{}\{}\Location Data\{}'.format(cwd, folder, data_type), sheet_name = None)
        data = []
        for i in range(len(excel_data)): #colapse date from each image into one matrix 
            image = list(excel_data.keys())[i]
            for tube_data in excel_data[image].to_numpy():
                data.append(list(tube_data))
        location_data[folder][data_type[:-4].split()[-1]] = data

for sample in location_data.keys():
    two_sided_tubes = 0
    for full_tube in location_data[sample]['full']:
        all_SE_tubes, all_RE_tubes = location_data[sample]['green'], location_data[sample]['blue']
        if contains_SE_tube(full_tube, all_SE_tubes) and contains_RE_tube(full_tube, all_RE_tubes):
            two_sided_tubes = two_sided_tubes + 1
    print('{}: {}'.format(sample, two_sided_tubes))