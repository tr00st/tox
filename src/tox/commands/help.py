from __future__ import print_function, unicode_literals

import py


def show_help(config):
    tw = py.io.TerminalWriter()
    tw.write(config._parser._format_help())
    tw.line()
    tw.line("Environment variables", bold=True)
    tw.line("TOXENV: comma separated list of environments (overridable by '-e')")
    tw.line("TOX_SKIP_ENV: regular expression to filter down from running tox environments")
    tw.line(
        "TOX_TESTENV_PASSENV: space-separated list of extra environment variables to be "
        "passed into test command environments"
    )
    tw.line("PY_COLORS: 0 disable colorized output, 1 enable (default)")
