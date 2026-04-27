@echo off
echo Cleaning Shreeji Ceramica App Cache...
del /q "%LOCALAPPDATA%\Shreeji Ceramica\search_index_v2.json" 2>nul
del /q "%LOCALAPPDATA%\Shreeji Ceramica\image_path_cache.json" 2>nul
echo Done! Old cache cleared. 
echo Now starting the app...
pause
