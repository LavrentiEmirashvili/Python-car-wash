"""
PyQt5 frontend for the car wash application.
Uses Models, services (with decorators), and role-based dashboards.
"""

import datetime

from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPainterPath
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QProgressBar,
    QFileDialog,
    QCheckBox,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
)

from Models import Customer, Staff
from services import (
    calculate_booking_price,
    cancel_booking,
    complete_booking,
    create_booking,
    daily_booking_count,
    find_self_service_stations,
    find_stations_by_district,
    get_customer_history,
    get_customer_upcoming_bookings,
    most_popular_service,
    register_car,
    remove_car,
    total_revenue,
    initiate_email_verification,
    verify_email,
    initiate_2fa,
    verify_2fa,
    request_password_recovery,
    reset_password
)
import database
from store import AppStore

# Color palette
COLOR_BG = "#121212"
COLOR_SURFACE = "#1e1e1e"
COLOR_ELEVATED = "#2d2d2d"
COLOR_BORDER = "#444444"
COLOR_TEXT = "#eeeeee"
COLOR_TEXT_MUTED = "#999999"
COLOR_ACCENT = "#ffffff"
COLOR_ACCENT_TEXT = "#121212"
COLOR_HOVER = "#333333"

FONT_FAMILY = '"Noto Sans Georgian", "Segoe UI Variable", "Segoe UI", sans-serif'
FONT_SIZE_BASE = 14
FONT_SIZE_SMALL = 12
FONT_SIZE_TITLE = 25

BOOKING_TYPE_LABELS = {
    "staff_wash": "პერსონალის რეცხვა (25₾)",
    "self_service": "თვითმომსახურება (12₾)",
}

STATUS_LABELS = {
    "pending": "მოლოდინში",
    "confirmed": "დადასტურებული",
    "completed": "დასრულებული",
    "cancelled": "გაუქმებული",
}


def _make_circular_pixmap(src_pix: QPixmap, size: int) -> QPixmap:
    """Return a circular-clipped pixmap of the given size from source pixmap."""
    if src_pix is None or src_pix.isNull():
        # placeholder background
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(COLOR_ELEVATED))
        painter.setPen(QColor(COLOR_BORDER))
        painter.drawEllipse(1, 1, size - 2, size - 2)

        # Draw a simple person silhouette icon
        painter.setBrush(QColor(COLOR_TEXT_MUTED))
        painter.setPen(Qt.NoPen)
        # Head
        painter.drawEllipse(int(size * 0.35), int(size * 0.2), int(size * 0.3), int(size * 0.3))
        # Body (semicircle)
        painter.drawChord(int(size * 0.15), int(size * 0.55), int(size * 0.7), int(size * 0.7), 0 * 16, 180 * 16)

        painter.end()
        return pm

    scaled = src_pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    # center the scaled image
    dx = (scaled.width() - size) // 2
    dy = (scaled.height() - size) // 2
    painter.drawPixmap(-dx, -dy, scaled)
    painter.end()
    return result


def configure_table(table):
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(45)
    table.setStyleSheet(f"""
        QTableWidget {{
            background-color: {COLOR_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
        }}
        QTableWidget::item {{
            padding: 8px;
        }}
        QTableWidget::item:selected {{
            background-color: {COLOR_ACCENT};
            color: {COLOR_ACCENT_TEXT};
        }}
    """)


def show_error(parent, title, exc):
    QMessageBox.critical(parent, title, str(exc))


def show_info(parent, title, message):
    QMessageBox.information(parent, title, message)


def setup_app_font(app):
    """Pick the best available font for Georgian and Latin UI text."""
    from PyQt5.QtGui import QFontDatabase

    preferred = (
        "Noto Sans Georgian",
        "Segoe UI Variable Display",
        "Segoe UI Variable",
        "Segoe UI",
        "Arial",
    )
    families = QFontDatabase().families()
    chosen = next((name for name in preferred if name in families), "Segoe UI")

    font = QFont(chosen, FONT_SIZE_BASE)
    font.setStyleHint(QFont.SansSerif)
    font.setHintingPreference(QFont.PreferFullHinting)
    app.setFont(font)
    return font


class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("რეგისტრაცია")
        self.setMinimumWidth(450)
        self.setObjectName("registerDialog")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        title = QLabel("ახალი ანგარიშის შექმნა")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 8px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setSpacing(16)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("თქვენი სახელი")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@example.com")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("555123456")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("••••••••")
        
        self.enable_2fa_cb = QComboBox()
        self.enable_2fa_cb.addItems(["არა", "დიახ"])

        form.addRow("სახელი:", self.name_edit)
        form.addRow("ელფოსტა:", self.email_edit)
        form.addRow("ტელეფონი:", self.phone_edit)
        form.addRow("პაროლი:", self.password_edit)
        form.addRow("2FA-ს ჩართვა:", self.enable_2fa_cb)
        layout.addWidget(form_widget)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("რეგისტრაცია")
        self.buttons.button(QDialogButtonBox.Cancel).setText("გაუქმება")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self):
        return (
            self.name_edit.text().strip(),
            self.email_edit.text().strip(),
            self.phone_edit.text().strip(),
            self.password_edit.text().strip(),
            self.enable_2fa_cb.currentText() == "დიახ"
        )


class VerificationDialog(QDialog):
    def __init__(self, email, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ვერიფიკაცია")
        self.setMinimumWidth(380)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(24)

        title = QLabel("ვერიფიკაცია")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_TEXT};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info = QLabel(f"დადასტურების კოდი გაეგზავნა ელ-ფოსტაზე:\n<b>{email}</b>")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(info)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("000000")
        self.code_edit.setAlignment(Qt.AlignCenter)
        self.code_edit.setStyleSheet(f"""
            font-size: 28px; 
            letter-spacing: 8px; 
            font-weight: bold; 
            padding: 15px;
            background-color: {COLOR_BG};
            border: 2px solid {COLOR_BORDER};
        """)
        self.code_edit.setMaxLength(6)
        layout.addWidget(self.code_edit)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("დადასტურება")
        self.buttons.button(QDialogButtonBox.Cancel).setText("გაუქმება")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_code(self):
        return self.code_edit.text().strip()

class PasswordRecoveryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("პაროლის აღდგენა")
        self.setMinimumWidth(400)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(35, 35, 35, 35)
        self.layout.setSpacing(20)

        title = QLabel("პაროლის აღდგენა")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_TEXT};")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("თქვენი ელ-ფოსტა")
        self.layout.addWidget(QLabel("ელ-ფოსტა:"))
        self.layout.addWidget(self.email_edit)
        
        self.send_btn = QPushButton("კოდის გაგზავნა")
        self.send_btn.setObjectName("primaryBtn")
        self.layout.addWidget(self.send_btn)
        
        self.recovery_form = QWidget()
        self.recovery_layout = QFormLayout(self.recovery_form)
        self.recovery_layout.setSpacing(15)
        
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("6-ნიშნა კოდი")
        self.new_pass_edit = QLineEdit()
        self.new_pass_edit.setEchoMode(QLineEdit.Password)
        self.new_pass_edit.setPlaceholderText("ახალი პაროლი")
        
        self.recovery_layout.addRow("კოდი:", self.code_edit)
        self.recovery_layout.addRow("ახალი პაროლი:", self.new_pass_edit)
        self.recovery_form.setVisible(False)
        self.layout.addWidget(self.recovery_form)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("პაროლის შეცვლა")
        self.buttons.button(QDialogButtonBox.Cancel).setText("გაუქმება")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        self.layout.addWidget(self.buttons)

class LoginPage(QWidget):
    def __init__(self, store: AppStore, on_login):
        super().__init__()
        self.store = store
        self.on_login = on_login

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(32, 32, 32, 32)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setMaximumWidth(480)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(18)

        title = QLabel("Car Wash")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("პრემიუმ ავტოსამრეცხაო სერვისი")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subtitle")
        card_layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("მაგ.: admin@carwash.ge")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("შეიყვანეთ პაროლი")
        form.addRow("ელფოსტა:", self.email_edit)
        form.addRow("პაროლი:", self.password_edit)
        card_layout.addLayout(form)

        login_btn = QPushButton("შესვლა")
        login_btn.setObjectName("primaryBtn")
        login_btn.setMinimumHeight(48)
        login_btn.clicked.connect(self._login)
        card_layout.addWidget(login_btn)

        register_btn = QPushButton("ახალი ანგარიშის შექმნა")
        register_btn.setObjectName("secondaryBtn")
        register_btn.setMinimumHeight(48)
        register_btn.clicked.connect(self._register)
        card_layout.addWidget(register_btn)

        forgot_btn = QPushButton("პაროლის აღდგენა")
        forgot_btn.setObjectName("secondaryBtn")
        forgot_btn.clicked.connect(self._forgot_password)
        card_layout.addWidget(forgot_btn)

        hint = QLabel(
            "საცდელი ანგარიშები:\n"
            "• ადმინისტრატორი — admin@carwash.ge / admin123\n"
            "• პერსონალი — luka@carwash.ge / staff123\n"
            "• კლიენტი — giorgi@gmail.com / customer123"
        )
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        layout.addWidget(card, alignment=Qt.AlignCenter)

    def _login(self):
        email = self.email_edit.text().strip()
        password = self.password_edit.text().strip()
        try:
            user = self.store.login(email, password)
            if user:
                if user.is_2fa_enabled:
                    initiate_2fa(user)
                    dialog = VerificationDialog(user.email, self)
                    dialog.setWindowTitle("2FA ვერიფიკაცია")
                    if dialog.exec_() == QDialog.Accepted:
                        code = dialog.get_code()
                        if verify_2fa(user, code):
                            self.on_login(user)
                        else:
                            show_error(self, "2FA", ValueError("არასწორი 2FA კოდი"))
                    return
                else:
                    self.on_login(user)
            else:
                show_error(self, "შესვლა", ValueError("არასწორი ელ-ფოსტა ან პაროლი"))
        except ValueError as exc:
            show_error(self, "შესვლა", exc)

    def _register(self):
        dialog = RegisterDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        name, email, phone, password, use_2fa = dialog.get_data()
        if not all([name, email, phone, password]):
            show_error(self, "რეგისტრაცია", ValueError("ყველა ველი სავალდებულოა"))
            return
        try:
            # Create but not verified yet
            customer = self.store.register_new_customer(name, email, phone, password)
            customer.is_2fa_enabled = use_2fa
            
            initiate_email_verification(customer)
            v_dialog = VerificationDialog(customer.email, self)
            if v_dialog.exec_() == QDialog.Accepted:
                code = v_dialog.get_code()
                if verify_email(customer, code):
                    show_info(self, "რეგისტრაცია", f"მოგესალმებით, {customer.name}!\nთქვენი ანგარიში გააქტიურდა.")
                else:
                    show_error(self, "ვერიფიკაცია", ValueError("არასწორი კოდი. ანგარიში ვერ გააქტიურდა."))
            else:
                # Keep the user in store but unverified, they can't login anyway
                show_info(self, "რეგისტრაცია", "ანგარიში შეიქმნა, მაგრამ ელ-ფოსტა არ არის დადასტურებული.")
        except (ValueError, TypeError) as exc:
            show_error(self, "რეგისტრაცია", exc)

    def _forgot_password(self):
        dialog = PasswordRecoveryDialog(self)
        
        def send_code():
            email = dialog.email_edit.text().strip()
            if not email:
                show_error(dialog, "შეცდომა", ValueError("გთხოვთ შეიყვანოთ ელ-ფოსტა"))
                return
            if request_password_recovery(self.store.users, email):
                show_info(dialog, "აღდგენა", "აღდგენის კოდი გაიგზავნა თქვენს ელ-ფოსტაზე.")
                dialog.recovery_form.setVisible(True)
                dialog.send_btn.setEnabled(False)
                dialog.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
            else:
                show_error(dialog, "შეცდომა", ValueError("მომხმარებელი ამ ელ-ფოსტით ვერ მოიძებნა"))

        dialog.send_btn.clicked.connect(send_code)
        
        if dialog.exec_() == QDialog.Accepted:
            email = dialog.email_edit.text().strip()
            code = dialog.code_edit.text().strip()
            new_pass = dialog.new_pass_edit.text()
            
            user = next((u for u in self.store.users if u.email.lower() == email.lower()), None)
            if user and reset_password(user, code, new_pass):
                show_info(self, "აღდგენა", "პაროლი წარმატებით შეიცვალა.")
            else:
                show_error(self, "აღდგენა", ValueError("არასწორი კოდი ან მომხმარებელი"))


