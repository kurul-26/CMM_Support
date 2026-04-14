import sys
import os
import math
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)
def normalize(angle: float) -> float:
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle
def snap(angle: float) -> float:
    return round(angle / 7.5) * 7.5
def snap_A(angle: float) -> float:
    if angle <= 3.25:
        return 0
    val = round(angle / 7.5) * 7.5
    return min(val, 105)
def calc_B(theta: float) -> tuple:
    in_raw = normalize(theta)
    out_raw = normalize(theta - 180)
    in_snap = normalize(snap(in_raw))
    out_snap = normalize(snap(out_raw))
    if theta == 0:
        out_snap = 0
    if theta == 180:
        in_snap = -180
    return in_raw, in_snap, out_raw, out_snap
class DigitalDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(100)
        self.setMinimumWidth(200)
        self.A_val = 0.0
        self.B_val = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                border: 1px solid #222;
                border-radius: 1px;
            }
        """)
    def update_values(self, A: float, B: float) -> None:
        self.A_val = A
        self.B_val = B
        self.update()
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Courier New", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(0, 255, 102))
        a_text = f"A: {self.A_val:6.1f}°"
        painter.drawText(10, 40, a_text)
        b_text = f"B: {self.B_val:6.1f}°"
        painter.drawText(10, 80, b_text)
class ToggleSwitch(QCheckBox):
    def __init__(self):
        super().__init__()
        self.setFixedSize(60, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._offset = 2
        self.anim = QPropertyAnimation(self, b"offset", self)
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.stateChanged.connect(self.start_anim)
    def mousePressEvent(self, event):
        self.setChecked(not self.isChecked())
        event.accept()
    def start_anim(self):
        self.anim.stop()
        self.anim.setEndValue(32 if self.isChecked() else 2)
        self.anim.start()
    def get_offset(self) -> int:
        return self._offset
    def set_offset(self, val: int) -> None:
        self._offset = val
        self.update()
    offset = pyqtProperty(int, fget=get_offset, fset=set_offset)
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        if self.isChecked():
            p.setBrush(QColor("blue"))
        else:
            p.setBrush(QColor("red"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, 14, 14)
        p.setBrush(QColor("white"))
        p.drawEllipse(self._offset, 2, 24, 24)
def draw_coordinate_system(p: QPainter, cx: int, cy: int, r_outer: int) -> None:
    pen = QPen(QColor("black"), 2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    font = QFont("Arial", 12, QFont.Weight.Bold)
    p.setFont(font)
    rad = math.radians(0)
    x_end = cx + (r_outer + 30) * math.sin(rad)
    y_end = cy + (r_outer + 30) * math.cos(rad)
    p.drawLine(cx, cy, int(x_end), int(y_end))
    p.drawText(int(x_end) - 11, int(y_end) + 19, "+X")
    rad = math.radians(180)
    x_end = cx + (r_outer + 30) * math.sin(rad)
    y_end = cy + (r_outer + 30) * math.cos(rad)
    p.drawLine(cx, cy, int(x_end), int(y_end))
    p.drawText(int(x_end) - 10, int(y_end) - 9, "-X")
    rad = math.radians(90)
    x_end = cx + (r_outer + 30) * math.sin(rad)
    y_end = cy + (r_outer + 30) * math.cos(rad)
    p.drawLine(cx, cy, int(x_end), int(y_end))
    p.drawText(int(x_end) + 5, int(y_end) + 5, "+Y")
    rad = math.radians(270)
    x_end = cx + (r_outer + 30) * math.sin(rad)
    y_end = cy + (r_outer + 30) * math.cos(rad)
    p.drawLine(cx, cy, int(x_end), int(y_end))
    p.drawText(int(x_end) - 20, int(y_end) + 4, "-Y")
class AngleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.theta = 0
        self.display_theta = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(16)
        self.setMinimumSize(500, 500)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    def set_angle(self, theta: float) -> None:
        self.theta = theta % 360
    def update_angle(self) -> None:
        diff = self.theta - self.display_theta
        if abs(diff) < 0.5:
            self.display_theta = self.theta
        else:
            self.display_theta += diff * 0.2
        self.update()
    def draw_probe_arrow(self, p: QPainter, cx: int, cy: int, radius: int, 
                          angle_deg: float, inward: bool = True, color: QColor = QColor("red")) -> None:
        rad = math.radians(angle_deg)
        offset = 6
        r = radius + (offset if inward else -offset)
        px = cx + r * math.sin(rad)
        py = cy + r * math.cos(rad)
        dx = math.sin(rad)
        dy = math.cos(rad)
        arrow_len = 20
        if inward:
            start_x = px + dx * arrow_len
            start_y = py + dy * arrow_len
        else:
            start_x = px - dx * arrow_len
            start_y = py - dy * arrow_len
        p.setPen(QPen(color, 3))
        p.drawLine(int(start_x), int(start_y), int(px), int(py))
        angle = math.atan2(py - start_y, px - start_x)
        size = 6
        left = QPointF(px - size * math.cos(angle - math.pi/6),
                       py - size * math.sin(angle - math.pi/6))
        right = QPointF(px - size * math.cos(angle + math.pi/6),
                        py - size * math.sin(angle + math.pi/6))
        p.drawLine(QPointF(px, py), left)
        p.drawLine(QPointF(px, py), right)
    def paintEvent(self, e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() // 2
        cy = self.height() // 2
        r_main = 150
        r_outer = 170
        r_inner = 130
        p.setPen(QPen(QColor("black"), 3))
        p.drawEllipse(cx - r_main, cy - r_main, r_main * 2, r_main * 2)
        p.setPen(QPen(QColor("blue"), 3))
        p.drawEllipse(cx - r_outer, cy - r_outer, r_outer * 2, r_outer * 2)
        draw_coordinate_system(p, cx, cy, r_outer)
        p.setPen(QPen(QColor("red"), 3))
        p.drawEllipse(cx - r_inner, cy - r_inner, r_inner * 2, r_inner * 2)
        rad = math.radians(self.display_theta)
        inner_gap = 1
        outer_gap = 55
        start_x = cx + inner_gap * math.sin(rad)
        start_y = cy + inner_gap * math.cos(rad)
        end_x = cx + (r_main - outer_gap) * math.sin(rad)
        end_y = cy + (r_main - outer_gap) * math.cos(rad)
        p.setPen(QPen(QColor("black"), 3))
        p.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))
        p.setBrush(QColor("black"))
        p.drawEllipse(cx - 5, cy - 5, 10, 10)
        point_r = r_main
        px = cx + point_r * math.sin(rad)
        py = cy + point_r * math.cos(rad)
        p.drawEllipse(int(px) - 5, int(py) - 5, 10, 10)
        self.draw_probe_arrow(p, cx, cy, r_inner, self.display_theta, inward=False, color=QColor("red"))
        self.draw_probe_arrow(p, cx, cy, r_outer, self.display_theta, inward=True, color=QColor("blue"))
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hakkında")
        self.setFixedSize(400, 250)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #333;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 1px;
            }
        """)
        self.text_label.setText("""
            Bu araç, açısal ölçümler için 
            Hesaplamaları kolaylaştırmak adına 
            hobi amacıyla geliştirilmiştir.
            Pazarlanması ve ticari amaç ile 
            kullanılması kesinlikle yasaktır.
            github.com/kurul-26
            © Fatih Kurul
                    """)
        layout.addWidget(self.text_label)
        btn_close = QPushButton("Kapat")
        btn_close.setFixedHeight(30)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
