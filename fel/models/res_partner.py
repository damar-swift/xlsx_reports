from odoo import models, fields, api  # type: ignore
from odoo.exceptions import UserError  # type: ignore
import requests


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Búsqueda de NIT automatica"

    razon_social = fields.Char(string="Razón social", copy=False, readonly=True)
    extranjero = fields.Boolean(string="Extranjero", copy=False, default=False)

    @api.onchange("country_id")
    def _onchange_country_id(self):
        if self.country_id.name != "Guatemala ":
            self.extranjero = True
        else:
            self.extranjero = False

    @api.onchange("vat")
    def _onchange_vat(self):
        if self.extranjero:
            pass
        else:
            if self.vat:
                nombre = self._get_razon_social(self.vat)
                if nombre == "":
                    raise UserError("NIT inválido")
                else:
                    self.razon_social = nombre

    def _get_razon_social(self, vat):
        url = "https://consultareceptores.feel.com.gt/rest/action"
        data = {
            "emisor_codigo": "PROEL_DEMO",
            "emisor_clave": "163CE9295C7FB289FB650724B85F3D8C",
            "nit_consulta": vat,
        }
        respuesta = requests.post(url, json=data)
        respuesta_json = respuesta.json()
        return respuesta_json.get("nombre", "")

    def write(self, vals):
        if "vat" in vals:
            vals["razon_social"] = self._get_razon_social(vals["vat"])
        return super(ResPartner, self).write(vals)

    @api.model
    def create(self, vals):
        if "vat" in vals:
            vals["razon_social"] = self._get_razon_social(vals["vat"])
        return super(ResPartner, self).create(vals)
