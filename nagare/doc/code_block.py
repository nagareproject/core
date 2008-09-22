#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Extensions to ReStructuredText

Add:

  - the ``code-block`` directive that highlight a piece of core
  - the Trac roles ``:wiki:``, ``:ticket:``, ``:report:`` ... 
"""
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer

from docutils import nodes
from docutils.parsers.rst import directives

from rstdoc.traclib import roles, wiki_filter
from rstdoc.rstlib.astdoc import setDocStringFilter

DEFAULT = HtmlFormatter(noclasses=True)
VARIANTS = { 'linenos' : HtmlFormatter(noclasses=True, linenos='inline') }

def code_block_directive(name, arguments, options, content, lineno, content_offset, block_text, state, state_machine):
    """The ``code-block`` directive uses Pygment to highlight a piece of code
    
    It accepts the ``:linenos:`` option that adds line numbers
    """
    try:
        lexer = get_lexer_by_name(arguments[0])
    except ValueError:
        lexer = TextLexer()

    formatter = VARIANTS[options.keys()[0]] if options else DEFAULT
    parsed = highlight(u'\n'.join(content), lexer, formatter)
    return [nodes.raw('', parsed, format='html')]

code_block_directive.arguments = (1, 0, 1)
code_block_directive.content = 1
code_block_directive.options = dict([(key, directives.flag) for key in VARIANTS])


def register_directive():
    """Register the ``code-block`` directive"""
    try:
        import locale
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

    directives.register_directive('code-block', code_block_directive)

def tracRef(f, *path, **query):
    path = list(path)
    if path[0] in (u'browser', u'rstdoc'):
        path[1:1] = [u'trunk', u'nagare']
        
    return f(*path, **query)

def apidoc_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    i = text.find('#')
    if i == -1:
        path = text
        anchor = ''
    else:
        path = text[:i]
        anchor = text[i:]
        
    if role == 'apidoc':
        role = 'rstdoc'
        text = 'core/' + path.replace('.', '/') + '.py' + anchor 
        
    r = roles.trac_role(role, rawtext, text, lineno, inliner, options, content)

    r[0][0][0].data = path
    return r

def register_role(trac_url):
    roles.roles.register_local_role('apidoc', apidoc_role)
    roles.roles.register_local_role('wiki', apidoc_role)
        
    trac_ref = roles.tracRef(trac_url)
    roles.setTracRef(lambda *path, **query: tracRef(trac_ref, *path, **query))

    setDocStringFilter(wiki_filter.wikiFilter)
