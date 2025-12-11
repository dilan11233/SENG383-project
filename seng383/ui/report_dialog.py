from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

class ReportDialog(QDialog):
    def __init__(self, timetable_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ders Programı Raporu")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        close_button = QPushButton("Kapat")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.generate_report(timetable_widget)

    def generate_report(self, timetable_widget):
        report = ""
        for row in range(timetable_widget.table.rowCount()):
            for col in range(timetable_widget.table.columnCount()):
                item = timetable_widget.table.item(row, col)
                if item:
                    report += f"{timetable_widget.table.horizontalHeaderItem(col).text()} - {timetable_widget.table.verticalHeaderItem(row).text()}: {item.text()}\n"
        self.text_area.setText(report)
