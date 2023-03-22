pyinstaller --noconfirm --onefile --windowed --add-data "C:/Users/2lick/OneDrive - post.bgu.ac.il/Documents/Final BSC Project/Code/Classes;Classes/"  "C:/Users/2lick/OneDrive - post.bgu.ac.il/Documents/Final BSC Project/Code/GUI.py"

xcopy /R /Y "connections.json" "dist"
pause