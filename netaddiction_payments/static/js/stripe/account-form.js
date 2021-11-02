odoo.define('payment_netaddiction_stripe.payment_account_form', function (require) {
  "use strict";

  var ajax = require('web.ajax');
  var core = require('web.core');
  var qweb = core.qweb;
  var _t = core._t;
  var publicWidget = require('web.public.widget');

  ajax.loadXML('/netaddiction_payments/static/xml/stripe/templates.xml', qweb);

  publicWidget.registry.PaymentMethodForm = publicWidget.Widget.extend({
    selector: '#_payment_method_form',
    events: {
      'submit': 'onSubmit',
      'click #_add_pm': 'addPmEvent',
      'click #_delete_pm': 'deletePmEvent',
    },

    /**
     * @override
     */
    start: function () {
      return ajax.loadJS("https://js.stripe.com/v3/").then(() => {
        let pm_form = document.querySelector("#_payment_method_form")
        this.stripe_key = pm_form.dataset.stripe
        this.acquirer_id = pm_form.dataset.acquirer

        this._bindStripeCard()
        this._loadCardView()
      });
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
    _createCreditCard: function (card) {
      return this.stripe.createToken(card).then((data) => {
        if (data.error) {
          return data
        } else {
          return this._rpc({
            route: '/payment/netaddiction-stripe/create-payment-token',
            params: { 'acquirer_id': this.acquirer_id, 'token': data.token }
          })
        }
      })
    },

    /**
     * @private
     * @param {Event} ev
     */
    _createPaymentToken: function (ev) {
      let button = ev.target
      let card = this.stripe_card_element;
      this.disableButton(button)
      if (card._invalid) {
        return;
      }
      this._createCreditCard(card).then((result) => {
        this.enableButton(button);
        if (result.error) {
          console.log(result.error);
          return Promise.reject({ "message": result.error.message });
        } else {
          $("#card-wrapper").slideUp(() => {
            this._unloadCardView();
            this._unbindStripeCard();

            this._loadCardView();
            this._bindStripeCard();
            setTimeout(() => {
              $("#card-wrapper").slideDown("slow")
            }, 1500);
          });
        }
      }).guardedCatch((error) => {
        if (error.event) {
          error.event.preventDefault();
        }
        this.enableButton(button);
        let error_message = (error.message !== "") ? error.message : "Impossibile aggiungere la carta di credito."
        console.log(error_message);
        this._displayError(`${error_message} Se il problema persiste contattare il servizio clienti`);
      });

    },

    /**
     *
     * @private
     */
    _bindStripeCard: function () {
      var stripe = Stripe(this.stripe_key, { locale: 'it' });
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
     *
     * @private
     */
    _loadCardView: function () {
      this._rpc({
        route: '/payment/netaddiction-stripe/get-payments-token',
        params: { 'acquirer_id': this.acquirer_id }
      }).then((data) => {
        if (data != null) {
          data.map((card) => {
            var cards = $(qweb.render('stripe.cards', card));
            $("input", cards).hide();
            cards.appendTo($('#cards-list'));
            $(`#card_template_${card.id} .card_default_change`).click(() => {
              this._rpc({
                route: '/payment/netaddiction-stripe/set-default-payment',
                params: { 'acquirer_id': this.acquirer_id, 'token': card.id }
              }).then(() => {
                $("#card-wrapper").slideUp(() => {
                  this._unloadCardView();
                  this._unbindStripeCard();

                  this._loadCardView();
                  this._bindStripeCard();
                  setTimeout(() => {
                    $("#card-wrapper").slideDown("slow")
                  }, 1500);
                });
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
     * @param {String} message
     * @override
     */
    _displayError: function (message) {
      var wizard = $(qweb.render('stripe.error', { 'msg': message || _t('Payment error') }));
      wizard.appendTo($('body')).modal({ 'keyboard': true });
    },

    enableButton: function (button) {
      $('body').unblock();
      $(button).attr('disabled', false);
      $(button).children('.fa').addClass('fa-lock');
      $(button).find('span.o_loader').remove();
    },

    disableButton: function (button) {
      $("body").block({ overlayCSS: { backgroundColor: "#000", opacity: 0, zIndex: 1050 }, message: false });
      $(button).attr('disabled', true);
      $(button).children('.fa-lock').removeClass('fa-lock');
      $(button).prepend('<span class="o_loader"><i class="fa fa-refresh fa-spin"></i>&nbsp;</span>');
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @param {Event} ev
     */
    addPmEvent: function (ev) {
      ev.preventDefault();
      this._createPaymentToken(ev);
    }

  })

  return publicWidget.registry.PaymentMethodForm
})