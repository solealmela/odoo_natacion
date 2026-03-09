# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
from odoo.http import request
import json

class Club(models.Model):
    _name = 'natacion.club'
    _description = 'Club de Natación'

    name = fields.Char(string='Nombre', required=True)
    town = fields.Char(string='Pueblo')
    swimmers = fields.One2many('res.partner', 'club', string='Nadadores')
    image_1920 = fields.Image(string='Logo')
    total_points = fields.Float(string="Puntos totales", compute="_compute_total_points", store=True)

    @api.depends('swimmers.best_times.time')
    def _compute_total_points(self):
        for club in self:
            points = 0
            for swimmer in club.swimmers:
                for bt in swimmer.best_times:
                    points += max(0, 100 - bt.time)
            club.total_points = points


class Category(models.Model):
    _name = 'natacion.category'
    _description = 'Categoria de Natación'

    name = fields.Char(string='Nombre', required=True)
    years_min = fields.Integer(string='Edad mínima')
    years_max = fields.Integer(string='Edad máxima')


class Swimmer(models.Model):
    _inherit = 'res.partner'

    year_of_birth = fields.Integer(string='Año de nacimiento')
    age = fields.Integer(string='Edad', compute='_compute_age', store=True)
    club = fields.Many2one('natacion.club', string='Club')
    category = fields.Many2one('natacion.category', string='Categoría')
    best_times = fields.One2many('natacion.besttime', 'swimmer', string='Mejores tiempos')
    is_swimmer = fields.Boolean(string="Es Nadador", default=False)
    last_payment_date = fields.Date(string='Fecha del último pago')
    payment_valid_until = fields.Date(string="Pago válido hasta")
    payment_progress = fields.Float(string='Progreso de pago', compute='_compute_payment_progress', store=True)
    payment_amount = fields.Float(string="Importe cuota", default=40)
    is_payment_valid = fields.Boolean(string="Cuota vigente",compute="_compute_is_payment_valid",store=True)

    @api.depends('year_of_birth')
    def _compute_age(self):
        current_year = fields.Date.today().year
        for rec in self:
            rec.age = current_year - rec.year_of_birth if rec.year_of_birth else 0

    @api.depends('last_payment_date', 'payment_valid_until')
    def _compute_payment_progress(self):
        for rec in self:
            if rec.last_payment_date and rec.payment_valid_until:
                total_days = (rec.payment_valid_until - rec.last_payment_date).days
                days_passed = (fields.Date.today() - rec.last_payment_date).days
                rec.payment_progress = min(100.0, max(0.0, (days_passed / total_days) * 100))
            else:
                rec.payment_progress = 0

    @api.depends('payment_valid_until')
    def _compute_is_payment_valid(self):
        for rec in self:
            rec.is_payment_valid = rec.payment_valid_until and rec.payment_valid_until >= fields.Date.today()

    def open_full_form(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.id,
            'view_mode': 'form',    
            'target': 'current',
        }

    def action_register_payment(self):
        self.ensure_one()

        today = date.today()
        self.last_payment_date = today
        self.payment_valid_until = today + timedelta(days=365) 

        product = self.env['product.product'].search([('name', '=', 'Cuota Federado')], limit=1)
        if not product:
            raise ValidationError("Crea un producto llamado 'Cuota Federado'.")

        sale = self.env['sale.order'].create({
            'partner_id': self.id,
            'origin': 'Pago cuota anual',
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
                'price_unit': product.lst_price,
            })]
        })

        sale.action_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': "Pedido generado",
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': sale.id,
            'target': 'current',
        }


class Style(models.Model):
    _name = 'natacion.style'
    _description = 'Estilo de Natación'

    name = fields.Char(string='Nombre', required=True)
    best_times = fields.One2many('natacion.besttime', 'style', string='Mejores tiempos por estilo')