class ClickableTable(QTableWidget):    
    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
        else:
            super().mousePressEvent(event)
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CMM_Support_v1.0")
        self.counter = 1
        self.limit_error = False
        self._setup_ui()
        self._connect_signals()
        self.update_all()
    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #777;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
            }
            QLabel {
                color: #333;
            }
        """)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: white;")
        left_widget.setFixedWidth(280)
        left = QVBoxLayout(left_widget)
        left.setSpacing(12)
        left.addWidget(QLabel("Karakteristik & Item Numarası", styleSheet="font-weight: bold;"))
        self.input_item = QLineEdit()
        self.input_item.setPlaceholderText("Karakteristik & Item No girin...")
        left.addWidget(self.input_item)
        left.addWidget(QLabel("Dikey Model Açısı", styleSheet="font-weight: bold;"))
        self.input_A = QLineEdit("0")
        self.input_A.setPlaceholderText("Dikey Model Açısını Girin...")
        self.input_A.setFixedHeight(30)
        left.addWidget(self.input_A)
        left.addWidget(QLabel("Yatay Model Açısı", styleSheet="font-weight: bold;"))
        self.input_B = QLineEdit("0")
        self.input_B.setPlaceholderText("Yatay Model Açısını Girin...")
        self.input_B.setFixedHeight(30)
        left.addWidget(self.input_B)
        left.addSpacing(5)
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()
        toggle_layout.addWidget(QLabel("İç Ölçüm", styleSheet="font-weight: bold;"))
        self.toggle = ToggleSwitch()
        toggle_layout.addWidget(self.toggle)
        toggle_layout.addWidget(QLabel("Dış Ölçüm", styleSheet="font-weight: bold;"))
        toggle_layout.addStretch()
        left.addLayout(toggle_layout)
        left.addSpacing(10)
        self.info = QLabel("")
        self.info.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.info.setFixedHeight(85)
        self.info.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.info.setWordWrap(True)
        left.addWidget(self.info)
        left.addSpacing(5)
        self.display = DigitalDisplay()
        left.addWidget(self.display)
        left.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        self.btn_save = QPushButton("Kaydet")
        self.btn_delete = QPushButton("Sil")
        self.btn_reset = QPushButton("Reset")
        for btn in [self.btn_save, self.btn_delete, self.btn_reset]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(32)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_reset)
        left.addLayout(btn_layout)
        main_layout.addWidget(left_widget)
        self.widget = AngleWidget()
        self.widget.setStyleSheet("background-color: white;")
        main_layout.addWidget(self.widget, 1)
        right = QVBoxLayout()
        right.setSpacing(8)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Kayıtlar", styleSheet="font-weight: bold;"))
        header_layout.addStretch()  # Butonu sağa iter
        self.btn_about = QPushButton("Hakkında")
        self.btn_about.setFixedWidth(80)
        self.btn_about.setFixedHeight(25)
        self.btn_about.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        header_layout.addWidget(self.btn_about)
        right.addLayout(header_layout)
        self.table = ClickableTable()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["No", "A", "B", "Model Açısı", "Item"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: black;
                border: 2px solid black;
                alternate-background-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
                color: black;
            }
            QHeaderView::section {
                background-color: #f8f7fc;
                border: 0px solid black;
                border-bottom: 1px solid black;
                padding: 5px;
                font-weight: normal;
            }
        """)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 90)
        self.table.verticalHeader().setVisible(False)
        right.addWidget(self.table)
        main_layout.addLayout(right, 1)
        self.setLayout(main_layout)
        self.setFixedSize(1216, 550)
        self.table.setMinimumWidth(300)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.table.clearSelection()
            self.update_buttons()
        super().keyPressEvent(event)
    def _connect_signals(self) -> None:
        self.input_A.textChanged.connect(self.update_all)
        self.input_B.textChanged.connect(self.update_all)
        self.toggle.stateChanged.connect(self.update_all)
        self.btn_save.clicked.connect(self.save_record)
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_reset.clicked.connect(self.reset_all)
        self.btn_about.clicked.connect(self.show_about_dialog)
        self.table.itemSelectionChanged.connect(self.update_buttons)
        self.table.selectionModel().selectionChanged.connect(self.update_buttons)
    def show_about_dialog(self) -> None:
        dialog = AboutDialog(self)
        dialog.exec()
    def get_B_value(self) -> float:
        return self.out_snap if self.toggle.isChecked() else self.in_snap
    def update_all(self) -> None:
        self.limit_error = False
        try:
            A_val = float(self.input_A.text())
        except ValueError:
            A_val = 0
        if A_val > 108.75:
            self.limit_error = True
        try:
            B_val = float(self.input_B.text())
        except ValueError:
            B_val = 0
        self.A_snap = snap_A(A_val)
        self.in_raw, self.in_snap, self.out_raw, self.out_snap = calc_B(B_val)
        self.widget.set_angle(B_val)
        B_final = self.get_B_value()
        try:
            B_final = float(B_final)
        except (TypeError, ValueError):
            B_final = 0.0
        self.info.setText(
            f"📐 Model Açısı: {B_val:.3f}°\n"
            f"🔴 İç Ölçüm: {self.in_raw:.3f}°\n"
            f"🔵 Dış Ölçüm: {self.out_raw:.3f}°"
        )
        self.update_buttons()
        self.display.update_values(self.A_snap, B_final)
    def update_buttons(self) -> None:
        has_selection = len(self.table.selectedItems()) > 0
        self.btn_delete.setEnabled(has_selection)
        if self.limit_error:
            self.btn_save.setEnabled(False)
            return
        try:
            current_A = round(self.A_snap, 1)
            current_B = round(self.get_B_value(), 1)
        except (TypeError, ValueError):
            self.btn_save.setEnabled(False)
            return
        for i in range(self.table.rowCount()):
            try:
                saved_A = float(self.table.item(i, 1).text().replace("°", ""))
                saved_B = float(self.table.item(i, 2).text().replace("°", ""))
                if round(saved_A, 1) == current_A and round(saved_B, 1) == current_B:
                    self.btn_save.setEnabled(False)
                    return
            except (AttributeError, ValueError):
                continue
        self.btn_save.setEnabled(True)
    def renumber_rows(self) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))
    def save_record(self) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        try:
            raw_B = float(self.input_B.text())
        except ValueError:
            raw_B = 0.0
        item_text = self.input_item.text().strip()
        def center_item(text: str) -> QTableWidgetItem:
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            return item
        new_num = row + 1
        self.table.setItem(row, 0, center_item(str(new_num)))
        self.table.setItem(row, 1, center_item(f"{self.A_snap:.1f}°"))
        self.table.setItem(row, 2, center_item(f"{self.get_B_value():.1f}°"))
        self.table.setItem(row, 3, center_item(f"{raw_B:.3f}°"))
        self.table.setItem(row, 4, center_item(item_text))
        self.update_buttons()
    def delete_record(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.renumber_rows()
            self.table.setCurrentCell(-1, -1)
            self.table.clearSelection()
            self.update_buttons()
    def reset_all(self) -> None:
        self.input_A.setText("0")
        self.input_B.setText("0")
        self.table.setRowCount(0)
        self.update_all()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())