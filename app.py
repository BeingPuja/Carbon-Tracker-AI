from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carbon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- Database Model ---
class CarbonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    car_km = db.Column(db.Float, default=0)
    bus_km = db.Column(db.Float, default=0)
    flight_hours = db.Column(db.Float, default=0)
    electricity = db.Column(db.Float, default=0)
    food = db.Column(db.Float, default=0)
    shopping = db.Column(db.Float, default=0)
    total = db.Column(db.Float)


# --- Emission factors ---
CAR = 0.12
BUS = 0.05
FLIGHT = 90
ELECTRICITY = 0.82
FOOD = 2.5
SHOPPING = 5.0


@app.route("/", methods=["GET", "POST"])
def index():
    carbon_total = None
    if request.method == "POST":
        try:
            car_km = float(request.form.get("car_km", 0))
            bus_km = float(request.form.get("bus_km", 0))
            flight_hours = float(request.form.get("flight_hours", 0))
            electricity = float(request.form.get("electricity", 0))
            food = float(request.form.get("food", 0))
            shopping = float(request.form.get("shopping", 0))


            carbon_total = (car_km * CAR) + (bus_km * BUS) + \
                           (flight_hours * FLIGHT) + (electricity * ELECTRICITY) + \
                           (food * FOOD) + (shopping * SHOPPING)


            # Save to DB
            entry = CarbonLog(
                car_km=car_km, bus_km=bus_km, flight_hours=flight_hours,
                electricity=electricity, food=food, shopping=shopping,
                total=carbon_total
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            print("Error saving data:", e)


    # Fetch logs
    logs = CarbonLog.query.order_by(CarbonLog.date.desc()).all()
    return render_template("index.html", carbon_total=carbon_total, logs=logs)

if __name__ == "__main__":
    # --- Create database tables inside app context ---
    with app.app_context():
        db.create_all()

    # --- Run the Flask server ---
    app.run(debug=True)


