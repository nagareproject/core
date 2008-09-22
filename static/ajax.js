//--
// Copyright (c) 2008, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

var nagare_callbacks = {
	cache : false,

    success : function (o) { setTimeout(o.responseText, 0) },
    failure : function (o) {
    	                     url = o.getResponseHeader['X-Debug-URL'];
    						 if(url) {
    					         window.location = url;
    						 } else {
    							 alert('XHR Error');
    					     }
                           },
    upload  : function (o) { setTimeout(o.responseXML.firstChild.lastChild.firstChild.firstChild.data, 0) }
};

var nagare_loaded_files = new Array();

function nagare_isAlreadyLoaded(href) {
    for(var i=0; i<nagare_loaded_files.length; i++)
        if(nagare_loaded_files[i] == href)
            return true;

    return false;
}

function nagare_filterAlreadyLoaded(hrefs) {
	var notLoaded = new Array();

	for(var i=0; i<hrefs.length; i++)
		if(!nagare_isAlreadyLoaded(hrefs[i]))
			notLoaded[notLoaded.length] = hrefs[i];

	return notLoaded;
}

function nagare_loadAll(js_urls, css_urls, css, js) {
	if(css.length) nagare_loadCSS(css);

	js_urls = nagare_filterAlreadyLoaded(js_urls);
	css_urls = nagare_filterAlreadyLoaded(css_urls);

    nb = js_urls.length; // + css_urls.length;

	if(nb) {
	    function loaded() {
	        if(!this.readyState || (this.readyState == "loaded") || (this.readyState == "complete"))
	            if(!--nb) setTimeout(js, 0);
	    };

		for(var i=0; i<js_urls.length; i++) nagare_getScript(js_urls[i], loaded);
		for(var i=0; i<css_urls.length; i++) nagare_getCSS(css_urls[i], loaded);
	} else setTimeout(js, 0);
}

function nagare_getScript(href, loaded) {
    var script = document.createElement("script");
    script.setAttribute("type", "text/javascript");
    script.setAttribute("src", href);
    script.onload = script.onreadystatechange = loaded;

    nagare_loaded_files[nagare_loaded_files.length] = href;
    document.getElementsByTagName("head").item(0).appendChild(script);
}

function nagare_getCSS(href, loaded) {
    var link = document.createElement("link");
    link.setAttribute("rel", "stylesheet");
    link.setAttribute("type", "text/css");
    link.setAttribute("href", href);
    link.onload = link.onreadystatechange = loaded;

    nagare_loaded_files[nagare_loaded_files.length] = href;
    document.getElementsByTagName("head").item(0).appendChild(link);
}

function nagare_loadCSS(css) {
	var style = document.createElement('style');
	style.setAttribute("type", "text/css");
	if(style.styleSheet) style.styleSheet.cssText = css;
	else style.appendChild(document.createTextNode(css));

	document.getElementsByTagName("head").item(0).appendChild(style);
}

function nagare_getAndEval(href) {
	YAHOO.util.Connect.initHeader('ACCEPT', NAGARE_CONTENT_TYPE);
    YAHOO.util.Connect.asyncRequest("GET", href, nagare_callbacks, null);
    return false;
}

function nagare_replaceNode(id, html) {
    n = document.getElementById(id);
    e = document.createElement("div");
    e.innerHTML = html;
    n.parentNode.replaceChild(e.firstChild, n);
}

function nagare_updateNode(id, html) {
    document.getElementById(id).innerHTML = html;
}

function nagare_hasUpload(f) {
    inputs = f.getElementsByTagName("input");
    for(var i=0; i<inputs.length; i++)
        if(inputs[i].getAttribute("type") == "file")
            return true;
    return false;
}

function nagare_postAndEval(f, action) {
	YAHOO.util.Connect.initHeader('ACCEPT', NAGARE_CONTENT_TYPE);	
    YAHOO.util.Connect.setForm(f, nagare_hasUpload(f));
    YAHOO.util.Connect.asyncRequest("POST", "?_a&"+action, nagare_callbacks);
    return false;
}
