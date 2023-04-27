find_cropping_params.py when takeing an image in 2 different channels of the same location, there is an offset between the two images. This script takes an (x,y) of the same object in both images and determines the cropping parameters so both images will be aligned. 
seed_concentration.ipynb pulls raw concentration measurements from the server to display and store the average and std for different samples.
move_images_to_raw.py moves all raw images to a new RAW folder
add_day_to_database.py using the name of a new imaging date folder, and names of the slide folders to prompt the user for all of the anneal conditions of the sample and stores them
rgb_stacker.py takes 2 channel images and stacks them together into 1 color image. This requires images of the same location have the same name, followed by "green" and "blue". For example "image1 green.tif" and "image1 blue.tif" will be stacked together.
add_scale_bar.py prompts you for the imagining conditions and adds a scale bar to images. 
nanotube_finder_SEs_only.py finds all nanotubes in a a set of images and exports their length distributions
nanotube_finder.py does the same thing, but for SEs and REs tubes, and it searches for two-sided nanotubes
nanotube_data_vis.ipynb is used for visualizing the nanotube length distributions

All scripts in this repo are expecting the following folder structure:

add_scale_bar.py
move_images_to_raw.py
nanotube_finder_SEs_only.py
nanotube_finder.py
rgb_stacker.py
plt_style.mplstyle
Images (folder)
----> date1
----> date2
--------> folder with images 1
--------> folder with images 2

For rgb stacker and nanotube_finder, the scripts expect each folder with images to have a RAW folder containing the raw images. Use move_images_to_raw.py to setup this structure.
(Run move_images_to_raw.py and enter the date of the folder). After the folder structure will look like this:

Images (folder)
----> date1
----> date2
--------> folder 1
------------> RAW
--------> folder 2
------------> RAW

Then when you run RGB stacker or nanotube finder more directories will be added like this

Images (folder)
----> date1
----> date2
--------> folder 1
------------> RAW
------------> rgb_stackts_tif
------------> rgb_stackts_jpg
------------> Nanotube Finder Results
--------> folder 2
------------> RAW
------------> rgb_stackts_tif
------------> rgb_stackts_jpg
------------> Nanotube Finder Results

For add_scale_bar.py you need to give the entire path name to the folder you want to add scale bars too (this allows you to add scale bars to any image folder, not just the RAW folder)

For all python files, start the script as you normally would. (you will need either python or anaconda installed)

All of my scripts are made with the intent that they pull info from a local sql server and push results to the same server.
If you would like to use this same storage structure you can download SQL Express here: https://www.microsoft.com/en-us/sql-server/sql-server-downloads#:~:text=Express,web%2C%20and%20small%20server%20applications 
And it should prompt you to download MSSMS (Microsoft SQL Server Management Studio)

Otherwise, if you would like to store your data using other methods you will need to modify parts of the code to export or import data using different methods. 