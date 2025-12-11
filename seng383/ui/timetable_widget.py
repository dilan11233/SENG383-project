from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PySide6.QtCore import Qt
from ui.styles import COLOR_THEORY, COLOR_LAB, COLOR_CONFLICT, COLOR_EMPTY

class TimetableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setRowCount(8)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        )
        self.table.setVerticalHeaderLabels([f"{i+1}. Saat" for i in range(8)])
        self.layout.addWidget(self.table)

    def set_lesson(self, day_index, hour_index, lesson_name, lesson_type="theory"):
        """
        Belirli gün ve saat için ders adı ekler.
        lesson_type: "theory", "lab", "conflict", "empty"
        """
        item = QTableWidgetItem(lesson_name)
        item.setTextAlignment(Qt.AlignCenter)

        # Renk atama
        if lesson_type == "theory":
            item.setBackground(COLOR_THEORY)
        elif lesson_type == "lab":
            item.setBackground(COLOR_LAB)
        elif lesson_type == "conflict":
            item.setBackground(COLOR_CONFLICT)
        elif lesson_type == "empty":
            item.setBackground(COLOR_EMPTY)

        self.table.setItem(hour_index, day_index, item)

    def clear_timetable(self):
        self.table.clearContents()

    def load_timetable(self, timetable_data: dict):
        """
        timetable_data: {day_index: {hour_index: (lesson_name, lesson_type)}}
        """
        self.clear_timetable()
        for day, hours in timetable_data.items():
            for hour, (lesson, ltype) in hours.items():
                self.set_lesson(day, hour, lesson, ltype)