class CustomerDashboard(QWidget):
    def __init__(self, store: AppStore):
        super().__init__()
        self.store = store
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setObjectName("dashboardContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header area
        header_card = QFrame()
        header_card.setObjectName("loginCard") # Reuse card style
        header_card_layout = QVBoxLayout(header_card)
        
        self.header = QLabel()
        self.header.setObjectName("dashboardHeader")
        self.header.setWordWrap(True)
        header_card_layout.addWidget(self.header)

        # Loyalty Area
        self.loyalty_container = QWidget()
        self.loyalty_bars_layout = QVBoxLayout(self.loyalty_container)
        self.loyalty_bars_layout.setContentsMargins(0, 5, 0, 0)
        header_card_layout.addWidget(self.loyalty_container)
        
        layout.addWidget(header_card)

        tabs = QTabWidget()

        # --- Cars tab ---
        cars_tab = QWidget()
        cars_layout = QVBoxLayout(cars_tab)
        self.cars_table = self._make_table(["სანომრე", "მოდელი", "ფერი"])
        cars_layout.addWidget(self.cars_table)

        remove_btn = QPushButton("არჩეული მანქანის წაშლა")
        remove_btn.setObjectName("secondaryBtn")
        remove_btn.clicked.connect(self._remove_car)
        cars_layout.addWidget(remove_btn)

        add_group = QGroupBox("მანქანის დამატება")
        add_form = QFormLayout(add_group)
        self.plate_edit = QLineEdit()
        self.plate_edit.setPlaceholderText("AA-123-BB")
        self.model_edit = QLineEdit()
        self.color_edit = QLineEdit()
        add_form.addRow("სანომრე:", self.plate_edit)
        add_form.addRow("მოდელი:", self.model_edit)
        add_form.addRow("ფერი:", self.color_edit)
        add_btn = QPushButton("➕ დამატება")
        add_btn.clicked.connect(self._add_car)
        add_form.addRow(add_btn)
        cars_layout.addWidget(add_group)
        tabs.addTab(cars_tab, "მანქანები")

        # --- Booking tab ---
        book_tab = QWidget()
        book_layout = QVBoxLayout(book_tab)
        book_form = QFormLayout()
        self.station_combo = QComboBox()
        self.car_combo = QComboBox()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.time_edit = QTimeEdit(QTime(10, 0))
        self.time_edit.setDisplayFormat("HH:mm")
        self.type_combo = QComboBox()
        for key, label in BOOKING_TYPE_LABELS.items():
            self.type_combo.addItem(label, key)
        self.district_filter = QLineEdit()
        self.district_filter.setPlaceholderText("მაგ: საბურთალო")
        filter_btn = QPushButton("ფილტრი რაიონით")
        filter_btn.clicked.connect(self._filter_stations)
        self_service_btn = QPushButton("მხოლოდ თვითმომსახურება")
        self_service_btn.clicked.connect(self._filter_self_service)

        book_form.addRow("სადგური:", self.station_combo)
        book_form.addRow("მანქანა:", self.car_combo)
        book_form.addRow("თარიღი:", self.date_edit)
        book_form.addRow("დრო:", self.time_edit)
        book_form.addRow("სერვისი:", self.type_combo)
        book_form.addRow("რაიონი:", self.district_filter)
        book_form.addRow(filter_btn)
        book_form.addRow(self_service_btn)
        book_layout.addLayout(book_form)

        book_btn = QPushButton("ჯავშნის შექმნა")
        book_btn.setObjectName("primaryBtn")
        book_btn.clicked.connect(self._create_booking)
        book_layout.addWidget(book_btn)
        book_layout.addStretch()
        tabs.addTab(book_tab, "ახალი ჯავშანი")

        # --- Upcoming tab ---
        upcoming_tab = QWidget()
        upcoming_layout = QVBoxLayout(upcoming_tab)
        self.upcoming_table = self._make_table(
            ["სადგური", "მანქანა", "თარიღი", "დრო", "ტიპი", "სტატუსი", "ფასი"]
        )
        upcoming_layout.addWidget(self.upcoming_table)
        cancel_btn = QPushButton("არჩეული ჯავშნის გაუქმება")
        cancel_btn.clicked.connect(self._cancel_booking)
        upcoming_layout.addWidget(cancel_btn)
        tabs.addTab(upcoming_tab, "მომავალი ჯავშნები")

        # --- History tab ---
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_table = self._make_table(
            ["სადგური", "მანქანა", "თარიღი", "ტიპი", "ფასი"]
        )
        history_layout.addWidget(self.history_table)
        tabs.addTab(history_tab, "ისტორია")

        layout.addWidget(tabs)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _make_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        configure_table(table)
        return table

    def refresh(self):
        user = self.store.current_user
        if not user: return

        self.header.setText(
            f"<b>{user.name}</b> — {user.get_dashboard()}<br>"
            f"ანგარიშის ბალანსი: {user.balance} ₾"
        )
        
        # Refresh Loyalty Bars
        for i in reversed(range(self.loyalty_bars_layout.count())): 
            item = self.loyalty_bars_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                # Clear nested layouts if any
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)

        self.loyalty_bars_layout.addWidget(LoyaltyProgressBar(user))

        self._populate_stations(self.store.stations)
        self._refresh_cars()
        self._refresh_upcoming()
        self._refresh_history()

    def _populate_stations(self, stations):
        self.station_combo.clear()
        for station in stations:
            ss = "✓ თვითმომსახურება" if station.has_self_service else "✗ თვითმომსახურება"
            self.station_combo.addItem(f"{station.name} ({ss})", station)

    def _refresh_cars(self):
        user = self.store.current_user
        self.car_combo.clear()
        self.cars_table.setRowCount(0)
        for car in user.cars:
            row = self.cars_table.rowCount()
            self.cars_table.insertRow(row)
            self.cars_table.setItem(row, 0, QTableWidgetItem(car.plate))
            self.cars_table.setItem(row, 1, QTableWidgetItem(car.model))
            self.cars_table.setItem(row, 2, QTableWidgetItem(car.color))
            self.car_combo.addItem(str(car), car)

    def _add_car(self):
        user = self.store.current_user
        try:
            register_car(
                user,
                self.plate_edit.text().strip(),
                self.model_edit.text().strip(),
                self.color_edit.text().strip(),
            )
            self.plate_edit.clear()
            self.model_edit.clear()
            self.color_edit.clear()
            self.refresh()
            show_info(self, "მანქანა", "მანქანა წარმატებით დაემატა")
        except (ValueError, TypeError) as exc:
            show_error(self, "მანქანა", exc)

    def _remove_car(self):
        user = self.store.current_user
        row = self.cars_table.currentRow()
        if row < 0:
            show_error(self, "წაშლა", ValueError("აირჩიეთ მანქანა ცხრილში"))
            return
        plate_item = self.cars_table.item(row, 0)
        if not plate_item:
            show_error(self, "წაშლა", ValueError("სანომრე ვერ მოიძებნა"))
            return
        plate = plate_item.text().strip()

        # Prevent deletion if there are upcoming bookings for this car
        upcoming_for_car = [b for b in self._all_upcoming() if b.car.plate.upper() == plate.upper()]
        if upcoming_for_car:
            show_error(self, "წაშლა", ValueError("ამ მანქანაზე აქტიური ჯავშანია — ჯერ გააუქმეთ ჯავშნები"))
            return
        try:
            remove_car(user, plate)
            # Also remove related bookings from in-memory stations history for consistency
            for st in self.store.stations:
                st.bookings = [b for b in st.bookings if not (b.customer == user and b.car.plate.upper() == plate.upper())]
            self.refresh()
            show_info(self, "წაშლა", f"მანქანა {plate} წაიშალა")
        except (ValueError, TypeError) as exc:
            show_error(self, "წაშლა", exc)

    def _filter_stations(self):
        district = self.district_filter.text().strip()
        if not district:
            self._populate_stations(self.store.stations)
            return
        filtered = find_stations_by_district(self.store.stations, district)
        self._populate_stations(filtered)
        if not filtered:
            show_info(self, "ძებნა", "ამ რაიონში სადგური ვერ მოიძებნა")

    def _filter_self_service(self):
        filtered = find_self_service_stations(self.store.stations)
        self._populate_stations(filtered)

    def _create_booking(self):
        user = self.store.current_user
        station = self.station_combo.currentData()
        car = self.car_combo.currentData()
        if not station or not car:
            show_error(self, "ჯავშანი", ValueError("აირჩიეთ სადგური და მანქანა"))
            return

        date = self.date_edit.date().toPyDate()
        time = self.time_edit.time().toPyTime()
        booking_type = self.type_combo.currentData()

        try:
            booking, price = create_booking(
                user, station, car, date, time, booking_type
            )
            self.refresh()
            show_info(
                self,
                "ჯავშანი",
                f"ჯავშანი დადასტურებულია!\n{booking}\nფასი: {price}₾",
            )
        except (ValueError, TypeError) as exc:
            show_error(self, "ჯავშანი", exc)

    def _all_upcoming(self):
        user = self.store.current_user
        upcoming = []
        for station in self.store.stations:
            upcoming.extend(get_customer_upcoming_bookings(user, station))
        return sorted(upcoming)

    def _refresh_upcoming(self):
        self.upcoming_table.setRowCount(0)
        self._upcoming_bookings = self._all_upcoming()
        for booking in self._upcoming_bookings:
            row = self.upcoming_table.rowCount()
            self.upcoming_table.insertRow(row)
            price = calculate_booking_price(booking)
            self.upcoming_table.setItem(row, 0, QTableWidgetItem(booking.station.name))
            self.upcoming_table.setItem(row, 1, QTableWidgetItem(booking.car.plate))
            self.upcoming_table.setItem(row, 2, QTableWidgetItem(str(booking.date)))
            self.upcoming_table.setItem(row, 3, QTableWidgetItem(booking.time.strftime("%H:%M")))
            self.upcoming_table.setItem(
                row, 4, QTableWidgetItem(BOOKING_TYPE_LABELS.get(booking.booking_type, booking.booking_type))
            )
            self.upcoming_table.setItem(
                row, 5, QTableWidgetItem(STATUS_LABELS.get(booking.status, booking.status))
            )
            self.upcoming_table.setItem(row, 6, QTableWidgetItem(f"{price}₾"))

    def _cancel_booking(self):
        row = self.upcoming_table.currentRow()
        if row < 0 or row >= len(self._upcoming_bookings):
            show_error(self, "გაუქმება", ValueError("აირჩიეთ ჯავშანი"))
            return
        booking = self._upcoming_bookings[row]
        try:
            fee = cancel_booking(booking)
            msg = "ჯავშანი გაუქმებულია"
            if fee:
                msg += f"\nგვიანი გაუქმების ჯარიმა: {fee}₾"
            self.refresh()
            show_info(self, "გაუქმება", msg)
        except (ValueError, PermissionError) as exc:
            show_error(self, "გაუქმება", exc)

    def _refresh_history(self):
        user = self.store.current_user
        self.history_table.setRowCount(0)
        for station in self.store.stations:
            for booking in get_customer_history(user, station):
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                price = calculate_booking_price(booking)
                self.history_table.setItem(row, 0, QTableWidgetItem(booking.station.name))
                self.history_table.setItem(row, 1, QTableWidgetItem(booking.car.plate))
                self.history_table.setItem(row, 2, QTableWidgetItem(str(booking.date)))
                self.history_table.setItem(
                    row, 3, QTableWidgetItem(BOOKING_TYPE_LABELS.get(booking.booking_type, booking.booking_type))
                )
                self.history_table.setItem(row, 4, QTableWidgetItem(f"{price}₾"))


