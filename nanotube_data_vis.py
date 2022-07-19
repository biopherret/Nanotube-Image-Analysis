import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('sarah_plt_style.mplstyle')

def fov_volume(cs_size, sample_volume):
    '''Give cover slip size in mm, assuming a square coverslip, and the sample volume in uL,
    return the volume of a field of view, in uL'''
    pixel_per_um = 15.4792
    #1uL = 1mm^3
    fov_z = sample_volume / (cs_size)**2 #mm
    fov_x = (1354 / pixel_per_um) * 10**(-3) #convert pixels to microns to mm
    fov_y = (1030 / pixel_per_um) * 10**(-3) 

    return fov_x * fov_y * fov_z #uL

def find_seed_concentration(seed_added_uL, purified_seed_nM, nanotube_added_uL, sample_uL):
    tile_anneal_uL = 20

    tile_anneal_seed_nM = (purified_seed_nM * seed_added_uL) / tile_anneal_uL
    slide_seed_nM = (tile_anneal_seed_nM * nanotube_added_uL) / sample_uL
    return slide_seed_nM

def convert_excel_tab_to_lists(excel_tab):
    array = np.transpose(excel_tab.to_numpy())

    if np.shape(array)[0] == 2:
        se_lengths = list(array[1])
        return se_lengths
    elif np.shape(array)[0] == 4:
        re_lengths = list(array[1][~np.isnan(array[1])])
        se_lengths = list(array[2][~np.isnan(array[2])])
        ts_lengths = list(array[3][~np.isnan(array[3])])
        return re_lengths, se_lengths, ts_lengths

def colapse_slide_cs_data(excel_data):
    data_per_fov = []
    combined_fov = []
    for image_name in list(excel_data.keys()):
        image_data = convert_excel_tab_to_lists(excel_data[image_name])

        if len(image_name.split()) == 1:
            data_per_fov.append(image_data)
        else:
            if image_name.split()[-2] == 'cs' or image_name.split()[-2] == 'CS' or image_name.split()[-1] =='cs' or image_name.split()[-1] == 'CS': #cs will always come before slide
                combined_fov = image_data #set combined fov data to the cs data
            elif image_name.split()[-2] == 'slide' or image_name.split()[-1] == 'slide':
                combined_fov += image_data #add the slide data to the cs data in the same list
                data_per_fov.append(combined_fov) #add data to fov data in one list
                combined_fov = [] #reset combined fov data
            else: #if only one image for the field of view
                data_per_fov.append(image_data)

    return np.array(data_per_fov, dtype=object)

def get_percent_yield(num_tubes, num_fov, sample):
    sample_fov_volume = fov_volume(sample['cs size'], sample['sample volume'])
    sample_seed_concentration = find_seed_concentration(sample['seed volume added'], sample['seed concentration'], sample['nanotube volume added'], sample['sample volume'])
    tubes_per_uL = num_tubes / (sample_fov_volume * num_fov)
    tubes_per_L = tubes_per_uL * 10**(6)
    tube_nM = (tubes_per_L / avn) * 10**(9)
    sample_percent_yield = (tube_nM / sample_seed_concentration) * 100

    return sample_percent_yield

#get data from excel files
f = open('Images/seed_data.json') #open json file (has the parameters of each sample, and the folder names)
data = json.load(f) #save json as a dictionary 
f.close() #close json file

avn = 6.022 * 10**(23) #avagadros number

seed_len_types = ['p3024', 's768', 's576', 's384']

os_len_dist = []
os_percent_yields = []
os_percent_yields_std = []

os_from_ts_len_dist = []
os_from_ts_percent_yields = []
os_from_ts_percent_yields_std = []

ts_len_dist = []
ts_percent_yields = []
ts_percent_yields_std = []

