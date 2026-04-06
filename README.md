# Migraine Tracker

A Python Flask web application for tracking migraines and related health metrics. Log your migraines, sleep, water intake, caffeine, stress, and menstrual data. Visualize patterns with charts and download detailed reports.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

## Usage

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Features

- **Dashboard** – Stats overview, recent activity feed, mini calendar, trend chart
- **Log Migraine** – Record severity, location, duration, triggers, symptoms, and medication
- **Health Log** – Track sleep, water intake, caffeine, stress, and menstrual data
- **Statistics** – Charts for frequency, severity trends, sleep correlation, top triggers
- **Reports** – Download weekly or monthly CSV and PDF reports

## Data

All data is stored locally in `database.db` (SQLite). No data is sent to any external server.
