odoo.define('payment_netaddiction_stripe.payment_form', function (require) {
  "use strict";

  var ajax = require('web.ajax');
  var core = require('web.core');
  var PaymentForm = require('payment.payment_form');

  var qweb = core.qweb;
  var _t = core._t;

  ajax.loadXML('/netaddiction_payments/static/xml/stripe/templates.xml', qweb);

  PaymentForm.include({
    xmlDependencies: ['/netaddiction_payments/static/xml/stripe/templates.xml'],
    events: _.extend({}, PaymentForm.prototype.events, {
      "change input[name='pm_id'][type='radio']": "pmChangeEvent",
      "click #stripeSaveCard": "stripeSaveCard",
    }),
    willStart: function () {
      return this._super.apply(this, arguments).then(function () {
        $('.card-body label span.payment_option_name').each(function () {
          $(this).parent().parent().css('display', 'none');
        })

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
      return stripe.createToken(card).then((data) => {
        if (data.error) {
          return data.error
        } else {
          return this._rpc({
            route: '/payment/netaddiction-stripe/create-payment-token',
            params: { 'acquirer_id': formData.acquirer_id, 'token': data.token }
          })
        }
      })
    },

    /**
     *
     * @private
     * @param {Object} stripe
     * @param {Object} formData
     * @returns {Promise}
     */
    _setupIntentMethod: function (stripe, acquirerID, token) {
      return this._rpc({
        route: '/payment/netaddiction-stripe/create-setup-intent',
        params: { 'acquirer_id': acquirerID, 'token': token }
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
    _createStripeToken: function (ev, $checkedRadio) {
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
      this._createCreditCard(stripe, formData, card).then((result) => {
        this.enableButton(button);
        if (result.error) {
          return Promise.reject({ "message": result.error.message });
        } else {
          $checkedRadio.val(result.token);
          $(acquirerForm).slideUp(() => {
            this._unloadCardView()
            this._unbindStripeCard();
            setTimeout(() => {
              this._bindStripeCard($checkedRadio);
              this._loadCardView($checkedRadio)
              $(acquirerForm).slideDown("slow")
            }, 1000);
          });
        }
      }).guardedCatch((error) => {
        if (error.event) {
          error.event.preventDefault();
        }
        this.enableButton(button);
        let error_message = (error.message !== "") ? error.message : "Impossibile aggiungere la carta di credito."
        this._displayError(`${error_message} Se il problema persiste contattare il servizio clienti`);
      });
    },

    /**
    *
    * @private
    * @param {Event} ev
    * @param {DOMElement} checkedRadio
    */
    _createIntentPayment: function (ev, $checkedRadio) {
      var self = this;
      var stripe = this.stripe;
      var button = $(ev.target).find('*[type="submit"]')[0];
      var token = $checkedRadio.val()
      this.disableButton(button);
      var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
      this._setupIntentMethod(stripe, acquirerID, token).then((result) => {
        if (result.error) {
          return Promise.reject({ "message": result.error.message });
        } else {
          self.el.submit();
        }
      }).guardedCatch((error) => {
        if (error.event) {
          error.event.preventDefault();
        }
        this.enableButton(button);
        if (error.message) {
          this._displayError("Impossibile completare il pagamento, controllare i dati della carta di credito. Se il problema persiste contattare il servizio clienti");
        }
      });
    },

    /**
     *
     * @private
     * @param {DOMElement} checkedRadio
     */
    _bindStripeCard: function ($checkedRadio) {
      var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
      var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirerID);
      $(acquirerForm).hide().removeClass("d-none").slideDown();
      var inputsForm = $('input', acquirerForm);
      var formData = this.getFormData(inputsForm);
      var stripe = Stripe(formData.stripe_key, { locale: 'it' });
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
      var self = this;
      var $checkedRadio = $checkedRadio
      let acquirer_id = this.getAcquirerIdFromRadio($checkedRadio);
      var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirer_id);

      this._rpc({
        route: '/payment/netaddiction-stripe/get-payments-token',
        params: { 'acquirer_id': acquirer_id }
      }).then(function (data) {
        if (data != null) {
          data.map((card, index) => {
            var cards = $(qweb.render('stripe.cards', card));
            cards.appendTo($('#cards-list'));
            if (card.isDefault === true) {
              $checkedRadio.value = card.id;
            }
            else {
              $(`#card_template_${card.id} .card_default_change`).click(function () {
                self._rpc({
                  route: '/payment/netaddiction-stripe/set-default-payment',
                  params: { 'acquirer_id': acquirer_id, 'token': card.id }
                }).then(function (data) {
                  $(acquirerForm).slideUp(() => {
                    self._unloadCardView()
                    self._unbindStripeCard();
                    setTimeout(() => {
                      self._bindStripeCard($checkedRadio);
                      self._loadCardView($checkedRadio)
                      $(acquirerForm).slideDown("slow")
                    }, 1000);
                  });
                });
              });
            }
            $(`#card_template_${card.id}`).click(function () {
              $('#cards-list > .card_stripe').each(function () {
                if (this.id == `card_template_${card.id}`) {
                  this.querySelector('input').checked = true;
                  $checkedRadio.value = card.id;
                }
                else {
                  this.querySelector('input').checked = false;
                }
              });
            });
          })
        }
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

      } else {
        this._unbindStripeCard();
        this._unloadCardView();
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
    payEvent: function (ev) {
      ev.preventDefault();
      var $checkedRadio = this.$('input[name="pm_id"][type="radio"]:checked');
      if ($checkedRadio.length === 1 && $checkedRadio.data('provider') === 'netaddiction_stripe') {
        return this._createIntentPayment(ev, $checkedRadio);
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
      this._createStripeToken(ev, $checkedRadio);
    }

  })

})