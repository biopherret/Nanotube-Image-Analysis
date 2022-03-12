import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
import os

#assumes the following path format
#\Nanotube Image Analysis
#   this file.py
#   \Images
#       \Date1
#       \Date2
#           \images folder
#           \another images folder
#               \RGB Stacks jpg
#                   image 1
#                   image 2

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

for image_file_name in image_files:
    #create a 1354 x 1030 pixel, 72 dpi, blank figure with no frame
    fig = plt.figure(frameon=False)
    fig.set_size_inches(18.806,14.306)
    ax = plt.Axes(fig, [0,0,1,1])
    ax.set_axis_off()
    fig.add_axes(ax)

    #add original image to blank image
    image = plt.imread('{}\{}'.format(org_image_dir, image_file_name))
    ax.imshow(image, aspect = 'auto')

    #add the scale bar
    scalebar = AnchoredSizeBar(ax.transData,
                       155, '10 \u03BCm', 'lower right', #pixel length of the bar, caption, position
                        pad=1,
                       color='white',
                       frameon=False,
                       size_vertical=5,
                       fontproperties=fm.FontProperties(size=18))
    ax.add_artist(scalebar)

    #export scale bar images
    plt.savefig('{}\{}'.format(new_folder, image_file_name), dip = 72, fromat = 'jpg')
    plt.close()