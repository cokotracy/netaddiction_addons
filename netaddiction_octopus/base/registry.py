from importlib import import_module


def custom_supplier_module(custom_supplier=None):
    if not custom_supplier:
        return False
    custom_supplier = custom_supplier.strip().lower()
    location = f'odoo.addons.netaddiction_octopus.suppliers.{custom_supplier}'
    return import_module(location)


def handler_class(handler=None):
    if not handler:
        return False
    handler = handler.strip().lower()
    module = custom_supplier_module(handler)
    return module.CustomSupplier
