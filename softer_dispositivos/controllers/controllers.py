# -*- coding: utf-8 -*-
# from odoo import http


# class Pacientes(http.Controller):
#     @http.route('/pacientes/pacientes', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pacientes/pacientes/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pacientes.listing', {
#             'root': '/pacientes/pacientes',
#             'objects': http.request.env['pacientes.pacientes'].search([]),
#         })

#     @http.route('/pacientes/pacientes/objects/<model("pacientes.pacientes"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pacientes.object', {
#             'object': obj
#         })

