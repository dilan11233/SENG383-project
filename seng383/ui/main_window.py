from PyQt5.QtWidgets import QMainWindow, QAction, QMenuBar, QVBoxLayout, QWidget
from ui.timetable_widget import TimetableWidget
from ui.inputs_widget import InputsWidget
from ui.report_dialog import ReportDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ders Programı Uygulaması")
        self.resize(800, 600)

        # Merkezi widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Timetable ve Inputs
        self.timetable = TimetableWidget()
        self.inputs = InputsWidget(self.timetable)

        layout.addWidget(self.inputs)
        layout.addWidget(self.timetable)

        # Menü
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        report_action = QAction("Rapor Al", self)
        report_action.triggered.connect(self.show_report)

        file_menu = menubar.addMenu("Dosya")
        file_menu.addAction(report_action)

    def show_report(self):
        dialog = ReportDialog(self.timetable)
        dialog.exec_()
