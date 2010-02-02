#!/usr/bin/env python

# Copyright 2006 James Tauber and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import compiler
from compiler import ast
import os
import copy

class Klass:

    klasses = {}

    def __init__(self, name):
        self.name = name
        self.klasses[name] = self
        self.functions = set()

    def set_base(self, base_name):
        self.base = self.klasses.get(base_name)

    def add_function(self, function_name):
        self.functions.add(function_name)


class TranslationError(Exception):
    def __init__(self, message, node):
        self.message = "line %s:\n%s\n%s" % (node.lineno, message, node)

    def __str__(self):
        return self.message


class Translator:

    def __init__(self, module_name, mod, output):

        if module_name:
            self.module_prefix = module_name + "_"
        else:
            self.module_prefix = ""
        self.imported_modules = set()
        self.top_level_functions = set()
        self.top_level_classes = set()
        self.top_level_vars = set()
        self.output = output
        self.imported_classes = {}
        self.method_imported_globals = set()

        if mod.doc:
            print >>self.output, mod.doc

        for child in mod.node:
            if isinstance(child, ast.Function):
                self.top_level_functions.add(child.name)
            elif isinstance(child, ast.Class):
                self.top_level_classes.add(child.name)

        for child in mod.node:
            if isinstance(child, ast.Function):
                self._function(child)
            elif isinstance(child, ast.Class):
                self._class(child)
            elif isinstance(child, ast.Import):
                self.imported_modules.add(child.names[0][0])
            elif isinstance(child, ast.From):
                self.imported_modules.add(child.modname)
                self._from(child)
            elif isinstance(child, ast.Discard):
                self._discard(child, None)
            elif isinstance(child, ast.Assign):
                self._assign(child, None, True)
            else:
                raise TranslationError("unsupported type (in __init__)", child)


    def _function(self, node):
        function_name = self.module_prefix + node.name
        function_args = "(" + ", ".join(node.argnames) + ")"
        print >>self.output, "function %s%s {" % (function_name, function_args)

        if node.doc:
            print >>self.output, node.doc

        else:
            for child in node.code:
                self._stmt(child, None)

        print >>self.output, "}"
        print >>self.output, "\n"


    def _return(self, node, current_klass):
        expr = self.expr(node.value, current_klass)
        if expr != "null":
            print >>self.output, "    return " + expr + ";"
        else:
            print >>self.output, "    return;"


    def _break(self, node, current_klass):
        print >>self.output, "    break;"


    def _continue(self, node, current_klass):
        print >>self.output, "    continue;"


    def _callfunc(self, v, current_klass):
        if isinstance(v.node, ast.Name):
            if v.node.name in self.top_level_functions:
                call_name = self.module_prefix + v.node.name
            elif v.node.name in self.top_level_classes:
                call_name = self.module_prefix + v.node.name
            elif self.imported_classes.has_key(v.node.name):
                call_name = self.imported_classes[v.node.name] + '_' + v.node.name
            elif v.node.name == "callable":
                call_name = "pyjslib_isFunction"
            elif v.node.name == "map":
                call_name = "pyjslib_map"
            elif v.node.name == "filter":
                call_name = "pyjslib_filter"
            elif v.node.name == "dir":
                call_name = "pyjslib_dir"
            elif v.node.name == "getattr":
                call_name = "pyjslib_getattr"
            elif v.node.name == "hasattr":
                call_name = "pyjslib_hasattr"
            elif v.node.name == "int":
                call_name = "pyjslib_int"
            elif v.node.name == "str":
                call_name = "pyjslib_str"
            elif v.node.name == "range":
                call_name = "pyjslib_range"
            elif v.node.name == "len":
                call_name = "pyjslib_len"
            else:
                call_name = v.node.name
            call_args = []
        elif isinstance(v.node, ast.Getattr):
            attr_name = v.node.attrname
            if isinstance(v.node.expr, ast.Name):
                call_name = self._name2(v.node.expr, current_klass, attr_name)
                call_args = []
            elif isinstance(v.node.expr, ast.Getattr):
                call_name = self._getattr2(v.node.expr, current_klass, attr_name)
                call_args = []
            elif isinstance(v.node.expr, ast.CallFunc):
                call_name = self._callfunc(v.node.expr, current_klass) + "." + v.node.attrname
                call_args = []
            elif isinstance(v.node.expr, ast.Subscript):
                call_name = self._subscript(v.node.expr, current_klass) + "." + v.node.attrname
                call_args = []
            else:
                raise TranslationError("unsupported type (in _callfunc)", v.node.expr)
        else:
            raise TranslationError("unsupported type (in _callfunc)", v.node)

        for ch4 in v.args:
            arg = self.expr(ch4, current_klass)
            call_args.append(arg)

        return call_name + "(" + ", ".join(call_args) + ")"


    def _getattr(self, v):
        attr_name = v.attrname
        if isinstance(v.expr, ast.Name):
            obj = v.expr.name
            if obj == "self":
                obj = "this"
            elif self.imported_classes.has_key(obj):
                obj = "__" + self.imported_classes[obj] + '_' + obj
            elif obj in self.imported_modules:
                return obj + "_" + attr_name
            elif obj[0] == obj[0].upper():
                obj = "__" + self.module_prefix + obj
            return obj + "." + attr_name
        elif isinstance(v.expr, ast.Getattr):
            return self._getattr(v.expr) + "." + attr_name
        elif isinstance(v.expr, ast.Subscript):
            return self._subscript(v.expr, self.module_prefix) + "." + attr_name
        elif isinstance(v.expr, ast.CallFunc):
            return self._callfunc(v.expr, self.module_prefix) + "." + attr_name
        else:
            raise TranslationError("unsupported type (in _getattr)", v.expr)


    def _name(self, v):
        if v.name == "True":
            return "true"
        elif v.name == "False":
            return "false"
        elif v.name == "None":
            return "null"
        elif v.name == "self":
            return "this"
        elif v.name in self.top_level_classes:
            return self.module_prefix + v.name # @@@ should this be prefixed __?
        elif v.name in self.method_imported_globals:
            return self.module_prefix + v.name
        else:
            return v.name


    def _name2(self, v, current_klass, attr_name):
        obj = v.name

        if obj in self.method_imported_globals:
            call_name = self.module_prefix + obj + "." + attr_name
        elif self.imported_classes.has_key(obj):
            attr_str = ""
            if attr_name != "__init__":
                attr_str = ".prototype." + attr_name
            call_name = "__" + self.imported_classes[obj] + '_' + obj + attr_str + ".call"
        elif obj in self.imported_modules:
            call_name = obj + "_" + attr_name
        elif obj[0] == obj[0].upper():
            if attr_name == "__init__":
                call_name = "__" + self.module_prefix + obj + ".call"
            else:
                call_name = "__" + self.module_prefix + obj + ".prototype." + attr_name + ".call"
        else:
            if obj == "self":
                obj = "this"
            call_name = obj + "." + attr_name

        return call_name


    def _getattr2(self, v, current_klass, attr_name):
        if isinstance(v.expr, ast.Name):
            obj = v.expr.name
            if obj in self.imported_modules:
                if attr_name == "__init__":
                    call_name = "__" + obj + "_" + v.attrname + ".call"
                else:
                    call_name = "__" + obj + "_" + v.attrname + "." + attr_name + ".call"
            else:
                if obj == "self":
                    obj = "this"
                call_name = obj + "." + v.attrname + "." + attr_name
        elif isinstance(v.expr, ast.Getattr):
            call_name = self._getattr2(v.expr, current_klass, v.attrname + "." + attr_name)
        else:
            raise TranslationError("unsupport type (in _getattr2)", v.expr)

        return call_name


    def _class(self, node):

        class_name = self.module_prefix + node.name
        current_klass = Klass(node.name)

        for child in node.code:
            if isinstance(child, ast.Function):
                current_klass.add_function(child.name)

        if len(node.bases) == 0:
            base_class = ""
        elif len(node.bases) == 1:
            if isinstance(node.bases[0], ast.Name):
                if self.imported_classes.has_key(node.bases[0].name):
                    base_class = self.imported_classes[node.bases[0].name] + '_' + node.bases[0].name
                else:
                    base_class = self.module_prefix + node.bases[0].name
            elif isinstance(node.bases[0], ast.Getattr):
                base_class = self._name(node.bases[0].expr) + "_" + node.bases[0].attrname
            else:
                raise TranslationError("unsupported type (in _class)", node.bases[0])

            print >>self.output, "pyjs_extend(__" + class_name + ", __" + base_class + ");"
            current_klass.set_base(base_class)
        else:
            raise TranslationError("more than one base (in _class)", node)

        print >>self.output, "__" + class_name + '.prototype.__class__ = "' + class_name + '";'

        if "__init__" not in current_klass.functions:
            print >>self.output, "function " + class_name + "() {"
            print >>self.output, "    return new __" + class_name + "();"
            print >>self.output, "}"
            print >>self.output, "function __" + class_name + "() {"
            # call superconstructor
            if base_class:
                print >>self.output, "    __" + base_class + ".call(this);"
            print >>self.output, "}"

        for child in node.code:
            if isinstance(child, ast.Pass):
                pass
            elif isinstance(child, ast.Function):
                self._method(child, current_klass, class_name)
            elif isinstance(child, ast.Assign):
                self.classattr(child, current_klass)
            else:
                raise TranslationError("unsupported type (in _class)", child)

    def classattr(self, node, current_klass):
        self._assign(node, current_klass, True)

    def _method(self, node, current_klass, class_name):
        # reset global var scope
        self.method_imported_globals = set()

        arg_names = node.argnames

        if len(arg_names) == 0:
            raise TranslationError("first arg not 'self' (in _method)", node)
        if arg_names[0] != "self":
            raise TranslationError("first arg not 'self' (in _method)", node)
        function_args = "(" + ", ".join(arg_names[1:]) + ")"

        if node.name == "__init__":
            print >>self.output, "function " + class_name + function_args + " {"
            print >>self.output, "    return new __" + class_name + function_args + ";"
            print >>self.output, "}"
            print >>self.output, "function __" + class_name + function_args + " {"
        else:
            print >>self.output, "__" + class_name + ".prototype." + node.name + " = function" + function_args + " {"

        # default arguments
        if len(node.defaults):
            default_pos = len(arg_names) - len(node.defaults)
            for default_node in node.defaults:
                if isinstance(default_node, ast.Const):
                    default_value = self._const(default_node)
                elif isinstance(default_node, ast.Name):
                    default_value = self._name(default_node)
                else:
                    raise TranslationError("unsupported type (in _method)", default_node)

                default_name = arg_names[default_pos]
                default_pos += 1
                print >>self.output, "    if (typeof %s == 'undefined') %s=%s;" % (default_name, default_name, default_value)

        if node.doc:
            print >>self.output, node.doc

        else:
            for child in node.code:
                self._stmt(child, current_klass)

        if node.name == "__init__":
            print >>self.output, "}"
        else:
            print >>self.output, "};"


    def _stmt(self, node, current_klass):
        if isinstance(node, ast.Return):
            self._return(node, current_klass)
        elif isinstance(node, ast.Break):
            self._break(node, current_klass)
        elif isinstance(node, ast.Continue):
            self._continue(node, current_klass)
        elif isinstance(node, ast.Assign):
            self._assign(node, current_klass)
        elif isinstance(node, ast.AugAssign):
            self._augassign(node, current_klass)
        elif isinstance(node, ast.Discard):
            self._discard(node, current_klass)
        elif isinstance(node, ast.If):
            self._if(node, current_klass)
        elif isinstance(node, ast.For):
            self._for(node, current_klass)
        elif isinstance(node, ast.While):
            self._while(node, current_klass)
        elif isinstance(node, ast.Subscript):
            self._subscript_stmt(node, current_klass)
        elif isinstance(node, ast.Global):
            self._global(node, current_klass)
        elif isinstance(node, ast.Pass):
            pass
        else:
            raise TranslationError("unsupported type (in _stmt)", node)


    def _augassign(self, node, current_klass):
        v = node.node
        if isinstance(v, ast.Getattr):
            lhs = self._getattr(v)
        else:
            lhs = self._name(node.node)
        op = node.op
        rhs = self.expr(node.expr, current_klass)
        print >>self.output, "    " + lhs + " " + op + " " + rhs + ";"


    def _assign(self, node, current_klass, top_level = False):
        if len(node.nodes) != 1:
            raise TranslationError("not single node (in _assign)", node)
        v = node.nodes[0]
        if isinstance(v, ast.AssAttr):
            attr_name = v.attrname
            if isinstance(v.expr, ast.Name):
                obj = v.expr.name

                if obj in self.top_level_classes:
                    lhs = "__" + self.module_prefix + obj + "." + attr_name
                    lhs += " = __" + self.module_prefix + obj + ".prototype." + attr_name
                elif self.imported_classes.has_key(obj):
                    lhs = "__" + self.imported_classes[obj] + '_' + obj + "." + attr_name
                    lhs += " = __" + self.imported_classes[obj] + '_' +  obj + ".prototype." + attr_name
                else:
                    if obj == "self":
                        obj = "this"
                    lhs = "    " + obj + "." + attr_name

            elif isinstance(v.expr, ast.Getattr):
                lhs = "    " + self._getattr(v)
            elif isinstance(v.expr, ast.Subscript):
                lhs = "    " + self._subscript(v.expr, current_klass) + "." + attr_name
            else:
                raise TranslationError("unsupported type (in _assign)", v.expr)
            if v.flags == "OP_ASSIGN":
                op = "="
            else:
                raise TranslationError("unsupported flag (in _assign)", v)

        elif isinstance(v, ast.AssName):
            if top_level:
                if current_klass:
                    lhs = "__" + self.module_prefix + current_klass.name + "." + v.name
                    lhs += " = __" + self.module_prefix + current_klass.name + ".prototype." + v.name
                else:
                    self.top_level_vars.add(v.name)
                    lhs = "var " + self.module_prefix + v.name
            else:
                if v.name in self.method_imported_globals:
                    lhs = "    " + self.module_prefix + v.name
                else:
                    lhs = "    var " + v.name
            if v.flags == "OP_ASSIGN":
                op = "="
            else:
                raise TranslationError("unsupported flag (in _assign)", v)
        elif isinstance(v, ast.Subscript):
            if v.flags == "OP_ASSIGN":
                obj = self.expr(v.expr, current_klass)
                if len(v.subs) != 1:
                    raise TranslationError("must have one sub (in _assign)", v)
                idx = self.expr(v.subs[0], current_klass)
                value = self.expr(node.expr, current_klass)
                print >>self.output, "    " + obj + ".__setitem__(" + idx + ", " + value + ");"
                return
            else:
                raise TranslationError("unsupported flag (in _assign)", v)
        else:
            raise TranslationError("unsupported type (in _assign)", v)


        rhs = self.expr(node.expr, current_klass)
        print >>self.output, lhs + " " + op + " " + rhs + ";"


    def _discard(self, node, current_klass):
        if isinstance(node.expr, ast.CallFunc):
            expr = self._callfunc(node.expr, current_klass)
            print >>self.output, "    " + expr + ";"
        elif isinstance(node.expr, ast.Const):
            print >>self.output, node.expr.value
        else:
            raise TranslationError("unsupported type (in _discard)", node.expr)


    def _if(self, node, current_klass):
        for i in range(len(node.tests)):
            test, consequence = node.tests[i]
            if i == 0:
                keyword = "if"
            else:
                keyword = "else if"

            self._if_test(keyword, test, consequence, current_klass)

        if node.else_:
            keyword = "else"
            test = None
            consequence = node.else_

            self._if_test(keyword, test, consequence, current_klass)


    def _if_test(self, keyword, test, consequence, current_klass):

        if test:
            expr = self.expr(test, current_klass)

            print >>self.output, "    " + keyword + " (" + expr + ") {"
        else:
            print >>self.output, "    " + keyword + " {"

        if isinstance(consequence, ast.Stmt):
            for child in consequence.nodes:
                self._stmt(child, current_klass)
        else:
            raise TranslationError("unsupported type (in _if_test)", consequence)

        print >>self.output, "    }"


    def _from(self, node):
        for name in node.names:
            self.imported_classes[name[0]] = node.modname


    def _compare(self, node, current_klass):
        lhs = self.expr(node.expr, current_klass)

        if len(node.ops) != 1:
            raise TranslationError("only one ops supported (in _compare)", node)

        op = node.ops[0][0]
        rhs_node = node.ops[0][1]
        rhs = self.expr(rhs_node, current_klass)

        if op == "in":
            return rhs + ".__contains__(" + lhs + ")"
        elif op == "not in":
            return "!" + rhs + ".__contains__(" + lhs + ")"

        return "(" + lhs + " " + op + " " + rhs + ")"


    def _not(self, node, current_klass):
        expr = self.expr(node.expr, current_klass)

        return "!(" + expr + ")"

    def _or(self, node, current_klass):
        expr = "("+") || (".join([self.expr(child, current_klass) for child in node.nodes])+")"
        return expr

    def _and(self, node, current_klass):
        expr = "("+") && (".join([self.expr(child, current_klass) for child in node.nodes])+")"
        return expr

    def _for(self, node, current_klass):
        assign_name = ""
        assign_tuple = ""

        # based on Bob Ippolito's Iteration in Javascript code
        if isinstance(node.assign, ast.AssName):
            assign_name = node.assign.name
            if node.assign.flags == "OP_ASSIGN":
                op = "="
        elif isinstance(node.assign, ast.AssTuple):
            op = "="
            i = 0
            for child in node.assign:
                child_name = child.name
                if assign_name == "":
                    assign_name = "temp_" + child_name

                assign_tuple += """
                var %(child_name)s %(op)s %(assign_name)s.__getitem__(%(i)i);
                """ % locals()
                i += 1
        else:
            raise TranslationError("unsupported type (in _for)", node.assign)

        if isinstance(node.list, ast.Name):
            list_expr = self._name(node.list)
        elif isinstance(node.list, ast.Getattr):
            list_expr = self._getattr(node.list)
        elif isinstance(node.list, ast.CallFunc):
            list_expr = self._callfunc(node.list, current_klass)
        else:
            raise TranslationError("unsupported type (in _for)", node.list)

        lhs = "var " + assign_name
        iterator_name = "__" + assign_name

        print >>self.output, """
        var %(iterator_name)s = %(list_expr)s.__iter__();
        try {
            while (true) {
                %(lhs)s %(op)s %(iterator_name)s.next();
                %(assign_tuple)s
        """ % locals()
        for node in node.body.nodes:
            self._stmt(node, current_klass)
        print >>self.output, """
            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        """ % locals()


    def _while(self, node, current_klass):
        test = self.expr(node.test, current_klass)
        print >>self.output, "    while (" + test + ") {"
        if isinstance(node.body, ast.Stmt):
            for child in node.body.nodes:
                self._stmt(child, current_klass)
        else:
            raise TranslationError("unsupported type (in _while)", node.body)
        print >>self.output, "    }"


    def _const(self, node):
        if isinstance(node.value, int):
            return str(node.value)
        elif isinstance(node.value, float):
            return str(node.value)
        elif isinstance(node.value, str):
            return '"' + node.value + '"'
        elif node.value is None:
            return "null"
        else:
            raise TranslationError("unsupported type (in _const)", node)

    def _unarysub(self, node, current_klass):
        return "-" + self.expr(node.expr, current_klass)

    def _add(self, node, current_klass):
        return self.expr(node.left, current_klass) + " + " + self.expr(node.right, current_klass)

    def _sub(self, node, current_klass):
        return self.expr(node.left, current_klass) + " - " + self.expr(node.right, current_klass)

    def _div(self, node, current_klass):
        return self.expr(node.left, current_klass) + " / " + self.expr(node.right, current_klass)

    def _mul(self, node, current_klass):
        return self.expr(node.left, current_klass) + " * " + self.expr(node.right, current_klass)

    def _mod(self, node, current_klass):
        return self.expr(node.left, current_klass) + " % " + self.expr(node.right, current_klass)

    def _invert(self, node, current_klass):
        return "("+"~" + self.expr(node.expr, current_klass)+")"

    def _bitand(self, node, current_klass):
        return "("+" & ".join([self.expr(child, current_klass) for child in node.nodes])+")"

    def _bitor(self, node, current_klass):
        return "("+" | ".join([self.expr(child, current_klass) for child in node.nodes])+")"

    def _subscript(self, node, current_klass):
        if node.flags == "OP_APPLY":
            if len(node.subs) == 1:
                return self.expr(node.expr, current_klass) + ".__getitem__(" + self.expr(node.subs[0], current_klass) + ")"
            else:
                raise TranslationError("must have one sub (in _subscript)", node)
        else:
            raise TranslationError("unsupported flag (in _subscript)", node)

    def _subscript_stmt(self, node, current_klass):
        if node.flags == "OP_DELETE":
            print >>self.output, "    " + self.expr(node.expr, current_klass) + ".__delitem__(" + self.expr(node.subs[0], current_klass) + ");"
        else:
            raise TranslationError("unsupported flag (in _subscript)", node)

    def _list(self, node, current_klass):
        return "new pyjslib_List([" + ", ".join([self.expr(x, current_klass) for x in node.nodes]) + "])"

    def _dict(self, node, current_klass):
        items = []
        for x in node.items:
            key = self.expr(x[0], current_klass)
            value = self.expr(x[1], current_klass)
            items.append("[" + key + ", " + value + "]")
        return "new pyjslib_Dict([" + ", ".join(items) + "])"

    def _tuple(self, node, current_klass):
        return "new pyjslib_Tuple([" + ", ".join([self.expr(x, current_klass) for x in node.nodes]) + "])"

    def _slice(self, node, current_klass):
        if node.flags == "OP_APPLY":
            lower = "null"
            upper = "null"
            if node.lower != None:
                lower = self.expr(node.lower, current_klass)
            if node.upper != None:
                upper = self.expr(node.upper, current_klass)
            return  "pyjslib_slice(" + self.expr(node.expr, current_klass) + ", " + lower + ", " + upper + ")"
        else:
            raise TranslationError("unsupported flag (in _slice)", node)

    def _global(self, node, current_klass):
        for name in node.names:
            self.method_imported_globals.add(name)

    def expr(self, node, current_klass):
        if isinstance(node, ast.Const):
            return self._const(node)
        # @@@ not sure if the parentheses should be here or in individual operator functions - JKT
        elif isinstance(node, ast.Mul):
            return " ( " + self._mul(node, current_klass) + " ) "
        elif isinstance(node, ast.Add):
            return " ( " + self._add(node, current_klass) + " ) "
        elif isinstance(node, ast.Sub):
            return " ( " + self._sub(node, current_klass) + " ) "
        elif isinstance(node, ast.Div):
            return " ( " + self._div(node, current_klass) + " ) "
        elif isinstance(node, ast.Mod):
            return self._mod(node, current_klass)
        elif isinstance(node, ast.UnarySub):
            return self._unarysub(node, current_klass)
        elif isinstance(node, ast.Not):
            return self._not(node, current_klass)
        elif isinstance(node, ast.Or):
            return self._or(node, current_klass)
        elif isinstance(node, ast.And):
            return self._and(node, current_klass)
        elif isinstance(node, ast.Invert):
            return self._invert(node, current_klass)
        elif isinstance(node, ast.Bitand):
            return self._bitand(node, current_klass)
        elif isinstance(node, ast.Bitor):
            return self._bitor(node, current_klass)
        elif isinstance(node, ast.Compare):
            return self._compare(node, current_klass)
        elif isinstance(node, ast.CallFunc):
            return self._callfunc(node, current_klass)
        elif isinstance(node, ast.Name):
            return self._name(node)
        elif isinstance(node, ast.Subscript):
            return self._subscript(node, current_klass)
        elif isinstance(node, ast.Getattr):
            return self._getattr(node)
        elif isinstance(node, ast.List):
            return self._list(node, current_klass)
        elif isinstance(node, ast.Dict):
            return self._dict(node, current_klass)
        elif isinstance(node, ast.Tuple):
            return self._tuple(node, current_klass)
        elif isinstance(node, ast.Slice):
            return self._slice(node, current_klass)
        else:
            raise TranslationError("unsupported type (in expr)", node)



