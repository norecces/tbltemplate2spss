# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals

from savReaderWriter.savReader import SavReader
from collections import OrderedDict

from structs import SurveyStructure, VariableStructure
import pandas as pd

DUMMY_FIELDS = ['InterviewID', 'Respondent', 'PanelResp', 'Page', 'Start', 'End', "ValidateCount",
                'Status', 'QueryString', 'Referer', 'IP', 'Agent', 'Length', 'Version',
                'SurveyStarted', 'ValidateCount@1', 'pre_data@resp', 'pre_data@s', 'pre_data@a']


class SavFile(object):

    def __init__(self, sav_file_name, use_unlabeled_values=False, multiple_choice_separator='_'):

        self.sav_file_name = sav_file_name
        self.reader = SavReader(self.sav_file_name, ioUtf8=True)

        self.reader.ioUtf8 = True
        self.plain_struct = self.get_plain_struct(use_unlabeled_values, multiple_choice_separator)
        self.data = pd.DataFrame(self.reader.all(), columns=self.reader.varNames)

    def _get_variable_names(self):
        #copy all values into memory or the process will run slowly
        return self.reader.varNames

    def _get_variable_labels(self):
        return self.reader.varLabels

    def _get_variable_types(self):
        return self.reader.varTypes

    def _get_value_labels(self):
        return self.reader.valueLabels

    def get_plain_struct(self, use_unlabeled_values, multiple_choice_separator):
        db_struct = SurveyStructure(multiple_choice_separator=multiple_choice_separator)

        variable_names = self._get_variable_names()
        variable_labels = self._get_variable_labels()
        variable_types = self._get_variable_types()
        variable_values = self._get_value_labels()

        for variable_id in variable_names:
            print(variable_id)
            variable_structure = VariableStructure(
                variable_id=variable_id,
                variable_label=variable_labels.get(variable_id, ''),
                variable_type=variable_types.get(variable_id, ''),
                variable_children=[],
                variable_values=variable_values.get(variable_id, {})
            )
            if not len(variable_structure['variable_values'].keys()) and use_unlabeled_values:
                # in case values labels are empty
                if variable_id in DUMMY_FIELDS:
                    continue

                if int(variable_structure['variable_type']) > 1:
                    # not int variables
                    continue

                variable_structure['variable_values'] = OrderedDict(
                    (k, '') for k in sorted(set(self.reader[:, variable_names.index(variable_id)]))
                )
            db_struct.append(variable_structure)

        return db_struct