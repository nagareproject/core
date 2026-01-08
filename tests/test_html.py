# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    from cStringIO import StringIO as BuffIO
except ImportError:
    from io import BytesIO as BuffIO

from lxml import etree

from nagare import component, presentation
from nagare.renderers import html


def c14n(node):
    if not isinstance(node, str):
        node = node.tostring(method='xml').decode('utf-8')

    node = etree.fromstring(node).getroottree()

    buf = BuffIO()
    node.write_c14n(buf)

    return buf.getvalue()


def test_html1():
    h = html.Renderer()
    tag = h.input
    assert isinstance(tag, html.TextInput)
    assert tag.get('type') is None

    tag = h.input(type='text')
    assert isinstance(tag, html.TextInput)
    assert tag.get('type') == 'text'

    tag = h.input(type='submit')
    assert isinstance(tag, html.SubmitInput)
    assert tag.get('type') == 'submit'

    tag = h.input(type='foo')
    assert isinstance(tag, html.TextInput)
    assert tag.get('type') == 'foo'


def test_html_render_form1():
    h = html.Renderer()
    h << h.html(
        h.body(h.form(h.input(type='hidden', name='input1', value='value'), h.input(type='submit', name='submit')))
    )
    form = h.root.xpath('.//form')
    attributes = form[0].attrib
    assert attributes['method'] == 'post'
    assert attributes['accept-charset'] == 'utf-8'
    assert attributes['enctype'] == 'multipart/form-data'
    assert attributes['action'] == '?'

    assert c14n(h.root) == c14n(
        '<html><body><form enctype="multipart/form-data" method="post" accept-charset="utf-8" action="?"><input type="hidden" name="input1" value="value"/><input type="submit" name="submit"/></form></body></html>'
    )


def test_html_render_form2():
    h = html.Renderer()
    h << h.html(
        h.body(
            h.form(
                h.input(type='hidden', name='input1', value='value'),
                h.input(type='submit', name='submit'),
                {'accept-charset': 'iso-8859-15'},
            )
        )
    )
    form = h.root.xpath('.//form')
    attributes = form[0].attrib
    assert attributes['method'] == 'post'
    assert attributes['accept-charset'] == 'iso-8859-15'
    assert attributes['enctype'] == 'multipart/form-data'
    assert attributes['action'] == '?'


def test_html_render_form3():
    h = html.Renderer()
    h << h.html(
        h.body(
            h.form(h.input(type='hidden', name='input1', value='value')),
            h.form(h.input(type='string', name='input2', value='value')),
        )
    )
    forms = h.root.xpath('.//form')
    assert len(forms) == 2


def test_html_render_form4():
    h = html.Renderer()
    form = h.form(h.input(type='hidden', name='input1', value='value'), h.form(h.input(type='submit', name='submit')))
    h << h.html(h.body(form))

    forms = h.root.xpath('.//form')
    assert len(forms) == 2

    form.clean()
    forms = h.root.xpath('.//form')
    assert len(forms) == 1


def test_html_render_select1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select:
                    h << h.option(value='option1')
                    h << h.option(value='option2', selected='selected')
    options = h.root.xpath('.//option')
    assert options[0].get('selected') is None
    assert options[1].get('selected') == 'selected'


def test_html_render_select2():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select:
                    h << h.option(value='option1').selected('option2')
                    h << h.option(value='option2').selected('option2')

    options = h.root.xpath('.//option')
    assert options[0].get('selected') is None
    assert options[1].get('selected') == 'selected'


def test_html_render_select3():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select(multiple=True):
                    h << h.option(value='option1').selected(['option1', 'option3'])
                    h << h.option(value='option2').selected(['option1', 'option3'])
                    h << h.option(value='option3').selected(['option1', 'option3'])

    options = h.root.xpath('.//option')
    assert options[0].get('selected') == 'selected'
    assert options[1].get('selected') is None
    assert options[2].get('selected') == 'selected'


def test_html_render_select4():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select(multiple=True):
                    h << h.option(value='option1').selected(['option1', 'option3'])
                    h << h.option(value='option2', selected='selected').selected(['option1', 'option3'])
                    h << h.option(value='option3').selected(['option1', 'option3'])

    options = h.root.xpath('.//option')
    assert options[0].get('selected') == 'selected'
    assert options[1].get('selected') is None
    assert options[2].get('selected') == 'selected'


def test_html_render_select5():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.select(
                    [
                        h.option(value='option1').selected(['option1', 'option3']),
                        h.option(value='option2').selected(['option1', 'option3']),
                        h.option(value='option3').selected(['option1', 'option3']),
                    ],
                    multiple=True,
                )

    options = h.root.xpath('.//option')
    assert options[0].get('selected') == 'selected'
    assert options[1].get('selected') is None
    assert options[2].get('selected') == 'selected'


