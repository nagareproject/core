# Encoding: utf-8

# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import decimal
import datetime
import unittest

import pytz

from nagare import local, i18n


class Translation(dict):
    def gettext(self, msg):
        return self[msg]

    def ugettext(self, msg):
        return unicode(self.gettext(msg))

    def ngettext(self, singular, plural, n):
        return self[singular if n == 1 else plural]

    def ungettext(self, singular, plural, n):
        return unicode(self.ngettext(singular, plural, n))


class Locale(i18n.Locale):
    def _get_translation(self, domain=None):
        return Translation({
            'hello': 'bonjour',
            'Holidays': 'Vacances %(year)d',
            'horse': 'cheval',
            'horses': 'chevaux'
        })


# -----------------------------------------------------------------------------

class TestTranslations(unittest.TestCase):
    def setUp(self):
        local.request = local.Process()
        i18n.set_locale(Locale('fr', 'FR'))

    def test_gettext(self):
        s = i18n.gettext('hello')
        self.assertTrue(isinstance(s, str))
        self.assertEqual(s, 'bonjour')

    def test_gettext_params(self):
        s = i18n.gettext('Holidays', year=2010)
        self.assertIsInstance(s, str)
        self.assertEqual(s, 'Vacances 2010')

    def test_gettext_unknown(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))
        s = i18n.gettext('unknown')
        self.assertIsInstance(s, str)
        self.assertEqual(s, 'unknown')

    def test_ugettext(self):
        s = i18n.ugettext('hello')
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'bonjour')

    def test_ugettext_params(self):
        s = i18n.ugettext('Holidays', year=2010)
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'Vacances 2010')

    def test_ugettext_unknown(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))
        s = i18n.ugettext('unknown')
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'unknown')

    def test__(self):
        s = i18n._('hello')
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'bonjour')

    def test_ngettext_singular(self):
        s = i18n.ngettext('horse', 'horses', 1)
        self.assertIsInstance(s, str)
        self.assertEqual(s, 'cheval')

    def test_ngettext_plural(self):
        s = i18n.ngettext('horse', 'horses', 3)
        self.assertIsInstance(s, str)
        self.assertEqual(s, 'chevaux')

    def test_ngettext_singular_unknown(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))
        s = i18n.ngettext('unknown1', 'unknown2', 1)
        self.assertIsInstance(s, str)
        self.assertEqual(s, 'unknown1')

    def test_ngettext_plural_unknown(self):
        i18n.set_locale(i18n.Locale('fr_FR'))
        s = i18n.ngettext('unknown1', 'unknown2', 3)
        self.assertIsInstance(s, str)
        self.assertEqual(s, 'unknown2')

    def test_ungettext_singular(self):
        s = i18n.ungettext('horse', 'horses', 1)
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'cheval')

    def test_ungettext_plural(self):
        s = i18n.ungettext('horse', 'horses', 3)
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'chevaux')

    def test_ungettext_singular_unknown(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))
        s = i18n.ungettext('unknown1', 'unknown2', 1)
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'unknown1')

    def test_ungettext_plural_unknown(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))
        s = i18n.ungettext('unknown1', 'unknown2', 3)
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'unknown2')

    def test_N_singular(self):
        s = i18n._N('horse', 'horses', 1)
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'cheval')

    def test_N_plural(self):
        s = i18n._N('horse', 'horses', 3)
        self.assertIsInstance(s, unicode)
        self.assertEqual(s, u'chevaux')

    def test_lazy_gettext(self):
        s = i18n.lazy_gettext('hello')
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, str)
        self.assertEqual(s, 'bonjour')

    def test_lazy_gettext_params(self):
        s = i18n.lazy_gettext('Holidays', year=2010)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, str)
        self.assertEqual(s, 'Vacances 2010')

    def test_lazy_ugettext(self):
        s = i18n.lazy_ugettext('hello')
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, unicode)
        self.assertEqual(s, u'bonjour')

    def test_lazy_ugettext_params(self):
        s = i18n.lazy_ugettext('Holidays', year=2010)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, unicode)
        self.assertEqual(s, u'Vacances 2010')

    def test_L_ugettext(self):
        s = i18n._L('hello')
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, unicode)
        self.assertEqual(s, u'bonjour')

    def test_lazy_ngettext_singular(self):
        s = i18n.lazy_ngettext('horse', 'horses', 1)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, str)
        self.assertEqual(s, 'cheval')

    def test_lazy_ngettext_plural(self):
        s = i18n.lazy_ngettext('horse', 'horses', 3)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, str)
        self.assertEqual(s, 'chevaux')

    def test_lazy_ungettext_singular(self):
        s = i18n.lazy_ungettext('horse', 'horses', 1)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, unicode)
        self.assertEqual(s, u'cheval')

    def test_lazy_ungettext_plural(self):
        s = i18n.lazy_ungettext('horse', 'horses', 3)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, unicode)
        self.assertEqual(s, u'chevaux')

    def test_LN_ungettext_singular(self):
        s = i18n._LN('horse', 'horses', 1)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, unicode)
        self.assertEqual(s, u'cheval')

    def test_LN_ungettext_plural(self):
        s = i18n._LN('horse', 'horses', 3)
        self.assertEqual(s.__class__.__name__, 'LazyProxy')
        self.assertIsInstance(s.value, unicode)
        self.assertEqual(s, u'chevaux')


