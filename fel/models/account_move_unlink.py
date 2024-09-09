from odoo import models  # type: ignore
from odoo.exceptions import UserError  # type: ignore


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Bloqueo de la eliminación de facturas"

    def unlink(self):
        for factura in self:
            if factura.state == "cancel":
                raise UserError("No se pueden eliminar los registros.")
        return super(AccountMove, self).unlink()
