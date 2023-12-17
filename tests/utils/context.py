import os
import shutil
import tempfile
import logging
import subprocess
import re
import csv
import sys
from glob import glob
from pty import openpty

COVERAGE_SCRIPT = 'python3-coverage'
KICAD_NETLIST_EXT = '.xml'
KICAD_SCH_EXT = '.sch'
REF_DIR = 'tests/reference'


MODE_SCH = 1
MODE_PCB = 0


if sys.version_info.major >= 3:
    def os_open(name, flags, mode):
        return os.open(name, flags, mode=mode)

    def os_makedirs(dir):
        os.makedirs(dir, exist_ok=True)
else:
    # Ancient python compatibility
    def os_open(name, flags, mode):
        return os.open(name, flags, mode)

    def os_makedirs(dir):
        if not os.path.isdir(dir):
            os.makedirs(dir)


class TestContext(object):

    def __init__(self, test_dir, test_name, prj_name, ext, config_name=None):
        # We are using PCBs
        self.mode = MODE_PCB
        # The name used for the test output dirs and other logging
        self.test_name = test_name
        # The name of the PCB board file
        self.prj_name = prj_name
        # The actual board file that will be loaded
        self._get_netlist_file()
        # The INI file we'll use
        self._get_config_name(config_name)
        # The actual output dir for this run
        self._set_up_output_dir(test_dir)
        # Output format
        self.ext = ext
        # stdout and stderr from the run
        self.out = None
        self.err = None
        self.proc = None

    def get_board_dir(self):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(this_dir, '../input_samples')

    def _get_netlist_file(self):
        self.netlist_file = os.path.abspath(os.path.join(self.get_board_dir(), self.prj_name + KICAD_NETLIST_EXT))
        self.sch_file = os.path.abspath(os.path.join(self.get_board_dir(), self.prj_name + KICAD_SCH_EXT))
        logging.info('KiCad file: ' + self.netlist_file)
        assert os.path.isfile(self.netlist_file)

    def _get_config_dir(self):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(this_dir, '../config_samples')

    def _get_config_name(self, name):
        skip_test = False
        if not name:
            name = 'bom'
            skip_test = True
        self.config_file = os.path.abspath(os.path.join(self._get_config_dir(), name + '.ini'))
        logging.info('Config file: ' + self.config_file)
        assert skip_test or os.path.isfile(self.config_file)

    def _set_up_output_dir(self, test_dir):
        if test_dir:
            self.output_dir = os.path.join(test_dir, self.test_name)
            os_makedirs(self.output_dir)
            self._del_dir_after = False
        else:
            # create a tmp dir
            self.output_dir = tempfile.mkdtemp(prefix='tmp-kiplot-' + self.test_name + '-')
            self._del_dir_after = True
        logging.info('Output dir: ' + self.output_dir)

    def clean_up(self):
        logging.debug('Clean-up')
        if self._del_dir_after:
            logging.debug('Removing dir')
            shutil.rmtree(self.output_dir)
        # We don't have a project, and we don't want one
        pro = os.path.join(self.get_board_dir(), self.prj_name + '.pro')
        if os.path.isfile(pro):
            os.remove(pro)
        # We don't have a footprint cache, and we don't want one
        fp_cache = os.path.join(self.get_board_dir(), 'fp-info-cache')
        if os.path.isfile(fp_cache):
            os.remove(fp_cache)

    def get_out_path(self, filename):
        return os.path.join(self.output_dir, filename)

    def expect_out_file(self, filename):
        file = self.get_out_path(filename)
        assert os.path.isfile(file), file
        assert os.path.getsize(file) > 0
        logging.debug(filename + ' OK')
        return file

    def load_csv_header(self, filename):
        with open(self.expect_out_file(filename)) as csvfile:
            reader = csv.reader(csvfile)
            return next(reader)

    def load_csv(self, filename, column=3):
        rows = []
        components = []
        with open(self.expect_out_file(filename)) as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for r in reader:
                if not r:
                    break
                rows.append(','.join(r))
                components.extend(r[column].split(' '))
        return rows, components

    def load_html_header(self, filename, column=4, split=True):
        file = self.expect_out_file(filename)
        with open(file) as f:
            html = f.read()
        m = re.search(r'<tr>\s+'
                      + r'<th></th>\s+'
                      + r'<th.*?>(.*)</th>\s+'
                      + r'<th.*?>(.*)</th>\s+'
                      + r'<th.*?>(.*)</th>\s+'
                      + r'<th.*?>(.*)</th>\s+'
                      + r'<th.*?>(.*)</th>', html, re.MULTILINE)
        return m.groups() if m else None

    def load_html(self, filename, column=4, split=True):
        file = self.expect_out_file(filename)
        with open(file) as f:
            html = f.read()
        rows = []
        rows_dnf = []
        components = []
        components_dnf = []
        prev = 0
        dnf = False
        for entry in re.finditer(r'<tr>\s+'
                                 + r'<td.*?>(\d+)</td>\s+'
                                 + r'<td.*?>(.*)</td>\s+'
                                 + r'<td.*?>(.*)</td>\s+'
                                 + r'<td.*?>(.*)</td>\s+'
                                 + r'<td.*?>(.*)</td>', html):
            cur = int(entry.group(1))
            if cur < prev:
                dnf = True
            if dnf:
                rows_dnf.append(entry.group(0))
                if split:
                    components_dnf.extend(entry.group(column).split(' '))
                else:
                    components_dnf.append(entry.group(column))
            else:
                rows.append(entry.group(0))
                if split:
                    components.extend(entry.group(column).split(' '))
                else:
                    components.append(entry.group(column))
            prev = cur
        return rows, components, rows_dnf, components_dnf

    def load_xml(self, filename, ref='References'):
        file = self.expect_out_file(filename)
        rows = []
        components = []
        line_re = re.compile(r'\s+<group.*' + ref + '="([^"]+)"')
        with open(file) as f:
            for line in f:
                m = line_re.match(line)
                if m:
                    rows.append(line)
                    components.extend(m.group(1).split(' '))
        return rows, components

    def load_xlsx(self, filename, column=4, heads=False):
        """ Assumes the components are in sheet1 """
        file = self.expect_out_file(filename)
        subprocess.call(['unzip', file, '-d', self.get_out_path('desc')])
        # Some XMLs are stored with 0600 preventing them to be read by next CI/CD stage
        subprocess.call(['chmod', '-R', 'og+r', self.get_out_path('desc')])
        worksheet = self.get_out_path(os.path.join('desc', 'xl', 'worksheets', 'sheet1.xml'))
        rows = []
        comp_strs = []
        with open(worksheet) as f:
            xml = f.read()
        # Cell matching string
        col_char = chr(ord('A') + column - 1)
        re_dcol = re.compile(r'<c r="' + col_char + r'\d+"[^>]+><v>(\d+)</v></c>')
        # We should find row #1
        row_n = 1
        # Search the rows
        for entry in re.finditer(r'<row r="(\d+)"[^>]+>(.*?)<\/row>', xml):
            row = entry.group(0)
            if heads:
                # If we are looking for the headings extract them and exit
                rows.append(row)
                for col in re.finditer(r'<c r="\w\d+"[^>]+><v>(\d+)</v></c>', row):
                    comp_strs.append(col.group(1))
                break
            # Check if we reached the schematic info section
            if int(entry.group(1)) > row_n:
                break
            row_n += 1
            # Extract the column we are looking for
            m = re_dcol.search(row)
            if m:
                rows.append(row)
                comp_strs.append(m.group(1))
                # logging.debug(row+" -> "+m.group(1))
            else:
                break
        # Remove the row 1
        if not heads:
            rows.pop(0)
            comp_strs.pop(0)
        # Translate the indexes to strings
        # 1) Get the list of strings
        strings = self.get_out_path(os.path.join('desc', 'xl', 'sharedStrings.xml'))
        with open(strings) as f:
            xml = f.read()
        strs = [entry.group(1) for entry in re.finditer(r'<si><t>(.*?)<\/t><\/si>', xml)]
        # 2) Replace the strings and get the components
        components = []
        for idx in comp_strs:
            cell = strs[int(idx)]
            # logging.debug(str(idx)+' -> '+cell)
            if heads:
                components.append(cell)
            else:
                components.extend(cell.split(' '))
        return rows, components

    def dont_expect_out_file(self, filename):
        file = self.get_out_path(filename)
        assert not os.path.isfile(file)

    def create_dummy_out_file(self, filename):
        file = self.get_out_path(filename)
        with open(file, 'w') as f:
            f.write('Dummy file\n')

    def run(self, ret_val=None, extra=None, use_a_tty=False, filename=None, no_subdir=False,
            no_config_file=False, chdir_out=False, no_verbose=False):
        logging.debug('Running ' + self.test_name)
        # Change the command to be local and add the board and output arguments
        cmd = [COVERAGE_SCRIPT, 'run', '-a']
        if chdir_out:
            cmd.append('--rcfile=../../.coveragerc')
            os.environ['COVERAGE_FILE'] = os.path.join(os.getcwd(), '.coverage')
        cmd.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../../KiBOM_CLI.py'))
        if not no_verbose:
            cmd.append('-vvv')
        if not no_config_file:
            cmd = cmd + ['--cfg', self.config_file]
        if extra is not None:
            cmd = cmd + extra
        if not no_subdir:
            # This changed in 1.7.x the path indicated in the output name is ignored.
            # The only way is to specify an absolute path here.
            cmd = cmd + ['-d', os.path.abspath(self.output_dir)]
        cmd.append(filename if filename else self.netlist_file)
        cmd.append(self.prj_name + '.' + self.ext)
        logging.debug(cmd)
        out_filename = self.get_out_path('output.txt')
        err_filename = self.get_out_path('error.txt')
        if use_a_tty:
            # This is used to test the coloured logs, we need stderr to be a TTY
            master, slave = openpty()
            f_err = slave
            f_out = slave
        else:
            # Redirect stdout and stderr to files
            f_out = os_open(out_filename, os.O_RDWR | os.O_CREAT, 0o664)
            f_err = os_open(err_filename, os.O_RDWR | os.O_CREAT, 0o664)
        # Run the process
        if chdir_out:
            cwd = os.getcwd()
            os.chdir(self.output_dir)
        process = subprocess.Popen(cmd, stdout=f_out, stderr=f_err)
        if chdir_out:
            os.chdir(cwd)
            del os.environ['COVERAGE_FILE']
        ret_code = process.wait()
        logging.debug('ret_code ' + str(ret_code))
        if use_a_tty:
            self.err = os.read(master, 10000)
            self.err = self.err.decode()
            self.out = self.err
        exp_ret = 0 if ret_val is None else ret_val
        assert ret_code == exp_ret
        if use_a_tty:
            os.close(master)
            os.close(slave)
            with open(out_filename, 'w') as f:
                f.write(self.out)
            with open(err_filename, 'w') as f:
                f.write(self.out)
        else:
            # Read stdout
            os.lseek(f_out, 0, os.SEEK_SET)
            self.out = os.read(f_out, 10000)
            os.close(f_out)
            self.out = self.out.decode()
            # Read stderr
            os.lseek(f_err, 0, os.SEEK_SET)
            self.err = os.read(f_err, 10000)
            os.close(f_err)
            self.err = self.err.decode()
        # Check for infamous .tmp files
        tmps = glob(os.path.join(self.get_board_dir(), '*.tmp'))
        assert len(tmps) == 0, str(tmps)

    def search_out(self, text):
        m = re.search(text, self.out, re.MULTILINE)
        return m

    def search_err(self, text):
        m = re.search(text, self.err, re.MULTILINE)
        return m

    def search_in_file(self, file, texts):
        logging.debug('Searching in "' + file + '" output')
        with open(self.get_out_path(file)) as f:
            txt = f.read()
        res = []
        for t in texts:
            logging.debug('- r"' + t + '"')
            m = re.search(t, txt, re.MULTILINE)
            assert m
            # logging.debug(' '+m.group(0))
            res.append(m.groups())
        return res

    def search_not_in_file(self, file, texts):
        logging.debug('Searching not in "' + file + '" output')
        with open(self.get_out_path(file)) as f:
            txt = f.read()
        for t in texts:
            logging.debug('- r"' + t + '"')
            m = re.search(t, txt, re.MULTILINE)
            assert m is None

    def compare_txt(self, text, reference=None, diff='diff.txt'):
        if reference is None:
            reference = text
        cmd = ['/bin/sh', '-c', 'diff -ub ' + os.path.join(REF_DIR, reference) + ' '
               + self.get_out_path(text) + ' > ' + self.get_out_path(diff)]
        logging.debug('Comparing texts with: ' + str(cmd))
        res = subprocess.call(cmd)
        assert res == 0

    def filter_txt(self, file, pattern, repl):
        fname = self.get_out_path(file)
        with open(fname) as f:
            txt = f.read()
        with open(fname, 'w') as f:
            f.write(re.sub(pattern, repl, txt))
