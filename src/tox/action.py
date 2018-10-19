from __future__ import print_function, unicode_literals

import os
import pipes
import subprocess
import sys
import time

import py

from tox.constants import INFO
from tox.exception import InvocationError


class Action(object):
    def __init__(self, session, venv, msg, args):
        self.venv = venv
        self.msg = msg
        self.activity = msg.split(" ", 1)[0]
        self.session = session
        self.report = session.report
        self.args = args
        self.id = venv and venv.envconfig.envname or "tox"
        self._popenlist = []
        if self.venv:
            self.venvname = self.venv.name
        else:
            self.venvname = "GLOB"
        if msg == "runtests":
            cat = "test"
        else:
            cat = "setup"
        envlog = session.resultlog.get_envlog(self.venvname)
        self.commandlog = envlog.get_commandlog(cat)

    def __enter__(self):
        self.report.logaction_start(self)
        return self

    def __exit__(self, *args):
        self.report.logaction_finish(self)

    def setactivity(self, name, msg):
        self.activity = name
        if msg:
            self.report.verbosity0("{} {}: {}".format(self.venvname, name, msg), bold=True)
        else:
            self.report.verbosity1("{} {}: {}".format(self.venvname, name, msg), bold=True)

    def info(self, name, msg):
        self.report.verbosity1("{} {}: {}".format(self.venvname, name, msg), bold=True)

    def _initlogpath(self, actionid):
        if self.venv:
            logdir = self.venv.envconfig.envlogdir
        else:
            logdir = self.session.config.logdir
        try:
            log_count = len(logdir.listdir("{}-*".format(actionid)))
        except (py.error.ENOENT, py.error.ENOTDIR):
            logdir.ensure(dir=1)
            log_count = 0
        path = logdir.join("{}-{}.log".format(actionid, log_count))
        f = path.open("w")
        f.flush()
        return f

    def popen(self, args, cwd=None, env=None, redirect=True, returnout=False, ignore_ret=False):
        stdout = outpath = None
        resultjson = self.session.config.option.resultjson

        cmd_args = [str(x) for x in args]
        cmd_args_shell = " ".join(pipes.quote(i) for i in cmd_args)
        if resultjson or redirect:
            fout = self._initlogpath(self.id)
            fout.write(
                "actionid: {}\nmsg: {}\ncmdargs: {!r}\n\n".format(
                    self.id, self.msg, cmd_args_shell
                )
            )
            fout.flush()
            outpath = py.path.local(fout.name)
            fin = outpath.open("rb")
            fin.read()  # read the header, so it won't be written to stdout
            stdout = fout
        elif returnout:
            stdout = subprocess.PIPE
        if cwd is None:
            # FIXME XXX cwd = self.session.config.cwd
            cwd = py.path.local()
        try:
            popen = self._popen(args, cwd, env=env, stdout=stdout, stderr=subprocess.STDOUT)
        except OSError as e:
            self.report.error(
                "invocation failed (errno {:d}), args: {}, cwd: {}".format(
                    e.errno, cmd_args_shell, cwd
                )
            )
            raise
        popen.outpath = outpath
        popen.args = cmd_args
        popen.cwd = cwd
        popen.action = self
        self._popenlist.append(popen)
        try:
            self.report.logpopen(popen, cmd_args_shell)
            try:
                if resultjson and not redirect:
                    if popen.stderr is not None:
                        # prevent deadlock
                        raise ValueError("stderr must not be piped here")
                    # we read binary from the process and must write using a
                    # binary stream
                    buf = getattr(sys.stdout, "buffer", sys.stdout)
                    out = None
                    last_time = time.time()
                    while 1:
                        # we have to read one byte at a time, otherwise there
                        # might be no output for a long time with slow tests
                        data = fin.read(1)
                        if data:
                            buf.write(data)
                            if b"\n" in data or (time.time() - last_time) > 1:
                                # we flush on newlines or after 1 second to
                                # provide quick enough feedback to the user
                                # when printing a dot per test
                                buf.flush()
                                last_time = time.time()
                        elif popen.poll() is not None:
                            if popen.stdout is not None:
                                popen.stdout.close()
                            break
                        else:
                            time.sleep(0.1)
                            # the seek updates internal read buffers
                            fin.seek(0, 1)
                    fin.close()
                else:
                    out, err = popen.communicate()
            except KeyboardInterrupt:
                self.report.keyboard_interrupt()
                popen.wait()
                raise
            ret = popen.wait()
        finally:
            self._popenlist.remove(popen)
        if ret and not ignore_ret:
            invoked = " ".join(map(str, popen.args))
            if outpath:
                self.report.error(
                    "invocation failed (exit code {:d}), logfile: {}".format(ret, outpath)
                )
                out = outpath.read()
                self.report.error(out)
                if hasattr(self, "commandlog"):
                    self.commandlog.add_command(popen.args, out, ret)
                raise InvocationError("{} (see {})".format(invoked, outpath), ret)
            else:
                raise InvocationError("{!r}".format(invoked), ret)
        if not out and outpath:
            out = outpath.read()
        if hasattr(self, "commandlog"):
            self.commandlog.add_command(popen.args, out, ret)
        return out

    def _rewriteargs(self, cwd, args):
        newargs = []
        for arg in args:
            if not INFO.IS_WIN and isinstance(arg, py.path.local):
                arg = cwd.bestrelpath(arg)
            newargs.append(str(arg))
        # subprocess does not always take kindly to .py scripts so adding the interpreter here
        if INFO.IS_WIN:
            ext = os.path.splitext(str(newargs[0]))[1].lower()
            if ext == ".py" and self.venv:
                newargs = [str(self.venv.envconfig.envpython)] + newargs
        return newargs

    def _popen(self, args, cwd, stdout, stderr, env=None):
        if env is None:
            env = os.environ.copy()
        return self.session.popen(
            self._rewriteargs(cwd, args),
            shell=False,
            cwd=str(cwd),
            universal_newlines=True,
            stdout=stdout,
            stderr=stderr,
            env=env,
        )
