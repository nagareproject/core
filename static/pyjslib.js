StopIteration = function () {};
StopIteration.prototype = new Error();
StopIteration.name = 'StopIteration';
StopIteration.message = 'StopIteration';

KeyError = function () {};
KeyError.prototype = new Error();
KeyError.name = 'KeyError';
KeyError.message = 'KeyError';

function pyjslib_String_find(sub, start, end) {
    var pos=this.indexOf(sub, start);
    if (pyjslib_isUndefined(end)) return pos;

    if (pos + sub.length>end) return -1;
    return pos;
}

function pyjslib_String_join(data) {
    var text="";

    if (pyjslib_isArray(data)) {
        return data.join(this);
    }
    else if (pyjslib_isIteratable(data)) {
        var iter=data.__iter__();
        try {
            text+=iter.next();
            while (true) {
                var item=iter.next();
                text+=this + item;
            }
        }
        catch (e) {
            if (e != StopIteration) throw e;
        }
    }

    return text;
}

function pyjslib_String_replace(old, replace, count) {
    var do_max=false;
    var start=0;
    var new_str="";
    var pos=0;

    if (!pyjslib_isString(old)) return this.__replace(old, replace);
    if (!pyjslib_isUndefined(count)) do_max=true;

    while (start<this.length) {
        if (do_max && !count--) break;

        pos=this.indexOf(old, start);
        if (pos<0) break;

        new_str+=this.substring(start, pos) + replace;
        start=pos+old.length;
    }
    if (start<this.length) new_str+=this.substring(start);

    return new_str;
}

function pyjslib_String_split(sep, maxsplit) {
    var items=new pyjslib_List();
    var do_max=false;
    var subject=this;
    var start=0;
    var pos=0;

    if (pyjslib_isUndefined(sep) || pyjslib_isNull(sep)) {
        sep=" ";
        subject=subject.strip();
        subject=subject.replace(/\s+/g, sep);
    }
    else if (!pyjslib_isUndefined(maxsplit)) do_max=true;

    while (start<subject.length) {
        if (do_max && !maxsplit--) break;

        pos=subject.indexOf(sep, start);
        if (pos<0) break;

        items.append(subject.substring(start, pos));
        start=pos+sep.length;
    }
    if (start<subject.length) items.append(subject.substring(start));

    return items;
}

function pyjslib_String_strip(chars) {
    return this.lstrip(chars).rstrip(chars);
}

function pyjslib_String_lstrip(chars) {
    if (pyjslib_isUndefined(chars)) return this.replace(/^\s+/, "");

    return this.replace(new RegExp("^[" + chars + "]+"), "");
}

function pyjslib_String_rstrip(chars) {
    if (pyjslib_isUndefined(chars)) return this.replace(/\s+$/, "");

    return this.replace(new RegExp("[" + chars + "]+$"), "");
}

function pyjslib_String_startswith(prefix, start) {
    if (pyjslib_isUndefined(start)) start = 0;

    if (this.substring(start, prefix.length) == prefix) return true;
    return false;
}

String.prototype.upper = String.prototype.toUpperCase;
String.prototype.lower = String.prototype.toLowerCase;
String.prototype.find=pyjslib_String_find;
String.prototype.join=pyjslib_String_join;

String.prototype.__replace=String.prototype.replace;

String.prototype.replace=pyjslib_String_replace;
//String.prototype.split=pyjslib_String_split;
String.prototype.strip=pyjslib_String_strip;
String.prototype.lstrip=pyjslib_String_lstrip;
String.prototype.rstrip=pyjslib_String_rstrip;
String.prototype.startswith=pyjslib_String_startswith;

function pyjs_extend(klass, base) {
	function inherit() {}
	inherit.prototype = base.prototype;
	klass.prototype = new inherit();
	klass.prototype.constructor = klass;

	for (var i in base.prototype) {
		v = base.prototype[i];
		if (typeof v != "function") klass[i] = v;
	}
}

