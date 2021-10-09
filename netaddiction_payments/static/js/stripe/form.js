odoo.define('payment_netaddiction_stripe.payment_form', function (require) {
  "use strict";

  var ajax = require('web.ajax');
  var core = require('web.core');
  var Dialog = require('web.Dialog');
  var PaymentForm = require('payment.payment_form');

  var qweb = core.qweb;
  var _t = core._t;

  ajax.loadXML('/netaddiction_payments/static/xml/stripe/templates.xml', qweb);

  PaymentForm.include({

    selector: '.o_payment_form',
    events: _.extend({
      'change input[type=radio]': 'pmChangeEvent',
    }),

    willStart: function () {
      return this._super.apply(this, arguments).then(function () {
        return ajax.loadJS("https://js.stripe.com/v3/");
      })
    },
    /**
     * called when clicking on pay now or add payment event to create token for credit card/debit card.
     *
     * @private
     * @param {Event} ev
     * @param {DOMElement} checkedRadio
     * @param {Boolean} addPmEvent
     */
    _getOrCreateStripeToken: function (ev, $checkedRadio, addPmEvent) {
      var self = this;
      if (ev.type === 'submit') {
        var button = $(ev.target).find('*[type="submit"]')[0]
      } else {
        var button = ev.target;
      }
      console.log("Chiamare Stripe");
      this.disableButton(button);
      // var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
      // var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirerID);
      // var inputsForm = $('input', acquirerForm);
      // if (this.options.partnerId === undefined) {
      //   console.warn('payment_form: unset partner_id when adding new token; things could go wrong');
      // }

      // var formData = self.getFormData(inputsForm);
      // var stripe = this.stripe;
      // var card = this.stripe_card_element;
      // if (card._invalid) {
      //   return;
      // }
      // this._createPaymentMethod(stripe, formData, card, addPmEvent).then(function (result) {
      //   if (result.error) {
      //     return Promise.reject({ "message": { "data": { "arguments": [result.error.message] } } });
      //   } else {
      //     const paymentMethod = addPmEvent ? result.setupIntent.payment_method : result.paymentMethod.id;
      //     _.extend(formData, { "payment_method": paymentMethod });
      //     return self._rpc({
      //       route: formData.data_set,
      //       params: formData,
      //     });
      //   }
      // }).then(function (result) {
      //   if (addPmEvent) {
      //     if (formData.return_url) {
      //       window.location = formData.return_url;
      //     } else {
      //       window.location.reload();
      //     }
      //   } else {
      //     $checkedRadio.val(result.id);
      //     self.el.submit();
      //   }
      // }).guardedCatch(function (error) {
      //   // We don't want to open the Error dialog since
      //   // we already have a container displaying the error
      //   if (error.event) {
      //     error.event.preventDefault();
      //   }
      //   // if the rpc fails, pretty obvious
      //   self.enableButton(button);
      //   self.displayError(
      //     _t('Unable to save card'),
      //     _t("We are not able to add your payment method at the moment. ") +
      //     self._parseError(error)
      //   );
      // });
    },
    /**
     * called when clicking a Stripe radio if configured for s2s flow; instanciates the card and bind it to the widget.
     *
     * @private
     * @param {DOMElement} checkedRadio
     */
    _bindStripeCard: function ($checkedRadio) {
      // var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
      // var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirerID);
      // var inputsForm = $('input', acquirerForm);
      // var formData = this.getFormData(inputsForm);
      // var stripe = Stripe(formData.stripe_key);
      // var element = stripe.elements();
      // var card = element.create('card', { hidePostalCode: true });
      // card.mount('#card-element');
      // card.on('ready', function (ev) {
      //   card.focus();
      // });
      // card.addEventListener('change', function (event) {
      //   var displayError = document.getElementById('card-errors');
      //   displayError.textContent = '';
      //   if (event.error) {
      //     displayError.textContent = event.error.message;
      //   }
      // });
      // this.stripe = stripe;
      // this.stripe_card_element = card;
    },
    /**
     * destroys the card element and any stripe instance linked to the widget.
     *
     * @private
     */
    _unbindStripeCard: function () {
      if (this.stripe_card_element) {
        this.stripe_card_element.destroy();
      }
      this.stripe = undefined;
      this.stripe_card_element = undefined;
    },
    /**
     * @override
     */
    updateNewPaymentDisplayStatus: function () {
      var $checkedRadio = this.$('input[type="radio"]:checked');

      if ($checkedRadio.length !== 1) {
        return;
      }
      var provider = $checkedRadio.data('provider')
      if (provider === 'netaddiction_stripe') {
        // always re-init stripe (in case of multiple acquirers for stripe, make sure the stripe instance is using the right key)
        this._unbindStripeCard();
        this._bindStripeCard($checkedRadio);
      }
      return this._super.apply(this, arguments);
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    payEvent: function (ev) {
      ev.preventDefault();
      console.log('asdasdasdasda');
      var $checkedRadio = this.$('input[type="radio"]:checked');
      console.log($checkedRadio);
      if ($checkedRadio.length === 1 && $checkedRadio.data('provider') === 'netaddiction_stripe') {
        return this._getOrCreateStripeToken(ev, $checkedRadio);
      } else {
        return this._super.apply(this, arguments);
      }
    },

    pmChangeEvent: function (ev) {
      $(ev.currentTarget).find('input[type="radio"]').prop("checked", true);
      this.updateNewPaymentDisplayStatus();
    },

  })

})