class Championship(models.Model):
    _name = 'natacion.championship'
    _description = 'Campeonato de Natación'

    name = fields.Char(string='Nombre', required=True)
    clubs = fields.Many2many('natacion.club', string='Clubs participantes')
    swimmers = fields.Many2many('res.partner', string='Nadadores participantes', domain="[('club', 'in', clubs)]")
    sessions = fields.One2many('natacion.session', 'championship_id', string='Sesiones del campeonato')
    date_start = fields.Date(string='Fecha de inicio')
    date_end = fields.Date(string='Fecha de fin')
    total_duration = fields.Float(string='Duración total', compute='_compute_total_duration', store=True)
    classification = fields.Json(string="Clasificación", compute="_compute_classification")
    classification_html = fields.Html(
        string="Clasificación General", 
        compute="_generate_html_classification", 
        store=True
    )

    @api.depends('sessions', 'sessions.test_ids', 'sessions.test_ids.series')
    def _compute_total_duration(self):
        for champ in self:
            total = 0
            for session in champ.sessions:
                for test in session.test_ids:
                    total += len(test.series) * 10
            champ.total_duration = total

    def _generate_html_classification(self):
        for record in self:
            html = "<div class='table-responsive'><table class='table table-sm table-striped'>"
            html += "<thead><tr class='bg-primary text-white'><th>Pos</th><th>Nadador</th><th>Prueba</th><th>Club</th><th>Tiempo</th></tr></thead><tbody>"

            results = self.env['natacion.result'].search([
                ('series.test.session.championship_id', '=', record.id)
            ], order='time asc')

            if not results:
                html += "<tr><td colspan='5' class='text-center'>No hay resultados registrados todavía.</td></tr>"
            else:
                for pos, res in enumerate(results, 1):
                    html += f"""<tr>
                        <td><b>{pos}º</b></td>
                        <td>{res.swimmer.name}</td>
                        <td>{res.series.test.name}</td>
                        <td>{res.swimmer.club.name or '-'}</td>
                        <td>{res.time} s</td>
                    </tr>"""
            
            html += "</tbody></table></div>"
            record.classification_html = html

    @api.depends('sessions.test_ids.series.results.time')
    def _compute_classification(self):
        for champ in self:
            result = {}
            for session in champ.sessions:
                for test in session.test_ids: 
                    cat_name = test.category.name if test.category else 'General'
                    style_name = test.style.name if test.style else 'Estilo Libre'
                    
                    if cat_name not in result:
                        result[cat_name] = {}
                    if style_name not in result:
                        result[style_name] = []

                    test_results = []
                    for serie in test.series:
                        for r in serie.results:
                            test_results.append({
                                'swimmer': r.swimmer.name if r.swimmer else 'Anónimo',
                                'time': r.time,
                                'club': r.swimmer.club.name if r.swimmer.club else 'Independiente'
                            })

                    test_results.sort(key=lambda x: x['time'])

                    for pos, res in enumerate(test_results, 1):
                        res['position'] = pos
                    
                    result[style_name] = test_results

            champ.classification = result
            champ._generate_html_classification()

    def action_populate_championship(self):
        import random
        from datetime import datetime, timedelta

        self.ensure_one()

        if not self.date_start:
            raise ValidationError("El campeonato debe tener fecha de inicio antes de popularlo")

        Category = self.env['natacion.category']
        Style = self.env['natacion.style']
        Club = self.env['natacion.club']
        Partner = self.env['res.partner']
        Session = self.env['natacion.session']
        Test = self.env['natacion.test']

        categories = Category.search([])
        styles = Style.search([])
        all_clubs = Club.search([])

        clubs = random.sample(list(all_clubs), min(3, len(all_clubs)))
        self.clubs = [(6, 0, [c.id for c in clubs])]

        swimmers = Partner.search([
            ('is_swimmer', '=', True),
            ('club', 'in', [c.id for c in clubs])
        ])
        swimmers = random.sample(list(swimmers), min(30, len(swimmers)))
        self.swimmers = [(6, 0, [s.id for s in swimmers])]

        base_datetime = datetime.combine(self.date_start, datetime.min.time())

        sessions = []

        for i in range(5):
            session = Session.create({
                'name': f'Sesión {i+1}',
                'date': base_datetime + timedelta(hours=i * 2),
                'championship_id': self.id
            })
            sessions.append(session)

        for session in sessions:
            for cat in categories:
                for style in styles:
                    new_test = Test.create({
                        'name': f'{style.name} - {cat.name}',
                        'session': session.id,
                        'category': cat.id,
                        'style': style.id,
                        'swimmers': [(6, 0, self.swimmers.ids)] 
                    })

    def action_open_results_wizard(self):
        self.ensure_one()
        
        first_session = self.sessions[:1]
        
        if not first_session:
            raise ValidationError("Este campeonato no tiene sesiones creadas. ¡Crea una primero!")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestionar Resultados',
            'res_model': 'natacion.session.results.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_session': first_session.id, 
            }
        }
    
    def action_create_championship_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Campeonato',
            'res_model': 'natacion.championship.creation.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


