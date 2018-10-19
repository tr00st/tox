from __future__ import print_function, unicode_literals

import sys

from tox.config import parseconfig
from tox.exception import MissingRequirement, MinVersionError
from tox.reporter import Reporter
from tox.util import set_os_env_var
from .help import show_help
from .help_ini import show_help_ini
from .core import Session


def prepare(args):
    config = parseconfig(args)
    if config.option.help:
        show_help(config)
        raise SystemExit(0)
    elif config.option.helpini:
        show_help_ini(config)
        raise SystemExit(0)
    return config


def cmdline(args=None):
    if args is None:
        args = sys.argv[1:]
    main(args)


def main(args):
    try:
        config = prepare(args)
        with set_os_env_var("TOX_WORK_DIR", config.toxworkdir):
            retcode = build_session(config).runcommand()
        if retcode is None:
            retcode = 0
        raise SystemExit(retcode)
    except KeyboardInterrupt:
        raise SystemExit(2)
    except (MinVersionError, MissingRequirement) as e:
        r = Reporter(None)
        r.error(str(e))
        raise SystemExit(1)


def build_session(config):
    return Session(config)
