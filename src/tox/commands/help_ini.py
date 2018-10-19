from __future__ import print_function, unicode_literals

import py


def show_help_ini(config):
    tw = py.io.TerminalWriter()
    tw.sep("-", "per-testenv attributes")
    for env_attr in config._testenv_attr:
        tw.line(
            "{:<15} {:<8} default: {}".format(
                env_attr.name, "<{}>".format(env_attr.type), env_attr.default
            ),
            bold=True,
        )
        tw.line(env_attr.help)
        tw.line()
