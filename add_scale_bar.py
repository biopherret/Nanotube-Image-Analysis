import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
import os

#assumes the following path format
#\Nanotube Image Analysis
#   this file.py
#   \Images
#      \some folder with images 

#change and get current working directory (cwd)
os.chdir('{}\Images\{}'.format(os.getcwd(), input('Input the directory path to folder of images to add scale bars too (from the Images Folder): ')))
org_image_dir = os.getcwd()

#get image files
image_files = os.listdir(org_image_dir)
os.chdir('../')
cwd = os.getcwd()

#make new directory
new_folder = '{}\{} with scale bars'.format(cwd, os.path.basename(os.path.normpath(org_image_dir))) 
os.mkdir(new_folder)

objective = input('What objective was used?: ')
if objective == '100x':
    pixel_per_micron = 15.5
elif objective == '60x':
    pixel_per_micron = 9.3
elif objective == '40x':
    pixel_per_micron = 6.2
elif objective == '20x':
    pixel_per_micron = 3.1
elif objective == '4x':
    pixel_per_micron = 0.62
else:
    print(f'{objective} pixel to micron conversation not saved, att the calibration measurement to the script and re-run.')

scalebar_len_um = int(input('What is the desired length of the scalebar(um)?: '))
scalebar_len_pixels = int(scalebar_len_um * pixel_per_micron)

for image_file_name in image_files:
    #create a 1354 x 1030 pixel, 72 dpi, blank figure with no frame
    fig = plt.figure(frameon=False)
    fig.set_size_inches(18.806,14.306)
    ax = plt.Axes(fig, [0,0,1,1])
    ax.set_axis_off()
    fig.add_axes(ax)

    #add original image to blank image
    image = plt.imread('{}\{}'.format(org_image_dir, image_file_name))
    ax.imshow(image, aspect = 'auto', cmap='gray')

    #add the scale bar
    scalebar = AnchoredSizeBar(ax.transData,
                       scalebar_len_pixels, f'{scalebar_len_um} \u03BCm', 'lower right', #pixel length of the bar, caption, position
                        pad=1,
                       color='white',
                       frameon=False,
                       size_vertical=10,
                       fontproperties=fm.FontProperties(size=30))
    ax.add_artist(scalebar)

    #export scale bar images
    image_file_name = image_file_name[0:-4] + '.jpg' #export as jpg
    plt.savefig('{}\{}'.format(new_folder, image_file_name))
    plt.close()