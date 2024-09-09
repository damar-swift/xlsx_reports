from odoo import models, fields # type: ignore
from odoo.exceptions import UserError # type: ignore

class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    poliza = fields.Char(string="Póliza", copy=False)

