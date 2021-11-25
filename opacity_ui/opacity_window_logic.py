import os
import cv2
import nibabel as nib
from scipy.ndimage import rotate
import numpy as np
from PySide6.QtWidgets import QMainWindow, QSlider
from PySide6.QtGui import QPixmap, QImage
from opacity_ui.opacity_ui import Ui_MainWindow
from opacity_ui.utils import opacity_change3
# pyside6-uic mainwindow.ui > ui_mainwindow.py


class OpacityWindow(QMainWindow):
    def __init__(self, args):
        super(OpacityWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.args = args

        # load image
        self.image_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'images'))

        self.image_1 = None
        self.image_2 = None
        self.image_3 = None

        self.load_images()
        self.shape_original = self.image_1.shape
        self.images_original = (self.image_1, self.image_2, self.image_3)

        # configure sliders
        self.configure_sliders()

        # configure buttons
        self.ui.pushButton.clicked.connect(self.axial)
        self.ui.pushButton_2.clicked.connect(self.sagittal)
        self.ui.pushButton_3.clicked.connect(self.coronal)

        # create intial pixmap
        self.pixmap = self.convert_np_to_pixmap(self.image_1[:, :, 0])

        self.ui.label.setPixmap(self.pixmap)

    def load_images(self):
        path_one = self.args.p1
        path_two = self.args.p2
        path_three = self.args.p3

        self.image_1 = nib.load(path_one)
        self.image_1 = self.image_1.get_fdata()
        self.image_1 = np.asarray(self.image_1)
        self.image_1 = rotate(self.image_1, 90)

        self.image_2 = nib.load(path_two)
        self.image_2 = self.image_2.get_fdata()
        self.image_2 = np.asarray(self.image_2)
        self.image_2 = rotate(self.image_2, 90)

        self.image_3 = nib.load(path_three)
        self.image_3 = self.image_3.get_fdata()
        self.image_3 = np.asarray(self.image_3)
        self.image_3 = rotate(self.image_3, 90)

    def configure_sliders(self):
        # slider 1 - opacity
        self.ui.verticalSlider.setMinimum(0)
        self.ui.verticalSlider.setMaximum(1000)
        self.ui.verticalSlider.setTickInterval(100)
        self.ui.verticalSlider.setTickPosition(QSlider.TicksLeft)

        # slider 2 - opacity
        self.ui.verticalSlider_2.setMinimum(0)
        self.ui.verticalSlider_2.setMaximum(1000)
        self.ui.verticalSlider_2.setTickInterval(100)
        self.ui.verticalSlider_2.setTickPosition(QSlider.TicksLeft)

        # slider 3 - slice
        shape = self.image_1.shape
        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(shape[2])
        self.ui.horizontalSlider.setTickInterval(int(self.shape_original[2]/10))
        self.ui.horizontalSlider.setTickPosition(QSlider.TicksBelow)
        self.ui.horizontalSlider.setSliderPosition(int(shape[2]/2))

        # slider 4 - threshold
        self.ui.horizontalSlider_2.setMaximum(0)
        self.ui.horizontalSlider_2.setMaximum(255)
        self.ui.horizontalSlider_2.setTickInterval(25)
        self.ui.horizontalSlider_2.setTickPosition(QSlider.TicksBelow)

        # whenever the sliders change, execute the opacity change
        self.ui.verticalSlider.valueChanged.connect(self.display_update)
        self.ui.verticalSlider_2.valueChanged.connect(self.display_update)
        self.ui.horizontalSlider.valueChanged.connect(self.display_update)
        self.ui.horizontalSlider_2.valueChanged.connect(self.display_update)

    def axial(self):
        self.image_1 = self.images_original[0]
        self.image_2 = self.images_original[1]
        self.image_3 = self.images_original[2]

        # update slice slider range
        self.ui.horizontalSlider.setMaximum(self.shape_original[2])
        self.ui.horizontalSlider.setTickInterval(int(self.shape_original[2] / 10))

        self.display_update()

    def sagittal(self):  # not (0,1), (0,2)
        self.image_1 = np.rot90(np.rot90(self.images_original[0], 1, (1, 2)), 3)
        self.image_2 = np.rot90(np.rot90(self.images_original[1], 1, (1, 2)), 3)
        self.image_3 = np.rot90(np.rot90(self.images_original[2], 1, (1, 2)), 3)

        # update slice slider range
        shape = self.image_1.shape
        self.ui.horizontalSlider.setMaximum(shape[2])
        self.ui.horizontalSlider.setTickInterval(int(shape[2] / 10))

        self.display_update()

    def coronal(self):
        self.image_1 = np.rot90(np.rot90(np.transpose(self.images_original[0])))
        self.image_2 = np.rot90(np.rot90(np.transpose(self.images_original[1])))
        self.image_3 = np.rot90(np.rot90(np.transpose(self.images_original[2])))

        # update slice slider range
        self.ui.horizontalSlider.setMaximum(self.shape_original[2])
        self.ui.horizontalSlider.setTickInterval(int(self.shape_original[2] / 10))

        self.display_update()

    def convert_np_to_pixmap(self, numpy_array):
        # convert to cv2
        frame = cv2.cvtColor(np.uint8(numpy_array), cv2.COLOR_GRAY2RGB)

        # convert to qimage
        h, w = numpy_array.shape[:2]
        bytes_per_line = 3 * w
        qimage = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # convert to pixmap
        pixmap = QPixmap.fromImage(qimage)

        return pixmap

    def display_update(self):
        op1 = self.ui.verticalSlider.value() / 1000  # maximum value of slider
        op2 = self.ui.verticalSlider_2.value() / 1000
        idx = self.ui.horizontalSlider.value()  # slice index
        threshold = self.ui.horizontalSlider_2.value()

        blended = opacity_change3(self.image_1[:, :, idx], self.image_2[:, :, idx], self.image_3[:, :, idx], op1, op2, threshold)
        self.pixmap = self.convert_np_to_pixmap(blended)
        self.ui.label.setPixmap(self.pixmap)
