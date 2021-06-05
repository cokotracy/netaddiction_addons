odoo.define('netaddiction_website.product_category_details', function (require) {
var publicWidget = require('web.public.widget');

// var qweb = core.qweb;

publicWidget.registry.websiteSaleCategory.include({
    events: {
        'click .fa-caret-down': '_onOpenClick',
        'click .fa-caret-up': '_onCloseClick',
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onOpenClick: function (ev) {
        var $fa = $(ev.currentTarget);
        $fa.parent().siblings().find('.fa-caret-down:first').click();
        $fa.parents('li').find('ul:first').show('normal');
        $fa.toggleClass('fa-caret-up fa-caret-down');
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onCloseClick: function (ev) {
        var $fa = $(ev.currentTarget);
        $fa.parent().find('ul:first').hide('normal');
        $fa.toggleClass('fa-caret-down fa-caret-up');
    },
})

});