def test_html_render_checkbox1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.input(type='checkbox', value='option1')
                h << h.input(type='checkbox', value='option2', checked='checked')
    checkboxes = h.root.xpath('.//input[@type="checkbox"]')
    assert 'checked' not in checkboxes[0].attrib
    assert 'checked' in checkboxes[1].attrib


def test_html_render_checkbox2():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                checkbox = h.input(type='checkbox', value='option1')
                h << checkbox
                h << h.input(type='checkbox', value='option2', checked='checked')
    checkboxes = h.root.xpath('.//input[@type="checkbox"]')
    checkbox.selected(True)

    assert 'checked' in checkboxes[0].attrib
    assert 'checked' in checkboxes[1].attrib


def test_html_render_checkbox3():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                checkbox = h.input(type='checkbox', value='option1', checked='checked')
                h << checkbox
                h << h.input(type='checkbox', value='option2')
    checkboxes = h.root.xpath('.//input[@type="checkbox"]')
    checkbox.selected(False)

    assert 'checked' not in checkboxes[0].attrib


def test_html_render_radiobutton1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.input(name='radio', type='radio', value='option1')
                h << h.input(name='radio', type='radio', value='option2', checked='checked')
                h << h.input(name='radio', type='radio', value='option3')
    radios = h.root.xpath('.//input[@type="radio"]')
    assert 'checked' not in radios[0].attrib
    assert 'checked' in radios[1].attrib
    assert 'checked' not in radios[2].attrib


def test_html_render_radiobutton2():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                radio = h.input(name='radio', type='radio', value='option1')
                h << radio
                h << h.input(name='radio', type='radio', value='option2', checked='checked')
                h << h.input(name='radio', type='radio', value='option3')
    radios = h.root.xpath('.//input[@type="radio"]')
    radio.selected(True)
    assert 'checked' in radios[0].attrib
    assert 'checked' in radios[1].attrib
    assert 'checked' not in radios[2].attrib


def test_html_render_radiobutton3():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.input(name='radio', type='radio', value='option1')
                radio = h.input(name='radio', type='radio', value='option2', checked='checked')
                h << radio
                h << h.input(name='radio', type='radio', value='option3')
    radios = h.root.xpath('.//input[@type="radio"]')
    radio.selected(False)
    assert 'checked' not in radios[0].attrib
    assert 'checked' not in radios[1].attrib
    assert 'checked' not in radios[2].attrib


def test_html_render_radiobutton4():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                (
                    h
                    << h.input(name='radio', type='radio', value='value1', id='option1')
                    << h.label('option 1', for_='option1')
                    << h.br
                )
                (
                    h
                    << h.input(name='radio', type='radio', value='value1', id='option2', checked='checked')
                    << h.label('option 2', for_='option2')
                    << h.br
                )
                (
                    h
                    << h.input(name='radio', type='radio', value='value1', id='option3')
                    << h.label('option 3', for_='option3')
                    << h.br
                )
    labels = h.root.xpath('.//label')

    assert all(label.get('for') is not None for label in labels)


def test_html_render_textarea1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.textarea('test', name='textearea1', type='textarea')

    textarea = h.root.xpath('.//textarea')[0]
    assert textarea.text == 'test'


def test_html_render_submit1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name='submit1', type='submit')
                h << input

    assert isinstance(input, html.SubmitInput)


def test_html_render_password1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name='password1', type='password')
                h << input

    assert isinstance(input, html.TextInput)


def test_html_render_hidden1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name='hidden1', type='hidden')
                h << input

    assert isinstance(input, html.TextInput)


def test_html_render_file1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name='file1', type='file')
                h << input

    assert isinstance(input, html.FileInput)


def test_html_render_text1():
    h = html.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name='text1', type='text')
                h << input

    assert isinstance(input, html.TextInput)


def test_html_render_img1():
    h = html.Renderer()

    with h.html:
        with h.body:
            h << h.img(src='http://www.google.com/intl/en_ALL/images/logo.gif')

    assert c14n(h.root) == c14n(
        '<html><body><img src="http://www.google.com/intl/en_ALL/images/logo.gif"/></body></html>'
    )


def test_html_render_img2():
    h = html.Renderer(static_url='/tmp/static/')

    with h.html:
        with h.body:
            h << h.img(src='logo.gif')

    assert c14n(h.root) == c14n('<html><body><img src="/tmp/static/logo.gif"/></body></html>')


