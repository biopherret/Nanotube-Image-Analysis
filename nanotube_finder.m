SetOptions[$Output, FormatType -> OutputForm]
SetSharedFunction[Print]
(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
InputFolder = ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> InputFolder];

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
Print["get max and min"]
MedianPixelValues = ParallelTable[ImageMeasurements[RAWImages[[i, j]], "Median"], {i, NumFolders}, {j, NumImages[[i]]}]
MaxPixelValues = ParallelTable[ImageMeasurements[RAWImages[[i, j]], "Max"], {i, NumFolders}, {j, NumImages[[i]]}]

Print["define things"]
g = 2
FinalMedian = 0.25
FinalMax = 1.3
AdjustParams = Solve[(b + 1) (c + 1) d^g - c/2 == FinalMedian && (b + 1) (c + 1) m^g - c/2 == FinalMax, {b, c}]
b[d_, m_] = AdjustParams[[1,1,2]]
c[d_, m_] = AdjustParams[[1,2,2]]

Print["actually adjust"]
Images = ParallelTable[ImageAdjust[RAWImages[[i,j]], {c[MedianPixelValues[[i,j]], MaxPixelValues[[i,j]]], b[MedianPixelValues[[i,j]], MaxPixelValues[[i,j]]], 2}], {i, NumFolders}, {j, NumImages[[i]]}]
Print[ImageMeasurements[Images[[1, 1]], "Median"]]
Print[ImageMeasurements[RAWImages[[1, 1]], "Max"]]


ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\Adjust"]], {i, NumFolders}]
TotalImages = Sum[NumImages[[i]], {i, NumFolders}]
Progress[x_] = N[x/TotalImages, 2]*100
counter = 0
SetSharedVariable[counter]
Print["Exporting color images as jpgs..."]
ParallelTable[Export[BaseFolders[[i]] <> "\\Adjust\\" <> ImageBaseFileNames[[i, j]] <> ".jpg", Images[[i, j]]]; counter += 1; If[Mod[counter, 10] == 0, Print[ToString[Progress[counter]] <> "% of jpg images exported"]], {i, NumFolders}, {j, NumImages[[i]]}]