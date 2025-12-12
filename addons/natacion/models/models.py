# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError


class Club(models.Model):
    _name = 'natacion.club'
    _description = 'Club'

    name = fields.Char(string="Nom", required=True)
    town = fields.Char(string="Poble")
    swimmers = fields.One2many('res.partner', 'club_id', string = 'Nadadors')
    image_1920 = fields.Image(string="Logo")
    best_times = fields.One2many('natacion.besttime', 'club_id', string="Millors temps")
    total_points = fields.Float(string="Punts", compute="_compute_total_points")

    def _compute_total_points(self):
        for club in self:
            points = 0
            for swimmer in club.swimmers:
                for bt in swimmer.best_times:
                    points += max(0, 100 - bt.time)
            club.total_points = points


class Category(models.Model):
    _name = 'natacion.category'
    _description = 'Categoría'

    name = fields.Char(required=True)
    years_min = fields.Integer(string="Edat mínima")
    years_max = fields.Integer(string="Edat màxima")


class Swimmer(models.Model):
    _inherit = 'res.partner'

    image_1920 = fields.Image("Foto")
    year_of_birth = fields.Integer()
    category = fields.Many2one('natacion.category')
    club_id = fields.Many2one('natacion.club')
    best_times = fields.One2many('natacion.besttime', 'swimmer_id', string="Best Times")
    is_swimmer = fields.Boolean(string="Es Nadador", default=False)
    age = fields.Integer(compute="_compute_age", store=True)
    last_payment_date = fields.Date(string="Último Pago")
    payment_progress = fields.Float(string="Progreso Pago", compute="_compute_payment_progress")
    payment_valid_until = fields.Date(string="Pago válido hasta")
    payment_amount = fields.Float(string="Importe cuota", default=40)
    is_payment_valid = fields.Boolean(string="Cuota vigente",compute="_compute_is_payment_valid",store=True)

    @api.depends('last_payment_date', 'payment_valid_until')
    def _compute_payment_progress(self):
        for rec in self:
            if rec.last_payment_date and rec.payment_valid_until:
                total_days = (rec.payment_valid_until - rec.last_payment_date).days
                days_passed = (fields.Date.today() - rec.last_payment_date).days
                rec.payment_progress = min(100.0, max(0.0, (days_passed / total_days) * 100))
            else:
                rec.payment_progress = 0



    def open_full_form(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.id,
            'view_mode': 'form',    
            'target': 'current',
        }

    @api.depends('year_of_birth')
    def _compute_age(self):
        current_year = fields.Date.today().year
        for rec in self:
            rec.age = current_year - rec.year_of_birth if rec.year_of_birth else 0

    def action_register_payment(self):
        """Registra el pago anual del nadador y crea una venta."""
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


    @api.depends('last_payment_date')
    def _compute_is_payment_valid(self):
        for rec in self:
            if rec.last_payment_date:
                rec.is_payment_valid = rec.last_payment_date + timedelta(days=365) >= fields.Date.today()
            else:
                rec.is_payment_valid = False


class Style(models.Model):
    _name = 'natacion.style'
    _description = 'Estilo'

    name = fields.Char(required=True)
    best_swimmers = fields.Many2many('res.partner')


class BestTime(models.Model):
    _name = 'natacion.besttime'

    swimmer_id = fields.Many2one('res.partner')
    club_id = fields.Many2one('natacion.club')
    style_id = fields.Many2one('natacion.style')
    time = fields.Float()


class Championship(models.Model):
    _name = 'natacion.championship'
    _description = 'Campionat'

    name = fields.Char(required=True)
    club_ids = fields.Many2many('natacion.club')
    swimmer_ids = fields.Many2many('res.partner')
    session_ids = fields.One2many('natacion.session', 'championship_id')
    start_date = fields.Date()
    end_date = fields.Date()
    total_duration = fields.Integer(string="Duració total (minuts)", compute="_compute_total_duration")
    classification = fields.Json(string="Classificació", compute="_compute_classification")

    def _compute_classification(self):
        for champ in self:
            result = {}
            for session in champ.session_ids:
                for test in session.test_ids:
                    cat_name = test.category.name
                    style_name = test.style_id.name
                    result.setdefault(cat_name, {})
                    result[cat_name].setdefault(style_name, [])
                    for serie in test.series:
                        for r in serie.result_ids:
                            result[cat_name][style_name].append({
                                'swimmer': r.swimmer_id.name,
                                'time': r.time,
                                'position': r.position,
                            })
            champ.classification = result

    @api.depends('session_ids', 'session_ids.test_ids', 'session_ids.test_ids.series')
    def _compute_total_duration(self):
        for champ in self:
            total = 0
            for session in champ.session_ids:
                for test in session.test_ids:
                    total += len(test.series) * 10
            champ.total_duration = total

    def action_add_swimmer(self, swimmer):
        """Añade un nadador al campeonato solo si la cuota está vigente."""
        self.ensure_one()
        if not swimmer.is_swimmer:
            raise ValidationError(f"{swimmer.name} no es un nadador.")
        today = fields.Date.today()
        if not swimmer.payment_valid_until or swimmer.payment_valid_until < today:
            raise ValidationError(f"{swimmer.name} no tiene la cuota vigente.")
        if swimmer not in self.swimmer_ids:
            self.swimmer_ids |= swimmer


    def action_add_all_valid_swimmers(self):
        self.ensure_one()
        today = fields.Date.today()
        count = 0
        for club in self.club_ids:
            for swimmer in club.swimmers:
                # Esto es solo para debug
                print(swimmer.name, swimmer.is_swimmer, swimmer.payment_valid_until)
                
                if swimmer.is_swimmer and swimmer.payment_valid_until and swimmer.payment_valid_until >= today:
                    if swimmer not in self.swimmer_ids:
                        self.swimmer_ids |= swimmer
                        count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Nadadores añadidos"),
                'message': _("Se han añadido %d nadadores de los clubes vinculados.") % count,
                'type': 'success',
                'sticky': False,
            }
        }



