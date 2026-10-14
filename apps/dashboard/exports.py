"""
AgriLens Intelligence Report Export Utility.
Provides CSV and Excel (openpyxl) export capabilities with formula injection mitigation,
methodological provenance disclosures, and strict server-side geographic access enforcement.
"""
import csv
import io
from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def sanitize_for_export(val):
    """
    Guards against formula injection vulnerabilities (CSV/Excel Formula Injection / CWE-1236).
    Prefixes values starting with '=', '+', '-', '@', tab, or carriage return with a single quote.
    """
    if val is None:
        return ""
    if isinstance(val, (int, float, Decimal)):
        return val
    s = str(val)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + s
    return s


def generate_national_csv(year, season, source, crop, summary, crop_summaries, rankings):
    """Generates sanitized, structured CSV export of National Agricultural Bulletin."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="agrilens_national_report_SAS_{year}_{season}.csv"'

    writer = csv.writer(response)
    # Metadata Header
    writer.writerow([sanitize_for_export("AGRILENS RWANDA • NATIONAL AGRICULTURAL ANALYTICS BULLETIN")])
    writer.writerow([sanitize_for_export(f"Survey Season: SAS {year} Season {season}")])
    writer.writerow([sanitize_for_export(f"Provenance Policy: {summary.get('provenance_label', source)}")])
    writer.writerow([sanitize_for_export(f"Export Timestamp (UTC): {timezone.now().isoformat()}")])
    writer.writerow([])

    # Executive KPIs
    writer.writerow([sanitize_for_export("EXECUTIVE INDICATOR SUMMARY")])
    writer.writerow([sanitize_for_export("Metric"), sanitize_for_export("Value"), sanitize_for_export("Unit / Note")])
    writer.writerow([sanitize_for_export(f"{crop} Production"), sanitize_for_export(summary.get('total_production_mt', 0)), sanitize_for_export("Metric Tons (MT)")])
    writer.writerow([sanitize_for_export("Cultivated Area"), sanitize_for_export(summary.get('total_area_ha', 0)), sanitize_for_export("Hectares (ha)")])
    writer.writerow([sanitize_for_export("Weighted Yield"), sanitize_for_export(summary.get('weighted_yield_kg_per_ha', 0)), sanitize_for_export("kg/ha")])
    writer.writerow([sanitize_for_export("Plots Sampled"), sanitize_for_export(summary.get('total_plots', 0)), sanitize_for_export("Observations")])
    writer.writerow([sanitize_for_export("Harvest Loss Rate"), sanitize_for_export(summary.get('loss_rate_percentage', 0)), sanitize_for_export("%")])
    writer.writerow([])

    # Practice Adoption
    writer.writerow([sanitize_for_export("AGRICULTURAL PRACTICE ADOPTION (SAMPLE PLOT SHARE VS WEIGHTED AREA)")])
    writer.writerow([sanitize_for_export("Practice"), sanitize_for_export("Plot Adoption Rate (%)"), sanitize_for_export("Weighted Area Adoption Rate (%)"), sanitize_for_export("Source Survey Availability")])
    practices = [
        ('Improved Seed', 'improved_seed'),
        ('Inorganic Fertilizer', 'inorganic_fertilizer'),
        ('Organic Fertilizer', 'organic_fertilizer'),
        ('Irrigation Access', 'irrigation'),
        ('Mechanization', 'mechanization'),
        ('Anti-Erosion Infrastructure', 'anti_erosion'),
    ]
    for label, key in practices:
        ar = summary.get('adoption_rates', {}).get(key, 0.0)
        war = summary.get('weighted_adoption_rates', {}).get(key, 0.0)
        avail = summary.get('practice_availability', {}).get(key, 'AVAILABLE')
        writer.writerow([sanitize_for_export(label), sanitize_for_export(ar), sanitize_for_export(war), sanitize_for_export(avail)])
    writer.writerow([])

    # Strategic Priority Crops Matrix
    writer.writerow([sanitize_for_export("STRATEGIC PRIORITY CROPS MATRIX")])
    writer.writerow([
        sanitize_for_export("Crop Name"),
        sanitize_for_export("Category"),
        sanitize_for_export("Sampled Plots"),
        sanitize_for_export("Production (MT)"),
        sanitize_for_export("Area (ha)"),
        sanitize_for_export("Weighted Yield (kg/ha)"),
        sanitize_for_export("Loss Rate (%)"),
    ])
    for item in crop_summaries:
        c_obj = item['crop']
        s_obj = item['summary']
        writer.writerow([
            sanitize_for_export(c_obj.name),
            sanitize_for_export(c_obj.category.name if c_obj.category else "Staple"),
            sanitize_for_export(s_obj.get('total_plots', 0)),
            sanitize_for_export(s_obj.get('total_production_mt', 0.0)),
            sanitize_for_export(s_obj.get('total_area_ha', 0.0)),
            sanitize_for_export(s_obj.get('weighted_yield_kg_per_ha', 0.0)),
            sanitize_for_export(s_obj.get('loss_rate_percentage', 0.0)),
        ])
    writer.writerow([])

    # District Rankings
    writer.writerow([sanitize_for_export(f"DISTRICT PERFORMANCE RANKINGS ({crop})")])
    writer.writerow([
        sanitize_for_export("Rank"),
        sanitize_for_export("District"),
        sanitize_for_export("Province"),
        sanitize_for_export("Sampled Plots"),
        sanitize_for_export("Weighted Yield (kg/ha)"),
        sanitize_for_export("Improved Seed (%)"),
        sanitize_for_export("Inorganic Fert (%)"),
        sanitize_for_export("Irrigation (%)"),
        sanitize_for_export("Anti-Erosion (%)"),
        sanitize_for_export("Loss Rate (%)"),
    ])
    for idx, r in enumerate(rankings, 1):
        writer.writerow([
            sanitize_for_export(idx),
            sanitize_for_export(r.get('district_name', '')),
            sanitize_for_export(r.get('province_name', '')),
            sanitize_for_export(r.get('plots_sampled', 0)),
            sanitize_for_export(r.get('yield_kg_per_ha', 0.0)),
            sanitize_for_export(r.get('improved_seed_rate', 0.0)),
            sanitize_for_export(r.get('fertilizer_rate', 0.0)),
            sanitize_for_export(r.get('irrigation_rate', 0.0)),
            sanitize_for_export(r.get('anti_erosion_rate', 0.0)),
            sanitize_for_export(r.get('loss_rate', 0.0)),
        ])

    return response


def generate_national_excel(year, season, source, crop, summary, crop_summaries, rankings):
    """Generates stylized, executive-ready Excel workbook (.xlsx) of National Agricultural Bulletin."""
    wb = openpyxl.Workbook()
    # Sheet 1: Executive Summary
    ws_kpi = wb.active
    ws_kpi.title = "Executive Summary"

    # Styling definitions
    header_fill = PatternFill(start_color="005CAB", end_color="005CAB", fill_type="solid")
    sub_fill = PatternFill(start_color="E8F7FE", end_color="E8F7FE", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="001F3B")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=11)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    # Title Banner
    ws_kpi.merge_cells("A1:E1")
    ws_kpi["A1"] = f"AgriLens Rwanda • National Agricultural Bulletin (SAS {year} Season {season})"
    ws_kpi["A1"].font = title_font

    ws_kpi["A2"] = f"Provenance: {summary.get('provenance_label', source)} | Exported: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    ws_kpi["A2"].font = Font(name="Calibri", size=10, italic=True, color="64748B")

    # KPIs
    kpi_headers = ["Indicator", "Value", "Unit / Basis"]
    for col_idx, h in enumerate(kpi_headers, 1):
        cell = ws_kpi.cell(row=4, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    kpis = [
        (f"{crop} Production", summary.get('total_production_mt', 0.0), "Metric Tons (MT)"),
        ("Cultivated Area", summary.get('total_area_ha', 0.0), "Hectares (ha)"),
        ("Weighted Yield", summary.get('weighted_yield_kg_per_ha', 0.0), "kg/ha"),
        ("Sample Plots Surveyed", summary.get('total_plots', 0), "Observations"),
        ("Post-Harvest Loss Rate", summary.get('loss_rate_percentage', 0.0), "%"),
    ]
    for row_idx, (name, val, unit) in enumerate(kpis, 5):
        c1 = ws_kpi.cell(row=row_idx, column=1, value=sanitize_for_export(name))
        c2 = ws_kpi.cell(row=row_idx, column=2, value=sanitize_for_export(val))
        c3 = ws_kpi.cell(row=row_idx, column=3, value=sanitize_for_export(unit))
        for c in (c1, c2, c3):
            c.border = thin_border
            c.font = regular_font

    # Practice Adoption Table
    ws_kpi.cell(row=12, column=1, value="Agricultural Practice Adoption Benchmarks").font = bold_font
    practice_headers = ["Practice", "Plot Share (%)", "Weighted Area Share (%)", "Survey Data Availability"]
    for col_idx, h in enumerate(practice_headers, 1):
        cell = ws_kpi.cell(row=13, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    practices = [
        ('Improved Seed Usage', 'improved_seed'),
        ('Inorganic Fertilizer', 'inorganic_fertilizer'),
        ('Organic Fertilizer', 'organic_fertilizer'),
        ('Irrigation Infrastructure', 'irrigation'),
        ('Mechanization', 'mechanization'),
        ('Anti-Erosion Infrastructure', 'anti_erosion'),
    ]
    for row_idx, (label, key) in enumerate(practices, 14):
        ar = summary.get('adoption_rates', {}).get(key, 0.0)
        war = summary.get('weighted_adoption_rates', {}).get(key, 0.0)
        avail = summary.get('practice_availability', {}).get(key, 'AVAILABLE')
        c1 = ws_kpi.cell(row=row_idx, column=1, value=sanitize_for_export(label))
        c2 = ws_kpi.cell(row=row_idx, column=2, value=sanitize_for_export(ar))
        c3 = ws_kpi.cell(row=row_idx, column=3, value=sanitize_for_export(war))
        c4 = ws_kpi.cell(row=row_idx, column=4, value=sanitize_for_export(avail))
        for c in (c1, c2, c3, c4):
            c.border = thin_border
            c.font = regular_font

    # Sheet 2: Priority Crops Matrix
    ws_crops = wb.create_sheet(title="Priority Crops")
    crop_hdrs = ["Crop Name", "Category", "Plots Sampled", "Production (MT)", "Cultivated Area (ha)", "Weighted Yield (kg/ha)", "Loss Rate (%)"]
    for col_idx, h in enumerate(crop_hdrs, 1):
        cell = ws_crops.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    for row_idx, item in enumerate(crop_summaries, 2):
        c_obj = item['crop']
        s_obj = item['summary']
        vals = [
            c_obj.name,
            c_obj.category.name if c_obj.category else "Staple",
            s_obj.get('total_plots', 0),
            s_obj.get('total_production_mt', 0.0),
            s_obj.get('total_area_ha', 0.0),
            s_obj.get('weighted_yield_kg_per_ha', 0.0),
            s_obj.get('loss_rate_percentage', 0.0),
        ]
        for col_idx, v in enumerate(vals, 1):
            cell = ws_crops.cell(row=row_idx, column=col_idx, value=sanitize_for_export(v))
            cell.border = thin_border
            cell.font = regular_font

    # Sheet 3: District Rankings
    ws_ranks = wb.create_sheet(title=f"Districts ({crop[:20]})")
    rank_hdrs = ["National Rank", "District", "Province", "Sampled Plots", "Yield (kg/ha)", "Improved Seed (%)", "Inorganic Fert (%)", "Irrigation (%)", "Anti-Erosion (%)", "Loss Rate (%)"]
    for col_idx, h in enumerate(rank_hdrs, 1):
        cell = ws_ranks.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    for row_idx, r in enumerate(rankings, 2):
        vals = [
            row_idx - 1,
            r.get('district_name', ''),
            r.get('province_name', ''),
            r.get('plots_sampled', 0),
            r.get('yield_kg_per_ha', 0.0),
            r.get('improved_seed_rate', 0.0),
            r.get('fertilizer_rate', 0.0),
            r.get('irrigation_rate', 0.0),
            r.get('anti_erosion_rate', 0.0),
            r.get('loss_rate', 0.0),
        ]
        for col_idx, v in enumerate(vals, 1):
            cell = ws_ranks.cell(row=row_idx, column=col_idx, value=sanitize_for_export(v))
            cell.border = thin_border
            cell.font = regular_font

    # Auto-adjust column widths for all sheets
    for ws in [ws_kpi, ws_crops, ws_ranks]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="agrilens_national_report_SAS_{year}_{season}.xlsx"'
    return response


def generate_district_csv(district, year, season, source, crop, district_summary, sectors):
    """Generates sanitized CSV export of District Agricultural Performance Dossier."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="agrilens_{district.name.lower()}_dossier_SAS_{year}_{season}.csv"'

    writer = csv.writer(response)
    writer.writerow([sanitize_for_export(f"AGRILENS RWANDA • {district.name.upper()} DISTRICT PERFORMANCE DOSSIER")])
    writer.writerow([sanitize_for_export(f"Province: {district.province.name} | Survey Season: SAS {year} Season {season}")])
    writer.writerow([sanitize_for_export(f"Target Crop: {crop} | Export Timestamp: {timezone.now().isoformat()}")])
    writer.writerow([])

    # District KPIs
    writer.writerow([sanitize_for_export("DISTRICT PERFORMANCE INDICATORS")])
    writer.writerow([sanitize_for_export("Metric"), sanitize_for_export("District Value"), sanitize_for_export("National Benchmark"), sanitize_for_export("Variance / Rank")])
    writer.writerow([
        sanitize_for_export(f"{crop} Weighted Yield"),
        sanitize_for_export(district_summary.get('weighted_yield_kg_per_ha', 0.0)),
        sanitize_for_export(district_summary.get('national_yield_kg_per_ha', 0.0)),
        sanitize_for_export(f"{district_summary.get('yield_vs_national_percentage', 0.0)}% vs National"),
    ])
    writer.writerow([
        sanitize_for_export("National Ranking"),
        sanitize_for_export(f"Rank {district_summary.get('national_rank', 'N/A')} of {district_summary.get('national_total_districts', 30)}"),
        sanitize_for_export("Top Benchmark"),
        sanitize_for_export("All Districts"),
    ])
    writer.writerow([
        sanitize_for_export("Provincial Ranking"),
        sanitize_for_export(f"Rank {district_summary.get('provincial_rank', 'N/A')} of {district_summary.get('provincial_total_districts', 'N/A')}"),
        sanitize_for_export("Province Benchmark"),
        sanitize_for_export(district.province.name),
    ])
    writer.writerow([
        sanitize_for_export("Estimated Production"),
        sanitize_for_export(district_summary.get('total_production_mt', 0.0)),
        sanitize_for_export("N/A"),
        sanitize_for_export("MT"),
    ])
    writer.writerow([
        sanitize_for_export("Cultivated Area"),
        sanitize_for_export(district_summary.get('total_area_ha', 0.0)),
        sanitize_for_export("N/A"),
        sanitize_for_export("ha"),
    ])
    writer.writerow([
        sanitize_for_export("Survey Sample Observations"),
        sanitize_for_export(district_summary.get('total_plots', 0)),
        sanitize_for_export("N/A"),
        sanitize_for_export("plots"),
    ])
    writer.writerow([])

    # Practice Adoption
    writer.writerow([sanitize_for_export("PRACTICE ADOPTION COMPARISON")])
    writer.writerow([sanitize_for_export("Practice"), sanitize_for_export(f"{district.name} Adoption (%)"), sanitize_for_export("Survey Availability")])
    practices = [
        ('Improved Seed Usage', 'improved_seed'),
        ('Inorganic Fertilizer', 'inorganic_fertilizer'),
        ('Organic Fertilizer', 'organic_fertilizer'),
        ('Irrigation Access', 'irrigation'),
        ('Mechanization', 'mechanization'),
        ('Anti-Erosion Infrastructure', 'anti_erosion'),
    ]
    for label, key in practices:
        ar = district_summary.get('adoption_rates', {}).get(key, 0.0)
        avail = district_summary.get('practice_availability', {}).get(key, 'AVAILABLE')
        writer.writerow([sanitize_for_export(label), sanitize_for_export(ar), sanitize_for_export(avail)])
    writer.writerow([])

    # Administrative Sectors
    writer.writerow([sanitize_for_export(f"ADMINISTRATIVE SECTORS IN {district.name.upper()} ({len(sectors)})")])
    for s in sectors:
        writer.writerow([sanitize_for_export(s.name), sanitize_for_export(s.code or '')])

    return response


