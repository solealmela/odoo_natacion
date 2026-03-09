# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class NatacionController(http.Controller):

    #http://localhost:8069/natacion/api/championship/1
    @http.route('/natacion/championship/<int:champ_id>', type='http', auth='public', methods=['GET'], csrf=False)
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
        
        return request.make_response(
            json.dumps(data),   
            headers={'Content-Type': 'application/json'}
        )
    

    #@http.route('/natacion/pagar_quota', type='http', auth='public', cors='*', csrf=False) 
    #def apiGet(self, **args):
    #    print(args, http.request.httprequest.method)
    #    if http.request.httprequest.method == 'POST':


