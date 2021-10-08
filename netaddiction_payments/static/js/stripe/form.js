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
    events: {
      'change input[type=radio]': 'pmChangeEvent',
    },

    willStart: function () {
      return this._super.apply(this, arguments).then(function () {
        return ajax.loadJS("https://js.stripe.com/v3/");
      })
    },
    /**
     * called when clicking a Stripe radio if configured for s2s flow; instanciates the card and bind it to the widget.
     *
     * @private
     * @param {DOMElement} checkedRadio
     */
    _bindStripeCard: function ($checkedRadio) {
      var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
      var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirerID);
      var inputsForm = $('input', acquirerForm);
      var formData = this.getFormData(inputsForm);
      console.log(formData);
      var stripe = Stripe(formData.stripe_publishable_key);
      var element = stripe.elements();
      var card = element.create('card', { hidePostalCode: true });
      card.mount('#card-element');
      card.on('ready', function (ev) {
        card.focus();
      });
      card.addEventListener('change', function (event) {
        var displayError = document.getElementById('card-errors');
        displayError.textContent = '';
        if (event.error) {
          displayError.textContent = event.error.message;
        }
      });
      this.stripe = stripe;
      this.stripe_card_element = card;
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
    addPmEvent: function (ev) {
      ev.stopPropagation();
      ev.preventDefault();
      var $checkedRadio = this.$('input[type="radio"]:checked');
      console.log($checkedRadio);

      if ($checkedRadio.length === 1 && this.isNewPaymentRadio($checkedRadio) && $checkedRadio.data('provider') === 'netaddiction_stripe') {
        console.log("Stripe selezionato!");
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