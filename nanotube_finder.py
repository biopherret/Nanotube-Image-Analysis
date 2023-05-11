import os
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from sklearn.cluster import AgglomerativeClustering
from joblib import Parallel, delayed
import matplotlib.patches as mpatches
from scipy.spatial.distance import cdist
import pandas as pd
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import sqlalchemy as sa
import pyodbc
from skimage.morphology import skeletonize
from fil_finder import FilFinder2D
import astropy.units as u

plt.style.use('lexi_plt_style.mplstyle')

conn_str = (
    r'driver={SQL Server};'
    r'server=4C4157STUDIO\SQLEXPRESS;' #server name
    r'database=FygensonLabData;' #database name
    r'trusted_connection=yes;'
    )

#using SQLAlchemy to avoid a UserWarning
connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": conn_str})
engine = create_engine(connection_url) #create SQLAlchemy engine object

cnxn = pyodbc.connect(conn_str) #connect to server using pyodbc
cursor = cnxn.cursor()

def run_quary(quary_str):
    '''Run a quary and return the output as a pandas datafrme

    Args:
        quary_str (str): quary string (not case sensitive, SQL strings need to be enclosed in single quotes)

    Returns:
        dataframe: quary output
    '''
    with engine.begin() as conn:
        return pd.read_sql_query(sa.text(quary_str), conn)

def edit_database(quary_str):
    '''Edit database with quary

    Args:
        quary_str (str): quary string (not case sensitive, SQL strings need to be enclosed in single quotes)
    '''
    cursor.execute(quary_str)
    cnxn.commit()

def educated_guess(blue_images, green_images):
    blue_ig = [int(np.median(image) * 1.25) for image in blue_images]
    green_ig = [int(np.median(image) * 1.5) for image in green_images]

    bmin, bmax, gmin, gmax = min(blue_ig) - 10, max(blue_ig) + 10, min(green_ig) - 10, max(green_ig) + 10

    return [(blue_ig[i], green_ig[i]) for i in range(num_images)], bmin, bmax, gmin, gmax

def find_ete_length(x_points : np.array, y_points : np.array):
    '''finds the lengths (aka largest dimension) of a cluster using its x and y point data

    Args:
        x_points (np.array): 1d array of x points in the cluster
        y_points (np.array): 1d array of y points in the cluster

    Returns:
        float: length of the cluster
    '''
    return np.sqrt((max(x_points) - min(x_points))**2 + (max(y_points) - min(y_points))**2)

def outlier_probability(g : float, mu_g : float, sigma_g : float, mu_b : float, sigma_b : float, data : np.array):
    '''finds the probability of each data point being an outlier using gaussian mixture model

    Args:
        g (float): proportion of data points which are not outliers
        mu_g (float): average value of a good data point
        sigma_g (float): standard deviation of good data points
        mu_b (float): average of outlier data points
        sigma_b (float): standard deviation of outlier data points
        data (np.array): array of data

    Returns:
        np.array: probability (from 0 to 1) of each data point being an outlier
    '''

    good_term = (g)/(np.sqrt(2 * np.pi * sigma_g**2)) * np.exp(-(data - mu_g)**2/(2 * sigma_g**2)) #proportional to the probability a pixel falls in the good distribution
    bad_term = (1-g)/(np.sqrt(2 * np.pi * sigma_b**2)) * np.exp(-(data - mu_b)**2/(2 * sigma_b**2)) #proportional to the probability a pixel falls in the outlier distribution

    return (bad_term)/(good_term + bad_term)

def custom_minimize(fun, guess, args = (), max_fun_calls = None, bounds = None):
    best_par = guess
    best_chi_square = fun(best_par, *args)
    function_calls = 1
    improved = True #will stop the loop when takeing a step does not improve the result
    stop = False #will stop the loop when reach max number of function calls
    tested_parameters = []

    while improved and not stop:
        improved = False
        for dim in range(np.size(guess)):
            if best_chi_square == np.Inf:
                step_size = 5
            else:
                step_size = 1
            for step in [best_par[dim] - step_size, best_par[dim] + step_size]: #try taking either a step forward or a step backwards in one each dimension
                if step >= bounds[dim][0] and step <= bounds[dim][1]: #if the proposed step is inside the given bounds
                    test_par = list(best_par)
                    test_par[dim] = step
                    if test_par not in tested_parameters: #if we haven't previously tested this set of parameters
                        tested_parameters.append(test_par)
                        test_chi_square = fun(test_par, *args)
                        function_calls += 1
                        if test_chi_square < best_chi_square:
                            best_chi_square = test_chi_square
                            best_par = test_par
                            improved = True
            if max_fun_calls is not None and function_calls >= max_fun_calls:
                stop = True #stop the for loop if we reach the max number of function calls
                break

    return best_par

