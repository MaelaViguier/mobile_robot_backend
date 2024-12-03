import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QFileDialog
from PyQt5.QtGui import QPixmap

class ImageAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analyseur d'image")
        self.setGeometry(100, 100, 600, 400)

        self.image_label = QLabel(self)
        self.image_label.setGeometry(50, 50, 500, 250)

        self.load_button = QPushButton('Charger une image', self)
        self.load_button.setGeometry(50, 320, 150, 30)
        self.load_button.clicked.connect(self.load_image)

        self.analyze_button = QPushButton('Analyser', self)
        self.analyze_button.setGeometry(250, 320, 150, 30)
        self.analyze_button.clicked.connect(self.analyze_image)

        self.result_label = QLabel(self)
        self.result_label.setGeometry(50, 360, 500, 30)

        self.image_path = ""

    def load_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self,"Choisir une image", "","All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp)", options=options)
        if file_name:
            self.image_path = file_name
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(500, 250))

    def analyze_image(self):
        if self.image_path:
            # Charger l'image avec OpenCV
            image = cv2.imread(self.image_path)

            # Convertir l'image de BGR à HSV
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Trouver les valeurs minimales et maximales de RVB
            min_rgb = np.min(image, axis=(0, 1))
            max_rgb = np.max(image, axis=(0, 1))

            # Trouver les valeurs minimales et maximales de HSV
            min_hsv = np.min(hsv_image, axis=(0, 1))
            max_hsv = np.max(hsv_image, axis=(0, 1))

            # Afficher les résultats
            result_text = f"Valeurs min et max de RVB : {min_rgb} - {max_rgb}\n"
            result_text += f"Valeurs min et max de HSV : {min_hsv} - {max_hsv}"
            self.result_label.setText(result_text)
        else:
            self.result_label.setText("Veuillez charger une image d'abord.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageAnalyzer()
    window.show()
    sys.exit(app.exec_())