import cStringIO

def translate(file_name, module_name):
    output = cStringIO.StringIO()
    mod = compiler.parseFile(file_name)
    t = Translator(module_name, mod, output)
    return output.getvalue()


class PlatformParser:
    def __init__(self, platform_dir = ""):
        self.platform_dir = platform_dir
        self.parse_cache = {}
        self.platform = ""

    def setPlatform(self, platform):
        self.platform = platform

    def parseModule(self, module_name, file_name):
        if self.parse_cache.has_key(file_name):
            mod = self.parse_cache[file_name]
        else:
            print "Importing " + module_name
            mod = compiler.parseFile(file_name)
            self.parse_cache[file_name] = mod

        platform_file_name = self.generatePlatformFilename(file_name)
        if self.platform and os.path.isfile(platform_file_name):
            mod = copy.deepcopy(mod)
            mod_override = compiler.parseFile(platform_file_name)
            self.merge(mod, mod_override)

        return mod

    def generatePlatformFilename(self, file_name):
        (module_name, extension) = os.path.splitext(os.path.basename(file_name))
        platform_file_name = module_name + self.platform + extension

        return os.path.join(os.path.dirname(file_name), self.platform_dir, platform_file_name)

    def merge(self, tree1, tree2):
        for child in tree2.node:
            if isinstance(child, ast.Function):
                self.replaceFunction(tree1, child.name, child)
            elif isinstance(child, ast.Class):
                self.replaceClassMethods(tree1, child.name, child)

        return tree1

    def replaceFunction(self, tree, function_name, function_node):
        # find function to replace
        for child in tree.node:
            if isinstance(child, ast.Function) and child.name == function_name:
                self.copyFunction(child, function_node)
                return
        raise TranslationError("function not found: " + function_name, function_node)

    def replaceClassMethods(self, tree, class_name, class_node):
        # find class to replace
        old_class_node = None
        for child in tree.node:
            if isinstance(child, ast.Class) and child.name == class_name:
                old_class_node = child
                break

        if not old_class_node:
            raise TranslationError("class not found: " + class_name, class_node)

        # replace methods
        for function_node in class_node.code:
            if isinstance(function_node, ast.Function):
                found = False
                for child in old_class_node.code:
                    if isinstance(child, ast.Function) and child.name == function_node.name:
                        found = True
                        self.copyFunction(child, function_node)
                        break

                if not found:
                    raise TranslationError("class method not found: " + class_name + "." + function_node.name, function_node)

    def copyFunction(self, target, source):
        target.code = source.code
        target.argnames = source.argnames
        target.defaults = source.defaults
        target.doc = source.doc