def classify_pixels(par, blue_pixel, green_pixel):
    '''classify each pixel as either background (0),  REs pixel (1), or SEs pixel(2)

    Args:
        par (tuple): (blue cutoff value, green cutoff value)
        blue_pixel (np.array): image in blue
        green_pixel (np.array): image in green

    Returns:
        np.array: classified image
    '''
    Pb, Pg = par
    if blue_pixel > Pb:
        return 1 #REs
    elif green_pixel > Pg:
        return 2 #SEs
    else:
        return 0 #background

classify_pixels = np.vectorize(classify_pixels, excluded=[0])

class cluster_image:
    def filter_lone_pixels(self):
        '''filters the cluster image for single pixels with no neighbors

        Returns:
            np.array, int: filtered image and the number of pixels which were filtered out
        '''
        unfiltered_RE_image = (self.image == 1) * 1 #this is a boolean image, where 1 -> True
        x_RE = signal.convolve2d(unfiltered_RE_image, np.ones((3,3)), mode='same')
        filtered_RE_image = unfiltered_RE_image * (x_RE > 1) #points which were originally one and had no neighbors, or were zero, will be unaffected by the convolve

        unfiltered_SE_image = (self.image == 2) * 1 #this is a boolean image, where 2 -> True
        x_SE = signal.convolve2d(unfiltered_SE_image, np.ones((3,3)), mode='same')
        filtered_SE_image = unfiltered_SE_image * (x_SE > 1)

        filtered_image = filtered_RE_image + (filtered_SE_image * 2)

        return filtered_image

    def find_clusters(self):
        '''clusters pixels in the cluster image using Agglomerative Clustering
        uses the set of SE and RE points which have already had single pixel clusters filtered out

        Returns:
            np.array, np.array: 1d array of numbers, index corresponds to the filtered point array, number corresponds to its cluster assignment. First array is for REs second for SEs
        '''

        #distance_threshold=2 means a pixel is only added to a cluster if it is touching a point in that cluster (including diagonals)
        try:
            clustering_RE = AgglomerativeClustering(n_clusters = None, compute_full_tree=True, distance_threshold=2, linkage = 'single').fit(self.RE_points) #generates the clustering map.
            clusters_RE = clustering_RE.fit_predict(self.RE_points) #gives the cluster assignment for each point in the data
        except:
            clusters_RE = np.ones(len(self.RE_points))

        try:
            clustering_SE = AgglomerativeClustering(n_clusters = None, compute_full_tree=True, distance_threshold=2, linkage = 'single').fit(self.SE_points)
            clusters_SE = clustering_SE.fit_predict(self.SE_points)
        except:
            clusters_SE = np.ones(len(self.SE_points))

        if np.size(clusters_RE) == 0:
            num_RE_clust = 0
        else:
            num_RE_clust = max(clusters_RE) + 1 #assignments are from 0 to max_num so the total number of clusters is max_num + 1

        if np.size(clusters_SE) == 0:
            num_SE_clust = 0
        else:
            num_SE_clust = max(clusters_SE) + 1 #assignments are from 0 to max_num so the total number of clusters is max_num + 1

        SE_widths = []
        for num_clust in range(num_SE_clust):
            size = len(self.SE_points[np.where(clusters_SE == num_clust)][:,1]) #get the size of the cluster

            if size > 120: #f the cluster is big enough to be a nanotube
                ete_length = find_ete_length(self.SE_points[np.where(clusters_SE == num_clust)][:,1], self.SE_points[np.where(clusters_SE == num_clust)][:,0]) #get the end to end length
                SE_widths.append(size / ete_length) #estimate the width
            else:
                SE_widths.append(np.nan)

        SE_good_clust = np.where(outlier_probability(0.9, 8, 1, 30, 5, np.array(SE_widths)) < 0.9)[0] #only keep the clusters which are unlikely to be outliers

        RE_widths = []
        for num_clust in range(num_RE_clust):
            size = len(self.RE_points[np.where(clusters_RE == num_clust)][:,1]) #get the size of the cluster

            if size > 120: #f the cluster is big enough to be a nanotube
                ete_length = find_ete_length(self.RE_points[np.where(clusters_RE == num_clust)][:,1], self.RE_points[np.where(clusters_RE == num_clust)][:,0]) #get the end to end length
                RE_widths.append(size / ete_length) #estimate the width
            else:
                RE_widths.append(np.nan)

        RE_good_clust = np.where(outlier_probability(0.9, 8, 1, 30, 5, np.array(RE_widths)) < 0.9)[0] #only keep the clusters which are unlikely to be outliers

        return clusters_RE, clusters_SE, np.array(RE_widths)[RE_good_clust], np.array(SE_widths)[SE_good_clust], RE_good_clust, SE_good_clust

    def get_length_dist(self):
        '''Get the length distribution of the found clusters

        Returns:
            np.array: length distribution
        '''
        se_contour_lengths = []
        for se_clust in self.good_SE_clusters:
            clust_ypoints = self.SE_points[self.SE_clust_assign == se_clust, 0] #get the x and y points of the cluster
            clust_xpoints = self.SE_points[self.SE_clust_assign == se_clust, 1]

            clust_image = self.filt_image[min(clust_ypoints):max(clust_ypoints), min(clust_xpoints):max(clust_xpoints)] #make a crop of the classified image to only include one cluster
            clust_image[clust_image == 1] = 0 #assign any REs points that happen to be in the image to background
            clust_image[clust_image == 2] = 1 #re-assign any 2 points to 1s so that it is a true binary image

            skuly = skeletonize(clust_image) #skelinotize the image

            fil = FilFinder2D(skuly, mask = skuly)
            fil.create_mask(border_masking=True, verbose=False, use_existing_mask=True)
            fil.medskel(verbose=False)
            try:
                fil.analyze_skeletons(skel_thresh=10*u.pix)
                se_contour_lengths.append(np.count_nonzero(fil.skeleton_longpath == 1)) #find the length of the longest path on the skeleton
            except:
                pass

        re_contour_lengths = []
        for re_clust in self.good_RE_clusters:
            clust_ypoints = self.RE_points[self.RE_clust_assign == re_clust, 0] #get the x and y points of the cluster
            clust_xpoints = self.RE_points[self.RE_clust_assign == re_clust, 1]

            clust_image = self.filt_image[min(clust_ypoints):max(clust_ypoints), min(clust_xpoints):max(clust_xpoints)] #make a crop of the classified image to only include one cluster
            clust_image[clust_image == 2] = 0 #assign any SEs points in the image to 0

            skuly = skeletonize(clust_image) #skelinotize the image

            fil = FilFinder2D(skuly, mask = skuly)
            fil.create_mask(border_masking=True, verbose=False, use_existing_mask=True)
            fil.medskel(verbose=False)
            try:
                fil.analyze_skeletons(skel_thresh=10*u.pix)
                re_contour_lengths.append(np.count_nonzero(fil.skeleton_longpath == 1)) #find the length of the longest path on the skeleton
            except:
                pass

        return np.array(re_contour_lengths), np.array(se_contour_lengths)

    def find_two_sided_clusters(self):
        '''finds clusters, and their bounds which make up two sided tubes, ie tubes which one REs side and one SEs side

        Returns:
            tuple, array: first array for the cluster pairs (REs, SEs) which make up two sided tubes, second for the (xmin, xmax, ymin, ymax) bounds of each two sided tube found
        '''

        overlapping_clusters = []
        overlapping_cluster_bounds = []
        overlapping_cluster_widths = []
        overlapping_cluster_lengths = []

        se_is_ts = np.zeros(len(self.good_SE_clusters)) #start with assumption all tubes are not part of ts tube
        re_is_ts = np.zeros(len(self.good_RE_clusters))

        for RE_cluster in self.good_RE_clusters:
            RE_points = self.RE_points[np.where(self.RE_clust_assign == RE_cluster)]
            for SE_cluster in self.good_SE_clusters:
                SE_points = self.SE_points[np.where(self.SE_clust_assign == SE_cluster)]
                if np.min(cdist(RE_points, SE_points)) <= 1: #if these two clusters are touching
                    RE_size = len(self.RE_points[np.where(self.RE_clust_assign == RE_cluster)][:,1])
                    SE_size = len(self.SE_points[np.where(self.SE_clust_assign == SE_cluster)][:,1])

                    x_min = min(min(RE_points[:,1]), min(SE_points[:,1]))
                    x_max = max(max(RE_points[:,1]), max(SE_points[:,1]))
                    y_min = min(min(RE_points[:,0]), min(SE_points[:,0]))
                    y_max = max(max(RE_points[:,0]), max(SE_points[:,0]))
                    ete_length = np.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
                    width = (RE_size + SE_size) / ete_length

                    if outlier_probability(0.9, 8, 1, 30, 5, width) < 0.9: #if it is not an outlier
                        overlapping_clusters.append(np.array([RE_cluster, SE_cluster]))
                        overlapping_cluster_bounds.append(np.array([x_min, x_max, y_min, y_max]))
                        overlapping_cluster_lengths.append(ete_length)
                        overlapping_cluster_widths.append(width)

                        re_is_ts[np.where(self.good_RE_clusters == RE_cluster)] = 1 #assign this tube as being in a ts tube
                        se_is_ts[np.where(self.good_SE_clusters == SE_cluster)] = 1

        return (np.array(overlapping_clusters), np.array(overlapping_cluster_bounds), np.array((np.array(overlapping_cluster_lengths), np.array(overlapping_cluster_widths)))), (re_is_ts, se_is_ts)

    def __init__(self, par, blue, green):
        self.image = classify_pixels(par, blue, green)
        self.filt_image = self.filter_lone_pixels() #filters out classified pixels which are not neighboring any pixels of the same classification

        self.RE_points, self.SE_points = np.argwhere(self.filt_image == 1), np.argwhere(self.filt_image == 2)#[:,1] is x coordinates, [:,0] is y coordinates

        self.RE_clust_assign, self.SE_clust_assign, self.RE_clust_width, self.SE_clust_width, self.good_RE_clusters, self.good_SE_clusters = self.find_clusters() #all cluster assignments of RE pixels and SE pixel

        self.chi_square = 0

        if np.size(self.SE_clust_width) == 0: #if no SE points made it to clustering (ie no clusters are found)
            self.SE_var_width = 1
            self.chi_square = np.Inf
        else:
            if np.var(self.SE_clust_width) == 0: #if only one cluster is found
                self.SE_var_width = 1
            else:
                self.SE_var_width =  np.var(self.SE_clust_width)

        if np.size(self.RE_clust_width) == 0: #if no RE points made it to clustering (ie no clusters are found)
            self.RE_var_width = 1
            self.chi_square = np.Inf
        else:
            if np.var(self.RE_clust_width) == 0: #if only one cluster is found
                self.RE_var_width = 1
            else:
                self.RE_var_width =  np.var(self.RE_clust_width)

        if self.chi_square != np.Inf:
            self.chi_square = np.sum((self.RE_clust_width - 8)**2 / self.RE_var_width) / len(self.good_RE_clusters) + np.sum((self.SE_clust_width - 8)**2 / self.SE_var_width) / len(self.good_SE_clusters)

