odoo.define('website_all_in_one.product_brand_label', function(require){
        
        $('.label_remove').on('click', '.js_delete_product', function(e) {
            e.preventDefault();
            $(this).closest('tr').trigger('change');
        });
});

