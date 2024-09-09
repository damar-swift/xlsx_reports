from odoo import models, fields, api  # type: ignore


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Modulo con lógica de exportación"

    exportacion = fields.Boolean(string="¿Es factura de exportación?", default=False)
    nombre_consignatario = fields.Char(string="Nombre del consignatario", copy=False)
    direccion_consignatario = fields.Char(string="Dirección del consignatario", copy=False)
    codigo_consignatario = fields.Char(string="Código del consignatario", copy=False)
    nombre_comprador = fields.Char(string="Nombre del comprador", copy=False)
    direccion_comprador = fields.Char(string="Dirección del comprador", copy=False)
    codigo_comprador = fields.Char(string="Código del comprador", copy=False)
    referencia = fields.Char(string="Referencia", copy=False, default="EXPORTACION")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id.country_id.name != "Guatemala ":
            self.exportacion = True
        else:
            self.exportacion = False

        if self.partner_id.name:
            self.nombre_consignatario = self.partner_id.name
            calle = f"{self.partner_id.street}" if self.partner_id.street else ""
            calle_dos = f"{self.partner_id.street2}" if self.partner_id.street2 else ""
            ciudad = f"{self.partner_id.city}" if self.partner_id.city else ""
            estado = f"{self.partner_id.state_id.name}" if self.partner_id.state_id.name else ""
            pais = f"{self.partner_id.country_id.name}" if self.partner_id.country_id.name else ""
            direccion = f"{calle} {calle_dos} {ciudad} {estado} {pais}"
            self.direccion_consignatario = direccion.strip()