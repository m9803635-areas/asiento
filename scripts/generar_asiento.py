#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de generación de asientos contables de reclasificación para SAP (PVCP).
Compara centros de beneficio (cdpf) entre facturas y extracto SAP, resalta errores en naranja
y genera los apuntes Debe 40 / Haber 50 en la cuenta 4886651108.
"""

import argparse
import datetime
import os
import re
from copy import copy
import openpyxl
from openpyxl.styles import PatternFill, Font

# Matriz Maestra cdpf
SOC_CDPF_MAP = {
    'E572': 'F013035',
    'E573': 'F013096',
    'E574': 'F013147',
    'E575': 'F013237',
    'E576': 'F013336',
    'E578': 'F013600',
}

SOC_NAME_MAP = {
    'E572': 'TROIS FORÊTS/MOSELLE',
    'E573': 'AILETTE',
    'E574': 'HAUTS DE BRUYERES / CHAUMONT',
    'E575': 'BOIS-FRANCS',
    'E576': 'BOIS AUX DAIMS / VIENNE',
    'E577': 'VILLAGES NATURE',
    'E578': 'Lot et Garonne',
}

def get_expected_cdpf(soc, concepto, vn2, actual_cdpf=None):
    soc = str(soc or '').strip()
    concepto = str(concepto or '').upper()
    vn2 = str(vn2 or '').upper()
    
    if soc == 'E577':
        combined = f"{concepto} {vn2}"
        if 'CREPERIE' in combined or 'CRÊPERIE' in combined:
            return 'F013701'
        elif 'BAR LAGON' in combined or 'BAR AQL' in combined or 'LAGON' in combined:
            return 'F013702'
        elif 'BAR BOW' in combined or 'BOWLING' in combined:
            return 'F013703'
        elif actual_cdpf in ['F013701', 'F013702', 'F013703']:
            return actual_cdpf
        else:
            return 'F013701'
    return SOC_CDPF_MAP.get(soc, '')

def format_date_aaaammdd(val):
    if val is None:
        return ''
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime('%Y%m%d')
    try:
        val_int = int(val)
        if val_int > 1000:
            d = datetime.date(1899, 12, 30) + datetime.timedelta(days=val_int)
            return d.strftime('%Y%m%d')
        return str(val_int)
    except Exception:
        return str(val)

def procesar_archivo(filepath):
    print(f"Abriendo libro: {filepath}")
    wb = openpyxl.load_workbook(filepath)
    
    if 'SAP' not in wb.sheetnames or 'facturas' not in wb.sheetnames or 'Asiento' not in wb.sheetnames:
        raise ValueError("El archivo debe contener las pestañas 'SAP', 'facturas' y 'Asiento'")
        
    ws_sap = wb['SAP']
    ws_fac = wb['facturas']
    ws_asiento = wb['Asiento']
    
    # Extraer partidas NF de SAP
    sap_nf_dict = {}
    sap_nf_list = []
    
    for r in range(2, ws_sap.max_row + 1):
        txt = str(ws_sap.cell(r, 15).value or '')
        if 'NF' in txt:
            soc_a = ws_sap.cell(r, 1).value
            cdpf_b = ws_sap.cell(r, 2).value
            date_h = ws_sap.cell(r, 8).value
            montant_k = ws_sap.cell(r, 11).value
            soc_q = ws_sap.cell(r, 17).value
            
            m = re.search(r'NF\.?(\d+)', txt)
            inv_num = m.group(1) if m else ''
            
            entry = {
                'sap_row': r,
                'inv_num': inv_num,
                'cdpf_sap': str(cdpf_b).strip() if cdpf_b else '',
                'date_raw': date_h,
                'date_str': format_date_aaaammdd(date_h),
                'montant': float(montant_k) if montant_k is not None else 0.0,
                'txt': txt,
                'soc': str(soc_q).strip() if soc_q else str(soc_a).strip(),
                'bukrs': str(soc_a).strip() if soc_a else 'E571'
            }
            sap_nf_list.append(entry)
            if inv_num:
                sap_nf_dict[inv_num] = entry
                
    print(f"Facturas NF encontradas en SAP: {len(sap_nf_list)}")
    
    orange_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
    
    # Encabezados en facturas
    cell_m1 = ws_fac.cell(1, 13, value="cdpf")
    cell_n1 = ws_fac.cell(1, 14, value="cdpf SAP")
    ref_cell = ws_fac.cell(1, 1)
    if ref_cell.has_style:
        cell_m1.font = copy(ref_cell.font)
        cell_m1.fill = copy(ref_cell.fill)
        cell_m1.alignment = copy(ref_cell.alignment)
        cell_n1.font = copy(ref_cell.font)
        cell_n1.fill = copy(ref_cell.fill)
        cell_n1.alignment = copy(ref_cell.alignment)
        
    # Actualizar filas de facturas
    discrepancias = []
    for r in range(2, ws_fac.max_row + 1):
        inv_num = str(ws_fac.cell(r, 1).value or '').strip()
        soc = ws_fac.cell(r, 11).value
        concepto = ws_fac.cell(r, 8).value
        vn2 = ws_fac.cell(r, 9).value
        
        actual_cdpf = sap_nf_dict[inv_num]['cdpf_sap'] if inv_num in sap_nf_dict else None
        expected_cdpf = get_expected_cdpf(soc, concepto, vn2, actual_cdpf)
        ws_fac.cell(r, 13, value=expected_cdpf)
        
        if inv_num in sap_nf_dict:
            c_n = ws_fac.cell(r, 14, value=actual_cdpf)
            if actual_cdpf != expected_cdpf:
                c_n.fill = orange_fill
                ws_fac.cell(r, 13).fill = orange_fill
                discrepancias.append(sap_nf_dict[inv_num])
        else:
            ws_fac.cell(r, 14, value=None)
            
    # Formatear fechas en Asiento a AAAAMMAA
    for r in range(3, ws_asiento.max_row + 1):
        ws_asiento.cell(r, 3, value=format_date_aaaammdd(ws_asiento.cell(r, 3).value))
        ws_asiento.cell(r, 4, value=format_date_aaaammdd(ws_asiento.cell(r, 4).value))
        
    print(f"Discrepancias identificadas para reclasificar: {len(discrepancias)}")
    asiento_row = ws_asiento.max_row + 1
    
    for err in discrepancias:
        inv_date = err['date_str']
        amt = err['montant']
        wrong_cdpf = err['cdpf_sap']
        correct_cdpf = get_expected_cdpf(err['soc'], err['txt'], '')
        desc = err['txt']
        soc = err['bukrs']
        
        # Línea 1: Haber (50) - anula cdpf erróneo
        ws_asiento.cell(asiento_row, 1, value=soc)
        ws_asiento.cell(asiento_row, 3, value=inv_date)
        ws_asiento.cell(asiento_row, 4, value=inv_date)
        ws_asiento.cell(asiento_row, 5, value="SA")
        ws_asiento.cell(asiento_row, 6, value="EUR")
        ws_asiento.cell(asiento_row, 7, value="Reclass. Compte")
        ws_asiento.cell(asiento_row, 8, value="Reclass. Compte")
        ws_asiento.cell(asiento_row, 12, value="50")
        ws_asiento.cell(asiento_row, 13, value="4886651108")
        ws_asiento.cell(asiento_row, 16, value=amt)
        ws_asiento.cell(asiento_row, 18, value=wrong_cdpf)
        ws_asiento.cell(asiento_row, 19, value=wrong_cdpf)
        ws_asiento.cell(asiento_row, 27, value=desc)
        ws_asiento.cell(asiento_row, 28, value=desc)
        asiento_row += 1
        
        # Línea 2: Debe (40) - imputa cdpf correcto
        ws_asiento.cell(asiento_row, 1, value=soc)
        ws_asiento.cell(asiento_row, 3, value=inv_date)
        ws_asiento.cell(asiento_row, 4, value=inv_date)
        ws_asiento.cell(asiento_row, 5, value="SA")
        ws_asiento.cell(asiento_row, 6, value="EUR")
        ws_asiento.cell(asiento_row, 7, value="Reclass. Compte")
        ws_asiento.cell(asiento_row, 8, value="Reclass. Compte")
        ws_asiento.cell(asiento_row, 12, value="40")
        ws_asiento.cell(asiento_row, 13, value="4886651108")
        ws_asiento.cell(asiento_row, 16, value=amt)
        ws_asiento.cell(asiento_row, 18, value=correct_cdpf)
        ws_asiento.cell(asiento_row, 19, value=correct_cdpf)
        ws_asiento.cell(asiento_row, 27, value=desc)
        ws_asiento.cell(asiento_row, 28, value=desc)
        asiento_row += 1

    wb.save(filepath)
    print(f"Archivo guardado y actualizado exitosamente en: {filepath}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Control y reclasificación de cdpf en PVCP")
    parser.add_argument('--file', required=True, help="Ruta al libro Excel (.xlsx)")
    args = parser.parse_args()
    procesar_archivo(args.file)
