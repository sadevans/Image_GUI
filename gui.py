import sys
from PyQt6.QtWidgets import QMainWindow, QApplication,  QFileDialog, QMessageBox, QWidget, QGridLayout, QSizePolicy, QHBoxLayout, QLineEdit, QSlider, QPushButton, QLabel, QStackedWidget, QListWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPixmap, QPainter, QIcon, QFont
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from pathlib import Path
import os
import numpy as np


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.filenames_img = None
        self.filenames_mask = None

        self.setMinimumSize(400, 300)

        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(size_policy)

        self.setAutoFillBackground(True)
        screen = QApplication.primaryScreen()   # текущий экран
        screen_geometry = screen.geometry() # геометрия экрана
        self.setGeometry(screen_geometry)   # размер окна = размер экрана

        self.stacked_widget = QStackedWidget()
        self.select_folders_widget = QWidget()

        layout = QVBoxLayout()
        self.select_folders_widget.setLayout(layout)

        self.setCentralWidget(self.stacked_widget)
        self.show_select_folder()
        self.show()

    def show_photo_viewer(self, photo_viewer):
        self.stacked_widget.addWidget(photo_viewer)
        self.stacked_widget.setCurrentWidget(photo_viewer)

    def show_masks_checker(self, masks_checker):
        self.stacked_widget.addWidget(masks_checker)
        self.stacked_widget.setCurrentWidget(masks_checker)

    def show_select_folder(self):
        self.select_folders_widget = SelectFolders(self)
        self.stacked_widget.addWidget(self.select_folders_widget)
        self.stacked_widget.setCurrentWidget(self.select_folders_widget)



