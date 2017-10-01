# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals


class TablesSet(object):
    def __init__(self):
        self.tables = []
        self.tables_ids = []

    def add_table(self, table):
        self.tables.append(table)
        self.tables_ids.append(table.id)

    def get_table_by_id(self, table_id):
        return self.tables[self.tables_ids.index(table_id)]


class Table(object):

    SPSS_TABLE_TEMPLATE = u'{ADDITIONAL}\nTABLES\n/FORMAT ZERO MISSING("."){OBS}\n/MRGROUP $ff "" {VARS}\n' \
                          u'/FTOTAL $T "BASE"\n/TABLE={TVARS} BY tban\n/STAT\n{STATS}\tcount ($T (F5.0) "" )\n' \
                          u'/TITLE "{TITLE}"\n"{SUBTITLE}"\n/CAPTION "{CAPTION}"\n/CORNER "{CORNER}".\n\n'

    def __init__(self, question_structure):
        self.id = None
        self.title = None
        self.subtitle = None
        self.corner = None
        self.rows = None
        self.columns = None
        self.statistics = None
        self.footer = None
        self.chart = None

        self.question_structure = question_structure

        self.is_exported = False

    def to_syntax(self, syntax_type):
        if syntax_type == 'spss':
            return self._convert_to_spss_syntax()

    def _convert_to_spss_syntax(self):
        spss_settings = {
            'text_varstocases': '',
            'text_recode': '',
            'text_filter': '',
            'spss_mrgroup_variables': '',
            'spss_table_variables': '',
            'spss_statistics': '',
            'spss_obs': ''
        }
        text_recode = ''
        text_filter = ''
        text_statistics = ''
        spss_mrgroup_variables = list(self.rows)
        spss_table_variables = [u'$ff']
        question_variable_id = self.question_structure['variable_id']

        spss_cpct_template = u'\tcpct ($ff ({PCTFORMAT}) "{PCTSIGN}" : sban)\n'
        spss_mean_template = u'\tmean ({MEANVARIABLE} ({MEANFORMAT}) "{MEANSIGN}")\n\tvariance ({MEANVARIABLE} (F5.2) "variance")\n'

        if self.statistics.percentage is not None:
            text_statistics += spss_cpct_template.format(PCTFORMAT=u'PCT5.0', PCTSIGN=u'')
            for prop in self.statistics.percentage.props:
                if prop.startswith('t') or prop.startswith('b'):
                    first_letter = prop[0]
                    letter_multiplier = 1 if first_letter == 't' else 2
                    try:
                        num = int(prop[1:])
                        label_values = self.question_structure['variable_values'].keys()
                        label_values.sort()

                        text_recode += u'recode ' + ' '.join(self.rows)

                        if first_letter == 't':
                            text_recode += u' (' + u', '.join([str(v) for v in label_values[-1*num:]])
                        else:
                            text_recode += u' (' + u', '.join([str(v) for v in label_values[1:num+1]]) #starts with 1 because of None

                        text_recode += u' = ' + str(letter_multiplier*100+num) + u')(else=sys) into '
                        text_recode += prop + question_variable_id + u'.\n'
                        text_recode += u'val lab ' + prop + question_variable_id
                        text_recode += u' ' + str(letter_multiplier*100+num)
                        text_recode += (u' "Top-' if first_letter == 't' else u' "Bottom-') + str(num) + u'".\n'
                        spss_mrgroup_variables.append(prop + question_variable_id)
                    except ValueError as e:
                        print(prop, prop[1:])

                    except TypeError as e:
                        print(prop, e)
        if self.statistics.mean:

            label_values = self.question_structure['variable_values'].keys()
            recode_to_sysmis = u''
            if 9 in label_values and 8 not in label_values:
                recode_to_sysmis += u'(9=sys)'
            if 99 in label_values and 98 not in label_values:
                recode_to_sysmis += u'(99=sys)'
            text_recode += u'recode ' + u' '.join(self.rows) + u' ' + recode_to_sysmis + u'(else=copy) into '
            text_recode += u'm' + question_variable_id + u'.\n'
            text_filter = u'temp.\nsel if ~sysmis(' + u' '.join(self.rows) + u').\n'
            mean_variable = u'm' + question_variable_id
            spss_settings['spss_obs'] += u'\n/OBS ' + mean_variable
            spss_table_variables.append(mean_variable)
            text_statistics += spss_mean_template.format(MEANVARIABLE=mean_variable, MEANFORMAT=u'F5.2', MEANSIGN=u'mean')

        spss_settings['text_recode'] = text_recode
        spss_settings['text_filter'] = text_filter

        spss_settings['spss_mrgroup_variables'] = u' '.join(spss_mrgroup_variables)
        spss_settings['spss_statistics'] = text_statistics

        spss_table_variables.append(u'$T')
        spss_settings['spss_table_variables'] = u'+'.join(spss_table_variables)

        return self.SPSS_TABLE_TEMPLATE.format(
            ADDITIONAL=text_recode+text_filter,
            OBS=spss_settings['spss_obs'],
            VARS=spss_settings['spss_mrgroup_variables'],
            TVARS=spss_settings['spss_table_variables'],
            STATS=spss_settings['spss_statistics'],
            TITLE=self.title.upper(),
            SUBTITLE=self.subtitle,
            CORNER=self.corner,
            CAPTION=self.footer
        ).replace(u'None', u'')





