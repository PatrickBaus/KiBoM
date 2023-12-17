# -*- coding: utf-8 -*-
from typing import List

from kibom.case_insensitive_dict import CaseInsensitiveDict


class ColumnList:

    # Default columns (immutable)
    COL_REFERENCE = 'References'
    COL_DESCRIPTION = 'Description'
    COL_VALUE = 'Value'
    COL_FP = 'Footprint'
    COL_FP_LIB = 'Footprint Lib'
    COL_PART = 'Part'
    COL_PART_LIB = 'Part Lib'
    COL_SHEETPATH = 'Sheetpath'
    COL_DATASHEET = 'Datasheet'

    # Default columns for groups
    COL_GRP_QUANTITY = 'Quantity Per PCB'
    # COL_GRP_TOTAL_COST = 'Total Cost'
    # COL_GRP_TOTAL_COST_L = COL_GRP_TOTAL_COST.lower()
    COL_GRP_BUILD_QUANTITY = 'Build Quantity'

    # Generated columns
    _COLUMNS_GEN = CaseInsensitiveDict.fromkeys([
        COL_GRP_QUANTITY,
        COL_GRP_BUILD_QUANTITY,
    ])

    # Default columns
    # These columns are 'immutable'
    _COLUMNS_DEFAULT = CaseInsensitiveDict.fromkeys([
        COL_DESCRIPTION,
        COL_PART,
        COL_PART_LIB,
        COL_REFERENCE,
        COL_VALUE,
        COL_FP,
        COL_FP_LIB,
        COL_SHEETPATH,
        COL_GRP_QUANTITY,
        COL_GRP_BUILD_QUANTITY,
        COL_DATASHEET
    ])
