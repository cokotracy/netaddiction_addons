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
