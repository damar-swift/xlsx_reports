from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError # type: ignore

class AccountMove(models.Model):
    _inherit = "account.move"

    proveedor_exterior = fields.Boolean(default=False, copy=False, store=True, compute="_compute_proveedor_exterior")
    factura_especial = fields.Boolean(default=False)

    @api.depends("partner_id.country_id")
    def _compute_proveedor_exterior(self):
        for factura in self:
            if factura.partner_id.country_id.code != "GT":
                factura.proveedor_exterior = True
            else:
                factura.proveedor_exterior = False

    def _post(self, soft):
        res = super(AccountMove, self)._post(soft)

        operar_facturas = self.filtered(lambda inv: inv.move_type == "in_invoice" and not inv.proveedor_exterior and not inv.factura_especial)
        
        for factura in operar_facturas:
            diario_iva = self.env["account.journal"].search([("name", "=", "RETENCION DE IVA")], limit=1)
            diario_isr = self.env["account.journal"].search([("name", "=", "RETENCIONES ISR")], limit=1)

            if not diario_iva:
                raise UserError("No se encontró el diario")

            if not diario_isr:
                raise UserError("No se encontró el diario")

            pago_iva = self.env["account.payment.method.line"].search(
                [("journal_id", "=", diario_iva.id), ("payment_method_id", "=", 2)], limit=1
            )
            if not pago_iva:
                raise UserError("No se encontró el método de pago")

            pago_isr = self.env["account.payment.method.line"].search(
                [("journal_id", "=", diario_isr.id), ("payment_method_id", "=", 2)], limit=1
            )
            if not pago_isr:
                raise UserError("No se encontró el método de pago")

            impuestos_encontrados = dict()
            impuestos_existentes = {
                "IVA 12%": {"nombre_corto": "IVA", "codigo_gravable": 1},
                "IVA 0%": {"nombre_corto": "IVA", "codigo_gravable": 2},
                "TURISMO HOSPEDAJE": {"nombre_corto": "TURISMO HOSPEDAJE", "codigo_gravable": 1}
            }

            for impuesto_existente in self.env["account.tax"].search(
                [("name", "in", list(impuestos_existentes.keys()))]
            ):
                if impuesto_existente.amount_type == "percent":
                    impuestos_existentes[impuesto_existente.name]["importe"] = impuesto_existente.amount / 100

            for line in factura.invoice_line_ids:
                for impuesto in line.tax_ids:
                    nombre = impuestos_existentes[impuesto.name]["nombre_corto"]
                    importe = impuestos_existentes[impuesto.name]["importe"]
                    if impuesto_existente.amount_type == "percent":
                        monto = round((line.price_subtotal * float(importe)), 2)
                    impuestos_encontrados[nombre] = impuestos_encontrados.get(nombre, 0) + monto

            ret_iva = 0
            ret_isr = 0

            lista_ret_iva = ["ISR Utilidades", "ISR Ventas", "ISR Ventas (Directo)"]

            if factura.company_id.retenedor_iva:
                if factura.fiscal_position_id.name in lista_ret_iva and "IVA" in impuestos_encontrados.keys():
                    if impuestos_encontrados["IVA"] > 0 and factura.amount_total >= 2500:
                        ret_iva = round(factura.company_id.porcentaje_retencion * impuestos_encontrados["IVA"], 2)
                elif factura.fiscal_position_id.name == "Pequeño contribuyente":
                    if factura.amount_total >= 2500:
                        ret_iva = round(factura.amount_total * 0.05)

            if ret_iva > 0:
                registrar_pago_iva = (
                    self.env["account.payment.register"]
                    .with_context({"active_model": "account.move", "active_ids": [factura.id]})
                    .create(
                        {
                            "payment_type": "outbound",
                            "partner_type": "supplier",
                            "partner_id": factura.partner_id.id,
                            "journal_id": diario_iva.id,
                            "amount": ret_iva,
                            "payment_method_line_id": pago_iva.id,
                            "communication": factura.name,
                        }
                    )
                )

                registrar_pago_iva.action_create_payments()

            lista_ret_isr = ["ISR Ventas", "ISR Ventas - Retenedor IVA"]

            if factura.fiscal_position_id.name in lista_ret_isr and factura.amount_untaxed > 2500:
                if factura.amount_untaxed > 30000:
                    ret_isr = 30000 * 0.05 + (factura.amount_untaxed - 30000) * 0.07
                else:
                    ret_isr = factura.amount_untaxed * 0.05

            if ret_isr > 0:
                registrar_pago_isr = (
                    self.env["account.payment.register"]
                    .with_context({"active_model": "account.move", "active_ids": [factura.id]})
                    .create(
                        {
                            "payment_type": "outbound",
                            "partner_type": "supplier",
                            "partner_id": factura.partner_id.id,
                            "journal_id": diario_isr.id,
                            "amount": ret_isr,
                            "payment_method_line_id": pago_isr.id,
                            "communication": factura.name,
                        }
                    )
                )

                registrar_pago_isr.action_create_payments()

        return res