def test_html_render_img3():
    h = html.Renderer(static_url='/tmp/static/')

    with h.html:
        with h.body:
            h << h.img(src='/logo.gif')

    assert c14n(h.root) == c14n('<html><body><img src="/logo.gif"/></body></html>')


def test_html_render_a1():
    h = html.Renderer()

    with h.html:
        with h.body:
            h << h.a('google', href='http://www.google.com')

    assert c14n(h.root) == c14n('<html><body><a href="http://www.google.com">google</a></body></html>')


def test_html_render_action1():
    h = html.Renderer(static_url='/tmp/static/', component=component.Component())

    with h.html:
        with h.body:
            a = h.a().action(lambda x: None)
            h << a

    assert a.attrib['href'] is not None


def test_html_render_action2():
    h = html.Renderer(static_url='/tmp/static/', component=component.Component())

    with h.html:
        with h.body:
            a = h.a(href='http://www.google.com').action(lambda x: None)
            h << a

    assert a.attrib['href'].startswith('http://www.google.com')
    assert a.attrib['href'] != 'http://www.google.com'


def test_html_render_action3():
    h = html.Renderer(static_url='/tmp/static/', component=component.Component())

    with h.html:
        with h.body:
            i = h.img().action(lambda x: None)
            h << i

    assert i.attrib.get('src')


def test_html_render_action4():
    class C:
        pass

    @presentation.render_for(C)
    def render(self, h, *args):
        with h.body:
            a = h.a(href='logo.gif').action(lambda x: None)
            h << a

        return h.root

    div = component.Component(C()).render(html.Renderer(static_url='/tmp/static/'))

    print(div.tostring())
    assert div[0].attrib['href'].startswith('/logo.gif')


def test_html_render_action5():
    class C:
        pass

    @presentation.render_for(C)
    def render(self, h, *args):
        with h.div:
            a = h.a().action(lambda x: None)
            h << a

    div = component.Component(C()).render(html.AsyncRenderer(static_url='/tmp/static/'))

    assert div[0].attrib['href'] is not None


def test_html_render_action6():
    class C:
        pass

    @presentation.render_for(C)
    def render(self, h, *args):
        with h.div:
            a1 = h.a(href='http://www.google.com')
            h << a1
            a2 = h.a(href='http://www.google.com').action(lambda x: None)
            h << a2
            a3 = h.a(href='/foo').action(lambda x: None)
            h << a3

        return h.root

    div = component.Component(C()).render(html.AsyncRenderer(static_url='/tmp/static/'))

    assert div[0].attrib['href'] == 'http://www.google.com'
    assert 'data-nagare' not in div[0].attrib

    assert div[1].attrib['href'].startswith('http://www.google.com')
    assert div[1].attrib['href'] != 'http://www.google.com'
    assert div[1].attrib['data-nagare'] == '15'

    assert div[2].attrib['href'].startswith('/foo')
    assert div[2].attrib['href'] != '/foo'
    assert div[2].attrib['data-nagare'] == '15'


def test_html_render_action7():
    class C7:
        pass

    @presentation.render_for(C7)
    def render(self, h, *args):
        with h.html:
            with h.body:
                a = h.img(src='/a')
                h << a
                b = h.img(src='b')
                h << b
                c = h.img.action(lambda x: None)
                c = h.a.action(lambda: None)
                h << c

        return a, b, c

    h = html.AsyncRenderer(session_id=42, state_id=10, static_url='/tmp/static/')
    a, b, c = component.Component(C7()).render(h)

    url = urlparse.urlparse(a.attrib['src'])
    assert url[:4] == ('', '', '/a', '')

    url = urlparse.urlparse(b.attrib['src'])
    assert url[:4] == ('', '', '/tmp/static/b', '')

    assert 'data-nagare' in c.attrib
    url = urlparse.urlparse(c.attrib['href'])
    assert ('_s' in url[4]) and ('_c' in url[4])


