from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton

class InputsWidget(QWidget):
    def __init__(self, timetable_widget, parent=None):
        super().__init__(parent)
        self.timetable = timetable_widget

        layout = QHBoxLayout(self)

        # Gün seçimi
        self.day_combo = QComboBox()
        self.day_combo.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])

        # Saat seçimi
        self.hour_combo = QComboBox()
        self.hour_combo.addItems([f"{i+1}. Saat" for i in range(8)])

        # Ders adı
        self.lesson_input = QLineEdit()
        self.lesson_input.setPlaceholderText("Ders adı giriniz")

        # Ekle butonu
        self.add_button = QPushButton("Ekle")
        self.add_button.clicked.connect(self.add_lesson)

        layout.addWidget(self.day_combo)
        layout.addWidget(self.hour_combo)
        layout.addWidget(self.lesson_input)
        layout.addWidget(self.add_button)

    def add_lesson(self):
        day_index = self.day_combo.currentIndex()
        hour_index = self.hour_combo.currentIndex()
        lesson_name = self.lesson_input.text().strip()
        if lesson_name:
            self.timetable.set_lesson(day_index, hour_index, lesson_name)
            self.lesson_input.clear()
