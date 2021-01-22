from odoo import models


class AutoPreparation(models.TransientModel):
    _inherit = 'stock.picking.to.batch'

    def attach_pickings(self):
        """ COMPLETE OVERRIDE OF THE STANDARD METHOD """

        # versione base, metto in lista le spedizioni segnate
        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        error_stock = []
        subtype = self.env.ref('netaddiction_warehouse.error_autopreparation')
        # TODO: Da Migrare.
        # Non trovo il modello base e non ho idea di cosa faccia
        # exec_obj = self.env['netaddiction.positivity.executor']
        mail_obj = self.env['mail.message']

        for pick in pickings:
            note = []
            # pay = True
            # se non è disponibile
            if pick.state != 'assigned':
                error_stock.append(pick.id)
                note.append('Non è disponibile.')
                # pay = False
            # se ha già una lista
            if pick.batch_id:
                error_stock.append(pick.id)
                note.append('Ha già una lista associata.')
                # pay = False
            # se non è in lavorazione o in parzialmente completato
            if pick.sale_id.state not in ['sale', 'partial_done']:
                error_stock.append(pick.id)
                note.append(
                    'L\'ordine non è in lavorazione o in'
                    ' parzialmente completato'
                )
                # pay = False

            # FIXME: res.partner's 'rating' field has not been migrated
            # controllo indirizzo e valutazione cliente
            # if pick.sale_id.partner_id.rating == 0:
            #     error_stock.append(pick.id)
            #     note.append('Rating cliente negativo')
            #     pay = False

            shipping_address = pick.sale_id.partner_shipping_id
            if not shipping_address.street \
                    or not shipping_address.street2 \
                    or not shipping_address.city:
                error_stock.append(pick.id)
                note.append('Mancano dati nell\'indirizzo di spedizione')
                # pay = False

            if pick.verify_quantity():
                error_stock.append(pick.id)
                note.append(
                    'Una spedizione dell\'ordine ha un prodotto con quantità'
                    ' maggiore di quella acquistata dal cliente'
                )
                # pay = False
            # if stock.sale_id.customer_comment:
            #    error_stock.append(stock.id)
            #    note.append('Commento Cliente')
            #    pay = False

            # cc_pay = self.env.ref('netaddiction_payments.cc_journal')
            # TODO this payment method is not used anymore? Maybe Andrea
            #  Colangelo will be your hero here
            # if pay and pick.sale_order_payment_method.id == cc_pay.id:
            #     payment = pick.payment_id
            #     if not payment:
            #         error_stock.append(pick.id)
            #         note.append('Non c\'è il pagamento')
            #     cc_pay = self.env.ref('netaddiction_payments.cc_journal')
            #     if payment.journal_id.id == cc_pay.id:
            #         if payment.state != 'posted' \
            #                 and payment.cc_status != 'commit':
            #             try:
            #                 exec_obj.auth_and_check(
            #                     payment.partner_id.id,
            #                     payment.partner_id.email, payment.amount,
            #                     payment.cc_token, pick.sale_id.id
            #                 )
            #             except Exception as e:
            #                 error_stock.append(pick.id)
            #                 note.append(str(e) or repr(e))

            if note:
                mail_obj.create({
                    'subject': 'Errori autopreparazione',
                    'message_type': 'notification',
                    'model': 'stock.picking',
                    'res_id': pick.id,
                    'body': '<br/>'.join(note),
                    'subtype_id': subtype.id
                })
            else:
                pick.write({'batch_id': self.batch_id.id})

        if len(error_stock) > 0:
            act = self.env.ref('stock.action_picking_tree_all').read()[0]
            act['domain'] = [('id', 'in', error_stock)]
            act['display_name'] = 'Spedizioni con errori'
            return act
        return {}
