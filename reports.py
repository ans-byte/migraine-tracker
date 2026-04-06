import csv
import io
from datetime import date, timedelta
from calendar import monthrange

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from models import Migraine, SleepLog, WaterIntake, StressLog, db
from sqlalchemy import func


def _get_date_range(start_date, end_date):
    migraines = Migraine.query.filter(
        Migraine.date >= start_date, Migraine.date <= end_date
    ).all()
    sleep_logs = SleepLog.query.filter(
        SleepLog.date >= start_date, SleepLog.date <= end_date
    ).all()
    water_logs = WaterIntake.query.filter(
        WaterIntake.date >= start_date, WaterIntake.date <= end_date
    ).all()
    stress_logs = StressLog.query.filter(
        StressLog.date >= start_date, StressLog.date <= end_date
    ).all()
    return migraines, sleep_logs, water_logs, stress_logs


def _build_csv(start_date, end_date, label):
    migraines, sleep_logs, water_logs, stress_logs = _get_date_range(start_date, end_date)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([f"Migraine Tracker Report: {label}"])
    writer.writerow([f"Period: {start_date} to {end_date}"])
    writer.writerow([])

    writer.writerow(["=== MIGRAINE SUMMARY ==="])
    writer.writerow(["Date", "Severity", "Location", "Duration (hrs)", "Triggers", "Symptoms", "Medication", "Notes"])
    for m in migraines:
        writer.writerow([
            m.date, m.severity, m.location or "", m.duration_hours or "",
            m.triggers or "", m.symptoms or "", m.medication or "", m.notes or ""
        ])
    if not migraines:
        writer.writerow(["No migraines recorded"])
    writer.writerow([])

    total_m = len(migraines)
    avg_sev = round(sum(m.severity for m in migraines) / total_m, 2) if total_m else "N/A"
    writer.writerow(["Total Migraines", total_m])
    writer.writerow(["Average Severity", avg_sev])
    writer.writerow([])

    writer.writerow(["=== SLEEP LOG ==="])
    writer.writerow(["Date", "Hours Slept", "Quality (1-10)", "Wake Time", "Notes"])
    for s in sleep_logs:
        writer.writerow([s.date, s.hours_slept, s.quality or "", s.wake_time or "", s.notes or ""])
    if not sleep_logs:
        writer.writerow(["No sleep logs recorded"])
    writer.writerow([])

    if sleep_logs:
        avg_sleep = round(sum(s.hours_slept for s in sleep_logs) / len(sleep_logs), 2)
        writer.writerow(["Average Sleep Hours", avg_sleep])
    writer.writerow([])

    writer.writerow(["=== WATER INTAKE ==="])
    writer.writerow(["Date", "Cups"])
    for w in water_logs:
        writer.writerow([w.date, w.cups])
    if not water_logs:
        writer.writerow(["No water intake recorded"])
    if water_logs:
        writer.writerow(["Total Cups", sum(w.cups for w in water_logs)])
    writer.writerow([])

    writer.writerow(["=== STRESS LEVELS ==="])
    writer.writerow(["Date", "Level (1-10)", "Notes"])
    for st in stress_logs:
        writer.writerow([st.date, st.level, st.notes or ""])
    if not stress_logs:
        writer.writerow(["No stress logs recorded"])
    if stress_logs:
        avg_stress = round(sum(st.level for st in stress_logs) / len(stress_logs), 2)
        writer.writerow(["Average Stress Level", avg_stress])

    return output.getvalue()


def generate_weekly_csv(start_date):
    if isinstance(start_date, str):
        from datetime import datetime
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=6)
    label = f"Week of {start_date}"
    return _build_csv(start_date, end_date, label)


def generate_monthly_csv(year, month):
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    import calendar
    label = f"{calendar.month_name[month]} {year}"
    return _build_csv(start_date, end_date, label)


