#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Internationalization service
"""

import os
import datetime

from peak.rules import when

from nagare.namespaces import xml
from nagare import serializer, ajax, local, log

try:
    from babel import core, negotiate_locale, Locale as CoreLocale
    from babel import dates, numbers, support
    import pytz

    class LazyProxy(support.LazyProxy):
        """Picklable ``babel.support.LazyProxy`` objects
        """
        @property
        def value(self):
            """Always evaluate, without any cache
            """
            return self._func(*self._args, **self._kwargs)

        def __getstate__(self):
            return (self._func, self._args, self._kwargs)

        def __setstate__(self, attrs):
            self.__init__(attrs[0], *attrs[1], **attrs[2])


    @when(xml.add_child, (xml._Tag, LazyProxy))
    def add_child(self, lazy):
        """Add a lazy string to a tag

        In:
          - ``self`` -- the tag
          - ``lazy`` -- the lazy string to add

        """
        self.add_child(lazy.value)

    @when(ajax.py2js, (LazyProxy,))
    def py2js(lazy, h):
        """Generic method to transcode a lazy string to javascript

        In:
          - ``lazy`` -- the lazy string
          - ``h`` -- the current renderer

        Return:
          - transcoded javascript
        """

        return ajax.py2js(lazy.value, h)

    @when(serializer.serialize, (LazyProxy,))
    def serialize(lazy, content_type, doctype, declaration):
        """Generic method to generate a text from a lazy string

        In:
          - ``lazy`` -- the lazy string
          - ``content_type`` -- the rendered content type
          - ``doctype`` -- the (optional) doctype
          - ``declaration`` -- is the XML declaration to be outputed ?

        Return:
          - a tuple (content_type, content)
        """
        return serializer.serialize(lazy.value, content_type, doctype, declaration)

except ImportError:

    # Dummy ``Locale`` base class and ``LazyProxy``, used when the i18n extra
    # is not installed

    class CoreLocale(object):
        def __init__(self, language, territory, script, variant):
            if not (language is territory is script is variant is None):
                log.warning('i18n extra not installed')

            self.language = None

    def LazyProxy(f, *args, **kw):
        return f(*args, **kw)

# -----------------------------------------------------------------------------

# Mac Leopard OS bug (see http://code.djangoproject.com/ticket/5846)

if os.environ.get('LC_CTYPE', '').lower() == 'utf-8':
    os.environ['LC_CTYPE'] = 'en_US.utf-8'

# -----------------------------------------------------------------------------

# Service API
# -----------

def gettext(msg, **kw):
    return get_locale().gettext(msg, **kw)

def ugettext(msg, **kw):
    return get_locale().ugettext(msg, **kw)
_ = ugettext

def ngettext(singular, plural, n, **kw):
    return get_locale().ngettext(singular, plural, n, **kw)

def ungettext(singular, plural, n, **kw):
    return get_locale().ungettext(singular, plural, n, **kw)
_N = ungettext

def lazy_gettext(msg, **kw):
    return LazyProxy(gettext, msg, **kw)

def lazy_ugettext(msg, **kw):
    return LazyProxy(ugettext, msg, **kw)
_L = lazy_ugettext

def lazy_ngettext(singular, plural, n, **kw):
    return LazyProxy(ngettext, singular, plural, n, **kw)

def lazy_ungettext(singular, plural, n, **kw):
    return LazyProxy(ungettext, singular, plural, n, **kw)
_LN = lazy_ungettext


def get_period_names():
    return get_locale().get_period_names()

def get_day_names(width='wide', context='format'):
    return get_locale().get_day_names(width, context)

def get_month_names(width='wide', context='format'):
    return get_locale().get_month_names(width, context)

def get_quarter_names(width='wide', context='format'):
    return get_locale().get_quarter_names(width, context)

def get_era_names(width='wide'):
    return get_locale().get_era_names(width)

def get_date_format(format='medium'):
    return get_locale().get_date_format(format)

def get_datetime_format(format='medium'):
    return get_locale().get_datetime_format(format)

def get_time_format(format='medium'):
    return get_locale().get_time_format(format)

def get_timezone_gmt(dt=None, width='long'):
    return get_locale().get_timezone_gmt(dt, width)

def get_timezone_location(dt_or_timezone=None):
    return get_locale().get_timezone_location(dt_or_timezone)

def get_timezone_name(dt_or_timezone=None, width='long', uncommon=False):
    return get_locale().get_timezone_name(dt_or_timezone, width, uncommon)


def get_currency_name(currency):
    return get_locale().get_currency_name(currency)

def get_currency_symbol(currency):
    return get_locale().get_currency_symbol(currency)

def get_decimal_symbol():
    return get_locale().get_decimal_symbol()

def get_plus_sign_symbol():
    return get_locale().get_plus_sign_symbol()

def get_minus_sign_symbol():
    return get_locale().get_minus_sign_symbol()

def get_exponential_symbol():
    return get_locale().get_exponential_symbol()

def get_group_symbol():
    return get_locale().get_group_symbol()

def format_number(number):
    return get_locale().format_number(number)

def format_decimal(number, format=None):
    return get_locale().format_decimal(number, format)

def format_currency(number, currency, format=None):
    return get_locale().format_currency(number, currency, format)

def format_percent(number, format=None):
    return get_locale().format_percent(number, format)

def format_scientific(number, format=None):
    return get_locale().format_scientific(number, format)

def parse_number(string):
    return get_locale().parse_number(string)

def parse_decimal(string):
    return get_locale().parse_decimal(string)


def to_timezone(dt):
    return get_locale().to_timezone(dt)

def to_utc(dt):
    return get_locale().to_utc(dt)

def format_time(t=None, format='medium'):
    return get_locale().format_time(t, format)

def format_date(d=None, format='medium'):
    return get_locale().format_date(d, format)

def format_datetime(dt=None, format='medium'):
    return get_locale().format_datetime(dt, format)

def parse_time(string):
    return get_locale().parse_time(string)

def parse_date(string):
    return get_locale().parse_date(string)

# -----------------------------------------------------------------------------

# Locale API
# ----------

_translations_cache = {}    # Already loaded translation objects

class DummyTranslation(object):
    """Identity translation
    """
    gettext = ugettext = _ = lazy_gettext = lazy_ugettext = _L = lambda self, msg: msg

    ngettext = ungettext = _N = lazy_ngettext = lazy_ungettext = _LN = lambda self, singular, plural, n: singular if n==1 else plural


class Locale(CoreLocale):
    def __init__(
                    self,
                    language=None, territory=None, script=None, variant=None,
                    dirname=None, domain=None,
                    timezone=None, default_timezone=None
                ):
        """
        A locale

        In:
          - ``language`` -- the language code (i.e 'en'),
            as described in `ISO 639 <http://ftp.ics.uci.edu/pub/ietf/http/related/iso639.txt>`_
          - ``territory`` -- the territory (country or region) code (i.e 'US'),
            as described in `ISO 3166 <http://userpage.chemie.fu-berlin.de/diverse/doc/ISO_3166.html>`_
          - ``script`` -- the script code,
            as described in `ISO 15924 <http://www.evertype.com/standards/iso15924/>`_
          - ``variant`` -- the variant code (i.e ``Locale('de', 'DE', '1901')``)

          - ``dirname`` -- the directory containing the ``MO`` files
          - ``domain`` -- the messages domain

          - ``timezone`` -- the timezone (timezone object or code)
            (i.e ``pytz.timezone('America/Los_Angeles')`` or ``America/Los_Angeles``)
          - ``default_timezone`` -- default timezone when a ``datetime`` object has
            no associated timezone. If no default timezone is given, the ``timezone``
            value is used
        """
        if language is not None:
            super(Locale, self).__init__(language, territory, script, variant)
        else:
            self.language = self.territory = self.script = self.variant = None

        self.dirname = dirname
        self.domain = domain

        if isinstance(timezone, basestring):
            timezone = pytz.timezone(timezone)
        self.tzinfo = timezone
        
        if default_timezone is None:
            default_timezone = timezone
        
        if isinstance(default_timezone, basestring):
            default_timezone = pytz.timezone(default_timezone)
        self.default_timezone = default_timezone

        self._previous_locale = None

    def _get_translation(self):
        """Load the translation object, if not already loaded
        """
        if self.language is None:
            return DummyTranslation()

        key = (self.dirname, self.language, self.domain)
        translation = _translations_cache.get(key)
        if not translation:
            translation = support.Translations.load(*key)
            _translations_cache[key] = translation

        return translation

    def gettext(self, msg, **kw):
        """Return the localized translation of a message

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the localized translation, as a 8-bit string encoded with the
            catalog's charset encoding
        """
        msg = self._get_translation().gettext(msg)
        return msg % kw if kw else msg

    def ugettext(self, msg, **kw):
        """Return the localized translation of a message

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the localized translation, as an unicode string
        """
        msg = self._get_translation().ugettext(msg)
        return msg % kw if kw else msg
    _ = ugettext

    def ngettext(self, singular, plural, n, **kw):
        """Return the plural-forms localized translation of a message

        If a translation is found, apply the ``plural`` formula to ``n``, and
        return the resulting translation. If no translation is found, return
        ``singular`` if ``n`` is 1; return ``plural`` otherwise

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the localized translation, as a 8-bit string encoded with the
            catalog's charset encoding
        """
        msg = self._get_translation().ngettext(singular, plural, n)
        return msg % kw if kw else msg

    def ungettext(self, singular, plural, n, **kw):
        """Return the plural-forms localized translation of a message

        If a translation is found, apply the ``plural`` formula to ``n``, and
        return the resulting translation. If no translation is found, return
        ``singular`` if ``n`` is 1; return ``plural`` otherwise

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the localized translation, as an unicode string
        """
        msg = self._get_translation().ungettext(singular, plural, n)
        return msg % kw if kw else msg
    _N = ungettext

    def lazy_gettext(self, msg, **kw):
        """Return the lazy localized translation of a message

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the lazy localized translation, as a 8-bit string encoded with the
            catalog's charset encoding
        """
        return LazyProxy(self.gettext, msg, **kw)

    def lazy_ugettext(self, msg, **kw):
        """Return the lazy localized translation of a message

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the lazy localized translation, as an unicode string
        """
        return LazyProxy(self.ugettext, msg, **kw)
    _L = lazy_ugettext

    def lazy_ngettext(self, singular, plural, n, **kw):
        """Return the lazy plural-forms localized translation of a message

        If a translation is found, apply the ``plural`` formula to ``n``, and
        return the resulting translation. If no translation is found, return
        ``singular`` if ``n`` is 1; return ``plural`` otherwise

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the lazy localized translation, as a 8-bit string encoded with the
            catalog's charset encoding
        """
        return LazyProxy(self.ngettext, singular, plural, n, **kw)

    def lazy_ungettext(self, singular, plural, n, **kw):
        """Return the lazy plural-forms localized translation of a message

        If a translation is found, apply the ``plural`` formula to ``n``, and
        return the resulting translation. If no translation is found, return
        ``singular`` if ``n`` is 1; return ``plural`` otherwise

        In:
          - ``msg`` -- message to translate
          - ``kw`` -- optional values to substitute into the translation

        Return:
          - the lazy localized translation, as an unicode string
        """
        return LazyProxy(self.ungettext, singular, plural, n, **kw)
    _LN = lazy_ungettext


    def get_period_names(self):
        """Return the names for day periods (AM/PM)

        >>> Locale('en', 'US').get_period_names()['am']
        u'AM'
        """
        return dates.get_period_names(self)

    def get_day_names(self, width='wide', context='format'):
        """Return the day names for the specified format

        >>> Locale('en', 'US').get_day_names('wide')[1]
        u'Tuesday'
        >>> Locale('es').get_day_names('abbreviated')[1]
        u'mar'
        >>> Locale('de', 'DE').get_day_names('narrow', context='stand-alone')[1]
        u'D'

        In:
          - ``width`` -- 'wide', 'abbreviated' or 'narrow'
          - ``context`` -- either 'format' or 'stand-alone'

        Return:
          - the day names
        """
        return dates.get_day_names(width, context, self)

    def get_month_names(self, width='wide', context='format'):
        """Return the month names for the specified format

        >>> Locale('en', 'US').get_month_names('wide')[1]
        u'January'
        >>> Locale('es').get_month_names('abbreviated')[1]
        u'ene'
        >>> Locale('de', 'DE').get_month_names('narrow', context='stand-alone')[1]
        u'J'

        In:
          - ``width`` -- 'wide', 'abbreviated' or 'narrow'
          - ``context`` -- either 'format' or 'stand-alone'

        Return:
          - the month names
        """
        return dates.get_month_names(width, context, self)

    def get_quarter_names(self, width='wide', context='format'):
        """Return the quarter names for the specified format

        >>> Locale('en', 'US').get_quarter_names('wide')[1]
        u'1st quarter'
        >>> Locale('de', 'DE').get_quarter_names('abbreviated')[1]
        u'Q1'

        In:
          - ``width`` -- 'wide', 'abbreviated' or 'narrow'
          - ``context`` -- either 'format' or 'stand-alone'

        Return:
          - the quarter names
        """
        return dates.get_quarter_names(width, context, self)

    def get_era_names(self, width='wide'):
        """Return the era names used for the specified format

        >>> Locale('en', 'US').get_era_names('wide')[1]
        u'Anno Domini'
        >>> Locale('de', 'DE').get_era_names('abbreviated')[1]
        u'n. Chr.'

        In:
          - ``width`` -- 'wide', 'abbreviated' or 'narrow'

        Return:
          - the era names
        """
        return dates.get_era_names(width, self)

    def get_date_format(self, format='medium'):
        """Return the date formatting pattern for the specified format

        >>> Locale('en', 'US').get_date_format()
        <DateTimePattern u'MMM d, yyyy'>
        >>> Locale('de', 'DE').get_date_format('full')
        <DateTimePattern u'EEEE, d. MMMM yyyy'>

        In:
          - ``format`` -- 'full', 'long', 'medium' or 'short'

        Return:
          - the date formatting pattern
        """
        return dates.get_date_format(format, self)

    def get_datetime_format(self, format='medium'):
        """Return the datetime formatting pattern for the specified format

        >>> Locale('en', 'US').get_datetime_format()
        u'{1} {0}'

        In:
          - ``format`` -- 'full', 'long', 'medium' or 'short'

        Return:
          - the datetime formatting pattern
        """
        return dates.get_datetime_format(format, self)

    def get_time_format(self, format='medium'):
        """Return the time formatting pattern for the specified format

        >>> Locale('en', 'US').get_time_format()
        <DateTimePattern u'h:mm:ss a'>
        >>> Locale('de', 'DE').get_time_format('full')
        <DateTimePattern u'HH:mm:ss v'>

        In:
          - ``format`` -- 'full', 'long', 'medium' or 'short'

        Return:
          - the time formatting pattern
        """
        return dates.get_time_format(format, self)

    def get_timezone_gmt(self, dt=None, width='long'):
        """Return the timezone associated with the given ``dt`` datetime object, formatted as string indicating the offset from GMT

        >>> dt = datetime.datetime(2007, 4, 1, 15, 30)
        >>> Locale('en').get_timezone_gmt(dt)
        u'GMT+00:00'

        In:
          - ``datetime`` -- a ``datetime`` object; if ``None``, the current
            date and time in UTC is used
          - ``width`` -- either 'long' or 'short'

        Return:
          - The timezone
        """
        return dates.get_timezone_gmt(dt, width, self)

    def get_timezone_location(self, dt_or_timezone=None):
        """Return a representation of the given timezone using "location format"

        The result depends on both the local display name of the country and the
        city assocaited with the time zone:

        >>> from pytz import timezone
        >>> tz = timezone('America/St_Johns')
        >>> Locale('de', 'DE').get_timezone_location(tz)
        u"Kanada (St. John's)"
        >>> tz = timezone('America/Mexico_City')
        >>> Locale('de', 'DE').get_timezone_location(tz)
        u'Mexiko (Mexiko-Stadt)'

        In:
          - ``dt_or_tzinfo`` -- ``datetime`` or ``tzinfo`` object that determines
            the timezone; if `None`, the current date and time in UTC is assumed

        Return:
          - the timezone representation
        """
        return dates.get_timezone_location(dt_or_timezone, self)

    def get_timezone_name(self, dt_or_timezone=None, width='long', uncommon=False):
        """Return the localized display name for the given timezone

        In:
          - ``dt_or_timezone`` -- the timezone, specified using a ``datetime`` or ``tzinfo`` object
          - ``width`` --
          - ``uncommon`` --

        >>> from pytz import timezone
        >>> dt = datetime.time(15, 30, tzinfo=timezone('America/Los_Angeles'))
        >>> Locale('en', 'US').get_timezone_name(dt)
        u'Pacific Standard Time'
        >>> Locale('en', 'US').get_timezone_name(dt, width='short')
        u'PST'

        In:
          - ``dt_or_tzinfo`` -- the ``datetime`` or ``tzinfo`` object that determines
            the timezone; if a ``tzinfo`` object is used, the resulting display
            name will be generic, i.e. independent of daylight savings time;
            if ``None``, the current date in UTC is assumed
          - ``width`` -- either 'long' or 'short'
          - ``uncommon`` -- whether even uncommon timezone abbreviations should be used

        Return:
          - the localized timezone name
        """
        return dates.get_timezone_name(dt_or_timezone, width, uncommon, self)


    def get_currency_name(self, currency):
        """Return the name used for the specified currency

        >>> Locale('en', 'US').get_currency_name('USD')
        u'US Dollar'

        In:
          - ``currency`` -- the currency code

        Return:
          - the currency name
        """
        return numbers.get_currency_name(currency, self)

    def get_currency_symbol(self, currency):
        """Return the symbol used for the specified currency

        >>> Locale('en', 'US').get_currency_symbol('USD')
        u'$'

        In:
          - ``currency`` -- the currency code

        Return:
          - the currency symbol
        """
        return numbers.get_currency_symbol(currency, self)

    def get_decimal_symbol(self):
        """Return the symbol used to separate decimal fractions

        >>> Locale('en', 'US').get_decimal_symbol()
        u'.'
        """
        return numbers.get_decimal_symbol(self)

    def get_plus_sign_symbol(self):
        """Return the plus sign symbol

        >>> Locale('en', 'US').get_plus_sign_symbol()
        u'+'
        """
        return numbers.get_plus_sign_symbol(self)

    def get_minus_sign_symbol(self):
        """Return the plus sign symbol

        >>> Locale('en', 'US').get_minus_sign_symbol()
        u'-'
        """
        return numbers.get_minus_sign_symbol(self)

    def get_exponential_symbol(self):
        """Return the symbol used to separate mantissa and exponent

        >>> Locale('en', 'US').get_exponential_symbol()
        u'E'
        """
        return numbers.get_exponential_symbol(self)

    def get_group_symbol(self):
        """Return the symbol used to separate groups of thousands

        >>> Locale('en', 'US').get_group_symbol()
        u','
        """
        return numbers.get_group_symbol(self)

    def format_number(self, number):
        """Return the given number formatted

        >>> Locale('en', 'US').format_number(1099)
        u'1,099'
        """
        return numbers.format_number(number, self)

    def format_decimal(self, number, format=None):
        """Return the given decimal number formatted

        >>> Locale('en', 'US').format_decimal(1.2345)
        u'1.234'
        >>> Locale('en', 'US').format_decimal(1.2346)
        u'1.235'
        >>> Locale('en', 'US').format_decimal(-1.2346)
        u'-1.235'
        >>> Locale('sv', 'SE').format_decimal(1.2345)
        u'1,234'
        >>> Locale('de').format_decimal(12345)
        u'12.345'
        """
        return numbers.format_decimal(number, format, self)

    def format_currency(self, number, currency, format=None):
        """Return formatted currency value

        >>> Locale('en', 'US').format_currency(1099.98, 'USD')
        u'$1,099.98'
        >>> Locale('es', 'CO').format_currency(1099.98, 'USD')
        u'US$\\xa01.099,98'
        >>> Locale('de', 'DE').format_currency(1099.98, 'EUR')
        u'1.099,98\\xa0\\u20ac'

        The pattern can also be specified explicitly:

        >>> Locale('en', 'US').format_currency(1099.98, 'EUR', u'\xa4\xa4 #,##0.00')
        u'EUR 1,099.98'
        """
        return numbers.format_currency(number, currency, format, self)

    def format_percent(self, number, format=None):
        """Return formatted percent value

        >>> Locale('en', 'US').format_percent(0.34)
        u'34%'
        >>> Locale('en', 'US').format_percent(25.1234)
        u'2,512%'
        >>> Locale('sv', 'SE').format_percent(25.1234)
        u'2\\xa0512\\xa0%'

        The format pattern can also be specified explicitly:

        >>> Locale('en', 'US').format_percent(25.1234, u'#,##0\u2030')
        u'25,123\u2030'
        """
        return numbers.format_percent(number, format, self)

    def format_scientific(self, number, format=None):
        """Return value formatted in scientific notation

        >>> Locale('en', 'US').format_scientific(10000)
        u'1E4'

        The format pattern can also be specified explicitly:

        >>> Locale('en', 'US').format_scientific(1234567, u'##0E00')
        u'1.23E06'
        """
        return numbers.format_scientific(number, format, self)

    def parse_number(self, string):
        """Parse localized number string into a long integer

        >>> Locale('en', 'US').parse_number('1,099')
        1099L
        >>> Locale('de', 'DE').parse_number('1.099')
        1099L

        When the given string cannot be parsed, an exception is raised:

        >>> Locale('de').parse_number('1.099,98')
        Traceback (most recent call last):
            ...
        NumberFormatError: '1.099,98' is not a valid number
        """
        return numbers.parse_number(string, self)

    def parse_decimal(self, string):
        """Parse localized decimal string into a float

        >>> Locale('en', 'US').parse_decimal('1,099.98')
        1099.98
        >>> Locale('de').parse_decimal('1.099,98')
        1099.98

        When the given string cannot be parsed, an exception is raised:

        >>> Locale('de').parse_decimal('2,109,998')
        Traceback (most recent call last):
            ...
        NumberFormatError: '2,109,998' is not a valid decimal number
        """
        return numbers.parse_decimal(string, self)


    def to_timezone(self, dt):
        """Return a localized datetime object

        In:
          - ``dt`` -- ``datetime`` object

        Return:
          - new localized ``datetime`` object
        """
        if not self.tzinfo:
            return dt

        if not dt.tzinfo:
            dt = dt.replace(tzinfo=self.default_timezone)

        return dt.astimezone(self.tzinfo)

    def to_utc(self, dt):
        """Return a UTC datetime object

        In:
          - ``dt`` -- ``datetime`` object

        Return:
          - new localized to UTC ``datetime`` object
        """
        if not dt.tzinfo:
            dt = (self.default_timezone or pytz.UTC).localize(dt)
            
        return dt.astimezone(pytz.UTC)

    def format_time(self, t=None, format='medium'):
        """Return a time formatted according to the given pattern

        >>> t = datetime.time(15, 30)
        >>> Locale('en', 'US').format_time(t)
        u'3:30:00 PM'
        >>> Locale('de', 'DE').format_time(t, format='short')
        u'15:30'

        If you don't want to use the locale default formats, you can specify a
        custom time pattern:

        >>> Locale('en').format_time(t, "hh 'o''clock' a")
        u"03 o'clock PM"

        In:
          - ``t`` --  ``time`` or ``datetime`` object; if `None`, the current time in UTC is used
          - ``format`` -- 'full', 'long', 'medium', or 'short', or a custom date/time pattern

        Returns:
          - the formatted time string
        """
        if isinstance(t, datetime.time):
            t = datetime.time(t.hour, t.minute, t.second)
            
        if isinstance(t, datetime.datetime):
            t = self.to_utc(t)

        return dates.format_time(t, format, locale=self, tzinfo=self.tzinfo)

    def format_date(self, d=None, format='medium'):
        """Return a date formatted according to the given pattern

        >>> d = datetime.date(2007, 04, 01)
        >>> Locale('en', 'US').format_date(d)
        u'Apr 1, 2007'
        >>> Locale('de', 'DE').format_date(d, format='full')
        u'Sonntag, 1. April 2007'

        If you don't want to use the locale default formats, you can specify a
        custom date pattern:

        >>> Locale('en').format_date(d, "EEE, MMM d, ''yy")
        u"Sun, Apr 1, '07"

        In:
          - ``d`` -- ``date`` or ``datetime`` object; if ``None``, the current date is used
          - ``format`` -- 'full', 'long', 'medium', or 'short', or a custom date/time pattern

        Return:
          - the formatted date string
        """
        return dates.format_date(d, format, self)

    def format_datetime(self, dt=None, format='medium'):
        """Return a date formatted according to the given pattern

        >>> dt = datetime.datetime(2007, 04, 01, 15, 30)
        >>> Locale('en', 'US').format_datetime(dt)
        u'Apr 1, 2007 3:30:00 PM'

        >>> from pytz import timezone
        >>> dt = datetime.datetime(2007, 04, 01, 15, 30)
        >>> Locale('fr', 'FR', timezone=timezone('Europe/Paris'), default_timezone=pytz.UTC).format_datetime(dt, 'full')
        u'dimanche 1 avril 2007 17:30:00 HEC'
        >>> Locale('en', timezone=timezone('US/Eastern'), default_timezone=pytz.UTC).format_datetime(dt, "yyyy.MM.dd G 'at' HH:mm:ss zzz")
        u'2007.04.01 AD at 11:30:00 EDT'

        In:
          - ``dt`` -- ``datetime`` object; if ``None``, the current date and time is used
          - ``format`` -- 'full', 'long', 'medium', or 'short', or a custom date/time pattern

        Return:
          - The formatted datetime string
        """
        if dt:
            dt = self.to_timezone(dt)
        return dates.format_datetime(dt, format, locale=self, tzinfo=self.tzinfo)

    def parse_time(self, string):
        """Parse a time from a string

        This function uses the time format for the locale as a hint to determine
        the order in which the time fields appear in the string.

        >>> Locale('en', 'US').parse_time('15:30:00')
        datetime.time(15, 30)

        In:
          - ``string`` -- the string containing the time

        Return:
          - a ``datetime.time`` object
        """
        return dates.parse_time(string, self)

    def parse_date(self, string):
        """Parse a date from a string

        This function uses the date format for the locale as a hint to determine
        the order in which the date fields appear in the string.

        >>> Locale('en', 'US').parse_date('4/1/04')
        datetime.date(2004, 4, 1)
        >>> Locale('de', 'DE').parse_date('01.04.2004')
        datetime.date(2004, 4, 1)

        In:
          - ``string`` -- the string containing the date

        Return:
          - a ``datetime.datetime`` object
        """
        return dates.parse_date(string, self)

    def __enter__(self):
        """Push this locale to the stack
        """
        previous_locale = get_locale()

        if self.dirname is None:
            self.dirname = previous_locale.dirname

        self._previous_locale = previous_locale
        set_locale(self)

    def __exit__(self, *args, **kw):
        """Pop this locale from the stack
        """
        set_locale(self._previous_locale)

# -----------------------------------------------------------------------------

class NegotiatedLocale(Locale):
    def __init__(
                    self,
                    request,
                    locales, default_locale=(None, None),
                    dirname=None, domain=None,
                    timezone=None, default_timezone=None
                ):
        """
        A locale with negotiated language and territory

        In:
          - ``request`` -- the HTTP request object
          - ``locales`` -- tuples of (language, territory) accepted by the application
            (i.e ``[('fr', 'FR'), ('de', 'DE'), ('en',)]``)
          - ``default_locale`` -- tuple of (language, territory) to use if the
            negociation failed

          - ``dirname`` -- the directory containing the ``MO`` files
          - ``domain`` -- the messages domain

          - ``timezone`` -- the timezone (timezone object or code)
            (i.e ``pytz.timezone('America/Los_Angeles')`` or ``America/Los_Angeles``)
          - ``default_timezone`` -- default timezone when a ``datetime`` object has
            no associated timezone. If no default timezone is given, the ``timezone``
            value is used
        """
        locale = negotiate_locale(
                                    request.accept_language,
                                    map('-'.join, locales),
                                    '-'
                                 )

        if not locale:
            (language, territory) = default_locale
        else:
            locale = core.LOCALE_ALIASES.get(locale, locale).replace('_', '-')

            if '-' not in locale:
                language = locale
                territory = None
            else:
                (language, territory) = locale.split('-')
                territory = territory.upper()

        super(NegotiatedLocale, self).__init__(
                                                language, territory,
                                                dirname=dirname, domain=domain,
                                                timezone=timezone, default_timezone=default_timezone
                                              )

# -----------------------------------------------------------------------------

def get_locale():
    return getattr(local.request, 'locale', None) or Locale()

def set_locale(locale):
    local.request.locale = locale
