#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    "name" : "Stock Product Location",
    "name_fr_FR" : "Emplacement de produit",
    "name_de_DE" : "Lagerverwaltung Artikel Lagerort",
    "name_es_ES" : "Ubicación de existencias de producto",
    "name_es_CO" : "Ubicación de existencias de producto",
    "version": "1.2.2",
    "author" : "B2CK",
    'email': 'info@b2ck.com',
    'website': 'http://www.tryton.org/',
    "description": '''Define default storage location by warehouse on product.
Theses locations will be used by the supplier shipment for generating
inventory moves.
''',
    "description_fr_FR": '''Defini un emplacement Magasin par défaut par produit.
Ces emplacements seront utilisés par les colisages fournisseurs pour
générer les mouvements internes.
''',
    "description_de_DE": '''Standardlagerorte für Artikel
    - Ermöglicht die Definition von Standardlagerorten für Artikel in einem Warenlager
    - Diese Lagerorte werden von Lieferposten von Lieferanten für die
      Lagerbewegungen benutzt
''',
    "description_es_ES": '''Define la ubicación del almacén predeterminado por depósito y producto.
Estas ubicaciones se utilizarán en el envio de proveedor para generar movimientos de inventario.
''',
    "description_es_CO": '''Define la ubicación de almacenamiento predeterminada
por depósito y producto.
Esta ubicación la utilizará el envío del proveedor para generar movimientos
de inventaio.
''',
    "depends" : [
        "ir",
        "product",
        "stock",
    ],
    "xml" : [
        "location.xml",
        "product.xml",
    ],
    'translation': [
        'fr_FR.csv',
        'de_DE.csv',
        'es_ES.csv',
        'es_CO.csv',
    ],
}
