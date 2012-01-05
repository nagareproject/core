//--
// Copyright (c) 2008-2012, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

// ----------------------------------------------------------------------------
// Requests

var nagare_callbacks = {
    cache : false,

    success : function (o) { setTimeout(o.responseText, 0) },
    failure : function (o) {
                            var url = o.getResponseHeader["X-Debug-URL"];
                            if(url) {
                                        window.location = url;
                                    } else {
                                        alert("XHR Error");
                                    }
                           },
    upload  : function (o) {
                            if(o.responseText.substring(0, 5) != "URL: ") {
                                var js = "";
                                var js_fragments = o.responseXML.lastChild.lastChild.firstChild;
                                for(var i=0; i<js_fragments.childNodes.length; i++)
                                    js += js_fragments.childNodes[i].data;
                                setTimeout(js, 0);
                            } else {
                                alert("XHR Error");
                            }
                           }
};

function nagare_getAndEval(href) {
    YAHOO.util.Connect.initHeader("ACCEPT", NAGARE_CONTENT_TYPE);
    YAHOO.util.Connect.asyncRequest("GET", href, nagare_callbacks);
    return false;
}

function nagare_hasUpload(f) {
    var inputs = f.getElementsByTagName("input");
    for(var i=0; i<inputs.length; i++)
        if(inputs[i].getAttribute("type") == "file")
            return true;
    return false;
}

function nagare_postAndEval(f, action) {
    YAHOO.util.Connect.initHeader("ACCEPT", NAGARE_CONTENT_TYPE);
    YAHOO.util.Connect.setForm(f, nagare_hasUpload(f));
    YAHOO.util.Connect.asyncRequest("POST", "?_a&"+action, nagare_callbacks);
    return false;
}

function nagare_imageInputSubmit(event, button, action) {
    var evt = event || window.event;
    var xy = YAHOO.util.Dom.getXY(button);
    return nagare_postAndEval(button.form, action+".x="+(evt.clientX-xy[0])+"&"+action+".y="+(evt.clientY-xy[1]));
}

// ----------------------------------------------------------------------------
// Responses

var nagare_loaded_named_css = {}
var nagare_loaded_named_js = {}

function nagare_filter(items, filter) {
    var not_in_filter = new Array();

    for(var i=0; i<items.length; i++)
        if(!filter[items[i][0]])
            not_in_filter[not_in_filter.length] = items[i];

    return not_in_filter;
}


function nagare_itemgetter(l, x) {
    var r = new Array();
    for(var i=0; i<l.length; i++) r[r.length] = l[i][x];
    return r
}

function nagare_loadCSS(css, attrs) {
    if(css.length) {
        var style = document.createElement("style");

        style.setAttribute("type", "text/css");
        for (var name in attrs) {
            style.setAttribute(name, attrs[name]);
        }

        if(style.styleSheet) style.styleSheet.cssText = css;
        else style.appendChild(document.createTextNode(css));

        document.getElementsByTagName("head")[0].appendChild(style);
    }
}

function nagare_loadAll(named_css, anon_css, css_urls, named_js, anon_js, js_urls) {
    var named_css = nagare_filter(named_css, nagare_loaded_named_css)
    for(var i=0; i<named_css.length; i++) {
        nagare_loadCSS(named_css[i][1], named_css[i][2]);
        nagare_loaded_named_css[named_css[i][0]] = 1;
    }

    nagare_loadCSS(anon_css, {});

    var named_js = nagare_filter(named_js, nagare_loaded_named_js)
    for(var i=0; i<named_js.length; i++) {
        setTimeout(named_js[i][1], 0);
        nagare_loaded_named_js[named_js[i][0]] = 1;
    }

    setTimeout(anon_js, 0);

    YAHOO.util.Get.css(nagare_itemgetter(css_urls, 0), { onSuccess: function (o) {
        YAHOO.util.Get.script(nagare_itemgetter(js_urls, 0), { onSuccess: function(o) { o.purge() } })
    } });
}

//----------------------------------------------------------------------------
// DOM manipulation

function nagare_replaceNode(id, html) {
    var n = document.getElementById(id);
    if(n && html) {
        var e = document.createElement("div");
        e.innerHTML = html;
        n.parentNode.replaceChild(e.firstChild, n);

    }
}

function nagare_updateNode(id, html) {
    var n = document.getElementById(id)
    if(n && html) n.innerHTML = html;
}

function get_field_value(field) {
    return escape(field.type=='checkbox' && !field.checked ? "" : field.value);
}
