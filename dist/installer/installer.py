import os
import sys
import requests
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QCheckBox, QStackedLayout, QHBoxLayout, QGroupBox, QComboBox, QProgressBar, QLineEdit, QMessageBox, QFileDialog, QVBoxLayout
from PyQt6.QtGui import QPixmap, QIcon, QImage
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QByteArray, QFile, QTextStream , QObject, pyqtSignal, pyqtSlot
import zipfile
import shutil
import tempfile
import win32com.client
import logging
import re
import winreg as reg
import base64
from image_base64 import image_data
from icons import styledark_rc
from stylesheet import Style

class QtUi(QMainWindow, Style):
    def __init__(self):
        super().__init__()
        self.logic = Logic(self)
        self.setWindowTitle('Installer') # Window name
        self.setCentralWidget(QWidget(self))  # Set a central widget
        self.layout = QStackedLayout(self.centralWidget())  # Set the layout on the central widget
        self.setFixedSize(700, 550) # Fixed window size
        self.ui()  # Init UI

    # self.header
    def Header(self):
        # Header Layout
        self.headerLayout = QVBoxLayout()
        self.headerLayout.setContentsMargins(0, 20, 0, 0)
        # Icon Widget
        CEicon = QLabel()
        image_bytes = base64.b64decode(image_data)
        image = QImage.fromData(QByteArray(image_bytes))
        pixmap = QPixmap.fromImage(image)
        ## Scale the pixmap
        scaledPixmap = pixmap.scaled(180, 180,)
        CEicon.setPixmap(scaledPixmap)
        # Text Widget
        CElabel = QLabel("<b>Citra-Enhanced Installer")
        # Set Widgets
        self.headerLayout.addWidget(CEicon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.headerLayout.addWidget(CElabel, alignment=Qt.AlignmentFlag.AlignCenter)
        return self.headerLayout
    
    # Widgets
    def ui(self):
        # Welcome page
        self.welcomePage = QWidget()
        ## Layout and gorup
        welcomerLayout = QVBoxLayout()
        welcomerGroup = QGroupBox("")
        welcomerGroupLayout = QVBoxLayout()
        buttonsLayout = QHBoxLayout()
        welcomerGroup.setLayout(welcomerGroupLayout)
        self.welcomePage.setLayout(welcomerLayout) # Set the welcomepage layout
        ## Widgets
        welcomerLabel = QLabel('<b>Citra Enhanced is a fork of Citra which aims to incrase')
        welcomerLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.installButton = QPushButton('Install')
        self.installButton.clicked.connect(self.logic.clickfunction)
        self.updateButton = QPushButton('Update')
        self.updateButton.clicked.connect(self.logic.clickfunction)
        self.uninstallButton = QPushButton('Uninstall')
        self.uninstallButton.clicked.connect(self.logic.clickfunction)
        ## Add widgets / layouts
        welcomerLayout.addLayout(self.Header()) 
        welcomerLayout.addWidget(welcomerGroup)
        welcomerGroupLayout.addWidget(welcomerLabel)
        buttonsLayout.addWidget(self.installButton)
        buttonsLayout.addWidget(self.updateButton)
        buttonsLayout.addWidget(self.uninstallButton)
        welcomerLayout.addLayout(buttonsLayout)
        ## Add the welcome page to the layout
        self.layout.addWidget(self.welcomePage)


        # Install page
        self.installPage = QWidget()
        ## Layout and gorup
        installLayout = QVBoxLayout()
        checkboxLayout = QVBoxLayout()
        checkboxGroup = QGroupBox("Do you want to create shortcuts?") # Checkboxes
        checkboxGroup.setLayout(checkboxLayout) # Set the layout of Checkboxes
        pathSelectorLayout = QHBoxLayout() # Browse widget layout
        self.installPage.setLayout(installLayout) # Set the installpage layout
        ## Widgets
        InstalOpt = QLabel('<b>Installation Options')
        InstalOpt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.installationSourceComboBox = QComboBox() # Dropdown menu
        self.installationSourceComboBox.addItem("Latest Release") 
        self.installationSourceComboBox.addItem("Latest Nightly") 
        self.desktopShortcutCheckbox = QCheckBox("Create a desktop shortcut") # Checkboxes
        self.startMenuShortcutCheckbox = QCheckBox("Create a start menu shortcut")
        self.installationPathLineEdit = QLineEdit(os.path.join(os.environ['LOCALAPPDATA'], 'Citra Enhanced')) # Browse for installation path widget
        self.browseButton = QPushButton("Browse")
        self.browseButton.clicked.connect(self.logic.browseForInstallationPath)
        self.installCitraButton = QPushButton('Install') # Install button
        self.installCitraButton.clicked.connect(self.logic.clickfunction)
        ## Add widgets / layouts
        installLayout.addLayout(self.Header()) ### Icon self.header
        installLayout.addWidget(InstalOpt) ### Instalation Option Label
        installLayout.addWidget(self.installationSourceComboBox) ## Install Sorce Widget
        pathSelectorLayout.addWidget(self.installationPathLineEdit) ## Browse Widget
        pathSelectorLayout.addWidget(self.browseButton)
        installLayout.addLayout(pathSelectorLayout)
        checkboxLayout.addWidget(self.desktopShortcutCheckbox) # Checkboxes
        checkboxLayout.addWidget(self.startMenuShortcutCheckbox)
        installLayout.addWidget(checkboxGroup)
        installLayout.addWidget(self.installCitraButton)
        ## Add the install page to the layout
        self.layout.addWidget(self.installPage)


        # Progress bar page
        self.progressBarPage = QWidget()
        ## Layout and groups
        progressBarLayout = QVBoxLayout()
        self.progressBarPage.setLayout(progressBarLayout)
        ## Widgets
        self.downloadProgressBar = QProgressBar()
        self.downloadProgressBar.setRange(0, 100)  # Progress bar Widgets
        self.extractionProgressBar = QProgressBar()
        self.extractionProgressBar.setRange(0, 100)    
        labeldown = QLabel("Downloading Citra Enhanced:")
        labelext = QLabel("Extracting Citra-Enhanced:")
        ## Add widgets / layouts
        progressBarLayout.addLayout(self.Header())  # Add the icon self.header
        progressBarLayout.addWidget(labeldown)
        progressBarLayout.addWidget(self.downloadProgressBar)
        progressBarLayout.addWidget(labelext)
        progressBarLayout.addWidget(self.extractionProgressBar)
        # Add the progress bar page to the layout
        self.layout.addWidget(self.progressBarPage)


        # Finish page
        self.finishPage = QWidget()
        ## Layout and groups
        finishLayout = QVBoxLayout()
        self.finishPage.setLayout(finishLayout)
        ## Widgets
        finishLabel = QLabel("<b>Installation Complete!")
        finishLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the text horizontally
        finishButton = QPushButton("Finish")
        finishButton.clicked.connect(self.close)
        ## Add widgets / layouts
        finishLayout.addLayout(self.Header())  # Add the icon self.header
        finishLayout.addWidget(finishLabel)
        finishLayout.addWidget(finishButton)
        # Add the progress bar page to the layout
        self.layout.addWidget(self.finishPage)   
    
    def load_stylesheet(app):
            app.setStyleSheet(Style.dark_stylesheet)

class Logic:
# Every method here is due to change , the update and uninstall buttons do nothing for now althouhg the install ubtton works    
    def __init__(self, qtui):
        self.qtui = qtui

    def clickfunction(self):
        button = qtui.sender()
        if button is qtui.installButton:
            qtui.layout.setCurrentIndex(1)
        elif button is qtui.updateButton:
            print('Placeholder')
        elif button is qtui.uninstallButton:
            print('Placeholder')
        if button is qtui.installCitraButton:
            qtui.layout.setCurrentIndex(2)
            self.install()
        
    def browseForInstallationPath(self):
        selectedDirectory = QFileDialog.getExistingDirectory(self.qtui, "Select Installation Directory", self.qtui.installationPathLineEdit.text())
        if selectedDirectory:  # Check if a directory was selected
            # Append "Citra-Enhanced" to the selected directory path
            CitraEnhancedDirectory = os.path.join(selectedDirectory, 'Citra-Enhanced')
            qtui.installationPathLineEdit.setText(CitraEnhancedDirectory)

    def install(self):
        selection = qtui.installationSourceComboBox.currentText()
        if selection == "Latest Nightly":
            url = "https://nightly.link/Gamer64ytb/Citra-Enhanced/workflows/build/master/windows-msvc.zip"
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                print("Download successful, proceeding with installation.")
            else:
                QMessageBox.critical(self, "Error", "Failed to download. HTTP status code: {response.status_code}.")
                return
        elif selection == "Latest Release":
            url = Logic.get_latest_release_url(self)
            if not url:
                QMessageBox.critical(self, "Error", "Repo URL was not found.")
                return
        temp_file = tempfile.NamedTemporaryFile(delete=False).name
        self.installationPath = self.qtui.installationPathLineEdit.text()
        os.makedirs(self.installationPath, exist_ok=True)
        self.start_download (url, temp_file)

    def print_finished(self):
        print("Thread has finished.")

    
    def start_download(self, url, temp_file):
        self.download_thread = QThread()  # Create a QThread
        self.download_worker = DownloadWorker(url, temp_file)  # Create the worker
        self.download_worker.moveToThread(self.download_thread)  # Move the worker to the thread
        self.download_thread.started.connect(self.download_worker.do_download)  # Start the worker when the thread starts
        self.download_worker.progress.connect(self.qtui.downloadProgressBar.setValue)  # Connect the progress signal
        self.download_thread.start()  # Start the thread

        self.download_worker.finished.connect(lambda: self.extract_zip(temp_file, self.installationPath))

    def finish_download(self, temp_file):
        self.download_worker.deleteLater()
        print ("Download finished.")
        self.extract_zip(temp_file, self.installationPath)
            


    def get_latest_release_url(self):
        try:
            api_url = "https://api.github.com/repos/kleidis/Citra-Enhanced/releases"
            response = requests.get(api_url)
            if response.status_code != 200:
                QMessageBox.critical(self, "Error", "Failed to fetch releases from GitHub.")
                return None

            releases = response.json()
            for release in releases:
                assets = release.get('assets', [])
                for asset in assets:
                    if "windows-msvc" in asset['name']:
                        return asset['browser_download_url']
            QMessageBox.critical(qtui, "Error", "No suitable release found.")
            return None
        except Exception as e:
            QMessageBox.critical(qtui, "Exception", f"An error occurred: {e}")
            return None

    def clear_directory(self, directory):
        """
        Removes all files and directories in the specified directory.

        :param directory: Path to the directory to clear.
        """
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                logging.error(f'Failed to delete {item_path}. Reason: {e}')

    def extract_zip(self, temp_file, extract_to):
        print (f"Extracting {temp_file} to {extract_to}.")
        try:
            # Clear the target directory before extracting new files
            if os.path.exists(extract_to):
                self.clear_directory(extract_to)

            # Rename the temporary file to have a .zip extension
            zip_file_path = temp_file + '.zip'
            os.rename(temp_file, zip_file_path)

            # Temporary extraction folder
            temp_extract_folder = tempfile.mkdtemp()

            # Extract the main zip file to a temporary folder
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_folder)
                logging.info(f"Main zip extraction completed to temporary folder.")

            # Find the nested zip file or the main directory
            nested_zip_path = None
            for root, dirs, files in os.walk(temp_extract_folder):
                for file in files:
                    if file.endswith('.zip'):
                        nested_zip_path = os.path.join(root, file)
                        break
                if nested_zip_path:  # Stop searching if the nested zip is found
                    break

            if nested_zip_path:
                with zipfile.ZipFile(nested_zip_path, 'r') as nested_zip_ref:
                    nested_zip_ref.extractall(extract_to)
                    logging.info(f"Nested zip extraction completed to {extract_to}.")
            else:
                # If no nested zip, move the contents from the temp folder to the desired location
                for item in os.listdir(temp_extract_folder):
                    s = os.path.join(temp_extract_folder, item)
                    d = os.path.join(extract_to, item)
                    if os.path.isdir(s):
                        shutil.move(s, d)
                    else:
                        shutil.copy2(s, d)
                logging.info("Moved extracted files to the desired location.")

            # After extracting all files
            nested_dir_name = None
            for item in os.listdir(extract_to):
                if os.path.isdir(os.path.join(extract_to, item)) and 'windows-msvc' in item:
                    nested_dir_name = item
                    break

            if nested_dir_name:
                nested_dir_path = os.path.join(extract_to, nested_dir_name)
                for item in os.listdir(nested_dir_path):
                    s = os.path.join(nested_dir_path, item)
                    d = os.path.join(extract_to, item)
                    if os.path.isdir(s):
                        shutil.move(s, d)
                    else:
                        shutil.copy2(s, d)
                # Remove the now-empty nested directory
                shutil.rmtree(nested_dir_path)

            # Set the progress bar to 100% and call installation_complete
            qtui.extractionProgressBar.setValue(100)
            executable_path = os.path.normpath(os.path.join(qtui.installationPathLineEdit.text(), 'citra-qt.exe'))
