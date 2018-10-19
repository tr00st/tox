from __future__ import print_function, unicode_literals

import time

import py


class Verbosity(object):
    DEBUG = 2
    INFO = 1
    DEFAULT = 0
    QUIET = -1
    EXTRA_QUIET = -2


class Reporter(object):
    actionchar = "-"

    def __init__(self, session):
        self.tw = py.io.TerminalWriter()
        self.session = session
        self.reported_lines = []

    @property
    def verbosity(self):
        if self.session:
            return (
                self.session.config.option.verbose_level - self.session.config.option.quiet_level
            )
        else:
            return Verbosity.DEBUG

    def logpopen(self, popen, cmd_args_shell):
        """ log information about the action.popen() created process. """
        if popen.outpath:
            self.verbosity1("  {}$ {} >{}".format(popen.cwd, cmd_args_shell, popen.outpath))
        else:
            self.verbosity1("  {}$ {} ".format(popen.cwd, cmd_args_shell))

    def logaction_start(self, action):
        msg = "{} {}".format(action.msg, " ".join(map(str, action.args)))
        self.verbosity2("{} start: {}".format(action.venvname, msg), bold=True)
        assert not hasattr(action, "_starttime")
        action._starttime = time.time()

    def logaction_finish(self, action):
        duration = time.time() - action._starttime
        self.verbosity2(
            "{} finish: {} after {:.2f} seconds".format(action.venvname, action.msg, duration),
            bold=True,
        )
        delattr(action, "_starttime")

    def startsummary(self):
        if self.verbosity >= Verbosity.QUIET:
            self.tw.sep("_", "summary")

    def logline_if(self, level, msg, key=None, **kwargs):
        if self.verbosity >= level:
            message = str(msg) if key is None else "{}{}".format(key, msg)
            self.logline(message, **kwargs)

    def logline(self, msg, **opts):
        self.reported_lines.append(msg)
        self.tw.line("{}".format(msg), **opts)

    def keyboard_interrupt(self):
        self.error("KEYBOARDINTERRUPT")

    def keyvalue(self, name, value):
        if name.endswith(":"):
            name += " "
        self.tw.write(name, bold=True)
        self.tw.write(value)
        self.tw.line()

    def line(self, msg, **opts):
        self.logline(msg, **opts)

    def info(self, msg):
        self.logline_if(Verbosity.DEBUG, msg)

    def using(self, msg):
        self.logline_if(Verbosity.INFO, msg, "using ", bold=True)

    def good(self, msg):
        self.logline_if(Verbosity.QUIET, msg, green=True)

    def warning(self, msg):
        self.logline_if(Verbosity.QUIET, msg, "WARNING: ", red=True)

    def error(self, msg):
        self.logline_if(Verbosity.QUIET, msg, "ERROR: ", red=True)

    def skip(self, msg):
        self.logline_if(Verbosity.QUIET, msg, "SKIPPED: ", yellow=True)

    def verbosity0(self, msg, **opts):
        self.logline_if(Verbosity.DEFAULT, msg, **opts)

    def verbosity1(self, msg, **opts):
        self.logline_if(Verbosity.INFO, msg, **opts)

    def verbosity2(self, msg, **opts):
        self.logline_if(Verbosity.DEBUG, msg, **opts)
