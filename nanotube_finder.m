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
(*For two sided tubes make sure images taken under green fluorescence have "green" in their file name,same for blue fluorescence 
First part of the file name for images to be grouped must be the same so images get paired properly*)
Files = If[Sidedness == "os", 
    ParallelTable[Flatten[Select[FileNames[All, RAWFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}], 
    <|
        "green" -> ParallelTable[Flatten[Select[FileNames["*green*", RAWFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}],
        "blue" -> ParallelTable[Flatten[Select[FileNames["*blue*", RAWFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
    |>]
NumImages = If[Sidedness == "os", ParallelTable[Length[Files[[i]]], {i, NumFolders}], ParallelTable[Length[Files[["green", i]]], {i, NumFolders}]]
ImageFileNames = ParallelTable[Flatten[FileNames[All, RAWFolders[[i]]]], {i, NumFolders}] (*get the Image file names w/ file path*)
ImageBaseFileNames = If[Sidedness == "os", (*get just the file names*)
    ParallelTable[FileBaseName[ImageFileNames[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}],
    ParallelTable[StringDelete[FileBaseName[ImageFileNames[[i, j]]], " blue"], {i, NumFolders}, {j, 1, NumImages[[i]] * 2, 2}]] 

Print["Increacing contrast and croping images..."]
(*Explination of how the adjust parameters work in lab notes*)
AdjustParams = Quiet[Solve[(b + 1) (c + 1) d^g - c/2 == FinalMedian && (b + 1) (c + 1) m^g - c/2 == FinalMax, {b, c}]]
b[d_, m_] = AdjustParams[[1,1,2]]
c[d_, m_] = AdjustParams[[1,2,2]]
Print["get raw images"]
RAWImages = If[Sidedness == "os", (*load and crop images*)
    ParallelTable[ImageCrop[Import[Files[[i, j]]], {1354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}],
    <|
    "green" -> ParallelTable[ImageCrop[Import[Files[["green", i, j]]], {1354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}],
    "blue" -> ParallelTable[ImageCrop[Import[Files[["blue", i, j]]], {2354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}]
    |>]
Print["get pixel value"]
PixelValues = If[Sidedness == "os", (*find median and max pixel values of pre adjusted iamges*)
    ParallelTable[ImageMeasurements[RAWImages[[i, j]], {"Median", "Max"}], {i, NumFolders}, {j, NumImages[[i]]}],
    (ParallelTable[ImageMeasurements[#[[i]], {"Median", "Max"}], {i, NumFolders}]) &/@ RAWImages]
Print["adjust images"]
Print[PixelValues[["green", 1, 1]]]
AdjustImages = If[Sidedness == "os",
    ParallelTable[ImageAdjust[RAWImages[[i,j]], {c[PixelValues[[i,j,1]], PixelValues[[i,j,2]]], b[PixelValues[[i,j,1]], PixelValues[[i,j,2]]], 2}], {i, NumFolders}, {j, NumImages[[i]]}],
    <|
        "green" -> ParallelTable[ImageAdjust[RAWImages[["green",i,j]], {c[PixelValues[["green",i,j,1]], PixelValues[["green", i,j,2]]], b[PixelValues[["green",i,j,1]], PixelValues[["green", i,j,2]]], 2}], {i, NumFolders}, {j, NumImages[[i]]}],
        "blue" -> ParallelTable[ImageAdjust[RAWImages[["blue",i,j]], {c[PixelValues[["blue", i,j,1]], PixelValues[["blue", i,j,2]]], b[PixelValues[["blue", i,j,1]], PixelValues[["blue", i,j,2]]], 2}], {i, NumFolders}, {j, NumImages[[i]]}]
    |>]


