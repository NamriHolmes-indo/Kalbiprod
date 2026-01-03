{
    "name": "Kalbiprod",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Kalkulator bisnis untuk produk",
    "author": "Ngonsul-IT",
    "license": "LGPL-3",
    "depends": ["product", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/pricing_order_view.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
}