def test_a():
    def url_parse(url):
        url = urlparse.urlparse(url)
        params = urlparse.parse_qs(url.query, keep_blank_values=True)

        return url.scheme, url.netloc, url.path, url.fragment, params

    h = html.Renderer()

    assert h.a('action', href='http://examples.com/a').tostring() == b'<a href="http://examples.com/a">action</a>'
    assert (
        h.a('action', href='http://examples.com/a').action(lambda: None).tostring()
        == b'<a href="http://examples.com/a">action</a>'
    )
    assert (
        h.a('action', href='http://examples.com/a#b').action(lambda: None).tostring()
        == b'<a href="http://examples.com/a#b">action</a>'
    )

    h = html.Renderer(session_id=42, state_id=10)

    assert h.a('action', href='http://examples.com/a').tostring() == b'<a href="http://examples.com/a">action</a>'

    a = h.a('action', href='http://examples.com/a').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    assert url_parse(a.get('href')) == ('http', 'examples.com', '/a', '', {})

    a = h.a('action', href='http://examples.com/a#b').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    assert url_parse(a.get('href')) == ('http', 'examples.com', '/a', 'b', {})

    a = h.a('action', href='/foo/a').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    assert url_parse(a.get('href')) == ('', '', '/foo/a', '', {})

    a = h.a('action', href='/foo/a#b').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    assert url_parse(a.get('href')) == ('', '', '/foo/a', 'b', {})

    class Component:
        url = ''

        @staticmethod
        def register_action(*args, **kw):
            return 1234

    h = html.Renderer(session_id=42, state_id=10, component=Component())

    assert h.a('action', href='http://examples.com/a').tostring() == b'<a href="http://examples.com/a">action</a>'

    a = h.a('action', href='http://examples.com/a').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    url = url_parse(a.get('href'))
    assert url[:4] == ('http', 'examples.com', '/a', '')
    assert ('_s' in url[4]) and ('_c' in url[4])

    a = h.a('action', href='http://examples.com/a#b').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    url = url_parse(a.get('href'))
    assert url[:4] == ('http', 'examples.com', '/a', 'b')
    assert ('_s' in url[4]) and ('_c' in url[4])

    a = h.a('action', href='/foo/a').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    assert url_parse(a.get('href')) == (
        '',
        '',
        '/foo/a',
        '',
        {'_s': ['42'], '_c': ['00010'], '_action1500001234': ['']},
    )

    a = h.a('action', href='/foo/a#b').action(lambda: None)
    a = h.fromstring(a.tostring(), fragment=True)[0]
    assert url_parse(a.get('href')) == (
        '',
        '',
        '/foo/a',
        'b',
        {'_s': ['42'], '_c': ['00010'], '_action1500001234': ['']},
    )


def test_area():
    def url_parse(url):
        url = urlparse.urlparse(url)
        params = urlparse.parse_qs(url.query, keep_blank_values=True)

        return url.scheme, url.netloc, url.path, url.fragment, params

    h = html.Renderer()
    assert h.area(href='http://examples.com/a').tostring() == b'<area href="http://examples.com/a">'
    assert (
        h.area(href='http://examples.com/a').action(lambda: None).tostring() == b'<area href="http://examples.com/a">'
    )
    assert (
        h.area(href='http://examples.com/a#b').action(lambda: None).tostring()
        == b'<area href="http://examples.com/a#b">'
    )

    h = html.Renderer(session_id=42, state_id=10)

    assert h.area(href='http://examples.com/a').tostring() == b'<area href="http://examples.com/a">'

    area = h.area(href='http://examples.com/a').action(lambda: None)
    area = h.fromstring(area.tostring(), fragment=True)[0]
    assert url_parse(area.get('href')) == ('http', 'examples.com', '/a', '', {})

    area = h.area(href='http://examples.com/a#b').action(lambda: None)
    area = h.fromstring(area.tostring(), fragment=True)[0]
    assert url_parse(area.get('href')) == ('http', 'examples.com', '/a', 'b', {})

    class Component:
        url = ''

        @staticmethod
        def register_action(*args, **kw):
            return 1234

    h = html.Renderer(session_id=42, state_id=10, component=Component())

    area = h.area(href='http://examples.com/a').action(lambda: None)
    area = h.fromstring(area.tostring(), fragment=True)[0]
    url = url_parse(area.get('href'))
    assert url[:4] == ('http', 'examples.com', '/a', '')
    assert ('_s' in url[4]) and ('_c' in url[4])

    area = h.area(href='http://examples.com/a#b').action(lambda: None)
    area = h.fromstring(area.tostring(), fragment=True)[0]
    url = url_parse(area.get('href'))
    assert url[:4] == ('http', 'examples.com', '/a', 'b')
    assert ('_s' in url[4]) and ('_c' in url[4])

    h = html.Renderer(static_url='/static/root')
    a = h.area(href='http://examples.com/a')
    assert a.get('href') == 'http://examples.com/a'

    a = h.area(href='/a')
    assert a.get('href') == '/a'

    a = h.area(href='a')
    assert a.get('href') == '/a'


def test_button():
    class Component:
        url = ''

        @staticmethod
        def register_action(*args, **kw):
            return 1234

    h = html.Renderer(session_id=42, state_id=10, component=Component())

    assert h.button.action(lambda: None).tostring() == b'<button name="_action1600001234"></button>'