for seed_len in seed_len_types:
    os_seed_lens = []
    os_seed_percent_yields = []

    os_from_ts_seed_lens = []
    os_from_ts_seed_percent_yields = []

    ts_seed_lens = []
    ts_seed_percent_yields = []

    #one sided seed
    for sample in data['os {}'.format(seed_len)]:
        excel_data = pd.read_excel('Images\{}\\Nanotube finder results\\Nanotube Finder Results.xlsx'.format(sample['folder']), sheet_name = None) #this a a whole excel file, which inclues all data for one tube color of one sample
        data_per_fov_sample = colapse_slide_cs_data(excel_data)
        for fov in data_per_fov_sample:
            os_seed_lens.extend(fov)
        
        os_seed_percent_yields.append(get_percent_yield(np.size(data_per_fov_sample), len(data_per_fov_sample), sample))

    #two sided seed
    if seed_len != 's384':
        for sample in data['ts {}'.format(seed_len)]:
            #get the individual SE and RE lengths data to contribute to the one sided data
            excel_data = pd.read_excel('Images\{}\\Nanotube finder results\\Nanotube Finder Results.xlsx'.format(sample['folder']), sheet_name = None) #this a a whole excel file, which inclues all data for one tube color of one sample
            data_per_fov_sample = colapse_slide_cs_data(excel_data)

            num_os = 0
            num_ts = 0
            for fov in data_per_fov_sample:
                os_from_ts_seed_lens.extend(fov[0])
                os_from_ts_seed_lens.extend(fov[1])
                ts_seed_lens.extend(fov[2])

                num_os += len(fov[0])
                num_os += len(fov[1])
                num_ts += len(fov[2])

            os_from_ts_seed_percent_yields.append(get_percent_yield(num_os, len(data_per_fov_sample), sample))
            ts_seed_percent_yields.append(get_percent_yield(num_ts, len(data_per_fov_sample), sample))

            print(sample['folder'])
            tube_ratio = (num_os**2)/(num_ts)
            image_vol = (10**15)/(len(data_per_fov_sample) * fov_volume(sample['cs size'], sample['sample volume']) * avn)
            sample_dilution = sample['sample volume']/sample['nanotube volume added']
            tile_anneal_dilution = 20.0/sample['seed volume added']
            pure_dilution = sample['seed volume']/(10 * sample['seed anneal volume'])
            print(tube_ratio * image_vol * sample_dilution * tile_anneal_dilution * pure_dilution * 100)
            
    os_len_dist.append(os_seed_lens)
    os_percent_yields.append(np.average(os_seed_percent_yields))
    os_percent_yields_std.append(np.std(os_seed_percent_yields))

    if seed_len != 's384':
        os_from_ts_len_dist.append(os_from_ts_seed_lens)
        os_from_ts_percent_yields.append(np.average(os_from_ts_seed_percent_yields))
        os_from_ts_percent_yields_std.append(np.std(os_from_ts_seed_percent_yields))

        ts_len_dist.append(ts_seed_lens)
        ts_percent_yields.append(np.average(ts_seed_percent_yields))
        ts_percent_yields_std.append(np.std(ts_seed_percent_yields))

#print(os_percent_yields)
#print(ts_percent_yields)
#print(os_from_ts_percent_yields)

fig, axs = plt.subplots(2,2, figsize = (15,15))
axs[1,1].set_title('One-sided tubes grown from one sided seeds')
axs[1,1].bar(np.arange(len(seed_len_types)), os_percent_yields, yerr=os_percent_yields_std, align='center')
axs[1,1].set_xticks(np.arange(len(seed_len_types)))
axs[1,1].set_xticklabels(seed_len_types)
axs[1,1].set_ylabel('Percent Yield Nanotubes')
#axs[1,1].set_ylim(0, 1.25)

axs[1,0].set_title('One-sided tubes grown from two sided seeds')
axs[1,0].bar(np.arange(len(seed_len_types) - 1), os_from_ts_percent_yields, yerr=os_from_ts_percent_yields_std, align='center')
axs[1,0].set_xticks(np.arange(len(seed_len_types) -1))
axs[1,0].set_xticklabels(seed_len_types[0:-1])
axs[1,0].set_ylabel('Percent Yield Nanotubes')
#axs[1,0].set_ylim(0, 2.5)

axs[0,0].set_title('Two-sided tubes grown from two sided seeds')
axs[0,0].bar(np.arange(len(seed_len_types) - 1), ts_percent_yields, yerr=ts_percent_yields_std, align='center')
axs[0,0].set_xticks(np.arange(len(seed_len_types) -1))
axs[0,0].set_xticklabels(seed_len_types[0:-1])
axs[0,0].set_ylabel('Percent Yield Nanotubes')
#axs[0,0].set_ylim(0, 2.5)
#plt.show()

fig, axs = plt.subplots(2,2, figsize = (15,15))
axs[1,1].set_title('One-sided tubes grown from one sided seeds')
axs[1,1].hist(os_len_dist[0], alpha = 0.3, bins = 40, label = 'p3024')
axs[1,1].hist(os_len_dist[1], alpha = 0.3, bins = 40, label = 's768')
axs[1,1].hist(os_len_dist[2], alpha = 0.3, bins = 40, label = 's576')
axs[1,1].hist(os_len_dist[3], alpha = 0.3, bins = 40, label = 's384')
axs[1,1].set_ylim(0,550)
axs[1,1].set_ylabel('lengths')
fig.legend()

axs[1,0].set_title('One-sided tubes grown from two sided seeds')
axs[1,0].hist(os_from_ts_len_dist[0], alpha = 0.3, bins = 40, label = 'p3024')
axs[1,0].hist(os_from_ts_len_dist[1], alpha = 0.3, bins = 40, label = 's768')
axs[1,0].hist(os_from_ts_len_dist[2], alpha = 0.3, bins = 40, label = 's576')
axs[1,0].set_ylim(0,550)
axs[1,0].set_ylabel('lengths')

axs[0,0].set_title('Two-sided tubes grown from two sided seeds')
axs[0,0].hist(ts_len_dist[0], alpha = 0.3, bins = 40, label = 'p3024')
axs[0,0].hist(ts_len_dist[1], alpha = 0.3, bins = 40, label = 's768')
axs[0,0].hist(ts_len_dist[2], alpha = 0.3, bins = 40, label = 's576')
axs[0,0].set_ylim(0,550)
axs[0,0].set_ylabel('lengths')



#plt.show()


        





    