class Session(models.Model):
    _name = 'natacion.session'
    _description = 'Sesión del Campeonato'

    name = fields.Char(string="Nombre", required=True)
    championship_id = fields.Many2one('natacion.championship', string="Campeonato")
    date = fields.Datetime(string="Fecha y Hora Inicio", required=True)
    duration = fields.Float(string="Duración (min)", compute="_compute_duration", store=True)
    test_ids = fields.One2many('natacion.test', 'session', string="Pruebas")

    @api.depends('test_ids.series')
    def _compute_duration(self):
        for record in self:
            total_series = sum(len(test.series) for test in record.test_ids)
            record.duration = total_series * 10

    @api.constrains('date')
    def _check_date(self):
        for record in self:
            if record.date.date() < record.championship_id.date_start:
                raise ValidationError("La sesión no puede ser anterior al inicio del campeonato.")

    @api.constrains('date', 'duration')
    def _check_overlap(self):
        for record in self:
            start = record.date
            end = start + timedelta(minutes=record.duration)
            
            overlap = self.search([
                ('championship_id', '=', record.championship_id.id),
                ('id', '!=', record.id),
                ('date', '<', end),
            ]).filtered(lambda s: (s.date + timedelta(minutes=s.duration)) > start)
            
            if overlap:
                raise ValidationError("Esta sesión se solapa con otra sesión existente.")


class Test(models.Model):
    _name = 'natacion.test'
    _description = 'Prueba de Natación'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    style = fields.Many2one('natacion.style', string='Estilo')
    category = fields.Many2one('natacion.category', string='Categoría')
    swimmers = fields.Many2many('res.partner', string='Nadadores inscritos')
    series = fields.One2many('natacion.series', 'test', string='Series de la prueba')
    session = fields.Many2one('natacion.session', string='Sesión')

    @api.constrains('category', 'style', 'session')
    def _check_category_style_session(self):
        for test in self:
            overlapping = self.search([
                ('session', '=', test.session.id),
                ('id', '!=', test.id),
                ('category', '=', test.category.id),
                ('style', '=', test.style.id),
            ])
            if overlapping:
                raise ValidationError("Esta categoría y estilo ya existen en esta sesión")



class Series(models.Model):
    _name = 'natacion.series'
    _description = 'Serie de Natación'

    name = fields.Char(string='Nombre', required=True)
    test = fields.Many2one('natacion.test', string='Prueba')
    results = fields.One2many('natacion.result', 'series', string='Resultados de la serie')
    results_json = fields.Text(string="Resultados JSON")
    
class BestTime(models.Model):
    _name = 'natacion.besttime'
    _description = 'Mejor tiempo de un nadador en una categoría'

    swimmer = fields.Many2one('res.partner', string='Nadador', required=True)
    category = fields.Many2one('natacion.category', string='Categoría')
    style = fields.Many2one('natacion.style', string='Estilo')
    time = fields.Float(string='Mejor tiempo', digits=(6,2))


class Result(models.Model):
    _name = 'natacion.result'
    _description = 'Resultado de una serie'

    swimmer = fields.Many2one('res.partner', string='Nadador')
    series = fields.Many2one('natacion.series', string='Serie')
    time = fields.Float(string='Tiempo registrado')
    position = fields.Integer(string='Posición', compute='_compute_position', store=True)

    @api.depends('series.results.time')
    def _compute_position(self):
        for result in self:
            if result.series:
                all_results = result.series.results.sorted(key=lambda r: r.time)
                for pos, r in enumerate(all_results, start=1):
                    r.position = pos

# Wizards