# -----------------------------------------------------------------------------

class TestDateNames(unittest.TestCase):
    def setUp(self):
        local.request = local.Process()
        i18n.set_locale(i18n.Locale('fr', 'FR'))

    def test_get_period_names(self):
        self.assertEqual(i18n.get_period_names(), {
            'afternoon1': u'après-midi',
            'am': u'AM',
            'evening1': u'soir',
            'midnight': u'minuit',
            'morning1': u'matin',
            'night1': u'nuit',
            'noon': u'midi',
            'pm': u'PM'
        })

    def test_get_day_names(self):
        self.assertEqual(i18n.get_day_names(), {0: u'lundi', 1: u'mardi', 2: u'mercredi', 3: u'jeudi', 4: u'vendredi', 5: u'samedi', 6: u'dimanche'})
        self.assertEqual(i18n.get_day_names(width='wide'), {0: u'lundi', 1: u'mardi', 2: u'mercredi', 3: u'jeudi', 4: u'vendredi', 5: u'samedi', 6: u'dimanche'})
        self.assertEqual(i18n.get_day_names(width='abbreviated'), {0: u'lun.', 1: u'mar.', 2: u'mer.', 3: u'jeu.', 4: u'ven.', 5: u'sam.', 6: u'dim.'})
        self.assertEqual(i18n.get_day_names(width='narrow'), {0: u'L', 1: u'M', 2: u'M', 3: u'J', 4: u'V', 5: u'S', 6: u'D'})

    def test_get_month_names(self):
        self.assertEqual(i18n.get_month_names(), {1: u'janvier', 2: u'février', 3: u'mars', 4: u'avril', 5: u'mai', 6: u'juin', 7: u'juillet', 8: u'août', 9: u'septembre', 10: u'octobre', 11: u'novembre', 12: u'décembre'})
        self.assertEqual(i18n.get_month_names(width='wide'), {1: u'janvier', 2: u'février', 3: u'mars', 4: u'avril', 5: u'mai', 6: u'juin', 7: u'juillet', 8: u'août', 9: u'septembre', 10: u'octobre', 11: u'novembre', 12: u'décembre'})
        self.assertEqual(i18n.get_month_names(width='abbreviated'), {1: u'janv.', 2: u'févr.', 3: u'mars', 4: u'avr.', 5: u'mai', 6: u'juin', 7: u'juil.', 8: u'août', 9: u'sept.', 10: u'oct.', 11: u'nov.', 12: u'déc.'})
        self.assertEqual(i18n.get_month_names(width='narrow'), {1: u'J', 2: u'F', 3: u'M', 4: u'A', 5: u'M', 6: u'J', 7: u'J', 8: u'A', 9: u'S', 10: u'O', 11: u'N', 12: u'D'})

    def test_get_quarter_names(self):
        self.assertEqual(i18n.get_quarter_names(), {1: u'1er trimestre', 2: u'2e trimestre', 3: u'3e trimestre', 4: u'4e trimestre'})
        self.assertEqual(i18n.get_quarter_names(width='wide'), {1: u'1er trimestre', 2: u'2e trimestre', 3: u'3e trimestre', 4: u'4e trimestre'})
        self.assertEqual(i18n.get_quarter_names(width='abbreviated'), {1: u'T1', 2: u'T2', 3: u'T3', 4: u'T4'})
        self.assertEqual(i18n.get_quarter_names(width='narrow'), {1: u'1', 2: u'2', 3: u'3', 4: u'4'})

    def test_get_era_names(self):
        i18n.set_locale(i18n.Locale('en', 'US'))

        self.assertEqual(i18n.get_era_names(), {0: u'Before Christ', 1: u'Anno Domini'})
        self.assertEqual(i18n.get_era_names(width='wide'), {0: u'Before Christ', 1: u'Anno Domini'})
        self.assertEqual(i18n.get_era_names(width='abbreviated'), {0: u'BC', 1: u'AD'})
        self.assertEqual(i18n.get_era_names(width='narrow'), {0: u'B', 1: u'A'})

    def test_get_date_format(self):
        self.assertEqual(i18n.get_date_format(format='full').pattern, 'EEEE d MMMM y')
        self.assertEqual(i18n.get_date_format(format='long').pattern, 'd MMMM y')
        self.assertEqual(i18n.get_date_format().pattern, 'd MMM y')
        self.assertEqual(i18n.get_date_format(format='medium').pattern, 'd MMM y')
        self.assertEqual(i18n.get_date_format(format='short').pattern, 'dd/MM/y')

    def test_get_datetime_format(self):
        self.assertEqual(i18n.get_datetime_format(format='full'), u"{1} 'à' {0}")
        self.assertEqual(i18n.get_datetime_format(format='long'), u"{1} 'à' {0}")
        self.assertEqual(i18n.get_datetime_format(), u"{1} 'à' {0}")
        self.assertEqual(i18n.get_datetime_format(format='medium'), u"{1} 'à' {0}")
        self.assertEqual(i18n.get_datetime_format(format='short'), u'{1} {0}')

    def test_get_time_format(self):
        self.assertEqual(i18n.get_time_format(format='full').pattern, 'HH:mm:ss zzzz')
        self.assertEqual(i18n.get_time_format(format='long').pattern, 'HH:mm:ss z')
        self.assertEqual(i18n.get_time_format().pattern, 'HH:mm:ss')
        self.assertEqual(i18n.get_time_format(format='medium').pattern, 'HH:mm:ss')
        self.assertEqual(i18n.get_time_format(format='short').pattern, 'HH:mm')

    def test_get_timezone_gmt(self):
        utc_date = datetime.datetime(2007, 4, 1, 15, 30)

        tz = pytz.timezone('Pacific/Pitcairn')
        d = Locale('en', timezone=tz).to_timezone(utc_date)

        self.assertEqual(i18n.get_timezone_gmt(d, width='long'), u'UTC-08:00')
        self.assertEqual(i18n.get_timezone_gmt(d), u'UTC-08:00')
        self.assertEqual(i18n.get_timezone_gmt(d, width='short'), '-0800')

        i18n.set_locale(i18n.Locale('en', 'US'))

        self.assertEqual(i18n.get_timezone_gmt(d, width='long'), u'GMT-08:00')
        self.assertEqual(i18n.get_timezone_gmt(d), u'GMT-08:00')
        self.assertEqual(i18n.get_timezone_gmt(d, width='short'), '-0800')

    def test_get_timezone_location(self):
        tz = pytz.timezone('Africa/Bamako')
        self.assertEqual(i18n.get_timezone_location(tz), 'Mali')

    def test_get_timezone_name(self):
        utc_date = datetime.datetime(2007, 4, 1, 15, 30)

        tz = pytz.timezone('Pacific/Pitcairn')
        d = Locale('en', timezone=tz).to_timezone(utc_date)

        self.assertEqual(i18n.get_timezone_name(d), u'heure des îles Pitcairn')
        self.assertEqual(i18n.get_timezone_name(d, width='long'), u'heure des îles Pitcairn')
        self.assertEqual(i18n.get_timezone_name(d, width='short'), '-0800')


