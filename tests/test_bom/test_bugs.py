"""
Bugs tests

- Columns aren't case-insensitive.

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import logging
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context  # noqa: E402


def test_column_sensitive(test_dir):
    """ Test if the COLUMN_ORDER section can contain columns in lowercase """
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'ColumnSensitive', prj, ext, 'column_sensitive')
    ctx.run()
    out = prj + '.' + ext
    heads = ctx.load_csv_header(out)
    logging.debug(heads)
    assert len(heads) == 4
    ctx.clean_up()


def test_variants_issue_SG136_default(test_dir):
    prj = 'kibom-variant_2'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'test_variants_issue_SG136_default', prj, ext)
    extra = ['-r', 'default']
    ctx.run(no_config_file=True, extra=extra)
    out = prj + '_bom_A_(default).' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 1
    assert len(components) == 2
    assert 'R1' in components
    assert 'R2' in components
    assert 'C1' not in components
    assert 'C2' not in components
    ctx.clean_up()


def test_variants_issue_SG136_production(test_dir):
    prj = 'kibom-variant_2'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'test_variants_issue_SG136_production', prj, ext, 'production')
    ctx.run()
    # ctx.run(no_config_file=True, extra=['-r', 'production'])
    out = prj + '_bom_A_(production).' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 2
    assert len(components) == 3
    assert 'R1' in components
    assert 'R2' in components
    assert 'C1' not in components
    assert 'C2' in components
    ctx.clean_up()


def test_variants_issue_SG136_test(test_dir):
    prj = 'kibom-variant_2'
    ext = 'csv'
    ctx = context.TestContext(test_dir, 'test_variants_issue_SG136_test', prj, ext)
    extra = ['-r', 'test']
    ctx.run(no_config_file=True, extra=extra)
    out = prj + '_bom_A_(test).' + ext
    rows, components = ctx.load_csv(out)
    assert len(rows) == 2
    assert len(components) == 3
    assert 'R1' in components
    assert 'R2' not in components
    assert 'C1' in components
    assert 'C2' in components
    ctx.clean_up()
