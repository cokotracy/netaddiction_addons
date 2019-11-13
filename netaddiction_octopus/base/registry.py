from importlib import import_module


class Registry():

    def __init__(self):
        self.suppliers = {}

    def discover(self, location='odoo.addons.netaddiction_octopus.suppliers'):
        import_module(location)

    def register(self, supplier):
        self.suppliers[supplier.__name__] = supplier

    def __getitem__(self, supplier_id):
        return self.suppliers[supplier_id]

    def __iter__(self):
        for supplier in self.suppliers.values():
            yield supplier


registry = Registry()
registry.discover()


def custom_supplier_module(custom_supplier=None):
    if not custom_supplier:
        return False
    location=f'odoo.addons.netaddiction_octopus.suppliers.{custom_supplier}'
    return import_module(location)
