(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];

Print["Loading Files..."]
(*find folders in the current directory*)
Folders = Flatten[ (*flattens into a 1d list*)
    FileNames[All, MainDirec] (*get names of all folders*)
    ] (*1d list of folders in the inputed date folder*)
NumFolders = Length[Folders]

(*get all image files*)
Files = ParallelTable[
    Flatten[ (*flattens into a 1d list*)
    Select[FileNames[All, Folders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], (*Get all .tif files*)
    {i, NumFolders} (*iterate through each folder*)
    ] (*2d matrix of .tif files*)
NumImages = ParallelTable[Length[Files[[i]]], {i, NumFolders}]

(*Get all image file names*)
ImageFileNames = ParallelTable[
    Flatten[ (*flattens into a 1d list*)
        FileNames[All, Folders[[i]]]], (*get all file names, including the path name*)
        {i, NumFolders} (*iterate through each folder*)
        ] (*2d matrix of file name w/ paths*)
ImageBaseFileNames =  ParallelTable[
    FileBaseName[ImageFileNames[[i, j]]], (*file remove path from name*)
    {i, NumFolders}, (*iterate through each folder*)
    {j, NumImages[[i]]} (*iterate through each image*)
    ] (*2d matrix of file names w/o paths*)

Print["Creating RAW folder and moving images..."]
ParallelTable[
    Quiet[ (*supresses error messages (happens if a RAW folder allready exists)*)
        CreateDirectory[Folders[[i]] <> "\\RAW"]], (*creates a new directory named RAW*)
        {i, NumFolders} (*iterate through all folders*)
        ] 
ParallelTable[
    CopyFile[Files[[i, j]], Folders[[i]] <> "\\RAW\\" <> ImageBaseFileNames[[i, j]] <> ".tif"], (*copy tif file to RAW folder*)
    {i, NumFolders}, (*iterate throgh all folders*)
    {j, NumImages[[i]]} (*iterate through each image*)
    ]
ParallelTable[
    DeleteFile[Folders[[i]] <> "\\" <> ImageBaseFileNames[[i, j]] <> ".tif"], (*delete original imaage file that was copied into RAW folder*)
    {i, NumFolders}, (*iterate through all folders*)
    {j, NumImages[[i]]} (*iterate through each image*)
    ]