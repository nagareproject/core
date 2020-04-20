//--
// Copyright (c) 2008-2020, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

var [nagare_callRemote, nagare_replaceNode, nagare_loadAll] = (function () {
    "use strict;"
    var nagare_loaded_named_js = {};

    function evalCSS(name, css, attrs) {
        if(css.length) {
            var style = document.createElement("style");

            style.setAttribute("type", "text/css");
            style.setAttribute("data-nagare-css", name);
            for(var name in attrs) style.setAttribute(name, attrs[name]);

            if(style.styleSheet) style.styleSheet.cssText = css;
            else style.appendChild(document.createTextNode(css));

            document.head.appendChild(style);
        }
    }

    function evalJS(name, js, attrs) {
        if(!nagare_loaded_named_js[name]) setTimeout(js, 0);
        nagare_loaded_named_js[name] = true;
    }

    function fetchCSS(url, attrs) {
        var link = document.createElement("link");

        link.setAttribute("rel", "stylesheet");
        link.setAttribute("type", "text/css");
        link.setAttribute("href", url);
        for(var name in attrs)  link.setAttribute(name, attrs[name]);

        document.head.appendChild(link);
    }

    function fetchJS(url, attrs) {
        var script = document.createElement("script");

        script.setAttribute("type", "text/javascript");
        script.setAttribute("src", url);
        for(var name in attrs)  script.setAttribute(name, attrs[name]);

        document.head.appendChild(script);
    }

    function loadAll(named_css, css, named_js, js) {
        for(var i=0; i<named_css.length; i++) {
            var name = named_css[i][0];
            var selector = "[data-nagare-css='" + name + "']";
            if(!document.head.querySelector(selector)) evalCSS(name, named_css[i][1], named_css[i][2]);
        }

        for(var i=0; i<named_js.length; i++) {
            var name = named_js[i][0];
            var selector = "[data-nagare-js='" + name + "']";
            if(!document.head.querySelector(selector)) evalJS(name, named_js[i][1], named_js[i][2]);
            nagare_loaded_named_js[name] = true;
        }

        for(var i=0; i<css.length; i++) {
            var url = css[i][0];
            var a = document.createElement('a');
            var links = document.head.querySelectorAll("link[rel=stylesheet]");
            for(var j=0, found=false; !found && j<links.length; j++) {
                a.href = links[j].href;
                found = (a.host == window.location.host) && (a.pathname == url);
            }
            if(!found) fetchCSS(url, css[i[1]]);
        }

        for(var i=0; i<js.length; i++) {
            var url = js[i][0];
            var selector = "script[src='" + url + "']";
            if(!document.head.querySelector(selector)) fetchJS(url, css[i[1]]);
        }
    }

    function replaceNode(id, html) {
        var node = document.getElementById(id);
        var parent = node.parentNode;
        var index = Array.prototype.indexOf.call(parent.children, node);

        node.outerHTML = html;

        var scripts = parent.children[index].querySelectorAll("script");
        for(var i=0; i<scripts.length; i++) setTimeout(scripts[i].textContent, 0);

        var js = parent.children[index].querySelectorAll("script[src]");
        for(var i=0; i<js.length; i++) {
            var script = document.createElement("script");
            script.setAttribute("type", "text/javascript");
            script.setAttribute("src", js[i].getAttribute("src"));

            js[i].parentNode.replaceChild(script, js[i]);
        }
    }

    function sendRequest(url, options, params) {
        if(params && params.length) url += "&_params=" + encodeURIComponent(JSON.stringify(params));

        options.cache = "no-cache";
        options.headers = {"X-REQUESTED-WITH": "XMLHttpRequest"};

        return fetch(url, options)
            .catch(function () { throw new Error("Network error") })
            .then(function (response) {
                if(!response.ok) {
                    if(response.status == 503 && response.headers.get('location')) {
                        window.document.location = response.headers.get('location');
                    } else {
                        response.text().then(function(text) {
                            document.open()
                            document.write(text);
                            document.close()
                        })
                    }

                    response = Promise.reject('Server error');
                }

                return response;
            })
    }

    function callRemote(url) {
        return (...params) => sendRequest(url, {method: "GET"}, params).then(response => response.json());
    }

    function sendAndEval(url, options) {
        return sendRequest(url, options)
            .catch(Promise.reject)
            .then(response => response.text())
            .then(eval)
            .catch(x => undefined)
    }

    function getAndEval(url) { sendAndEval(url, {method: "GET"}) }

    function postAndEval(form, action1, action2) {
        var data = new FormData(form);

        if(action1) data.append(action1[0], action1[1]);
        if(action2) data.append(action2[0], action2[1]);

        return sendAndEval("?" , {method: "POST", body: data});
    }

    function process_click_event(event) {
        var target = event.target;
        if(!('nagare' in target.dataset)) {
            target = target.closest("a");
            if(!target || !('nagare' in target.dataset)) { return true }
        }

        switch(target.dataset['nagare']) {
            // case "1":
            //     if(event.type !== "change") { return }

            //     var value = (target.attr("type") === "checkbox") && !target.prop("checked") ? "" : target.val();
            //     getAndEval(action + "=" + encodeURIComponent(value));
            //     break;

            // case "2":
            case "5":
                var action = target.getAttribute("href");
                getAndEval(action);
                break;

            case "6":
                var action = target.getAttribute("name");
                postAndEval(event.target.form, [action, ""]);
                /*
                if(event.target.form) {
                    postAndEval(event.target.form, action);
                } else {
                    getAndEval(action);
                }
                */
                break;

            case "7":
                var action = target.getAttribute("name");

                var offset = target.getBoundingClientRect();
                var x = Math.round(event.clientX - offset.left);
                var y = Math.round(event.clientY - offset.top);

                postAndEval(event.target.form, [action + ".x", x], [action + ".y", y]);

                // getAndEval(action + ".x=" + x + ";" + action + ".y=" + y);
                break;
        }

        event.preventDefault();
        return false;
    }

    document.addEventListener('click', process_click_event, true);
    // document.addEventListener('change', process_event, true);

    return [callRemote, replaceNode, loadAll];
}());
