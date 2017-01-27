openerp.netaddiction_products = function(instance, local) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    var Model = instance.web.Model;
    var Dialog = instance.web.Dialog;

    QWeb.add_template("/netaddiction_products/static/src/xml/new_fields.xml");

    /**
    questo widget è strettamente specifico per gli extra_field,
    se il cmapo non è una relazione verso "netaddiction.extradata.key.value" 
    genero un errore
    **/
    local.ExtraDataField = instance.web.form.AbstractField.extend({
        init: function() {
            this._super.apply(this, arguments);
            this.set("value", "");
        },
        events : {
            'click .extra_data_img' : 'OpenImg',
            'click .video_flv' : 'OpenVideo',
            'click .get_extra_data' : 'Get_extra_data',
        },
        start: function() {
            if(this.field.relation != 'netaddiction.extradata.key.value'){
                var options ={
                    title: "ERRORE", 
                    subtitle: '',
                    size: 'large',
                    dialogClass: '',
                    $content: QWeb.render('dialog_error_extra_data',{text : this.name + ' non può avere come widget: ' + this.widget}),
                    buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"}]
                }
                
                var dial = new Dialog(this,options);
                return dial.open()
                
            }

            /*this.on("change:effective_readonly", this, function() {
                this.display_field();
                this.render_value();
            });*/
            
            this.render_value();
            return this._super();
        },
        /*display_field: function() {
            var self = this;
            this.$el.html(QWeb.render("ExtraDataField", {widget: this}));
            if (! this.get("effective_readonly")) {
                this.$("input").change(function() {
                    self.internal_set_value(self.$("input").val());
                });
            }
        },*/
        render_value: function() {
            var object = this.field.relation;
            var field = this.field.relation_field;
            var filter = [['id','in',this.get('value')]];
            var self = this;

            var patterns = {
                protocol: '^(http(s)?(:\/\/))?(www\.)?',
                domain: '[a-zA-Z0-9-_\.]+',
                tld: '(\.[a-zA-Z0-9]{2,})',
                params: '([-a-zA-Z0-9:%_\+.~#?&//=]*)'
            }
            
            new Model(object).query().filter(filter).all().then(function(result){
                $.each(result,function(index,value){
                    if(value.key == 'images'){
                        var string = String(value.value);
                        var string = string.replace('[','');
                        var string = string.replace(']','');
                        var string = string.replace(/'/g,'')
                        var string = string.replace(/"/g,'')
                        var string = string.trim();
                        var array = string.split(',');
                        value.value2 = array;
                    }
                    if(value.key=='video_flv'){
                        var res = findUrls(value.value);
                        value.url_value = res[0];
                    }
                })
                if (self.get("effective_readonly")) {
                    self.$el.html(QWeb.render("ExtraDataField", {widget: self, result: result}));
                }
            });
            
        },
        OpenImg: function(e){
            var src = $(e.currentTarget).attr('src');
            var options ={
                title: "Immagine", 
                subtitle: '',
                size: 'large',
                dialogClass: '',
                $content: QWeb.render('dialog_error_extra_data',{img : src}),
                buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"},{text:"Cancella Immagine",classes:"btn-delete-img",click : this.delete_image}]
            }
                
            var dial = new Dialog(this,options);
            dial.open();
        },
        delete_image: function(e){
            var dialog_obj = this;
            var src = $('.big_extra_data_img').attr('src');
            var filter = [['product_id','=',this.getParent().getParent().datarecord.id],['key','=','images']];
            var object = this.getParent().field.relation;
            new Model(object).query().filter(filter).all().then(function(result){
                new Model(object).call('delete_one_extra_img',[result[0].id, src]).then(function(result){
                    if(result.result == 'ok'){
                        $('.extra_data_img').each(function(i,v){
                            if($(v).attr('src') == src){
                                $(v).remove();
                            }
                        })
                        dialog_obj.destroy();
                    }
                });
            });
        },
        Get_extra_data: function(e){
            /* devo recuperare l'id del prodotto*/
            var filter = [['id','in',this.get('value')]];
            var object = this.field.relation;
            var self = this;
            var pid = this.getParent().datarecord.id;
            var extra_data_id = this.getParent().datarecord.extra_data_id;
            if(extra_data_id==false){
                var options ={
                    title: "ERRORE", 
                    subtitle: '',
                    size: 'large',
                    dialogClass: '',
                    $content: QWeb.render('dialog_error_extra_data',{text : 'Non è settato l\'ID Scheda Extra Dati oppure lo hai settato ma non hai salvato.'}),
                    buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"}]
                }
                
                var dial = new Dialog(this,options);
                return dial.open()
            }else{
                new Model('product.product').call('extra_dati_get_data',[pid]).then(function(result){
                    console.log(result[0].values)
                    self.$el.html(QWeb.render("ExtraDataField", {widget: self, result: result[0].values}));
                    if(result[0].new_images.length > 0){
                        var options ={
                            title: "Sono state trovate nuove immagini extra: scegli quelle da aggiungere", 
                            subtitle: '',
                            size: 'large',
                            dialogClass: '',
                            $content: QWeb.render('dialog_new_images',{imgs : result[0].new_images}),
                            buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"}]
                        }
                                
                        var dial = new Dialog(this,options);
                        dial.open();

                        $(dial.$el[0]).find('.confirm_image').click(function(r){
                            var src = $(r.currentTarget).attr('src');
                            var filter = [['product_id','=',pid],['key','=','images']];
                            new Model(object).query().filter(filter).all().then(function(result){
                                new Model(object).call('add_one_extra_img',[result[0].id, src]).then(function(result){
                                    if(result.result == 'ok'){
                                        $(r.currentTarget).slideUp('slow');
                                        $('.list_image').append('<img src="'+src+'" class="extra_data_img"/>');
                                    }
                                });
                            });
                        })
                    }
                    
                });
            }
            
        }
    });

    instance.web.form.widgets.add('extra_data_field', 'instance.netaddiction_products.ExtraDataField');

    function findUrls( text )
    {
        var source = (text || '').toString();
        var urlArray = [];
        var url;
        var matchArray;

        // Regular expression to find FTP, HTTP(S) and email URLs.
        var regexToken = /(((ftp|https?):\/\/)[\-\w@:%_\+.~#?,&\/\/=]+)|((mailto:)?[_.\w-]+@([\w][\w\-]+\.)+[a-zA-Z]{2,3})/g;

        // Iterate through any URLs in the text.
        while( (matchArray = regexToken.exec( source )) !== null )
        {
            var token = matchArray[0];
            urlArray.push( token );
        }

        return urlArray;
    }
}