class Session(models.Model):
    _name = 'natacion.session'
    _description = 'Sessió'

    date = fields.Datetime()
    championship_id = fields.Many2one('natacion.championship')
    test_ids = fields.One2many('natacion.test', 'session_id')
    registered_swimmers = fields.Many2many('res.partner')

    @api.constrains('date', 'championship_id')
    def _check_session_date(self):
        for session in self:
            if session.date and session.championship_id.start_date:
                if session.date.date() < session.championship_id.start_date:
                    raise ValidationError("La sessió ha de ser posterior a l'inici del campionat")

    @api.constrains('date', 'championship_id')
    def _check_session_overlap(self):
        for session in self:
            overlapping = self.search([
                ('championship_id', '=', session.championship_id.id),
                ('id', '!=', session.id),
                ('date', '=', session.date)
            ])
            if overlapping:
                raise ValidationError("Hi ha una sessió que ja té aquesta data i hora")


class Test(models.Model):
    _name = 'natacion.test'
    _description = 'Prova'

    description = fields.Char()
    style_id = fields.Many2one('natacion.style')
    category = fields.Many2one('natacion.category')
    session_id = fields.Many2one('natacion.session')
    registered_swimmers = fields.Many2many('res.partner')
    series = fields.One2many('natacion.serie', 'test_id')
    result_ids = fields.One2many('natacion.result', 'test_id')
    series_size = fields.Integer(string="Tamaño máximo por serie", default=8)


    @api.constrains('registered_swimmers')
    def _check_payment_for_registration(self):
        for test in self:
            for swimmer in test.registered_swimmers:
                if swimmer.is_swimmer and not swimmer.is_payment_valid:
                    raise ValidationError(
                        f"{swimmer.name} no puede inscribirse porque su cuota ha caducado."
                    )
                
    def action_register_swimmer(self, swimmer):
        if swimmer.is_swimmer and swimmer.is_payment_valid:
            self.registered_swimmers = [(4, swimmer.id)]
        else:
            raise ValidationError(f"{swimmer.name} no puede inscribirse, pago no vigente.")
        
    def generate_series(self):
        """Genera las series automáticamente según los nadadores inscritos y tamaño de serie"""
        self.ensure_one()
        if not self.registered_swimmers:
            raise ValidationError("No hay nadadores inscritos en esta prueba.")

        self.series.unlink()

        swimmers = list(self.registered_swimmers)
        max_per_serie = self.series_size or 8
        series_list = []

        for i in range(0, len(swimmers), max_per_serie):
            serie_swimmers = swimmers[i:i + max_per_serie]
            serie = self.env['natacion.serie'].create({
                'test_id': self.id,
                'name': f"Sèrie {len(series_list)+1}"
            })

            for s in serie_swimmers:
                self.env['natacion.result'].create({
                    'test_id': self.id,
                    'serie_id': serie.id,
                    'swimmer_id': s.id,
                    'time': 0.0, 
                    'position': 0
                })
            series_list.append(serie)

    def action_generate_series_with_swimmers(self):
        """Añade los nadadores válidos del campeonato y genera las series automáticamente."""
        self.ensure_one()

        # Añade nadadores válidos
        if self.session_id and self.session_id.championship_id:
            championship = self.session_id.championship_id
        else:
            championship = self.env['natacion.championship'].search([], limit=1)

        for swimmer in championship.swimmer_ids:
            if swimmer.is_payment_valid:
                self.registered_swimmers = [(4, swimmer.id)]

        # Genera las series
        self.generate_series()



class Serie(models.Model):
    _name = 'natacion.serie'
    _description = 'Sèrie'

    test_id = fields.Many2one('natacion.test')
    name = fields.Char()
    result_ids = fields.One2many('natacion.result', 'serie_id')


class Result(models.Model):
    _name = 'natacion.result'
    _description = 'Resultat'

    swimmer_id = fields.Many2one('res.partner')
    serie_id = fields.Many2one('natacion.serie')
    test_id = fields.Many2one('natacion.test')
    time = fields.Float()
    position = fields.Integer()
