import json
import os
import base64

# ---------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------
BASE_PATH = "/mnt/extra-addons/natacion/clubes"
JSON_FILE = os.path.join(BASE_PATH, "clubes/clubes.json")
IMAGES_PATH = BASE_PATH  # Las imágenes están directamente en esta carpeta

# ---------------------------------------------------
# CARGAR JSON
# ---------------------------------------------------
with open(JSON_FILE, "r", encoding="utf-8") as f:
    clubes_data = json.load(f)

# Limitar a 20 clubes
clubes_data = clubes_data[:21]

# ---------------------------------------------------
# CREAR CLUBS EN ODOO
# ---------------------------------------------------
for idx, c in enumerate(clubes_data, start=1):
    name = c.get("club")
    location = c.get("location")
    image_url = c.get("image")  # solo para info, se usará imagen local si existe

    if not name:
        continue  # saltar entradas sin nombre de club

    # Buscar si ya existe el club
    club_existente = env['natacion.club'].search([('name','=',name)], limit=1)
    if club_existente:
        print(f"Club ya existe: {name}")
        continue

    # Intentar cargar imagen local
    possible_extensions = ['.png', '.jpg', '.jpeg']
    image_data = None
    for ext in possible_extensions:
        image_file = os.path.join(IMAGES_PATH, f"club_{idx}{ext}")
        if os.path.exists(image_file):
            with open(image_file, "rb") as img_f:
                image_data = base64.b64encode(img_f.read())
            break

    # Crear el registro en Odoo
    env['natacion.club'].create({
        'name': name,
        'town': location or '',
        'image': image_data,
    })

    print(f"Creado club: {name} ({location})")

print("¡Los 20 primeros clubes han sido procesados!")