class SelectFolders(QWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.path_denoised: str = None
        self.path_mask: str = None

        self.filenames_img = None
        self.filenames_mask = None
        self.filenames_img_ = None
        self.filenames_mask_ = None
        self.files_img = None
        self.files_mask = None
        self.miss_masks = None
        self.images_without_masks = None

        self.all_have_masks = True
        self.other_ext = False
        self.no_images = False

        self.main_window.setWindowTitle('Select Folders')

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(-50, -50, -50, -50)
        self.layout.setVerticalSpacing(-10)

        instruction_label = QLabel('Выберите пути к папкам с изображениями')
        instruction_label.setFont(QFont('Montserrat', 14))  # Устанавливаем шрифт
        self.layout.addWidget(instruction_label, 0, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignHCenter)
        

        # directory wirh images selection
        dir_btn1 = QPushButton('Browse')
        dir_btn1.setObjectName('Btn')
        dir_btn1.clicked.connect(self.open_dir_dialog)
        self.dir_name_edit1 = QLineEdit()
        self.dir_name_edit1.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        den_label = QLabel('Denoised images directory:')
        den_label.setFont(QFont('Montserrat', 14))
        self.layout.addWidget(den_label, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.dir_name_edit1, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(dir_btn1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        # directory with masks selection
        dir_btn2 = QPushButton('Browse')
        dir_btn2.setObjectName('Btn')
        dir_btn2.clicked.connect(self.open_dir_dialog2)
        self.dir_name_edit2 = QLineEdit()

        mask_label = QLabel('Mask images directory:')
        mask_label.setFont(QFont('Montserrat', 14))
        self.layout.addWidget(mask_label, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.dir_name_edit2, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(dir_btn2, 2, 2, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        # creating submit button
        submit_btn = QPushButton('Submit paths')
        submit_btn.setObjectName('submitBtn')
        submit_btn.clicked.connect(self.check_masks)
        self.layout.addWidget(submit_btn, 2, 2, alignment=Qt.AlignmentFlag.AlignCenter)  # Добавляем кнопку подтверждения путей


    def check_masks(self):
        if self.path_denoised is None or self.path_mask is None:
            msg = QMessageBox()
            msg.setWindowTitle("Предупреждение")
            msg.setText("Пожалуйста, выберите папку и повторите ввод.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

        else:
            self.get_images()
            if self.no_images:
                msg = QMessageBox()
                msg.setWindowTitle("Предупреждение")
                msg.setText("В выбранной папке отсутствуют файлы изображений.\nПожалуйста, выберете корректную папку")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                self.no_images = False
            else:
                if self.all_have_masks:
                    self.OpenPhotoViewer()
                else:
                    self.OpenCheckMasks()


    def get_images(self):
        self.filenames_img = os.listdir(self.path_denoised)
        self.filenames_mask = os.listdir(self.path_mask)

        self.img_ext = np.unique([file[-4:] for file in self.filenames_img])
        self.mask_ext = np.unique([file[-4:] for file in self.filenames_mask])

        file_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff'}

        if len(set(self.img_ext).intersection(file_extensions)) != 0 and len(set(self.mask_ext).intersection(file_extensions)) != 0:

            self.filenames_img_ = [file for file in self.filenames_img if file[-4:] in file_extensions]
            self.filenames_mask_ = [file for file in self.filenames_mask if file[-4:] in file_extensions]

            self.filenames_img_.sort()
            self.filenames_mask_.sort()

            self.filenames_img = None
            self.filenames_mask = None

            self.files_img = [file[:-4] for file in self.filenames_img_] # имена
            self.files_mask = [file[:-4] for file in self.filenames_mask_] # имена

            if self.files_img != self.files_mask:

                self.miss_masks = list(set(self.files_img) - set(self.files_mask))
                self.images_without_masks = [file for file in self.filenames_img_ if file[:-4] in self.miss_masks]
                self.all_have_masks = False
        else:
            self.no_images = True
    
    
    def OpenPhotoViewer(self):
        self.photo_viewer = PhotoViewer(self.main_window, self.path_denoised, self.path_mask, self.filenames_img_, self.filenames_mask_)
        self.main_window.show_photo_viewer(self.photo_viewer)


    def OpenCheckMasks(self):
        self.masks_checker = CheckMasks(self.main_window, self.path_denoised, self.path_mask, self.filenames_img_, self.filenames_mask_, self.images_without_masks)
        self.main_window.show_masks_checker(self.masks_checker)
        

    def open_dir_dialog(self):
        dir_name1 = QFileDialog.getExistingDirectory(self, "Select a denoised images directory")
        if dir_name1:
            path_denoised = Path(dir_name1)
            self.dir_name_edit1.setText(str(path_denoised))
            self.path_denoised = str(path_denoised)


    def open_dir_dialog2(self):
        dir_name2 = QFileDialog.getExistingDirectory(self, "Select a mask directory")
        if dir_name2:
            path_mask = Path(dir_name2)
            self.dir_name_edit2.setText(str(path_mask))
            self.path_mask = str(path_mask)


class PhotoViewer(QWidget):
    def __init__(self, main_window, path_denoised, path_mask, filenames_img, filenames_mask):
        super().__init__()

        self.main_window = main_window

        self.path_denoised = path_denoised
        self.path_mask = path_mask

        self.filenames_img = filenames_img
        self.filenames_mask = filenames_mask
        
        self.current_img_index = 0

        self.current_opacity = 20 # начальное значение = 20 (0.2 * 100)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        image_layout = QHBoxLayout()

        self.prev_button = QPushButton(QIcon.fromTheme("go-previous"), "<", self)
        self.prev_button.setObjectName('Btn')
        self.prev_button.clicked.connect(self.swipe_left)
        self.next_button = QPushButton(QIcon.fromTheme("go-next"), ">", self)
        self.next_button.setObjectName('Btn')
        self.next_button.clicked.connect(self.swipe_right)


        bottom_layout = QHBoxLayout()
        go_back_btn = QPushButton('Go back')
        go_back_btn.setObjectName('submitBtn')
        go_back_btn.clicked.connect(self.OpenSelectFolders)
        bottom_layout.addWidget(go_back_btn)

        image_layout.addWidget(self.prev_button)

        self.img_label = QLabel()
        self.img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.opacity_slider.setValue(self.current_opacity)

        bottom_layout.addWidget(self.opacity_slider)

        self.opacity_slider.valueChanged.connect(self.update_opacity)

        image_layout.addWidget(self.img_label)
        image_layout.addWidget(self.next_button)

        self.layout.addLayout(image_layout)
        self.layout.addLayout(bottom_layout)

        self.show_images(self.current_img_index)



    def update_opacity(self):
        self.current_opacity = self.opacity_slider.value()  # преобразование значения в диапазоне [0, 100] в [0.0, 1.0]
        self.show_images(self.current_img_index)


    def OpenSelectFolders(self):
        self.main_window.show_select_folder()


    def show_images(self, index):
        if 0 <= index < len(self.filenames_img):
            img_path = os.path.join(self.path_denoised, self.filenames_img[index])
            mask_path = os.path.join(self.path_mask, self.filenames_mask[index])

            img = QPixmap(img_path)
            mask = QPixmap(mask_path)

            painter = QPainter(img)
            painter.setOpacity(self.current_opacity  / 100.0)
            painter.drawPixmap(0, 0, mask)

            painter.end()

            self.img_label.setPixmap(img)
            
            self.img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.main_window.setWindowTitle(self.filenames_img[index])

    
    def swipe_left(self):
        if self.current_img_index > 0:
            self.current_img_index -= 1
            self.show_images(self.current_img_index)
        elif self.current_img_index == 0:
            self.current_img_index = len(self.filenames_img) - 1
            self.show_images(self.current_img_index)


    def swipe_right(self):
        if self.current_img_index < len(self.filenames_img) - 1:
            self.current_img_index += 1
            self.show_images(self.current_img_index)
        elif self.current_img_index == len(self.filenames_img) - 1:
            self.current_img_index = 0
            self.show_images(self.current_img_index)


class CheckMasks(QWidget):
    def __init__(self, main_window, path_denoised, path_mask, filenames_img, filenames_mask, images_without_masks):
        super().__init__()
        
        self.main_window = main_window
        self.path_denoised = path_denoised
        self.path_mask = path_mask

        self.filenames_img = filenames_img
        self.filenames_mask = filenames_mask
        self.images_without_masks = images_without_masks

        self.new_filenames_img = None
        self.new_filenames_mask = None
        
        self.current_img_index = 0

        self.main_window.setWindowTitle("Some images don't have masks")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)


        instruction_label =QLabel(f'Всего изображений {len(self.filenames_img)}\nИзображений без масок {len(self.images_without_masks)}\n')
        instruction_label.setFont(QFont('Montserrat', 16))  # Устанавливаем шрифт
        
        self.layout.addWidget(instruction_label, alignment=Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignTop)
        

        images_without_masks_list = QListWidget()

        images_without_masks_list.setFixedHeight(700)
        self.layout.addWidget(images_without_masks_list, alignment=Qt.AlignmentFlag.AlignHCenter)
        images_without_masks_list.addItems(file for file in self.images_without_masks)
        
        button_layout = QHBoxLayout()

        go_back_btn = QPushButton('Go back')
        go_back_btn.setObjectName('submitBtn')
        go_back_btn.clicked.connect(self.OpenSelectFolders)
        button_layout.addWidget(go_back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        continue_btn = QPushButton('Ok, continue')
        continue_btn.setObjectName('submitBtn')
        continue_btn.clicked.connect(self.check)
        button_layout.addWidget(continue_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.layout.addLayout(button_layout)


    def OpenSelectFolders(self):
        self.main_window.show_select_folder()


    def check(self):
        if len(self.filenames_img) == len(self.images_without_masks):
            msg = QMessageBox()
            msg.setWindowTitle("Предупреждение")
            msg.setText("Нет изображений с масками.\nПожалуйста, выберите папки заново.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

        else:
            self.OpenPhotoViewer()
        

    def OpenPhotoViewer(self):
        self.new_filenames_img = list(set(self.filenames_img) - set(self.images_without_masks))
        self.new_filenames_mask = list(set(self.filenames_mask) - set(self.images_without_masks))
        self.photo_viewer = PhotoViewer(self.main_window, self.path_denoised, self.path_mask, self.new_filenames_img, self.new_filenames_mask)
        self.main_window.show_photo_viewer(self.photo_viewer)
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(open('style.css').read())
    window = MainWindow()
    sys.exit(app.exec())