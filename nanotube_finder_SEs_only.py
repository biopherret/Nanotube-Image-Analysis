import os
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from sklearn.cluster import AgglomerativeClustering
from joblib import Parallel, delayed
import pandas as pd
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import sqlalchemy as sa
import pyodbc

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
    
def edit_database(quary_str):
    '''Edit database with quary

    Args:
        quary_str (str): quary string (not case sensitive, SQL strings need to be enclosed in single quotes)
    ''' 
    cursor.execute(quary_str)
    cnxn.commit()

def educated_guess(green_images):
    green_ig = [int(np.median(image) * 1.5) for image in green_images]

    gmin, gmax = min(green_ig) - 10, max(green_ig) + 10

    return [[green_ig[i]] for i in range(num_images)], gmin, gmax

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

def classify_pixels(par, green_pixel):
    '''classify each pixel as either background (0) or an SEs pixel (2)

    Args:
        par (tuple): green cutoff value
        green_pixel (np.array): image to apply classification to

    Returns:
        np.array: classified image
    '''
    Pg = par[0]
    if green_pixel > Pg:
        return 2 #SEs
    else:
        return 0 #background

classify_pixels = np.vectorize(classify_pixels, excluded=[0])

class cluster_image:
    def filter_lone_pixels(self):
        '''filters the cluster image for single pixels with no neighbors

        Returns:
            np.array, int: filtered image and the number of pixels which wer e filtered out
        '''
        unfiltered_SE_image = (self.image == 2) * 1 #this is a boolean image, where 2 -> True
        x_SE = signal.convolve2d(unfiltered_SE_image, np.ones((3,3)), mode='same')
        filtered_SE_image = unfiltered_SE_image * (x_SE > 1)

        filtered_image = filtered_SE_image * 2

        return filtered_image

    def find_clusters(self):
        '''clusters pixels in the cluster image using Agglomerative Clustering
        uses the set of SE and RE points which have already had single pixel clusters filtered out

        Returns:
            np.array, np.array: 1d array of numbers, index corresponds to the filtered point array, number corresponds to its cluster assignment. First array is for REs second for SEs
        '''

        #distance_threshold=2 means a pixel is only added to a cluster if it is touching a point in that cluster (including diagonals)
        try:
            clustering_SE = AgglomerativeClustering(n_clusters = None, compute_full_tree=True, distance_threshold=2, linkage = 'single').fit(self.SE_points)
            clusters_SE = clustering_SE.fit_predict(self.SE_points)
        except:
            clusters_SE = np.ones(len(self.SE_points))

        if np.size(clusters_SE) == 0:
            num_SE_clust = 0
        else:
            num_SE_clust = max(clusters_SE) + 1 #assignments are from 0 to max_num so the total number of clusters is max_num + 1

        SE_sizes = np.array([len(self.SE_points[np.where(clusters_SE == num_clust)][:,1]) for num_clust in range(num_SE_clust)]) #find the sizes of each cluster

        SE_ete_lengths = np.array([find_ete_length(self.SE_points[np.where(clusters_SE == num_clust)][:,1], self.SE_points[np.where(clusters_SE == num_clust)][:,0]) for num_clust in range(num_SE_clust)]) #find end to end lengths of each cluster

        SE_widths = np.array([SE_sizes[num_clust] / SE_ete_lengths[num_clust] for num_clust in range(num_SE_clust)]) #use end to end lengths to get widths (roughly, this assumes straight tubes which most of them are)

        SE_good_clust = np.where((SE_sizes > 120) & (outlier_probability(0.9, 8, 1, 30, 5, SE_widths) < 0.9))[0] #clusters which are large enough to be nanotubes AND are less than 90% likely to be an outlier

        SE_lengths = np.array([SE_sizes[num_clust] / 8 for num_clust in range(num_SE_clust)]) #get the contour length using the known nanotube width in pixels

        #only return dimensions for good clusters
        SE_lengths = SE_lengths[SE_good_clust]
        SE_widths = SE_widths[SE_good_clust]

        return clusters_SE, (SE_lengths, SE_widths, SE_sizes), SE_good_clust

    def __init__(self, par, green):
        self.image = classify_pixels(par, green)
        self.filt_image = self.filter_lone_pixels() #filters out classified pixels which are not neighboring any pixels of the same classification

        self.SE_points = np.argwhere(self.filt_image == 2)#[:,1] is x coordinates, [:,0] is y coordinates

        self.SE_clust_assign, self.SE_clust_dim, self.good_SE_clusters = self.find_clusters() #all cluster assignments of RE pixels and SE pixel

        if np.size(self.SE_clust_dim[1]) == 0: #if no points made it to clustering
            self.SE_var_width = 1
            self.chi_square = np.Inf
        else:
            if np.var(self.SE_clust_dim[1]) == 0:
                self.SE_var_width = 1
            else:
                self.SE_var_width = np.var(self.SE_clust_dim[1])

            self.chi_square = np.sum((self.SE_clust_dim[1] - 8)**2 / self.SE_var_width) / len(self.good_SE_clusters)

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

green_images = [plt.imread('{}\RAW\{}'.format(image_dir, image_file)) for image_file in image_files] #due to the way samples are imaged, the two images are slightly misaligned so we crop the excess of each, [y-direction, x-direction]

ydim, xdim = 1030, 1354 #images are 1354 x 1030 post crop
num_images = len(green_images)

print('Making an educated guess for the pixel classification parameters...')
initial_guesses, gmin, gmax = educated_guess(green_images)

print('Finding best pixel classification parameters...')
best_fits = Parallel(n_jobs = -1, verbose = 10)(delayed(custom_minimize)(lambda par, green : cluster_image(par, green).chi_square, initial_guesses[i], args=(green_images[i]), bounds = [(gmin, gmax)]) for i in range(num_images))

print('Getting cluster data using best parameters ...')
best_images = Parallel(n_jobs= -1, verbose = 10)(delayed(cluster_image)(classify_pixels(best_fits[i], green_images[i])) for i in range(num_images))

print('Exporting length data to SQL server ...')
for im_set in range(num_images):
    image_name = image_files[im_set][:-4]

    ses_lengths = best_images[im_set].SE_clust_dim[0]
    for se_tube in ses_lengths:
        edit_database(f"Insert Into length_distributions (slide_sample_id, image_name, length_type, lengths) Values ({slide_sample_id},'{image_name}', 'se', {se_tube})")

print('Plotting and exporting found clusters ...')
if num_images%6 == 0:
    num_rows = int(num_images/6)
else:
    num_rows = int(num_images/6) + 1

figs, axs = plt.subplots(num_rows, 6, figsize = (60, 7.5 * int(num_images/6)))

for im_set in range(num_images):
    i = int(im_set/6)
    j = im_set - i*6
    axs[i,j].set_title('{} $\chi^2$ {:.2f}'.format(image_files[im_set][:-4], best_images[im_set].chi_square))
    for se_cluster in best_images[im_set].good_SE_clusters:
        axs[i,j].scatter(best_images[im_set].SE_points[best_images[im_set].SE_clust_assign == se_cluster,1], best_images[im_set].SE_points[best_images[im_set].SE_clust_assign == se_cluster,0], s = 1, c = '#2ca02c')

    axs[i,j].set_ylim((0, ydim))
    axs[i,j].set_xlim((0, xdim))
    axs[i,j].invert_yaxis()

plt.savefig(f'{folder_name}\\Nanotube Finder Results')
plt.show()
plt.close()