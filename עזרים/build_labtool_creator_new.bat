pyinstaller --noconfirm --onefile --windowed --add-binary "./Code Files/NKTPDLL.dll;." --add-data "./Code Files/NKTP_DLL.py;." --add-data "./Code Files/connections.json;." --add-data "./Code Files/LASER.py;." --add-data "./Code Files/OSA.py;." --add-data "./Code Files/Operator.py;." --add-data "./Code Files/GUI.py;." --add-data "./Code Files/allantools.py;." --add-data "./Code Files/Analyzer.py;." --add-data "./Code Files/Interactive_Graph.py;." "./Code Files/GUI.py"

copy /Y ".\Code Files\connections.json" "dist"
copy /Y ".\Code Files\NKTPDLL.dll" "dist"
rmdir /S /Q build
pause