class StaffDashboard(QWidget):
    def __init__(self, store: AppStore):
        super().__init__()
        self.store = store
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.header = QLabel()
        self.header.setObjectName("dashboardHeader")
        self.header.setWordWrap(True)
        layout.addWidget(self.header)

        stats_group = QGroupBox("📊 სტატისტიკა")
        stats_layout = QFormLayout(stats_group)
        self.daily_count_label = QLabel("0")
        stats_layout.addRow("დღევანდელი ჯავშნები:", self.daily_count_label)
        layout.addWidget(stats_group)

        self.bookings_table = QTableWidget(0, 7)
        self.bookings_table.setHorizontalHeaderLabels(
            ["კლიენტი", "მანქანა", "თარიღი", "დრო", "ტიპი", "სტატუსი", "ფასი"]
        )
        configure_table(self.bookings_table)
        layout.addWidget(self.bookings_table)

        complete_btn = QPushButton("არჩეული ჯავშნის დასრულება")
        complete_btn.setObjectName("primaryBtn")
        complete_btn.clicked.connect(self._complete_booking)
        layout.addWidget(complete_btn)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def refresh(self):
        user = self.store.current_user
        station = self.store.station_for_staff(user)
        if not station:
            self.header.setText(f"<b>{user.name}</b> — {user.get_dashboard()}<br>სადგური ვერ მოიძებნა")
            return

        self.header.setText(
            f"<b>{user.name}</b> — {user.get_dashboard()}<br>"
            f"სადგური: {station}"
        )

        try:
            count = daily_booking_count(user, station)
            self.daily_count_label.setText(str(count))
        except PermissionError as exc:
            show_error(self, "წვდომა", exc)

        today = datetime.date.today()
        station_bookings = station.bookings_for_date(today)
        self._station_bookings = [b for b in station_bookings if b.status != "cancelled"]
        self.bookings_table.setRowCount(0)

        for booking in self._station_bookings:
            row = self.bookings_table.rowCount()
            self.bookings_table.insertRow(row)
            price = calculate_booking_price(booking)
            self.bookings_table.setItem(row, 0, QTableWidgetItem(booking.customer.name))
            self.bookings_table.setItem(row, 1, QTableWidgetItem(booking.car.plate))
            self.bookings_table.setItem(row, 2, QTableWidgetItem(str(booking.date)))
            self.bookings_table.setItem(row, 3, QTableWidgetItem(booking.time.strftime("%H:%M")))
            self.bookings_table.setItem(
                row, 4, QTableWidgetItem(BOOKING_TYPE_LABELS.get(booking.booking_type, booking.booking_type))
            )
            self.bookings_table.setItem(
                row, 5, QTableWidgetItem(STATUS_LABELS.get(booking.status, booking.status))
            )
            self.bookings_table.setItem(row, 6, QTableWidgetItem(f"{price}₾"))

    def _complete_booking(self):
        row = self.bookings_table.currentRow()
        if row < 0 or row >= len(self._station_bookings):
            show_error(self, "დასრულება", ValueError("აირჩიეთ ჯავშანი"))
            return
        booking = self._station_bookings[row]
        if booking.status == "completed":
            show_error(self, "დასრულება", ValueError("ეს ჯავშანი უკვე დასრულებულია"))
            return
        try:
            complete_booking(self.store.current_user, booking)
            self.refresh()
            show_info(self, "დასრულება", f"ჯავშანი დასრულებულია: {booking.car.plate}")
        except PermissionError as exc:
            show_error(self, "დასრულება", exc)