__pyjslib_List.prototype.__class__ = "pyjslib_List";
function pyjslib_List(data) {
    return new __pyjslib_List(data);
}
function __pyjslib_List(data) {
    if (typeof data == 'undefined') data=null;

        this.l = [];

        if (pyjslib_isArray(data)) {
            for (var i in data) {
                this.l[i]=data[i];
                }
            }
        else if (pyjslib_isIteratable(data)) {
            var iter=data.__iter__();
            var i=0;
            try {
                while (true) {
                    item=iter.next();
                    this.i[i++]=item;
                    }
                }
            catch (e) {
                if (e != StopIteration) throw e;
                }
            }

}

__pyjslib_List.prototype.append = function(item) {
    this.l[this.l.length] = item;
};
__pyjslib_List.prototype.remove = function(value) {

        var index=this.index(value);
        if (index<0) return false;
        this.l.splice(index, 1);
        return true;

};
__pyjslib_List.prototype.index = function(value, start) {
    if (typeof start == 'undefined') start=0;

        var length=this.l.length;
        for (var i=start; i<length; i++) {
            if (this.l[i]==value) {
                return i;
                }
            }
        return -1;

};
__pyjslib_List.prototype.insert = function(index, value) {
    var a = this.l; this.l=a.slice(value, index).concat(value, a.slice(index));
};
__pyjslib_List.prototype.slice = function(lower, upper) {
    return this.l.slice(lower, upper);
};
__pyjslib_List.prototype.__getitem__ = function(index) {
    return this.l[index];
};
__pyjslib_List.prototype.__setitem__ = function(index, value) {
    this.l[index]=value;
};
__pyjslib_List.prototype.__delitem__ = function(index) {
    this.l.splice(index, 1);
};
__pyjslib_List.prototype.__len__ = function() {
    return this.l.length;
};
__pyjslib_List.prototype.__contains__ = function(value) {
    return (this.index(value)>=0) ? true : false;
};
__pyjslib_List.prototype.__iter__ = function() {

        var i = 0;
        var l = this.l;

        return {
            'next': function() {
                if (i >= l.length) {
                    throw StopIteration;
                }
                return l[i++];
            }
        };

};
__pyjslib_Dict.prototype.__class__ = "pyjslib_Dict";
function pyjslib_Dict(data) {
    return new __pyjslib_Dict(data);
}
function __pyjslib_Dict(data) {
    if (typeof data == 'undefined') data=null;

        this.d = {};

        if (pyjslib_isArray(data)) {
            for (var i in data) {
                var item=data[i];
                this.d[item[0]]=item[1];
                }
            }
        else if (pyjslib_isIteratable(data)) {
            var iter=data.__iter__();
            try {
                while (true) {
                    var item=iter.next();
                    this.d[item.__getitem__(0)]=item.__getitem__(1);
                    }
                }
            catch (e) {
                if (e != StopIteration) throw e;
                }
            }
        else if (pyjslib_isObject(data)) {
            for (var key in data) {
                this.d[key]=data[key];
                }
            }

}
__pyjslib_Dict.prototype.__setitem__ = function(key, value) {
 this.d[key]=value;
};
__pyjslib_Dict.prototype.__getitem__ = function(key) {

        var value=this.d[key];
        // if (pyjslib_isUndefined(value)) throw KeyError;
        return value;

};
__pyjslib_Dict.prototype.__len__ = function() {

        var size=0;
        for (var i in this.d) size++;
        return size;

};
__pyjslib_Dict.prototype.has_key = function(key) {

        if (pyjslib_isUndefined(this.d[key])) return false;
        return true;

};
__pyjslib_Dict.prototype.__delitem__ = function(key) {
 delete this.d[key];
};
__pyjslib_Dict.prototype.__contains__ = function(key) {
    return (pyjslib_isUndefined(this.d[key])) ? false : true;
};
__pyjslib_Dict.prototype.keys = function() {

        var keys=new pyjslib_List();
        for (var key in this.d) keys.append(key);
        return keys;

};
__pyjslib_Dict.prototype.values = function() {

        var keys=new pyjslib_List();
        for (var key in this.d) keys.append(this.d[key]);
        return keys;

};
__pyjslib_Dict.prototype.__iter__ = function() {

        return this.keys().__iter__();

};
__pyjslib_Dict.prototype.iterkeys = function() {

        return this.keys().__iter__();

};
__pyjslib_Dict.prototype.itervalues = function() {

        return this.values().__iter__();

};
__pyjslib_Dict.prototype.iteritems = function() {

        var d = this.d;
        var iter=this.keys().__iter__();

        return {
            '__iter__': function() {
                return this;
            },

            'next': function() {
                while (key=iter.next()) {
                    var item=new pyjslib_List();
                    item.append(key);
                    item.append(d[key]);
                    return item;
                }
            }
        };

};
function pyjslib_range() {

    var start = 0;
    var stop = 0;
    var step = 1;

    if (arguments.length == 2) {
        start = arguments[0];
        stop = arguments[1];
        }
    else if (arguments.length == 3) {
        start = arguments[0];
        stop = arguments[1];
        step = arguments[2];
        }
    else if (arguments.length>0) stop = arguments[0];

    return {
        'next': function() {
            if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) throw StopIteration;
            var rval = start;
            start += step;
            return rval;
            },
        '__iter__': function() {
            return this;
            }
        }

}