# -----------------------------------------------------------------------------

class TestFormats(unittest.TestCase):
    def setUp(self):
        local.request = local.Process()
        i18n.set_locale(i18n.Locale('fr', 'FR'))

    def test_get_currency_name(self):
        self.assertEqual(i18n.get_currency_name('USD'), u'dollar des États-Unis')

    def test_get_currency_symbol(self):
        self.assertEqual(i18n.get_currency_symbol('USD'), '$US')

    def test_get_decimal_symbol(self):
        self.assertEqual(i18n.get_decimal_symbol(), ',')

    def test_get_plus_sign_symbol(self):
        self.assertEqual(i18n.get_plus_sign_symbol(), '+')

    def test_get_minus_sign_symbol(self):
        self.assertEqual(i18n.get_minus_sign_symbol(), '-')

    def test_get_exponential_symbol(self):
        self.assertEqual(i18n.get_exponential_symbol(), 'E')

    def test_get_group_symbol(self):
        self.assertEqual(i18n.get_group_symbol(), u'\N{NO-BREAK SPACE}')

    def test_format_number(self):
        self.assertEqual(i18n.format_number(1099), u'1\N{NO-BREAK SPACE}099')

    def test_format_decimal(self):
        self.assertEqual(i18n.format_decimal(1236.1236), u'1\N{NO-BREAK SPACE}236,124')

    def test_format_currency(self):
        self.assertEqual(i18n.format_currency(1236.126, 'EUR'), u'1\N{NO-BREAK SPACE}236,13\N{NO-BREAK SPACE}\N{EURO SIGN}')

    def test_format_percent(self):
        self.assertEqual(i18n.format_percent(24.1234), u'2\N{NO-BREAK SPACE}412\N{NO-BREAK SPACE}%')

    def test_format_scientific(self):
        self.assertEqual(i18n.format_scientific(10000), '1E4')
        self.assertEqual(i18n.format_scientific(1234567, u'##0E00'), '1.23E06')

    def test_parse_number(self):
        self.assertEqual(i18n.parse_number(u'1\N{NO-BREAK SPACE}099'), 1099)

    def test_parse_decimal(self):
        self.assertEqual(i18n.parse_decimal(u'1\N{NO-BREAK SPACE}099,1234'), decimal.Decimal('1099.1234'))


