{
    "name": "Softer Website Patch",
    "version": "17.0.1.0.0",
    "category": "Website",
    "summary": "Parche para corregir el manejo de REQUEST_URI en website",
    "description": """
        Corrige el error KeyError: 'REQUEST_URI' en el método _is_canonical_url
        del módulo website cuando se ejecuta sin proxy reverso.
    """,
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "depends": ["base", "website"],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": True,
    "post_init_hook": "post_init_hook",
    "license": "LGPL-3",
}
