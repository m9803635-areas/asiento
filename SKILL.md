---
name: asiento
description: >-
  Generación automatizada de asientos contables de reclasificación en SAP a partir del control de centros de beneficio (cdpf) y facturas de concesión (PVCP). Identifica discrepancias entre el centro de beneficio asignado en SAP (columna B) y la matriz maestra de cdpf por sociedad/concepto, marcando errores en naranja y generando los apuntes contables (cuadro Debe 40 / Haber 50) en la cuenta 4886651108 con fechas en formato AAAAMMAA.
---

# Skill: Reclasificación Contable de Centros de Beneficio (Asiento SAP)

Esta habilidad automatiza el control de asignación de **Centros de Beneficio (`cdpf` / PRCTR / KOSTL)** en las facturas de concesiones de Pierre & Vacances Center Parcs (PVCP) y genera la plantilla de carga de asientos contables de reclasificación para SAP.

---

## 1. Matriz Maestra de Asignación de Centros de Beneficio (`cdpf`)

| Société | Nombre / Centro | Subconcepto / Subcentro | `cdpf` Esperado |
| :--- | :--- | :--- | :--- |
| **E572** | TROIS FORÊTS / MOSELLE | Principal | `F013035` |
| **E573** | AILETTE | Principal | `F013096` |
| **E574** | HAUTS DE BRUYERES / CHAUMONT | Principal | `F013147` |
| **E575** | BOIS-FRANCS | Principal | `F013237` |
| **E576** | CP BOIS AUX DAIMS / VIENNE | Principal | `F013336` |
| **E577** | VILLAGES NATURE | Crêperie | `F013701` |
| **E577** | VILLAGES NATURE | Bar Lagon / Bar AQL | `F013702` |
| **E577** | VILLAGES NATURE | Bar Bowling | `F013703` |
| **E578** | LOT ET GARONNE | Principal | `F013600` |

---

## 2. Lógica de Control en Hoja `facturas`

1. **Columna M (`cdpf`)**: Se calcula el centro de beneficio teórico que corresponde según la sociedad (Columna K) y, para `E577`, analizando las columnas `Concepto Facturado` (Col H) o `vn2` (Col I).
2. **Columna N (`cdpf SAP`)**: Se busca la factura en el extracto de SAP (pestaña `SAP`, columna O que contiene `NF.<número_factura>`) y se extrae el centro de beneficio contabilizado en la columna B (`Centre de profit`).
3. **Detección de Errores y Formato**:
   - Si `cdpf SAP` ≠ `cdpf teórico`, la celda se resalta en **color naranja** (`PatternFill(start_color="FFA500", fill_type="solid")`).
   - Ambas celdas (`cdpf` y `cdpf SAP`) quedan señaladas visualmente para trazabilidad inmediata.

---

## 3. Generación del Asiento de Reclasificación (Hoja `Asiento`)

Para cada partida errónea identificada, se genera un par de apuntes balanceados (partida doble) para transferir el saldo entre centros de beneficio:

### Estructura de Columnas

| Columna | Nombre Técnico SAP | Descripción | Valor / Regla |
| :--- | :--- | :--- | :--- |
| **A** | `BUKRS` | Sociedad contable | Sociedad emisora / cabecera (ej. `E571`) |
| **C** | `BUDAT` | Fecha contable | Formato `AAAAMMAA` (ej. `20260930`, `20261031`) |
| **D** | `BLDAT` | Fecha de la pieza | Formato `AAAAMMAA` (**fecha exacta de la factura**) |
| **E** | `BLART` | Clase de documento | `SA` |
| **F** | `WAERS` | Moneda | `EUR` |
| **G** | `XBLNR` | Referencia | `Reclass. Compte` |
| **H** | `BKTXT` | Texto de cabecera | `Reclass. Compte` |
| **L** | `BSCHL` | Clave de contabilización | **`50`** para el Haber / **`40`** para el Debe |
| **M** | `SAKNR` | Cuenta de mayor | **`4886651108`** |
| **P** | `WRBTR` | Importe | Importe en valor absoluto a reclasificar |
| **R** | `KOSTL` | Centro de coste | Centro de beneficio asociado |
| **S** | `PRCTR` | Centro de beneficio | Centro de beneficio asociado |
| **AA** | `SGTXT` | Texto de posición | Descripción completa de la factura (ej. `NF.169003845,...`) |
| **AB** | `DKOSC` | Esquema de imputación | Descripción completa de la factura (ej. `NF.169003845,...`) |

### Apuntes de Reclasificación (Por cada factura errónea)

1. **Línea de Abono (Haber - `50`)**: Cancela la contabilización original en el centro de beneficio incorrecto.
   - `BSCHL` = `50`
   - `KOSTL` / `PRCTR` = Centro erróneo (ej. `F013076`)
   - `WRBTR` = Importe de la factura
2. **Línea de Cargo (Debe - `40`)**: Imputa el importe en el centro de beneficio correcto.
   - `BSCHL` = `40`
   - `KOSTL` / `PRCTR` = Centro correcto (ej. `F013096`)
   - `WRBTR` = Importe de la factura

El asiento resultante queda perfectamente cuadrado (`Debe - Haber = 0,00 €`).
