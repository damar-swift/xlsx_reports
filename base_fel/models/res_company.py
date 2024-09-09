from odoo import fields, models # type: ignore
from odoo.exceptions import UserError # type: ignore

class ResCompany(models.Model):
    _inherit = "res.company"

    razon_social = fields.Char(string="Razón social", copy=False, readonly=True)
    proveedor = fields.Selection(
        string="Proveedor", selection=[("none", "Seleccione un proveedor"), ("infile", "INFILE")], default="none"
    )
    usuario = fields.Char(string="Usuario")
    llave_firma = fields.Char(string="Llave firma")
    llave_api = fields.Char(string="Llave API")
    tipo_contribuyente = fields.Selection(
        string="Tipo de contribuyente",
        selection=[
            ("none", "Seleccione un tipo de contribuyente"),
            ("general", "General"),
            ("small", "Pequeño contribuyente"),
        ],
        default="none",
    )
    retenedor_iva = fields.Boolean(string="Agente retenedor de IVA", default=False)
    porcentaje_retencion = fields.Float(string="Porcentaje de retención IVA", default=0.0)
    regimen_isr = fields.Selection(
        string="Régimen de ISR",
        selection=[
            ("none", "Seleccione un régimen de ISR"),
            ("utilities", "Utilidades de actividades lucrativas"),
            ("simplified", "Opcional simplificado sobre ingresos de actividades lucrativas"),
        ],
        default="none",
    )
    num_establecimiento = fields.Char(string="Número de establecimiento")