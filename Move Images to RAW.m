(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];

Print["Loading Files..."]
(*find folders in the current directory*)
Folders = Flatten[FileNames[All, MainDirec]]
NumFolders = Length[Folders]

(*get all image files*)
Files = ParallelTable[Flatten[Select[FileNames[All, Folders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
NumImages = ParallelTable[Length[Files[[i]]], {i, NumFolders}]

(*Get all image file names*)
ImageFileNames = ParallelTable[Flatten[FileNames[All, Folders[[i]]]], {i, NumFolders}]
ImageBaseFileNames =  ParallelTable[FileBaseName[ImageFileNames[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Creating RAW folder and moving images..."]
ParallelTable[Quiet[CreateDirectory[Folders[[i]] <> "\\RAW"]], {i, NumFolders}] 
ParallelTable[CopyFile[Files[[i, j]], Folders[[i]] <> "\\RAW\\" <> ImageBaseFileNames[[i, j]] <> ".tif"], {i, NumFolders}, {j, NumImages[[i]]}]
ParallelTable[DeleteFile[Folders[[i]] <> "\\" <> ImageBaseFileNames[[i, j]] <> ".tif"], {i, NumFolders}, {j, NumImages[[i]]}]