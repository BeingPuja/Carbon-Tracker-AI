def calc_transport(distance_km, mode="car"):
    factors = {"car": 0.12, "bus": 0.05, "bike": 0.0, "flight": 0.25, "train": 0.03}
    try: distance_km = float(distance_km)
    except: distance_km = 0
    return round(distance_km * factors.get(mode, 0.12), 2)


def calc_energy(kwh):
    try: kwh = float(kwh)
    except: kwh = 0
    return round(kwh * 0.42, 2)


def calc_diet(meals, diet="meat"):
    factors = {"meat": 5.0, "vegetarian": 2.0, "vegan": 1.5, "mixed": 3.5}
    try: meals = float(meals)
    except: meals = 0
    return round(meals * factors.get(diet, 3.5), 2)


def total_emission(data):
    transport_em = calc_transport(data.get("distance",0), data.get("mode","car"))
    energy_em = calc_energy(data.get("kwh",0))
    diet_em = calc_diet(data.get("meals",0), data.get("diet","mixed"))
    total = round(transport_em + energy_em + diet_em, 2)
    return {"transport_em": transport_em, "energy_em": energy_em, "diet_em": diet_em, "total": total}