def _build_pdf(start_date, end_date, label):
    migraines, sleep_logs, water_logs, stress_logs = _get_date_range(start_date, end_date)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=18, spaceAfter=6, textColor=colors.HexColor("#4f46e5")
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=4,
        textColor=colors.HexColor("#374151")
    )
    normal_style = styles["Normal"]
    small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=9)

    story = []

    story.append(Paragraph("Migraine Tracker Report", title_style))
    story.append(Paragraph(f"{label} &nbsp;&nbsp; | &nbsp;&nbsp; {start_date} to {end_date}", normal_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb"), spaceAfter=10))
    story.append(Spacer(1, 0.1 * inch))

    # Migraine summary
    story.append(Paragraph("Migraine Summary", heading_style))
    total_m = len(migraines)
    avg_sev = round(sum(m.severity for m in migraines) / total_m, 1) if total_m else 0
    avg_dur = round(sum(m.duration_hours for m in migraines if m.duration_hours) / total_m, 1) if total_m else 0

    summary_data = [
        ["Metric", "Value"],
        ["Total Migraines", str(total_m)],
        ["Average Severity", str(avg_sev) if total_m else "N/A"],
        ["Average Duration (hrs)", str(avg_dur) if total_m else "N/A"],
    ]
    summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.15 * inch))

    if migraines:
        story.append(Paragraph("Migraine Details", heading_style))
        m_data = [["Date", "Sev", "Location", "Duration", "Triggers", "Medication"]]
        for m in migraines:
            m_data.append([
                str(m.date),
                str(m.severity),
                m.location or "-",
                f"{m.duration_hours}h" if m.duration_hours else "-",
                (m.triggers or "-")[:30],
                (m.medication or "-")[:20],
            ])
        m_table = Table(m_data, colWidths=[0.9*inch, 0.5*inch, 1.1*inch, 0.8*inch, 2.0*inch, 1.5*inch])
        m_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(m_table)
        story.append(Spacer(1, 0.15 * inch))

    # Sleep stats
    story.append(Paragraph("Sleep Statistics", heading_style))
    if sleep_logs:
        avg_sleep = round(sum(s.hours_slept for s in sleep_logs) / len(sleep_logs), 1)
        avg_quality = round(sum(s.quality for s in sleep_logs if s.quality) / len(sleep_logs), 1)
        sleep_data = [
            ["Metric", "Value"],
            ["Total Nights Logged", str(len(sleep_logs))],
            ["Average Hours Slept", str(avg_sleep)],
            ["Average Sleep Quality", str(avg_quality)],
        ]
    else:
        sleep_data = [["Metric", "Value"], ["No sleep data recorded", "-"]]

    sleep_table = Table(sleep_data, colWidths=[3 * inch, 3 * inch])
    sleep_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0891b2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sleep_table)
    story.append(Spacer(1, 0.15 * inch))

    # Water intake
    story.append(Paragraph("Water Intake", heading_style))
    if water_logs:
        total_cups = sum(w.cups for w in water_logs)
        avg_cups = round(total_cups / len(water_logs), 1)
        water_data = [
            ["Metric", "Value"],
            ["Days Tracked", str(len(water_logs))],
            ["Total Cups", str(total_cups)],
            ["Average Cups/Day", str(avg_cups)],
        ]
    else:
        water_data = [["Metric", "Value"], ["No water intake recorded", "-"]]

    water_table = Table(water_data, colWidths=[3 * inch, 3 * inch])
    water_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(water_table)
    story.append(Spacer(1, 0.15 * inch))

    # Stress levels
    story.append(Paragraph("Stress Levels", heading_style))
    if stress_logs:
        avg_stress = round(sum(s.level for s in stress_logs) / len(stress_logs), 1)
        stress_data = [
            ["Metric", "Value"],
            ["Days Tracked", str(len(stress_logs))],
            ["Average Stress Level", str(avg_stress)],
            ["Highest Stress", str(max(s.level for s in stress_logs))],
            ["Lowest Stress", str(min(s.level for s in stress_logs))],
        ]
    else:
        stress_data = [["Metric", "Value"], ["No stress data recorded", "-"]]

    stress_table = Table(stress_data, colWidths=[3 * inch, 3 * inch])
    stress_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(stress_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_weekly_pdf(start_date):
    if isinstance(start_date, str):
        from datetime import datetime
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=6)
    label = f"Week of {start_date}"
    return _build_pdf(start_date, end_date, label)


def generate_monthly_pdf(year, month):
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    import calendar
    label = f"{calendar.month_name[month]} {year}"
    return _build_pdf(start_date, end_date, label)
