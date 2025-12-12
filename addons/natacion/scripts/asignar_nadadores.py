# /mnt/extra-addons/natacion/scripts/asignar_nadadores.py

import random

# 'env' ya existe en odoo shell, no hace falta cr ni SUPERUSER_ID

# Tomamos los 20 clubes
clubes = env['natacion.club'].search([], limit=20)

# Tomamos todos los nadadores que no tienen club
nadadores = env['res.partner'].search([('club_id', '=', False)])

# Asignamos aleatoriamente cada nadador a uno de los 20 clubes
for nadador in nadadores:
    club = random.choice(clubes)
    nadador.club_id = club.id

print(f"Asignados {len(nadadores)} nadadores a los 20 clubes.")
