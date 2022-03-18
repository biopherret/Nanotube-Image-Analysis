import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def fov_volume(cs_size, sample_volume):
    '''Give cover slip size in mm, assumeing a square coverslip, and the sample volume in uL,
    return the volume of a field of view, in uL'''
    pixel_per_um = 15.4792
    #1uL = 1mm^3
    fov_z = sample_volume / (cs_size)**2 #mm
    fov_x = (1354 / pixel_per_um) * 10**(-3) #convert pixels to microns to mm
    fov_y = (1030 / pixel_per_um) * 10**(-3) 

    return fov_x * fov_y * fov_z #uL

def find_seed_concentration(seed_added_uL, perc_yield_seed):
    tile_anenal_uL = 20

    seed_nM_pre_dilution = perc_yield_seed * 10
    seed_nmol_per_uL = seed_nM_pre_dilution * seed_added_uL
    return seed_nmol_per_uL / tile_anenal_uL

def convert_excel_tab_to_list(excel_tab):
    array = excel_tab.to_numpy()
    new_list = []
    for row in array:
        new_list.append(list(row))

    return new_list

def two_sided_data(data):
    ts_data = {}
    for row in data:
        if str(row[2]) == 'nan':
            ts_data[row[0]] = {'ts count per fov' : float(row[1]), 'cs size' : float(row[3]), 'sample vol' : float(row[4]), 'seed added': float(row[5]), 'seed yield' : float(row[6])}

    return ts_data

def one_sided_data(data):
    os_data = {}
    for row in data:
        if str(row[1]) == 'nan':
            os_data[row[0]] = {'os count per fov' : float(row[2]), 'cs size' : float(row[3]), 'sample vol' : float(row[4]), 'seed added': float(row[5]), 'seed yield' : float(row[6])}

    return os_data

avn = 6.022 * 10**(23)

#change and get current working directory (cwd)
os.chdir('{}\Images'.format(os.getcwd()))
cwd = os.getcwd()
edata = pd.read_excel('{}\Processed Data.xlsx'.format(cwd), sheet_name = None)
data = convert_excel_tab_to_list(edata['Tabelle1'])
ts_data = two_sided_data(data)
os_data = one_sided_data(data)

for seed_type in list(ts_data.keys()):
    fov_vol = fov_volume(ts_data[seed_type]['cs size'], ts_data[seed_type]['sample vol'])
    seed_nM = find_seed_concentration(ts_data[seed_type]['seed added'], ts_data[seed_type]['seed yield'])
    tubes_per_uL = ts_data[seed_type]['ts count per fov'] / fov_vol
    tubes_per_L = tubes_per_uL * 10**(6)
    tube_nM = (tubes_per_L / avn) * 10**(9)
    perc_yield = (tube_nM / seed_nM) * 100

    print('{}: {}%'.format(seed_type, perc_yield))

x = []
heights = []
for seed_type in list(os_data.keys()):
    fov_vol = fov_volume(os_data[seed_type]['cs size'], os_data[seed_type]['sample vol'])
    seed_nM = find_seed_concentration(os_data[seed_type]['seed added'], os_data[seed_type]['seed yield'])
    tubes_per_uL = os_data[seed_type]['os count per fov'] / fov_vol
    tubes_per_L = tubes_per_uL * 10**(6)
    tube_nM = (tubes_per_L / avn) * 10**(9)
    perc_yield = (tube_nM / seed_nM) * 100

    x.append(seed_type)
    heights.append(perc_yield)

    print('{}: {}%'.format(seed_type, perc_yield))

plt.bar(x, heights)
plt.title('One Sided Seeded Nanotube Yield')
plt.ylabel('Percent Yield Relative to added Seed')
plt.xlabel('Scaffold')
plt.show()

x = []
heights = []
for seed_type in list(ts_data.keys()):
    fov_vol = fov_volume(ts_data[seed_type]['cs size'], ts_data[seed_type]['sample vol'])
    seed_nM = find_seed_concentration(ts_data[seed_type]['seed added'], ts_data[seed_type]['seed yield'])
    tubes_per_uL = ts_data[seed_type]['ts count per fov'] / fov_vol
    tubes_per_L = tubes_per_uL * 10**(6)
    tube_nM = (tubes_per_L / avn) * 10**(9)
    perc_yield = (tube_nM / seed_nM) * 100

    x.append(seed_type)
    heights.append(perc_yield)

    print('{}: {}%'.format(seed_type, perc_yield))

plt.bar(x, heights)
plt.title('Two Sided Seeded Nanotube Yield')
plt.ylabel('Percent Yield Relative to added Seed')
plt.xlabel('Scaffold')
plt.show()