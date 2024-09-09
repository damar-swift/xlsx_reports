from odoo import models, api  # type: ignore
from odoo.exceptions import UserError  # type: ignore
import requests


class ResCompany(models.Model):
    _inherit = "res.company"
    _description = "Ampliación de la información de las empresas."

    @api.onchange("tipo_contribuyente")
    def _onchange_contribuyente(self):
        if self.tipo_contribuyente != "general":
            self.retenedor_iva = False
        if self.tipo_contribuyente != "general":
            self.regimen_isr = "none"

    @api.onchange("vat")
    def _onchange_vat(self):
        if self.vat:
            nombre = self._get_razon_social(self.vat)
            if nombre == "":
                raise UserError("NIT inválido")
            else:
                self.razon_social = nombre

    def _get_razon_social(self, vat):
        url = "https://consultareceptores.feel.com.gt/rest/action"
        data = {"emisor_codigo": f"{self.usuario}", "emisor_clave": f"{self.llave_api}", "nit_consulta": vat}
        respuesta = requests.post(url, json=data)
        respuesta_json = respuesta.json()
        return respuesta_json.get("nombre", "")

    def write(self, vals):
        if "vat" in vals:
            vals["razon_social"] = self._get_razon_social(vals["vat"])
        return super(ResCompany, self).write(vals)

    @api.model
    def create(self, vals):
        if "vat" in vals:
            vals["razon_social"] = self._get_razon_social(vals["vat"])
        return super(ResCompany, self).create(vals)
