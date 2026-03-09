# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Productos(models.Model):
    _inherit = "product.template"

    es_destacat = fields.Boolean(string="Es destacat", default=False)
    text_publicitari = fields.Html(string="Text publicitari")

class ProductWizard(models.TransientModel):
    _name = "productos.product_wizard"

    nuevo_texto = fields.Html(string="Texto publicitario")
    productos_ids = fields.Many2many("product.template", string="Productos", required=True)

    step = fields.Selection([
        ('anyadir_productos', 'Añadir productos'),
        ('texto_publicitario', 'Texto publicitario')
    ], default='anyadir_productos')

    def action_next(self):
        self.ensure_one()
        if self.step == 'anyadir_productos':
            self.step = 'texto_publicitario'
        return self._reopen_wizard()

    def action_previous(self):
        self.ensure_one()
        if self.step == 'texto_publicitario':
            self.step = 'anyadir_productos'
        return self._reopen_wizard()

    def _reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_actualizar_productos(self):
        for record in self:
            for producto in record.productos_ids:
                producto.es_destacat = True
                producto.text_publicitari = record.nuevo_texto

        return {'type': 'ir.actions.act_window_close'}



