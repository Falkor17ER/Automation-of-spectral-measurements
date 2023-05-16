pyinstaller --noconfirm --onefile --windowed --add-data "./Code Files/LASER.py;." --add-data "./Code Files/NKTP_DLL.py;." --add-data "./Code Files/Operator.py;." --add-data "./Code Files/OSA.py;."  "./Code Files/GUI.py"

pyinstaller --noconfirm --onefile --windowed --clean --add-data "./Code Files/allantools.py;." --add-data "./Code Files/Analyzer.py;."  "./Code Files/Interactive_Graph.py"

copy /Y ".\Code Files\connections.json" "dist"
copy /Y ".\Code Files\NKTPDLL.dll" "dist"
rmdir /S /Q build
pause