import sys
from PyQt5.QtCore import QThread, QObject, pyqtSignal

class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        # Do some work here...
        self.finished.emit()

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.thread = QThread()
        self.worker = Worker()

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

app = QApplication(sys.argv)
window = MyWindow()
window.show()
sys.exit(app.exec_())
