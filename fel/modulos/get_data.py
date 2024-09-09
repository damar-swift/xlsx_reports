def impuestos():
    impuestos_existentes = {
        "IVA 12%": {"nombre_corto": "IVA", "codigo_gravable": 1},
        "IVA 0%": {"nombre_corto": "IVA", "codigo_gravable": 2},
        "TURISMO HOSPEDAJE": {"nombre_corto": "TURISMO HOSPEDAJE", "codigo_gravable": 1},
        "Retención IVA factura especial": {"nombre_corto": "cfe:RetencionIVA"},
        "Retención ISR factura especial": {"nombre_corto": "cfe:RetencionISR"}
    }

    return impuestos_existentes


def medidas():
    udms = {"Unidades": "UND"}

    return udms