#            self.add_to_programs_list(executable_path)
            self.installation_complete()
        except Exception as e:
            logging.error(f"Failed to extract zip file: {e}. File: {temp_file}")

    def installation_complete(self):
        executable_path = os.path.normpath(os.path.join(qtui.installationPathLineEdit.text(), 'citra-qt.exe'))
        if qtui.desktopShortcutCheckbox.isChecked():
            self.create_desktop_shortcut(executable_path)
        if qtui.startMenuShortcutCheckbox.isChecked():
            self.create_start_menu_shortcut(executable_path)
        qtui.layout.setCurrentIndex(qtui.layout.indexOf(qtui.finishPage))  # Switch to finish page

# HEAVILY INCOMPLETE , DO NOT USE
#    def add_to_programs_list(self, executable_path):
#        """
#        Add the application to the Windows Program list with the uninstall option.
#
#        :param executable_path: Path to the executable file of the application.
#        """
#        print("Adding to programs list...")
#        # Path to the uninstall key
#        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Citra-Enhanced"
#        # Uninstaller path
#        uninstaller_path = os.path.normpath(os.path.join(self.installationPathLineEdit.text(), 'uninstaller.exe'))
#        print(f"Uninstaller path: {uninstaller_path}")
#
#       # Attempt to open the key, create if it does not exist
#        try:
#            key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_WRITE)
#            print("Registry key exists, opened successfully.")
#        except FileNotFoundError:
#            key = reg.CreateKey(reg.HKEY_CURRENT_USER, key_path)
#            print("Registry key does not exist, created successfully.")
#
#        # Set values within the key
#        with key:
#            reg.SetValueEx(key, "DisplayName", 0, reg.REG_SZ, "Citra-Enhanced")
#            reg.SetValueEx(key, "UninstallString", 0, reg.REG_SZ, uninstaller_path)
#            reg.SetValueEx(key, "DisplayIcon", 0, reg.REG_SZ, executable_path)
#            reg.SetValueEx(key, "Publisher", 0, reg.REG_SZ, "Citra-Enhanced-Emu")
#            reg.SetValueEx(key, "URLInfoAbout", 0, reg.REG_SZ, "https://Citra-Enhanced-emu.github.io/")
#            print("Registry values set successfully.")
#
#        print("Added to programs list successfully.")

    def create_desktop_shortcut(self, target):
        desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        shortcut_path = os.path.join(desktop_path, 'Citra-Enhanced.lnk')
        self.create_shortcut(target, shortcut_path)

    def create_start_menu_shortcut(self, target):
        start_menu_path = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        shortcut_path = os.path.join(start_menu_path, 'Citra-Enhanced.lnk')
        self.create_shortcut(target, shortcut_path)


    def create_shortcut(self, target, shortcut_path, description="", arguments="", hotkey=""):
        # Verify the target exists
        if not os.path.exists(target):
            logging.error(f"Shortcut target does not exist: {target}")
            return

        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = target
            shortcut.WorkingDirectory = os.path.dirname(target)
            shortcut.Description = description
            shortcut.Arguments = arguments
            if hotkey:
                shortcut.Hotkey = hotkey
            shortcut.IconLocation = target  # You can customize this if needed
            shortcut.save()
            logging.info(f"Shortcut created successfully at {shortcut_path}")
        except Exception as e:
            logging.error(f"Failed to create shortcut: {e}")

class DownloadWorker(QThread):
    progress = pyqtSignal(int)

    def __init__(self, url, dest):
        super().__init__()
        self.url = url
        self.dest = dest

    @pyqtSlot()
    def do_download(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                print("The content-length of the response is zero.")
                return

            downloaded_size = 0
            with open(self.dest, 'wb') as file:
                for data in response.iter_content(1024):
                    downloaded_size += len(data)
                    file.write(data)
                    progress_percentage = (downloaded_size / total_size) * 100
                    self.progress.emit(int(progress_percentage))
            print(f"Download completed. File saved to {self.dest}")
            self.finished.emit()
        except Exception as e:
            print("Error doing download.")
            self.finished.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qtui = QtUi()
    logic = Logic(qtui)
    qtui.load_stylesheet()
    qtui.show()
    sys.exit(app.exec())



