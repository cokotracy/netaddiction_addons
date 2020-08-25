odoo.define('netaddiction_website.product_category_details', function (require) {
var publicWidget = require('web.public.widget');

// var qweb = core.qweb;


publicWidget.registry.ProductCategoryDetails = publicWidget.Widget.extend({
    selector: '.product_category_details',
    events: {
            'click .fa-chevron-down': '_onClick',
        },
        
    _onClick: function () {
        this.$el.find('ul').toggleClass('d-none');
    }
    
});
});