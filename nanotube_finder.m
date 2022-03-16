SetOptions[$Output, FormatType -> OutputForm]
SetSharedFunction[Print]
(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];
Sidedness = ToString[Input["ts or os tubes?: "]]

(*Hardcoded Inputs*)
g = 2
FinalMedian = 0.25
FinalMax = 1.3

Print["Loading Files..."]
BaseFolders = Flatten[FileNames[All, MainDirec]] (*find folders in the current directory*)
NumFolders = Length[BaseFolders]
RAWFolders = ParallelTable[BaseFolders[[i]] <> "\\RAW", {i, NumFolders}] (*get the RAW folder directory*)
Files = ParallelTable[Flatten[Select[FileNames[All, RAWFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}] (*load all tif files*)
NumImages = ParallelTable[Length[Files[[i]]], {i, NumFolders}]
ImageFileNames = ParallelTable[Flatten[FileNames[All, RAWFolders[[i]]]], {i, NumFolders}] (*get the Image file names w/ file path*)
ImageBaseFileNames = ParallelTable[FileBaseName[ImageFileNames[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}] (*get just the file names*)

Print["Increacing contrast and croping images..."]
(*Explination of how the adjust parameters work in lab notes*)
AdjustParams = Quiet[Solve[(b + 1) (c + 1) d^g - c/2 == FinalMedian && (b + 1) (c + 1) m^g - c/2 == FinalMax, {b, c}]]
b[d_, m_] = AdjustParams[[1,1,2]]
c[d_, m_] = AdjustParams[[1,2,2]]

RAWImages = ParallelTable[ImageCrop[Import[Files[[i, j]]], {1354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}] (*load and crop images*)
MedianPixelValues = ParallelTable[ImageMeasurements[RAWImages[[i, j]], "Median"], {i, NumFolders}, {j, NumImages[[i]]}] (*find median and max pixel values of pre adjusted iamges*)
MaxPixelValues = ParallelTable[ImageMeasurements[RAWImages[[i, j]], "Max"], {i, NumFolders}, {j, NumImages[[i]]}]
AdjustImages = ParallelTable[ImageAdjust[RAWImages[[i,j]], {c[MedianPixelValues[[i,j]], MaxPixelValues[[i,j]]], b[MedianPixelValues[[i,j]], MaxPixelValues[[i,j]]], 2}], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting adjusted images as jpgs..."]
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\Adjust"]], {i, NumFolders}]
TotalImages = Sum[NumImages[[i]], {i, NumFolders}]
Progress[x_] = ToIntN[x/TotalImages, 2]*100
counter = 0
SetSharedVariable[counter]
ParallelTable[Export[BaseFolders[[i]] <> "\\Adjust\\" <> ImageBaseFileNames[[i, j]] <> ".jpg", Images[[i, j]]]; counter += 1; If[Mod[counter, 10] == 0, Print[ToString[Progress[counter]] <> "% of adjusted images exported"]], {i, NumFolders}, {j, NumImages[[i]]}]



(*For two sided tubes make sure images taken under green fluorescence have "green" in their file name,same for blue fluorescence 
First part of the file name for images to be grouped must be the same so images get paired properly*)