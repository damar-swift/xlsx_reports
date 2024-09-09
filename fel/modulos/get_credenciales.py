def credenciales_url():
    return "https://certificador.feel.com.gt/fel/procesounificado/transaccion/v2/xml"


def credenciales_header(obj):
    return {
        "UsuarioFirma": f"{obj.company_id.usuario}",
        "LlaveFirma": f"{obj.company_id.llave_firma}",
        "UsuarioApi": f"{obj.company_id.usuario}",
        "LlaveApi": f"{obj.company_id.llave_api}",
        "Content-Type": "application/xml",
    }
