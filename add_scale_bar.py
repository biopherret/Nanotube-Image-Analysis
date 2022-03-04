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
os.chdir('{}\Images\{}'.format(os.getcwd(), input('Input the directory path to folder of images to analyze from the Images folder: ')))
cwd = os.getcwd()

base_folders = os.listdir(cwd)

for folder in base_folders:
    #get list of image file names
    image_files = (os.listdir('{}\{}\RGB Stacks jpg'.format(cwd, folder)))
    #make a new directory
    os.mkdir('{}\{}\RGB Stacks jpg with scale bars'.format(cwd, folder))
    for image_file_name in image_files:
        #create a 1354 x 1030 pixel, 72 dpi, blank figure with no frame
        fig = plt.figure(frameon=False)
        fig.set_size_inches(18.806,14.306)
        ax = plt.Axes(fig, [0,0,1,1])
        ax.set_axis_off()
        fig.add_axes(ax)

        #add color image to blank image
        image = plt.imread('{}\{}\RGB Stacks jpg\{}'.format(cwd, folder, image_file_name))
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
        plt.savefig('{}\{}\RGB Stacks jpg with scale bars\{}'.format(cwd, folder, image_file_name), dip = 72, fromat = 'jpg')
        plt.close()