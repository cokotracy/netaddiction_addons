odoo.define('netaddiction_website.product_category_details', function (require) {
var publicWidget = require('web.public.widget');

// var qweb = core.qweb;


publicWidget.registry.ProductCategoryDetails = publicWidget.Widget.extend({
    selector: '#wsale_products_categories_collapse',
    events: {
            'click .fa-chevron-down': '_onClick',
        },

        start: function () {
            if (this.$el.find('.fa-chevron-down').length) {
                this.$el.find('li ul').addClass('d-none');
            }
        },
        
        _onClick: function (e) {
            $(e.target).parent().find('.nav-hierarchy').toggleClass('d-none');
        }
    
});
});