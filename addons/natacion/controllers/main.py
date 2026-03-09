# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class NatacionController(http.Controller):

    # URL: http://localhost:8069/natacion/api/championship/1
    @http.route('/natacion/api/championship/<int:champ_id>', type='http', auth='public', methods=['GET'], cors='*', csrf=False)
    def get_championship(self, champ_id, **kwargs):
        champ = request.env['natacion.championship'].sudo().browse(champ_id)
        
        if not champ.exists():
            return request.make_response(json.dumps({'status': 'not found'}), status=404)

        data = {
            'nombre': champ.name,
            'inicio': str(champ.date_start),
            'sesiones': [{
                'nombre': s.name, 
                'pruebas': [t.name for t in s.test_ids]
            } for s in champ.sessions]
        }
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        return request.make_response(json.dumps(data), headers=headers)

    @http.route('/natacion/pagar_quota', type='json', auth='public', methods=['POST'], cors='*', csrf=False)
    def pagar_quota(self, **kwargs):
        user_id = kwargs.get('id')
        
        print(f"--- PROCESANDO PAGO EN ODOO PARA EL USUARIO: {user_id} ---")

        return {
            'status': 'success',
            'message': f'Pago registrado correctamente para el ID {user_id}',
            'invoice_url': 'http://localhost:8069/report/html/account.report_invoice/1'
        }