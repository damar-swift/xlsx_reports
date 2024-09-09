from odoo import models, fields  # type: ignore


class AccountMove(models.Model):
    _inherit = "account.move"

    autorizacion_proveedor = fields.Char(string="Número de autorización")
    serie_proveedor = fields.Char(string="Número de serie")
    dte_proveedor = fields.Char(string="Número de DTE")
    acceso_proveedor = fields.Char(string="Número de acceso")
    emision_proveedor = fields.Date(string="Fehca de emisión")
