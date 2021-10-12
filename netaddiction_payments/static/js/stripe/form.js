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
    xmlDependencies: ['/netaddiction_payments/static/xml/stripe/templates.xml'],
    selector: '.o_payment_form',
    events: _.extend({
      'change input[name="pm_id"][type="radio"]': 'pmChangeEvent',
      "click #stripeSaveCard": "stripeSaveCard",
      "submit #o_payment_form_pay": "_onSubmit",
    }),

    willStart: function () {
      return this._super.apply(this, arguments).then(function () {
        return ajax.loadJS("https://js.stripe.com/v3/");
      })
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     *
     * @private
     * @param {Object} stripe
     * @param {Object} formData
     * @param {Object} card
     * @returns {Promise}
     */
    _createCreditCard: function (stripe, formData, card) {
      stripe.createToken(card).then((result) => {
        if (result.error) {
          console.log(result.error);
        } else {
          return this._rpc({
            route: '/payment/netaddiction-stripe/create-payment-token',
            params: { 'acquirer_id': formData.acquirer_id, 'token': result.token }
          }).then(function (result) {
            console.log(result);
          });
        }
      })
    },

    /**
     *
     * @private
     * @param {Object} stripe
     * @param {Object} formData
     * @param {Object} card
     * @returns {Promise}
     */
    _setupIntentMethod: function (stripe, formData, card) {
      return this._rpc({
        route: '/payment/netaddiction-stripe/create-setup-intent',
        params: { 'acquirer_id': formData.acquirer_id }
      }).then(function (intent_secret) {
        return stripe.confirmCardSetup(intent_secret)
      });
    },

    /**
     *
     * @private
     * @param {Event} ev
     * @param {DOMElement} checkedRadio
     */
    _getOrCreateStripeToken: function (ev, $checkedRadio) {
      var self = this;
      var button = ev.target;
      this.disableButton(button);
      var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
      var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirerID);
      var inputsForm = $('input', acquirerForm);
      var formData = self.getFormData(inputsForm);
      var stripe = this.stripe;
      var card = this.stripe_card_element;
      if (card._invalid) {
        return;
      }
      this._createCreditCard(stripe, formData, card,)
      // this._createCreditCard(stripe, formData, card,).then(function (result) {
      //   if (result.error) {
      //     return Promise.reject({ "message": { "data": { "arguments": [result.error.message] } } });
      //   } else {
      //     console.log(result);
      //     // _.extend(formData, { "payment_method": result.setupIntent.payment_method });
      //     // return self._rpc({
      //     //   route: formData.data_set,
      //     //   params: formData,
      //     // });
      //   }
      // }
      // }).then(function (result) {
      //   // $('input:first', acquirerForm).after(`<input type="hidden" name="pm_id" value="${result.id}">`)
      //   $checkedRadio.val(result.id);
      //   self.el.submit();
      // }).guardedCatch(function (error) {
      //   if (error.event) {
      //     error.event.preventDefault();
      //   }
      //   self.enableButton(button);
      //   self._displayError("Impossibile utilizzare la seguente carta di credito/debito");
      // });
    },

    /**
     *
     * @private
     * @param {DOMElement} checkedRadio
     */
    _bindStripeCard: function ($checkedRadio) {
      var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
      var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirerID);
      $(acquirerForm).removeClass("d-none");
      var inputsForm = $('input', acquirerForm);
      var formData = this.getFormData(inputsForm);
      var stripe = Stripe(formData.stripe_key);
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
     *
     * @private
     * @param {DOMElement} checkedRadio
     */
    _loadCardView: function ($checkedRadio) {
      let acquirer_id = this.getAcquirerIdFromRadio($checkedRadio);
      this._rpc({
        route: '/payment/netaddiction-stripe/get-payments-token',
        params: { 'acquirer_id': acquirer_id }
      }).then(function (data) {
        console.log(data);
        var cards = $(qweb.render('stripe.cards'));
        cards.appendTo($('#cards-list'));
      });
    },

    /**
     *
     * @private
     */
    _unloadCardView: function () {
      $('#cards-list').html('');
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
      var $checkedRadio = this.$('input[name="pm_id"][type="radio"]:checked');
      // we hide all the acquirers form
      this.$('[id*="o_payment_add_token_acq_"]').addClass('d-none');
      this.$('[id*="o_payment_form_acq_"]').addClass('d-none');
      if ($checkedRadio.length !== 1) {
        return;
      }
      $checkedRadio = $checkedRadio[0];
      var acquirer_id = this.getAcquirerIdFromRadio($checkedRadio);

      if (this.isNewPaymentRadio($checkedRadio)) {
        this.$('#o_payment_add_token_acq_' + acquirer_id).removeClass('d-none');
      }
      else if (this.isFormPaymentRadio($checkedRadio)) {
        this.$('#o_payment_form_acq_' + acquirer_id).removeClass('d-none');
      }

      var provider = $checkedRadio.dataset.provider
      if (provider === 'netaddiction_stripe') {
        // always re-init stripe (in case of multiple acquirers for stripe, make sure the stripe instance is using the right key)
        this._unbindStripeCard();
        this._unloadCardView();
        this._bindStripeCard($checkedRadio);
        this._loadCardView($checkedRadio);

      }

    },

    /**
     * @param {String} message
     * @override
     */
    _displayError: function (message) {
      var wizard = $(qweb.render('stripe.error', { 'msg': message || _t('Payment error') }));
      wizard.appendTo($('body')).modal({ 'keyboard': true });
      $("#o_payment_form_pay").removeAttr('disabled');
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    onSubmit: function (ev) {
      ev.stopPropagation();
      ev.preventDefault();

      var button = $(ev.target).find('*[type="submit"]')[0]
      if (button.id === 'o_payment_form_pay') {
        return this.payEvent(ev);
      } else if (button.id === 'o_payment_form_add_pm') {
        return this.addPmEvent(ev);
      }
      return;
    },

    /**
    * @override
    */
    payEvent: function (ev) {
      ev.preventDefault();
      var $checkedRadio = this.$('input[name="pm_id"][type="radio"]:checked');
      if ($checkedRadio.length === 1 && $checkedRadio.data('provider') === 'netaddiction_stripe') {
        // return this._getOrCreateStripeToken(ev, $checkedRadio);
        console.log("Pagamento con Stripe");
      } else {
        return this._super.apply(this, arguments);
      }
    },

    pmChangeEvent: function (ev) {
      $(ev.currentTarget).find('input[name="pm_id"][type="radio"]').prop("checked", true);
      this.updateNewPaymentDisplayStatus();
    },

    stripeSaveCard: function (ev) {
      ev.preventDefault();
      var $checkedRadio = this.$('input[name="pm_id"][type="radio"]:checked');
      this._getOrCreateStripeToken(ev, $checkedRadio);
    }

  })

})