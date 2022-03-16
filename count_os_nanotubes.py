import os
import pandas as pd

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
    one_sided_tubes = []
    num_fov = len(location_data[sample]['green'])
    for i in range(num_fov):
        count = 0
        for tube in location_data[sample]['green'][i]:
            count += 1
        one_sided_tubes.append(count)
        
    ave = sum(one_sided_tubes) / num_fov
    ave_tube_per_fov[sample] = ave

print(ave_tube_per_fov)