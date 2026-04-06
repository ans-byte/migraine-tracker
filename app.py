from flask import Flask, render_template, request, jsonify, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from collections import Counter
import io
import os

from models import db, Migraine, FoodLog, SleepLog, WaterIntake, CaffeineLog, StressLog, MenstrualLog
import reports as report_gen

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "migraine-tracker-secret-2024")

db.init_app(app)

with app.app_context():
    db.create_all()


# ── Page routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    today = date.today()
    month_start = today.replace(day=1)

    total_this_month = Migraine.query.filter(Migraine.date >= month_start).count()
    migraines_month = Migraine.query.filter(Migraine.date >= month_start).all()
    avg_severity = (
        round(sum(m.severity for m in migraines_month) / len(migraines_month), 1)
        if migraines_month else 0
    )

    last_migraine = Migraine.query.order_by(Migraine.date.desc()).first()
    days_since = (today - last_migraine.date).days if last_migraine else None

    sleep_logs = SleepLog.query.filter(SleepLog.date >= month_start).all()
    avg_sleep = (
        round(sum(s.hours_slept for s in sleep_logs) / len(sleep_logs), 1)
        if sleep_logs else 0
    )

    return render_template(
        "index.html",
        today=today,
        total_this_month=total_this_month,
        avg_severity=avg_severity,
        days_since=days_since,
        avg_sleep=avg_sleep,
    )


@app.route("/log-migraine")
def log_migraine():
    recent = Migraine.query.order_by(Migraine.date.desc()).limit(5).all()
    return render_template("log_migraine.html", today=date.today(), recent_migraines=recent)


@app.route("/log-health")
def log_health():
    return render_template("log_health.html", today=date.today())


@app.route("/reports")
def reports():
    return render_template("reports.html", today=date.today())


@app.route("/statistics")
def statistics():
    return render_template("statistics.html")


# ── API: save entries ─────────────────────────────────────────────────────────

@app.route("/api/migraine", methods=["POST"])
def api_save_migraine():
    data = request.get_json(silent=True) or {}
    try:
        entry_date = datetime.strptime(data.get("date", str(date.today())), "%Y-%m-%d").date()
        severity = int(data.get("severity", 5))
        if not 1 <= severity <= 10:
            return jsonify({"error": "Severity must be between 1 and 10"}), 400

        triggers = data.get("triggers", [])
        symptoms = data.get("symptoms", [])
        if isinstance(triggers, list):
            triggers = ",".join(triggers)
        if isinstance(symptoms, list):
            symptoms = ",".join(symptoms)

        entry = Migraine(
            date=entry_date,
            severity=severity,
            location=data.get("location"),
            duration_hours=float(data["duration_hours"]) if data.get("duration_hours") else None,
            triggers=triggers,
            symptoms=symptoms,
            medication=data.get("medication"),
            notes=data.get("notes"),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "id": entry.id, "message": "Migraine entry saved"}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@app.route("/api/food", methods=["POST"])
def api_save_food():
    data = request.get_json(silent=True) or {}
    try:
        entry = FoodLog(
            date=datetime.strptime(data.get("date", str(date.today())), "%Y-%m-%d").date(),
            meal_type=data.get("meal_type", "snack"),
            items=data.get("items"),
            ingredients=data.get("ingredients"),
            notes=data.get("notes"),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "id": entry.id, "message": "Food entry saved"}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@app.route("/api/sleep", methods=["POST"])
def api_save_sleep():
    data = request.get_json(silent=True) or {}
    try:
        hours = float(data.get("hours_slept", 0))
        entry = SleepLog(
            date=datetime.strptime(data.get("date", str(date.today())), "%Y-%m-%d").date(),
            hours_slept=hours,
            quality=int(data["quality"]) if data.get("quality") else None,
            wake_time=data.get("wake_time"),
            notes=data.get("notes"),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "id": entry.id, "message": "Sleep entry saved"}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@app.route("/api/water", methods=["POST"])