print('Loading images ...')
#change and get current working directory (cwd)
date_key = int(input('Input the name of the image day folder: '))
base_folders = os.listdir(f'{os.getcwd()}\Images\{str(date_key)}') #find the folder names
folder_name = input('Input the folder of images to find nanotubes in (from the Date Folder): ')
os.chdir('{}\Images\{}\{}'.format(os.getcwd(), date_key, folder_name))
image_dir = os.getcwd()
slide_sample_id = f'{date_key}{base_folders.index(folder_name):02}'

#get image files
image_files = sorted(os.listdir('{}\RAW'.format(image_dir)))
os.chdir('../')
cwd = os.getcwd()

cube_offset_df = run_quary(f'Select * From cube_offset Where date_id = {date_key}').set_index('date_id')
green_crop = [cube_offset_df.loc[date_key]['green_crop_ystart'], cube_offset_df.loc[date_key]['green_crop_yend'], cube_offset_df.loc[date_key]['green_crop_xstart'], cube_offset_df.loc[date_key]['green_crop_xend']]
blue_crop = [cube_offset_df.loc[date_key]['blue_crop_ystart'], cube_offset_df.loc[date_key]['blue_crop_yend'], cube_offset_df.loc[date_key]['blue_crop_xstart'], cube_offset_df.loc[date_key]['blue_crop_xend']]


