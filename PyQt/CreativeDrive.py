import sys
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from pathlib import Path
from tqdm import tqdm
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import time

# background thread class
class UploadThread(QtCore.QThread):
    response_signal = QtCore.pyqtSignal(str)
    error_signal = QtCore.pyqtSignal(bool)
    update_signal = QtCore.pyqtSignal(list)
    time_signal = QtCore.pyqtSignal(str)

    def __init__(self, access_token, path, parent=None):
        super(UploadThread, self).__init__(parent)
        self.threadactive = True
        self.token = access_token
        self.filepath = path
        self.starTime = time.time()
        
    def run(self):
        while (self.threadactive):
            upload_url = "http://localhost:8000/api/upload/"
            fields = {'upload': open(self.filepath, 'rb')}
            path = Path(self.filepath)
            total_size = path.stat().st_size
            filename = path.name

            with tqdm(
                desc=filename,
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                with open(self.filepath, "rb") as f:
                    fields["upload"] = (filename, f)
                    e = MultipartEncoder(fields=fields)
                    #m = MultipartEncoderMonitor(
                    #    e, lambda monitor: bar.update(monitor.bytes_read - bar.n),
                    #)
                    m = MultipartEncoderMonitor(
                        e, lambda monitor: self.set_signals(monitor.bytes_read,total_size),
                    )
                    #headers = {"Content-Type": m.content_type}
                    key = "Bearer " + self.token
                    headers = {"Authorization": key, "Content-Type": m.content_type}
                    self.r = requests.post(upload_url, data=m, headers=headers)
                    self.response = self.r.json()
                    self.response_signal.emit(str(self.response))
                    #self.log_textedit.setText(str(response))
                    try:
                        id = self.response['id']
                        self.error_signal.emit(False)
                        self.threadactive = False
                    except KeyError:
                        self.error_signal.emit(True)
                        self.threadactive = False

    def set_signals(self, bytes_read, total_size):
        self.elapsedTime = time.time()-self.starTime
        self.remainingTime = abs(round(self.elapsedTime*(1-bytes_read/total_size),2))
        self.time_signal.emit(str(self.remainingTime) + " s")
        self.update_signal.emit([bytes_read, total_size])

    def stop(self):
        self.threadactive = False
        self.terminate()

class LoginWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(LoginWidget, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Login")
        self.user_lineedit = QtWidgets.QLineEdit()
        self.password_lineedit = QtWidgets.QLineEdit()
        self.password_lineedit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.log_textedit = QtWidgets.QTextBrowser()
        login_button = QtWidgets.QPushButton(
            text="Fazer login",
            clicked=self.login
        )
        hlay = QtWidgets.QHBoxLayout()
        lay = QtWidgets.QFormLayout(self)
        lay.addRow("Usuário:", self.user_lineedit)
        lay.addRow("Senha:", self.password_lineedit)
        lay.addRow(self.log_textedit)
        lay.addRow(login_button)

    @QtCore.pyqtSlot()
    def login(self):
        url = "http://localhost:8000/api/users/token/"
        data = {'username': self.user_lineedit.text(), 'password': self.password_lineedit.text()}
        r = requests.post(url, data=data)
        response = r.json()
        self.log_textedit.setText(str(response))
        try:
            access_token = response['access']
            QtWidgets.QMessageBox.information(self, "Login", "Login realizado com sucesso!")
            self.goMenuWidget(access_token)
        except KeyError:
            QtWidgets.QMessageBox.critical(self, "Erro", "Um erro ocorreu durante o login. Por favor tente novamente.")

    @QtCore.pyqtSlot()
    def goMenuWidget(self, token):
        self.window = MenuWidget(token)
        self.window.show()
        self.close()  

class MenuWidget(QtWidgets.QWidget):
    def __init__(self, token, parent=None):
        super(MenuWidget, self).__init__(parent)
        self.access_token = token
        self.init_ui()
        # Init QSystemTrayIcon
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
        show_action = QtWidgets.QAction("Maximizar", self)
        hide_action = QtWidgets.QAction("Minimizar", self)
        quit_action = QtWidgets.QAction("Sair", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(QtWidgets.qApp.quit)
        tray_menu = QtWidgets.QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def init_ui(self):
        self.setWindowTitle("CreativeDrive")
        self.filepath_lineedit = QtWidgets.QLineEdit()
        self.progressBar = QtWidgets.QProgressBar() # progress bar
        self.timeRemaining = QtWidgets.QLabel(self)
        self.time = 0
        self.timeRemaining.setText(str(self.time))
        self.select_button = QtWidgets.QPushButton(
            text="Escolher arquivo",
            clicked=self.select_file
        )
        self.name_lineedit = QtWidgets.QLineEdit()
        self.log_textedit = QtWidgets.QTextBrowser()
        upload_button = QtWidgets.QPushButton(
            text="Upload",
            clicked=self.upload_thread
        )
        cancelUpload_button = QtWidgets.QPushButton(
            text="Cancelar upload",
            clicked=self.cancel_upload
        )
        hlay = QtWidgets.QHBoxLayout()
        hlay.addWidget(self.filepath_lineedit)
        hlay.addWidget(self.select_button)
        lay = QtWidgets.QFormLayout(self)
        lay.addRow("Arquivo:", hlay)
        lay.addRow("Progresso: ", self.progressBar)
        lay.addRow("Tempo restante:", self.timeRemaining)
        lay.addRow(self.log_textedit)
        lay.addRow(upload_button)
        lay.addRow(cancelUpload_button)
        self.update()

    @QtCore.pyqtSlot()
    def select_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 
            "Abrir arquivo", 
            QtCore.QDir.currentPath(), 
        )
        if filename:
            self.filepath_lineedit.setText(filename)

    @QtCore.pyqtSlot()
    def upload_thread(self):
        self.filepath = self.filepath_lineedit.text()
        self.uploadThread = UploadThread(self.access_token, self.filepath)
        self.uploadThread.response_signal.connect(self.log_textedit.setText)
        self.uploadThread.error_signal.connect(lambda error: self.check_upload(error))
        self.uploadThread.update_signal.connect(lambda signals: self.updateProgressBar(signals[0], signals[1]))
        self.uploadThread.time_signal.connect(self.timeRemaining.setText)
        self.uploadThread.start()

    @QtCore.pyqtSlot()
    def updateProgressBar(self, bytesRead, totalSize):
        self.progressBar.setValue(int(100*bytesRead/totalSize))

    @QtCore.pyqtSlot()
    def cancel_upload(self):
        self.uploadThread.stop()
        QtWidgets.QMessageBox.information(self, "Upload cancelado", "Upload cancelado com sucesso!")  
        self.timeRemaining.setText(None)
        self.updateProgressBar(0, 1)

    @QtCore.pyqtSlot()
    def check_upload(self, error):
        if (error):
            QtWidgets.QMessageBox.critical(self, "Erro", "Um erro ocorreu durante o upload. Por favor tente novamente.")
        else:
            QtWidgets.QMessageBox.information(self, "Upload", "Upload realizado com sucesso!")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
                "CreativeDrive",
                "O programa foi minimizado para a trackbar",
                QtWidgets.QSystemTrayIcon.Information,
                2000
            )

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = LoginWidget()
    w.show()
    sys.exit(app.exec_())
