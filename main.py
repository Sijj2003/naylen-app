import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QCalendarWidget, QInputDialog, QGridLayout, QMessageBox, QTabWidget, QTextEdit, QComboBox,
                             QDialog)
from PyQt5.QtCore import QDate, QSize, Qt
from PyQt5.QtGui import QIcon, QTextCharFormat, QColor
import sqlite3
from database import setup_database
from reporte import get_report_data, generate_pdf_report
import calendar
import hashlib

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar Sesión")
        self.setGeometry(600, 400, 300, 150)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Ingrese la contraseña:")
        layout.addWidget(self.label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.check_password)
        layout.addWidget(self.password_input)
        
        self.login_button = QPushButton("Ingresar")
        self.login_button.clicked.connect(self.check_password)
        layout.addWidget(self.login_button)
        
        self.setLayout(layout)

    def check_password(self):
        # Contraseña en texto plano
        password_correcta = "28042003"
        password_ingresada = self.password_input.text()
        
        if password_ingresada == password_correcta:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Contraseña incorrecta. Por favor, inténtelo de nuevo.")
            self.password_input.clear()
            self.password_input.setFocus()

class ProyectoSistemaPromotoras(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sistema de Gestión de Promotoras')
        self.setGeometry(100, 100, 900, 700)
        self.current_promotora_id = None
        setup_database()
        self.init_ui()
        self.load_promotoras()
        
    def init_ui(self):
        main_layout = QHBoxLayout()

        # Panel izquierdo: Mis Promotoras
        panel_izquierdo = QVBoxLayout()
        panel_izquierdo.addWidget(QLabel('<h3>Mis Promotoras</h3>'))
        
        promotora_ops_layout = QHBoxLayout()
        self.promotora_input = QLineEdit()
        self.promotora_input.setPlaceholderText('Nombre de la nueva promotora')
        add_promotora_btn = QPushButton('Añadir')
        add_promotora_btn.clicked.connect(self.add_promotora)
        promotora_ops_layout.addWidget(self.promotora_input)
        promotora_ops_layout.addWidget(add_promotora_btn)
        
        panel_izquierdo.addLayout(promotora_ops_layout)
        
        self.promotora_list = QListWidget()
        self.promotora_list.itemClicked.connect(self.select_promotora)
        panel_izquierdo.addWidget(self.promotora_list)
        
        promotora_actions_layout = QHBoxLayout()
        edit_btn = QPushButton('Editar')
        edit_btn.clicked.connect(self.edit_promotora)
        delete_btn = QPushButton('Eliminar')
        delete_btn.clicked.connect(self.delete_promotora)
        promotora_actions_layout.addWidget(edit_btn)
        promotora_actions_layout.addWidget(delete_btn)
        panel_izquierdo.addLayout(promotora_actions_layout)
        
        main_layout.addLayout(panel_izquierdo, 1)

        # Panel derecho: Detalles de la Promotora con pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setEnabled(False) 
        
        # Pestaña 1: Perfil de Promotora
        self.profile_tab = QWidget()
        self.profile_tab.setLayout(QVBoxLayout())
        self.promotora_title = QLabel('')
        self.promotora_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.profile_tab.layout().addWidget(self.promotora_title)
        
        profile_form_layout = QGridLayout()
        profile_form_layout.addWidget(QLabel('Inventario Inicial (Cajas):'), 0, 0)
        self.inventario_cajas_input = QLineEdit()
        profile_form_layout.addWidget(self.inventario_cajas_input, 0, 1)
        
        profile_form_layout.addWidget(QLabel('Unidades por Caja:'), 1, 0)
        self.unidades_por_caja_input = QLineEdit()
        profile_form_layout.addWidget(self.unidades_por_caja_input, 1, 1)

        profile_form_layout.addWidget(QLabel('Comercio:'), 2, 0)
        self.comercio_input = QLineEdit()
        profile_form_layout.addWidget(self.comercio_input, 2, 1)

        self.save_profile_btn = QPushButton('Guardar Perfil')
        self.save_profile_btn.clicked.connect(self.save_promotora_profile)
        profile_form_layout.addWidget(self.save_profile_btn, 3, 1)
        self.profile_tab.layout().addLayout(profile_form_layout)
        
        self.tab_widget.addTab(self.profile_tab, "Perfil")
        
        # Pestaña 2: Registro de Ventas
        self.sales_tab = QWidget()
        self.sales_tab.setLayout(QVBoxLayout())
        self.sales_tab.layout().addWidget(QLabel('<h3>Combos Colocados (Día a Día)</h3>'))
        
        ventas_layout = QVBoxLayout()
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.selectionChanged.connect(self.show_daily_sale)
        ventas_layout.addWidget(self.calendar_widget)
        
        ventas_registro_layout = QGridLayout()
        ventas_registro_layout.addWidget(QLabel('Cantidad (Combos):'), 0, 0)
        self.combos_input = QLineEdit()
        self.combos_input.setPlaceholderText('Ingrese la cantidad de combos')
        ventas_registro_layout.addWidget(self.combos_input, 0, 1)
        
        self.save_venta_btn = QPushButton('Guardar Venta del Día')
        self.save_venta_btn.clicked.connect(self.save_daily_sale)
        ventas_registro_layout.addWidget(self.save_venta_btn, 1, 1)
        
        ventas_layout.addLayout(ventas_registro_layout)
        self.sales_tab.layout().addLayout(ventas_layout)
        
        self.tab_widget.addTab(self.sales_tab, "Ventas")

        # Pestaña 3: Resumen de Operaciones
        self.summary_tab = QWidget()
        self.summary_tab.setLayout(QVBoxLayout())
        self.summary_text_area = QTextEdit()
        self.summary_text_area.setReadOnly(True)
        self.summary_tab.layout().addWidget(self.summary_text_area)
        self.tab_widget.addTab(self.summary_tab, "Resumen de Operaciones")

        # Botones de informe
        reporte_layout = QHBoxLayout()
        generate_report_btn = QPushButton('Generar Informe en PDF')
        generate_report_btn.clicked.connect(self.generate_report)
        reporte_layout.addWidget(generate_report_btn)
        
        main_layout.addWidget(self.tab_widget, 2)
        main_layout.addLayout(reporte_layout)
        self.setLayout(main_layout)

    def load_promotoras(self):
        self.promotora_list.clear()
        conn = sqlite3.connect('sistema_promotoras.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM promotoras")
        promotoras = cursor.fetchall()
        conn.close()
        for p_id, p_nombre in promotoras:
            item = QListWidgetItem(p_nombre)
            item.setData(1, p_id)
            self.promotora_list.addItem(item)
    
    def add_promotora(self):
        nombre = self.promotora_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, 'Error', 'El nombre no puede estar vacío.')
            return
        
        conn = sqlite3.connect('sistema_promotoras.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO promotoras (nombre) VALUES (?)", (nombre,))
        conn.commit()
        conn.close()
        QMessageBox.information(self, 'Éxito', 'Promotora añadida con éxito.')
        self.promotora_input.clear()
        self.load_promotoras()
        
    def edit_promotora(self):
        selected_item = self.promotora_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, 'Error', 'Seleccione una promotora para editar.')
            return
        
        promotora_id = selected_item.data(1)
        old_name = selected_item.text()
        new_name, ok = QInputDialog.getText(self, 'Editar Promotora', 'Nuevo nombre:', QLineEdit.Normal, old_name)
        
        if ok and new_name.strip():
            conn = sqlite3.connect('sistema_promotoras.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE promotoras SET nombre = ? WHERE id = ?", (new_name.strip(), promotora_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, 'Éxito', 'Promotora actualizada.')
            self.load_promotoras()

    def delete_promotora(self):
        selected_item = self.promotora_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, 'Error', 'Seleccione una promotora para eliminar.')
            return

        promotora_id = selected_item.data(1)
        confirm = QMessageBox.question(self, 'Confirmar Eliminación', '¿Está seguro que desea eliminar esta promotora y sus datos?', QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            conn = sqlite3.connect('sistema_promotoras.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM promotoras WHERE id = ?", (promotora_id,))
            cursor.execute("DELETE FROM ventas WHERE promotora_id = ?", (promotora_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, 'Éxito', 'Promotora eliminada.')
            self.load_promotoras()
            self.tab_widget.setEnabled(False)
            self.summary_text_area.setText("Seleccione una promotora para ver el resumen.")

    def select_promotora(self, item):
        self.current_promotora_id = item.data(1)
        self.promotora_title.setText(item.text())
        self.tab_widget.setEnabled(True)
        self.load_promotora_profile()
        self.load_summary_report()
        self.highlight_sales_dates()

    def load_promotora_profile(self):
        conn = sqlite3.connect('sistema_promotoras.db')
        cursor = conn.cursor()
        cursor.execute("SELECT inventario_inicial, unidades_por_caja, comercio FROM promotoras WHERE id = ?", (self.current_promotora_id,))
        data = cursor.fetchone()
        conn.close()

        if data:
            self.inventario_cajas_input.setText(str(data[0]) if data[0] is not None else '')
            self.unidades_por_caja_input.setText(str(data[1]) if data[1] is not None else '')
            self.comercio_input.setText(data[2] if data[2] else '')
        else:
            self.inventario_cajas_input.clear()
            self.unidades_por_caja_input.clear()
            self.comercio_input.clear()

        self.show_daily_sale()
        self.highlight_sales_dates()

    def highlight_sales_dates(self):
        """Resalta las fechas con ventas en el calendario."""
        if not self.current_promotora_id:
            return
        
        # Primero, borra el formato de todas las fechas para evitar residuos
        default_format = QTextCharFormat()
        self.calendar_widget.setDateTextFormat(QDate(), default_format)

        conn = sqlite3.connect('sistema_promotoras.db')
        cursor = conn.cursor()
        cursor.execute("SELECT fecha FROM ventas WHERE promotora_id = ?", (self.current_promotora_id,))
        sales_dates = cursor.fetchall()
        conn.close()

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("lightgreen"))

        for date_str in sales_dates:
            date_qdate = QDate.fromString(date_str[0], "yyyy-MM-dd")
            self.calendar_widget.setDateTextFormat(date_qdate, highlight_format)

    def save_promotora_profile(self):
        if not self.current_promotora_id:
            QMessageBox.warning(self, 'Error', 'Seleccione una promotora.')
            return
        
        try:
            cajas = int(self.inventario_cajas_input.text()) if self.inventario_cajas_input.text() else None
            unidades = int(self.unidades_por_caja_input.text()) if self.unidades_por_caja_input.text() else None
            comercio = self.comercio_input.text().strip()
            
            conn = sqlite3.connect('sistema_promotoras.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE promotoras SET inventario_inicial = ?, unidades_por_caja = ?, comercio = ? WHERE id = ?",
                           (cajas, unidades, comercio, self.current_promotora_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, 'Éxito', 'Perfil de promotora actualizado.')
            self.load_summary_report()
            self.highlight_sales_dates()
        except ValueError:
            QMessageBox.warning(self, 'Error', 'Inventario y unidades deben ser números.')
            
    def save_daily_sale(self):
        if not self.current_promotora_id:
            QMessageBox.warning(self, 'Error', 'Seleccione una promotora primero.')
            return
        
        fecha = self.calendar_widget.selectedDate().toString("yyyy-MM-dd")
        cantidad_str = self.combos_input.text().strip()
        
        # Lógica para eliminar el registro si la cantidad es 0 o está vacía
        if not cantidad_str or cantidad_str == '0':
            conn = sqlite3.connect('sistema_promotoras.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ventas WHERE promotora_id = ? AND fecha = ?", (self.current_promotora_id, fecha))
            conn.commit()
            conn.close()
            QMessageBox.information(self, 'Éxito', f'Venta para el {fecha} eliminada correctamente.')
            self.combos_input.clear()
        else:
            # Lógica para guardar o sobrescribir la venta si la cantidad es válida
            if not cantidad_str.isdigit():
                QMessageBox.warning(self, 'Error', 'Ingrese una cantidad válida.')
                return
            
            cantidad = int(cantidad_str)
            unidades_vendidas = cantidad * 2
                
            conn = sqlite3.connect('sistema_promotoras.db')
            cursor = conn.cursor()
            
            # Utiliza INSERT OR REPLACE INTO para sobrescribir la entrada si ya existe
            cursor.execute("INSERT OR REPLACE INTO ventas (promotora_id, fecha, combos_vendidos) VALUES (?, ?, ?)",
                           (self.current_promotora_id, fecha, unidades_vendidas))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, 'Éxito', f'Venta de {cantidad} combos ({unidades_vendidas} unidades) registrada para el {fecha}.')
        
        # Actualiza el resumen y el calendario en ambos casos
        self.load_summary_report()
        self.highlight_sales_dates()
        
    def show_daily_sale(self):
        if not self.current_promotora_id:
            return
        fecha = self.calendar_widget.selectedDate().toString("yyyy-MM-dd")
        conn = sqlite3.connect('sistema_promotoras.db')
        cursor = conn.cursor()
        cursor.execute("SELECT combos_vendidos FROM ventas WHERE promotora_id = ? AND fecha = ?", (self.current_promotora_id, fecha))
        venta = cursor.fetchone()
        conn.close()

        if venta:
            # Divide entre 2 para mostrar el número de combos, no de unidades
            self.combos_input.setText(str(int(venta[0] / 2)))
        else:
            self.combos_input.clear()

    def load_summary_report(self):
        if not self.current_promotora_id:
            self.summary_text_area.setText("Seleccione una promotora para ver el resumen.")
            return

        report_data = get_report_data(self.current_promotora_id)
        if report_data:
            text = f"--- Informe Preliminar ---\n\n"
            text += f"Emitido por: {report_data['emisor_nombre']}\n"
            text += f"Promotora: {report_data['promotora_nombre']}\n"
            text += f"Comercio: {report_data['comercio']}\n\n"
            
            text += f"--- Resumen General ---\n"
            
            # Formateo seguro para la UI
            inv_cajas = report_data['inventario_inicial_cajas'] if report_data['inventario_inicial_cajas'] is not None else "N/A"
            inv_unidades = report_data['inventario_inicial_unidades'] if report_data['inventario_inicial_unidades'] is not None else "N/A"
            unid_caja = report_data['unidades_por_caja'] if report_data['unidades_por_caja'] is not None else "N/A"
            total_combos = f"{report_data['total_combos_vendidos']:.2f}" if report_data['total_combos_vendidos'] is not None else "N/A"
            cajas_colocadas = f"{report_data['cajas_colocadas']:.2f}" if report_data['cajas_colocadas'] is not None else "N/A"
            inv_rest_cajas = f"{report_data['inventario_restante_cajas']:.2f}" if report_data['inventario_restante_cajas'] is not None else "N/A"
            inv_rest_unidades = report_data['inventario_restante'] if report_data['inventario_restante'] is not None else "N/A"

            text += f"Inventario Inicial: {inv_cajas} cajas ({inv_unidades} unidades)\n"
            text += f"Unidades por Caja: {unid_caja}\n"
            text += f"Total de Combos Vendidos: {total_combos} combos ({report_data['total_unidades']} unidades)\n"
            text += f"Cajas Colocadas: {cajas_colocadas} cajas\n"
            text += f"Inventario Restante: {inv_rest_cajas} cajas ({inv_rest_unidades} unidades)\n"

            text += f"\n--- Ventas Detalladas Día a Día ---\n"
            if not report_data['ventas_dia_a_dia'].empty:
                for _, row in report_data['ventas_dia_a_dia'].iterrows():
                    combos = row['combos_vendidos'] / 2.0
                    unidades = row['combos_vendidos']
                    text += f"- Fecha: {row['fecha'].strftime('%Y-%m-%d')} | Combos: {combos:.2f} ({unidades} unidades)\n"
            else:
                text += "No hay ventas registradas.\n"
            
            text += f"\n--- Totales de Venta ---\n"
            for mes, total_combos in report_data['ventas_mensuales_combos'].items():
                total_unidades = report_data['ventas_mensuales_unidades'][mes]
                text += f"- Mes de {calendar.month_name[mes.month]}: {total_combos:.2f} combos ({total_unidades} unidades)\n"
            
            text += f"\n--- Ventas Semanales ---\n"
            for date_range, total_combos in report_data['ventas_semanales_combos'].items():
                total_unidades = report_data['ventas_semanales_unidades'][date_range]
                text += f"- Semana del {date_range}: {total_combos:.2f} combos ({total_unidades} unidades)\n"
            
            self.summary_text_area.setText(text)
        else:
            self.summary_text_area.setText("No hay datos para previsualizar.")

    def generate_report(self):
        if not self.current_promotora_id:
            QMessageBox.warning(self, 'Error', 'Seleccione una promotora para generar el informe.')
            return
        
        try:
            mensaje = generate_pdf_report(self.current_promotora_id)
            QMessageBox.information(self, 'Éxito', mensaje)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Ocurrió un error al generar el informe: {e}')
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        window = ProyectoSistemaPromotoras()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