green_images = [plt.imread('{}\RAW\{}'.format(image_dir, image_file))[green_crop[0]:green_crop[1], green_crop[2]:green_crop[3]] for image_file in image_files[1::2]] #due to the way samples are imaged, the two images are slightly misaligned so we crop the excess of each
blue_images = [plt.imread('{}\RAW\{}'.format(image_dir, image_file))[blue_crop[0]:blue_crop[1], blue_crop[2]:blue_crop[3]] for image_file in image_files[::2]] #[y-direction, x-direction]

xdim = cube_offset_df.loc[date_key]['xdim'] #retrieve dimensions of images post crop
ydim = cube_offset_df.loc[date_key]['ydim']
num_images = len(green_images)

print('Making an educated guess for the pixel classification parameters...')
initial_guesses, bmin, bmax, gmin, gmax = educated_guess(blue_images, green_images)

print('Finding best pixel classification parameters...')
best_fits = Parallel(n_jobs = -1, verbose = 10)(delayed(custom_minimize)(lambda par, blue, green : cluster_image(par, blue, green).chi_square, initial_guesses[i], args=(blue_images[i], green_images[i]), bounds = ((bmin, bmax), (gmin, gmax))) for i in range(num_images))

print('Getting cluster data using best parameters ...')
best_images = Parallel(n_jobs= -1, verbose = 10)(delayed(cluster_image)(best_fits[i], blue_images[i], green_images[i]) for i in range(num_images))
two_sided_data = Parallel(n_jobs = -1, verbose = 10)(delayed(lambda cluster_im : cluster_im.find_two_sided_clusters())(best_images[im_set]) for im_set in range(num_images))

