from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError, ValidationError # type: ignore
import xml.etree.ElementTree as ET
import requests
import pytz
from datetime import datetime, date, timedelta
from ..modulos import factura as FACT
from ..modulos import especial as FESP
from ..modulos import nota_credito as NCRE
from ..modulos import nota_debito as NDEB
from ..modulos import anulacion as ANL
from ..modulos import get_credenciales as GC

class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Modulo de facturación electrónica por Swift Solutions."

    facturacion_electronica_activa = fields.Boolean(compute="_compute_facturacion_activa", store=False)
    numero_autorizacion = fields.Char(string="Número de autorización", readonly=True, copy=False)
    serie = fields.Char(string="Número de serie", readonly=True, copy=False)
    numero_dte = fields.Char(string="Número de DTE", readonly=True, copy=False)
    numero_acceso = fields.Char(string="Número de acceso", readonly=True, copy=False)
    fecha_emision = fields.Datetime(string="Fecha y hora de emisión", readonly=True, copy=False)
    fecha_certificacion = fields.Datetime(string="Fecha y hora de certificación", readonly=True, copy=False)
    certificada = fields.Boolean(default=False, copy=False)
    certificacion_error = fields.Boolean(default=False, copy=False)
    xml_generado = fields.Char(string="XML Generado", readonly=True, copy=False)
    xml_certificado = fields.Char(string="XML Certificado", readonly=True, copy=False)
    json_temporal = fields.Char(string="XML con errores", copy=False)
    numero_anulacion = fields.Char(string="Número de anulación", readonly=True, copy=False)
    anulacion_serie = fields.Char(string="Número de serie de anulación", readonly=True, copy=False)
    numero_dte_anulado = fields.Char(string="Número de DTE de anulación", readonly=True, copy=False)
    numero_acceso_anulacion = fields.Char(string="Número de acceso de anulación", readonly=True, copy=False)
    fecha_anulacion = fields.Datetime(string="Fecha de anulación", readonly=True, copy=False)
    xml_cancelado_generado = fields.Char(string="XML cancelado generado", readonly=True, copy=False)
    xml_cancelado_certificado = fields.Char(string="XML cancelado certificado", readonly=True, copy=False)
    motivo_anulacion = fields.Char(
        string="Motivo de anulación", help="Si desea anular una factura, deberá indicar el motivo.", copy=False
    )
    tipo_documento = fields.Selection(
        string="Tipo de documento a emitir",
        selection=[
            ("fact", "Factura"),
            ("fact_cambiaria", "Factura cambiaria"),
        ],
        default=False,
        copy=False,
    )
    tipo_factura = fields.Selection(
        selection=[
            ("recibo", "Recibo"),
            ("fact_cambiaria", "Factura cambiaria"),
            ("fact_peque", "Factura pequeño contribuyente"),
            ("fact_peque_cam", "Factura cambiaria pequeño contribuyente"),
            ("recibo_donacion", "Recibo donación"),
            ("fact", "Factura"),
            ("nota_abono", "Nota de abono"),
            ("nota_credito", "Nota de crédito"),
            ("nota_debito", "Nota de débito"),
            ("poliza", "Póliza"),
            ("fyduca", "Fyduca"),
            ("fauca", "FAUCA"),
            ("fact_elect", "Factura electrónica"),
            ("declaracion_aduanera", "Declaración aduanera"),
            ("form_sat", "Formulario SAT"),
            ("escritura_publica", "Escritura pública"),
            ("fact_elect_peque", "Factura electrónica pequeño contribuyente"),
            ("fact_reg_elec_peque", "Factura régimen electrónico pequeño contribuyente"),
            ("fact_reg_esp_agrope", "Factura régimen especial contribuyente agropecuario"),
            ("fact_reg_elect_esp_agrope", "Factura régimen electrónico especial contribuyente agropecuario")
        ],
        default=False,
        copy=False
    )
    tipo_pago = fields.Selection(
        string="Método de pago",
        selection=[
            ("efectivo", "Efectivo"),
            ("cheque", "Cheque"),
            ("transferencia", "Transferencia"),
            ("tarjeta_credito", "Tarjeta de crédito"),
            ("deposito", "Depósito")
        ],
        copy=False
    )
    errores_fel_id = fields.One2many("errores.fel", "account_move_factuas_ids")

    @api.depends("journal_id")
    def _compute_facturacion_activa(self):
        for registro in self:
            registro.facturacion_electronica_activa = registro.journal_id.facturacion_activa

    def certificar_documento(self, url, headers, tree):
        certificar_xml = ET.tostring(tree.getroot(), encoding="UTF-8", method="xml")
        respuesta = requests.post(url, headers=headers, data=certificar_xml)
        respuesta_json = respuesta.json()

        return certificar_xml, respuesta_json

    def establecer_error(self, json):
        for error in json["descripcion_errores"]:
            self.env["errores.fel"].create(
                {
                    "mensaje_error": error.get("mensaje_error"),
                    "fecha_hora_error": datetime.now(),
                    "account_move_factuas_ids": self.id,
                }
            )

    def facturacion_electronica(self, factura):
        url = GC.credenciales_url()
        headers = GC.credenciales_header(self)

        if not factura.invoice_date:
            factura.invoice_date = datetime.now(pytz.timezone("America/Guatemala")).date()
            if factura.invoice_date != factura.invoice_date_due:
                factura.tipo_factura = "fact_cambiaria"
            elif factura.invoice_date == factura.invoice_date_due:
                factura.tipo_factura = "fact"


        if factura.debit_origin_id:
            tree = NDEB.generar_nota_debito(self, factura)

        elif factura.move_type == "out_refund":
            tree = NCRE.generar_nota_credito(self, factura)

        elif factura.tipo_factura == "fact" or factura.tipo_factura == "fact_cambiaria":
            tree = FACT.generar_factura(self, factura)

        elif factura.factura_especial:
            tree = FESP.generar_especial(self, factura)

        else:
            return

        certificar_xml, respuesta_json = self.certificar_documento(url, headers, tree)
        if respuesta_json["resultado"] == False:
            factura.certificacion_error = True
            factura.json_temporal = certificar_xml
            factura.establecer_error(respuesta_json)
            return
        else:
            factura.numero_autorizacion = respuesta_json["uuid"]
            factura.serie = respuesta_json["serie"]
            factura.numero_dte = respuesta_json["numero"]
            factura.xml_generado = certificar_xml
            factura.fecha_emision = datetime.now()
            fecha_hora_certificado = respuesta_json["fecha"].split("T")
            hora_certificado = fecha_hora_certificado[1].split("-")
            fecha_hora_str = f"{fecha_hora_certificado[0]} {hora_certificado[0]}"
            fecha_hora_time = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M:%S")
            fecha_hora_modificada = fecha_hora_time + timedelta(hours=6)
            factura.fecha_certificacion = fecha_hora_modificada
            factura.xml_certificado = respuesta_json["xml_certificado"]
            if factura.certificacion_error:
                factura.certificacion_error = False
            factura.certificada = True

            var_numero_autorizacion = respuesta_json["uuid"]
            var_serie = respuesta_json["serie"]
            var_numero_dte = respuesta_json["numero"]
            var_fecha = date.today()

            link_factura = (
                f"https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid={var_numero_autorizacion}"
            )

            mensaje = f"""
                <strong style='display:block;'>Datos FEL de la factura</strong>
                <ul>
                    <li>
                        Número de autorización: {var_numero_autorizacion}
                    </li>
                    <li>
                        Serie: {var_serie}
                    </li>
                    <li>
                        Número DTE: {var_numero_dte}
                    </li>
                    <li>
                        Fecha: {var_fecha}
                    </li>
                </ul>
                <a href='{link_factura}' target='_blank'>Ver factura<a/>
            """

            factura.message_post(
                body=mensaje,
                body_is_html=True,
                author_id=self.env.ref("base.partner_root").id,
                subject="Factura certificada correctamente",
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

    def _post(self, soft):
        move_types = ["fact", "fact_cambiaria", "fact_exportacion", "out_refund"]
        por_certificar = self.filtered(
            lambda factura: factura.journal_id.facturacion_activa
            and (factura.tipo_factura in move_types or factura.factura_especial or not factura.tipo_factura)
            and not factura.certificada
        )

        for factura in por_certificar:
            self.facturacion_electronica(factura)

        continuar_movimientos = self.filtered(lambda fact: not fact.certificacion_error)
        return super(AccountMove, continuar_movimientos)._post(soft)

    def boton_anular(self):
        for factura in self:
            if factura.state == "posted" and not factura.motivo_anulacion:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "wizard.anular.factura",
                    "view_mode": "form",
                    "target": "new",
                    "context": {"default_factura_id": factura.id},
                }
            else:
                factura.procesar_anulacion()

    def procesar_anulacion(self):
        url = GC.credenciales_url()
        headers = GC.credenciales_header(self)

        for factura in self:
            if factura.state == "posted":
                if not factura.motivo_anulacion:
                    raise UserError("Debe indicar el motivo por el cual desea anular esta factura.")

                tree = ANL.anular_factura(self, factura)
                anular_xml, respuesta_json = self.certificar_documento(url, headers, tree)
                factura.numero_anulacion = respuesta_json["uuid"]
                factura.anulacion_serie = respuesta_json["serie"]
                factura.numero_dte_anulado = respuesta_json["numero"]
                factura.xml_cancelado_generado = anular_xml
                factura.xml_cancelado_certificado = respuesta_json["xml_certificado"]
                fecha_hora_obtenida = str(respuesta_json["fecha"])
                fecha = fecha_hora_obtenida.split("T")
                hora = fecha[1].split("-")
                hora_objeto = datetime.strptime(hora[0], "%H:%M:%S") + timedelta(hours=6)
                hora_formateada = str(hora_objeto).split(" ")
                factura.fecha_anulacion = f"{fecha[0]} {hora_formateada[1]}"
                self.mapped("line_ids").remove_move_reconcile()
                self.write({"state": "cancel", "is_move_sent": False})

            else:
                raise UserError("La factura ya se encuentra anulada.")
