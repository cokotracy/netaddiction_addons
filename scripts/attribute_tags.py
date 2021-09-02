#creo la lista di attributi che voglio trasformare in tags (da inserire nell'array)
attribute_accepted = []

#inserisco i nuovi tags
for new_tag in attribute_accepted:
    request.env['product.template.tag'].create(
        {
            'name': new_tag, 
            'sequence': 10, 
            'company_id': 1, 
            'create_uid':2, 
            'write_uid':2, 
            'create_date': date.today(), 
            'write_date': date.today()
        })   

#seleziono i prodotti che contengono gli attributi desiderati
products = request.env['product.template.attribute.value'].search([('name', 'in', attribute_accepted)])

for prod in products:
    #prendo l'id dei nuovi tags creati
    tag_id = request.env['product.template.tag'].search([('name', '=', prod['name'])])
    
    #creo la relazione tra prodotto e tag
    try:
        query = f"INSERT INTO product_template_product_tag_rel(product_tmpl_id, tag_id)VALUES ({prod['product_tmpl_id']['id']}, {tag_id['id']})"
    except IndexError:
        query = ""

    request.env.cr.execute(query)