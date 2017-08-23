$("#oe_main_menu_navbar").addClass("hidden-xs");

$("#search_button").click(function(){
    $("#search_text").fadeToggle();
    $("#my_stores").fadeToggle();
});

function product_tab()
{
    tab_page_id = "#" + document.getElementById("product_tab").value;
    $(".product_tab").removeClass("active");
    $(".product_tab").removeClass("in");
    $(tab_page_id).addClass("active");
    $(tab_page_id).addClass("in");
}

function minus(product_id)
{
    value = parseInt(document.getElementById(product_id).value)
    if(value > 0){
        value --;
        document.getElementById(product_id).value = value;
    }
}

function plus(product_id)
{
    value = parseInt(document.getElementById(product_id).value) + 1;
    document.getElementById(product_id).value = value;
}

$(".table_cell").hide();
function toggle_cell(product_id)
{
    var product = "product_cell_" + product_id;
    $("#" + product).slideToggle("slow");
}

/* send rep.order */
function send_rep_order(order_id, res_partner, product_id, ){
    quantity = res_partner + "_qty_" +product_id;
    discount = res_partner + "_discount_" +product_id;
    document.getElementById(quantity).value
    openerp.jsonRpc("/crm/send/repord", 'call', {
        'order_id': order_id,
        'product_id': product_id,
        'product_uom_qty': document.getElementById(quantity).value,
        'discount': document.getElementById(discount).value
    });
}

/* add product */
function add_product(res_partner, product_id){
    openerp.jsonRpc("/crm/add/product", 'call', {
        'res_partner': res_partner,
        'product_id': product_id,
    }).done(function(data){
        if(data == "added"){
            // $("#ksp_" + product_id + "_product").css({"background-color": "#fff"});
            $("#ksp_" + product_id + "_plus").addClass("hidden");
            $("#ksp_" + product_id + "_minus").removeClass("hidden");
            $("#ksp_" + product_id + "_minus").addClass("col-xs-3");
            $("#ksp_" + product_id + "_minus").addClass("col-sm-3");
            $("#ksp_" + product_id + "_minus").addClass("col-md-3");
            $("#ksp_" + product_id + "_minus").addClass("col-lg-3");
        }
    });
}

/* remove product */
function remove_product(res_partner, product_id){
    openerp.jsonRpc("/crm/remove/product", 'call', {
        'res_partner': res_partner,
        'product_id': product_id,
    }).done(function(data){
        if(data == "removed"){
            // $("#ksp_" + product_id + "_product").css({"background-color": "#f4f4f4"});
            $("#ksp_" + product_id + "_minus").addClass("hidden");
            $("#ksp_" + product_id + "_plus").removeClass("hidden");
            $("#ksp_" + product_id + "_plus").addClass("col-xs-3");
            $("#ksp_" + product_id + "_plus").addClass("col-sm-3");
            $("#ksp_" + product_id + "_plus").addClass("col-md-3");
            $("#ksp_" + product_id + "_plus").addClass("col-lg-3");
        }
    });
}

/* change rep order type */
function change_order_type(order){
    order_type = document.getElementById("order_type_" + order).value;
    openerp.jsonRpc("/crm/repord/type", 'call', {
        'order': order,
        'order_type': order_type,
    }).done(function(data){
        if(data != "order_type_changed"){
            window.alert('Something went wrong when changing order type');
        }
        else {
            if(order_type == "order" || order_type == "3rd_party") {
                $("tr.oe-extra-product").hide();
            } else {
                $("tr.oe-extra-product").show();
            };
        }
    });
}

/* change campaign */
function change_campaign(order){
    campaign_id = document.getElementById("campaign_" + order).value;
    openerp.jsonRpc("/crm/repord/campaign", 'call', {
        'order': order,
        'campaign_id': campaign_id,
    }).done(function(data){
        if(data != "campaign_changed"){
            window.alert('Something went wrong when changing campaign');
        }
    });
}

/* change delivery date */
function change_delivery_date(order){
    delivery_date = document.getElementById("delivery_date_" + order).value;
    openerp.jsonRpc("/crm/repord/deliverydate", 'call', {
        'order': order,
        'date_order': delivery_date,
    }).done(function(data){
        if(data != "delivery_date_changed"){
            window.alert('Something went wrong when changing delivery date');
        }
    });
}

/* get updated rep order */
function get_updated_order(order){
    openerp.jsonRpc("/crm/" + order + "/updated_order", 'call', {
    }).done(function(data){
        $("#updated_order_info_" + order).html('<p class="text-center"><b>' + data['order'].name + '</b></p><div class="col-md-6"><p><b>Kund: </b>' + data['order'].partner + '</p><p><b>Datum:</b> ' + data['order'].date_order + '</p></div><div class="col-md-6"><p><b>Typ:</b> ' + data['order'].order_type + '</p><p><b>3:e part:</b> ' + (data['order'].third_party_supplier != '' ? data['order'].third_party_supplier : '') +'</p></div>');
        var line_content = "";
        $.each(data['order_line'], function(key, info) {
            var content = '<tr><td><span class="text-muted">[' + data['order_line'][key]['default_code'] + ']</span> ' + data['order_line'][key]['product'] + '</td><td>' + data['order_line'][key]['product_uom_qty'] + '</td><td>' + data['order_line'][key]['product_uom'] + '</td><td>' + data['order_line'][key]['discount'] + '</td></tr>';
            line_content += content;
        });
        $("#updated_order_line_" + order).html(line_content);
    });
}

