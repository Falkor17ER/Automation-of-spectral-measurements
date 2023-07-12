pyinstaller --noconfirm --onefile --windowed --add-data "\Code Files"  "\Code Files\GUI.py"

xcopy /R /Y "connections.json" "dist"
pause