class SwimmerRegistrationWizard(models.TransientModel):
    _name = 'natacion.swimmer.registration.wizard'
    _description = 'Wizard para inscribir Nadadores'

    championship_id = fields.Many2one(
        'natacion.championship',
        string='Campeonato',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    swimmer_ids = fields.Many2many(
        'res.partner',
        string='Nadadores a inscribir',
        domain="[('is_swimmer','=',True)]"
    )

    @api.onchange('championship_id')
    def _onchange_championship_id(self):
        """Filtrar nadadores por los clubes del campeonato"""
        if self.championship_id:
            club_ids = self.championship_id.clubs.ids
            return {
                'domain': {
                    'swimmer_ids': [('is_swimmer', '=', True), ('club', 'in', club_ids)]
                }
            }

    def action_register_swimmers(self):
        """Inscribir nadadores con validaciones y persistencia total"""
        self.ensure_one()
        
        if not self.swimmer_ids:
            raise ValidationError("Debes seleccionar al menos un nadador.")

        for swimmer in self.swimmer_ids:
            if not swimmer.is_payment_valid:
                raise ValidationError(
                    f"El nadador {swimmer.name} no tiene la cuota vigente."
                )

        championship = self.championship_id
        current_swimmer_ids = championship.swimmers.ids
        new_swimmer_ids = self.swimmer_ids.ids
        final_ids = list(set(current_swimmer_ids + new_swimmer_ids))
        championship.write({
            'swimmers': [(6, 0, final_ids)]
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class SessionResultsWizard(models.TransientModel):
    _name = 'natacion.session.results.wizard'
    _description = 'Wizard para gestionar resultados'

    session = fields.Many2one('natacion.session', string='Sesión', required=True)
    test = fields.Many2one('natacion.test', string='Prueba', required=True)
    series = fields.Many2one('natacion.series', string='Serie', required=True)
    result_line = fields.One2many('natacion.session.results.wizard.line', 'wizard', string='Resultados')

    @api.onchange('session')
    def _onchange_session(self):
        self.test = False
        self.series = False
        return {'domain': {'test': [('session', '=', self.session.id)]}}

    @api.onchange('test')
    def _onchange_test(self):
        self.series = False
        return {'domain': {'series': [('test', '=', self.test.id)]}}

    @api.onchange('series')
    def _onchange_series(self):
        self.result_line = [(5, 0, 0)]
        
        if self.series:
            lines = []
            existing_results = self.env['natacion.result'].search([
                ('series', '=', self.series.id)
            ])
 
            times_map = {r.swimmer.id: r.time for r in existing_results}

            for swimmer in self.series.test.swimmers:
                saved_time = times_map.get(swimmer.id, 0.0)
                
                lines.append((0, 0, {
                    'swimmer': swimmer.id,
                    'time': saved_time
                }))

            self.result_line = lines

    def action_save_results(self):
        self.ensure_one()
        if not self.series:
            raise ValidationError("No hay una serie seleccionada.")

        self.env['natacion.result'].search([('series', '=', self.series.id)]).unlink()

        for line in self.result_line:
            if line.time > 0:
                self.env['natacion.result'].create({
                    'swimmer': line.swimmer.id,
                    'series': self.series.id,
                    'time': line.time
                })
        
        champ = self.session.championship_id
        if champ:
            champ._generate_html_classification()
            
        return {'type': 'ir.actions.act_window_close'}
    
class SessionResultsWizardLine(models.TransientModel):
    _name = 'natacion.session.results.wizard.line'
    _description = 'Línea de resultados'

    wizard = fields.Many2one('natacion.session.results.wizard', invisible=True)
    swimmer = fields.Many2one('res.partner', string='Nadador', readonly=True)
    time = fields.Float(string='Tiempo (segundos)')


class ChampionshipCreationWizard(models.TransientModel):
    _name = 'natacion.championship.creation.wizard'
    _description = 'Wizard de creación de campeonatos'

    name = fields.Char(string='Nombre del Campeonato', required=True)
    date_start = fields.Date(string='Fecha de inicio', required=True)
    date_end = fields.Date(string='Fecha de fin', required=True)
    clubs = fields.Many2many('natacion.club', string='Clubs participantes')
    
    step = fields.Selection([
        ('basic', 'Datos básicos'),
        ('sessions', 'Configurar Sesiones y Pruebas'),
        ('summary', 'Resumen Final')
    ], default='basic')

    session_ids = fields.One2many('natacion.championship.creation.wizard.session', 'wizard_id', string='Sesiones')
    summary_text = fields.Html(string="Resumen", compute="_compute_summary_text")

    @api.depends('session_ids', 'session_ids.test_line_ids')
    def _compute_summary_text(self):
        for rec in self:
            html = f"<h4>{rec.name or 'Nuevo Campeonato'}</h4>"
            html += f"<ul><li><b>Desde:</b> {rec.date_start} <b>Hasta:</b> {rec.date_end}</li></ul>"
            for sess in rec.session_ids:
                html += f"<p><b>Sesión: {sess.name}</b> ({sess.date})</p><ul>"
                for test in sess.test_line_ids:
                    html += f"<li>{test.name} - {test.series_count} series</li>"
                html += "</ul>"
            rec.summary_text = html

    def action_next(self):
        self.ensure_one()
        if self.step == 'basic':
            self.step = 'sessions'
        elif self.step == 'sessions':
            self.step = 'summary'
        return self._reopen_wizard()

    def action_previous(self):
        self.ensure_one()
        if self.step == 'summary':
            self.step = 'sessions'
        elif self.step == 'sessions':
            self.step = 'basic'
        return self._reopen_wizard()

    def _reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_all(self):
        self.ensure_one()
        champ = self.env['natacion.championship'].create({
            'name': self.name,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'clubs': [(6, 0, self.clubs.ids)]
        })
        for s_line in self.session_ids:
            session = self.env['natacion.session'].create({
                'name': s_line.name,
                'date': s_line.date,
                'championship_id': champ.id
            })
            for t_line in s_line.test_line_ids:
                test = self.env['natacion.test'].create({
                    'name': t_line.name,
                    'style': t_line.style_id.id,
                    'category': t_line.category_id.id,
                    'session': session.id
                })
                for i in range(t_line.series_count):
                    self.env['natacion.series'].create({
                        'name': f"Serie {i+1} - {test.name}",
                        'test': test.id
                    })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'natacion.championship',
            'res_id': champ.id,
            'view_mode': 'form',
            'target': 'current',
        }

class ChampionshipCreationWizardSession(models.TransientModel):
    _name = 'natacion.championship.creation.wizard.session'
    _description = 'Sesión temporal del Wizard'
    wizard_id = fields.Many2one('natacion.championship.creation.wizard')
    name = fields.Char(string='Nombre sesión', required=True)
    date = fields.Datetime(string='Fecha/Hora', required=True)
    test_line_ids = fields.One2many('natacion.championship.creation.wizard.test', 'session_wizard_id', string='Pruebas')

class ChampionshipCreationWizardTest(models.TransientModel):
    _name = 'natacion.championship.creation.wizard.test'
    _description = 'Prueba temporal del Wizard'
    session_wizard_id = fields.Many2one('natacion.championship.creation.wizard.session')
    name = fields.Char(string='Nombre prueba')
    category_id = fields.Many2one('natacion.category', string='Categoría')
    style_id = fields.Many2one('natacion.style', string='Estilo')
    series_count = fields.Integer(string='Nº Series', default=1)


class SessionTicketWizard(models.TransientModel):
    _name = 'natacion.session.ticket.wizard'
    _description = 'Wizard para generar entradas'

    session_id = fields.Many2one('natacion.session', string="Sesión", required=True)
    number_of_tickets = fields.Integer(string="¿Cuántas entradas?", default=50)

    def action_print_tickets(self):
        self.ensure_one()
        return self.env.ref('natacion.action_report_session_tickets').with_context(
            total_tickets=self.number_of_tickets + 1
        ).report_action(self.session_id)
    

# Controller

class NatacionAPI(http.Controller):

    @http.route('/natacion/api/championship/<int:res_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_championship_info(self, res_id, **kwargs):
        champ = request.env['natacion.championship'].sudo().browse(res_id)
        
        if not champ.exists():
            return request.make_response(
                json.dumps({'error': 'Campeonato no encontrado'}),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        data = {
            'id': champ.id,
            'name': champ.name,
            'date_start': str(champ.date_start),
            'date_end': str(champ.date_end),
            'sessions': []
        }

        for session in champ.sessions:
            session_data = {
                'name': session.name,
                'date': str(session.date),
                'tests': []
            }
            for test in session.test_ids:
                session_data['tests'].append({
                    'name': test.name,
                    'style': test.style.name if test.style else '',
                    'category': test.category.name if test.category else ''
                })
            data['sessions'].append(session_data)

        return request.make_response(
            json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )