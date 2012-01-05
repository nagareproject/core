//--
// Copyright (c) 2008-2012, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

function comet_getAndEval(id, nb, callback, poll_time) {
    var comet_callbacks = {
        cache : false,

        success : function (o) {
                                    var new_nb = o.responseText.substring(0, 9);
                                    var msg = o.responseText.substring(9);

                                    setTimeout(function () { callback(msg); }, 0);
                                    comet_getAndEval(id, (new_nb != "") ? new_nb : nb, callback, poll_time);
                               },

        failure : function (o) {
                                    if(o.status != 501) {
                                        setTimeout(function() { comet_getAndEval(id, nb, callback, poll_time); }, poll_time);
                                    }
                               }
    }

    YAHOO.util.Connect.initHeader("ACCEPT", NAGARE_CONTENT_TYPE);
    YAHOO.util.Connect.asyncRequest("GET", "?_channel="+id+"&_nb="+nb, comet_callbacks);
}
