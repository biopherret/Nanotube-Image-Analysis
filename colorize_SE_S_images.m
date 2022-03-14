SetOptions[$Output, FormatType -> OutputForm]
SetSharedFunction[Print]
(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];

Print["Loading Files..."]
(*Find folders in the current directory*)
BaseFolders = Flatten[FileNames[All, MainDirec]]
NumFolders = Length[BaseFolders]
RAWFolders = ParallelTable[BaseFolders[[i]] <> "\\RAW", {i, NumFolders}]
(*Make sure images taken under green fluorescence have "green" in their file name,same for blue fluorescence First part of the file name for images to be grouped must be the same so images get paired properly*)
Files = ParallelTable[Flatten[Select[FileNames[All, RAWFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
NumImages = ParallelTable[Length[Files[[i]]], {i, NumFolders}]

(*Get the Image file names, without color to use to name final stacked images*)
ImageFileNames = ParallelTable[Flatten[FileNames[All, RAWFolders[[i]]]], {i, NumFolders}]
ImageBaseFileNames = ParallelTable[FileBaseName[ImageFileNames[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Increacing contrast and croping images..."]
(*Increase contrast and crop images 
Crop so they are the same size as hte rgb stacked color images
Brightness increase value is different between images b/c blue imaging takes brighter images*)
RAWImages = ParallelTable[Import[Files[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]
MedianPixelValues = ParallelTable[ImageMeasurements[RAWImages[[i, j]], "Median"], {i, NumFolders}, {j, NumImages[[i]]}]

(*0.4/Median brightness adjust sets the background image brighness to 0.4 for both images*)
Images = ParallelTable[ImageCrop[RAWImages[[i, j]]*(0.4/MedianPixelValues[[i, j]]), {1354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Creating composit images..."]
(*RBG stack green and blue fluorescence images 
green image in the red channel, blue image in the green and blue channel
increase contrast after combining the images*)
background = Image[ConstantArray[0.4, {1030, 1354}]]
ColorImages = ParallelTable[ImageAdjust[ColorCombine[{Images[[i, j]], background, background}, "RGB"], 1.8], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting color images as tifs..."]
(*Export color images to the RGB Stacks Folders as tif and jpg*)
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\RGB Stacks tif"]], {i, NumFolders}]
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\RGB Stacks jpg"]], {i, NumFolders}]
TotalImages = Sum[NumImages[[i]], {i, NumFolders}]
Progress[x_] = N[x/TotalImages, 2]*100
counter = 0
SetSharedVariable[counter]
ParallelTable[Export[BaseFolders[[i]] <> "\\RGB Stacks tif\\" <> ImageBaseFileNames[[i, j]] <> ".tif", ColorImages[[i, j]]]; counter += 1; If[Mod[counter, 10] == 0, Print[ToString[Progress[counter]] <> "% of tif images exported"]], {i, NumFolders}, {j, NumImages[[i]]}]
Print["Exporting color images as jpgs..."]
counter = 0
ParallelTable[Export[BaseFolders[[i]] <> "\\RGB Stacks jpg\\" <> ImageBaseFileNames[[i, j]] <> ".jpg", ColorImages[[i, j]]]; counter += 1; If[Mod[counter, 10] == 0, Print[ToString[Progress[counter]] <> "% of jpg images exported"]], {i, NumFolders}, {j, NumImages[[i]]}]