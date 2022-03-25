# -*- coding: utf-8 -*-
"""
Simple tests

- Simple cases for:
  - CSV
  - HTML
  - XML
  - XLSX
- Output in:
  - Same dir as netlist
  - Subdir relative to netlist
  - Unrelated dir (most test are this case)
  - Unrelated deep subdir
- Variants
  - Matrix in kibom-variante
  - V1+V3 from kibom-variante
- Components units
  - Sort and groups of RLC_sort
- Datasheet as link
- Digi-Key link
- Join columns
- ignore_dnf = 0
- html_generate_dnf = 0
- use_alt = 1
- number_rows = 0
- COLUMN_RENAME
  - CSV
  - HTML
  - XML
  - XLSX
- group_connectors = 1/0

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import shutil
import logging
import re
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context  # noqa: E402

BOM_DIR = 'BoM'
KIBOM_TEST_COMPONENTS = ['C1', 'C2', 'C3', 'C4', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8', 'R9', 'R10']
EXCLUDE_TEST = ['R6']


def check_kibom_test_netlist(rows, components, exclude=EXCLUDE_TEST, groups=5, comps=KIBOM_TEST_COMPONENTS):
    """ Checks the kibom-test.xml expected results """
    # Groups
    assert len(rows) == groups
    logging.debug(str(groups) + " groups OK")
    # Components
    if comps:
        assert len(components) == len(comps)
        logging.debug(str(len(comps)) + " components OK")
    # Excluded
    if exclude:
        for ex in exclude:
            assert ex not in components
        logging.debug(str(len(exclude)) + " not fitted OK")
    # All the other components
    if comps:
        for c in comps:
            assert c in components
        logging.debug("list of components OK")


def check_dnc(rows, comp, column=6):
    for row in rows:
        if row.find(comp) != -1:
            fields = row.split(',')
            assert fields[column] == '1 (DNC)'
            logging.debug(comp + " is DNC OK")
            return


def test_bom_simple_csv(test_dir):
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMSimpleCSV', prj, ext)
    ctx.run(no_config_file=True)
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components)
    check_dnc(rows, 'R7')
    ctx.clean_up()


def test_bom_simple_html(test_dir):
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContext(test_dir, 'BoMSimpleHTML', prj, ext)
    ctx.run(no_config_file=True)
    out = prj + '_bom_A.' + ext
    rows, components, rows_dnf, dnf = ctx.load_html(out)
    check_kibom_test_netlist(rows, components, groups=5)
    assert len(dnf) == 1
    assert 'R6' in dnf
    ctx.clean_up()


def test_bom_simple_xml(test_dir):
    prj = 'kibom-test'
    ext = 'xml'
    ctx = context.TestContext(test_dir, 'BoMSimpleXML', prj, ext)
    ctx.run(no_config_file=True)
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_xml(out)
    check_kibom_test_netlist(rows, components)
    ctx.clean_up()


def test_bom_simple_xlsx(test_dir):
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContext(test_dir, 'BoMSimpleXLSX', prj, ext)
    ctx.run(no_config_file=True)
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_xlsx(out)
    check_kibom_test_netlist(rows, components)
    ctx.clean_up()


def test_bom_deep_subdir(test_dir):
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMDeepSubdir', prj, ext)
    sub_dir = os.path.join('1', '2', '3')
    extra = ['-d', os.path.abspath(os.path.join(ctx.output_dir, sub_dir))]
    ctx.run(no_config_file=True, no_subdir=True, extra=extra)
    out = os.path.join(sub_dir, prj + '_bom_A.' + ext)
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components)
    ctx.clean_up()


def test_bom_same_dir(test_dir):
    """ The default behavior: put the output along with the netlist """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMSameDir', prj, ext)
    ctx.run(no_config_file=True, no_subdir=True)
    fn = prj + '_bom_A.' + ext
    out = os.path.join(ctx.get_board_dir(), fn)
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components)
    # Move the result to the output dir, avoid pollution
    os.rename(out, ctx.get_out_path(fn))
    ctx.clean_up()


def test_bom_rel_dir(test_dir):
    """ Relative sub directory (from netlist) """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMRelSubDir', prj, ext)
    sub_dir = os.path.join('1', '2', '3')
    extra = ['-d', sub_dir]
    ctx.run(no_config_file=True, no_subdir=True, extra=extra)
    fn = prj + '_bom_A.' + ext
    out = os.path.join(ctx.get_board_dir(), sub_dir, fn)
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components)
    # Move the result to the output dir, avoid pollution
    os.rename(out, ctx.get_out_path(fn))
    shutil.rmtree(os.path.join(ctx.get_board_dir(), '1'))
    ctx.clean_up()


def test_variant_t1_1(test_dir):
    prj = 'kibom-variante'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMVar_t1_1', prj, ext)
    extra = ['-r', 'V1']
    ctx.run(no_config_file=True, extra=extra)
    out = prj + '_bom_A_(V1).' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 2
    assert len(components) == 2
    assert 'R1' in components
    assert 'R2' in components
    assert 'R3' not in components
    assert 'R4' not in components
    assert ctx.search_out('WARNING') is None
    check_dnc(rows, 'R2')
    ctx.clean_up()


def test_variant_t1_2(test_dir):
    prj = 'kibom-variante'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMVar_t1_2', prj, ext)
    extra = ['-r', 'V2']
    ctx.run(no_config_file=True, extra=extra)
    out = prj + '_bom_A_(V2).' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 1
    assert len(components) == 2
    assert 'R1' in components
    assert 'R2' not in components
    assert 'R3' in components
    assert 'R4' not in components
    assert ctx.search_out('WARNING') is None
    ctx.clean_up()


def test_variant_t1_3(test_dir):
    prj = 'kibom-variante'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMVar_t1_3', prj, ext)
    extra = ['-r', 'V3']
    ctx.run(no_config_file=True, extra=extra)
    out = prj + '_bom_A_(V3).' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 1
    assert len(components) == 2
    assert 'R1' in components
    assert 'R2' not in components
    assert 'R3' not in components
    assert 'R4' in components
    assert ctx.search_out('WARNING') is None
    ctx.clean_up()


def test_variant_t1_4(test_dir):
    prj = 'kibom-variante'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMVar_t1_4', prj, ext)
    ctx.run(no_config_file=True)
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 2
    assert len(components) == 3
    assert 'R1' in components
    assert 'R2' in components
    assert 'R3' in components
    assert 'R4' not in components
    check_dnc(rows, 'R2')
    assert ctx.search_out('WARNING') is None
    ctx.clean_up()


def test_variant_t1_5(test_dir):
    """ default union V3 """
    prj = 'kibom-variante'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMVar_t1_1', prj, ext)
    extra = ['-r', 'V1,V3']
    ctx.run(no_config_file=True, extra=extra)
    out = prj + '_bom_A_(V1,V3).' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 1
    assert len(components) == 2
    assert 'R1' in components
    assert 'R2' not in components
    assert 'R3' not in components
    assert 'R4' in components
    assert ctx.search_out('WARNING') is None
    ctx.clean_up()


def test_sort_1(test_dir):
    prj = 'RLC_sort'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'BoMSort1', prj, ext)
    ctx.run(no_config_file=True)
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components, exclude=None, groups=14, comps=None)
    exp = ['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C1', 'C2', 'C3', 'C4', 'C11', 'C12',
           'R5', 'R4', 'R9', 'R10', 'R3', 'R2', 'R1', 'R8', 'R7']
    assert components == exp
    ctx.clean_up()


def test_datasheet_link(test_dir):
    prj = 'links'
    ext = 'html'
    ctx = context.TestContext(test_dir, 'DataSheetLink', prj, ext, 'datasheet_link')
    ctx.run()
    out = prj + '.' + ext
    rows, components, rows_dnf, dnf = ctx.load_html(out, 3, False)
    assert len(rows) == 2
    assert len(rows_dnf) == 1
    for c in components + dnf:
        assert c.strip().startswith('<a href')
        assert 'pdf' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_digikey_link(test_dir):
    prj = 'links'
    ext = 'html'
    ctx = context.TestContext(test_dir, 'DigiKeyLink', prj, ext, 'digikey_link')
    ctx.run()
    out = prj + '.' + ext
    rows, components, rows_dnf, dnf = ctx.load_html(out, 5, False)
    assert len(rows) == 2
    assert len(rows_dnf) == 1
    for c in components + dnf:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_join_1(test_dir):
    prj = 'join'
    ext = 'html'
    ctx = context.TestContext(test_dir, 'Join_1', prj, ext, 'join')
    ctx.run()
    out = prj + '.' + ext
    rows, components, rows_dnf, dnf = ctx.load_html(out, 2, False)
    assert len(rows) == 3
    assert len(rows_dnf) == 0
    assert 'C1' in rows[0] and '1nF 10% 50V' in rows[0] and 'KEMET C0805C102K5RACTU' in rows[0]
    assert 'J1 J2' in rows[1] and 'Molex KK' in rows[1] and 'Molex 0022232021' in rows[1]
    assert 'R1' in rows[2] and '1k 5%' in rows[2] and 'Bourns CR0805-JW-102ELF' in rows[2]
    ctx.clean_up()


def test_include_dnf(test_dir):
    """ ignore_dnf = 0 """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'IncludeDNF', prj, ext, 'include_dnf')
    ctx.run()
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components, exclude=None, groups=6,
                             comps=KIBOM_TEST_COMPONENTS + EXCLUDE_TEST)
    ctx.clean_up()


def test_html_dont_generate_dnf(test_dir):
    """ html_generate_dnf = 0 """
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContext(test_dir, 'DontGenerateDNF', prj, ext, 'html_dont_generate_dnf')
    ctx.run()
    out = prj + '_bom_A.' + ext
    rows, components, rows_dnf, dnf = ctx.load_html(out)
    check_kibom_test_netlist(rows, components, groups=5)
    assert len(dnf) == 0
    ctx.clean_up()


def test_use_alt(test_dir):
    """ use_alt = 1 """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'UseAlt', prj, ext, 'use_alt')
    ctx.run()
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components, groups=5, comps=['C1-C4', 'R9-R10', 'R7', 'R8', 'R1-R5'])
    ctx.clean_up()


def test_no_number_rows(test_dir):
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'NoNumberRows', prj, ext, 'no_numbers')
    ctx.run()
    out = prj + '_bom_A.' + ext
    rows, components = ctx.load_csv(out, 2)
    check_kibom_test_netlist(rows, components)
    check_dnc(rows, 'R7', 5)
    ctx.clean_up()


def test_column_rename_csv(test_dir):
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'ColumnRenameCSV', prj, ext, 'col_rename')
    ctx.run()
    out = prj + '.' + ext
    heads = ctx.load_csv_header(out)
    assert heads == ['Renglón', 'Referencias', 'Componente', 'Valor', 'Código Digi-Key', 'Cantidad por PCB']
    rows, components = ctx.load_csv(out, 1)
    check_kibom_test_netlist(rows, components, exclude=[], groups=3, comps=['C1', 'J1', 'J2', 'R1'])
    ctx.clean_up()


def test_column_rename_html(test_dir):
    prj = 'links'
    ext = 'html'
    ctx = context.TestContext(test_dir, 'ColumnRenameHTML', prj, ext, 'col_rename')
    ctx.run()
    out = prj + '.' + ext
    heads = ctx.load_html_header(out)
    assert heads == ('Referencias', 'Componente', 'Valor', 'Código Digi-Key', 'Cantidad por PCB')
    rows, components, rows_dnf, dnf = ctx.load_html(out, 2)
    check_kibom_test_netlist(rows, components, exclude=[], groups=3, comps=['C1', 'J1', 'J2', 'R1'])
    ctx.clean_up()


def test_column_rename_xml(test_dir):
    prj = 'links'
    ext = 'xml'
    ctx = context.TestContext(test_dir, 'ColumnRenameXML', prj, ext, 'col_rename')
    ctx.run()
    out = prj + '.' + ext
    rows, components = ctx.load_xml(out, 'Referencias')
    m = re.match(r'<group\s+(.*?)="[^"]+"\s+(.*?)="[^"]+"\s+(.*?)="[^"]+"\s+(.*?)="[^"]+"\s+(.*?)="[^"]+"', rows[0].strip())
    assert m
    groups = m.groups()
    for h in ['Referencias', 'Componente', 'Valor', 'Código_Digi-Key', 'Cantidad_por_PCB']:
        assert h in groups
    check_kibom_test_netlist(rows, components, exclude=[], groups=3, comps=['C1', 'J1', 'J2', 'R1'])
    ctx.clean_up()


def test_column_rename_xlsx(test_dir):
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContext(test_dir, 'ColumnRenameXLSX', prj, ext, 'col_rename')
    ctx.run()
    out = prj + '.' + ext
    rows, components = ctx.load_xlsx(out, 2, True)
    assert components == ['Renglón', 'Referencias', 'Componente', 'Valor', 'Código Digi-Key', 'Cantidad por PCB']
    rows, components = ctx.load_xlsx(out, 2)
    check_kibom_test_netlist(rows, components, exclude=[], groups=3, comps=['C1', 'J1', 'J2', 'R1'])
    ctx.clean_up()


def test_group_connectors(test_dir):
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'GroupConnectors', prj, ext)
    ctx.run(no_config_file=True)
    out = prj + '_bom_.' + ext
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components, exclude=None, groups=2, comps=['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()


def test_no_group_connectors(test_dir):
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'NoGroupConnectors', prj, ext, 'no_group_connectors')
    ctx.run()
    out = prj + '_bom_.' + ext
    rows, components = ctx.load_csv(out)
    check_kibom_test_netlist(rows, components, exclude=None, groups=4, comps=['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()