/* confirm rep order */
function order_confirm(order){
    var confirm_validate = "";
    send_mail = $("#send_mail_" + order).is(":checked");
    openerp.jsonRpc("/crm/repord/confirm", 'call', {
        'order': order,
        'send_mail': send_mail
    }).done(function(data){
        $('#confirm_modal_' + order).modal('hide');
        if(data == "no_email"){
            window.alert("Butiken har ingen epost!");
        }
        else if(data == "repord_confirmed"){
            $("#send_mail_" + order).addClass("hidden");
            $("#confirm_" + order).addClass("hidden");
            confirm_validate = "Reporden har skickats!";
            $("#create_new_" + order).removeClass("hidden");
        }
        else if(data == "validation_fail"){
            window.alert("Fel i ordern! Fel typ, eller så har du blandat Lerøy- och Paolos-produkter.");
        }
        else if(data == "no_lines"){
            window.alert("Ordern har inga rader!");
        }
        $("#confirm_message_" + order).text(confirm_validate);
        console.log("validation fail");
    });
}

/* show meeting input */
function show_create_meeting(){
    $("#show_meeting_button_group").addClass("hidden");
    $("#meeting_button_group").removeClass("hidden");
}

/* hide meeting input */
function hide_create_meeting(){
    $("#meeting_button_group").addClass("hidden");
    $("#show_meeting_button_group").removeClass("hidden");
}

/* create meeting */
function create_meeting(partner){
    if ($("input[name=meeting_content]").val() != "") {
        openerp.jsonRpc("/crm/meeting/create", 'call', {
            'partner_id': partner,
            'meeting_content': $("input[name=meeting_content]").val(),
            'meeting_date': $("input[name=meeting_date]").val(),
            'meeting_time_start': $("input[name=meeting_time_start]").val(),
            'meeting_time_end': $("input[name=meeting_time_end]").val(),
        }).done(function(data){
            if(data == "meeting_created"){
                $("#meeting_table").load(document.URL + " #meeting_table");
                $("#meeting_content").val("");
                $("#meeting_date").val("");
                $("#meeting_time_start").val("");
                $("#meeting_time_end").val("");
                $("#meeting_button_group").addClass("hidden");
                $("#show_meeting_button_group").removeClass("hidden");
            }
        });
    }
}

/* show note input */
function show_create_note(){
    $("#show_note_button_group").addClass("hidden");
    $("#note_button_group").removeClass("hidden");
}

/* hide note input */
function hide_create_note(){
    $("#note_button_group").addClass("hidden");
    $("#show_note_button_group").removeClass("hidden");
}

/* create todo list */
function create_note(partner){
    if ($("input[name=memo]").val() != "") {
        openerp.jsonRpc("/crm/todo/create", 'call', {
            'partner': partner,
            'memo': $("input[name=memo]").val(),
        }).done(function(data){
            if(data == "note_created"){
                $("#todo_table").load(document.URL + " #todo_table");
                $("#note_memo").val("");
                $("#note_button_group").addClass("hidden");
                $("#show_note_button_group").removeClass("hidden");
            }
        });
    }
}

/* change todo list to done */
function todo_done(note_id){
    openerp.jsonRpc("/crm/todo/done", 'call', {
        'note_id': note_id,
    }).done(function(data){
        if(data == "note_done"){
            $("#note_" + note_id + "_text").css({
                "text-decoration": "line-through",
                "color": "#f00;",
                "margin-top": 10 + "px;"
            });
            $("#todo_table").load(document.URL + " #todo_table");
        }
    });
}

/* Register presentation */
function register_presentation(partner_id, categ, id){
    if (confirm("Vill du registrera denna presentation?") == true) {
        openerp.jsonRpc("/crm/presentation/done", 'call', {
            'partner_id': partner_id,
            'categ': categ,
        }).done(function(data){
            if(data == "presentation_done"){
                $("#" + partner_id + id).css({"opacity": "0.4", "cursor": "not-allowed"});
                $("#" + partner_id + id).removeAttr("onclick");
            }
        });
    }
}

/* change status of meeting */
function customer_visited(partner_id){
    if (confirm("Är du säker?") == true) {
        button = partner_id + "_meeting";
        openerp.jsonRpc("/crm/" + partner_id + "/meeting/visited", 'call', {
            'partner': partner_id,
        }).done(function(data){
            if(data == "meeting_done"){
                $("#" + button).addClass("hidden");
            }
        });
    }
}

/* submit file automatically */
/* option 1 */
$("#upload_file").live("change", function(){
    $("#photo_form").submit();
});

/* option 2 */
function upload_photo(){
    $("#photo_form").submit();
}

/* delete image */
function delete_image(attachment_id){
    if (confirm("Vill du radera den bilden?") == true) {
        openerp.jsonRpc("/crm/delete/image", 'call', {
            'attachment_id': attachment_id,
        }).done(function(data){
            if(data == "image_deleted"){
                $("#image_div").load(document.URL +  " #image_div");
            }
        });
    }
}

/* store info update */
function store_info_update(partner){
    openerp.jsonRpc("/crm/" + partner_id + "/store_info_update", 'call', {
        'partner': partner,
    });
}

/* refresh the page. keep current tabs */
function refresh_page(){
    var href = window.location.pathname;
    href = href + '?category=' + $('li.active > a.brand_tab').data('category-id');
    href = href + '&active_tab=' + $('li.active > a.oe_paolos_tab_picker').data('tab-id');
    window.location.href = href;
}
