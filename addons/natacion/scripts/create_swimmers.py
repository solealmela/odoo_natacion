import csv
import random
import base64
import os
from datetime import date

# ---------------- CONFIGURACIÓN DE RUTAS ----------------
BASE_PATH = "/mnt/extra-addons/natacion"

IMAGES_PATH = f"{BASE_PATH}/images/faces/"
MUJERES_CSV = f"{BASE_PATH}/csv/mujeres.csv"
HOMBRES_CSV = f"{BASE_PATH}/csv/hombres.csv"
APELLIDOS_CSV = f"{BASE_PATH}/csv/apellidos.csv"

TOTAL_SWIMMERS = 1000

# ---------------- ACCESO A MODELOS ----------------
Partner = env['res.partner']
Category = env['natacion.category']

# ---------------- CREAR CATEGORÍAS ----------------
def create_categories():
    categories = [
        ("Benjamín", 6, 10),
        ("Alevín", 11, 12),
        ("Infantil", 13, 14),
        ("Junior", 15, 18),
        ("Senior", 19, 99)
    ]

    created = []

    for name, years_min, years_max in categories:
        cat = Category.search([("name", "=", name)], limit=1)
        if not cat:
            cat = Category.create({
                "name": name,
                "years_min": years_min,
                "years_max": years_max,
            })
        created.append(cat)
    
    print("✔ Categorías creadas")
    return created

# ---------------- CARGAR NOMBRES Y APELLIDOS ----------------
def load_weighted_names(path, name_field, weight_field):
    names = []
    weights = []
    with open(path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            names.append(row[name_field].title())
            weights.append(int(float(row[weight_field])))
    return names, weights

female_names, female_weights = load_weighted_names(MUJERES_CSV, 'nombre', 'frec')
male_names, male_weights = load_weighted_names(HOMBRES_CSV, 'nombre', 'frec')

lastnames, lastname_weights = load_weighted_names(APELLIDOS_CSV, 'apellido', 'frec_pri')

# ---------------- FUNCIONES PARA FOTOS ----------------
all_images = [f for f in os.listdir(IMAGES_PATH) if f.lower().endswith((".jpg", ".png", ".jpeg"))]

def get_random_image():
    image_file = random.choice(all_images)
    with open(os.path.join(IMAGES_PATH, image_file), "rb") as img:
        return base64.b64encode(img.read())

# ---------------- FUNCIONES PARA GENERAR NOMBRES ----------------
def random_full_name():
    if random.random() < 0.5:
        name = random.choices(female_names, weights=female_weights, k=1)[0]
        age = random.randint(9, 18)
    else:
        name = random.choices(male_names, weights=male_weights, k=1)[0]
        age = random.randint(9, 18)

    last1 = random.choices(lastnames, weights=lastname_weights, k=1)[0]
    last2 = random.choices(lastnames, weights=lastname_weights, k=1)[0]

    full_name = f"{name} {last1} {last2}"
    return full_name, age

# ---------------- ASIGNAR CATEGORÍA ----------------
def assign_category(age, categories):
    for cat in categories:
        if cat.years_min  <= age <= cat.years_max:
            return cat.id
    return False

# ---------------- CREAR NADADORES ----------------
def create_swimmers(n=TOTAL_SWIMMERS):
    categories = create_categories()
    current_year = date.today().year

    for i in range(n):
        full_name, age = random_full_name()
        yob = current_year - age

        Partner.create({
            "name": full_name,
            "is_swimmer": True,
            "year_of_birth": yob,
            "category": assign_category(age, categories),
            "image_1920": get_random_image(),
        })

        if i % 50 == 0:
            print(f"Creando nadador {i}/{n}...")

    print("✔ ¡Nadadores creados con fotos y categorías!")

# ---------------- EJECUTAR ----------------
create_swimmers(TOTAL_SWIMMERS)
