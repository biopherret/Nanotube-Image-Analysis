from csv import excel
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

def convert_excel_tab_to_list(excel_tab):
    array = excel_tab.to_numpy()
    new_list = []
    for row in array:
        new_list.append(list(row))

    return new_list

def colapse_slide_cs_data(excel_data):
    data_per_fov = []
    combined_fov = []
    for image_name in list(excel_data.keys()):
        image_data = convert_excel_tab_to_list(excel_data[image_name])
        if image_name.split()[-1] == 'cs' or image_name.split()[-1] == 'CS': #cs will always come before slide
            combined_fov = image_data #set combined fov data to the cs data
        elif image_name.split()[-1] == 'slide':
            combined_fov += image_data #add the slide data to the cs data in the same list
            data_per_fov.append(combined_fov) #add data to fov data in one list
            combined_fov = [] #reset combined fov data
        else: #if only one image for the field of view
            data_per_fov.append(image_data)

    return data_per_fov

#change and get current working directory (cwd)
os.chdir('{}\Images\{}'.format(os.getcwd(), input('Input the directory path to folder of images to analyze from the Images folder: ')))
cwd = os.getcwd()
base_folders = os.listdir(cwd)

location_data = {}
for folder in base_folders:
    #get list of data file names
    data_files = (os.listdir('{}\{}\Location Data'.format(cwd, folder)))
    location_data[folder] = {}
    for tube_type in data_files:
        excel_data = pd.read_excel('{}\{}\Location Data\{}'.format(cwd, folder, tube_type), sheet_name = None) #this a a whole excel file, which inclues all data for one tube color of one sample
        data_per_fov = colapse_slide_cs_data(excel_data) #each element of the data_per_fov list is all the data, for a field of view, not all the data for a single image
        location_data[folder][tube_type[:-4].split()[-1]] = data_per_fov

ave_tube_per_fov = {}
for sample in location_data.keys():
    two_sided_tubes = []
    num_fov = len(location_data[sample]['full'])
    for i in range(num_fov):
        count = 0
        for full_tube in location_data[sample]['full'][i]:
            all_SE_tubes, all_RE_tubes = location_data[sample]['green'][i], location_data[sample]['blue'][i]
            if contains_SE_tube(full_tube, all_SE_tubes) and contains_RE_tube(full_tube, all_RE_tubes):
                count += 1
        two_sided_tubes.append(count)
    ave = sum(two_sided_tubes) / num_fov
    ave_tube_per_fov[sample] = ave

print(ave_tube_per_fov)
