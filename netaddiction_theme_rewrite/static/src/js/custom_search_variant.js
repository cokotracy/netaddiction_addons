odoo.define('netaddiction_theme_rewrite.productSearchBar', function (require) {
  'use strict';
  var publicWidget = require('web.public.widget');
  var productsSearchBar = publicWidget.registry.productsSearchBar

  productsSearchBar.include({
    xmlDependencies: productsSearchBar.prototype.xmlDependencies.concat(
      ['/website_sale/static/src/xml/website_sale_utils.xml']
    )
  })

  return productsSearchBar
})