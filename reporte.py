import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import calendar

class PDF(FPDF):
    def header(self):
        self.image('logo-web.png', 10, 8, 50)
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Informe de Ventas', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title, fill_color=(200, 220, 255)):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(*fill_color)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()
    
    def section_frame(self, x, y, w, h, border_color=(100, 149, 237)):
        self.set_draw_color(*border_color)
        self.set_line_width(0.5)
        self.rect(x, y, w, h)
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)

def get_emisor_name():
    conn = sqlite3.connect('sistema_promotoras.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM emisor")
    emisor = cursor.fetchone()
    conn.close()
    return emisor[0] if emisor else "NAYLEN JIMENEZ"

def get_report_data(promotora_id):
    """Calcula y devuelve los datos del informe."""
    conn = sqlite3.connect('sistema_promotoras.db')
    df_promotora = pd.read_sql_query(f"SELECT * FROM promotoras WHERE id = {promotora_id}", conn)
    df_ventas = pd.read_sql_query(f"SELECT * FROM ventas WHERE promotora_id = {promotora_id}", conn)
    conn.close()

    if df_promotora.empty:
        return None

    promotora_data = df_promotora.iloc[0]
    
    # Prepara los datos de ventas
    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'])
    df_ventas_sorted = df_ventas.sort_values(by='fecha')

    total_unidades = df_ventas_sorted['combos_vendidos'].sum() if not df_ventas_sorted.empty else 0
    total_combos_vendidos = total_unidades / 2.0
    
    # Cálculo de inventario restante y cajas colocadas
    inventario_inicial_cajas = promotora_data['inventario_inicial']
    unidades_por_caja = promotora_data['unidades_por_caja']
    
    inventario_inicial_unidades = None
    inventario_restante = None
    inventario_restante_cajas = None
    cajas_colocadas = 0.0

    if inventario_inicial_cajas is not None and unidades_por_caja is not None:
        if unidades_por_caja > 0:
            inventario_inicial_unidades = inventario_inicial_cajas * unidades_por_caja
            inventario_restante = inventario_inicial_unidades - total_unidades
            inventario_restante_cajas = inventario_restante / unidades_por_caja
            cajas_colocadas = total_unidades / unidades_por_caja
        else: # unidades_por_caja es 0
            inventario_inicial_unidades = inventario_inicial_cajas * 0
            inventario_restante = inventario_inicial_unidades - total_unidades
            inventario_restante_cajas = 0
            cajas_colocadas = 0
    
    # Cálculo de ventas por semana y mes
    ventas_semanales_unidades = {}
    ventas_semanales_combos = {}
    if not df_ventas_sorted.empty:
        for week_num, group in df_ventas_sorted.groupby(df_ventas_sorted['fecha'].dt.isocalendar().week):
            start_date = group['fecha'].min()
            end_date = group['fecha'].max()
            date_range = f"{start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}"
            total_semanal = group['combos_vendidos'].sum()
            ventas_semanales_unidades[date_range] = total_semanal
            ventas_semanales_combos[date_range] = total_semanal / 2.0

    ventas_mensuales_unidades = df_ventas_sorted.groupby(df_ventas_sorted['fecha'].dt.to_period('M'))['combos_vendidos'].sum()
    ventas_mensuales_combos = ventas_mensuales_unidades / 2.0
    
    return {
        "promotora_nombre": promotora_data['nombre'],
        "promotora_id": promotora_data['id'],
        "emisor_nombre": get_emisor_name(),
        "comercio": promotora_data['comercio'],
        "inventario_inicial_cajas": inventario_inicial_cajas,
        "inventario_inicial_unidades": inventario_inicial_unidades,
        "unidades_por_caja": unidades_por_caja,
        "total_unidades": total_unidades,
        "total_combos_vendidos": total_combos_vendidos,
        "cajas_colocadas": cajas_colocadas,
        "inventario_restante": inventario_restante,
        "inventario_restante_cajas": inventario_restante_cajas,
        "ventas_dia_a_dia": df_ventas_sorted,
        "ventas_semanales_unidades": ventas_semanales_unidades,
        "ventas_semanales_combos": ventas_semanales_combos,
        "ventas_mensuales_unidades": ventas_mensuales_unidades,
        "ventas_mensuales_combos": ventas_mensuales_combos
    }

def generate_pdf_report(promotora_id):
    """Genera el informe en PDF utilizando los datos de get_report_data."""
    report_data = get_report_data(promotora_id)
    if not report_data:
        return "Promotora no encontrada."
    
    pdf = PDF()
    pdf.add_page()
    
    # Información en el PDF
    pdf.chapter_title(f"Informe de Ventas - {report_data['promotora_nombre']}")
    pdf.ln(10) # Espacio para evitar superposición con el logo
    pdf.set_font('Arial', '', 10)
    pdf.write(5, "Emitido por: ")
    pdf.set_font('Arial', 'B', 10)
    pdf.write(5, f"{report_data['emisor_nombre']}\n")
    pdf.ln(10)

    # Bloque de Resumen General
    y_start = pdf.get_y()
    pdf.chapter_title("Resumen General", fill_color=(230, 230, 230))
    
    # Formateo seguro para PDF
    inv_cajas = report_data['inventario_inicial_cajas'] if report_data['inventario_inicial_cajas'] is not None else "N/A"
    inv_unidades = report_data['inventario_inicial_unidades'] if report_data['inventario_inicial_unidades'] is not None else "N/A"
    unid_caja = report_data['unidades_por_caja'] if report_data['unidades_por_caja'] is not None else "N/A"
    total_combos = f"{report_data['total_combos_vendidos']:.2f}" if report_data['total_combos_vendidos'] is not None else "N/A"
    cajas_colocadas = f"{report_data['cajas_colocadas']:.2f}" if report_data['cajas_colocadas'] is not None else "N/A"
    inv_rest_cajas = f"{report_data['inventario_restante_cajas']:.2f}" if report_data['inventario_restante_cajas'] is not None else "N/A"
    inv_rest_unidades = report_data['inventario_restante'] if report_data['inventario_restante'] is not None else "N/A"

    pdf.chapter_body(f"Nombre de la Promotora: {report_data['promotora_nombre']}\n"
                     f"Comercio de la Promotora: {report_data['comercio']}\n"
                     f"Inventario Inicial: {inv_cajas} cajas ({inv_unidades} unidades)\n"
                     f"Unidades por Caja: {unid_caja}\n"
                     f"Total de Combos Vendidos: {total_combos} combos ({report_data['total_unidades']} unidades)\n"
                     f"Cajas Colocadas: {cajas_colocadas} cajas\n"
                     f"Inventario Restante: {inv_rest_cajas} cajas ({inv_rest_unidades} unidades)\n")
    pdf.section_frame(10, y_start, 190, pdf.get_y() - y_start)

    # Bloque de Ventas Detalladas
    y_start = pdf.get_y()
    pdf.chapter_title("Ventas Detalladas Día a Día", fill_color=(230, 230, 230))
    if not report_data['ventas_dia_a_dia'].empty:
        for index, row in report_data['ventas_dia_a_dia'].iterrows():
            combos = row['combos_vendidos'] / 2.0
            unidades = row['combos_vendidos']
            pdf.chapter_body(f"  - Fecha: {row['fecha'].strftime('%Y-%m-%d')} | Combos: {combos:.2f} ({unidades} unidades)")
    else:
        pdf.chapter_body("No hay ventas registradas.")
    pdf.section_frame(10, y_start, 190, pdf.get_y() - y_start)

    # Bloque de Totales de Venta
    y_start = pdf.get_y()
    pdf.chapter_title("Totales de Venta", fill_color=(230, 230, 230))
    pdf.chapter_body("Venta Total por Semana:")
    for date_range, total_combos in report_data['ventas_semanales_combos'].items():
        total_unidades = report_data['ventas_semanales_unidades'][date_range]
        pdf.chapter_body(f"  - Semana del {date_range}: {total_combos:.2f} combos ({total_unidades} unidades)")
    
    pdf.chapter_body("\nVenta Total por Mes:")
    for mes, total_combos in report_data['ventas_mensuales_combos'].items():
        total_unidades = report_data['ventas_mensuales_unidades'][mes]
        pdf.chapter_body(f"  - Mes de {calendar.month_name[mes.month]}: {total_combos:.2f} combos ({total_unidades} unidades)")
    pdf.section_frame(10, y_start, 190, pdf.get_y() - y_start)

    filename = f'reporte_{report_data["promotora_nombre"].replace(" ", "_")}.pdf'
    pdf.output(filename)
    return f"Informe de '{report_data['promotora_nombre']}' generado en '{filename}'."