class AdminDashboard(QWidget):
    def __init__(self, store: AppStore):
        super().__init__()
        self.store = store
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.header = QLabel()
        self.header.setObjectName("dashboardHeader")
        self.header.setWordWrap(True)
        layout.addWidget(self.header)

        tabs = QTabWidget()

        # Stations overview
        stations_tab = QWidget()
        stations_layout = QVBoxLayout(stations_tab)
        self.stations_table = QTableWidget(0, 5)
        self.stations_table.setHorizontalHeaderLabels(
            ["სახელი", "მისამართი", "რაიონი", "შემოსავალი", "პოპულარული სერვისი"]
        )
        configure_table(self.stations_table)
        stations_layout.addWidget(self.stations_table)
        tabs.addTab(stations_tab, "🏢 სადგურები")

        # All bookings
        bookings_tab = QWidget()
        bookings_layout = QVBoxLayout(bookings_tab)
        self.bookings_table = QTableWidget(0, 8)
        self.bookings_table.setHorizontalHeaderLabels(
            ["სადგური", "კლიენტი", "მანქანა", "თარიღი", "დრო", "ტიპი", "სტატუსი", "ფასი"]
        )
        configure_table(self.bookings_table)
        bookings_layout.addWidget(self.bookings_table)
        tabs.addTab(bookings_tab, "ყველა ჯავშანი")

        # Staff management
        staff_tab = QWidget()
        staff_layout = QVBoxLayout(staff_tab)
        form = QFormLayout()
        self.staff_name = QLineEdit()
        self.staff_email = QLineEdit()
        self.staff_phone = QLineEdit()
        self.staff_phone.setPlaceholderText("555123456")
        self.staff_password = QLineEdit()
        self.staff_password.setEchoMode(QLineEdit.Password)
        self.staff_station = QComboBox()
        for i, station in enumerate(self.store.stations, start=1):
            self.staff_station.addItem(f"#{i} — {station.name}", i)
        form.addRow("სახელი:", self.staff_name)
        form.addRow("ელ-ფოსტა:", self.staff_email)
        form.addRow("ტელეფონი:", self.staff_phone)
        form.addRow("პაროლი:", self.staff_password)
        form.addRow("სადგური:", self.staff_station)
        staff_layout.addLayout(form)
        add_staff_btn = QPushButton("პერსონალის დამატება")
        add_staff_btn.setObjectName("primaryBtn")
        add_staff_btn.clicked.connect(self._add_staff)
        staff_layout.addWidget(add_staff_btn)
        staff_layout.addStretch()
        tabs.addTab(staff_tab, "პერსონალი")

        layout.addWidget(tabs)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def refresh(self):
        user = self.store.current_user
        self.header.setText(f"<b>{user.name}</b> — {user.get_dashboard()}")

        self.stations_table.setRowCount(0)
        for station in self.store.stations:
            try:
                revenue = total_revenue(user, station)
                popular = most_popular_service(user, station)
                popular_label = BOOKING_TYPE_LABELS.get(popular, popular)
            except PermissionError:
                revenue, popular_label = 0, "—"

            row = self.stations_table.rowCount()
            self.stations_table.insertRow(row)
            self.stations_table.setItem(row, 0, QTableWidgetItem(station.name))
            self.stations_table.setItem(row, 1, QTableWidgetItem(station.address))
            self.stations_table.setItem(row, 2, QTableWidgetItem(station.district))
            self.stations_table.setItem(row, 3, QTableWidgetItem(f"{revenue}₾"))
            self.stations_table.setItem(row, 4, QTableWidgetItem(popular_label))

        self.bookings_table.setRowCount(0)
        for booking in self.store.all_bookings():
            row = self.bookings_table.rowCount()
            self.bookings_table.insertRow(row)
            price = calculate_booking_price(booking) if booking.status == "completed" else "—"
            self.bookings_table.setItem(row, 0, QTableWidgetItem(booking.station.name))
            self.bookings_table.setItem(row, 1, QTableWidgetItem(booking.customer.name))
            self.bookings_table.setItem(row, 2, QTableWidgetItem(booking.car.plate))
            self.bookings_table.setItem(row, 3, QTableWidgetItem(str(booking.date)))
            self.bookings_table.setItem(row, 4, QTableWidgetItem(booking.time.strftime("%H:%M")))
            self.bookings_table.setItem(
                row, 5, QTableWidgetItem(BOOKING_TYPE_LABELS.get(booking.booking_type, booking.booking_type))
            )
            self.bookings_table.setItem(
                row, 6, QTableWidgetItem(STATUS_LABELS.get(booking.status, booking.status))
            )
            price_text = f"{price}₾" if isinstance(price, float) else price
            self.bookings_table.setItem(row, 7, QTableWidgetItem(price_text))

    def _add_staff(self):
        try:
            staff = self.store.register_new_staff(
                self.staff_name.text().strip(),
                self.staff_email.text().strip(),
                self.staff_phone.text().strip(),
                self.staff_password.text().strip(),
                self.staff_station.currentData(),
            )
            self.staff_name.clear()
            self.staff_email.clear()
            self.staff_phone.clear()
            self.staff_password.clear()
            show_info(self, "პერსონალი", f"პერსონალი დაემატა: {staff.name} ({staff.email})")
        except (ValueError, TypeError) as exc:
            show_error(self, "პერსონალი", exc)