# -----------------------------------------------------------------------------

class TestTimezones(unittest.TestCase):
    def test_to_timezone_no_timezone_datetime(self):
        d1 = datetime.datetime(2007, 4, 1, 15, 30)

        i18n.set_locale(i18n.Locale('fr', 'FR'))
        d2 = i18n.to_timezone(d1)
        self.assertIsNone(d2.tzinfo)
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Pacific/Pitcairn'))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'Pacific/Pitcairn')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Pacific/Pitcairn', default_timezone=pytz.UTC))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'Pacific/Pitcairn')
        self.assertEqual(d2.strftime('%H:%M'), '07:30')

    def test_to_timezone_utc_datetime(self):
        d1 = datetime.datetime(2007, 4, 1, 15, 30, tzinfo=pytz.UTC)

        i18n.set_locale(i18n.Locale('fr', 'FR'))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Pacific/Pitcairn'))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'Pacific/Pitcairn')
        self.assertEqual(d2.strftime('%H:%M'), '07:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Pacific/Pitcairn', default_timezone=pytz.UTC))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'Pacific/Pitcairn')
        self.assertEqual(d2.strftime('%H:%M'), '07:30')

    def test_to_timezone_local_datetime(self):
        tz = pytz.timezone('Pacific/Pitcairn')
        d1 = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))

        i18n.set_locale(i18n.Locale('fr', 'FR'))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'Pacific/Pitcairn')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'Africa/Niamey')
        self.assertEqual(d2.strftime('%H:%M'), '00:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey', default_timezone=pytz.UTC))
        d2 = i18n.to_timezone(d1)
        self.assertEqual(str(d2.tzinfo), 'Africa/Niamey')
        self.assertEqual(d2.strftime('%H:%M'), '00:30')

    def test_to_utc_no_timezone_datetime(self):
        d1 = datetime.datetime(2007, 4, 1, 15, 30)

        i18n.set_locale(i18n.Locale('fr', 'FR'))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '14:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey', default_timezone=pytz.UTC))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

    def test_to_utc_utc_datetime(self):
        d1 = datetime.datetime(2007, 4, 1, 15, 30, tzinfo=pytz.UTC)

        i18n.set_locale(i18n.Locale('fr', 'FR'))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey', default_timezone=pytz.UTC))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '15:30')

    def test_to_utc_local_datetime(self):
        tz = pytz.timezone('Pacific/Pitcairn')
        d1 = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))

        i18n.set_locale(i18n.Locale('fr', 'FR'))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '23:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '23:30')

        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey', default_timezone=pytz.UTC))
        d2 = i18n.to_utc(d1)
        self.assertEqual(str(d2.tzinfo), 'UTC')
        self.assertEqual(d2.strftime('%H:%M'), '23:30')

    def test_format_time_time_fr1(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))

        t = datetime.time(15, 30)

        self.assertEqual(i18n.format_time(t, format='full'), '15:30:00 UTC+00:00')
        self.assertEqual(i18n.format_time(t, format='long'), '15:30:00 +0000')
        self.assertEqual(i18n.format_time(t, format='medium'), '15:30:00')
        self.assertEqual(i18n.format_time(t), '15:30:00')
        self.assertEqual(i18n.format_time(t, format='short'), '15:30')

    def test_format_time_time_fr2(self):
        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))

        t = datetime.time(15, 30)

        self.assertEqual(i18n.format_time(t, format='full'), u'15:30:00 heure normale d’Afrique de l’Ouest')
        self.assertEqual(i18n.format_time(t, format='long'), '15:30:00 +0100')
        self.assertEqual(i18n.format_time(t, format='medium'), '15:30:00')
        self.assertEqual(i18n.format_time(t), '15:30:00')
        self.assertEqual(i18n.format_time(t, format='short'), '15:30')

    def test_format_time_time_fr3(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))

        t = datetime.time(15, 30, tzinfo=pytz.timezone('Pacific/Pitcairn'))

        self.assertEqual(i18n.format_time(t, format='full'), '15:30:00 UTC+00:00')
        self.assertEqual(i18n.format_time(t, format='long'), '15:30:00 +0000')
        self.assertEqual(i18n.format_time(t, format='medium'), '15:30:00')
        self.assertEqual(i18n.format_time(t), '15:30:00')
        self.assertEqual(i18n.format_time(t, format='short'), '15:30')

    def test_format_time_time_fr4(self):
        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))

        t = datetime.time(15, 30, tzinfo=pytz.timezone('Pacific/Pitcairn'))

        self.assertEqual(i18n.format_time(t, format='full'), u'15:30:00 heure normale d’Afrique de l’Ouest')
        self.assertEqual(i18n.format_time(t, format='long'), '15:30:00 +0100')
        self.assertEqual(i18n.format_time(t, format='medium'), '15:30:00')
        self.assertEqual(i18n.format_time(t), '15:30:00')
        self.assertEqual(i18n.format_time(t, format='short'), '15:30')

    def test_format_time_time_en(self):
        i18n.set_locale(i18n.Locale('en', 'US', timezone='Pacific/Pitcairn'))

        t = datetime.time(15, 30)

        self.assertEqual(i18n.format_time(t, format='full'), '3:30:00 PM Pitcairn Time')
        self.assertEqual(i18n.format_time(t, format='long'), '3:30:00 PM -0800')
        self.assertEqual(i18n.format_time(t, format='medium'), '3:30:00 PM')
        self.assertEqual(i18n.format_time(t), '3:30:00 PM')
        self.assertEqual(i18n.format_time(t, format='short'), '3:30 PM')

    def test_format_time_time_with_format(self):
        i18n.set_locale(i18n.Locale('en', 'US', timezone='Pacific/Pitcairn'))

        t = datetime.time(15, 30)
        self.assertEqual(i18n.format_time(t, format="hh 'o''clock' a, zzzz"), "03 o'clock PM, Pitcairn Time")

        t = datetime.time(15, 30, tzinfo=pytz.timezone('Africa/Niamey'))
        self.assertEqual(i18n.format_time(t, format="hh 'o''clock' a, zzzz"), "03 o'clock PM, Pitcairn Time")

    def test_format_time_datetime_fr1(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))

        d = datetime.datetime(2007, 4, 1, 15, 30)

        self.assertEqual(i18n.format_time(d, format='full'), '15:30:00 UTC+00:00')
        self.assertEqual(i18n.format_time(d, format='long'), '15:30:00 +0000')
        self.assertEqual(i18n.format_time(d, format='medium'), '15:30:00')
        self.assertEqual(i18n.format_time(d), '15:30:00')
        self.assertEqual(i18n.format_time(d, format='short'), '15:30')

    def test_format_time_datetime_fr2(self):
        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))

        d = datetime.datetime(2007, 4, 1, 15, 30)

        self.assertEqual(i18n.format_time(d, format='full'), u'15:30:00 heure normale d’Afrique de l’Ouest')
        self.assertEqual(i18n.format_time(d, format='long'), '15:30:00 +0100')
        self.assertEqual(i18n.format_time(d, format='medium'), '15:30:00')
        self.assertEqual(i18n.format_time(d), '15:30:00')
        self.assertEqual(i18n.format_time(d, format='short'), '15:30')

    def test_format_time_datetime_fr3(self):
        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey', default_timezone=pytz.UTC))

        d = datetime.datetime(2007, 4, 1, 15, 30)

        self.assertEqual(i18n.format_time(d, format='full'), u'16:30:00 heure normale d’Afrique de l’Ouest')
        self.assertEqual(i18n.format_time(d, format='long'), '16:30:00 +0100')
        self.assertEqual(i18n.format_time(d, format='medium'), '16:30:00')
        self.assertEqual(i18n.format_time(d), '16:30:00')
        self.assertEqual(i18n.format_time(d, format='short'), '16:30')

    def test_format_time_datetime_fr4(self):
        i18n.set_locale(i18n.Locale('fr', 'FR'))

        tz = pytz.timezone('Pacific/Pitcairn')
        d = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))

        self.assertEqual(i18n.format_time(d, format='full'), '23:30:00 UTC+00:00')
        self.assertEqual(i18n.format_time(d, format='long'), '23:30:00 +0000')
        self.assertEqual(i18n.format_time(d, format='medium'), '23:30:00')
        self.assertEqual(i18n.format_time(d), '23:30:00')
        self.assertEqual(i18n.format_time(d, format='short'), '23:30')

    def test_format_time_datetime_fr5(self):
        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))

        tz = pytz.timezone('Pacific/Pitcairn')
        d = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))

        self.assertEqual(i18n.format_time(d, format='full'), u'00:30:00 heure normale d’Afrique de l’Ouest')
        self.assertEqual(i18n.format_time(d, format='long'), '00:30:00 +0100')
        self.assertEqual(i18n.format_time(d, format='medium'), '00:30:00')
        self.assertEqual(i18n.format_time(d), '00:30:00')
        self.assertEqual(i18n.format_time(d, format='short'), '00:30')

    def test_format_time_datetime_with_format(self):
        i18n.set_locale(i18n.Locale('en', 'US', timezone='Pacific/Pitcairn'))

        d = datetime.datetime(2007, 4, 1, 15, 30)
        self.assertEqual(i18n.format_time(d, format="hh 'o''clock' a, zzzz"), u"03 o'clock PM, Pitcairn Time")

        tz = pytz.timezone('Africa/Niamey')
        d = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(i18n.format_time(d, format="hh 'o''clock' a, zzzz"), u"06 o'clock AM, Pitcairn Time")

    def test_format_date_date(self):
        d = datetime.date(2007, 4, 1)

        self.assertEqual(i18n.format_date(d, format='full'), 'dimanche 1 avril 2007')
        self.assertEqual(i18n.format_date(d, format='long'), '1 avril 2007')
        self.assertEqual(i18n.format_date(d, format='medium'), '1 avr. 2007')
        self.assertEqual(i18n.format_date(d), '1 avr. 2007')
        self.assertEqual(i18n.format_date(d, format='short'), '01/04/2007')

    def test_format_date_datetime(self):
        tz = pytz.timezone('Pacific/Pitcairn')
        d = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))

        self.assertEqual(i18n.format_date(d, format='full'), 'dimanche 1 avril 2007')
        self.assertEqual(i18n.format_date(d, format='long'), '1 avril 2007')
        self.assertEqual(i18n.format_date(d, format='medium'), '1 avr. 2007')
        self.assertEqual(i18n.format_date(d), '1 avr. 2007')
        self.assertEqual(i18n.format_date(d, format='short'), '01/04/2007')

    def test_format_date_date_with_format(self):
        d = datetime.date(2007, 4, 1)

        self.assertEqual(i18n.format_date(d, 'EEE, MMM d, yy'), 'dim., avr. 1, 07')

    def test_format_datetime(self):
        i18n.set_locale(i18n.Locale('fr', 'FR', timezone='Africa/Niamey'))

        tz = pytz.timezone('Pacific/Pitcairn')
        d = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))

        self.assertEqual(i18n.format_datetime(d, format='full'), u'lundi 2 avril 2007 à 00:30:00 heure normale d’Afrique de l’Ouest')
        self.assertEqual(i18n.format_datetime(d, format='long'), u'2 avril 2007 à 00:30:00 +0100')
        self.assertEqual(i18n.format_datetime(d, format='medium'), u'2 avr. 2007 à 00:30:00')
        self.assertEqual(i18n.format_datetime(d), u'2 avr. 2007 à 00:30:00')
        self.assertEqual(i18n.format_datetime(d, format='short'), '02/04/2007 00:30')

    def test_format_datetime_with_format(self):
        i18n.set_locale(i18n.Locale('en', 'US', timezone='Pacific/Pitcairn'))

        d = datetime.datetime(2007, 4, 1, 15, 30)
        self.assertEqual(i18n.format_datetime(d, format="yyyy.MM.dd G 'at' HH:mm:ss zzz"), '2007.04.01 AD at 15:30:00 -0800')

        tz = pytz.timezone('Africa/Niamey')
        d = tz.localize(datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(i18n.format_datetime(d, format="yyyy.MM.dd G 'at' HH:mm:ss zzz"), '2007.04.01 AD at 06:30:00 -0800')


# -----------------------------------------------------------------------------

class TestParsing(unittest.TestCase):
    def setUp(self):
        local.request = local.Process()
        i18n.set_locale(i18n.Locale('fr', 'FR'))

    def test_parse_time_fr(self):
        t = i18n.parse_time('15:30:10')
        self.assertIsInstance(t, datetime.time)
        self.assertEqual((t.hour, t.minute, t.second), (15, 30, 10))

    def test_parse_time_en(self):
        i18n.set_locale(i18n.Locale('en', 'US'))

        t = i18n.parse_time('15:30:10')
        self.assertIsInstance(t, datetime.time)
        self.assertEqual((t.hour, t.minute, t.second), (15, 30, 10))

    def test_parse_date_fr(self):
        d = i18n.parse_date('4/1/04')
        self.assertIsInstance(d, datetime.date)
        self.assertEqual((d.year, d.month, d.day), (2004, 1, 4))

        d = i18n.parse_date('4/1/2004')
        self.assertIsInstance(d, datetime.date)
        self.assertEqual((d.year, d.month, d.day), (2004, 1, 4))

    def test_parse_date_en(self):
        i18n.set_locale(i18n.Locale('en', 'US'))

        d = i18n.parse_date('4/1/04')
        self.assertIsInstance(d, datetime.date)
        self.assertEqual((d.year, d.month, d.day), (2004, 4, 1))

        d = i18n.parse_date('4/1/2004')
        self.assertIsInstance(d, datetime.date)
        self.assertEqual((d.year, d.month, d.day), (2004, 4, 1))


# -----------------------------------------------------------------------------

class TestContext(unittest.TestCase):
    def setUp(self):
        local.request = local.Process()

    def test_context_manager(self):
        locale1 = i18n.Locale('fr', 'FR', domain='domain1')
        locale2 = i18n.Locale('fr', 'FR', domain='domain2')

        i18n.set_locale(locale1)
        self.assertEqual(i18n.get_locale().domain, 'domain1')

        with locale2:
            self.assertEqual(i18n.get_locale().domain, 'domain2')
            with locale2:
                self.assertEqual(i18n.get_locale().domain, 'domain2')

        self.assertEqual(i18n.get_locale().domain, 'domain1')