print('Exporting length data to SQL server ...')
for im_set in range(num_images):
    image_name = image_files[1::2][im_set][:-10]
    ts_im_data, ts_assignments = two_sided_data[im_set]

    res_lengths, ses_lengths = best_images[im_set].get_length_dist()

    for i in range(len(res_lengths)):
        edit_database(f"Insert Into length_distributions Values ({slide_sample_id},'{image_name}', 're', {res_lengths[i]}, {ts_assignments[0][i]})")

    for i in range(len(ses_lengths)):
        edit_database(f"Insert Into length_distributions Values ({slide_sample_id},'{image_name}', 'se', {ses_lengths[i]}, {ts_assignments[1][i]})")

    ts_lengths = ts_im_data[2][0]
    for ts_tube in ts_lengths:
        edit_database(f"Insert Into length_distributions (slide_sample_id, image_name, length_type, lengths) Values ({slide_sample_id},'{image_name}', 'ts', {ts_tube})")


print('Plotting and exporting found clusters ...')
if num_images%6 == 0:
    num_rows = int(num_images/6)
else:
    num_rows = int(num_images/6) + 1

figs, axs = plt.subplots(num_rows, 6, figsize = (60, 7.5 * int(num_images/6)))

for im_set in range(num_images):
    i = int(im_set/6)
    j = im_set - i*6
    image_name = image_files[1::2][im_set][:-10]
    axs[i,j].set_title('{} $\chi^2$ {:.2f}'.format(image_name, best_images[im_set].chi_square))
    for re_cluster in best_images[im_set].good_RE_clusters:
        axs[i,j].scatter(best_images[im_set].RE_points[best_images[im_set].RE_clust_assign == re_cluster,1], best_images[im_set].RE_points[best_images[im_set].RE_clust_assign == re_cluster,0], s = 1, c = '#1f77b4')

    for se_cluster in best_images[im_set].good_SE_clusters:
        axs[i,j].scatter(best_images[im_set].SE_points[best_images[im_set].SE_clust_assign == se_cluster,1], best_images[im_set].SE_points[best_images[im_set].SE_clust_assign == se_cluster,0], s = 1, c = '#2ca02c')

    for two_sided_bounds in two_sided_data[im_set][0][1]:
        left, bottom, width, height = two_sided_bounds[0], two_sided_bounds[2], two_sided_bounds[1] - two_sided_bounds[0], two_sided_bounds[3] - two_sided_bounds[2] #determine location and size of box to plot to outline twosided tubes
        rect = mpatches.Rectangle((left, bottom), width, height, fill = False, color = 'purple', linewidth = 2)
        axs[i,j].add_patch(rect)

    axs[i,j].set_ylim((0, ydim))
    axs[i,j].set_xlim((0, xdim))
    axs[i,j].invert_yaxis()

plt.savefig(f'{folder_name}\\Nanotube finder results')
plt.show()
plt.close()