class AppTranslator:

    def __init__(self, library_dirs=["../library"], parser=None):
        self.extension = ".py"

        self.library_modules = []
        self.library_dirs = library_dirs

        if not parser:
            self.parser = PlatformParser()
        else:
            self.parser = parser

    def findFile(self, file_name):
        if os.path.isfile(file_name):
            return file_name

        for library_dir in self.library_dirs:
            full_file_name = os.path.join(os.path.dirname(__file__), library_dir, file_name)
            if os.path.isfile(full_file_name):
                return full_file_name

        raise Exception("file not found: " + file_name)

    def translate(self, module_name, is_app=True):

        if module_name not in self.library_modules:
            self.library_modules.append(module_name)

        file_name = self.findFile(module_name + self.extension)

        if is_app:
            module_name_translated = ""
        else:
            module_name_translated = module_name

        output = cStringIO.StringIO()

        mod = self.parser.parseModule(module_name, file_name)
        t = Translator(module_name_translated, mod, output)
        module_str = output.getvalue()

        imported_modules_str = ""
        for module in t.imported_modules:
            if module not in self.library_modules:
                imported_modules_str += self.translate(module, False)

        return imported_modules_str + module_str

    def translateLibraries(self, library_modules=[]):
        self.library_modules = library_modules

        imported_modules_str = ""
        for library in self.library_modules:
            imported_modules_str += self.translate(library, False)

        return imported_modules_str


if __name__ == "__main__":
    import sys
    file_name = sys.argv[1]
    if len(sys.argv) > 2:
        module_name = sys.argv[2]
    else:
        module_name = None
    print translate(file_name, module_name),
