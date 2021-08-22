from PyQt5 import QtWidgets
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
import matplotlib

matplotlib.use('QT5Agg')

class MplCanvas(Canvas):
    def __init__(self, parent=None, width=12, height=2, dpi =100):
        self.fig = Figure(dpi = 60)
        self.fig.tight_layout()

        self.ax = self.fig.add_subplot()
        Canvas.__init__(self, self.fig)

class MplWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QtWidgets.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.canvas.fig.tight_layout()
        self.canvas.fig.subplots_adjust(0.01, 0.1, 0.98, 0.95)
        self.setLayout(self.vbl)