function pyjslib_slice(object, lower, upper) {

    if (pyjslib_isString(object)) {
        if (pyjslib_isNull(upper)) upper=object.length;
        return object.substring(lower, upper);
        }
    if (pyjslib_isObject(object) && object.slice) return object.slice(lower, upper);

    return null;

}


function pyjslib_str(text) {

    return String(text);

}


function pyjslib_int(text, radix) {

    return parseInt(text, radix);

}


function pyjslib_len(object) {

    if (object==null) return 0;
    if (pyjslib_isObject(object) && object.__len__) return object.__len__();
    return object.length;

}


function pyjslib_getattr(obj, method) {

    if (!pyjslib_isObject(obj)) return null;
    if (!pyjslib_isFunction(obj[method])) return obj[method];

    return function() {
        obj[method].call(obj);
        }

}


function pyjslib_hasattr(obj, method) {

    if (!pyjslib_isObject(obj)) return false;
    if (pyjslib_isUndefined(obj[method])) return false;

    return true;

}


function pyjslib_dir(obj) {

    var properties=new pyjslib_List();
    for (property in obj) properties.append(property);
    return properties;

}


function pyjslib_filter(obj, method, sequence) {
    var items = new pyjslib_List([]);
    if ((sequence == null)) {
    var sequence = method;
    var method = obj;

        var __item = sequence.__iter__();
        try {
            while (true) {
                var item = __item.next();


    if (method(item)) {
    items.append(item);
    }

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }

    }
    else {

        var __item = sequence.__iter__();
        try {
            while (true) {
                var item = __item.next();


    if (method.call(obj, item)) {
    items.append(item);
    }

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }

    }
    return items;
}


function pyjslib_map(obj, method, sequence) {
    var items = new pyjslib_List([]);
    if ((sequence == null)) {
    var sequence = method;
    var method = obj;

        var __item = sequence.__iter__();
        try {
            while (true) {
                var item = __item.next();


    items.append(method(item));

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }

    }
    else {

        var __item = sequence.__iter__();
        try {
            while (true) {
                var item = __item.next();


    items.append(method.call(obj, item));

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }

    }
    return items;
}


function pyjslib_isObject(a) {

    return (a && typeof a == 'object') || pyjslib_isFunction(a);

}


function pyjslib_isFunction(a) {

    return typeof a == 'function';

}


function pyjslib_isString(a) {

    return typeof a == 'string';

}


function pyjslib_isNull(a) {

    return typeof a == 'object' && !a;

}


function pyjslib_isArray(a) {

    return pyjslib_isObject(a) && a.constructor == Array;

}


function pyjslib_isUndefined(a) {

    return typeof a == 'undefined';

}


function pyjslib_isIteratable(a) {

    return pyjslib_isObject(a) && a.__iter__;

}


function pyjslib_isNumber(a) {

    return typeof a == 'number' && isFinite(a);

}

