"""Build the Excel decision dashboard from the exported dashboard CSVs.

    python3 08_dashboard/export_dashboard_data.py
    python3 08_dashboard/build_excel_dashboard.py

By default the workbook holds simulated data only and is safe to publish. Add
--include-public to add the Open Banking monthly panel from
02_data/processed/public_monthly.csv; that version is written to
02_data/processed/ (excluded from Git) because the publisher has not granted an
open licence for redistribution.

All headline figures and chart tables are Excel formulas over the data sheets,
so the dashboard updates if the data sheets are replaced. Needs openpyxl.
"""

import argparse
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "08_dashboard" / "data"

NAVY, GOLD, CREAM, INK, GREY = "1F3B63", "B8860B", "F4F1E4", "1A1A1A", "6B6B6B"
SERIES = ["1F3B63", "B8860B", "4F8A8B", "A23B3B", "8C8C8C"]
FONT = "Arial"

SHEETS = [  # (sheet name, csv file, description)
    ("Services", "services.csv", "One row per fictional important business service"),
    ("Incidents", "incidents.csv", "One row per simulated service-impact episode"),
    ("Dependencies", "dependencies.csv", "One row per service-supplier link"),
    ("Scenarios", "scenarios.csv", "Recovery exercise x assumed effect, 50 synthetic seeds"),
    ("Recovery_Gap", "recovery_gap.csv", "Recovery-time cut each service needs"),
    ("Recovery_Curve", "recovery_curve.csv", "Breaches left after each % cut in recovery time"),
    ("Supplier_Exposure", "supplier_exposure.csv", "Services and tolerances behind each supplier"),
    ("Outage_Stress", "supplier_outage_stress.csv", "Full supplier outage of N minutes, no failover"),
]


def read(path):
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    out = [rows[0]]
    for row in rows[1:]:
        parsed = []
        for value in row:
            try:
                number = float(value)
                parsed.append(int(number) if number.is_integer() and "." not in value else number)
            except ValueError:
                parsed.append(value)
        out.append(parsed)
    return out


def font(size=10, bold=False, color=INK, italic=False):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic)


def fill(color):
    return PatternFill("solid", start_color=color, end_color=color)


THIN = Side(style="thin", color="D0CCBC")
RULE = Side(style="medium", color=INK)


def mono_header(cell, size=9):
    """Monochrome table header: black bold text on white with a rule underneath."""
    cell.font = font(size, bold=True, color=INK)
    cell.fill = PatternFill(fill_type=None)
    cell.border = Border(bottom=RULE)


def write_data_sheet(wb, name, rows, note):
    ws = wb.create_sheet(name)
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(r, c, value)
            cell.font = font(10, bold=(r == 1), color=INK)
            if r == 1:
                mono_header(cell, 10)
                cell.alignment = Alignment(wrap_text=True, vertical="center")
    for c, header in enumerate(rows[0], start=1):
        width = max(len(str(header)), *(len(str(r[c - 1])) for r in rows[1:])) + 2
        ws.column_dimensions[get_column_letter(c)].width = min(max(width, 10), 42)
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    note_row = len(rows) + 2
    ws.cell(note_row, 1, f"{note}. Source: 08_dashboard/data/ (simulated, fictional bank).").font = font(9, italic=True, color=GREY)
    columns = {h: get_column_letter(i) for i, h in enumerate(rows[0], start=1)}
    return ws, columns, len(rows)


def rng(sheet, cols, header, last):
    return f"{sheet}!${cols[header]}$2:${cols[header]}${last}"


def style_chart(chart, title, x_title=None, y_title=None):
    chart.title = title
    chart.style = 2
    chart.height, chart.width = 8.6, 15.5
    chart.legend.position = "b"
    if x_title:
        chart.x_axis.title = x_title
    if y_title:
        chart.y_axis.title = y_title
    chart.y_axis.majorGridlines = None
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    for i, series in enumerate(chart.series):
        colour = SERIES[i % len(SERIES)]
        series.graphicalProperties.line.solidFill = colour
        if isinstance(chart, BarChart):
            series.graphicalProperties.solidFill = colour
        else:
            series.graphicalProperties.line.width = 28000
            series.smooth = False
    return chart


def build(include_public, output):
    wb = Workbook()
    dash = wb.active
    dash.title = "Dashboard"
    calc = wb.create_sheet("Chart_Data")
    info = {}
    for name, filename, note in SHEETS:
        rows = read(DATA / filename)
        info[name] = write_data_sheet(wb, name, rows, note)
    if include_public:
        rows = read(ROOT / "02_data" / "processed" / "public_monthly.csv")
        info["Public_Monthly"] = write_data_sheet(
            wb, "Public_Monthly", rows,
            "Open Banking Limited API performance, published monthly aggregates. Not for redistribution")
    notes = wb.create_sheet("Notes")

    S = lambda sheet, header: rng(sheet, info[sheet][1], header, info[sheet][2])

    # ---------- Chart_Data: formula-driven tables behind every chart ----------
    calc["A1"] = "Chart tables (formulas over the data sheets; do not type over)"
    calc["A1"].font = font(11, bold=True, color=INK)
    services = [r[2] for r in read(DATA / "services.csv")[1:]]
    suppliers = [r[2] for r in read(DATA / "supplier_exposure.csv")[1:]]
    cuts = sorted({r[3] for r in read(DATA / "recovery_curve.csv")[1:]})
    outages = sorted({r[3] for r in read(DATA / "supplier_outage_stress.csv")[1:]})

    def header_row(row, labels):
        for c, label in enumerate(labels, start=1):
            cell = calc.cell(row, c, label)
            mono_header(cell, 10)
            cell.alignment = Alignment(wrap_text=True)

    # Table 1: service episodes and breaches (rows 3-7)
    header_row(3, ["Service", "Episodes", "Beyond tolerance", "Tolerance (min)"])
    for i, svc in enumerate(services):
        r = 4 + i
        calc.cell(r, 1, f"=Services!C{2 + i}")
        calc.cell(r, 2, f"=SUMIFS({S('Services', 'incident_count')},{S('Services', 'service_name')},A{r})")
        calc.cell(r, 3, f"=SUMIFS({S('Services', 'tolerance_breach_count')},{S('Services', 'service_name')},A{r})")
        calc.cell(r, 4, f"=SUMIFS({S('Services', 'impact_tolerance_minutes')},{S('Services', 'service_name')},A{r})")
    t1_last = 3 + len(services)

    # Table 2: recovery curve, cut % x service (default seed)
    t2 = t1_last + 2
    header_row(t2, ["Faster recovery (%)"] + services)
    for j, cut in enumerate(cuts):
        r = t2 + 1 + j
        calc.cell(r, 1, cut)
        for k in range(len(services)):
            col = get_column_letter(2 + k)
            calc.cell(r, 2 + k, f"=SUMIFS({S('Recovery_Curve', 'default_seed_breaches')},"
                                f"{S('Recovery_Curve', 'service_name')},{col}${t2},"
                                f"{S('Recovery_Curve', 'recovery_cut_pct')},$A{r})")
    t2_last = t2 + len(cuts)

    # Table 3: supplier outage stress, minutes x supplier
    t3 = t2_last + 2
    header_row(t3, ["Outage (minutes)"] + suppliers)
    for j, minutes in enumerate(outages):
        r = t3 + 1 + j
        calc.cell(r, 1, minutes)
        for k in range(len(suppliers)):
            col = get_column_letter(2 + k)
            calc.cell(r, 2 + k, f"=SUMIFS({S('Outage_Stress', 'services_beyond_tolerance')},"
                                f"{S('Outage_Stress', 'supplier_name')},{col}${t3},"
                                f"{S('Outage_Stress', 'outage_minutes')},$A{r})")
    t3_last = t3 + len(outages)

    # Table 4: exercise comparison, option x effect (median avoided across seeds)
    t4 = t3_last + 2
    effects = [("cautious", "Cautious (10% faster)"), ("central", "Central (30% faster)"),
               ("optimistic", "Optimistic (50% faster)")]
    header_row(t4, ["Exercise"] + [label for _, label in effects])
    options = []
    for r in read(DATA / "scenarios.csv")[1:]:
        if r[2] not in options:
            options.append(r[2])
    for j, option in enumerate(options):
        r = t4 + 1 + j
        calc.cell(r, 1, option)
        for k, (effect, _) in enumerate(effects):
            calc.cell(r, 2 + k, f"=SUMIFS({S('Scenarios', 'avoided_median')},"
                                f"{S('Scenarios', 'option_label')},$A{r},"
                                f"{S('Scenarios', 'effect_case')},\"{effect}\")")
    t4_last = t4 + len(options)

    # Table 5: helper to name the most concentrated supplier
    t5 = t4_last + 2
    header_row(t5, ["Supplier", "High-criticality services", "First breach (min)", "Rank key"])
    ex_cols, ex_last = info["Supplier_Exposure"][1], info["Supplier_Exposure"][2]
    for j in range(len(suppliers)):
        r, src = t5 + 1 + j, 2 + j
        calc.cell(r, 1, f"=Supplier_Exposure!{ex_cols['supplier_name']}{src}")
        calc.cell(r, 2, f"=Supplier_Exposure!{ex_cols['high_criticality_services']}{src}")
        calc.cell(r, 3, f"=Supplier_Exposure!{ex_cols['minutes_to_first_breach']}{src}")
        calc.cell(r, 4, f"=C{r}-B{r}*1000")
    t5_last = t5 + len(suppliers)
    calc.cell(t5_last + 1, 1, "Rank key: more high-criticality services first, then the fastest first breach.").font = font(9, italic=True, color=GREY)

    for c in range(1, 7):
        calc.column_dimensions[get_column_letter(c)].width = 24 if c == 1 else 18
    for row in calc.iter_rows(min_row=4):
        for cell in row:
            if cell.font.color is None or cell.font.color.rgb != "00FFFFFF":
                if not cell.font.bold:
                    cell.font = font(10, italic=cell.font.italic, color=GREY if cell.font.italic else INK)

    # ---------- Dashboard ----------
    dash.sheet_view.showGridLines = False
    for c in range(1, 20):
        dash.column_dimensions[get_column_letter(c)].width = 10.5
    dash.column_dimensions["A"].width = 2
    dash.merge_cells("B1:Q1")
    dash["B1"] = "Recovery exercise decisions: a fictional UK retail bank"
    dash["B1"].font = font(18, bold=True, color=INK)
    dash.merge_cells("B2:Q2")
    dash["B2"] = ("Which recovery exercises should an operational resilience committee pilot first, "
                  "and where is supplier concentration highest? Simulated period Sep 2024 to Aug 2026, seed 280926.")
    dash["B2"].font = font(10, color=GREY)
    dash.merge_cells("B3:Q3")
    dash["B3"] = ("Data honesty: every incident, supplier, tolerance and intervention effect below is simulated. "
                  "Nothing here estimates a real bank's risk. Public Open Banking data is aggregate context only and is never linked to the simulated bank.")
    dash["B3"].font = font(9, italic=True, color=INK)
    dash["B3"].fill = fill(CREAM)
    dash["B3"].alignment = Alignment(wrap_text=True, vertical="center")
    dash.row_dimensions[3].height = 30

    sv, svl = info["Services"][1], info["Services"][2]
    inc, incl = info["Incidents"][1], info["Incidents"][2]
    gap, gapl = info["Recovery_Gap"][1], info["Recovery_Gap"][2]
    shared = f"Incidents!${inc['shared_event_id']}$2:${inc['shared_event_id']}${incl}"
    tiles = [
        ("Service-impact episodes", f"=SUM(Services!{sv['incident_count']}2:{sv['incident_count']}{svl})", "0"),
        ("Beyond impact tolerance", f"=SUM(Services!{sv['tolerance_breach_count']}2:{sv['tolerance_breach_count']}{svl})", "0"),
        ("Share beyond tolerance", "=E6/B6", "0%"),
        ("Multi-service supplier events", f"=SUMPRODUCT(({shared}<>\"\")/COUNTIF({shared},{shared}&\"\"))", "0"),
        ("Most concentrated supplier",
         f"=INDEX(Chart_Data!$A${t5 + 1}:$A${t5_last},MATCH(MIN(Chart_Data!$D${t5 + 1}:$D${t5_last}),Chart_Data!$D${t5 + 1}:$D${t5_last},0))", "@"),
    ]
    for i, (label, formula, fmt) in enumerate(tiles):
        col = 2 + i * 3
        first, last = get_column_letter(col), get_column_letter(col + 2)
        dash.merge_cells(f"{first}5:{last}5")
        dash.merge_cells(f"{first}6:{last}7")
        dash[f"{first}5"] = label
        dash[f"{first}5"].font = font(9, bold=True, color="FFFFFF")
        dash[f"{first}6"] = formula
        dash[f"{first}6"].number_format = fmt
        dash[f"{first}6"].font = font(20 if i < 4 else 15, bold=True, color=INK)
        for r in (5, 6, 7):
            for c in range(col, col + 3):
                cell = dash.cell(r, c)
                cell.fill = fill(NAVY if r == 5 else CREAM)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    dash.row_dimensions[5].height = 18
    dash.row_dimensions[6].height = 20
    dash.row_dimensions[7].height = 20

    # Charts
    c1 = BarChart()
    c1.type = "bar"
    c1.grouping = "clustered"
    c1.add_data(Reference(calc, min_col=2, max_col=3, min_row=3, max_row=t1_last), titles_from_data=True)
    c1.set_categories(Reference(calc, min_col=1, min_row=4, max_row=t1_last))
    style_chart(c1, "Simulated episodes and breaches by service", None, "Episodes")
    c1.dataLabels = DataLabelList()
    c1.dataLabels.showVal = True
    c1.dataLabels.showSerName = False
    c1.dataLabels.showCatName = False
    c1.dataLabels.showLegendKey = False
    c1.x_axis.scaling.orientation = "maxMin"
    dash.add_chart(c1, "B9")

    c2 = LineChart()
    c2.add_data(Reference(calc, min_col=2, max_col=1 + len(services), min_row=t2, max_row=t2_last), titles_from_data=True)
    c2.set_categories(Reference(calc, min_col=1, min_row=t2 + 1, max_row=t2_last))
    style_chart(c2, "Breaches left if recovery were X% faster", "Faster recovery (%)", "Breaches left")
    dash.add_chart(c2, "J9")

    c3 = LineChart()
    c3.add_data(Reference(calc, min_col=2, max_col=1 + len(suppliers), min_row=t3, max_row=t3_last), titles_from_data=True)
    c3.set_categories(Reference(calc, min_col=1, min_row=t3 + 1, max_row=t3_last))
    style_chart(c3, "Services pushed past tolerance by a full supplier outage", "Outage length (minutes)", "Services beyond tolerance")
    c3.y_axis.scaling.min, c3.y_axis.scaling.max, c3.y_axis.majorUnit = 0, 2, 1
    dash.add_chart(c3, "B27")

    c4 = BarChart()
    c4.type = "col"
    c4.add_data(Reference(calc, min_col=2, max_col=4, min_row=t4, max_row=t4_last), titles_from_data=True)
    c4.set_categories(Reference(calc, min_col=1, min_row=t4 + 1, max_row=t4_last))
    style_chart(c4, "Median breaches avoided across 50 synthetic seeds", None, "Breaches avoided (median)")
    dash.add_chart(c4, "J27")

    # Tables under the charts
    top = 45
    dash.merge_cells(f"B{top}:Q{top}")
    dash[f"B{top}"] = "Recovery gap: how much faster each service must restore to cut its breaches"
    dash[f"B{top}"].font = font(12, bold=True, color=INK)
    heads = ["Service", "", "Tolerance (min)", "Episodes", "Breaches", "Median (min)",
             "Cut to halve breaches", "Cut to clear all", "Same cut, median of 50 seeds (halve)"]
    widths = [2, 1, 1, 1, 1, 1, 1, 1, 2]
    col = 2
    head_cols = []
    for h, w in zip(heads, widths):
        if not h:
            continue
        first, last = get_column_letter(col), get_column_letter(col + w - 1)
        if w > 1:
            dash.merge_cells(f"{first}{top + 1}:{last}{top + 1}")
        dash[f"{first}{top + 1}"] = h
        head_cols.append((first, w))
        col += w
    for c in range(2, col):
        cell = dash.cell(top + 1, c)
        mono_header(cell)
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    dash.row_dimensions[top + 1].height = 30
    fields = ["service_name", "impact_tolerance_minutes", "episodes", "breaches", "median_minutes",
              "cut_to_halve_breaches_pct", "cut_to_clear_all_pct", "seed_median_cut_to_halve_pct"]
    for i in range(gapl - 1):
        r = top + 2 + i
        for (first, w), field in zip(head_cols, fields):
            ci = dash[f"{first}{r}"].column
            if w > 1:
                dash.merge_cells(f"{first}{r}:{get_column_letter(ci + w - 1)}{r}")
            src = f"Recovery_Gap!{gap[field]}{2 + i}"
            brs = f"Recovery_Gap!{gap['breaches']}{2 + i}"
            seeds = f"Recovery_Gap!{gap['seeds_with_breaches']}{2 + i}"
            if field == "seed_median_cut_to_halve_pct":
                formula = f'=IF({seeds}<25,"rare: "&{seeds}&" of 50 seeds",{src}/100)'
            elif field.endswith("_pct"):
                formula = f'=IF({brs}=0,"none",{src}/100)'
            else:
                formula = f"={src}"
            dash[f"{first}{r}"] = formula
            dash[f"{first}{r}"].number_format = "0%" if field.endswith("_pct") else "0"
            dash[f"{first}{r}"].font = font(10, bold=(field == "service_name"))
            dash[f"{first}{r}"].alignment = Alignment(horizontal="left" if field == "service_name" else "center")
            for c in range(ci, ci + w):
                dash.cell(r, c).border = Border(bottom=THIN)
    gap_end = top + 1 + gapl - 1
    dash.merge_cells(f"B{gap_end + 1}:Q{gap_end + 1}")
    dash[f"B{gap_end + 1}"] = ("Read: card authorisation needs about 31% faster restoration to halve its breaches, and the answer barely moves across 50 synthetic seeds. "
                               "Mortgage servicing has no breaches at the default seed and in 46 of 50 seeds.")
    dash[f"B{gap_end + 1}"].font = font(9, italic=True, color=GREY)
    dash[f"B{gap_end + 1}"].alignment = Alignment(wrap_text=True)
    dash.row_dimensions[gap_end + 1].height = 26

    st = gap_end + 3
    dash.merge_cells(f"B{st}:Q{st}")
    dash[f"B{st}"] = "Supplier concentration: what a full outage of each supplier would reach (no failover assumed)"
    dash[f"B{st}"].font = font(12, bold=True, color=INK)
    ex = info["Supplier_Exposure"][1]
    sheads = [("Supplier", "supplier_name", 2), ("Type", "supplier_type", 2), ("Substitutability", "substitutability", 2),
              ("Services supported", "service_names", 4), ("High-criticality", "high_criticality_services", 1),
              ("First breach (min)", "minutes_to_first_breach", 1), ("All breached (min)", "minutes_to_breach_all", 1),
              ("Illustrative customers", "illustrative_customer_base", 2)]
    col = 2
    for label, field, w in sheads:
        first, last = get_column_letter(col), get_column_letter(col + w - 1)
        if w > 1:
            dash.merge_cells(f"{first}{st + 1}:{last}{st + 1}")
        dash[f"{first}{st + 1}"] = label
        for c in range(col, col + w):
            cell = dash.cell(st + 1, c)
            mono_header(cell)
            cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        for i in range(len(suppliers)):
            r = st + 2 + i
            if w > 1:
                dash.merge_cells(f"{first}{r}:{last}{r}")
            dash[f"{first}{r}"] = f"=Supplier_Exposure!{ex[field]}{2 + i}"
            dash[f"{first}{r}"].number_format = "#,##0" if field == "illustrative_customer_base" else "General"
            dash[f"{first}{r}"].font = font(10, bold=(field == "supplier_name"))
            dash[f"{first}{r}"].alignment = Alignment(horizontal="left" if w > 1 and field != "illustrative_customer_base" else "center")
            for c in range(col, col + w):
                dash.cell(r, c).border = Border(bottom=THIN)
        col += w
    dash.row_dimensions[st + 1].height = 30
    sup_end = st + 1 + len(suppliers)
    dash.merge_cells(f"B{sup_end + 1}:Q{sup_end + 1}")
    dash[f"B{sup_end + 1}"] = ("Read: Provider Beta carries both payments and card authorisation, the two tightest tolerances, and is rated low substitutability. "
                               "An outage longer than 90 minutes breaches card authorisation; longer than two hours breaches both. It had no shared event in the default history, so the replay alone undervalues it.")
    dash[f"B{sup_end + 1}"].font = font(9, italic=True, color=GREY)
    dash[f"B{sup_end + 1}"].alignment = Alignment(wrap_text=True)
    dash.row_dimensions[sup_end + 1].height = 26

    pc = sup_end + 3
    dash.merge_cells(f"B{pc}:Q{pc}")
    dash[f"B{pc}"] = "External context: Open Banking API performance (published monthly aggregate, not linked to the bank above)"
    dash[f"B{pc}"].font = font(12, bold=True, color=INK)
    if include_public:
        pub, publ = info["Public_Monthly"][1], info["Public_Monthly"][2]
        c5 = LineChart()
        c5.add_data(Reference(wb["Public_Monthly"], min_col=6, max_col=7, min_row=1, max_row=publ), titles_from_data=True)
        c5.set_categories(Reference(wb["Public_Monthly"], min_col=2, min_row=2, max_row=publ))
        style_chart(c5, "Published API availability, unweighted vs weighted (%)", None, "%")
        from openpyxl.chart.series import SeriesLabel
        c5.series[0].tx = SeriesLabel(v="Unweighted availability")
        c5.series[1].tx = SeriesLabel(v="Weighted availability")
        c5.y_axis.scaling.min = 98.5
        c5.y_axis.scaling.max = 100
        c5.width = 31.5
        dash.add_chart(c5, f"B{pc + 2}")
        end = pc + 20
    else:
        dash.merge_cells(f"B{pc + 1}:Q{pc + 2}")
        dash[f"B{pc + 1}"] = ("Lowest published unweighted availability in Aug 2024 to Aug 2026: 98.87% (March 2026), against 99.83% weighted that month. "
                              "Source: Open Banking Limited, API performance statistics, openbanking.org.uk/api-performance. "
                              "The monthly series is kept out of this published file because it is not openly licensed for redistribution.")
        dash[f"B{pc + 1}"].font = font(9, color=INK)
        dash[f"B{pc + 1}"].alignment = Alignment(wrap_text=True, vertical="top")
        dash.row_dimensions[pc + 1].height = 22
        dash.row_dimensions[pc + 2].height = 22
        end = pc + 3
    dash.merge_cells(f"B{end}:Q{end}")
    dash[f"B{end}"] = ("Method: seeded generator v1.0 (seed 280926), 4 services, 5 suppliers, 8 dependencies, 42 episodes. "
                       "Exercise effects are assumed duration multipliers (0.9 / 0.7 / 0.5). Tolerances are illustrative policy settings, not regulatory thresholds. "
                       "See the Notes sheet and the repository README.")
    dash[f"B{end}"].font = font(8, italic=True, color=GREY)
    dash[f"B{end}"].alignment = Alignment(wrap_text=True)
    dash.row_dimensions[end].height = 34

    dash.page_setup.orientation = "portrait"
    dash.page_setup.paperSize = dash.PAPERSIZE_A3
    dash.page_setup.fitToWidth = 1
    dash.page_setup.fitToHeight = 1
    dash.sheet_properties.pageSetUpPr.fitToPage = True
    dash.print_area = f"A1:R{end}"
    dash.page_margins.left = dash.page_margins.right = 0.4

    # ---------- Notes ----------
    lines = [
        ("Notes and data honesty", True),
        ("What this is: a decision-support demonstration for a fictional UK retail bank. All internal records are simulated by 04_etl/generate_simulated_bank.py (version 1.0, seed 280926).", False),
        ("What it is not: an estimate of any real bank's incidents, outage probabilities, losses or control effectiveness.", False),
        ("Impact tolerances (90, 120, 180, 480 minutes) are illustrative policy settings chosen before the data was generated. FCA SYSC 15A requires firms to set their own; it sets no number.", False),
        ("Recovery exercise effects are assumptions: each eligible episode's duration is multiplied by 0.9 (cautious), 0.7 (central) or 0.5 (optimistic). Ranges across 50 seeds (280926 to 280975) describe invented worlds, not confidence intervals.", False),
        ("Recovery gap: the cut is the smallest uniform reduction in a service's restoration time that removes the stated share of its breaches. Reported values are rounded up.", False),
        ("Supplier stress: assumes a full outage of one supplier stops every dependent service for the outage length, with no failover. Customer base is the generator's illustrative scale.", False),
        ("Public context: Open Banking Limited API performance statistics (openbanking.org.uk/api-performance). Aggregate across reporting providers; it does not describe this bank and is never joined to it.", False),
        ("Refresh: run 08_dashboard/export_dashboard_data.py then 08_dashboard/build_excel_dashboard.py. Every dashboard figure is a formula over the data sheets.", False),
    ]
    notes.column_dimensions["A"].width = 130
    for i, (text, bold) in enumerate(lines, start=1):
        cell = notes.cell(i, 1, text)
        cell.font = font(13 if bold else 10, bold=bold, color=INK)
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    wb.move_sheet("Notes", offset=-(len(wb.sheetnames) - 2))
    wb.calculation.fullCalcOnLoad = True
    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)
    print(f"Saved {output.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-public", action="store_true")
    args = parser.parse_args()
    target = (ROOT / "02_data" / "processed" / "resilience_dashboard_with_public_context.xlsx"
              if args.include_public else ROOT / "08_dashboard" / "resilience_dashboard.xlsx")
    build(args.include_public, target)