class TableRows(object):

    def __init__(self):
        self.pure = True
        self.groupby = None


class TableGroupBy(object):
    def __init__(self):
        self.text = ''
        self.by = None


class TableBy(object):
    def __init__(self):
        self.text = ''


class TableColumns(TableRows):
    pass


class TableChart():
    def __init__(self, **kwargs):
        self.type = kwargs.pop('Type', 'bar')
        # False, 0 - vertical bars; True, 1 = horizontal bars
        self.align = kwargs.pop('Align', False)
        self.is_stacked = kwargs.pop('Stacked', False)
        self.show_labels = kwargs.pop('Labels', True)



class TableStatistics():

    PROPERTIES = ['t2', 't3', 't4', 't5', 'b2', 'b3', 'b4', 'b5', 'm']

    def __init__(self):
        self.percentage = None
        self.mean = None
        self.median = None

    def add_properties(self, properties):
        self.percentage = PercentageStatistic()
        if properties is None:
            return
        if isinstance(properties, str) or isinstance(properties, unicode):
            properties = properties.split(' ')

        for prop in properties:
            if prop.startswith('t') or prop.startswith('b'):
                self.percentage.props.append(prop)

            if prop.startswith('m'):
                self.mean = True


class PercentageStatistic(object):

    SPSS_PCT_SIGN = ''
    SPSS_PCT_FORMAT = 'PCT5.0'
    SPSS_PCT_TEMPLATE = '''cpct ($ff ({SPSS_PCT_FORMAT}) '{SPSS_PCT_SIGN}' : sban)\n'''

    def __init__(self):
        self.props = []


class StatisticsConfig(object):
    __name__ = ''

    def __init__(self, label=None, precision=None, exclude=None):
        self.label = label
        self.precision = precision
        self.exclude = exclude

    def get_statistics_type(self):
        return self.__name__

    def is_statistics_type(self, stat_type):
        return self.__name__ == stat_type


class PercentageStat(StatisticsConfig):
    __name__ = '__PERCENTAGE__'

    def __init__(self, **kwargs):
        label = kwargs.pop('label')
        precision = kwargs.pop('precision')

        super(PercentageStat, self).__init__(label=label, precision=precision)


class MeanStat(StatisticsConfig):
    __name__ = '__MEAN__'

    def __init__(self, **kwargs):
        label = kwargs.pop('label')
        precision = kwargs.pop('precision')
        exclude = kwargs.pop('exclude')

        super(MeanStat, self).__init__(label=label, precision=precision, exclude=exclude)