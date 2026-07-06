# Flight Tracker radius of airport

A program that tracks active flights within a specified radius of any airport using the FlightRadar24 API and alerts you via sound as well as in terminal when a new flight enters your tracking zone.

---

## Features

- Enter any airport's ICAO code (e.g., `VERC` for Ranchi) to automatically retrieve its coordinates.
- Track flights within any distance threshold (in meters).
- Beeps or sounds a terminal bell automatically whenever a completely new flight enters your specified radius.

---

## Prerequisites

ensure you have **Python 3.x** installed.

### Install Dependencies

Clone this repository to your local machine,inside the project folder run:

```bash
pip install -r requirements.txt