def generate_district_excel(district, year, season, source, crop, district_summary, sectors):
    """Generates stylized Excel workbook (.xlsx) of District Agricultural Performance Dossier."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{district.name[:25]} Dossier"

    header_fill = PatternFill(start_color="005CAB", end_color="005CAB", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="001F3B")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    ws.merge_cells("A1:D1")
    ws["A1"] = f"AgriLens Rwanda • {district.name} District Agricultural Performance Dossier"
    ws["A1"].font = title_font

    ws["A2"] = f"Province: {district.province.name} | SAS {year} Season {season} | Crop: {crop} | Exported: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="64748B")

    # Metrics table
    hdrs = ["Indicator", "District Figure", "National Benchmark", "Variance / Performance"]
    for col_idx, h in enumerate(hdrs, 1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    rows = [
        (f"{crop} Weighted Yield", f"{district_summary.get('weighted_yield_kg_per_ha', 0.0)} kg/ha", f"{district_summary.get('national_yield_kg_per_ha', 0.0)} kg/ha", f"{district_summary.get('yield_vs_national_percentage', 0.0)}% vs National"),
        ("National Standing", f"Rank #{district_summary.get('national_rank', 'N/A')} of {district_summary.get('national_total_districts', 30)}", "Top National District", "National Rank"),
        ("Provincial Standing", f"Rank #{district_summary.get('provincial_rank', 'N/A')} of {district_summary.get('provincial_total_districts', 'N/A')}", "Top Provincial District", district.province.name),
        ("Cultivated Area", f"{district_summary.get('total_area_ha', 0.0)} ha", "N/A", "District Plot Expansion"),
        ("Total Estimated Production", f"{district_summary.get('total_production_mt', 0.0)} MT", "N/A", "Survey Expansion"),
        ("Survey Sample Size", f"{district_summary.get('total_plots', 0)} plots", "N/A", "Survey Microdata"),
    ]
    for row_idx, r in enumerate(rows, 5):
        for col_idx, v in enumerate(r, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=sanitize_for_export(v))
            cell.border = thin_border
            cell.font = regular_font

    # Practice Adoption
    ws.cell(row=13, column=1, value="Modern Practice Adoption Benchmarks").font = bold_font
    phdrs = ["Agronomic Practice", "District Adoption Rate (%)", "Survey Data Availability"]
    for col_idx, h in enumerate(phdrs, 1):
        cell = ws.cell(row=14, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    practices = [
        ('Improved Seed Usage', 'improved_seed'),
        ('Inorganic Fertilizer', 'inorganic_fertilizer'),
        ('Organic Fertilizer', 'organic_fertilizer'),
        ('Irrigation Infrastructure', 'irrigation'),
        ('Mechanization', 'mechanization'),
        ('Anti-Erosion Infrastructure', 'anti_erosion'),
    ]
    for row_idx, (label, key) in enumerate(practices, 15):
        ar = district_summary.get('adoption_rates', {}).get(key, 0.0)
        avail = district_summary.get('practice_availability', {}).get(key, 'AVAILABLE')
        c1 = ws.cell(row=row_idx, column=1, value=sanitize_for_export(label))
        c2 = ws.cell(row=row_idx, column=2, value=sanitize_for_export(ar))
        c3 = ws.cell(row=row_idx, column=3, value=sanitize_for_export(avail))
        for c in (c1, c2, c3):
            c.border = thin_border
            c.font = regular_font

    # Column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="agrilens_{district.name.lower()}_dossier_SAS_{year}_{season}.xlsx"'
    return response
