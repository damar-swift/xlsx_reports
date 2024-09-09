from odoo.exceptions import ValidationError  # type: ignore
import xml.etree.ElementTree as ET
from datetime import datetime
from ..modulos import get_data as data


def generar_nota_debito(self, factura):

    if not factura.debit_origin_id:
        raise ValidationError("La nota de débito debe ser creada a base de una factura existente")

    # ETIQUETA RAIZ DEL XML
    root = ET.Element(
        "dte:GTDocumento",
        {
            "xmlns:ds": "http://www.w3.org/2000/09/xmldsig",
            "xmlns:dte": "http://www.sat.gob.gt/dte/fel/0.2.0",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "Version": "0.1",
            "xsi:schemaLocation": "http://www.sat.gob.gt/dte/fel/0.2.0",
        },
    )

    # INFORMACIÓN GENERAL DEL DOCUMENTO
    dte_sat = ET.SubElement(root, "dte:SAT", {"ClaseDocumento": "dte"})
    dte_dte = ET.SubElement(dte_sat, "dte:DTE", {"ID": "DatosCertificados"})
    datos_emision = ET.SubElement(dte_dte, "dte:DatosEmision", {"ID": "DatosEmision"})
    fecha_obtenida = str(datetime.now()).split(" ")[0] if not factura.invoice_date else factura.invoice_date

    datos_generales = ET.SubElement(
        datos_emision,
        "dte:DatosGenerales",
        {
            "CodigoMoneda": f"{factura.currency_id.name}",
            "FechaHoraEmision": f"{fecha_obtenida}T00:00:00-06:00",
            "Tipo": "NDEB",
        },
    )

    # DATOS DEL EMISOR
    afiliacion_iva = "GEN" if factura.company_id.tipo_contribuyente == "general" else ""
    dte_emisor = ET.SubElement(
        datos_emision,
        "dte:Emisor",
        {
            "AfiliacionIVA": f"{afiliacion_iva}",
            "CodigoEstablecimiento": "1",
            "CorreoEmisor": f"{factura.company_id.email}",
            "NITEmisor": "11201094K",
            "NombreComercial": f"{factura.company_id.usuario}",
            "NombreEmisor": "PRODUCTOS ELECTRICOS CENTROAMERICANOS, S.A",
        },
    )
    direccion_emisor = ET.SubElement(dte_emisor, "dte:DireccionEmisor")
    dte_direccion_emisor = ET.SubElement(direccion_emisor, "dte:Direccion").text = f"{factura.company_id.street}"
    codigo_postal_emisor = ET.SubElement(direccion_emisor, "dte:CodigoPostal").text = f"{factura.company_id.zip}"
    municipio_emisor = ET.SubElement(direccion_emisor, "dte:Municipio").text = f"{factura.company_id.city}"
    departamento_emisor = ET.SubElement(direccion_emisor, "dte:Departamento").text = (
        f"{factura.company_id.state_id.name}"
    )
    pais_emisor = ET.SubElement(direccion_emisor, "dte:Pais").text = f"{factura.company_id.country_id.code}"

    # DATOS DEL RECEPTOR
    correo_receptor = f"{factura.partner_id.email}" if factura.partner_id.email else ""
    nombre_receptor = (
        f"{factura.partner_id.razon_social}" if not factura.partner_id.extranjero else f"{factura.partner_id.name}"
    )
    dte_receptor = ET.SubElement(
        datos_emision,
        "dte:Receptor",
        {
            "CorreoReceptor": correo_receptor,
            "IDReceptor": f"{factura.partner_id.vat}",
            "NombreReceptor": f"{nombre_receptor}",
        },
    )
    direccion_receptor = ET.SubElement(dte_receptor, "dte:DireccionReceptor")
    direccion_receptor_valor = f"{factura.partner_id.street}" if factura.partner_id.street else "CIUDAD"
    dte_direccion_receptor = ET.SubElement(direccion_receptor, "dte:Direccion").text = f"{direccion_receptor_valor}"
    codigo_postal = f"{factura.partner_id.zip}" if factura.partner_id.zip else "00000"
    codigo_postal_receptor = ET.SubElement(direccion_receptor, "dte:CodigoPostal").text = codigo_postal
    municipio = f"{factura.partner_id.state_id}" if factura.partner_id.state_id else "Guatemala"
    municipio_receptor = ET.SubElement(direccion_receptor, "dte:Municipio").text = municipio
    departamento = f"{factura.partner_id.city}" if factura.partner_id.city else "Guatemala"
    departamento_receptor = ET.SubElement(direccion_receptor, "dte:Departamento").text = departamento
    pais_receptor = ET.SubElement(direccion_receptor, "dte:Pais").text = f"{factura.partner_id.country_id.code}"

    # FRASES
    dte_frases = ET.SubElement(datos_emision, "dte:Frases")
    if factura.company_id.tipo_contribuyente == "general":
        if factura.company_id.regimen_isr == "utilities":
            frase_uno_escenario = 1
        elif factura.company_id.regimen_isr == "simplified":
            frase_uno_escenario = 2
        frase_uno = ET.SubElement(
            dte_frases, "dte:Frase", {"TipoFrase": "1", "CodigoEscenario": f"{frase_uno_escenario}"}
        )

    if factura.company_id.retenedor_iva:
        frase_dos = ET.SubElement(dte_frases, "dte:Frase", {"TipoFrase": "2", "CodigoEscenario": "1"})

    if factura.fiscal_position_id.frases_fel_id:
        for frase in factura.fiscal_position_id.frases_fel_id:
            frase_fel = ET.SubElement(
                dte_frases,
                "dte:Frase",
                {
                    "TipoFrase": f"{frase.tipo_frase}",
                    "CodigoEscenario": f"{frase.codigo_escenario}",
                },
            )

    # ITEMS
    dte_items = ET.SubElement(datos_emision, "dte:Items")
    linea = 1
    udms = data.medidas()
    impuestos_encontrados = dict()
    impuestos_existentes = data.impuestos()

    for impuesto_existente in self.env["account.tax"].search([("name", "in", list(impuestos_existentes.keys()))]):
        impuestos_existentes[impuesto_existente.name]["importe"] = impuesto_existente.amount / 100

    for line in factura.invoice_line_ids:
        bien_o_servicio = "B" if line.product_id.detailed_type != "service" else "S"
        dte_item = ET.SubElement(
            dte_items,
            "dte:Item",
            {"BienOServicio": f"{bien_o_servicio}", "NumeroLinea": f"{linea}"},
        )
        linea += 1
        descuento = round((line.discount / 100 * line.price_unit * line.quantity), 2)
        dte_cantidad = ET.SubElement(dte_item, "dte:Cantidad").text = f"{line.quantity}"
        unidad_medida = ET.SubElement(dte_item, "dte:UnidadMedida").text = udms[f"{line.product_uom_id.name}"]
        dte_descripcion = ET.SubElement(dte_item, "dte:Descripcion").text = f"{line.product_id.name}"
        precio_unitario = ET.SubElement(dte_item, "dte:PrecioUnitario").text = f"{line.price_unit}"
        dte_precio = ET.SubElement(dte_item, "dte:Precio").text = f"{round((line.price_unit*line.quantity), 2)}"
        dte_descuento = ET.SubElement(dte_item, "dte:Descuento").text = f"{descuento}"

        # IMPUESTOS DEL ITEM
        dte_impuestos = ET.SubElement(dte_item, "dte:Impuestos")
        for impuesto in line.tax_ids:
            dte_impuesto = ET.SubElement(dte_impuestos, "dte:Impuesto")
            nombre = impuestos_existentes[impuesto.name]["nombre_corto"]
            nombre_corto = ET.SubElement(dte_impuesto, "dte:NombreCorto").text = f"{nombre}"
            codigo_gravable = impuestos_existentes[impuesto.name]["codigo_gravable"]
            codigo_unidad_gravable = ET.SubElement(dte_impuesto, "dte:CodigoUnidadGravable").text = f"{codigo_gravable}"
            monto_gravable = ET.SubElement(dte_impuesto, "dte:MontoGravable").text = f"{line.price_subtotal}"
            importe = impuestos_existentes[impuesto.name]["importe"]
            monto = round((line.price_subtotal * float(importe)), 2)
            monto_impuesto = ET.SubElement(dte_impuesto, "dte:MontoImpuesto").text = f"{monto}"

            impuestos_encontrados[nombre] = impuestos_encontrados.get(nombre, 0) + monto

        dte_total = ET.SubElement(dte_item, "dte:Total").text = f"{line.price_total}"

    # TOTALES
    dte_totales = ET.SubElement(datos_emision, "dte:Totales")
    total_impuestos = ET.SubElement(dte_totales, "dte:TotalImpuestos")
    for registro_impuesto, registro_monto in impuestos_encontrados.items():
        total_impuesto = ET.SubElement(
            total_impuestos,
            "dte:TotalImpuesto",
            {"NombreCorto": f"{registro_impuesto}", "TotalMontoImpuesto": f"{round(registro_monto, 2)}"},
        )

    gran_total = ET.SubElement(dte_totales, "dte:GranTotal").text = f"{factura.amount_total}"

    # COMPLEMENTOS
    dte_complementos = ET.SubElement(datos_emision, "dte:Complementos")
    dte_complemento = ET.SubElement(
        dte_complementos,
        "dte:Complemento",
        {
            "IDComplemento": "TEXT",
            "NombreComplemento": "TEXT",
            "URIComplemento": "TEXT",
        },
    )
    referencias_nota = ET.SubElement(
        dte_complemento,
        "cno:ReferenciasNota",
        {
            "xmlns:cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0",
            "FechaEmisionDocumentoOrigen": f"{factura.debit_origin_id.invoice_date}",
            "MotivoAjuste": f"{factura.ref}",
            "NumeroAutorizacionDocumentoOrigen": f"{factura.debit_origin_id.numero_autorizacion}",
            "NumeroDocumentoOrigen": f"{factura.debit_origin_id.numero_dte}",
            "SerieDocumentoOrigen": f"{factura.debit_origin_id.serie}",
            "Version": f"{0.0}",
        },
    )

    # ADENDAS
    dte_adenda = ET.SubElement(dte_sat, "dte:Adenda")
    referencia_cliente = factura.ref if factura.ref else ""
    envios_orden_compra = ET.SubElement(dte_adenda, "envios-orden-compra").text = f"{referencia_cliente}"
    numero_interno = ET.SubElement(dte_adenda, "numerointerno").text = f"{factura.name}"

    telefono = ""
    if factura.partner_id.phone:
        telefono = factura.partner_id.phone
    elif factura.partner_id.mobile:
        telefono = factura.partner_id.mobile

    telefono_cliente = ET.SubElement(dte_adenda, "telefonocliente").text = f"{telefono}"
    iniciales_vendedor = ET.SubElement(dte_adenda, "inicialesvendedor").text = f"{factura.invoice_user_id.name}"
    codigo_cliente = ET.SubElement(dte_adenda, "codigocliente").text = f"{factura.partner_id.id}"

    # EXPORTACIÓN
    if factura.debit_origin_id.exportacion:
        datos_generales.set("Exp", "SI")
        dte_receptor.set("TipoEspecial", "EXT")

    tree = ET.ElementTree(root)
    return tree
