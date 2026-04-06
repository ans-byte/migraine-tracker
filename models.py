from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Migraine(db.Model):
    __tablename__ = "migraines"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    severity = db.Column(db.Integer, nullable=False)  # 1-10
    location = db.Column(db.String(50), nullable=True)
    duration_hours = db.Column(db.Float, nullable=True)
    triggers = db.Column(db.String(255), nullable=True)  # comma-separated
    symptoms = db.Column(db.String(255), nullable=True)  # comma-separated
    medication = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "severity": self.severity,
            "location": self.location,
            "duration_hours": self.duration_hours,
            "triggers": self.triggers.split(",") if self.triggers else [],
            "symptoms": self.symptoms.split(",") if self.symptoms else [],
            "medication": self.medication,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class FoodLog(db.Model):
    __tablename__ = "food_logs"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast/lunch/dinner/snack
    items = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "meal_type": self.meal_type,
            "items": self.items,
            "ingredients": self.ingredients,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class SleepLog(db.Model):
    __tablename__ = "sleep_logs"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hours_slept = db.Column(db.Float, nullable=False)
    quality = db.Column(db.Integer, nullable=True)  # 1-10
    wake_time = db.Column(db.String(10), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "hours_slept": self.hours_slept,
            "quality": self.quality,
            "wake_time": self.wake_time,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class WaterIntake(db.Model):
    __tablename__ = "water_intakes"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    cups = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "cups": self.cups,
            "created_at": self.created_at.isoformat(),
        }


class CaffeineLog(db.Model):
    __tablename__ = "caffeine_logs"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    cups = db.Column(db.Float, nullable=False)
    drink_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "cups": self.cups,
            "drink_type": self.drink_type,
            "created_at": self.created_at.isoformat(),
        }


class StressLog(db.Model):
    __tablename__ = "stress_logs"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1-10
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "level": self.level,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class MenstrualLog(db.Model):
    __tablename__ = "menstrual_logs"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    flow_level = db.Column(db.String(20), nullable=True)  # light/medium/heavy/spotting
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "flow_level": self.flow_level,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }
