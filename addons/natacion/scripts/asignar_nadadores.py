import random

# Tomamos los 20 clubes
clubes = env['natacion.club'].search([], limit=20)

# Tomamos todos los nadadores que no tienen club
nadadores = env['res.partner'].search([('club', '=', False), ('is_swimmer', '=', True)])

# Asignamos aleatoriamente cada nadador a uno de los 20 clubes
for nadador in nadadores:
    club = random.choice(clubes)
    nadador.club = club

print(f"Asignados {len(nadadores)} nadadores a los 20 clubes.")