class LoyaltyProgressBar(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        tier, next_tier, min_pts, max_pts, current_pts = user.get_loyalty_info()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Labels
        label_layout = QHBoxLayout()
        current_tier_label = QLabel(f"Current Status: {tier}")
        current_tier_label.setStyleSheet(f"font-weight: bold; color: {COLOR_ACCENT}; font-size: 14px;")
        
        points_text = f"{current_pts} pts"
        if next_tier != "Max":
            points_text += f" ({max_pts - current_pts} till {next_tier})"
        else:
            points_text = f"{current_pts} pts (Max Tier reached!)"
        
        points_label = QLabel(points_text)
        points_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        
        label_layout.addWidget(current_tier_label)
        label_layout.addStretch()
        label_layout.addWidget(points_label)
        layout.addLayout(label_layout)

        # Progress Bar
        self.bar = QProgressBar()
        if next_tier == "Max":
            self.bar.setRange(0, 100)
            self.bar.setValue(100)
        else:
            self.bar.setRange(min_pts, max_pts)
            self.bar.setValue(current_pts)
            
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(14)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_ELEVATED};
                border: 1px solid {COLOR_BORDER};
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.bar)


class ProfilePage(QWidget):
    def __init__(self, store: AppStore, on_back, on_logout):
        super().__init__()
        self.store = store
        self.on_back = on_back
        self.on_logout = on_logout
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header
        header_layout = QHBoxLayout()
        back_btn = QPushButton("← უკან")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.on_back)
        header_layout.addWidget(back_btn)
        
        title = QLabel("პროფილის პარამეტრები")
        title.setStyleSheet("font-size: 28px; font-weight: bold; margin-left: 20px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        content = QHBoxLayout()
        layout.addLayout(content)

        # Left Column: Profile Pic & Tiers
        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        
        self.pic_label = QLabel()
        self.pic_label.setFixedSize(180, 180)
        self.pic_label.setStyleSheet(f"border: 2px solid {COLOR_BORDER}; border-radius: 90px; background: {COLOR_SURFACE};")
        self.pic_label.setAlignment(Qt.AlignCenter)
        left_col.addWidget(self.pic_label, 0, Qt.AlignCenter)

        change_pic_btn = QPushButton("სურათის შეცვლა")
        change_pic_btn.clicked.connect(self._change_pic)
        left_col.addWidget(change_pic_btn, 0, Qt.AlignCenter)

        self.delete_pic_btn = QPushButton("სურათის წაშლა")
        self.delete_pic_btn.setStyleSheet("color: #ff4d4d;")
        self.delete_pic_btn.clicked.connect(self._delete_pic)
        left_col.addWidget(self.delete_pic_btn, 0, Qt.AlignCenter)

        # Loyalty Section
        self.loyalty_group = QGroupBox("ლოიალობის სისტემა")
        self.loyalty_layout = QVBoxLayout(self.loyalty_group)
        left_col.addWidget(self.loyalty_group)
        
        content.addLayout(left_col, 1)

        # Right Column: Personal Info & Settings
        right_col = QVBoxLayout()
        right_col.setSpacing(20)

        info_group = QGroupBox("პირადი ინფორმაცია")
        info_form = QFormLayout(info_group)
        self.name_label = QLabel()
        self.email_label = QLabel()
        self.phone_label = QLabel()
        self.balance_label = QLabel()
        self.points_label = QLabel()
        
        info_form.addRow("სახელი:", self.name_label)
        info_form.addRow("ელფოსტა:", self.email_label)
        info_form.addRow("ტელეფონი:", self.phone_label)
        info_form.addRow("ბალანსი:", self.balance_label)
        info_form.addRow("ქულები:", self.points_label)
        
        self.verify_btn = QPushButton("იმეილის ვერიფიკაცია")
        self.verify_btn.setObjectName("primaryBtn")
        self.verify_btn.clicked.connect(self._verify_email)
        info_form.addRow(self.verify_btn)
        
        right_col.addWidget(info_group)

        settings_group = QGroupBox("უსაფრთხოება და ანგარიში")
        settings_layout = QVBoxLayout(settings_group)
        
        self.two_fa_cb = QCheckBox("2FA ავტორიზაციის ჩართვა")
        self.two_fa_cb.toggled.connect(self._toggle_2fa)
        settings_layout.addWidget(self.two_fa_cb)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        settings_layout.addItem(spacer)

        delete_btn = QPushButton("ანგარიშის წაშლა")
        delete_btn.setStyleSheet("background-color: #ff4d4d; color: white; border: none;")
        delete_btn.clicked.connect(self._delete_account)
        settings_layout.addWidget(delete_btn)
        
        right_col.addWidget(settings_group)
        content.addLayout(right_col, 2)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def refresh(self):
        user = self.store.current_user
        if not user: return

        self.name_label.setText(user.name)
        self.email_label.setText(user.email)
        self.phone_label.setText(user.phone)
        self.balance_label.setText(f"{user.balance} ₾")
        self.points_label.setText(f"{user.points} pts")
        
        self.two_fa_cb.blockSignals(True)
        self.two_fa_cb.setChecked(user.is_2fa_enabled)
        self.two_fa_cb.blockSignals(False)

        self.verify_btn.setVisible(not user.is_verified)

        # Refresh Picture
        pm = QPixmap(user.profile_picture) if user.profile_picture else QPixmap()
        self.pic_label.setPixmap(_make_circular_pixmap(pm, 180))
        if user.profile_picture and not pm.isNull():
            self.delete_pic_btn.show()
        else:
            self.delete_pic_btn.hide()

        # Refresh Loyalty Bar
        for i in reversed(range(self.loyalty_layout.count())): 
            item = self.loyalty_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        if user.role == "customer":
            self.loyalty_layout.addWidget(LoyaltyProgressBar(user))
            self.loyalty_group.show()
        else:
            self.loyalty_group.hide()

    def _change_pic(self):
        path, _ = QFileDialog.getOpenFileName(self, "აირჩიეთ სურათი", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.store.current_user.profile_picture = path
            database.save_user(self.store.current_user)
            self.refresh()
            # Refresh avatar in top bar if available
            win = self.window()
            if hasattr(win, "_refresh_top_bar_user"):
                win._refresh_top_bar_user()

    def _delete_pic(self):
        self.store.current_user.profile_picture = None
        database.save_user(self.store.current_user)
        self.refresh()
        win = self.window()
        if hasattr(win, "_refresh_top_bar_user"):
            win._refresh_top_bar_user()

    def _toggle_2fa(self, enabled):
        self.store.current_user.is_2fa_enabled = enabled
        database.save_user(self.store.current_user)
        status = "ჩაირთო" if enabled else "გაითიშა"
        show_info(self, "2FA", f"2FA წარმატებით {status}")

    def _verify_email(self):
        try:
            initiate_email_verification(self.store.current_user)
            dlg = VerificationDialog(self.store.current_user.email, self)
            if dlg.exec_():
                code = dlg.get_code()
                if verify_email(self.store.current_user, code):
                    show_info(self, "ვერიფიკაცია", "იმეილი წარმატებით დადასტურდა!")
                    self.refresh()
                else:
                    show_error(self, "ვერიფიკაცია", "არასწორი კოდი")
        except Exception as e:
            show_error(self, "შეცდომა", e)

    def _delete_account(self):
        reply = QMessageBox.question(self, "ანგარიშის წაშლა", "დარწმუნებული ხართ, რომ გსურთ ანგარიშის წაშლა? ეს ქმედება შეუქცევადია.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.delete_user(self.store.current_user)
            self.on_logout()


def create_app_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(COLOR_ACCENT))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, 64, 64, 16, 16)
    painter.setPen(QColor(COLOR_BG))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(24)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "CW")
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self, store: AppStore):
        super().__init__()
        self.store = store
        self.setWindowTitle("Car Wash — Premium Management")
        self.setWindowIcon(create_app_icon())
        self.resize(1100, 720)
        self.setMinimumSize(900, 650)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        top_bar_frame = QFrame()
        top_bar_frame.setObjectName("topBar")
        self.top_bar_frame = top_bar_frame
        top_bar = QHBoxLayout(top_bar_frame)
        top_bar.setContentsMargins(20, 10, 20, 10)
        top_bar.setSpacing(12)
        self.user_label = QLabel()
        self.user_label.setObjectName("userLabel")
        top_bar.addWidget(self.user_label)
        top_bar.addStretch()
        logout_btn = QPushButton("გასვლა")
        logout_btn.setObjectName("secondaryBtn")
        logout_btn.clicked.connect(self._logout)
        top_bar.addWidget(logout_btn)

        profile_btn = QPushButton("პროფილი")
        profile_btn.setObjectName("secondaryBtn")
        profile_btn.clicked.connect(self._show_profile)
        top_bar.addWidget(profile_btn)

        # Avatar to the right of profile button
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(44, 44)
        self.avatar_label.setStyleSheet(f"border: 2px solid {COLOR_BORDER}; border-radius: 22px; background: {COLOR_ELEVATED};")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        top_bar.addWidget(self.avatar_label)

        root.addWidget(top_bar_frame)

        self.stack = QStackedWidget()
        self.login_page = LoginPage(store, self._on_login)
        self.customer_dashboard = CustomerDashboard(store)
        self.staff_dashboard = StaffDashboard(store)
        self.admin_dashboard = AdminDashboard(store)
        self.profile_page = ProfilePage(store, self._back_from_profile, self._logout)

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.customer_dashboard)
        self.stack.addWidget(self.staff_dashboard)
        self.stack.addWidget(self.admin_dashboard)
        self.stack.addWidget(self.profile_page)
        root.addWidget(self.stack)

        self._apply_styles()
        self.top_bar_frame.hide()
        self.stack.setCurrentWidget(self.login_page)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, #centralWidget, QDialog {{
                background-color: {COLOR_BG};
                color: {COLOR_TEXT};
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_BASE}px;
            }}

            QWidget {{
                color: {COLOR_TEXT};
            }}

            #topBar {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 16px;
            }}

            #userLabel {{
                color: {COLOR_TEXT_MUTED};
                font-size: {FONT_SIZE_SMALL}px;
                font-weight: 500;
            }}

            #loginCard, #registerDialog {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 20px;
            }}

            #appTitle {{
                color: {COLOR_ACCENT};
                font-size: {FONT_SIZE_TITLE}px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}

            #subtitle, #hint {{
                color: {COLOR_TEXT_MUTED};
                font-size: {FONT_SIZE_SMALL}px;
            }}

            #dashboardHeader {{
                font-size: {FONT_SIZE_BASE}px;
                color: {COLOR_TEXT};
                padding: 4px 2px 8px 2px;
                font-weight: bold;
            }}

            QLabel {{
                background: transparent;
            }}

            /* Buttons */
            QPushButton {{
                background-color: {COLOR_ELEVATED};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: 600;
                font-size: {FONT_SIZE_BASE}px;
                min-height: 40px;
            }}

            QPushButton:hover {{
                background-color: {COLOR_HOVER};
                border-color: {COLOR_TEXT_MUTED};
            }}

            QPushButton:pressed {{
                background-color: {COLOR_BG};
            }}

            #primaryBtn {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_ACCENT_TEXT};
                border: none;
                padding: 12px 24px;
                border-radius: 12px;
                min-height: 44px;
            }}

            #primaryBtn:hover {{
                background-color: {COLOR_TEXT};
                color: {COLOR_BG};
            }}

            #secondaryBtn {{
                background-color: transparent;
                border: 1px solid {COLOR_BORDER};
            }}
            
            #secondaryBtn:hover {{
                background-color: {COLOR_ELEVATED};
            }}

            /* Groups & Tabs */
            QGroupBox {{
                font-weight: 600;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 16px;
                margin-top: 14px;
                padding: 20px 16px 12px 16px;
                background-color: {COLOR_SURFACE};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: {COLOR_TEXT_MUTED};
            }}

            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDER};
                background-color: {COLOR_SURFACE};
                border-radius: 16px;
                top: -1px;
                padding: 10px;
            }}

            QTabBar::tab {{
                background-color: transparent;
                color: {COLOR_TEXT_MUTED};
                padding: 10px 20px;
                margin-right: 4px;
                border-radius: 10px;
                font-weight: 500;
            }}

            QTabBar::tab:selected {{
                background-color: {COLOR_ELEVATED};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
            }}

            QTabBar::tab:hover:!selected {{
                background-color: {COLOR_HOVER};
            }}

            /* Tables */
            QTableWidget {{
                background-color: {COLOR_SURFACE};
                alternate-background-color: {COLOR_ELEVATED};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
                gridline-color: {COLOR_BORDER};
                selection-background-color: {COLOR_HOVER};
                outline: none;
            }}

            QHeaderView::section {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_MUTED};
                border: none;
                border-bottom: 1px solid {COLOR_BORDER};
                padding: 10px;
                font-weight: 600;
            }}

            /* Inputs */
            QLineEdit, QComboBox, QDateEdit, QTimeEdit {{
                background-color: {COLOR_ELEVATED};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 10px 14px;
            }}

            QLineEdit:focus, QComboBox:focus {{
                border-color: {COLOR_TEXT_MUTED};
            }}

            /* ScrollBars */
            QScrollBar:vertical {{
                background: {COLOR_BG};
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLOR_BORDER};
                border-radius: 6px;
                min-height: 20px;
            }}
        """)

    def _on_login(self, user):
        self.store.current_user = user
        self.top_bar_frame.show()
        self._refresh_top_bar_user()

        if user.role == "customer":
            self.customer_dashboard.refresh()
            self.stack.setCurrentWidget(self.customer_dashboard)
        elif user.role == "staff":
            self.staff_dashboard.refresh()
            self.stack.setCurrentWidget(self.staff_dashboard)
        elif user.role == "admin":
            self.admin_dashboard.refresh()
            self.stack.setCurrentWidget(self.admin_dashboard)

    def _logout(self):
        self.store.logout()
        self.user_label.clear()
        self.top_bar_frame.hide()
        self.stack.setCurrentWidget(self.login_page)

    def _show_profile(self):
        self.profile_page.refresh()
        self._refresh_top_bar_user()
        self.stack.setCurrentWidget(self.profile_page)

    def _back_from_profile(self):
        user = self.store.current_user
        if not user:
            self.stack.setCurrentWidget(self.login_page)
            return

        self._refresh_top_bar_user()

        if user.role == "customer":
            self.stack.setCurrentWidget(self.customer_dashboard)
        elif user.role == "staff":
            self.stack.setCurrentWidget(self.staff_dashboard)
        elif user.role == "admin":
            self.stack.setCurrentWidget(self.admin_dashboard)

    def _refresh_top_bar_user(self):
        user = self.store.current_user
        if not user:
            self.user_label.clear()
            self.avatar_label.clear()
            return
        self.user_label.setText(f"მომხმარებელი: {user}  |  {user.get_dashboard()}")
        if user.profile_picture:
            pm = QPixmap(user.profile_picture)
        else:
            pm = QPixmap()
        self.avatar_label.setPixmap(_make_circular_pixmap(pm, 44))


def run_app():
    import sys

    app = QApplication(sys.argv)
    setup_app_font(app)
    store = AppStore()
    window = MainWindow(store)
    window.show()
    sys.exit(app.exec_())