def api_save_water():
    data = request.get_json(silent=True) or {}
    try:
        entry = WaterIntake(
            date=datetime.strptime(data.get("date", str(date.today())), "%Y-%m-%d").date(),
            cups=float(data.get("cups", 0)),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "id": entry.id, "message": "Water intake saved"}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@app.route("/api/caffeine", methods=["POST"])
def api_save_caffeine():
    data = request.get_json(silent=True) or {}
    try:
        entry = CaffeineLog(
            date=datetime.strptime(data.get("date", str(date.today())), "%Y-%m-%d").date(),
            cups=float(data.get("cups", 0)),
            drink_type=data.get("drink_type"),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "id": entry.id, "message": "Caffeine entry saved"}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@app.route("/api/stress", methods=["POST"])
def api_save_stress():
    data = request.get_json(silent=True) or {}
    try:
        level = int(data.get("level", 5))
        if not 1 <= level <= 10:
            return jsonify({"error": "Stress level must be between 1 and 10"}), 400
        entry = StressLog(
            date=datetime.strptime(data.get("date", str(date.today())), "%Y-%m-%d").date(),
            level=level,
            notes=data.get("notes"),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "id": entry.id, "message": "Stress entry saved"}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@app.route("/api/menstrual", methods=["POST"])
def api_save_menstrual():
    data = request.get_json(silent=True) or {}
    try:
        entry = MenstrualLog(
            date=datetime.strptime(data.get("date", str(date.today())), "%Y-%m-%d").date(),
            flow_level=data.get("flow_level"),
            notes=data.get("notes"),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "id": entry.id, "message": "Menstrual entry saved"}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


# ── API: read/delete ──────────────────────────────────────────────────────────

@app.route("/api/migraines")
def api_list_migraines():
    migraines = Migraine.query.order_by(Migraine.date.desc()).limit(50).all()
    return jsonify([m.to_dict() for m in migraines])


@app.route("/api/migraine/<int:entry_id>", methods=["DELETE"])
def api_delete_migraine(entry_id):
    entry = db.session.get(Migraine, entry_id)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"success": True, "message": "Migraine entry deleted"})


@app.route("/api/recent")
def api_recent():
    today = date.today()
    cutoff = today - timedelta(days=30)
    items = []

    for m in Migraine.query.filter(Migraine.date >= cutoff).all():
        items.append({"type": "migraine", "date": m.date.isoformat(),
                      "label": f"Migraine – Severity {m.severity}", "severity": m.severity})
    for s in SleepLog.query.filter(SleepLog.date >= cutoff).all():
        items.append({"type": "sleep", "date": s.date.isoformat(),
                      "label": f"Sleep – {s.hours_slept}h"})
    for w in WaterIntake.query.filter(WaterIntake.date >= cutoff).all():
        items.append({"type": "water", "date": w.date.isoformat(),
                      "label": f"Water – {w.cups} cups"})
    for st in StressLog.query.filter(StressLog.date >= cutoff).all():
        items.append({"type": "stress", "date": st.date.isoformat(),
                      "label": f"Stress – Level {st.level}"})

    items.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(items[:20])


@app.route("/api/calendar-data")
def api_calendar_data():
    today = date.today()
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    migraines = Migraine.query.filter(
        Migraine.date >= month_start, Migraine.date < next_month
    ).all()
    return jsonify([{"date": m.date.isoformat(), "severity": m.severity} for m in migraines])


