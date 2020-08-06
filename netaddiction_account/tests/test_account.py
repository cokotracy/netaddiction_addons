from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('standard', 'post_install')
class TestNetaddictionInvoice(TransactionCase):

    def setUp(self):
        super(TestNetaddictionInvoice, self).setUp()
        self.account_invoice = self.env['account.invoice']
        self.account_model = self.env['account.account']
        self.current_user = self.env.user
        self.invoice_account = self.account_model.search([
            ('user_type_id',
             '=',
             self.env.ref('account.data_account_type_receivable').id)
            ], limit=1)
        self.invoice_line_data = {
            'name': 'Test invoice line',
            'account_id': self.invoice_account.id,
            'quantity': 1.000,
            'price_unit': 1.00,
            }
        self.partner = self.env.ref('base.res_partner_2')
        self.simple_invoice_data = {
            'partner_id': self.partner.id,
            'is_customer_invoice': False,
            'sequence_number_next': '0001',
            'account_id': self.invoice_account.id,
            'type': 'in_invoice',
            'invoice_line_ids': [(0, 0, self.invoice_line_data)]
            }
        self.customer_invoice_data = {
            'partner_id': self.partner.id,
            'is_customer_invoice': True,
            'sequence_number_next': '0001',
            'account_id': self.invoice_account.id,
            'type': 'in_invoice',
            'invoice_line_ids': [(0, 0, self.invoice_line_data)]
            }

    def _create_invoice(self, values):
        invoice = self.account_invoice.create(values)
        invoice.journal_id.update_posted = True
        return invoice

    def test_no_vat_or_fiscalcode_partner(self):
        partner = self.partner
        partner.vat = ''
        partner.fiscalcode = ''
        invoice = self.account_invoice.create(self.simple_invoice_data)
        with self.assertRaises(UserError):
            invoice.is_customer_invoice = True

    def test_netaddiction_basic_invoice(self):
        invoice = self._create_invoice(self.simple_invoice_data)
        self.assertEqual(invoice.customer_number_identifier, '')
        invoice.action_move_create()
        self.assertFalse(invoice.number.endswith('.1'))
        self.assertFalse(invoice.move_id.name.endswith('.1'))

    def test_netaddiction_customer_invoice(self):
        invoice = self._create_invoice(self.customer_invoice_data)
        self.assertEqual(invoice.customer_number_identifier, '.1')
        invoice.action_move_create()
        self.assertTrue(invoice.number.endswith('.1'))
        self.assertTrue(invoice.move_id.name.endswith('.1'))

    def test_create_simple_invoice_change_to_customer(self):
        invoice = self._create_invoice(self.simple_invoice_data)
        invoice.partner_id.fiscalcode = 'AABBB70B12R999L'
        invoice.action_move_create()
        old_invoice_number = invoice.number
        invoice.action_invoice_cancel()
        invoice.action_invoice_draft()
        invoice.is_customer_invoice = True
        invoice.action_move_create()
        new_invoice_number = invoice.number
        self.assertNotEqual(old_invoice_number, new_invoice_number)
