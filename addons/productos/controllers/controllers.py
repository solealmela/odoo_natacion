# -*- coding: utf-8 -*-
from odoo import http


class Productos(http.Controller):
    @http.route('/productos/productos', auth='public', methods=['GET'])
    def index(self, **kw):
        for record in self:
            products = [http.request.env['product.template'].sudo().search([("name","=",record.name)])]

        data = [{
            'name': p.name,
            'image_1920': p.image_1920,
            'list_price': p.list_price,
            'text_publicitari': p.text_publicitari
        } for p in products]

        return http.request.make_json_response(
               products.read(("name")), 
               headers=None, 
               cookies=None, 
               status=200)