@app.route("/api/stats")
def api_stats():
    today = date.today()
    thirty_ago = today - timedelta(days=30)
    twelve_weeks_ago = today - timedelta(weeks=12)

    # Severity trend last 30 days
    migraines_30 = Migraine.query.filter(Migraine.date >= thirty_ago).order_by(Migraine.date).all()
    severity_trend = [{"date": m.date.isoformat(), "severity": m.severity} for m in migraines_30]

    # Weekly migraine frequency last 12 weeks
    migraines_12w = Migraine.query.filter(Migraine.date >= twelve_weeks_ago).all()
    week_counts = {}
    for m in migraines_12w:
        iso = m.date.isocalendar()
        key = f"{iso[0]}-W{iso[1]:02d}"
        week_counts[key] = week_counts.get(key, 0) + 1
    weekly_frequency = [{"week": k, "count": v} for k, v in sorted(week_counts.items())]

    # Top triggers
    all_migraines = Migraine.query.all()
    trigger_list = []
    for m in all_migraines:
        if m.triggers:
            trigger_list.extend([t.strip() for t in m.triggers.split(",") if t.strip()])
    trigger_counts = dict(Counter(trigger_list).most_common(8))

    # Sleep vs migraine correlation (last 30 days)
    sleep_30 = SleepLog.query.filter(SleepLog.date >= thirty_ago).all()
    sleep_by_date = {s.date.isoformat(): s.hours_slept for s in sleep_30}
    migraine_dates = {m.date.isoformat() for m in migraines_30}
    sleep_migraine = [
        {"date": d, "hours": h, "had_migraine": d in migraine_dates}
        for d, h in sleep_by_date.items()
    ]

    # Water intake last 30 days
    water_30 = WaterIntake.query.filter(WaterIntake.date >= thirty_ago).order_by(WaterIntake.date).all()
    water_trend = [{"date": w.date.isoformat(), "cups": w.cups} for w in water_30]

    # Stress vs migraine (last 30 days)
    stress_30 = StressLog.query.filter(StressLog.date >= thirty_ago).order_by(StressLog.date).all()
    stress_trend = [{"date": s.date.isoformat(), "level": s.level} for s in stress_30]

    # Location frequency
    loc_counts = {}
    for m in all_migraines:
        if m.location:
            loc_counts[m.location] = loc_counts.get(m.location, 0) + 1

    # Avg duration
    durations = [m.duration_hours for m in all_migraines if m.duration_hours]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0

    return jsonify({
        "severity_trend": severity_trend,
        "weekly_frequency": weekly_frequency,
        "trigger_counts": trigger_counts,
        "sleep_migraine": sleep_migraine,
        "water_trend": water_trend,
        "stress_trend": stress_trend,
        "location_counts": loc_counts,
        "avg_duration": avg_duration,
        "total_migraines": len(all_migraines),
    })


# ── Download routes ───────────────────────────────────────────────────────────

@app.route("/download/weekly-csv")
def download_weekly_csv():
    start_str = request.args.get("start", str(date.today() - timedelta(days=date.today().weekday())))
    csv_content = report_gen.generate_weekly_csv(start_str)
    buf = io.BytesIO(csv_content.encode("utf-8"))
    return send_file(buf, mimetype="text/csv",
                     as_attachment=True,
                     download_name=f"migraine-weekly-{start_str}.csv")


@app.route("/download/monthly-csv")
def download_monthly_csv():
    today = date.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))
    csv_content = report_gen.generate_monthly_csv(year, month)
    buf = io.BytesIO(csv_content.encode("utf-8"))
    return send_file(buf, mimetype="text/csv",
                     as_attachment=True,
                     download_name=f"migraine-{year}-{month:02d}.csv")


@app.route("/download/weekly-pdf")
def download_weekly_pdf():
    start_str = request.args.get("start", str(date.today() - timedelta(days=date.today().weekday())))
    pdf_bytes = report_gen.generate_weekly_pdf(start_str)
    buf = io.BytesIO(pdf_bytes)
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"migraine-weekly-{start_str}.pdf")


@app.route("/download/monthly-pdf")
def download_monthly_pdf():
    today = date.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))
    pdf_bytes = report_gen.generate_monthly_pdf(year, month)
    buf = io.BytesIO(pdf_bytes)
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"migraine-{year}-{month:02d}.pdf")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
