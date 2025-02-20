from PyQt5.QtCore import QThread, pyqtSignal


class LabelUpdater(QThread):
    update_done = pyqtSignal(object)  # Signal to emit when the task is done
    update_failed = pyqtSignal(str)  # Signal to emit if the task fails

    def __init__(self, func, args=()):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            result = self.func(*self.args)
            self.update_done.emit(result)  # Emit the result when done
        except Exception as e:
            self.update_failed.emit(str(e))  # Emit the error if something fails
