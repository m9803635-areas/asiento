# Skill de Reclasificación Contable de Centros de Beneficio (`/asiento`)

Este repositorio contiene la habilidad, reglas de negocio y scripts automatizados para el control y la reclasificación de **Centros de Beneficio (`cdpf` / PRCTR / KOSTL)** en SAP a partir de las facturas de concesión de Pierre & Vacances Center Parcs (PVCP) para el grupo AREAS.

---

## 📋 Estructura del Repositorio

- `SKILL.md`: Definición y especificación completa de la habilidad para el asistente Antigravity.
- `README.md`: Documentación funcional y técnica del flujo contable.
- `scripts/generar_asiento.py`: Script modular de Python para procesar cualquier libro Excel de control PVCP.

---

## 🏢 Matriz Maestra de Centros de Beneficio (`cdpf`)

| Sociedad | Nombre del Centro | Subconcepto / Subcentro | `cdpf` Esperado |
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

## ⚙️ Dinámica Contable

1. **Detección de Discrepancias**:
   - En la pestaña `facturas`, se compara la columna **M (`cdpf` teórico)** con la columna **N (`cdpf SAP` real)** extraída de la columna B de `SAP`.
   - Cualquier desvío se resalta en **color naranja sólido** (`#FFA500`).

2. **Generación del Asiento Cuadrado (`Asiento`)**:
   - Para cada factura errónea, se generan dos apuntes en la cuenta de mayor **`4886651108`**:
     * **Línea de Haber (`BSCHL = 50`)**: Da de baja el saldo del centro de beneficio incorrecto.
     * **Línea de Debe (`BSCHL = 40`)**: Imputa el saldo en el centro de beneficio correcto.
   - Las fechas contables (Col C `BUDAT`) y de documento (Col D `BLDAT`) se formatean estrictamente en **`AAAAMMAA`**, usando en Col D la fecha exacta de la factura a reclasificar.
   - La partida doble garantiza un saldo neto nulo (`Debe - Haber = 0,00 €`).

---

## 🚀 Uso Rápido

### Mediante Antigravity
Invoca el comando `/asiento` o indica:
> *"Revisa las facturas de la pestaña 'facturas' contra 'SAP', marca los errores de cdpf en color naranja y genera las líneas de reclasificación en la pestaña 'Asiento'."*

### Mediante Script en Línea de Comandos
```bash
python scripts/generar_asiento.py --file "exportPVCP2026_v2 CIERRE ANUAL.xlsx"
```
