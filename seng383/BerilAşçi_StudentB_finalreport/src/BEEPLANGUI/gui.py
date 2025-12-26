"""PyQt6 GUI for BeePlan scheduling system."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox, QDialog,
    QTextEdit, QFileDialog, QHeaderView, QToolTip, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QBrush, QFont
from typing import List, Dict, Optional
from models import Course, TimeSlot, Conflict
from algorithm import ScheduleAlgorithm
from utils import export_schedule_to_json


class ReportDialog(QDialog):
    """Dialog to display scheduling report."""
    
    def __init__(self, unscheduled_courses: List[Course], conflicts: List[Conflict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scheduling Report")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Unscheduled courses
        if unscheduled_courses:
            unscheduled_label = QLabel("<b>Unscheduled Courses:</b>")
            layout.addWidget(unscheduled_label)
            
            unscheduled_text = QTextEdit()
            unscheduled_text.setReadOnly(True)
            unscheduled_text.setMaximumHeight(150)
            text = "\n".join([f"• {c.code}: {c.name}" for c in unscheduled_courses])
            unscheduled_text.setPlainText(text)
            layout.addWidget(unscheduled_text)
        
        # Conflicts
        if conflicts:
            conflicts_label = QLabel("<b>Conflicts:</b>")
            layout.addWidget(conflicts_label)
            
            conflicts_text = QTextEdit()
            conflicts_text.setReadOnly(True)
            text = "\n".join([f"• {c.message}" for c in conflicts])
            conflicts_text.setPlainText(text)
            layout.addWidget(conflicts_text)
        
        # Success message
        if not unscheduled_courses and not conflicts:
            success_label = QLabel("<b style='color: green;'>✓ All courses scheduled successfully!</b>")
            layout.addWidget(success_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class BeePlanMainWindow(QMainWindow):
    """Main window for BeePlan application."""
    
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    HOURS = [9, 10, 11, 12, 13, 14, 15, 16]
    MINUTE = 20
    
    # Color scheme for different years
    YEAR_COLORS = {
        1: QColor(173, 216, 230),  # Light blue
        2: QColor(144, 238, 144),  # Light green
        3: QColor(255, 218, 185),  # Peach
        4: QColor(221, 160, 221),  # Plum
    }
    
    def __init__(self, courses: List[Course], instructors, rooms):
        super().__init__()
        self.courses = courses
        self.instructors = instructors
        self.rooms = rooms
        self.algorithm: Optional[ScheduleAlgorithm] = None
        self.conflicts: List[Conflict] = []
        self.selected_year_filter: Optional[int] = None  # None = All Years
        
        self.setWindowTitle("BeePlan - University Course Scheduling System")
        self.setMinimumSize(1200, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title_label = QLabel("BeePlan - Course Schedule")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Schedule")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.clicked.connect(self.generate_schedule)
        button_layout.addWidget(self.generate_btn)
        
        self.report_btn = QPushButton("View Report")
        self.report_btn.setMinimumHeight(40)
        self.report_btn.clicked.connect(self.show_report)
        button_layout.addWidget(self.report_btn)
        
        self.export_btn = QPushButton("Export JSON")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self.export_schedule)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Filter layout
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter by Year:")
        filter_layout.addWidget(filter_label)
        
        self.year_filter_combo = QComboBox()
        self.year_filter_combo.addItems(["All Years", "Year 1", "Year 2", "Year 3", "Year 4"])
        self.year_filter_combo.setCurrentIndex(0)  # Default to "All Years"
        self.year_filter_combo.currentIndexChanged.connect(self.on_year_filter_changed)
        filter_layout.addWidget(self.year_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # Schedule table
        self.schedule_table = QTableWidget()
        self._setup_table()
        main_layout.addWidget(self.schedule_table)
        
        # Status label
        self.status_label = QLabel("Ready to generate schedule")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
    
    def _setup_table(self):
        """Setup the schedule table widget."""
        # Columns: Time | Monday | Tuesday | Wednesday | Thursday | Friday
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels(["Time", "Monday", "Tuesday", 
                                                      "Wednesday", "Thursday", "Friday"])
        
        # Rows: One for each hour
        self.schedule_table.setRowCount(len(self.HOURS))
        
        # Set time column
        for i, hour in enumerate(self.HOURS):
            time_item = QTableWidgetItem(f"{hour:02d}:{self.MINUTE:02d}")
            time_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            font = QFont("Arial", 9)
            font.setBold(True)
            time_item.setFont(font)
            self.schedule_table.setItem(i, 0, time_item)
        
        # Configure table properties
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectItems)
        self.schedule_table.verticalHeader().setVisible(False)
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.setAlternatingRowColors(True)
        
        # Set row heights
        for i in range(len(self.HOURS)):
            self.schedule_table.setRowHeight(i, 80)
    
    def _get_cell_content(self, day: str, hour: int) -> List[tuple]:
        """Get all courses scheduled at a specific day and hour.
        
        Returns:
            List of (course, is_lab, duration) tuples
        """
        content = []
        for course in self.courses:
            # Check theory
            if course.theory_slot and course.theory_room:
                if course.theory_slot.day == day and course.theory_slot.hour == hour:
                    content.append((course, False, course.theory_hours))
            # Check lab
            if course.lab_slot and course.lab_room:
                if course.lab_slot.day == day and course.lab_slot.hour == hour:
                    content.append((course, True, course.lab_hours))
        
        return content
    
    def on_year_filter_changed(self, index: int):
        """Handle year filter selection change."""
        if index == 0:  # "All Years"
            self.selected_year_filter = None
        else:  # Year 1-4 (index 1-4 maps to year 1-4)
            self.selected_year_filter = index
        self._update_table()
    
    def _get_filtered_courses(self) -> List[Course]:
        """Get courses filtered by selected year."""
        if self.selected_year_filter is None:
            return self.courses
        return [c for c in self.courses if c.year == self.selected_year_filter]
    
    def _update_table(self):
        """Update the schedule table with current course assignments."""
        # Clear all cells (except time column)
        for row in range(len(self.HOURS)):
            for col in range(1, 6):  # Skip time column
                self.schedule_table.setItem(row, col, QTableWidgetItem(""))
        
        # Fill with course data (filtered by year)
        day_map = {day: idx + 1 for idx, day in enumerate(self.DAYS)}
        filtered_courses = self._get_filtered_courses()
        
        for course in filtered_courses:
            # Theory session
            if course.theory_slot and course.theory_room:
                day_idx = day_map.get(course.theory_slot.day)
                hour_row = self.HOURS.index(course.theory_slot.hour)
                
                if day_idx and hour_row >= 0:
                    duration_text = f"({course.theory_hours}h)" if course.theory_hours > 1 else ""
                    cell_text = f"{course.code}\n{course.name}\nRoom: {course.theory_room.id} {duration_text}"
                    item = QTableWidgetItem(cell_text)
                    
                    # Set font (italic for elective courses)
                    font = QFont("Arial", 8)
                    if course.type != "mandatory":
                        font.setItalic(True)
                    item.setFont(font)
                    
                    # Check for conflicts (priority: conflicts override year colors)
                    conflict_msg = self._get_conflict_message(course, course.theory_slot, False)
                    if conflict_msg:
                        item.setBackground(QBrush(QColor(255, 150, 150)))  # Bright red for conflicts
                        item.setToolTip(f"⚠️ CONFLICT: {conflict_msg}")
                    else:
                        # Normal year-based coloring (light blue for elective courses)
                        if course.type != "mandatory":
                            item.setForeground(QBrush(QColor(30, 144, 255)))  # Light blue text for electives
                            color = self.YEAR_COLORS.get(course.year, QColor(255, 255, 255))
                            # Make background slightly lighter/blue-tinted for electives
                            if color.red() == 255 and color.green() == 255 and color.blue() == 255:
                                color = QColor(240, 248, 255)  # Alice blue for white background
                            else:
                                color = color.lighter(115)  # Lighter version of year color
                            item.setBackground(QBrush(color))
                        else:
                            color = self.YEAR_COLORS.get(course.year, QColor(255, 255, 255))
                            item.setBackground(QBrush(color))
                    self.schedule_table.setItem(hour_row, day_idx, item)
            
            # Lab session
            if course.lab_slot and course.lab_room:
                day_idx = day_map.get(course.lab_slot.day)
                hour_row = self.HOURS.index(course.lab_slot.hour)
                
                if day_idx and hour_row >= 0:
                    # Check if cell already has content
                    existing_item = self.schedule_table.item(hour_row, day_idx)
                    if existing_item:
                        # Append lab info
                        existing_text = existing_item.text()
                        lab_text = f"\n--- LAB ---\nRoom: {course.lab_room.id}"
                        existing_item.setText(existing_text + lab_text)
                    else:
                        # --- YENİ KOD BAŞLANGICI ---
                        duration_text = f"({course.lab_hours}h)" if course.lab_hours > 1 else ""
                        
                        # 1. Ders Kodunu Garantiye Al (SENG 383 yazması için)
                        code_text = getattr(course, 'code', "Ders")
                        
                        # 2. Oda Bilgisini Al
                        room_text = course.lab_room.id if course.lab_room else "Lab"

                        # 3. Format: 
                        # SENG 383
                        # (LAB)
                        # L-101
                        cell_text = f"{code_text}\n(LAB)\n{room_text} {duration_text}"
                        
                        item = QTableWidgetItem(cell_text)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # Rengi Mavi Yap (Lab olduğu belli olsun)
                        item.setBackground(QColor("#E3F2FD")) 
                        
                        # Yazı Tipi Ayarları (Senin kodundaki mevcut ayarlar)
                        font = QFont("Arial", 8)
                        if getattr(course, 'type', '') != "mandatory":
                            font.setItalic(True)
                        item.setFont(font)
                        
                        # Çakışma Kontrolü (Senin kodundaki mantık)
                        conflict_msg = self._get_conflict_message(course, course.lab_slot, True)
                        if conflict_msg:
                            item.setBackground(QBrush(QColor(255, 150, 150)))
                            item.setToolTip(f"⚠️ CONFLICT: {conflict_msg}")
                        else:
                            # Seçmeli ders ise rengi ayarla
                            if getattr(course, 'type', '') != "mandatory":
                                item.setForeground(QBrush(QColor(30, 144, 255)))
                        
                        self.schedule_table.setItem(hour_row, day_idx, item)
                        # --- YENİ KOD BİTİŞİ ---
                        
                        # Set font (italic for elective courses)
                        font = QFont("Arial", 8)
                        if course.type != "mandatory":
                            font.setItalic(True)
                        item.setFont(font)
                        
                        # Check for conflicts (priority: conflicts override year colors)
                        conflict_msg = self._get_conflict_message(course, course.lab_slot, True)
                        if conflict_msg:
                            item.setBackground(QBrush(QColor(255, 150, 150)))  # Bright red for conflicts
                            item.setToolTip(f"⚠️ CONFLICT: {conflict_msg}")
                        else:
                            # Normal year-based coloring (darker for lab)
                            if course.type != "mandatory":
                                item.setForeground(QBrush(QColor(30, 144, 255)))  # Light blue text for electives
                                color = self.YEAR_COLORS.get(course.year, QColor(255, 255, 255))
                                if color.red() == 255 and color.green() == 255 and color.blue() == 255:
                                    color = QColor(230, 240, 255)  # Slightly darker blue-tinted for lab
                                else:
                                    color = color.darker(105).lighter(115)  # Adjust for elective lab
                                item.setBackground(QBrush(color))
                            else:
                                color = self.YEAR_COLORS.get(course.year, QColor(255, 255, 255))
                                color = color.darker(110)
                                item.setBackground(QBrush(color))
                        self.schedule_table.setItem(hour_row, day_idx, item)
    
    def _has_conflict(self, course: Course, time_slot: TimeSlot, is_lab: bool) -> bool:
        """Check if a course/time slot has a conflict."""
        for conflict in self.conflicts:
            if conflict.entry1:
                if (conflict.entry1.course == course and 
                    conflict.entry1.time_slot == time_slot and
                    conflict.entry1.is_lab == is_lab):
                    return True
            if conflict.entry2:
                if (conflict.entry2.course == course and
                    conflict.entry2.time_slot == time_slot and
                    conflict.entry2.is_lab == is_lab):
                    return True
        return False
    
    def _get_conflict_message(self, course: Course, time_slot: TimeSlot, is_lab: bool) -> str:
        """Get conflict message for a course/time slot."""
        for conflict in self.conflicts:
            if conflict.entry1:
                if (conflict.entry1.course == course and
                    conflict.entry1.time_slot == time_slot and
                    conflict.entry1.is_lab == is_lab):
                    return conflict.message
            if conflict.entry2:
                if (conflict.entry2.course == course and
                    conflict.entry2.time_slot == time_slot and
                    conflict.entry2.is_lab == is_lab):
                    return conflict.message
        return ""
    
    def generate_schedule(self):
        """Generate schedule using the algorithm."""
        self.status_label.setText("Generating schedule...")
        self.status_label.repaint()
        
        # Create algorithm instance
        self.algorithm = ScheduleAlgorithm(self.courses, self.instructors, self.rooms)
        
        # Generate schedule
        success, messages = self.algorithm.generate_schedule()
        
        # Validate schedule
        self.conflicts = self.algorithm.validate_schedule() if success else []
        
        # Update table
        self._update_table()
        
        # Update status
        if success:
            scheduled_count = sum(1 for c in self.courses if c.is_scheduled())
            total_count = len(self.courses)
            self.status_label.setText(f"Schedule generated! {scheduled_count}/{total_count} courses scheduled.")
            
            if self.conflicts:
                self.status_label.setText(
                    self.status_label.text() + f" ({len(self.conflicts)} conflicts detected)")
        else:
            self.status_label.setText(f"Schedule generation failed. {len(messages)} errors.")
            QMessageBox.warning(self, "Generation Failed", 
                              "Could not generate complete schedule.\n" + "\n".join(messages[:5]))
    
    def show_report(self):
        """Show scheduling report dialog."""
        unscheduled = [c for c in self.courses if not c.is_scheduled()]
        conflicts = self.conflicts if self.algorithm else []
        
        dialog = ReportDialog(unscheduled, conflicts, self)
        dialog.exec()
    
    def export_schedule(self):
        """Export schedule to JSON file."""
        if not any(c.is_scheduled() for c in self.courses):
            QMessageBox.warning(self, "Export Failed", 
                              "No schedule to export. Please generate a schedule first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Schedule", "schedule_output.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                export_schedule_to_json(self.courses, file_path)
                QMessageBox.information(self, "Export Successful", 
                                      f"Schedule exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", 
                                   f"Error exporting schedule: {str(e)}")
