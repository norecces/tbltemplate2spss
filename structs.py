# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals

from copy import deepcopy
from collections import OrderedDict


class SurveyStructure(list):

    def __init__(self, is_hierarchical=False, multiple_choice_separator='_', add_total=False):

        self._variables_ids_list = []
        self.is_hierarchical = is_hierarchical
        self.multiple_choices_separator = multiple_choice_separator

        super(SurveyStructure, self).__init__()

        if add_total:
            self.add_variable(
                variable_id='__TOTAL__',
                variable_type='Single',
                variable_label='',
                variable_values={1: 'Всего'}
            )

    def __contains__(self, key):
        return key in self._variables_ids_list

    def add_variable(self, variable_id, variable_type='', variable_label='',
                     variable_children=None, variable_survey_type='', variable_values=None):

        variable_struct = VariableStructure(
            variable_id=variable_id,
            variable_type=variable_type,
            variable_label=variable_label,
            variable_children=variable_children,
            variable_survey_type=variable_survey_type,
            variable_values=variable_values
        )

        if variable_id in self._variables_ids_list:
            self.remove(variable_id)
        self._variables_ids_list.append(variable_id)
        self.append(variable_struct)

    def get_variable_by_id(self, variable_id):
        return self[self._variables_ids_list.index(variable_id)]

    def get_all_questions_ids(self):
        return self._variables_ids_list

    def append(self, p_object):
        if not isinstance(p_object, (dict, VariableStructure, OrderedDict)):
            assert Exception('not suitable type ' + str(type(p_object)))

        if isinstance(p_object, (dict, OrderedDict)):
            p_object = VariableStructure(**p_object)

        if p_object['variable_id'] not in self._variables_ids_list:
            self._variables_ids_list.append(p_object['variable_id'])

        super(SurveyStructure, self).append(p_object)

    def remove(self, variable_id):
        variable_idx = self._variables_ids_list.index(variable_id)
        self.pop(variable_idx)
        self._variables_ids_list.pop(variable_idx)

    def to_dict(self):
        return {item['variable_id']: item for item in self}

    @classmethod
    def from_list(cls, lst):
        survey_structure = cls()
        for item in lst:
            if isinstance(item, (dict, OrderedDict)):
                survey_structure.append(VariableStructure(**item))
            elif isinstance(item, VariableStructure):
                survey_structure.append(item)
            else:
                raise TypeError('item type ' + str(type(item)) + ' is not instance of dict')
        return survey_structure

    def convert_to_hierarchical_structure(self, except_variables=None):
        if self.is_hierarchical:
            return deepcopy(self)
        if except_variables and not isinstance(except_variables, (list, set)):
            raise Exception('except_variables must be iterable got instead %s' % (type(except_variables), ))
        question_ids = []
        for variable_id in self._variables_ids_list:
            if except_variables:
                if variable_id in except_variables:
                    question_ids.append(variable_id)
                else:
                    question_ids.append(variable_id.split(self.multiple_choices_separator)[0])
            else:
                question_ids.append(variable_id.split(self.multiple_choices_separator)[0])

        temp_structure = OrderedDict()

        for variable_id_idx, question_id in enumerate(question_ids):
            if question_id in temp_structure:
                temp_structure[question_id].append(self._variables_ids_list[variable_id_idx])
            else:
                temp_structure[question_id] = [self._variables_ids_list[variable_id_idx]]

        new_survey_structure = SurveyStructure(is_hierarchical=True)
        for question_id in temp_structure.keys():

            variable_structure = self.get_variable_by_id(temp_structure[question_id][0])

            question_structure = VariableStructure(
                variable_id=question_id,
                variable_type=variable_structure['variable_type'],
                variable_label=variable_structure['variable_label'],
                variable_children=deepcopy(variable_structure['variable_children']),
                variable_survey_type=variable_structure['variable_survey_type'],
                variable_values=deepcopy(variable_structure['variable_values'])
            )

            for variable_id in temp_structure[question_id]:
                question_structure['variable_children'].append(variable_id)
                question_structure['variable_values'].update(
                    self.get_variable_by_id(variable_id)['variable_values']
                )

            new_survey_structure.append(question_structure)
        new_survey_structure._variables_ids_list = list(temp_structure.keys())

        return new_survey_structure


class VariableStructure(OrderedDict):
    __slots__ = ['variable_id', 'variable_type', 'variable_label', 'variable_children',
                 'variable_survey_type', 'variable_values']

    def __init__(self, variable_id, variable_type, variable_label=None,
                 variable_children=None, variable_survey_type=None, variable_values=None):
        super(VariableStructure, self).__init__()

        self['variable_id'] = variable_id
        self['variable_type'] = variable_type
        self['variable_label'] = variable_label if variable_label else u''
        self['variable_children'] = variable_children if variable_children else []
        self['variable_survey_type'] = variable_survey_type if variable_survey_type else None
        self['variable_values'] = variable_values if variable_values else OrderedDict()