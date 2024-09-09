import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


def anular_factura(self, factura):

    # ETIQUETA RAIZ DEL XML
    root = ET.Element(
        "dte:GTAnulacionDocumento",
        {
            "xmlns:ds": "http://www.w3.org/2000/09/xmldsig",
            "xmlns:dte": "http://www.sat.gob.gt/dte/fel/0.1.0",
            "xmlns:n1": "http://www.altova.com/samplexml/other-namespace",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "Version": "0.1",
            "xsi:schemaLocation": "http://www.sat.gob.gt/dte/fel/0.1.0",
        },
    )

    # INFORMACIÓN GENERAL DEL DOCUMENTO
    dte_sat = ET.SubElement(root, "dte:SAT")
    anulacion_dte = ET.SubElement(dte_sat, "dte:AnulacionDTE", {"ID": "DatosCertificados"})
    fecha_obtenida = str(factura.fecha_emision).split(" ")
    segundos = fecha_obtenida[1].split(".")
    hora_obtenida = datetime.strptime(segundos[0], "%H:%M:%S") - timedelta(hours=6)
    hora_final_str = str(hora_obtenida).split(" ")
    fecha_hora_formateada = f"{fecha_obtenida[0]}T{hora_final_str[1]}-06:00"
    fecha_anulacion = str(datetime.now()).split(" ")
    datos_generales = ET.SubElement(
        anulacion_dte,
        "dte:DatosGenerales",
        {
            "FechaEmisionDocumentoAnular": f"{fecha_hora_formateada}",
            "FechaHoraAnulacion": f"{fecha_anulacion[0]}T00:00:00-06:00",
            "ID": "DatosAnulacion",
            "IDReceptor": f"{factura.partner_id.vat}",
            "MotivoAnulacion": f"{factura.motivo_anulacion}",
            "NITEmisor": "11201094K",
            "NumeroDocumentoAAnular": f"{factura.numero_autorizacion}",
        },
    )
    tree = ET.ElementTree(root)
    return tree
