#               _         _      _               ____   _____      ___       ___
#   ___   __ _ | |  __ _ | |__  (_) _ __ ___    |___ \ |___ /     / _ \     / _ \
#  / __| / _` || | / _` || '_ \ | || '_ ` _ \     __) |  |_ \    | | | |   | | | |
#  \__ \| (_| || || (_| || |_) || || | | | | |   / __/  ___) | _ | |_| | _ | |_| |
#  |___/ \__,_||_| \__,_||_.__/ |_||_| |_| |_|  |_____||____/ (_) \___/ (_) \___/
#  Discrete event simulation in Python
#
#  see www.salabim.org for more information, the documentation and license information

__version__ = "23.0.0"

import heapq
import random
import time
import math
import array
import collections
import os
import inspect
import sys
import itertools
import io
import pickle
import logging
import types
import bisect
import operator
import ctypes
import shutil
import subprocess
import tempfile
import struct
import binascii
import operator
import copy
import numbers
import platform
import functools
import traceback
import contextlib
import datetime

from pathlib import Path


Pythonista = sys.platform == "ios"
Windows = sys.platform.startswith("win")
PyDroid = sys.platform == "linux" and any("pydroid" in v for v in os.environ.values())
Chromebook = "penguin" in platform.uname()


class g:
    pass


if Pythonista:
    try:
        import scene
        import ui
        import objc_util
    except ModuleNotFoundError:
        Pythonista = False  # for non Pythonista implementation on iOS

inf = float("inf")
nan = float("nan")


class QueueFullError(Exception):
    pass


class SimulationStopped(Exception):
    pass


class ItemFile:
    """
    define an item file to be used with read_item, read_item_int, read_item_float and read_item_bool

    Parameters
    ----------
    filename : str
        file to be used for subsequent read_item, read_item_int, read_item_float and read_item_bool calls |n|
        or |n|
        content to be interpreted used in subsequent read_item calls. The content should have at least one linefeed
        character and will be usually  triple quoted.

    Note
    ----
    It is advised to use ItemFile with a context manager, like ::

        with sim.ItemFile("experiment0.txt") as f:
            run_length = f.read_item_float() |n|
            run_name = f.read_item() |n|

    Alternatively, the file can be opened and closed explicitely, like ::

        f = sim.ItemFile("experiment0.txt")
        run_length = f.read_item_float()
        run_name = f.read_item()
        f.close()

    Item files consist of individual items separated by whitespace (blank or tab)|n|
    If a blank or tab is required in an item, use single or double quotes |n|
    All text following # on a line is ignored |n|
    All texts on a line within curly brackets {} is ignored and considered white space. |n|
    Curly braces cannot spawn multiple lines and cannot be nested.

    Example ::

        Item1
        "Item 2"
            Item3 Item4 # comment
        Item5 {five} Item6 {six}
        'Double quote" in item'
        "Single quote' in item"
        True
    """

    def __init__(self, filename):
        self.iter = self._nextread()
        if "\n" in filename:
            self.open_file = io.StringIO(filename)
        else:
            self.open_file = open(filename, "r")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.open_file.close()

    def close(self):
        self.open_file.close()

    def read_item_int(self):
        """
        read next field from the ItemFile as int.h

        if the end of file is reached, EOFError is raised
        """
        return int(self.read_item().replace(",", "."))

    def read_item_float(self):
        """
        read next item from the ItemFile as float

        if the end of file is reached, EOFError is raised
        """

        return float(self.read_item().replace(",", "."))

    def read_item_bool(self):
        """
        read next item from the ItemFile as bool

        A value of False (not case sensitive) will return False |n|
        A value of 0 will return False |n|
        The null string will return False |n|
        Any other value will return True

        if the end of file is reached, EOFError is raised
        """
        result = self.read_item().strip().lower()
        if result == "false":
            return False
        try:
            if float(result) == 0:
                return False
        except (ValueError, TypeError):
            pass
        if result == "":
            return False
        return True

    def read_item(self):
        """
        read next item from the ItemFile

        if the end of file is reached, EOFError is raised
        """
        try:
            return next(self.iter)
        except StopIteration:
            raise EOFError

    def _nextread(self):
        remove = "\r\n"
        quotes = "'\""

        for line in self.open_file:
            mode = "."
            result = ""
            for c in line:
                if c not in remove:
                    if mode in quotes:
                        if c == mode:
                            mode = "."
                            yield result  # even return the null string
                            result = ""
                        else:
                            result += c
                    elif mode == "{":
                        if c == "}":
                            mode = "."
                    else:
                        if c == "#":
                            break
                        if c in quotes:
                            if result:
                                yield result
                            result = ""
                            mode = c
                        elif c == "{":
                            if result:
                                yield result
                            result = ""
                            mode = c

                        elif c in (" ", "\t"):
                            if result:
                                yield result
                            result = ""
                        else:
                            result += c
            if result:
                yield result


class Monitor:
    """
    Monitor object

    Parameters
    ----------
    name : str
        name of the monitor |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

    monitor : bool
        if True (default), monitoring will be on. |n|
        if False, monitoring is disabled |n|
        it is possible to control monitoring later,
        with the monitor method

    level : bool
        if False (default), individual values are tallied, optionally with weight |n|
        if True, the tallied vslues are interpreted as levels

    initial_tally : any, preferably int, float or translatable into int or float
        initial value for the a level monitor |n|
        it is important to set the value correctly.
        default: 0 |n|
        not available for non level monitors

    type : str
        specifies how tallied values are to be stored
            - "any" (default) stores values in a list. This allows
               non numeric values. In calculations the values are
               forced to a numeric value (0 if not possible)
            - "bool" (True, False) Actually integer >= 0 <= 255 1 byte
            - "int8" integer >= -128 <= 127 1 byte
            - "uint8" integer >= 0 <= 255 1 byte
            - "int16" integer >= -32768 <= 32767 2 bytes
            - "uint16" integer >= 0 <= 65535 2 bytes
            - "int32" integer >= -2147483648<= 2147483647 4 bytes
            - "uint32" integer >= 0 <= 4294967295 4 bytes
            - "int64" integer >= -9223372036854775808 <= 9223372036854775807 8 bytes
            - "uint64" integer >= 0 <= 18446744073709551615 8 bytes
            - "float" float 8 bytes

    weight_legend : str
        used in print_statistics and print_histogram to indicate the dimension of weight or duration (for
        level monitors, e.g. minutes. Default: weight for non level monitors, duration for level monitors.

    stats_only : bool
        if True, only statistics will be collected (using less memory, but also less functionality) |n|
        if False (default), full functionality |n|

    fill : list or tuple
        can be used to fill the tallied values (all at time now). |n|
        fill is only available for non level and not stats_only monitors. |n|

    env : Environment
        environment where the monitor is defined |n|
        if omitted, default_env will be used
    """

    cached_xweight = {(ex0, force_numeric): (0, 0) for ex0 in (False, True) for force_numeric in (False, True)}

    def __init__(
        self, name=None, monitor=True, level=False, initial_tally=None, type=None, weight_legend=None, fill=None, stats_only=False, env=None, *args, **kwargs
    ):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        if isinstance(self.env, Environment):
            _set_name(name, self.env._nameserializeMonitor, self)
        else:
            self._name = name
        self._level = level
        self._weight_legend = ("duration" if self._level else "weight") if weight_legend is None else weight_legend
        if self._level:
            if weight_legend is None:
                self.weight_legend = "duration"
            else:
                self.weight_legend = weight_legend
            if initial_tally is None:
                self._tally = 0
            else:
                self._tally = initial_tally
            self._ttally = self.env._now
        else:
            if initial_tally is not None:
                raise TypeError("initial_tally not available for non level monitors")
            if weight_legend is None:
                self.weight_legend = "weight"
            else:
                self.weight_legend = weight_legend

        if type is None:
            type = "any"
        try:
            self.xtypecode, self.off = type_to_typecode_off(type)
        except KeyError:
            raise ValueError("type '" + type + "' not recognized")
        self.xtype = type
        self._stats_only = stats_only
        self.isgenerated = False
        self.reset(monitor)
        if fill is not None:
            if self._level:
                raise ValueError("fill is not supported for level monitors")
            if self._stats_only:
                raise ValueError("fill is not supported for stats_only monitors")
            self._x.extend(fill)
            self._t.extend(len(fill) * [self.env._now])

        self.setup(*args, **kwargs)

    def __add__(self, other):
        self._block_stats_only()
        if not isinstance(other, Monitor):
            return NotImplemented
        other._block_stats_only()
        return self.merge(other)

    def __radd__(self, other):
        self._block_stats_only()
        if other == 0:  # to be able to use sum
            return self
        if not isinstance(other, Monitor):
            return NotImplemented
        other._block_stats_only()
        return self.merge(other)

    def __mul__(self, other):
        self._block_stats_only()
        try:
            other = float(other)
        except Exception:
            return NotImplemented
        return self.multiply(other)

    def __rmul__(self, other):
        self._block_stats_only()
        return self * other

    def __truediv__(self, other):
        self._block_stats_only()
        try:
            other = float(other)
        except Exception:
            return NotImplemented
        return self * (1 / other)

    def _block_stats_only(self):
        if self._stats_only:
            frame = inspect.stack()[1][0]
            function = inspect.getframeinfo(frame).function
            if function == "__init__":
                function = frame.f_locals["self"].__class__.__name__
            raise NotImplementedError(function + " not available for " + self.name() + " because it is stats_only")

    def stats_only(self):
        return self._stats_only

    def merge(self, *monitors, **kwargs):
        """
        merges this monitor with other monitor(s)

        Parameters
        ----------
        monitors : sequence
           zero of more monitors to be merged to this monitor

        name : str
            name of the merged monitor |n|
            default: name of this monitor + ".merged"

        Returns
        -------
        merged monitor : Monitor

        Note
        ----
        Level monitors can only be merged with level monitors |n|
        Non level monitors can only be merged with non level monitors |n|
        Only monitors with the same type can be merged |n|
        If no monitors are specified, a copy is created. |n|
        For level monitors, merging means summing the available x-values|n|
        """
        self._block_stats_only()
        name = kwargs.pop("name", None)
        if kwargs:
            raise TypeError("merge() got an unexpected keyword argument '" + tuple(kwargs)[0] + "'")

        for m in monitors:
            m._block_stats_only()
            if not isinstance(m, Monitor):
                raise TypeError("not possible to merge monitor with " + object_to_str(m, True) + " type")
            if self._level != m._level:
                raise TypeError("not possible to mix level monitor with non level monitor")
            if self.xtype != m.xtype:
                raise TypeError("not possible to mix type '" + self.xtype + "' with type '" + m.xtype + "'")
            if self.env != m.env:
                raise TypeError("not possible to mix environments")
        if name is None:
            if self.name().endswith(".merged"):
                # this to avoid multiple .merged (particularly when merging with the + operator)
                name = self.name()
            else:
                name = self.name() + ".merged"

        new = _SystemMonitor(name=name, type=self.xtype, level=self._level, env=self.env)

        merge = [self] + list(monitors)

        if new._level:
            if new.xtypecode:
                new._x = array.array(self.xtypecode)
            else:
                new._x = []

            curx = [new.off] * len(merge)
            new._t = array.array("d")
            for t, index, x in heapq.merge(*[zip(merge[index]._t, itertools.repeat(index), merge[index]._x) for index in range(len(merge))]):
                if new.xtypecode:
                    curx[index] = x
                else:
                    try:
                        curx[index] = float(x)
                    except (ValueError, TypeError):
                        curx[index] = 0

                sum = 0
                for xi in curx:
                    if xi == new.off:
                        sum = new.off
                        break
                    sum += xi

                if new._t and (t == new._t[-1]):
                    new._x[-1] = sum
                else:
                    new._t.append(t)
                    new._x.append(sum)
            new.start = new._t[0]
        else:
            for t, _, x, weight in heapq.merge(
                *[
                    zip(
                        merge[index]._t, itertools.repeat(index), merge[index]._x, merge[index]._weight if merge[index]._weight else (1,) * len(merge[index]._x)
                    )
                    for index in range(len(merge))
                ]
            ):
                if weight == 1:
                    if new._weight:
                        new._weight.append(weight)
                else:
                    if not new._weight:
                        new._weight = array.array("d", (1,) * len(new._x))
                    new._weight.append(weight)
                new._t.append(t)
                new._x.append(x)
        new.monitor(False)
        new.isgenerated = True
        return new

    def t_multiply(self, factor, name=None):
        if name is None:
            name = "mapped"

        if not self._level:
            raise TypeError("t_multiply can't be applied to non level monitors")

        if factor <= 0:
            raise TypeError(f"factor {factor} <= 0")

        new = _SystemMonitor(name=name, type=self.xtype, level=self._level, env=self.env)
        new._x = []
        new._t = []
        for x in self._x:
            new._x.append(x)
        for t in self._t:
            new._t.append(t * factor)

        new.start = self.start * factor
        new.monitor(False)
        new._t[-1] = new._t[-1] * factor
        new.isgenerated = True
        return new

    def x_map(self, func, monitors=[], name=None):
        """
        maps a function to the x-values of the given monitors (static method)

        Parameters
        ----------
        func : function
           a function that accepts n x-values, where n is the number of monitors
           note that the function will not be called during the time any of the monitors is off

        monitors : list/tuple of additional monitors
           monitor(s) to be mapped |n|
           only allowed for level monitors-

        name : str
            name of the mapped monitor |n|
            default: "mapped"

        Returns
        -------
        mapped monitor : Monitor, type 'any'
        """
        if name is None:
            name = "mapped"

        if monitors is not None:
            monitors = [self] + monitors
        else:
            monitors = [self]
        if not all(m._level == self._level for m in monitors):
            raise TypeError("not possible to mix level and non level monitors")
        if not all(m.env == self.env for m in monitors):
            raise TypeError("not all monitors have this environment")

        new = _SystemMonitor(name=name, type="any", level=self._level, env=self.env)

        for m in monitors:
            m._x_any = []
            for x in m._x:
                m._x_any.append(new.off if x == m.off else x)

        if new._level:
            new._x = []

            curx = [new.off] * len(monitors)
            new._t = array.array("d")
            for t, index, x in heapq.merge(*[zip(monitors[index]._t, itertools.repeat(index), monitors[index]._x_any) for index in range(len(monitors))]):
                curx[index] = x

                if any(val == new.off for val in curx):
                    result = new.off
                else:
                    result = func(*curx)

                if new._t and (t == new._t[-1]):
                    new._x[-1] = result
                else:
                    new._t.append(t)
                    new._x.append(result)
            new.start = new._t[0]
        else:
            new._x = []
            new._t = array.array("d")

            for x, t in zip(monitors[0]._x_any, monitors[0]._t):
                if x == new.off:
                    new._x.append(new.off)
                else:
                    new._x.append(func(x))
                new._t.append(t)

        for m in monitors:
            del m._x_any

        new.monitor(False)
        new.isgenerated = True
        return new

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.slice(key.start, key.stop, key.step)
        else:
            return self.slice(key)

    def freeze(self, name=None):
        """
        freezes this monitor (particularly useful for pickling)

        Parameters
        ----------
        name : str
            name of the frozen monitor |n|
            default: name of this monitor + ".frozen"

        Returns
        -------
        frozen monitor : Monitor

        Notes
        -----
        The env attribute will become a partial copy of the original environment, with the name
        of the original environment, padded with '.copy.<serial number>'
        """
        self._block_stats_only()
        self_env = self.env
        self.env = Environment(to_freeze=True, name=self.env.name() + ".copy.", time_unit=self.env.get_time_unit())
        m = copy.deepcopy(self)
        self.env = self_env
        m.isgenerated = True
        m._name = self.name() + ".frozen" if name is None else name
        m.env._animate = False
        m.env._now = self.env._now
        m.env._offset = self.env._offset
        m.env._t = self.env._t
        return m

    def slice(self, start=None, stop=None, modulo=None, name=None):
        """
        slices this monitor (creates a subset)

        Parameters
        ----------
        start : float
           if modulo is not given, the start of the slice |n|
           if modulo is given, this is indicates the slice period start (modulo modulo)

        stop : float
           if modulo is not given, the end of the slice |n|
           if modulo is given, this is indicates the slice period end (modulo modulo) |n|
           note that stop is excluded from the slice (open at right hand side)

        modulo : float
            specifies the distance between slice periods |n|
            if not specified, just one slice subset is used.

        name : str
            name of the sliced monitor |n|
            default: name of this monitor + ".sliced"

        Returns
        -------
        sliced monitor : Monitor

        Note
        ----
        It is also possible to use square bracktets to slice, like m[0:1000].
        """
        self._block_stats_only()
        if name is None:
            name = self.name() + ".sliced"
        new = _SystemMonitor(level=self._level, type=self.xtype, name=name, env=self.env)
        actions = []
        if modulo is None:
            if start is None:
                start = -inf
            else:
                start += self.env._offset
            start = max(start, self.start)
            if stop is None:
                stop = inf
                stop_action = "z"  # inclusive
            else:
                stop += self.env._offset
                stop_action = "b"  # non inclusive

            stop = min(stop, self.env._now - self.env._offset)  # not self.now() in order to support frozen monitors
            actions.append((start, "a", 0, 0))
            actions.append((stop, stop_action, 0, 0))
        else:
            if start is None:
                raise TypeError("modulo specified, but no start specified. ")
            if stop is None:
                raise TypeError("modulo specified, but no stop specified")
            if stop <= start:
                raise ValueError("stop must be > start")
            if stop - start >= modulo:
                raise ValueError("stop must be < start + modulo")
            start = start % modulo
            stop = stop % modulo
            start1 = self._t[0] - (self._t[0] % modulo) + start
            len1 = (stop - start) % modulo
            while start1 < self.env._now:
                actions.append((start1, "a", 0, 0))
                actions.append((start1 + len1, "b", 0, 0))  # non inclusive
                start1 += modulo

        if new._level:
            if new.xtypecode:
                new._x = array.array(self.xtypecode)
            else:
                new._x = []
            new._t = array.array("d")
            curx = new.off
            new._t.append(self.start)
            new._x.append(curx)

        enabled = False
        for (t, type, x, weight) in heapq.merge(
            actions, zip(self._t, itertools.repeat("c"), self._x, self._weight if (self._weight and not self._level) else (1,) * len(self._x))
        ):
            if new._level:
                if type == "a":
                    enabled = True
                    if new._t[-1] == t:
                        new._x[-1] = curx
                    else:
                        if new._x[-1] == curx:
                            new._t[-1] = t
                        else:
                            new._t.append(t)
                            new._x.append(curx)
                elif type in ("b", "z"):
                    enabled = False
                    if new._t[-1] == t:
                        new._x[-1] = self.off
                    else:
                        if new._x[-1] == self.off:
                            new._t[-1] = t
                        else:
                            new._t.append(t)
                            new._x.append(self.off)
                else:
                    if enabled:
                        if curx != x:
                            if new._t[-1] == t:
                                new._x[-1] = x
                            else:
                                if x == new._x[-1]:
                                    new._t[-1] = t
                                else:
                                    new._t.append(t)
                                    new._x.append(x)
                    curx = x
            else:
                if type == "a":
                    enabled = True
                elif type in ("b", "z"):
                    enabled = False
                else:
                    if enabled:
                        if weight == 1:
                            if new._weight:
                                new._weight.append(weight)
                        else:
                            if not new._weight:
                                new._weight = array.array("d", (1,) * len(new._x))
                            new._weight.append(weight)
                        new._t.append(t)
                        new._x.append(x)
        new.monitor(False)
        new.isgenerated = True
        return new

    def setup(self):
        """
        called immediately after initialization of a monitor.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        """
        pass

    def register(self, registry):
        """
        registers the monitor in the registry

        Parameters
        ----------
        registry : list
            list of (to be) registered objects

        Returns
        -------
        monitor (self) : Monitor

        Note
        ----
        Use Monitor.deregister if monitor does not longer need to be registered.
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self in registry:
            raise ValueError(self.name() + " already in registry")
        registry.append(self)
        return self

    def deregister(self, registry):
        """
        deregisters the monitor in the registry

        Parameters
        ----------
        registry : list
            list of registered objects

        Returns
        -------
        monitor (self) : Monitor
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self not in registry:
            raise ValueError(self.name() + " not in registry")
        registry.remove(self)
        return self

    def __repr__(self):
        return (
            object_to_str(self)
            + ("[level]" if self._level else "")
            + " ("
            + self.name()
            + ")"
            + ("[stats_only]" if self._stats_only else "")
            + " ("
            + self.name()
            + ")"
        )

    def __call__(self, t=None):  # direct moneypatching __call__ doesn't work
        if not self._level:
            raise TypeError("get not available for non level monitors")
        if t is None:
            return self._tally
        t += self.env._offset
        if t == self.env._now:
            return self._tally  # even if monitor is off, the current value is valid
        if self._stats_only:
            raise NotImplementedError("__call__(t) not supported for stats_only monitors")
        if t < self._t[0]:
            return self.off
        i = bisect.bisect_left(list(zip(self._t, itertools.count())), (t, float("inf")))
        return self._x[i - 1]

    def get(self, t=None):
        """
        get the value of a level monitor

        Parameters
        ----------
        t : float
            time at which the value of the level is to be returned |n|
            default: now

        Returns
        -------
        last tallied value : any, usually float

            Instead of this method, the level monitor can also be called directly, like |n|

            level = sim.Monitor("level", level=True) |n|
            ... |n|
            print(level()) |n|
            print(level.get())  # identical |n|

        Note
        ----
        If the value is not available, self.off will be returned. |n|
        Only available for level monitors
        """
        return self.__call__(t)

    @property
    def value(self):
        """
        get/set the value of a level monitor

        :getter:
            gets the last tallied value : any (often float)

        :setter:
            equivalent to m.tally()

        Note
        ----
        value is only available for level monitors |n|
        value is available even if the monitor is turned off
        """
        if self._level:
            return self._tally
        raise TypeError("non level monitors are not supported")

    @value.setter
    def value(self, value):
        if self._level:
            self.tally(value)
        else:
            raise TypeError("non level monitors are not supported")

    def t(self):
        """
        get the time of last tally of a level monitor

        :getter:
            gets the time of the last tallied value : float

        Note
        ----
        t is only available for level monitors |n|
        t is available even if the monitor is turned off
        """
        if self._level:
            return self._ttally
        raise TypeError("non level monitors are not supported")

    def reset_monitors(self, monitor=None, stats_only=None):
        """
        resets monitor

        Parameters
        ----------
        monitor : bool
            if True (default), monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, the monitor state remains unchanged

        stats_only : bool
            if True, only statistics will be collected (using less memory, but also less functionality) |n|
            if False, full functionality |n|
            if omittted, no change of stats_only

        Note
        ----
        Exactly same functionality as Monitor.reset()
        """
        self.reset(monitor=monitor, stats_only=stats_only)

    def reset(self, monitor=None, stats_only=None):
        """
        resets monitor

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled
            if omitted, no change of monitoring state

        stats_only : bool
            if True, only statistics will be collected (using less memory, but also less functionality) |n|
            if False, full functionality |n|
            if omittted, no change of stats_only
        """
        if self.isgenerated:
            raise TypeError("sliced, merged or frozen monitors cannot be reset")
        if monitor is not None:
            self._monitor = monitor
        if stats_only is not None:
            self._stats_only = stats_only
        self.start = self.env._now
        if self._stats_only:  # all values for ex0=False and ex0=True
            self.mun = [0] * 2
            self.n = [0] * 2
            self.sn = [0] * 2
            self.sumw = [0] * 2
            self._minimum = [inf] * 2
            self._maximum = [-inf] * 2
            if self._level:
                self._ttally_monitored = self.env._now
            self._weight = False

        else:
            if self.xtypecode:
                self._x = array.array(self.xtypecode)
            else:
                self._x = []
            self._t = array.array("d")
            self._weight = False
            if self._level:
                self._weight = True  # signal for statistics that weights are present (although not stored in _weight)
                if self._monitor:
                    self._x.append(self._tally)
                else:
                    self._x.append(self.off)
                self._t.append(self.env._now)
            else:
                self._weight = False  # weights are only stored if there is a non 1 weight
            Monitor.cached_xweight = {(ex0, force_numeric): (0, 0) for ex0 in (False, True) for force_numeric in (False, True)}  # invalidate the cache

        self.monitor(monitor)

    def monitor(self, value=None):
        """
        enables/disables monitor

        Parameters
        ----------
        value : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change

        Returns
        -------
        True, if monitoring enabled. False, if not : bool
        """
        if self._stats_only:
            if value is not None:
                if self._monitor:
                    if self._level:
                        self._tally_add_now()

                self._ttally_monitored = self.env._now

                self._monitor = value
        else:

            if value is not None:
                if value and self.isgenerated:
                    raise TypeError("sliced, merged or frozen monitors cannot be turned on")
                self._monitor = value
                if self._level:
                    if self._monitor:
                        self.tally(self._tally)
                    else:
                        self._tally_off()  # can't use tally() here because self._tally should be untouched
        return self.monitor

    def start_time(self):
        """
        Returns
        -------
        Start time of the monitor : float
             either the time of creation or latest reset
        """
        return self.start - self.env._offset

    def tally(self, value, weight=1):
        """
        Parameters
        ----------
        x : any, preferably int, float or translatable into int or float
            value to be tallied

        weight: float
            weight to be tallied |n|
            default : 1 |n|
        """
        if self.isgenerated:
            raise TypeError("sliced, merged or frozen monitors cannot be reset")

        if self._stats_only:
            if self._level:
                if weight != 1:
                    raise ValueError("level monitor supports only weight=1, not: " + str(weight))
                if self._monitor:
                    weight = self.env._now - self._ttally_monitored
                    value_num = self._tally
                    self._ttally_monitored = self.env._now
                self._tally = value
                self._ttally = self.env._now

            else:
                value_num = value

            if self._monitor and weight != 0:
                if not isinstance(value_num, numbers.Number):
                    try:
                        if int(value_num) == float(value_num):
                            value_num = int(value_num)
                        else:
                            value_num = float(value_num)
                    except (ValueError, TypeError):
                        value_num = 0

                for ex0 in [False, True] if value_num else [False]:
                    self.n[ex0] += 1
                    # algorithm based on https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
                    self.sumw[ex0] += weight
                    mun1 = self.mun[ex0]
                    self.mun[ex0] = mun1 + (weight / self.sumw[ex0]) * (value_num - mun1)
                    self.sn[ex0] = self.sn[ex0] + weight * (value_num - mun1) * (value_num - self.mun[ex0])
                    self._minimum[ex0] = min(self._minimum[ex0], value_num)
                    self._maximum[ex0] = max(self._maximum[ex0], value_num)
                if weight != 1:
                    self._weight = True

        else:
            if self._level:
                if weight != 1:
                    if self._level:
                        raise ValueError("level monitor supports only weight=1, not: " + str(weight))
                if value == self.off:
                    raise ValueError("not allowed to tally " + str(self.off) + " (off)")
                self._tally = value
                self._ttally = self.env._now

                if self._monitor:
                    t = self.env._now
                    if self._t[-1] == t:
                        self._x[-1] = value
                    else:
                        self._x.append(value)
                        self._t.append(t)
            else:
                if self._monitor:
                    if weight == 1:
                        if self._weight:
                            self._weight.append(weight)
                    else:
                        if not self._weight:
                            self._weight = array.array("d", (1,) * len(self._x))
                        self._weight.append(weight)
                    self._x.append(value)
                    self._t.append(self.env._now)

    def _tally_add_now(self):  # used by stats_only level monitors
        save_ttally = self._ttally
        self.tally(self._tally)
        self._ttally = save_ttally

    def _tally_off(self):
        if self.isgenerated:
            raise TypeError("sliced, merged or frozen monitors cannot be reset")
        t = self.env._now
        if self._t[-1] == t:
            self._x[-1] = self.off
        else:
            self._x.append(self.off)
            self._t.append(t)

    def to_years(self, name=None):
        """
        makes a monitor with all x-values converted to years

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("years", name=name)

    def to_weeks(self, name=None):
        """
        makes a monitor with all x-values converted to weeks

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("weeks", name=name)

    def to_days(self, name=None):
        """
        makes a monitor with all x-values converted to days

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("days", name=name)

    def to_hours(self, name=None):
        """
        makes a monitor with all x-values converted to hours

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("hours", name=name)

    def to_minutes(self, name=None):
        """
        makes a monitor with all x-values converted to minutes

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("minutes", name=name)

    def to_seconds(self, name=None):
        """
        makes a monitor with all x-values converted to seconds

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("seconds", name=name)

    def to_milliseconds(self, name=None):
        """
        makes a monitor with all x-values converted to milliseconds

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("milliseconds", name=name)

    def to_microseconds(self, name=None):
        """
        makes a monitor with all x-values converted to microseconds

        Parameters
        ----------
        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.to_time_unit("microseconds", name=name)

    def to_time_unit(self, time_unit, name=None):
        """
        makes a monitor with all x-values converted to the specified time unit

        Parameters
        ----------
        time_unit : str
            Supported time_units: |n|
            "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds"

        name : str
            name of the converted monitor |n|
            default: name of this monitor

        Returns
        -------
        converted monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be converted. |n|
        It is required that a time_unit is defined for the environment.
        """
        self._block_stats_only()
        self.env._check_time_unit_na()
        return self.multiply(_time_unit_lookup(time_unit) / self.env._time_unit, name=name)

    def multiply(self, scale=1, name=None):
        """
        makes a monitor with all x-values multiplied with scale

        Parameters
        ----------
        scale : float
           scale to be applied

        name : str
            name of the multiplied monitor |n|
            default: name of this monitor

        Returns
        -------
        multiplied monitor : Monitor

        Note
        ----
        Only non level monitors with type float can be multiplied |n|
        """
        self._block_stats_only()
        if self._level:
            raise ValueError("level monitors can't be multiplied")

        if self.xtype == "float":
            if name is None:
                name = self.name()
            new = _SystemMonitor(name=name, monitor=False, type="float", level=False, env=self.env)
            new.isgenerated = True
            new._x = [x * scale for x in self._x]
            new._t = [t for t in self._t]
            return new

        else:
            raise ValueError("type", self.xtype, " monitors can't be multiplied (only float)")

    def name(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the monitor
            if omitted, no change

        Returns
        -------
        Name of the monitor : str

        Note
        ----
        base_name and sequence_number are not affected if the name is changed
        """
        if value is not None:
            self._name = value
        return self._name

    def rename(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the monitor
            if omitted, no change

        Returns
        -------
        self : monitor

        Note
        ----
        in contrast to name(), this method returns itself, so can used to chain, e.g. |n|
        (m0 + m1 + m2+ m3).rename('m0-m3').print_histograms() |n|
        m0[1000 : 2000].rename('m between t=1000 and t=2000').print_histograms() |n|
        """
        self.name(value)
        return self

    def base_name(self):
        """
        Returns
        -------
        base name of the monitor (the name used at initialization): str
        """
        return self._base_name

    def sequence_number(self):
        """
        Returns
        -------
        sequence_number of the monitor : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        """
        return self._sequence_number

    def mean(self, ex0=False):
        """
        mean of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        mean : float

        Note
        ----
        If weights are applied , the weighted mean is returned
        """
        if self._stats_only:
            ex0 = bool(ex0)
            if self._level:
                self._tally_add_now()
            if self.sumw[ex0]:
                return self.mun[ex0]
            else:
                return nan
        else:
            x, weight = self._xweight(ex0=ex0)
            sumweight = sum(weight)
            if sumweight:
                return sum(vx * vweight for vx, vweight in zip(x, weight)) / sumweight
            else:
                return nan

    def std(self, ex0=False):
        """
        standard deviation of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        standard deviation : float

        Note
        ----
        If weights are applied, the weighted standard deviation is returned
        """
        if self._stats_only:
            ex0 = bool(ex0)
            if self._level:
                self._tally_add_now()
            if self.sumw[ex0]:
                return math.sqrt(self.sn[ex0] / self.sumw[ex0])
            else:
                return nan
        else:
            x, weight = self._xweight(ex0=ex0)
            sumweight = sum(weight)
            if sumweight:
                wmean = self.mean(ex0=ex0)
                wvar = sum((vweight * (vx - wmean) ** 2) for vx, vweight in zip(x, weight)) / sumweight
                return math.sqrt(wvar)
            else:
                return nan

    def minimum(self, ex0=False):
        """
        minimum of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        minimum : float
        """
        if self._stats_only:
            ex0 = bool(ex0)
            if self.n[ex0]:
                return self._minimum[ex0]
            else:
                return nan
        else:
            x = self._xweight(ex0=ex0)[0]
            if x:
                return min(x)
            else:
                return nan

    def maximum(self, ex0=False):
        """
        maximum of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        maximum : float
        """

        if self._stats_only:
            if self.n[ex0]:
                return self._maximum[ex0]
            else:
                return nan
        else:
            x = self._xweight(ex0=ex0)[0]
            if x:
                return max(x)
            else:
                return nan

    def median(self, ex0=False, interpolation="linear"):
        """
        median of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        interpolation : str
            Default: 'linear' |n|
            |n|
            For non weighted monitors: |n|
            This optional parameter specifies the interpolation method to use when the 50% percentile lies between two data points i < j: |n|
            ‘linear’: i + (j - i) * fraction, where fraction is the fractional part of the index surrounded by i and j. (default for monitors that are not weighted not level|n|
            ‘lower’: i. |n|
            ‘higher’: j. (default for weighted and level monitors) |n|
            ‘nearest’: i or j, whichever is nearest. |n|
            ‘midpoint’: (i + j) / 2. |n|
            |n|
            For weighted and level monitors: |n|
            This optional parameter specifies the interpolation method to use when the 50% percentile corresponds exactly to two data points i and j |n|
            ‘linear’: (i + j) /2 |n|
            ‘lower’: i. |n|
            ‘higher’: j |n|
            ‘midpoint’: (i + j) / 2. |n|

        Returns
        -------
        median (50% percentile): float
        """
        return self.percentile(50, ex0=ex0, interpolation=interpolation)

    def percentile(self, q, ex0=False, interpolation="linear"):
        """
        q-th percentile of tallied values

        Parameters
        ----------
        q : float
            percentage of the distribution |n|
            values <0 are treated a 0 |n|
            values >100 are treated as 100

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        interpolation : str
            Default: 'linear' |n|
            |n|
            For non weighted monitors: |n|
            This optional parameter specifies the interpolation method to use when the desired percentile lies between two data points i < j: |n|
            ‘linear’: i + (j - i) * fraction, where fraction is the fractional part of the index surrounded by i and j. (default for monitors that are not weighted not level|n|
            ‘lower’: i. |n|
            ‘higher’: j. (default for weighted and level monitors) |n|
            ‘nearest’: i or j, whichever is nearest. |n|
            ‘midpoint’: (i + j) / 2. |n|
            |n|
            For weighted and level monitors: |n|
            This optional parameter specifies the interpolation method to use when the percentile corresponds exactly to two data points i and j |n|
            ‘linear’: (i + j) /2 |n|
            ‘lower’: i. |n|
            ‘higher’: j |n|
            ‘midpoint’: (i + j) / 2. |n|

        Returns
        -------
        q-th percentile : float
             0 returns the minimum, 50 the median and 100 the maximum
        """
        self._block_stats_only()

        if interpolation not in (("linear", "lower", "higher", "midpoint") if self._weight else ("linear", "lower", "higher", "midpoint", "nearest")):
            raise ValueError("incorrect interpolation method " + str(interpolation))

        q = max(0, min(q, 100))
        if q == 0:
            return self.minimum(ex0=ex0)
        if q == 100:
            return self.maximum(ex0=ex0)
        q /= 100
        x, weight = self._xweight(ex0=ex0)

        if len(x) == 1:
            return x[0]

        sum_weight = sum(weight)
        if not sum_weight:
            return nan

        x_sorted, weight_sorted = zip(*sorted(zip(x, weight), key=lambda v: v[0]))
        n = len(x_sorted)

        if self._weight:
            weight_cum = []
            cum = 0
            for k in range(n):
                cum += weight_sorted[k]
                weight_cum.append(cum / sum_weight)
            for k in range(n):
                if weight_cum[k] >= q:
                    break
            if weight_cum[k] != q:
                return x_sorted[k]

            if interpolation in ("linear", "midpoint"):
                return (x_sorted[k] + x_sorted[k + 1]) / 2
            if interpolation in ("lower"):
                return x_sorted[k]
            if interpolation == "higher":
                return x_sorted[k + 1]

        else:
            weight_cum = []
            for k in range(n):
                weight_cum.append(k / (n - 1))
            for k in range(n):
                if weight_cum[k + 1] > q:
                    break

            if interpolation == "linear":
                return interpolate(q, weight_cum[k], weight_cum[k + 1], x_sorted[k], x_sorted[k + 1])
            if interpolation == "lower":
                return x_sorted[k]
            if interpolation == "higher":
                return x_sorted[k + 1]
            if interpolation == "midpoint":
                return (x_sorted[k] + x_sorted[k + 1]) / 2
            if interpolation == "nearest":
                if q - weight_cum[k] <= weight_cum[k + 1] - q:
                    return x_sorted[k]
                else:
                    return x_sorted[k + 1]

    def bin_number_of_entries(self, lowerbound, upperbound, ex0=False):
        """
        count of the number of tallied values in range (lowerbound,upperbound]

        Parameters
        ----------
        lowerbound : float
            non inclusive lowerbound

        upperbound : float
            inclusive upperbound

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        number of values >lowerbound and <=upperbound : int

        Note
        ----
        Not available for level monitors
        """
        self._block_stats_only()
        if self._level:
            raise TypeError("bin_number_of_entries not available for level monitors")
        x = self._xweight(ex0=ex0)[0]
        return sum(1 for vx in x if (vx > lowerbound) and (vx <= upperbound))

    def bin_weight(self, lowerbound, upperbound):
        """
        total weight of tallied values in range (lowerbound,upperbound]

        Parameters
        ----------
        lowerbound : float
            non inclusive lowerbound

        upperbound : float
            inclusive upperbound

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        total weight of values >lowerbound and <=upperbound : int

        Note
        ----
        Not available for level monitors
        """
        self._block_stats_only()
        if self._level:
            raise TypeError("bin_weight not available for level monitors")
        return self.sys_bin_weight(lowerbound, upperbound)

    def bin_duration(self, lowerbound, upperbound):
        """
        total duration of tallied values in range (lowerbound,upperbound]

        Parameters
        ----------
        lowerbound : float
            non inclusive lowerbound

        upperbound : float
            inclusive upperbound

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        total duration of values >lowerbound and <=upperbound : int

        Note
        ----
        Not available for level monitors
        """
        self._block_stats_only()
        if not self._level:
            raise TypeError("bin_duration not available for non level monitors")
        return self.sys_bin_weight(lowerbound, upperbound)

    def sys_bin_weight(self, lowerbound, upperbound):
        x, weight = self._xweight()
        return sum((vweight for vx, vweight in zip(x, weight) if (vx > lowerbound) and (vx <= upperbound)))

    def value_number_of_entries(self, value):
        """
        count of the number of tallied values equal to value or in value

        Parameters
        ----------
        value : any
            if list, tuple or set, check whether the tallied value is in value |n|
            otherwise, check whether the tallied value equals the given value

        Returns
        -------
        number of tallied values in value or equal to value : int

        Note
        ----
        Not available for level monitors
        """
        self._block_stats_only()
        if self._level:
            raise TypeError("value_number_of_entries not available for level monitors")
        if isinstance(value, str):
            value = [value]
        try:
            iter(value)  # iterable?
            values = value
        except TypeError:
            values = [value]

        x = self._xweight(force_numeric=False)[0]
        return sum(1 for vx in x if (vx in values))

    def value_weight(self, value):
        """
        total weight of tallied values equal to value or in value

        Parameters
        ----------
        value : any
            if list, tuple or set, check whether the tallied value is in value |n|
            otherwise, check whether the tallied value equals the given value

        Returns
        -------
        total of weights of tallied values in value or equal to value : int

        Note
        ----
        Not available for level monitors
        """
        self._block_stats_only()
        if self._level:
            raise TypeError("value_weight not supported for level monitors")
        return self.sys_value_weight(value)

    def value_duration(self, value):
        """
        total duration of tallied values equal to value or in value

        Parameters
        ----------
        value : any
            if list, tuple or set, check whether the tallied value is in value |n|
            otherwise, check whether the tallied value equals the given value

        Returns
        -------
        total of duration of tallied values in value or equal to value : float

        Note
        ----
        Not available for non level monitors
        """
        self._block_stats_only()
        if not self._level:
            raise TypeError("value_weight not available for non level monitors")
        return self.sys_value_weight(value)

    def sys_value_weight(self, value):
        x, weight = self._xweight(force_numeric=False)

        if isinstance(value, str):
            value = [value]
        try:
            iter(value)  # iterable?
            values = value
        except TypeError:
            values = [value]

        return sum(vweight for (vx, vweight) in zip(x, weight) if vx in values)

    def number_of_entries(self, ex0=False):
        """
        count of the number of entries

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        number of entries : int

        Note
        ----
        Not available for level monitors
        """
        if self._level:
            raise TypeError("number_of_entries not available for level monitors")
        if self._stats_only:
            ex0 = bool(ex0)
            return self.n[ex0]
        else:
            x = self._xweight(ex0=ex0)[0]
            return len(x)

    def number_of_entries_zero(self):
        """
        count of the number of zero entries

        Returns
        -------
        number of zero entries : int

        Note
        ----
        Not available for level monitors
        """
        if self._level:
            raise TypeError("number_of_entries_zero not available for level monitors")
        return self.number_of_entries() - self.number_of_entries(ex0=True)

    def weight(self, ex0=False):
        """
        sum of weights

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        sum of weights : float

        Note
        ----
        Not available for level monitors
        """
        if self._level:
            raise TypeError("weight not available for level monitors")
        return self.sys_weight(ex0)

    def duration(self, ex0=False):
        """
        total duration

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        total duration : float

        Note
        ----
        Not available for non level monitors
        """
        if not self._level:
            raise TypeError("duration not available for non level monitors")
        return self.sys_weight(ex0)

    def sys_weight(self, ex0=False):
        if self._stats_only:
            ex0 = bool(ex0)
            return self.sumw[ex0]
        else:
            _, weight = self._xweight(ex0=ex0)
            return sum(weight)

    def weight_zero(self):
        """
        sum of weights of zero entries

        Returns
        -------
        sum of weights of zero entries : float

        Note
        ----
        Not available for level monitors
        """
        if self._level:
            raise TypeError("weight_zero not available for level monitors")
        return self.sys_weight_zero()

    def duration_zero(self):
        """
        total duratiom of zero entries

        Returns
        -------
        total duration of zero entries : float

        Note
        ----
        Not available for non level monitors
        """
        if not self._level:
            raise TypeError("duration_zero not available for non level monitors")
        return self.sys_weight_zero()

    def sys_weight_zero(self):
        return self.sys_weight() - self.sys_weight(ex0=True)

    def print_statistics(self, show_header=True, show_legend=True, do_indent=False, as_str=False, file=None):
        """
        print monitor statistics

        Parameters
        ----------
        show_header: bool
            primarily for internal use

        show_legend: bool
            primarily for internal use

        do_indent: bool
            primarily for internal use

        as_str: bool
            if False (default), print the statistics
            if True, return a string containing the statistics

        file: file
            if None (default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        statistics (if as_str is True) : str
        """
        result = []
        if do_indent:
            ll = 45
        else:
            ll = 0
        indent = pad("", ll)

        if show_header:
            result.append(indent + f"Statistics of {self.name()} at {fn(self.env._now - self.env._offset, 13, 3)}")

        if show_legend:
            result.append(indent + "                        all    excl.zero         zero")
            result.append(pad("-" * (ll - 1) + " ", ll) + "-------------- ------------ ------------ ------------")

        if self.sys_weight() == 0:
            result.append(pad(self.name(), ll) + "no data")
            return return_or_print(result, as_str, file)
        if self._weight:
            result.append(
                f"{pad(self.name(), ll)}{pad(self.weight_legend, 14)}{fn(self.sys_weight(), 13, 3)}{fn(self.sys_weight(ex0=True), 13, 3)}{fn(self.sys_weight_zero(), 13, 3)}"
            )
        else:
            result.append(
                f"{pad(self.name(), ll)}{pad('entries', 14)}{fn(self.number_of_entries(), 13, 3)}{fn(self.number_of_entries(ex0=True), 13, 3)}{fn(self.number_of_entries_zero(), 13, 3)}"
            )

        result.append(f"{indent}mean          {fn(self.mean(), 13, 3)}{fn(self.mean(ex0=True), 13, 3)}")

        result.append(f"{indent}std.deviation {fn(self.std(), 13, 3)}{fn(self.std(ex0=True), 13, 3)}")
        result.append("")
        result.append(f"{indent}minimum       {fn(self.minimum(), 13, 3)}{fn(self.minimum(ex0=True), 13, 3)}")
        if not self._stats_only:
            result.append(f"{indent}median        {fn(self.percentile(50), 13, 3)}{fn(self.percentile(50, ex0=True), 13, 3)}")
            result.append(f"{indent}90% percentile{fn(self.percentile(90), 13, 3)}{fn(self.percentile(90, ex0=True), 13, 3)}")
            result.append(f"{indent}95% percentile{fn(self.percentile(95), 13, 3)}{fn(self.percentile(95, ex0=True), 13, 3)}")
        result.append(f"{indent}maximum       {fn(self.maximum(), 13, 3)}{fn(self.maximum(ex0=True), 13, 3)}")
        return return_or_print(result, as_str, file)

    def histogram_autoscale(self, ex0=False):
        """
        used by histogram_print to autoscale |n|
        may be overridden.

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        bin_width, lowerbound, number_of_bins : tuple
        """
        self._block_stats_only()

        xmax = self.maximum(ex0=ex0)
        xmin = self.minimum(ex0=ex0)

        done = False
        for i in range(10):
            exp = 10**i
            for bin_width in (exp, exp * 2, exp * 5):
                lowerbound = math.floor(xmin / bin_width) * bin_width
                number_of_bins = int(math.ceil((xmax - lowerbound) / bin_width))
                if number_of_bins <= 30:
                    done = True
                    break
            if done:
                break
        return bin_width, lowerbound, number_of_bins

    def print_histograms(self, number_of_bins=None, lowerbound=None, bin_width=None, values=False, ex0=False, as_str=False, file=None):
        """
        print monitor statistics and histogram

        Parameters
        ----------
        number_of_bins : int
            number of bins |n|
            default: 30 |n|
            if <0, also the header of the histogram will be surpressed

        lowerbound: float
            first bin |n|
            default: 0

        bin_width : float
            width of the bins |n|
            default: 1

        values : bool
            if False (default), bins will be used |n|
            if True, the individual values will be shown (sorted on the value).
            in that case, no cumulative values will be given |n|

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        as_str: bool
            if False (default), print the histogram
            if True, return a string containing the histogram

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        histogram (if as_str is True) : str

        Note
        ----
        If number_of_bins, lowerbound and bin_width are omitted, the histogram will be autoscaled,
        with a maximum of 30 classes. |n|
        Exactly same functionality as Monitor.print_histogram()
        """
        return self.print_histogram(number_of_bins, lowerbound, bin_width, values, ex0, as_str=as_str, file=file)

    def print_histogram(
        self,
        number_of_bins=None,
        lowerbound=None,
        bin_width=None,
        values=False,
        ex0=False,
        as_str=False,
        file=None,
        sort_on_weight=False,
        sort_on_duration=False,
        sort_on_value=False,
    ):
        """
        print monitor statistics and histogram

        Parameters
        ----------
        number_of_bins : int
            number of bins |n|
            default: 30 |n|
            if <0, also the header of the histogram will be surpressed

        lowerbound: float
            first bin |n|
            default: 0

        bin_width : float
            width of the bins |n|
            default: 1

        values : bool
            if False (default), bins will be used |n|
            if True, the individual values will be shown (in alphabetical order).
            in that case, no cumulative values will be given |n|

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes


        as_str: bool
            if False (default), print the histogram
            if True, return a string containing the histogram

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        sort_on_weight : bool
            if True, sort the values on weight first (largest first), then on the values itself|n|
            if False, sort the values on the values itself |n|
            False is the default for non level monitors. Not permitted for level monitors.

        sort_on_duration : bool
            if True, sort the values on duration first (largest first), then on the values itself|n|
            if False, sort the values on the values itself |n|
            False is the default for level monitors. Not permitted for non level monitors.

        sort        sort_on_weight : bool
            if True, sort the values on weight first (largest first), then on the values itself|n|
            if False (default), sort the values on the values itself |n|
            Not permitted for level monitors.

        sort_on_duration : bool
            if True, sort the values on duration first (largest first), then on the values itself|n|
            if False (default), sort the values on the values itself |n|
            Not permitted for non level monitors.

        sort_on_value : bool
            if True, sort on the values. |n|
            if False (default), no sorting will take place, unless values is an iterable, in which case
            sorting will be done on the values anyway.

        Returns
        -------
        histogram (if as_str is True) : str

        Note
        ----
        If number_of_bins, lowerbound and bin_width are omitted, the histogram will be autoscaled,
        with a maximum of 30 classes.
        """

        if self._level and sort_on_weight:
            raise ValueError("level monitors can't be sorted on weight. Use sort_on_duration instead")
        if not self._level and sort_on_duration:
            raise ValueError("non level monitors can't be sorted on duration. Use sort_on_weight instead")
        if sort_on_value and sort_on_weight:
            raise ValueError("sort_on_value can't be combined with sorted_on_value")
        if sort_on_value and sort_on_weight:
            raise ValueError("sort_on_weight can't be combined with sorted_on_value")

        result = []
        result.append("Histogram of " + self.name() + ("[ex0]" if ex0 else ""))

        if self._stats_only:
            weight_total = self.sumw[bool(ex0)]
        else:
            x, weight = self._xweight(ex0=ex0, force_numeric=not values)
            weight_total = sum(weight)

        if weight_total == 0:
            result.append("")
            result.append("no data")
        else:
            values_is_iterable = False
            if not isinstance(values, str):
                try:
                    values = list(values)  # iterable?
                    values_is_iterable = True
                except TypeError:
                    pass
            if values or values_is_iterable:
                nentries = len(x)
                if self._weight:
                    result.append(f"{pad(self.weight_legend, 13)}{fn(weight_total, 13, 3)}")
                if not self._level:
                    result.append(f"{pad('entries', 13)}{fn(nentries, 13, 3)}")
                result.append("")
                if self._level:
                    result.append(f"value                {rpad(self.weight_legend, 13)}     %")
                else:
                    if self._weight:
                        result.append(f"value                {rpad(self.weight_legend, 13)}     % entries     %")
                    else:
                        result.append("value               entries     %")

                if values_is_iterable:
                    unique_values = []
                    for v in values:
                        if v in unique_values:
                            raise ValueError(f"value {v} used more than once")
                        unique_values.append(v)

                    if sort_on_weight or sort_on_duration or sort_on_value:
                        values_label = [v for v in self.values(ex0=ex0, sort_on_weight=sort_on_weight, sort_on_duration=sort_on_duration) if v in values]
                        values_not_in_monitor = [v for v in values if v not in values_label]
                        values_label.extend(sorted(values_not_in_monitor))
                    else:
                        values_label = values
                else:
                    values_label = self.values(ex0=ex0, sort_on_weight=sort_on_weight, sort_on_duration=sort_on_duration)

                values_condition = [[v] for v in values_label]
                rest_values = self.values(ex0=ex0)
                for v in values_label:
                    if v in rest_values:
                        rest_values.remove(v)

                if rest_values:  # not possible via set subtraction as values may be not hashable
                    values_condition.append(rest_values)
                    values_label.append("<rest>")

                for value_condition, value_label in zip(values_condition, values_label):
                    if self._level:
                        count = self.value_duration(value_condition)
                    else:
                        if self._weight:
                            count = self.value_weight(value_condition)
                            count_entries = self.value_number_of_entries(value_condition)
                        else:
                            count = self.value_number_of_entries(value_condition)

                    perc = count / weight_total
                    scale = 80
                    n = int(perc * scale)
                    s = "*" * n

                    if self._level:
                        result.append(pad(str(value_label), 20) + fn(count, 14, 3) + fn(perc * 100, 6, 1) + " " + s)
                    else:
                        if self._weight:
                            result.append(
                                pad(str(value_label), 20)
                                + fn(count, 14, 3)
                                + fn(perc * 100, 6, 1)
                                + rpad(str(count_entries), 8)
                                + fn(count_entries * 100 / nentries, 6, 1)
                            )
                        else:
                            result.append(pad(str(value_label), 20) + rpad(str(count), 7) + fn(perc * 100, 6, 1) + " " + s)
            else:
                auto_scale = True
                if bin_width is None:
                    bin_width = 1
                else:
                    auto_scale = False
                if lowerbound is None:
                    lowerbound = 0
                else:
                    auto_scale = False
                if number_of_bins is None:
                    number_of_bins = 30
                else:
                    auto_scale = False

                if auto_scale:
                    bin_width, lowerbound, number_of_bins = self.histogram_autoscale()
                result.append(self.print_statistics(show_header=False, show_legend=True, do_indent=False, as_str=True))
                if not self._stats_only and number_of_bins >= 0:
                    result.append("")
                    if self._weight:
                        result.append("           <= " + rpad(self.weight_legend, 13) + "     %  cum%")
                    else:
                        result.append("           <=       entries     %  cum%")

                    cumperc = 0
                    for i in range(-1, number_of_bins + 1):
                        if i == -1:
                            lb = -inf
                        else:
                            lb = lowerbound + i * bin_width
                        if i == number_of_bins:
                            ub = inf
                        else:
                            ub = lowerbound + (i + 1) * bin_width
                        if self._weight:
                            count = self.sys_bin_weight(lb, ub)
                        else:
                            count = self.bin_number_of_entries(lb, ub)

                        perc = count / weight_total
                        if weight_total == inf:
                            s = ""
                        else:
                            cumperc += perc
                            scale = 80
                            n = int(perc * scale)
                            ncum = int(cumperc * scale) + 1
                            s = ("*" * n) + (" " * (scale - n))
                            s = s[: ncum - 1] + "|" + s[ncum + 1 :]

                        result.append(f"{fn(ub, 13, 3)} {fn(count, 13, 3)}{fn(perc * 100, 6, 1)}{fn(cumperc * 100, 6, 1)} {s}")
        result.append("")
        return return_or_print(result, as_str=as_str, file=file)

    def values(self, ex0=False, force_numeric=False, sort_on_weight=False, sort_on_duration=False):
        """
        values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        force_numeric : bool
            if True, convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False (default), do not interpret x-values, return as list if type is list

        sort_on_weight : bool
            if True, sort the values on weight first (largest first), then on the values itself|n|
            if False, sort the values on the values itself |n|
            False is the default for non level monitors. Not permitted for level monitors.

        sort_on_duration : bool
            if True, sort the values on duration first (largest first), then on the values itself|n|
            if False, sort the values on the values itself |n|
            False is the default for level monitors. Not permitted for non level monitors.

        Returns
        -------
        all tallied values : array/list
        """
        self._block_stats_only()
        x, _ = self._xweight(ex0, force_numeric)

        if self._level:
            if sort_on_weight:
                raise ValueError("level monitors can't be sorted on weight. Use sort_on_duration instead")
        else:
            if sort_on_duration:
                raise ValueError("non level monitors can't be sorted on duration. Use sort_on_weight instead")

        def key(x):
            if sort_on_weight:
                weight = -self.value_weight(x)
            elif sort_on_duration:
                weight = -self.value_duration(x)
            else:
                weight = 1

            try:
                return (weight, float(x), "")
            except (ValueError, TypeError):
                return (weight, math.inf, str(x).lower())

        x_unique = []  # not possible to use set() as items do not have to be hashable
        for item in x:
            if item not in x_unique:
                x_unique.append(item)

        return list(sorted(x_unique, key=key))

    def animate(self, *args, **kwargs):
        """
        animates the monitor in a panel

        Parameters
        ----------
        linecolor : colorspec
            color of the line or points (default foreground color)

        linewidth : int
            width of the line or points (default 1 for level, 3 for non level monitors)

        fillcolor : colorspec
            color of the panel (default transparent)

        bordercolor : colorspec
            color of the border (default foreground color)

        borderlinewidth : int
            width of the line around the panel (default 1)

        nowcolor : colorspec
            color of the line indicating now (default red)

        titlecolor : colorspec
            color of the title (default foreground color)

        titlefont : font
            font of the title (default null string)

        titlefontsize : int
            size of the font of the title (default 15)

        title : str
            title to be shown above panel |n|
            default: name of the monitor

        x : int
            x-coordinate of panel, relative to xy_anchor, default 0

        y : int
            y-coordinate of panel, relative to xy_anchor. default 0

        offsetx : float
            offsets the x-coordinate of the panel (default 0)

        offsety : float
            offsets the y-coordinate of the panel (default 0)

        angle : float
            rotation angle in degrees, default 0

        xy_anchor : str
            specifies where x and y are relative to |n|
            possible values are (default: sw): |n|
            ``nw    n    ne`` |n|
            ``w     c     e`` |n|
            ``sw    s    se``

        vertical_offset : float
            the vertical position of x within the panel is
             vertical_offset + x * vertical_scale (default 0)

        vertical_scale : float
            the vertical position of x within the panel is
            vertical_offset + x * vertical_scale (default 5)

        horizontal_scale : float
            the relative horizontal position of time t within the panel is on
            t * horizontal_scale, possibly shifted (default 1)|n|

        width : int
            width of the panel (default 200)

        height : int
            height of the panel (default 75)

        vertical_map : function
            when a y-value has to be plotted it will be translated by this function |n|
            default: float |n|
            when the function results in a TypeError or ValueError, the value 0 is assumed |n|
            when y-values are non numeric, it is advised to provide an approriate map function, like: |n|
            vertical_map = "unknown red green blue yellow".split().index

        labels : iterable
            labels to be shown on the vertical axis (default: empty tuple) |n|
            the placement of the labels is controlled by the vertical_map method

        label_color : colorspec
            color of labels (default: foreground color)

        label_font : font
            font of the labels (default null string)

        label_fontsize : int
            size of the font of the labels (default 15)

        label_anchor : str
            specifies where the label coordinates (as returned by map_value) are relative to |n|
            possible values are (default: e): |n|
            ``nw    n    ne`` |n|
            ``w     c     e`` |n|
            ``sw    s    se``

        label_offsetx : float
            offsets the x-coordinate of the label (default 0)

        label_offsety : float
            offsets the y-coordinate of the label (default 0)

        label_linewidth : int
            width of the label line (default 1)

        label_linecolor : colorspec
            color of the label lines (default foreground color)

        layer : int
            layer (default 0)

        as_points : bool
            allows to override the as_points setting of tallies, which is
            by default False for level monitors and True for non level monitors

        parent : Component
            component where this animation object belongs to (default None) |n|
            if given, the animation object will be removed
            automatically when the parent component is no longer accessible

        screen_coordinates : bool
            use screen_coordinates |n|
            normally, the scale parameters are use for positioning and scaling
            objects. |n|
            if True, screen_coordinates will be used instead.

        over3d : bool
            if True, this object will be rendered to the OpenGL window |n|
            if False (default), the normal 2D plane will be used.

        Returns
        -------
        reference to AnimateMonitor object : AnimateMonitor

        Note
        ----
        All measures are in screen coordinates |n|

        Note
        ----
        It is recommended to use sim.AnimateMonitor instead |n|

        All measures are in screen coordinates |n|
        """
        return AnimateMonitor(monitor=self, *args, **kwargs)

    def x(self, ex0=False, force_numeric=True):
        """
        array/list of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is any (list)

        Returns
        -------
        all tallied values : array/list

        Note
        ----
        Not available for level monitors. Use xduration(), xt() or tx() instead.
        """
        self._block_stats_only()

        if self._level:
            raise TypeError("x not available for level monitors")
        return self._xweight(ex0=ex0, force_numeric=force_numeric)[0]

    def xweight(self, ex0=False, force_numeric=True):
        """
        array/list of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        Returns
        -------
        all tallied values : array/list

        Note
        ----
        not available for level monitors
        """
        self._block_stats_only()

        if self._level:
            raise TypeError("xweight not available for level monitors")
        return self._xweight(ex0, force_numeric)

    def xduration(self, ex0=False, force_numeric=True):
        """
        array/list of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        Returns
        -------
        all tallied values : array/list

        Note
        ----
        not available for non level monitors
        """
        self._block_stats_only()

        if not self._level:
            raise TypeError("xduration not available for non level monitors")
        return self._xweight(ex0, force_numeric)

    def xt(self, ex0=False, exoff=False, force_numeric=True, add_now=True):
        """
        tuple of array/list with x-values and array with timestamp

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        exoff : bool
            if False (default), include self.off. if True, exclude self.off's |n|
            non level monitors will return all values, regardless of exoff

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        add_now : bool
            if True (default), the last tallied x-value and the current time is added to the result |n|
            if False, the result ends with the last tallied value and the time that was tallied |n|
            non level monitors will never add now |n|
            if now is <= last tallied value, nothing will be added, even if add_now is True

        Returns
        -------
        array/list with x-values and array with timestamps : tuple

        Note
        ----
        The value self.off is stored when monitoring is turned off |n|
        The timestamps are not corrected for any reset_now() adjustment.
        """
        self._block_stats_only()

        if not self._level:
            exoff = False
            add_now = False

        if self.xtypecode or (not force_numeric):
            x = self._x
            typecode = self.xtypecode
            off = self.off
        else:
            x = do_force_numeric(self._x)
            typecode = ""
            off = -inf  # float

        if typecode:
            xx = array.array(typecode)
        else:
            xx = []
        t = array.array("d")
        if add_now:
            addx = [x[-1]]
            t_extra = self.env._t if self.env._animate else self.env._now
            addt = [t_extra]
        else:
            addx = []
            addt = []

        for vx, vt in zip(itertools.chain(x, addx), itertools.chain(self._t, addt)):
            if not ex0 or (vx != 0):
                if not exoff or (vx != off):
                    xx.append(vx)
                    t.append(vt)

        return xx, t

    def tx(self, ex0=False, exoff=False, force_numeric=False, add_now=True):
        """
        tuple of array with timestamps and array/list with x-values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        exoff : bool
            if False (default), include self.off. if True, exclude self.off's |n|
            non level monitors will return all values, regardless of exoff

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        add_now : bool
            if True (default), the last tallied x-value and the current time is added to the result |n|
            if False, the result ends with the last tallied value and the time that was tallied |n|
            non level monitors will never add now

        Returns
        -------
        array with timestamps and array/list with x-values : tuple

        Note
        ----
        The value self.off is stored when monitoring is turned off |n|
        The timestamps are not corrected for any reset_now() adjustment.
        """
        self._block_stats_only()

        return tuple(reversed(self.xt(ex0=ex0, exoff=exoff, force_numeric=force_numeric, add_now=add_now)))

    def _xweight(self, ex0=False, force_numeric=True):
        if self._level:
            t_extra = self.env._t if self.env._animate else self.env._now
            thishash = hash((self, len(self._x), t_extra))
        else:
            thishash = hash((self, len(self._x)))
        if Monitor.cached_xweight[(ex0, force_numeric)][0] == thishash:
            return Monitor.cached_xweight[(ex0, force_numeric)][1]

        if self.xtypecode or (not force_numeric):
            x = self._x
            typecode = self.xtypecode
        else:
            x = do_force_numeric(self._x)
            typecode = ""

        if self._level:
            weightall = array.array("d")
            lastt = None
            for t in self._t:
                if lastt is not None:
                    weightall.append(t - lastt)
                lastt = t
            weightall.append(t_extra - lastt)

            weight = array.array("d")
            if typecode:
                xx = array.array(typecode)
            else:
                xx = []

            for vx, vweight in zip(x, weightall):
                if vx != self.off:
                    if vx != 0 or not ex0:
                        xx.append(vx)
                        weight.append(vweight)
            xweight = (xx, weight)
        else:

            if ex0:
                x0 = [vx for vx in x if vx != 0]
                if typecode:
                    x0 = array.array(typecode, x)

            if self._weight:
                if ex0:
                    xweight = (x0, array.array("d", [vweight for vx, vweight in zip(x, self._weight) if vx != 0]))
                else:
                    xweight = (x, self._weight)
            else:
                if ex0:
                    xweight = (x0, array.array("d", (1,) * len(x0)))
                else:
                    xweight = (x, array.array("d", (1,) * len(x)))

        Monitor.cached_xweight[(ex0, force_numeric)] = (thishash, xweight)
        return xweight


class _CapacityMonitor(Monitor):
    @property
    def value(self):
        return self._tally

    @value.setter
    def value(self, value):
        self.parent.set_capacity(value)


class _ModeMonitor(Monitor):
    @property
    def value(self):
        return self._tally

    @value.setter
    def value(self, value):
        raise ValueError("not possible to use mode.value = . Use set_mode instead")


class _StatusMonitor(Monitor):
    @property
    def value(self):
        return self._tally

    @property
    def _value(self):  # this is just defined to be able to make the setter
        return self._tally

    @_value.setter
    def _value(self, value):  # as we don't want user to set (tally) the status
        self.tally(value)


class _SystemMonitor(Monitor):
    @property
    def value(self):
        return self._tally


class DynamicClass:
    def __init__(self):
        self._dynamics = set()

    def register_dynamic_attributes(self, attributes):
        """
        Registers one or more attributes as being dynamic

        Parameters
        ----------
        attributes : str
            a specification of attributes to be registered as dynamic |n|
            e.g. "x y"
        """
        if isinstance(attributes, str):
            attributes = attributes.split()
        for attribute in attributes:
            if hasattr(self, attribute):
                self._dynamics.add((attribute))
            else:
                raise ValueError(f"attribute {attribute} does not exist")

    def deregister_dynamic_attributes(self, attributes):
        """
        Deregisters one or more attributes as being dynamic

        Parameters
        ----------
        attributes : str
            a specification of attributes to be registered as dynamic |n|
            e.g. "x y"
        """

        if isinstance(attributes, str):
            attributes = attributes.split()
        for attribute in attributes:
            if hasattr(self, attribute):
                self._dynamics.remove((attribute))
            else:
                raise ValueError(f"attribute {attribute} does not exist")

    def __getattribute__(self, attr):
        if attr == "_dynamics":
            return super().__getattribute__(attr)

        c = super().__getattribute__(attr)
        if attr not in self._dynamics:
            return c
        if callable(c):
            if inspect.isfunction(c):
                nargs = c.__code__.co_argcount
                if nargs == 0:
                    return lambda t: c()
                if nargs == 1:
                    return c
                return functools.partial(c, self.arg)
            if inspect.ismethod(c):
                return c
        return lambda t: c

    def getattribute_spec(self, attr):
        """
        special version of getattribute.
        When it's dynamic it will return the value in case of a constan or a parameterless function
        Used only in AnimateCombined
        """

        if attr == "_dynamics":
            return super().__getattribute__(attr)

        c = super().__getattribute__(attr)
        if attr not in self._dynamics:
            return c
        if callable(c):
            if inspect.isfunction(c):
                nargs = c.__code__.co_argcount
                if nargs == 0:
                    return c()
                if nargs == 1:
                    return c
                return functools.partial(c, self.arg)
            if inspect.ismethod(c):
                return c
        return c

    def __call__(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise AttributeError(f"attribute {k} does not exist")

    def add_attr(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                raise AttributeError("attribute " + k + " already set")
            setattr(self, k, v)
        return self


class AnimateMonitor(DynamicClass):
    """
    animates a monitor in a panel

    Parameters
    ----------
    monitor : Monitor
        monitor to be animated

    linecolor : colorspec
        color of the line or points (default foreground color)

    linewidth : int
        width of the line or points (default 1 for level, 3 for non level monitors)

    fillcolor : colorspec
        color of the panel (default transparent)

    bordercolor : colorspec
        color of the border (default foreground color)

    borderlinewidth : int
        width of the line around the panel (default 1)

    nowcolor : colorspec
        color of the line indicating now (default red)

    titlecolor : colorspec
        color of the title (default foreground color)

    titlefont : font
        font of the title (default null string)

    titlefontsize : int
        size of the font of the title (default 15)

    title : str
        title to be shown above panel |n|
        default: name of the monitor

    x : int
        x-coordinate of panel, relative to xy_anchor, default 0

    y : int
        y-coordinate of panel, relative to xy_anchor. default 0

    offsetx : float
        offsets the x-coordinate of the panel (default 0)

    offsety : float
        offsets the y-coordinate of the panel (default 0)

    angle : float
        rotation angle in degrees, default 0

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    vertical_offset : float
        the vertical position of x within the panel is
         vertical_offset + x * vertical_scale (default 0)

    vertical_scale : float
        the vertical position of x within the panel is
        vertical_offset + x * vertical_scale (default 5)

    horizontal_scale : float
        the relative horizontal position of time t within the panel is on
        t * horizontal_scale, possibly shifted (default 1)|n|

    width : int
        width of the panel (default 200)

    height : int
        height of the panel (default 75)

    vertical_map : function
        when a y-value has to be plotted it will be translated by this function |n|
        default: float |n|
        when the function results in a TypeError or ValueError, the value 0 is assumed |n|
        when y-values are non numeric, it is advised to provide an approriate map function, like: |n|
        vertical_map = "unknown red green blue yellow".split().index

    labels : iterable or dict
        if an iterable, these are the values of the labels to be shown |n|
        if a dict, the keys are the values of the labels, the keys are the texts to be shown |n|
        labels will be shown on the vertical axis (default: empty tuple) |n|
        the placement of the labels is controlled by the vertical_map method

    label_color : colorspec
        color of labels (default: foreground color)

    label_font : font
        font of the labels (default null string)

    label_fontsize : int
        size of the font of the labels (default 15)

    label_anchor : str
        specifies where the label coordinates (as returned by map_value) are relative to |n|
        possible values are (default: e): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    label_offsetx : float
        offsets the x-coordinate of the label (default 0)

    label_offsety : float
        offsets the y-coordinate of the label (default 0)

    label_linewidth : int
        width of the label line (default 1)

    label_linecolor : colorspec
        color of the label lines (default foreground color)

    layer : int
        layer (default 0)

    as_points : bool
        allows to override the line/point setting, which is by default False for level
        monitors and True for non level monitors

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    visible : bool
        visible |n|
        if False, animation monitor is not shown, shown otherwise
        (default True)

    screen_coordinates : bool
        use screen_coordinates |n|
        if False,  the scale parameters are use for positioning and scaling
        objects. |n|
        if True (default), screen_coordinates will be used.

    Note
    ----
    All measures are in screen coordinates |n|
    """

    def __init__(
        self,
        monitor,
        linecolor="fg",
        linewidth=None,
        fillcolor="",
        bordercolor="fg",
        borderlinewidth=1,
        titlecolor="fg",
        nowcolor="red",
        titlefont="",
        titlefontsize=15,
        title=None,
        x=0,
        y=0,
        offsetx=0,
        offsety=0,
        angle=0,
        vertical_offset=0,
        parent=None,
        vertical_scale=5,
        horizontal_scale=1,
        width=200,
        height=75,
        xy_anchor="sw",
        vertical_map=float,
        labels=(),
        label_color="fg",
        label_font="",
        label_fontsize=15,
        label_anchor="e",
        label_offsetx=0,
        label_offsety=0,
        label_linewidth=1,
        label_linecolor="fg",
        as_points=None,
        over3d=None,
        layer=0,
        visible=True,
        keep=True,
        screen_coordinates=True,
        arg=None,
    ):
        super().__init__()
        _checkismonitor(monitor)
        monitor._block_stats_only()

        if title is None:
            title = monitor.name()

        if linewidth is None:
            linewidth = 1 if monitor._level else 3

        if over3d is None:
            over3d = default_over3d()

        offsetx += monitor.env.xy_anchor_to_x(xy_anchor, screen_coordinates=True, over3d=over3d)
        offsety += monitor.env.xy_anchor_to_y(xy_anchor, screen_coordinates=True, over3d=over3d)

        self.linecolor = linecolor
        self.linewidth = linewidth
        self.fillcolor = fillcolor
        self.bordercolor = bordercolor
        self.borderlinewidth = borderlinewidth
        self.titlecolor = titlecolor
        self.nowcolor = nowcolor
        self.titlefont = titlefont
        self.titlefontsize = titlefontsize
        self.title = title
        self.x = x
        self.y = y
        self.offsetx = offsetx
        self.offsety = offsety
        self.angle = angle
        self.vertical_offset = vertical_offset
        self.parent = parent
        self.vertical_scale = vertical_scale
        self.horizontal_scale = horizontal_scale
        self.width = width
        self.height = height
        self.xy_anchor = xy_anchor
        self.vertical_map = vertical_map
        self.labels = labels
        self.label_color = label_color
        self.label_font = label_font
        self.label_fontsize = label_fontsize
        self.label_anchor = label_anchor
        self.label_offsetx = label_offsetx
        self.label_offsety = label_offsety
        self.label_linewidth = label_linewidth
        self.label_linecolor = label_linecolor
        self.layer = layer
        self.visible = visible
        self.keep = keep
        self.arg = self if arg is None else arg
        self.as_points = not monitor._level if as_points is None else as_points
        self._monitor = monitor
        self.as_level = monitor._level
        self.over3d = over3d
        self.screen_coordinates = screen_coordinates
        self.register_dynamic_attributes(
            "linecolor linewidth fillcolor bordercolor borderlinewidth titlecolor nowcolor titlefont titlefontsize title "
            "x y offsetx offsety angle vertical_offset parent vertical_scale horizontal_scale width height "
            "xy_anchor labels label_color label_font label_fontsize label_anchor label_offsetx label_offsety "
            "label_linewidth label_linecolor layer visible keep"
        )

        if parent is not None:
            if not isinstance(parent, Component):
                raise ValueError(repr(parent) + " is not a component")
            parent._animation_children.add(self)
        self.env = monitor.env
        self.ao_frame = AnimateRectangle(
            spec=lambda: (0, 0, self.width_t, self.height_t),
            x=lambda: self.x_t,
            y=lambda: self.y_t,
            offsetx=lambda: self.offsetx_t,
            offsety=lambda: self.offsety_t,
            angle=lambda: self.angle_t,
            fillcolor=lambda t: self.fillcolor(t),
            linewidth=lambda t: self.borderlinewidth(t),
            linecolor=lambda t: self.bordercolor(t),
            screen_coordinates=self.screen_coordinates,
            layer=lambda: self.layer_t + 0.2,  # to make it appear vehind label lines and plot line/points
            over3d=self.over3d,
            visible=lambda: self.visible_t,
        )

        self.ao_text = AnimateText(
            text=lambda t: self.title(t),
            textcolor=lambda t: self.titlecolor(t),
            x=lambda: self.x_t,
            y=lambda: self.y_t,
            offsetx=lambda: self.offsetx_t,
            offsety=lambda t: self.offsety_t + self.height_t + self.titlefontsize(t) * 0.15,
            angle=lambda: self.angle_t,
            text_anchor="sw",
            fontsize=lambda t: self.titlefontsize(t),
            font=lambda t: self.titlefont(t),
            layer=lambda t: self.layer_t,
            over3d=self.over3d,
            visible=lambda: self.visible_t,
            screen_coordinates=self.screen_coordinates,
        )

        self.ao_line = AnimateLine(
            spec=lambda t: self.line(t),
            x=lambda: self.x_t,
            y=lambda: self.y_t,
            offsetx=lambda: self.offsetx_t,
            offsety=lambda: self.offsety_t,
            angle=lambda: self.angle_t,
            linewidth=lambda t: self.linewidth(t),
            linecolor=lambda t: self.linecolor(t),
            as_points=self.as_points,
            layer=lambda: self.layer_t,
            over3d=self.over3d,
            visible=lambda: self.visible_t,
            screen_coordinates=self.screen_coordinates,
        )

        self.ao_now_line = AnimateLine(
            spec=lambda t: self.now_line(t),
            x=lambda: self.x_t,
            y=lambda: self.y_t,
            offsetx=lambda: self.offsetx_t,
            offsety=lambda: self.offsety_t,
            angle=lambda: self.angle_t,
            linecolor=lambda t: self.nowcolor(t),
            layer=lambda: self.layer_t,
            over3d=self.over3d,
            visible=lambda: self.visible_t,
            screen_coordinates=self.screen_coordinates,
        )

        self.ao_label_texts = []
        self.ao_label_lines = []

        self.show()

    def t_to_x(self, t):
        t -= self.t_start
        if self.displacement_t < 0:
            t += self.displacement_t
            if t < 0:
                t = 0
                self.done = True
        x = t * self.horizontal_scale_t
        return max(0, min(self.width_t, x))

    def value_to_y(self, value):
        if value == self._monitor.off:
            value = 0
        else:
            try:
                value = self.vertical_map(value)

            except (ValueError, TypeError):
                value = 0
        return max(0, min(self.height_t, value * self.vertical_scale_t + self.vertical_offset_t))

    def line(self, t):

        result = []
        if len(self._monitor._x) != 0:
            value = self._monitor._x[-1]
        else:
            value = 0
        lastt = t + self._monitor.env._offset
        if self.as_level:
            result.append(self.t_to_x(lastt))
            result.append(self.value_to_y(value))
        self.done = False
        for value, t in zip(reversed(self._monitor._x), reversed(self._monitor._t)):
            if self.as_level:
                result.append(self.t_to_x(lastt))
                result.append(self.value_to_y(value))
            result.append(self.t_to_x(t))
            result.append(self.value_to_y(value))
            if self.done:
                if not self.as_level:
                    result.pop()  # remove the last outlier x
                    result.pop()  # remove the last outlier y
                break
            lastt = t
        return result

    def now_line(self, t):
        t -= self._monitor.start - self._monitor.env._offset
        t = min(t, self.width_div_horizontal_scale_t)
        x = t * self.horizontal_scale_t
        return x, 0, x, self.height_t

    def update(self, t):
        if not self.keep(t):
            self.remove()
            return

        self.width_t = self.width(t)
        self.height_t = self.height(t)
        self.x_t = self.x(t)
        self.y_t = self.y(t)
        self.offsetx_t = self.offsetx(t)
        self.offsety_t = self.offsety(t)
        self.angle_t = self.angle(t)
        self.layer_t = self.layer(t)
        self.visible_t = self.visible(t)
        self.vertical_scale_t = self.vertical_scale(t)
        self.vertical_offset_t = self.vertical_offset(t)
        self.horizontal_scale_t = self.horizontal_scale(t)
        self.linewidth_t = self.linewidth(t)
        self.t_start = self._monitor.start
        self.width_div_horizontal_scale_t = self.width_t / self.horizontal_scale_t
        self.displacement_t = self.width_div_horizontal_scale_t - (t - self.t_start)

        labels = []
        label_ys = []

        _labels = self.labels(t)

        for value in _labels:
            if isinstance(_labels, dict):
                text = _labels[value]
            else:
                text = value

            try:
                label_y = self.vertical_map(value) * self.vertical_scale_t + self.vertical_offset_t
                if 0 <= label_y <= self.height_t:
                    labels.append(text)
                    label_ys.append(label_y)
            except (ValueError, TypeError):
                pass

        for (label, label_y, ao_label_text, ao_label_line) in itertools.zip_longest(labels, label_ys, self.ao_label_texts[:], self.ao_label_lines[:]):
            if label is None:
                ao_label_text = self.ao_label_texts.pop()
                ao_label_line = self.ao_label_lines.pop()
                ao_label_text.remove()
                ao_label_line.remove()
            else:
                if ao_label_text is None:
                    ao_label_text = AnimateText(screen_coordinates=self.screen_coordinates)
                    ao_label_line = AnimateLine(screen_coordinates=self.screen_coordinates)
                    self.ao_label_texts.append(ao_label_text)
                    self.ao_label_lines.append(ao_label_line)

                ao_label_text.text = str(label)
                ao_label_text.textcolor = self.label_color(t)
                ao_label_text.x = self.x_t
                ao_label_text.y = self.y_t
                ao_label_text.offsetx = self.offsetx_t + self.label_offsetx(t)
                ao_label_text.offsety = self.offsety_t + self.label_offsety(t) + label_y
                ao_label_text.angle = self.angle_t
                ao_label_text.text_anchor = self.label_anchor(t)
                ao_label_text.fontsize = self.label_fontsize(t)
                ao_label_text.font = self.label_font(t)
                ao_label_text.layer = self.layer_t
                ao_label_text.over3d = self.over3d
                ao_label_text.visible = self.visible_t

                ao_label_line.spec = (0, 0, self.width_t, 0)
                ao_label_line.x = self.x_t
                ao_label_line.y = self.y_t
                ao_label_line.offsetx = self.offsetx_t
                ao_label_line.offsety = label_y
                ao_label_line.angle = self.angle_t
                ao_label_line.linewidth = self.label_linewidth(t)
                ao_label_line.linecolor = self.label_linecolor(t)
                ao_label_line.layer = self.layer_t + 0.1  # to make it appear behind the plot line/points
                ao_label_line.over3d = self.over3d
                ao_label_line.visible = self.visible_t

    def monitor(self):
        """
        Returns
        -------
        monitor this animation object refers : Monitor
        """
        return self._monitor

    def show(self):
        """
        show (unremove)

        It is possible to use this method if already shown
        """
        self.ao_frame.show()
        self.ao_text.show()
        self.ao_line.show()
        self.ao_now_line.show()
        self.env.sys_objects.add(self)

    def remove(self):
        """
        removes the animate object and thus closes this animation
        """
        self.ao_frame.remove()
        self.ao_text.remove()
        self.ao_line.remove()
        self.ao_now_line.remove()
        for ao in self.ao_label_texts:
            ao.remove()
        for ao in self.ao_label_lines:
            ao.remove()

        self.env.sys_objects.discard(self)

    def is_removed(self):
        return self in self.env.sys_objects


if Pythonista:

    class AnimationScene(scene.Scene):
        def __init__(self, env, *args, **kwargs):
            scene.Scene.__init__(self, *args, **kwargs)

        def setup(self):
            if g.animation_env.retina:
                self.bg = None

        def touch_ended(self, touch):
            env = g.animation_env
            if env is not None:
                for uio in env.ui_objects:
                    ux = uio.x + env.xy_anchor_to_x(uio.xy_anchor, screen_coordinates=True, retina_scale=True)
                    uy = uio.y + env.xy_anchor_to_y(uio.xy_anchor, screen_coordinates=True, retina_scale=True)
                    if uio.type == "button":
                        if touch.location in scene.Rect(ux - 2, uy - 2, uio.width + 2, uio.height + 2):
                            uio.action()
                            break  # new buttons might have been installed
                    if uio.type == "slider":
                        if touch.location in scene.Rect(ux - 2, uy - 2, uio.width + 4, uio.height + 4):
                            xsel = touch.location[0] - ux
                            uio._v = uio.vmin + round(-0.5 + xsel / uio.xdelta) * uio.resolution
                            uio._v = max(min(uio._v, uio.vmax), uio.vmin)
                            if uio.action is not None:
                                uio.action(str(uio._v))
                                break  # new items might have been installed

        def draw(self):
            env = g.animation_env
            g.in_draw = True
            if (env is not None) and env._animate and env.running:
                scene.background(env.pythonistacolor("bg"))

                if env._synced or env._video:  # video forces synced
                    if env._video:
                        env._t = env.video_t
                    else:
                        if env.paused:
                            env._t = env.start_animation_time
                        else:
                            env._t = env.start_animation_time + ((time.time() - env.start_animation_clocktime) * env._speed)
                    while (env.peek() < env._t) and env.running and env._animate:
                        env.step()
                        if env.paused:
                            env._t = env.start_animation_time = env._now
                            break

                else:
                    if (env._step_pressed or (not env.paused)) and env._animate:
                        env.step()
                        if not env._current_component._suppress_pause_at_step:
                            env._step_pressed = False
                if not env.paused:
                    env.frametimes.append(time.time())
                touchvalues = self.touches.values()
                if env.retina > 1:
                    with io.BytesIO() as fp:
                        env._capture_image("RGB", include_topleft=True).save(fp, "BMP")
                        img = ui.Image.from_data(fp.getvalue(), env.retina)
                    if self.bg is None:
                        self.bg = scene.SpriteNode(scene.Texture(img))
                        self.add_child(self.bg)
                        self.bg.position = self.size / 2
                        self.bg.z_position = 10000
                    else:
                        self.bg.texture = scene.Texture(img)
                else:
                    env.animation_pre_tick(env.t())
                    env.animation_pre_tick_sys(env.t())
                    capture_image = env._capture_image("RGB", include_topleft=True)
                    env.animation_post_tick(env.t)
                    ims = scene.load_pil_image(capture_image)
                    scene.image(ims, 0, 0, *capture_image.size)
                    scene.unload_image(ims)
                if env._video and (not env.paused):
                    env._save_frame()
                    env.video_t += env._speed / env._fps

                for uio in env.ui_objects:
                    if not uio.installed:
                        uio.install()
                    ux = uio.x + env.xy_anchor_to_x(uio.xy_anchor, screen_coordinates=True, retina_scale=True)
                    uy = uio.y + env.xy_anchor_to_y(uio.xy_anchor, screen_coordinates=True, retina_scale=True)

                    if uio.type == "entry":
                        raise NotImplementedError("AnimateEntry not supported on Pythonista")
                    if uio.type == "button":
                        linewidth = uio.linewidth
                        scene.push_matrix()
                        scene.fill(env.pythonistacolor(uio.fillcolor))
                        scene.stroke(env.pythonistacolor(uio.linecolor))
                        scene.stroke_weight(linewidth)
                        scene.rect(ux - 4, uy + 2, uio.width + 8, uio.height - 4)
                        scene.tint(env.pythonistacolor(uio.color))
                        scene.translate(ux + uio.width / 2, uy + uio.height / 2)
                        scene.text(uio.text(), uio.font, uio.fontsize, alignment=5)
                        scene.tint(1, 1, 1, 1)
                        # required for proper loading of images
                        scene.pop_matrix()
                    elif uio.type == "slider":
                        scene.push_matrix()
                        scene.tint(env.pythonistacolor(uio.foreground_color))
                        v = uio.vmin
                        x = ux + uio.xdelta / 2
                        y = uy
                        mindist = inf
                        v = uio.vmin
                        while v <= uio.vmax:
                            if abs(v - uio._v) < mindist:
                                mindist = abs(v - uio._v)
                                vsel = v
                            v += uio.resolution
                        thisv = uio._v
                        for touch in touchvalues:
                            if touch.location in scene.Rect(ux, uy, uio.width, uio.height):
                                xsel = touch.location[0] - ux
                                vsel = round(-0.5 + xsel / uio.xdelta) * uio.resolution
                                thisv = vsel
                        scene.stroke(env.pythonistacolor(uio.foreground_color))
                        v = uio.vmin
                        xfirst = -1
                        while v <= uio.vmax:
                            if xfirst == -1:
                                xfirst = x
                            if v == vsel:
                                scene.stroke_weight(3)
                            else:
                                scene.stroke_weight(1)
                            scene.line(x, y, x, y + uio.height)
                            v += uio.resolution
                            x += uio.xdelta

                        scene.push_matrix()
                        scene.stroke(env.pythonistacolor(uio.foreground_color))
                        scene.translate(xfirst, uy + uio.height + 2)
                        if uio._label:
                            scene.text(uio._label, uio.font, uio.fontsize, alignment=9)
                        scene.pop_matrix()
                        scene.translate(ux + uio.width, uy + uio.height + 2)
                        scene.text(str(thisv) + " ", uio.font, uio.fontsize, alignment=7)
                        scene.tint(1, 1, 1, 1)
                        # required for proper loading of images later
                        scene.pop_matrix()
            else:
                width, height = ui.get_screen_size()
                scene.pop_matrix()
                scene.tint(1, 1, 1, 1)
                scene.translate(width / 2, height / 2)
                scene.text("salabim animation paused/stopped")
                scene.pop_matrix()
                scene.tint(1, 1, 1, 1)
            g.in_draw = False


class Qmember:
    def __init__(self):
        pass

    def insert_in_front_of(self, m2, c, q, priority):
        available_quantity = q.capacity._tally - q._length-1 
        if available_quantity < 0:
            raise QueueFullError(q.name() + " has reached capacity " + str(q.capacity._tally))
        q.available_quantity.tally(available_quantity)

        m1 = m2.predecessor
        m1.successor = self
        m2.predecessor = self
        self.predecessor = m1
        self.successor = m2
        self.priority = priority
        self.component = c
        self.queue = q
        self.enter_time = c.env._now
        q._length += 1
        for iter in q._iter_touched:
            q._iter_touched[iter] = True
        c._qmembers[q] = self
        if q.env._trace:
            if not q._isinternal:
                q.env.print_trace("", "", c.name(), "enter " + q.name())
        q.length.tally(q._length)
        q.number_of_arrivals += 1


class Queue:
    """
    Queue object

    Parameters
    ----------
    fill : Queue, list or tuple
        fill the queue with the components in fill |n|
        if omitted, the queue will be empty at initialization

    name : str
        name of the queue |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

    capacity : float
        maximum number of components the queue can contain. |n|
        if exceeded, a QueueFullError will be raised |n|
        default: inf

    monitor : bool
        if True (default) , both length and length_of_stay are monitored |n|
        if False, monitoring is disabled.

    env : Environment
        environment where the queue is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, name=None, monitor=True, fill=None, capacity=inf, env=None, *args, **kwargs):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        _set_name(name, self.env._nameserializeQueue, self)
        self._head = Qmember()
        self._tail = Qmember()
        self._head.successor = self._tail
        self._head.predecessor = None
        self._tail.successor = None
        self._tail.predecessor = self._head
        self._head.component = None
        self._tail.component = None
        self._head.priority = 0
        self._tail.priority = 0
        self._length = 0
        self._iter_sequence = 0
        self._iter_touched = {}
        self._isinternal = False
        self.arrival_rate(reset=True)
        self.departure_rate(reset=True)
        self.length = _SystemMonitor("Length of " + self.name(), level=True, initial_tally=0, monitor=monitor, type="uint32", env=self.env)
        self.length_of_stay = Monitor("Length of stay in " + self.name(), monitor=monitor, type="float", env=self.env)
        self.capacity = _CapacityMonitor("Capacity of " + self.name(), level=True, initial_tally=capacity, monitor=monitor, type="float", env=env)
        self.capacity.parent=self
        self.available_quantity = _SystemMonitor("Available quantity of "+self.name(), level=True, initial_tally=capacity, monitor=monitor, type="float", env=env)

        if fill is not None:
            savetrace = self.env._trace
            self.env._trace = False
            for c in fill:
                c.enter(self)
            self.env._trace = savetrace
        if self.env._trace:
            self.env.print_trace("", "", self.name() + " create")
        self.setup(*args, **kwargs)

    def setup(self):
        """
        called immediately after initialization of a queue.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        """
        pass

    def animate(self, *args, **kwargs):
        """
        Animates the components in the queue.

        Parameters
        ----------
        x : float
            x-position of the first component in the queue |n|
            default: 50

        y : float
            y-position of the first component in the queue |n|
            default: 50

        direction : str
            if "w", waiting line runs westwards (i.e. from right to left) |n|
            if "n", waiting line runs northeards (i.e. from bottom to top) |n|
            if "e", waiting line runs eastwards (i.e. from left to right) (default) |n|
            if "s", waiting line runs southwards (i.e. from top to bottom)
            if "t", waiting line runs follows given trajectory

        trajectory : Trajectory
            trajectory to be followed if direction == "t"

        reverse : bool
            if False (default), display in normal order. If True, reversed.

        max_length : int
            maximum number of components to be displayed

        xy_anchor : str
            specifies where x and y are relative to |n|
            possible values are (default: sw): |n|
            ``nw    n    ne`` |n|
            ``w     c     e`` |n|
            ``sw    s    se``

        id : any
            the animation works by calling the animation_objects method of each component, optionally
            with id. By default, this is self, but can be overriden, particularly with the queue

        arg : any
            this is used when a parameter is a function with two parameters, as the first argument or
            if a parameter is a method as the instance |n|
            default: self (instance itself)

        Returns
        -------
        reference to AnimationQueue object : AnimationQueue

        Note
        ----
        It is recommended to use sim.AnimateQueue instead |n|

        All measures are in screen coordinates |n|

        All parameters, apart from queue and arg can be specified as: |n|
        - a scalar, like 10 |n|
        - a function with zero arguments, like lambda: title |n|
        - a function with one argument, being the time t, like lambda t: t + 10 |n|
        - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
        - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called

        """
        return AnimateQueue(self, *args, **kwargs)

    def animate3d(self, *args, **kwargs):
        """
        Animates the components in the queue in 3D.

        Parameters
        ----------
        x : float
            x-position of the first component in the queue |n|
            default: 0

        y : float
            y-position of the first component in the queue |n|
            default: 0

        z : float
            z-position of the first component in the queue |n|
            default: 0

        direction : str
            if "x+", waiting line runs in positive x direction (default) |n|
            if "x-", waiting line runs in negative x direction |n|
            if "y+", waiting line runs in positive y direction |n|
            if "y-", waiting line runs in negative y direction |n|
            if "z+", waiting line runs in positive z direction |n|
            if "z-", waiting line runs in negative z direction |n|

        reverse : bool
            if False (default), display in normal order. If True, reversed.

        max_length : int
            maximum number of components to be displayed

        layer : int
            layer (default 0)

        id : any
            the animation works by calling the animation_objects method of each component, optionally
            with id. By default, this is self, but can be overriden, particularly with the queue

        arg : any
            this is used when a parameter is a function with two parameters, as the first argument or
            if a parameter is a method as the instance |n|
            default: self (instance itself)

        Returns
        -------
        reference to Animation3dQueue object : Animation3dQueue

        Note
        ----
        It is recommended to use sim.AnimatedQueue instead |n|

        All parameters, apart from queue and arg can be specified as: |n|
        - a scalar, like 10 |n|
        - a function with zero arguments, like lambda: title |n|
        - a function with one argument, being the time t, like lambda t: t + 10 |n|
        - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
        - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called

        """
        return Animate3dQueue(self, *args, **kwargs)

    def all_monitors(self):
        """
        returns all monitors belonging to the queue

        Returns
        -------
        all monitors : tuple of monitors
        """
        return (self.length, self.length_of_stay)

    def reset_monitors(self, monitor=None, stats_only=None):
        """
        resets queue monitor length_of_stay and length

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change of monitoring state

        stats_only : bool
            if True, only statistics will be collected (using less memory, but also less functionality) |n|
            if False, full functionality |n|
            if omittted, no change of stats_only

        Note
        ----
        it is possible to reset individual monitoring with length_of_stay.reset() and length.reset()
        """
        self.length.reset(monitor=monitor, stats_only=stats_only)
        self.length_of_stay.reset(monitor=monitor, stats_only=stats_only)

    def arrival_rate(self, reset=False):
        """
        returns the arrival rate |n|
        When the queue is created, the registration is reset.

        Parameters
        ----------
        reset : bool
            if True, number_of_arrivals is set to 0 since last reset and the time of the last reset to now |n|
            default: False ==> no reset

        Returns
        -------
        arrival rate :  float
            number of arrivals since last reset / duration since last reset |n|
            nan if duration is zero
        """
        if reset:
            self.number_of_arrivals = 0
            self.number_of_arrivals_t0 = self.env._now
        duration = self.env._now - self.number_of_arrivals_t0
        if duration == 0:
            return nan
        else:
            return self.number_of_arrivals / duration

    def departure_rate(self, reset=False):
        """
        returns the departure rate |n|
        When the queue is created, the registration is reset.

        Parameters
        ----------
        reset : bool
            if True, number_of_departures is set to 0 since last reset and the time of the last reset to now |n|
            default: False ==> no reset

        Returns
        -------
        departure rate :  float
            number of departures since last reset / duration since last reset |n|
            nan if duration is zero
        """
        if reset:
            self.number_of_departures = 0
            self.number_of_departures_t0 = self.env._now
        duration = self.env._now - self.number_of_departures_t0
        if duration == 0:
            return nan
        else:
            return self.number_of_departures / duration

    def monitor(self, value):
        """
        enables/disables monitoring of length_of_stay and length

        Parameters
        ----------
        value : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|

        Note
        ----
        it is possible to individually control monitoring with length_of_stay.monitor() and length.monitor()
        """

        self.length.monitor(value=value)
        self.length_of_stay.monitor(value=value)

    def register(self, registry):
        """
        registers the queue in the registry

        Parameters
        ----------
        registry : list
            list of (to be) registered objects

        Returns
        -------
        queue (self) : Queue

        Note
        ----
        Use Queue.deregister if queue does not longer need to be registered.
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self in registry:
            raise ValueError(self.name() + " already in registry")
        registry.append(self)
        return self

    def deregister(self, registry):
        """
        deregisters the queue in the registry

        Parameters
        ----------
        registry : list
            list of registered queues

        Returns
        -------
        queue (self) : Queue
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self not in registry:
            raise ValueError(self.name() + " not in registry")
        registry.remove(self)
        return self

    def __repr__(self):
        return object_to_str(self) + " (" + self.name() + ")"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the queue

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append(object_to_str(self) + " " + hex(id(self)))
        result.append("  name=" + self.name())
        if self._length:
            result.append("  component(s):")
            mx = self._head.successor
            while mx != self._tail:
                result.append(
                    "    "
                    + pad(mx.component.name(), 20)
                    + " enter_time"
                    + self.env.time_to_str(mx.enter_time - self.env._offset)
                    + " priority="
                    + str(mx.priority)
                )
                mx = mx.successor
        else:
            result.append("  no components")
        return return_or_print(result, as_str, file)

    def print_statistics(self, as_str=False, file=None):
        """
        prints a summary of statistics of a queue

        Parameters
        ----------
        as_str: bool
            if False (default), print the statistics
            if True, return a string containing the statistics

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        statistics (if as_str is True) : str
        """
        result = []
        result.append(f"Statistics of {self.name()} at {fn(self.env._now - self.env._offset, 13, 3)}")
        result.append(self.length.print_statistics(show_header=False, show_legend=True, do_indent=True, as_str=True))

        result.append("")
        result.append(self.length_of_stay.print_statistics(show_header=False, show_legend=False, do_indent=True, as_str=True))
        return return_or_print(result, as_str, file)

    def print_histograms(self, exclude=(), as_str=False, file=None):
        """
        prints the histograms of the length and length_of_stay monitor of the queue

        Parameters
        ----------
        exclude : tuple or list
            specifies which monitors to exclude |n|
            default: () |n|

        as_str: bool
            if False (default), print the histograms
            if True, return a string containing the histograms

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        histograms (if as_str is True) : str
        """
        result = []
        for m in (self.length, self.length_of_stay):
            if m not in exclude:
                result.append(m.print_histogram(as_str=True))
        return return_or_print(result, as_str, file)

    def set_capacity(self, cap):
        """
        Parameters
        ----------
        cap : float or int
            capacity of the queue |n|
        """
        self.capacity.tally(cap)
        self.available_quantity.tally(cap - self._length)


    def name(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the queue
            if omitted, no change

        Returns
        -------
        Name of the queue : str

        Note
        ----
        base_name and sequence_number are not affected if the name is changed |n|
        All derived named are updated as well.
        """
        if value is not None:
            self._name = value
            self.length.name("Length of " + self.name())
            self.length_of_stay.name("Length of stay of " + self.name())
        return self._name

    def rename(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the queue
            if omitted, no change

        Returns
        -------
        self : queue

        Note
        ----
        in contrast to name(), this method returns itself, so can used to chain, e.g. |n|
        (q0 + q1 + q2 + q3).rename('q0 - q3').print_statistics() |n|
        (q1 - q0).rename('difference of q1 and q0)').print_histograms()
        """
        self.name(value)
        return self

    def base_name(self):
        """
        Returns
        -------
        base name of the queue (the name used at initialization): str
        """
        return self._base_name

    def sequence_number(self):
        """
        Returns
        -------
        sequence_number of the queue : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        """
        return self._sequence_number

    def add(self, component):
        """
        adds a component to the tail of a queue

        Parameters
        ----------
        component : Component
            component to be added to the tail of the queue |n|
            may not be member of the queue yet

        Note
        ----
        the priority will be set to
        the priority of the tail of the queue, if any
        or 0 if queue is empty |n|
        This method is equivalent to append()
        """
        component.enter(self)
        return self

    def append(self, component):
        """
        appends a component to the tail of a queue

        Parameters
        ----------
        component : Component
            component to be appened to the tail of the queue |n|
            may not be member of the queue yet

        Note
        ----
        the priority will be set to
        the priority of the tail of the queue, if any
        or 0 if queue is empty |n|
        This method is equivalent to add()
        """
        component.enter(self)
        return self

    def add_at_head(self, component):
        """
        adds a component to the head of a queue

        Parameters
        ----------

        component : Component
            component to be added to the head of the queue |n|
            may not be member of the queue yet

        Note
        ----
        the priority will be set to
        the priority of the head of the queue, if any
        or 0 if queue is empty
        """
        component.enter_at_head(self)
        return self

    def add_in_front_of(self, component, poscomponent):
        """
        adds a component to a queue, just in front of a component

        Parameters
        ----------
        component : Component
            component to be added to the queue |n|
            may not be member of the queue yet

        poscomponent : Component
            component in front of which component will be inserted |n|
            must be member of the queue

        Note
        ----
        the priority of component will be set to the priority of poscomponent
        """
        component.enter_in_front_of(self, poscomponent)
        return self

    def insert(self, index, component):
        """
        Insert component before index-th element of the queue

        Parameters
        ----------
        index : int
            component to be added just before index'th element |n|
            should be >=0 and <=len(self)

        component : Component
            component to be added to the queue

        Note
        ----
        the priority of component will be set to the priority of the index'th component,
        or 0 if the queue is empty
        """
        if index < 0:
            raise IndexError("index < 0")
        if index > self._length:
            raise IndexError("index > lengh of queue")
        component._checknotinqueue(self)
        mx = self._head.successor
        count = 0
        while mx != self._tail:
            if count == index:
                break
            count = count + 1
            mx = mx.successor
        priority = mx.priority
        Qmember().insert_in_front_of(mx, component, self, priority)
        return self

    def add_behind(self, component, poscomponent):
        """
        adds a component to a queue, just behind a component

        Parameters
        ----------
        component : Component
            component to be added to the queue |n|
            may not be member of the queue yet

        poscomponent : Component
            component behind which component will be inserted |n|
            must be member of the queue

        Note
        ----
        the priority of component will be set to the priority of poscomponent

        """
        component.enter_behind(self, poscomponent)
        return self

    def add_sorted(self, component, priority):
        """
        adds a component to a queue, according to the priority

        Parameters
        ----------
        component : Component
            component to be added to the queue |n|
            may not be member of the queue yet

        priority: type that can be compared with other priorities in the queue
            priority in the queue

        Note
        ----
        The component is placed just before the first component with a priority > given priority
        """
        component.enter_sorted(self, priority)
        return self

    def remove(self, component=None):
        """
        removes component from the queue

        Parameters
        ----------
        component : Component
            component to be removed |n|
            if omitted, all components will be removed.

        Note
        ----
        component must be member of the queue
        """
        if component is None:
            self.clear()
        else:
            component.leave(self)
        return self

    def head(self):
        """
        Returns
        -------
        the head component of the queue, if any. None otherwise : Component

        Note
        ----
        q[0] is a more Pythonic way to access the head of the queue
        """
        return self._head.successor.component

    def tail(self):
        """
        Returns
        -------
        the tail component of the queue, if any. None otherwise : Component

        Note
        -----
        q[-1] is a more Pythonic way to access the tail of the queue
        """
        return self._tail.predecessor.component

    def pop(self, index=None):
        """
        removes a component by its position (or head)

        Parameters
        ----------
        index : int
            index-th element to remove, if any |n|
            if omitted, return the head of the queue, if any

        Returns
        -------
        The i-th component or head : Component
            None if not existing
        """
        if index is None:
            c = self._head.successor.component
        else:
            c = self[index]
        if c is not None:
            c.leave(self)
        return c

    def successor(self, component):
        """
        successor in queue

        Parameters
        ----------
        component : Component
            component whose successor to return |n|
            must be member of the queue

        Returns
        -------
        successor of component, if any : Component
            None otherwise
        """
        return component.successor(self)

    def predecessor(self, component):
        """
        predecessor in queue

        Parameters
        ----------
        component : Component
            component whose predecessor to return |n|
            must be member of the queue

        Returns
        -------
        predecessor of component, if any : Component |n|
            None otherwise.
        """
        return component.predecessor(self)

    def __contains__(self, component):
        return component._member(self) is not None

    def __getitem__(self, key):
        if isinstance(key, slice):
            # Get the start, stop, and step from the slice
            startval, endval, incval = key.indices(self._length)
            if incval > 0:
                result = []
                targetval = startval
                mx = self._head.successor
                count = 0
                while mx != self._tail:
                    if targetval >= endval:
                        break
                    if targetval == count:
                        result.append(mx.component)
                        targetval += incval
                    count += 1
                    mx = mx.successor
            else:
                result = []
                targetval = startval
                mx = self._tail.predecessor
                count = self._length - 1
                while mx != self._head:
                    if targetval <= endval:
                        break
                    if targetval == count:
                        result.append(mx.component)
                        targetval += incval  # incval is negative here!
                    count -= 1
                    mx = mx.predecessor

            return list(result)

        elif isinstance(key, int):
            if key < 0:  # Handle negative indices
                key += self._length
            if key < 0 or key >= self._length:
                return None
            mx = self._head.successor
            count = 0
            while mx != self._tail:
                if count == key:
                    return mx.component
                count = count + 1
                mx = mx.successor

            return None  # just for safety

        else:
            raise TypeError("Invalid argument type: " + object_to_str(key))

    def __delitem__(self, key):
        if isinstance(key, slice):
            for c in self[key]:
                self.remove(c)
        elif isinstance(key, int):
            self.remove(self[key])
        else:
            raise TypeError("Invalid argument type:" + object_to_str(key))

    def __len__(self):
        return self._length

    def __reversed__(self):
        self._iter_sequence += 1
        iter_sequence = self._iter_sequence
        self._iter_touched[iter_sequence] = False
        iter_list = []
        mx = self._tail.predecessor
        while mx != self._head:
            iter_list.append(mx)
            mx = mx.predecessor
        iter_index = 0
        while len(iter_list) > iter_index or self._iter_touched[iter_sequence]:
            if self._iter_touched[iter_sequence]:
                # place all taken qmembers on the list
                iter_list = iter_list[:iter_index]
                mx = self._tail.predecessor
                while mx != self._head:
                    if mx not in iter_list:
                        iter_list.append(mx)
                    mx = mx.predecessor
                self._iter_touched[iter_sequence] = False
            else:
                c = iter_list[iter_index].component
                if c is not None:  # skip deleted components
                    yield c
                iter_index += 1

        del self._iter_touched[iter_sequence]

    def __add__(self, other):
        if not isinstance(other, Queue):
            return NotImplemented
        return self.union(other)

    def __radd__(self, other):
        if other == 0:  # to be able to use sum
            return self
        if not isinstance(other, Queue):
            return NotImplemented
        return self.union(other)

    def __or__(self, other):
        if not isinstance(other, Queue):
            return NotImplemented
        return self.union(other)

    def __sub__(self, other):
        if not isinstance(other, Queue):
            return NotImplemented
        return self.difference(other)

    def __and__(self, other):
        if not isinstance(other, Queue):
            return NotImplemented
        return self.intersection(other)

    def __xor__(self, other):
        if not isinstance(other, Queue):
            return NotImplemented
        return self.symmetric_difference(other)

    def _operator(self, other, op):
        if hasattr(other, "__iter__"):
            return op(set(self), set(other))
        return NotImplemented

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self._operator(other, operator.__eq__)

    def __ne__(self, other):
        return self._operator(other, operator.__ne__)

    def __lt__(self, other):
        return self._operator(other, operator.__lt__)

    def __le__(self, other):
        return self._operator(other, operator.__le__)

    def __gt__(self, other):
        return self._operator(other, operator.__gt__)

    def __ge__(self, other):
        return self._operator(other, operator.__ge__)

    def count(self, component):
        """
        component count

        Parameters
        ---------
        component : Component
            component to count

        Returns
        -------
        number of occurences of component in the queue

        Note
        ----
        The result can only be 0 or 1
        """
        return component.count(self)

    def index(self, component):
        """
        get the index of a component in the queue

        Parameters
        ----------
        component : Component
            component to be queried |n|
            does not need to be in the queue

        Returns
        -------
        index of component in the queue : int
            0 denotes the head, |n|
            returns -1 if component is not in the queue
        """
        return component.index(self)

    def component_with_name(self, txt):
        """
        returns a component in the queue according to its name

        Parameters
        ----------
        txt : str
            name of component to be retrieved

        Returns
        -------
        the first component in the queue with name txt : Component |n|
            returns None if not found
        """
        mx = self._head.successor
        while mx != self._tail:

            if mx.component.name() == txt:
                return mx.component
            mx = mx.successor
        return None

    def __iter__(self):
        self._iter_sequence += 1
        iter_sequence = self._iter_sequence
        self._iter_touched[iter_sequence] = False
        iter_list = []
        mx = self._head.successor
        while mx != self._tail:
            iter_list.append(mx)
            mx = mx.successor
        iter_index = 0
        while len(iter_list) > iter_index or self._iter_touched[iter_sequence]:
            if self._iter_touched[iter_sequence]:
                # place all taken qmembers on the list
                iter_list = iter_list[:iter_index]
                mx = self._head.successor
                while mx != self._tail:
                    if mx not in iter_list:
                        iter_list.append(mx)
                    mx = mx.successor
                self._iter_touched[iter_sequence] = False
            else:
                c = iter_list[iter_index].component
                if c is not None:  # skip deleted components
                    yield c
                iter_index += 1

        del self._iter_touched[iter_sequence]

    def extend(self, source, clear_source=False):
        """
        extends the queue with components of source that are not already in self (at the end of self)

        Parameters
        ----------
        source : queue, list or tuple

        clear_source : bool
            if False (default), the elements will remain in source |n|
            if True, source will be cleared, so effectively moving all elements in source to self. If source is
            not a queue, but a list or tuple, the clear_source flag may not be set.

        Returns
        -------
        None

        Note
        ----
        The components in source added to the queue will get the priority of the tail of self.
        """
        savetrace = self.env._trace
        count = 0
        self.env._trace = False
        for c in source:
            if c not in self:
                c.enter(self)
                count += 1
        self.env._trace = savetrace
        if self.env._trace:
            self.env.print_trace(
                "",
                "",
                self.name()
                + " extend from "
                + (source.name() if isinstance(source, Queue) else "instance of " + str(type(source)))
                + " ("
                + str(count)
                + " components)",
            )
        if clear_source:
            if isinstance(source, Queue):
                source.clear()
            else:
                raise TypeError("clear_source cannot be applied to instances of type" + str(type(source)))

    def as_set(self):
        return {c for c in self}

    def as_list(self):
        return [c for c in self]

    def union(self, q, name=None, monitor=False):
        """
        Parameters
        ----------
        q : Queue
            queue to be unioned with self

        name : str
            name of the  new queue |n|
            if omitted, self.name() + q.name()

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the queue

        Returns
        -------
        queue containing all elements of self and q : Queue

        Note
        ----
        the priority will be set to 0 for all components in the
        resulting  queue |n|
        the order of the resulting queue is as follows: |n|
        first all components of self, in that order,
        followed by all components in q that are not in self,
        in that order. |n|
        Alternatively, the more pythonic | operator is also supported, e.g. q1 | q2
        """
        save_trace = self.env._trace
        self.env._trace = False
        if name is None:
            name = self.name() + " | " + q.name()
        q1 = type(self)(name=name, monitor=monitor, env=self.env)
        self_set = self.as_set()

        mx = self._head.successor
        while mx != self._tail:
            Qmember().insert_in_front_of(q1._tail, mx.component, q1, 0)
            mx = mx.successor

        mx = q._head.successor
        while mx != q._tail:
            if mx.component not in self_set:
                Qmember().insert_in_front_of(q1._tail, mx.component, q1, 0)
            mx = mx.successor

        self.env._trace = save_trace
        return q1

    def intersection(self, q, name=None, monitor=False):
        """
        returns the intersect of two queues

        Parameters
        ----------
        q : Queue
            queue to be intersected with self

        name : str
            name of the  new queue |n|
            if omitted, self.name() + q.name()

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the queue

        Returns
        -------
        queue with all elements that are in self and q : Queue

        Note
        ----
        the priority will be set to 0 for all components in the
        resulting  queue |n|
        the order of the resulting queue is as follows: |n|
        in the same order as in self. |n|
        Alternatively, the more pythonic & operator is also supported, e.g. q1 & q2
        """
        save_trace = self.env._trace
        self.env._trace = False
        if name is None:
            name = self.name() + " & " + q.name()
        q1 = type(self)(name=name, monitor=monitor, env=self.env)
        q_set = q.as_set()
        mx = self._head.successor
        while mx != self._tail:
            if mx.component in q_set:
                Qmember().insert_in_front_of(q1._tail, mx.component, q1, 0)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def difference(self, q, name=None, monitor=monitor):
        """
        returns the difference of two queues

        Parameters
        ----------
        q : Queue
            queue to be 'subtracted' from self

        name : str
            name of the  new queue |n|
            if omitted, self.name() - q.name()

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the queue

        Returns
        -------
        queue containing all elements of self that are not in q

        Note
        ----
        the priority will be copied from the original queue.
        Also, the order will be maintained. |n|
        Alternatively, the more pythonic - operator is also supported, e.g. q1 - q2
        """
        if name is None:
            name = self.name() + " - " + q.name()
        save_trace = self.env._trace
        self.env._trace = False
        q1 = type(self)(name=name, monitor=monitor, env=self.env)
        q_set = q.as_set()
        mx = self._head.successor
        while mx != self._tail:
            if mx.component not in q_set:
                Qmember().insert_in_front_of(q1._tail, mx.component, q1, mx.priority)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def symmetric_difference(self, q, name=None, monitor=monitor):
        """
        returns the symmetric difference of two queues

        Parameters
        ----------
        q : Queue
            queue to be 'subtracted' from self

        name : str
            name of the  new queue |n|
            if omitted, self.name() - q.name()

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the queue

        Returns
        -------
        queue containing all elements that are either in self or q, but not in both

        Note
        ----
        the priority of all elements will be set to 0 for all components in the new queue.
        Order: First, elelements in self (in that order), then elements in q (in that order)
        Alternatively, the more pythonic ^ operator is also supported, e.g. q1 ^ q2
        """
        if name is None:
            name = self.name() + " ^ " + q.name()
        save_trace = self.env._trace
        self.env._trace = False
        q1 = type(self)(name=name, monitor=monitor, env=self.env)

        intersection_set = self.as_set() & q.as_set()
        mx = self._head.successor
        while mx != self._tail:
            if mx.component not in intersection_set:
                Qmember().insert_in_front_of(q1._tail, mx.component, q1, 0)
            mx = mx.successor
        mx = q._head.successor
        while mx != q._tail:
            if mx.component not in intersection_set:
                Qmember().insert_in_front_of(q1._tail, mx.component, q1, 0)
            mx = mx.successor

        self.env._trace = save_trace
        return q1

    def copy(self, name=None, copy_capacity=False, monitor=monitor):
        """
        returns a copy of a queue

        Parameters
        ----------
        name : str
            name of the new queue |n|
            if omitted, "copy of " + self.name()

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the queue

        copy_capacity : bool
            if True, the capacity will be copied |n|
            if False (default), the resulting queue will always be unrestricted

        Returns
        -------
        queue with all elements of self : Queue

        Note
        ----
        The priority will be copied from original queue.
        Also, the order will be maintained.
        """
        save_trace = self.env._trace
        self.env._trace = False
        if name is None:
            name = "copy of " + self.name()
        q1 = type(self)(name=name, monitor=monitor, env=self.env)
        if copy_capacity:
            q1.capacity._tally = self.capacity._tally
        mx = self._head.successor
        while mx != self._tail:
            Qmember().insert_in_front_of(q1._tail, mx.component, q1, mx.priority)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def move(self, name=None, monitor=monitor, copy_capacity=False):
        """
        makes a copy of a queue and empties the original

        Parameters
        ----------
        name : str
            name of the new queue

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the yqueue

        copy_capacity : bool
            if True, the capacity will be copied |n|
            if False (default), the new queue will always be unrestricted

        Returns
        -------
        queue containing all elements of self: Queue
        the capacity of the original queue will not be changed

        Note
        ----
        Priorities will be kept |n|
        self will be emptied
        """
        q1 = self.copy(name, monitor=monitor, copy_capacity=copy_capacity)
        self.clear()
        return q1

    def clear(self):
        """
        empties a queue

        removes all components from a queue
        """
        savetrace = self.env._trace
        self.env._trace = False
        mx = self._head.successor
        while mx != self._tail:
            c = mx.component
            mx = mx.successor
            c.leave(self)
        self.env._trace = savetrace
        if self.env._trace:
            self.env.print_trace("", "", self.name() + " clear")


class Animate3dBase(DynamicClass):
    """
    Base class for a 3D animation object |n|
    When a class inherits from this base class, it will be added to the animation objects list to be shown

    Parameters
    ----------
    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, visible=True, keep=True, arg=None, layer=0, parent=None, env=None, **kwargs):
        super().__init__()
        self.env = g.default_env if env is None else env
        self.visible = visible
        self.keep = keep
        self.arg = self if arg is None else arg
        self.layer = layer
        if parent is not None:
            if not isinstance(parent, Component):
                raise ValueError(repr(parent) + " is not a component")
            parent._animation_children.add(self)

        self.sequence = self.env.serialize()
        self.env.an_objects3d.add(self)
        self.register_dynamic_attributes("visible keep layer")
        self.setup(**kwargs)

    def setup(self):
        """
        called immediately after initialization of a the Animate3dBase object.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments will be passed

        Example
        -------
            class AnimateVehicle(sim.Animate3dBase):
                def setup(self, length):
                    self.length = length
                    self.register_dynamic_attributes("length")

                ...
        """
        pass

    def show(self):
        """
        show (unremove)

        It is possible to use this method if already shown
        """
        self.env.an_objects3d.add(self)

    def remove(self):
        """
        removes the 3d animation oject
        """
        self.env.an_objects3d.discard(self)

    def is_removed(self):
        return self in self.env.an_objects3d


class _Movement:  # used by trajectories
    def __init__(self, l, vmax=None, v0=None, v1=None, acc=None, dec=None):
        if vmax is None:
            vmax = 1
        if v0 is None:
            v0 = vmax
        if v1 is None:
            v1 = vmax
        if acc is None:
            acc = math.inf
        if dec is None:
            dec = math.inf

        acc2inv = 1 / (2 * acc)
        dec2inv = 1 / (2 * dec)
        s_v0_vmax = (vmax**2 - v0**2) * acc2inv
        s_vmax_v1 = (vmax**2 - v1**2) * dec2inv

        if s_v0_vmax + s_vmax_v1 > l:
            vmax = math.sqrt((l + (v0**2 * acc2inv) + (v1**2 * dec2inv)) / (acc2inv + dec2inv))

        self.l_v0_vmax = (vmax**2 - v0**2) * acc2inv
        self.l_vmax_v1 = (vmax**2 - v1**2) * dec2inv

        self.l_vmax = l - self.l_v0_vmax - self.l_vmax_v1
        if self.l_v0_vmax < 0 or self.l_vmax_v1 < 0:
            raise ValueError("not feasible")
        self.t_v0_vmax = (vmax - v0) / acc
        self.t_vmax = self.l_vmax / vmax
        self.t_vmax_v1 = (vmax - v1) / dec
        self.t = self.t_v0_vmax + self.t_vmax + self.t_vmax_v1
        self.v0 = v0
        self.vmax = vmax
        self.acc = acc
        self.dec = dec

    def l_at_t(self, t):
        if t < 0:
            return 0
        if self.acc == math.inf and self.dec == math.inf:
            return self.vmax * t
        if t < self.t_v0_vmax:
            return (self.v0 * t) + self.acc * t**2 / 2
        t -= self.t_v0_vmax
        if t < self.t_vmax:
            return self.l_v0_vmax + t * self.vmax
        t -= self.t_vmax
        if self.dec == math.inf:
            return self.l_v0_vmax + self.l_vmax + (self.vmax * t)
        return self.l_v0_vmax + self.l_vmax + (self.vmax * t) - self.dec * t**2 / 2


class _Trajectory:  # used by trajectories
    def in_trajectory(self, t):
        return self._t0 <= t <= self._t1

    def t0(self):
        return self._t0

    def t1(self):
        return self._t1

    def duration(self):
        return self._duration

    def rendered_polygon(self, time_step=1):
        result = []
        for t in arange(self.t0(), self.t1(), time_step):
            result.extend([self.x(t), self.y(t)])
        result.extend([self.x(self.t1()), self.y(self.t1())])
        return result

    def __add__(self, other):
        if other == 0:
            return self
        if not isinstance(other, _Trajectory):
            return NotImplemented
        return TrajectoryMerged([self, other])

    __radd__ = __add__


class TrajectoryMerged(_Trajectory):
    """
    merge trajectories

    Parameters
    ----------
    trajectories : iterable (list, tuple, ...)
        list trajectories to be merged

    Returns
    -------
    merged trajectory : Trajectory

    Notes
    -----
    It is arguably easier just to add or sum trajectories, like |n|

        trajectory = trajectory1 + trajectory2 + trajectory3 or |n|
        trajectory = sum((trajectory, trajectory2, trajectory3))
    """

    @functools.lru_cache(maxsize=1)
    def index(self, t):
        if t <= self._t0s[0]:
            return 0
        if t >= self._t0s[-1]:
            return len(self._t0s) - 1
        i = searchsorted(self._t0s, t, "left") - 1
        return i

    def __init__(self, trajectories):
        self._trajectories = trajectories
        self._duration = sum(trajectory._duration for trajectory in self._trajectories)
        self._t0 = 0
        self._t1 = self._t0 + self._duration
        self._length = sum(trajectory._length for trajectory in self._trajectories)
        cum_length = 0
        _t0 = self._t0
        self.cum_lengths = []
        self._t0s = []
        for trajectory in self._trajectories:
            self.cum_lengths.append(cum_length)
            self._t0s.append(_t0)
            cum_length += trajectory._length
            _t0 += trajectory._duration
        self.cum_lengths.append(cum_length)
        self._length = cum_length

    def __init__(self, trajectories):
        self._trajectories = trajectories
        self._duration = sum(trajectory._duration for trajectory in self._trajectories)
        self._t0 = trajectories[0]._t0
        self._t1 = self._t0 + self._duration
        self._length = sum(trajectory._length for trajectory in self._trajectories)
        cum_length = 0
        _t0 = self._t0
        self.cum_lengths = []
        self._t0s = []
        for trajectory in self._trajectories:
            self.cum_lengths.append(cum_length)
            self._t0s.append(_t0)
            cum_length += trajectory._length
            _t0 += trajectory._duration
        self.cum_lengths.append(cum_length)
        self._length = cum_length

    def __repr__(self):
        return f"TrajectoryMerged(t0={self._t0}, trajectories={self._trajectories}, t0s={self._t0s})"

    def x(self, t, _t0=None):
        """
        value of x

        Parameters
        ----------
        t : float
            time at which to evaluate x

        Returns
        -------
        evaluated x : float
        """
        i = self.index(t)
        trajectory = self._trajectories[i]
        t0 = self._t0s[i]
        return trajectory.x(t=t, _t0=t0)

    def y(self, t, _t0=None):
        """
        value of y

        Parameters
        ----------
        t : float
            time at which to evaluate y

        Returns
        -------
        evaluated y : float
        """
        i = self.index(t)
        trajectory = self._trajectories[i]
        t0 = self._t0s[i]
        return trajectory.y(t=t, _t0=t0)

    def angle(self, t, _t0=None):
        """
        value of angle (in degrees)

        Parameters
        ----------
        t : float
            time at which to evaluate angle

        Returns
        -------
        evaluated angle (in degrees) : float
        """
        i = self.index(t)
        trajectory = self._trajectories[i]
        t0 = self._t0s[i]
        return trajectory.angle(t=t, _t0=t0)

    def in_trajectory(self, t):
        """
        is t in trajectory?

        Parameters
        ----------
        t : float
            time at which to evaluate

        Returns
        -------
        is t in trajectory? : bool
        """
        return super().in_trajectory(t)

    def t0(self):
        """
        start time of trajectory

        Returns
        -------
        start time of trajectory : float
        """
        return super().t0()

    def t1(self):
        """
        end time of trajectory

        Returns
        -------
        end time of trajectory : float
        """
        return super().t1()

    def duration(self):
        """
        duration of trajectory

        Returns
        -------
        duration of trajectory (t1 - t0): float
        """
        return super().duration()

    def length(self, t=None, _t0=None):
        """
        length of traversed trajectory at time t or total length

        Parameters
        ----------
        t : float
            time at which to evaluate length. If omitted, total length will be returned

        Returns
        -------
        length : float
            length of traversed trajectory at time t or |n|
            total length if t omitted
        """
        i = self.index(t)
        trajectory = self._trajectories[i]
        t0 = self._t0s[i]
        return trajectory.length(t=t, _t0=t0) + self.cum_lengths[i]

    def rendered_polygon(self, time_step=1):
        """
        rendered polygon

        Parameters
        ----------
        time_step : float
            defines at which point in time the trajectory has to be rendered |n|
            default : 1

        Returns
        -------
        polygon : list of x, y
            rendered from t0 to t1 with time_step |n|
            can be used directly in sim.AnimatePoints() or AnimatePolygon()
        """
        return super().rendered_polygon(time_step)


class TrajectoryStandstill(_Trajectory):
    """
    Standstill trajectory, to be used in Animatexxx through x, y and angle methods

    Parameters
    ----------
    xy : tuple or list of 2 floats
        initial (and final) position. should be like x, y

    orientation : float or callable
        orientation (angle) in degrees |n|
        a one parameter callable is also accepted (and will be called with 0) |n|
        default: 0

    t0 : float
        time the trajectory should start |n|
        default: env.now() |n|
        if not the first in a merged trajectory or AnimateQueue, ignored

    env : Environment
        environment where the trajectory is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, xy, duration, orientation=0, t0=None, env=None):
        env = g.default_env if env is None else env
        self._t0 = env.now() if t0 is None else t0
        self._x, self._y = xy
        self._duration = duration
        self._length = 0
        self._t1 = self._t0 + duration
        if callable(orientation):
            self._angle = orientation(0)
        else:
            self._angle = orientation

    def x(self, t, _t0=None):
        """
        value of x

        Parameters
        ----------
        t : float
            time at which to evaluate x

        Returns
        -------
        evaluated x : float
        """
        return self._x

    def y(self, t, _t0=None):
        """
        value of y

        Parameters
        ----------
        t : float
            time at which to evaluate y

        Returns
        -------
        evaluated y : float
        """
        return self._y

    def angle(self, t, _t0=None):
        """
        value of angle (in degrees)

        Parameters
        ----------
        t : float
            time at which to evaluate angle

        Returns
        -------
        evaluated angle (in degrees) : float
        """
        return self._angle

    def in_trajectory(self, t):
        """
        is t in trajectory?

        Parameters
        ----------
        t : float
            time at which to evaluate

        Returns
        -------
        is t in trajectory? : bool
        """
        return super().in_trajectory(t)

    def t0(self):
        """
        start time of trajectory

        Returns
        -------
        start time of trajectory : float
        """
        return super().t0()

    def t1(self):
        """
        end time of trajectory

        Returns
        -------
        end time of trajectory : float
        """
        return super().t1()

    def duration(self):
        """
        duration of trajectory

        Returns
        -------
        duration of trajectory (t1 - t0): float
        """
        return super().duration()

    def length(self, t=None, _t0=None):
        """
        length of traversed trajectory at time t or total length

        Parameters
        ----------
        t : float
            time at which to evaluate length.

        Returns
        -------
        length : float
            always 0 |n|
        """
        return 0

    def rendered_polygon(self, time_step=1):
        """
        rendered polygon

        Parameters
        ----------
        time_step : float
            defines at which point in time the trajectory has to be rendered |n|
            default : 1

        Returns
        -------
        polygon : list of x, y
            rendered from t0 to t1 with time_step |n|
            can be used directly in sim.AnimatePoints() or AnimatePolygon()
        """
        return super().rendered_polygon(time_step)


class TrajectoryPolygon(_Trajectory):
    """
    Polygon trajectory, to be used in Animatexxx through x, y and angle methods

    Parameters
    ----------
    polygon : iterable of floats
        should be like x0, y0, x1, y1, ...

    t0 : float
        time the trajectory should start |n|
        default: env.now() |n|
        if not the first in a merged trajectory or AnimateQueue, ignored

    vmax : float
        maximum speed, i.e. position units per time unit |n|
        default: 1

    v0 : float
        velocity at start |n|
        default: vmax

    v1 : float
        velocity at end |n|
        default: vmax

    acc : float
        acceleration rate (position units / time units ** 2) |n|
        default: inf (i.e. no acceleration)

    dec : float
        deceleration rate (position units / time units ** 2) |n|
        default: inf (i.e. no deceleration)

    orientation : float
        default: gives angle in the direction of the movement when calling angle(t) |n|
        if a one parameter callable, the angle in the direction of the movement will be callled |n|
        if a float, this orientation will always be returned as angle(t)

    spline : None or string
        if None (default), polygon is used as such |n|
        if 'bezier' (or any string starting with 'b' or 'B', Bézier splining is used |n|
        if 'catmull_rom' (or any string starting with 'c' or 'C', Catmull-Rom splining is used

    res : int
        resolution of spline (ignored when no splining is applied)

    env : Environment
        environment where the trajectory is defined |n|
        if omitted, default_env will be used

    Notes
    -----
    bezier and catmull_rom splines require numpy to be installed.
    """

    def __init__(self, polygon, t0=None, vmax=None, v0=None, v1=None, acc=None, dec=None, orientation=None, spline=None, res=50, env=None):
        def catmull_rom_polygon(polygon, res):
            def evaluate(x, v0, v1, v2, v3):
                c1 = 1.0 * v1
                c2 = -0.5 * v0 + 0.5 * v2
                c3 = 1.0 * v0 + -2.5 * v1 + 2.0 * v2 - 0.5 * v3
                c4 = -0.5 * v0 + 1.5 * v1 + -1.5 * v2 + 0.5 * v3
                return ((c4 * x + c3) * x + c2) * x + c1

            if not has_numpy():
                raise ImportError("catmull_rom trajectory requires numpy")

            p_x = []
            p_y = []
            for x, y in zip(polygon[::2], polygon[1::2]):
                p_x.append(x)
                p_y.append(y)

            _x = numpy.empty(res * (len(p_x) - 1) + 1)
            _y = numpy.empty(res * (len(p_x) - 1) + 1)

            _x[-1] = p_x[-1]
            _y[-1] = p_y[-1]

            for i in range(len(p_x) - 1):
                _x[i * res : (i + 1) * res] = numpy.linspace(p_x[i], p_x[i + 1], res, endpoint=False)
                numpy.linspace(polygon[i * 2], polygon[i * 2 + 2], res, endpoint=False)
                _y[i * res : (i + 1) * res] = numpy.array(
                    [
                        evaluate(
                            x,
                            p_y[0] - (p_y[1] - p_y[0]) if i == 0 else p_y[i - 1],
                            p_y[i],
                            p_y[i + 1],
                            p_y[i + 1] + (p_y[i + 1] - p_y[i]) if i == len(p_x) - 2 else p_y[i + 2],
                        )
                        for x in numpy.linspace(0.0, 1.0, res, endpoint=False)
                    ]
                )
            polygon = []
            for xy in zip(_x, _y):
                polygon.extend(xy)
            return polygon

        def bezier_polygon(polygon, res):
            # based on https://github.com/torresjrjr/Bezier.py

            def bezier_curve(t_values, points):
                def two_points(t, P1, P2):
                    return (1 - t) * P1 + t * P2

                def do_points(t, points):
                    newpoints = []
                    for i1 in range(0, len(points) - 1):
                        newpoints += [two_points(t, points[i1], points[i1 + 1])]
                    return newpoints

                def do_point(t, points):
                    newpoints = points
                    while len(newpoints) > 1:
                        newpoints = do_points(t, newpoints)
                    return newpoints[0]

                curve = numpy.array([[0.0] * len(points[0])])
                for t in t_values:
                    curve = numpy.append(curve, [do_point(t, points)], axis=0)
                curve = numpy.delete(curve, 0, 0)
                return curve

            if not has_numpy():
                raise ImportError("bezier trajectory requires numpy")
            points = []
            for x, y in zip(polygon[::2], polygon[1::2]):
                points.append([x, y])
            points = numpy.array(points)
            t_points = numpy.linspace(0, 1, res)

            polygon = []
            curve = bezier_curve(t_points, points)
            for xy in curve:
                polygon.extend(xy)
            return polygon

        if spline is not None:
            if isinstance(spline, str) and spline.lower().startswith("c"):
                polygon = catmull_rom_polygon(polygon, res=res)
            elif isinstance(spline, str) and spline.lower().startswith("b"):
                polygon = bezier_polygon(polygon, res=res)
            else:
                raise ValueError(f"spline {spline} not recognized")

        env = g.default_env if env is None else env
        self._t0 = env.now() if t0 is None else t0

        cum_length = 0
        self.cum_length = []
        self._x = []
        self._y = []
        self._angle = []
        for x, y, next_x, next_y in zip(polygon[::2], polygon[1::2], polygon[2::2], polygon[3::2]):
            dx = next_x - x
            dy = next_y - y
            if orientation is None:
                self._angle.append(math.degrees(math.atan2(dy, dx)))
            else:
                if callable(orientation):
                    self._angle.append(orientation(math.degrees(math.atan2(dy, dx))))
                else:
                    self._angle.append(orientation)
            self._x.append(x)
            self._y.append(y)
            self.cum_length.append(cum_length)
            segment_length = math.sqrt(dx * dx + dy * dy)
            cum_length += segment_length
        self._x.append(next_x)
        self._y.append(next_y)
        self._angle.append(self._angle[-1])
        self.cum_length.append(cum_length)

        self._length = self.cum_length[-1]
        self.movement = _Movement(l=self._length, v0=v0, v1=v1, vmax=vmax, acc=acc, dec=dec)
        self._duration = self.movement.t
        self._t1 = self._t0 + self._duration

    def __repr__(self):
        return f"TrajectoryPolygon(t0={self._t0})"

    @functools.lru_cache(maxsize=1)
    def indexes(self, t, _t0=None):
        t = t - (self._t0 if _t0 is None else _t0)

        length = self.movement.l_at_t(t)

        if length <= self.cum_length[0]:
            return length, 0, 0
        if length >= self.cum_length[-1]:
            return length, len(self.cum_length) - 1, len(self.cum_length) - 1

        i = searchsorted(self.cum_length, length) - 1
        return length, i, i + 1

    def x(self, t, _t0=None):
        """
        value of x

        Parameters
        ----------
        t : float
            time at which to evaluate x

        Returns
        -------
        evaluated x : float
        """
        length, i, j = self.indexes(t, _t0=_t0)
        return interp(length, [self.cum_length[i], self.cum_length[j]], [self._x[i], self._x[j]])

    def y(self, t, _t0=None):
        """
        value of y

        Parameters
        ----------
        t : float
            time at which to evaluate y

        Returns
        -------
        evaluated y : float
        """
        length, i, j = self.indexes(t, _t0=_t0)
        return interp(length, [self.cum_length[i], self.cum_length[j]], [self._y[i], self._y[j]])

    def angle(self, t, _t0=None):
        """
        value of angle (in degrees)

        Parameters
        ----------
        t : float
            time at which to evaluate angle

        Returns
        -------
        evaluated angle (in degrees) : float
        """
        length, i, j = self.indexes(t, _t0=_t0)
        return self._angle[i]

    def in_trajectory(self, t):
        """
        is t in trajectory?

        Parameters
        ----------
        t : float
            time at which to evaluate

        Returns
        -------
        is t in trajectory? : bool
        """
        return super().in_trajectory(t)

    def t0(self):
        """
        start time of trajectory

        Returns
        -------
        start time of trajectory : float
        """
        return super().t0()

    def t1(self):
        """
        end time of trajectory

        Returns
        -------
        end time of trajectory : float
        """
        return super().t1()

    def duration(self):
        """
        duration of trajectory

        Returns
        -------
        duration of trajectory (t1 - t0): float
        """
        return super().duration()

    def length(self, t=None, _t0=None):
        """
        length of traversed trajectory at time t or total length

        Parameters
        ----------
        t : float
            time at which to evaluate lenght. If omitted, total length will be returned

        Returns
        -------
        length : float
            length of traversed trajectory at time t or |n|
            total length if t omitted
        """
        length, i, j = self.indexes(t, _t0=_t0)
        return self.cum_length[i] + length

    def rendered_polygon(self, time_step=1):
        """
        rendered polygon

        Parameters
        ----------
        time_step : float
            defines at which point in time the trajectory has to be rendered |n|
            default : 1

        Returns
        -------
        polygon : list of x, y
            rendered from t0 to t1 with time_step |n|
            can be used directly in sim.AnimatePoints() or AnimatePolygon()
        """
        return super().rendered_polygon(time_step)


class TrajectoryCircle(_Trajectory):
    """
    Circle (arc) trajectory, to be used in Animatexxx through x, y and angle methods

    Parameters
    ----------
    radius : float
        radius of the circle or arc

    x_center : float
        x-coordinate of the circle

    y_center : float
        y-coordinate of the circle

    angle0 : float
        start angle in degrees |n|
        default: 0

    angle1 : float
        end angle in degrees |n|
        default: 360

    t0 : float
        time the trajectory should start |n|
        default: env.now() |n|
        if not the first in a merged trajectory or AnimateQueue, ignored

    vmax : float
        maximum speed, i.e. position units per time unit |n|
        default: 1

    v0 : float
        velocity at start |n|
        default: vmax

    v1 : float
        velocity at end |n|
        default: vmax

    acc : float
        acceleration rate (position units / time units ** 2) |n|
        default: inf (i.e. no acceleration)

    dec : float
        deceleration rate (position units / time units ** 2) |n|
        default: inf (i.e. no deceleration)

    orientation : float
        default: gives angle in the direction of the movement when calling angle(t) |n|
        if a one parameter callable, the angle in the direction of the movement will be callled |n|
        if a float, this orientation will always be returned as angle(t)

    env : Environment
        environment where the trajectory is defined |n|
        if omitted, default_env will be used
    """

    def __init__(
        self, radius, x_center=0, y_center=0, angle0=0, angle1=360, t0=None, vmax=None, v0=None, v1=None, acc=None, dec=None, orientation=None, env=None
    ):
        env = g.default_env if env is None else env
        self._t0 = env.now() if t0 is None else t0
        self.radius = radius
        self.angle0 = angle0
        self.angle1 = angle1
        self.x_center = x_center
        self.y_center = y_center
        self._length = abs(math.radians(self.angle1 - self.angle0)) * self.radius
        self.movement = _Movement(l=self._length, v0=v0, v1=v1, vmax=vmax, acc=acc, dec=dec)
        self._duration = self.movement.t
        self._t1 = self._t0 + self._duration
        self.orientation = orientation

    def __repr__(self):
        return f"TrajectoryCircle(t0={self._t0})"

    def x(self, t, _t0=None):
        length = self.length(t, _t0=_t0)
        return self.x_center + self.radius * math.cos(math.radians(interp(length, (0, self._length), (self.angle0, self.angle1))))

    def y(self, t, _t0=None):
        length = self.length(t, _t0=_t0)
        return self.y_center + self.radius * math.sin(math.radians(interp(length, (0, self._length), (self.angle0, self.angle1))))

    def angle(self, t, _t0=None):
        length = self.length(t, _t0=_t0)
        if self.angle0 < self.angle1:
            result = interp(length, (0, self._length), (self.angle0, self.angle1)) + 90
        else:
            result = interp(length, (0, self._length), (self.angle0, self.angle1)) - 90

        if self.orientation is None:
            return result

        if callable(self.orientation):
            return self.orientation(result)
        return self.orientation

    def in_trajectory(self, t):
        """
        is t in trajectory?

        Parameters
        ----------
        t : float
            time at which to evaluate

        Returns
        -------
        is t in trajectory? : bool
        """
        return super().in_trajectory(t)

    def t0(self):
        """
        start time of trajectory

        Returns
        -------
        start time of trajectory : float
        """
        return super().t0()

    def t1(self):
        """
        end time of trajectory

        Returns
        -------
        end time of trajectory : float
        """
        return super().t1()

    def duration(self):
        """
        duration of trajectory

        Returns
        -------
        duration of trajectory (t1 - t0): float
        """
        return super().duration()

    @functools.lru_cache(maxsize=1)
    def length(self, t=None, _t0=None):
        """
        length of traversed trajectory at time t or total length

        Parameters
        ----------
        t : float
            time at which to evaluate lenght. If omitted, total length will be returned

        Returns
        -------
        length : float
            length of traversed trajectory at time t or |n|
            total length if t omitted
        """
        t0 = self._t0 if _t0 is None else _t0
        t1 = t0 + self._duration
        if t < t0:
            t = t0
        elif t > t1:
            t = t1
        return self.movement.l_at_t(t - t0)

    def rendered_polygon(self, time_step=1):
        """
        rendered polygon

        Parameters
        ----------
        time_step : float
            defines at which point in time the trajectory has to be rendered |n|
            default : 1

        Returns
        -------
        polygon : list of x, y
            rendered from t0 to t1 with time_step |n|
            can be used directly in sim.AnimatePoints() or AnimatePolygon()
        """
        return super().rendered_polygon(time_step)


class Environment:
    """
    environment object

    Parameters
    ----------
    trace : bool or file handle
        defines whether to trace or not |n|
        if this a file handle (open for write), the trace output will be sent to this file. |n|
        if omitted, False

    random_seed : hashable object, usually int
        the seed for random, equivalent to random.seed() |n|
        if "*", a purely random value (based on the current time) will be used
        (not reproducable) |n|
        if the null string, no action on random is taken |n|
        if None (the default), 1234567 will be used.

    time_unit : str
        Supported time_units: |n|
        "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds", "n/a" |n|
        default: "n/a"

    datetime0: bool or datetime.datetime
        display time and durations as datetime.datetime/datetime.timedelta |n|
        if falsy (default), disabled |n|
        if True, the t=0 will correspond to 1 January 1970 |n|
        if no time_unit is specified, but datetime0 is not falsy, time_unit will be set to seconds

    name : str
        name of the environment |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class (lowercased)
        or "default environment" if isdefault_env is True.

    print_trace_header : bool
        if True (default) print a (two line) header line as a legend |n|
        if False, do not print a header |n|
        note that the header is only printed if trace=True

    isdefault_env : bool
        if True (default), this environment becomes the default environment |n|
        if False, this environment will not be the default environment |n|
        if omitted, this environment becomes the default environment |n|

    set_numpy_random_seed : bool
        if True (default), numpy.random.seed() will be called with the given seed. |n|
        This is particularly useful when using External distributions. |n|
        If numpy is not installed, this parameter is ignored |n|
        if False, numpy.random.seed is not called.

    do_reset : bool
        if True, reset the simulation environment |n|
        if False, do not reset the simulation environment |n|
        if None (default), reset the simulation environment when run under Pythonista, otherwise no reset

    blind_animation : bool
        if False (default), animation will be performed as expected |n|
        if True, animations will run silently. This is useful to make videos when tkinter is not installed (installable).
        This is particularly useful when running a simulation on a server.
        Note that this will show a slight performance increase, when creating videos.

    Note
    ----
    The trace may be switched on/off later with trace |n|
    The seed may be later set with random_seed() |n|
    Initially, the random stream will be seeded with the value 1234567.
    If required to be purely, not reproducable, values, use
    random_seed="*".
    """

    _nameserialize = {}
    cached_modelname_width = [None, None]

    def __init__(
        self,
        trace=False,
        random_seed=None,
        set_numpy_random_seed=True,
        time_unit="n/a",
        datetime0=False,
        name=None,
        print_trace_header=True,
        isdefault_env=True,
        retina=False,
        do_reset=None,
        blind_animation=False,
        *args,
        **kwargs,
    ):
        if name is None:
            if isdefault_env:
                name = "default environment"
        _set_name(name, Environment._nameserialize, self)
        self._nameserializeMonitor = {}  # required here for to_freeze functionality
        self._time_unit = _time_unit_lookup(time_unit)
        self._time_unit_name = time_unit
        if datetime0 is None:
            datetime0 = False
        self.datetime0(datetime0)
        if "to_freeze" in kwargs:
            self.isfrozen = True
            return
        if do_reset is None:
            do_reset = Pythonista
        if do_reset:
            reset()
        if isdefault_env:
            g.default_env = self
        self.trace(trace)
        self._source_files = {inspect.getframeinfo(_get_caller_frame()).filename: 0}
        _random_seed(random_seed, set_numpy_random_seed=set_numpy_random_seed)
        self._suppress_trace_standby = True
        self._suppress_trace_linenumbers = False
        if self._trace:
            if print_trace_header:
                self.print_trace_header()
            self.print_trace("", "", self.name() + " initialize")
        self.env = self
        # just to allow main to be created; will be reset later
        self._nameserializeComponent = {}
        self._now = 0
        self._t = 0
        self._offset = 0
        self._main = Component(name="main", env=self, process=None)
        self._main.status._value = current
        self._main.frame = _get_caller_frame()
        self._current_component = self._main
        if self._trace:
            self.print_trace(self.time_to_str(0), "main", "current")
        self._nameserializeQueue = {}
        self._nameserializeComponent = {}
        self._nameserializeResource = {}
        self._nameserializeState = {}
        self._seq = 0
        self._event_list = []
        self._standbylist = []
        self._pendingstandbylist = []

        self.an_objects = set()
        self.an_objects_over3d = set()

        self.an_objects3d = set()
        self.ui_objects = []
        self.sys_objects = set()
        self.serial = 0
        self._speed = 1
        self._animate = False
        self._animate3d = False
        self.view = _AnimateIntro(env=self)
        _AnimateExtro(env=self)
        self._gl_initialized = False
        self._camera_auto_print = False
        self.obj_filenames = {}
        self.running = False
        self._maximum_number_of_bitmaps = 4000
        self._t = 0
        self.video_t = 0
        self.frame_number = 0
        self._exclude_from_animation = "only in video"
        self._audio = None
        self._audio_speed = 1
        self._animate_debug = False
        self._synced = True
        self._step_pressed = False
        self.stopped = False
        self.paused = False
        self.last_s0 = ""
        self._blind_animation = blind_animation
        if self._blind_animation:
            save_trace = self.trace()
            self.trace(False)
            self._blind_video_maker = _BlindVideoMaker(process="", suppress_trace=True)
            self.trace(save_trace)
        if PyDroid:
            if g.tkinter_loaded == "?":
                g.tkinter_loaded = "tkinter" in sys.modules

        if Pythonista:
            self._width, self._height = ui.get_screen_size()
            if retina:
                self.retina = int(scene.get_screen_scale())
            else:
                self.retina = 1
            self._width = int(self._width) * self.retina
            self._height = int(self._height) * self.retina
        else:
            self.retina = 1  # not sure whether this is required
            self._width = 1024
            self._height = 768
        self.root = None
        self._position = (0, 0)
        self._position3d = (0, 0)
        self._width3d = 1024
        self._height3d = 768
        self._video_width = "auto"
        self._video_height = "auto"
        self._video_mode = "2d"
        self._background3d_color = "black"
        self._title = "salabim"
        self._show_menu_buttons = True
        self._x0 = 0
        self._y0 = 0
        self._x1 = self._width
        self._scale = 1
        self._y1 = self._y0 + self._height
        self._background_color = "white"
        self._foreground_color = "black"
        self._fps = 30
        self._modelname = ""
        self.use_toplevel = False
        self._show_fps = False
        self._show_time = True
        self._video = ""
        self._video_out = None
        self._video_repeat = 1
        self._video_pingpong = False
        if Pythonista:
            fonts()  # this speeds up for strange reasons
        self.an_modelname()

        self.an_clocktext()

        self.setup(*args, **kwargs)

    def setup(self):
        """
        called immediately after initialization of an environment.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        """
        pass

    def serialize(self):
        self.serial += 1
        return self.serial

    def __repr__(self):
        return object_to_str(self) + " (" + self.name() + ")"

    def animation_pre_tick(self, t):
        """
        called just before the animation object loop. |n|
        Default behaviour: just return

        Parameters
        ----------
        t : float
            Current (animation) time.
        """
        return

    def animation_post_tick(self, t):
        """
        called just after the animation object loop. |n|
        Default behaviour: just return

        Parameters
        ----------
        t : float
            Current (animation) time.
        """
        return

    def animation_pre_tick_sys(self, t):
        for ao in self.sys_objects.copy():  # copy required as ao's may be removed due to keep
            ao.update(t)

    def animation3d_init(self):
        can_animate3d(try_only=False)
        glut.glutInit()
        glut.glutInitDisplayMode(glut.GLUT_RGBA | glut.GLUT_DOUBLE | glut.GLUT_DEPTH)
        glut.glutInitWindowSize(self._width3d, self._height3d)
        glut.glutInitWindowPosition(*self._position3d)

        self.window3d = glut.glutCreateWindow("salabim3d")

        gl.glClearDepth(1.0)
        gl.glDepthFunc(gl.GL_LESS)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glShadeModel(gl.GL_SMOOTH)

        #        glut.glutReshapeFunc(lambda width, height: glut.glutReshapeWindow(640, 480))
        self._opengl_key_press_bind = {}
        self._opengl_key_press_special_bind = {}

        glut.glutKeyboardFunc(self._opengl_key_pressed)
        glut.glutSpecialFunc(self._opengl_key_pressed_special)

        glut.glutDisplayFunc(lambda: None)
        self._gl_initialized = True

    def _opengl_key_pressed(self, *args):
        key = args[0]
        if key in self._opengl_key_press_bind:
            self._opengl_key_press_bind[key]()

    def _opengl_key_pressed_special(self, *args):
        special_keys = glut.glutGetModifiers()
        alt_active = glut.GLUT_ACTIVE_ALT & special_keys
        shift_active = glut.GLUT_ACTIVE_SHIFT & special_keys
        ctrl_active = glut.GLUT_ACTIVE_CTRL & special_keys
        spec_keys = []
        if alt_active:
            spec_keys.append("Alt")
        if shift_active:
            spec_keys.append("Shift")
        if ctrl_active:
            spec_keys.append("Control")
        spec_key = "-".join(spec_keys)
        key = (args[0], spec_key)

        if key in self._opengl_key_press_special_bind:
            self._opengl_key_press_special_bind[key]()

    def camera_move(self, spec="", lag=1, offset=0, enabled=True):
        """
        Moves the camera according to the given spec, which is normally a collection of camera_print
        outputs.

        Parameters
        ----------
        spec : str
            output normally obtained from camera_auto_print lines

        lag : float
            lag time (for smooth camera movements) (default: 1))

        offset : float
            the duration (can be negative) given is added to the times given in spec. Default: 0

        enabled : bool
            if True (default), move camera according to spec/lag |n|
            if False, freeze camera movement
        """
        if not has_numpy():
            raise ImportError("camera move requires numpy")

        props = "x_eye y_eye z_eye x_center y_center z_center field_of_view_y".split()

        build_values = collections.defaultdict(list)
        build_times = collections.defaultdict(list)
        values = collections.defaultdict(list)
        times = collections.defaultdict(list)

        if enabled:

            for prop in props:
                build_values[prop].append(getattr(self.view, prop)(t=offset))
                build_times[prop].append(offset)

            for prop in props:
                setattr(self.view, prop, lambda arg, t, prop=prop: interp(t, times[prop], values[prop]))  # default argument prop is evaluated at start!

            for line in spec.split("\n"):
                line = line.strip()
                if line.startswith("view("):
                    line = line[5:]
                    line0, line1 = line.split(")  # t=")
                    time = float(line1) + offset
                    parts = line0.replace(" ", "").split(",")
                    for part in parts:
                        prop, value = part.split("=")
                        if prop in props:
                            build_times[prop].append(time)
                            build_values[prop].append(float(value))
                        else:
                            raise ValueError(f"incorrect line in spec: {line}")

            for prop in props:
                pending_value = build_values[prop][0]
                pending_time = build_times[prop][0]
                values[prop].append(pending_value)
                times[prop].append(pending_time)
                build_values[prop].append(build_values[prop][-1])
                build_times[prop].append(build_times[prop][-1] + lag)

                for value, time in zip(build_values[prop], build_times[prop]):
                    if time > pending_time:
                        values[prop].append(pending_value)
                        times[prop].append(pending_time)

                    values[prop].append(interpolate(time, times[prop][-1], pending_time, values[prop][-1], pending_value))
                    times[prop].append(time)
                    pending_value = value
                    pending_time = time + lag

        else:
            for prop in props:
                setattr(self.view, prop, getattr(self.view, prop)(self.t()))

    def camera_rotate(self, event=None, delta_angle=None):
        t = self.t()
        adjusted_x = self.view.x_eye(t) - self.view.x_center(t)
        adjusted_y = self.view.y_eye(t) - self.view.y_center(t)
        cos_rad = math.cos(math.radians(delta_angle))
        sin_rad = math.sin(math.radians(delta_angle))
        self.view.x_eye = self.view.x_center(t) + cos_rad * adjusted_x + sin_rad * adjusted_y
        self.view.y_eye = self.view.y_center(t) - sin_rad * adjusted_x + cos_rad * adjusted_y

        if self._camera_auto_print:
            self.camera_print(props="x_eye y_eye")

    def camera_zoom(self, event=None, factor_xy=None, factor_z=None):
        t = self.t()
        self.view.x_eye = self.view.x_center(t) - (self.view.x_center(t) - self.view.x_eye(t)) * factor_xy
        self.view.y_eye = self.view.y_center(t) - (self.view.y_center(t) - self.view.y_eye(t)) * factor_xy
        self.view.z_eye = self.view.z_center(t) - (self.view.z_center(t) - self.view.z_eye(t)) * factor_z
        if self._camera_auto_print:
            self.camera_print(props="x_eye y_eye z_eye")

    def camera_xy_center(self, event=None, x_dis=None, y_dis=None):
        t = self.t()
        self.view.x_center = self.view.x_center(t) + x_dis
        self.view.y_center = self.view.y_center(t) + y_dis
        if self._camera_auto_print:
            self.camera_print(props="x_center y_center")

    def camera_xy_eye(self, event=None, x_dis=None, y_dis=None):
        t = self.t()
        self.view.x_eye = self.view.x_eye(t) + x_dis
        self.view.y_eye = self.view.y_eye(t) + y_dis
        if self._camera_auto_print:
            self.camera_print(props="x_eye y_eye")

    def camera_field_of_view(self, event=None, factor=None):
        t = self.t()
        self.view.field_of_view_y = self.view.field_of_view_y(t) * factor
        if self._camera_auto_print:
            self.camera_print(props="field_of_view_y")

    def camera_tilt(self, event=None, delta_angle=None):
        t = self.t()
        x_eye = self.view.x_eye(t)
        y_eye = self.view.y_eye(t)
        z_eye = self.view.z_eye(t)
        x_center = self.view.x_center(t)
        y_center = self.view.y_center(t)
        z_center = self.view.z_center(t)

        dx = x_eye - x_center
        dy = y_eye - y_center
        dz = z_eye - z_center
        dxy = math.hypot(dx, dy)
        if dy > 0:
            dxy = -dxy
        alpha = math.degrees(math.atan2(dxy, dz))
        alpha_new = alpha + delta_angle
        dxy_new = math.tan(math.radians(alpha_new)) * dz

        self.view.x_center = x_eye + (dxy_new / dxy) * (x_center - x_eye)
        self.view.y_center = y_eye + (dxy_new / dxy) * (y_center - y_eye)
        if self._camera_auto_print:
            self.camera_print(props="x_center y_center")

    def camera_rotate_axis(self, event=None, delta_angle=None):
        t = self.t()
        adjusted_x = self.view.x_center(t) - self.view.x_eye(t)
        adjusted_y = self.view.y_center(t) - self.view.y_eye(t)
        cos_rad = math.cos(math.radians(delta_angle))
        sin_rad = math.sin(math.radians(delta_angle))
        self.view.x_center = self.view.x_eye(t) + cos_rad * adjusted_x + sin_rad * adjusted_y
        self.view.y_center = self.view.y_eye(t) - sin_rad * adjusted_x + cos_rad * adjusted_y
        if self._camera_auto_print:
            self.camera_print(props="x_eye y_eye")

    def camera_print(self, event=None, props=None):
        t = self.t()
        if props is None:
            props = "x_eye y_eye z_eye x_center y_center z_center field_of_view_y"
        s = "view("
        items = []
        for prop in props.split():
            items.append(f"{getattr(self.view,prop)(t):.4f}")
        print("view(" + (",".join(f"{prop}={getattr(self.view,prop)(t):.4f}" for prop in props.split())) + f")  # t={t:.4f}")

    def _bind(self, tkinter_event, func):
        self.root.bind(tkinter_event, func)
        if len(tkinter_event) == 1:
            opengl_key = bytes(tkinter_event, "utf-8")
            self._opengl_key_press_bind[opengl_key] = func
        else:
            tkinter_event = tkinter_event[1:-1]  # get rid of <>
            if "-" in tkinter_event:
                spec_key, key = tkinter_event.split("-")
            else:
                key = tkinter_event
                spec_key = ""
            if key == "Up":
                opengl_key = (glut.GLUT_KEY_UP, spec_key)
            elif key == "Down":
                opengl_key = (glut.GLUT_KEY_DOWN, spec_key)
            elif key == "Left":
                opengl_key = (glut.GLUT_KEY_LEFT, spec_key)
            elif key == "Right":
                opengl_key = (glut.GLUT_KEY_RIGHT, spec_key)
            self._opengl_key_press_special_bind[opengl_key] = func

    def camera_auto_print(self, value=None):
        """
        queries or set camera_auto_print

        Parameters
        ----------
        value : boolean
            if None (default), no action |n|
            if True, camera_print will be called on each camera control keypress |n|
            if False, no automatic camera_print

        Returns
        -------
        Current status : bool

        Note
        ----
        The camera_auto_print functionality is useful to get the spec for camera_move()
        """
        if value is not None:
            self._camera_auto_print = value
            if value:
                self.camera_print()
        return self._camera_auto_print

    def _camera_control(self):
        self._bind("<Left>", functools.partial(self.camera_rotate, delta_angle=-1))
        self._bind("<Right>", functools.partial(self.camera_rotate, delta_angle=+1))

        self._bind("<Up>", functools.partial(self.camera_zoom, factor_xy=0.9, factor_z=0.9))
        self._bind("<Down>", functools.partial(self.camera_zoom, factor_xy=1 / 0.9, factor_z=1 / 0.9))

        self._bind("z", functools.partial(self.camera_zoom, factor_xy=1, factor_z=0.9))
        self._bind("Z", functools.partial(self.camera_zoom, factor_xy=1, factor_z=1 / 0.9))

        self._bind("<Shift-Up>", functools.partial(self.camera_zoom, factor_xy=0.9, factor_z=1))
        self._bind("<Shift-Down>", functools.partial(self.camera_zoom, factor_xy=1 / 0.9, factor_z=1))

        self._bind("<Alt-Left>", functools.partial(self.camera_xy_eye, x_dis=-10, y_dis=0))
        self._bind("<Alt-Right>", functools.partial(self.camera_xy_eye, x_dis=10, y_dis=0))
        self._bind("<Alt-Down>", functools.partial(self.camera_xy_eye, x_dis=0, y_dis=-10))
        self._bind("<Alt-Up>", functools.partial(self.camera_xy_eye, x_dis=0, y_dis=10))

        self._bind("<Control-Left>", functools.partial(self.camera_xy_center, x_dis=-10, y_dis=0))
        self._bind("<Control-Right>", functools.partial(self.camera_xy_center, x_dis=10, y_dis=0))
        self._bind("<Control-Down>", functools.partial(self.camera_xy_center, x_dis=0, y_dis=-10))
        self._bind("<Control-Up>", functools.partial(self.camera_xy_center, x_dis=0, y_dis=10))

        self._bind("o", functools.partial(self.camera_field_of_view, factor=0.9))
        self._bind("O", functools.partial(self.camera_field_of_view, factor=1 / 0.9))

        self._bind("t", functools.partial(self.camera_tilt, delta_angle=-1))
        self._bind("T", functools.partial(self.camera_tilt, delta_angle=1))

        self._bind("r", functools.partial(self.camera_rotate_axis, delta_angle=1))
        self._bind("R", functools.partial(self.camera_rotate_axis, delta_angle=-1))

        self._bind("p", functools.partial(self.camera_print))

    def show_camera_position(self, over3d=None):
        """
        show camera position on the tkinter window or over3d window

        The 7 camera settings will be shown in the top left corner.

        Parameters
        ----------
        over3d : bool
            if False (default), present on 2D screen |n|
            if True, present on 3D overlay
        """
        if over3d is None:
            over3d = default_over3d()
        top = self.height3d() - 40 if over3d else self.height() - 90
        for i, prop in enumerate("x_eye y_eye z_eye x_center y_center z_center field_of_view_y".split()):
            ao = AnimateRectangle(spec=(0, 0, 75, 35), fillcolor="30%gray", x=5 + i * 80, y=top, screen_coordinates=True, over3d=over3d)
            ao = AnimateText(
                text=lambda arg, t: f"{arg.label}",
                x=5 + i * 80 + 70,
                y=top + 15,
                font="calibri",
                text_anchor="se",
                textcolor="white",
                screen_coordinates=True,
                over3d=over3d,
            )
            ao.label = "fovy" if prop == "field_of_view_y" else prop

            ao = AnimateText(
                text=lambda arg, t: f"{getattr(self.view,arg.prop)(t):11.3f}",
                x=5 + i * 80 + 70,
                y=top,
                font="calibri",
                text_anchor="se",
                textcolor="white",
                screen_coordinates=True,
                over3d=over3d,
            )
            ao.prop = prop

    def print_info(self, as_str=False, file=None):
        """
        prints information about the environment

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append(object_to_str(self) + " " + hex(id(self)))
        result.append("  name=" + self.name())
        result.append("  now=" + self.time_to_str(self._now - self._offset))
        result.append("  current_component=" + self._current_component.name())
        result.append("  trace=" + str(self._trace))
        return return_or_print(result, as_str, file)

    def step(self):
        """
        executes the next step of the future event list

        for advanced use with animation / GUI loops
        """
        try:
            if not self._current_component._skip_standby:
                if len(self.env._pendingstandbylist) > 0:
                    c = self.env._pendingstandbylist.pop(0)
                    if c.status.value == standby:  # skip cancelled components
                        c.status._value = current
                        c._scheduled_time = inf
                        self.env._current_component = c
                        if self._trace:
                            self.print_trace(
                                self.time_to_str(self._now - self.env._offset),
                                c.name(),
                                "current (standby)",
                                s0=c.lineno_txt(),
                                _optional=self._suppress_trace_standby,
                            )
                        try:
                            next(c._process)
                            return
                        except TypeError:
                            c._process(**c._process_kwargs)
                            self._terminate(c)
                            return
                        except StopIteration:
                            self._terminate(c)
                            return

            if len(self.env._standbylist) > 0:
                self._pendingstandbylist = list(self.env._standbylist)
                self._standbylist = []

            if self._event_list:
                (t, priority, seq, c) = heapq.heappop(self._event_list)
            else:
                c = self._main
                if self.end_on_empty_eventlist:
                    t = self.env._now
                    self.print_trace("", "", "run ended", "no events left", s0=c.lineno_txt())
                else:
                    t = inf
            c._on_event_list = False
            self.env._now = t

            self._current_component = c

            c.status._value = current
            c._scheduled_time = inf
            if self._trace:
                if c.overridden_lineno:
                    self.print_trace(self.time_to_str(self._now - self._offset), c.name(), "current", s0=c.overridden_lineno)
                else:
                    self.print_trace(self.time_to_str(self._now - self._offset), c.name(), "current", s0=c.lineno_txt())
            if c == self._main:
                self.running = False
                return
            c._check_fail()
            if c._process_isgenerator:
                try:
                    next(c._process)
                except StopIteration:
                    self._terminate(c)
            else:
                c._process(**c._process_kwargs)
                self._terminate(c)
        except Exception as e:
            if self._animate:
                self.an_quit()
            raise e

    def _terminate(self, c):
        if c._process_isgenerator:
            if self._trace and not self._suppress_trace_linenumbers:
                gi_code = c._process.gi_code
                gs = inspect.getsourcelines(gi_code)
                s0 = c.overridden_lineno or self.filename_lineno_to_str(gi_code.co_filename, len(gs[0]) + gs[1] - 1) + "+"
            else:
                s0 = None
        else:
            if self._trace and not self._suppress_trace_linenumbers:
                gs = inspect.getsourcelines(c._process)
                s0 = c.overridden_lineno or self.filename_lineno_to_str(c._process.__code__.co_filename, len(gs[0]) + gs[1] - 1) + "+"
            else:
                s0 = None
        for r in list(c._claims):
            c._release(r, s0=s0)
        if self._trace:
            self.print_trace("", "", c.name() + " ended", s0=s0)
        c.remove_animation_children()
        c.status._value = data
        c._scheduled_time = inf
        c._process = None

    def _print_event_list(self, s):
        print("eventlist ", s)
        for (t, priority, sequence, comp) in self._event_list:
            print("    ", self.time_to_str(t), comp.name(), "priority", priority)

    def on_closing(self):
        self.an_quit()

    def animation_parameters(
        self,
        animate=None,
        synced=None,
        speed=None,
        width=None,
        height=None,
        title=None,
        show_menu_buttons=None,
        x0=None,
        y0=None,
        x1=None,
        background_color=None,
        foreground_color=None,
        background3d_color=None,
        fps=None,
        modelname=None,
        use_toplevel=None,
        show_fps=None,
        show_time=None,
        maximum_number_of_bitmaps=None,
        video=None,
        video_repeat=None,
        video_pingpong=None,
        audio=None,
        audio_speed=None,
        animate_debug=None,
        animate3d=None,
        width3d=None,
        height3d=None,
        video_width=None,
        video_height=None,
        video_mode=None,
        position=None,
        position3d=None,
        visible=None,
    ):

        """
        set animation parameters

        Parameters
        ----------
        animate : bool
            animate indicator |n|
            new animate indicator |n|
            if '?', animation will be set, possible |n|
            if not specified, no change

        animate3d : bool
            animate3d indicator |n|
            new animate3d indicator |n|
            if '?', 3D-animation will be set, possible |n|
            if not specified, no change

        synced : bool
            specifies whether animation is synced |n|
            if omitted, no change. At init of the environment synced will be set to True

        speed : float
            speed |n|
            specifies how much faster or slower than real time the animation will run.
            e.g. if 2, 2 simulation time units will be displayed per second.

        width : int
            width of the animation in screen coordinates |n|
            if omitted, no change. At init of the environment, the width will be
            set to 1024 for non Pythonista and the current screen width for Pythonista.

        height : int
            height of the animation in screen coordinates |n|
            if omitted, no change. At init of the environment, the height will be
            set to 768 for non Pythonista and the current screen height for Pythonista.

        position : tuple(x,y)
            position of the animation window |n|
            if omitted, no change. At init of the environment, the position will be
            set to (0, 0) |n|
            no effect for Pythonista

        width3d : int
            width of the 3d animation in screen coordinates |n|
            if omitted, no change. At init of the environment, the 3d width will be
            set to 1024.

        height3d : int
            height of the 3d animation in screen coordinates |n|
            if omitted, no change. At init of the environment, the 3d height will be
            set to 768.

        position3d : tuple(x,y)
            position of the 3d animation window |n|
            At init of the environment, the position will be set to (0, 0) |n|
            This has to be set before the 3d animation starts as the window can only be postioned at initialization

        title : str
            title of the canvas window |n|
            if omitted, no change. At init of the environment, the title will be
            set to salabim. |n|
            if "", the title will be suppressed.

        x0 : float
            user x-coordinate of the lower left corner |n|
            if omitted, no change. At init of the environment, x0 will be set to 0.

        y0 : float
            user y_coordinate of the lower left corner |n|
            if omitted, no change. At init of the environment, y0 will be set to 0.

        x1 : float
            user x-coordinate of the lower right corner |n|
            if omitted, no change. At init of the environment, x1 will be set to 1024
            for non Pythonista and the current screen width for Pythonista.

        background_color : colorspec
            color of the background |n|
            if omitted, no change. At init of the environment, this will be set to white.

        foreground_color : colorspec
            color of foreground (texts) |n|
            if omitted and background_color is specified, either white of black will be used,
            in order to get a good contrast with the background color. |n|
            if omitted and background_color is also omitted, no change. At init of the
            environment, this will be set to black.

        background3d_color : colorspec
            color of the 3d background |n|
            if omitted, no change. At init of the environment, this will be set to black.

        fps : float
            number of frames per second

        modelname : str
            name of model to be shown in upper left corner,
            along with text "a salabim model" |n|
            if omitted, no change. At init of the environment, this will be set
            to the null string, which implies suppression of this feature.

        use_toplevel : bool
            if salabim animation is used in parallel with
            other modules using tkinter, it might be necessary to
            initialize the root with tkinter.TopLevel().
            In that case, set this parameter to True. |n|
            if False (default), the root will be initialized with tkinter.Tk()

        show_fps : bool
            if True, show the number of frames per second |n|
            if False, do not show the number of frames per second (default)

        show_time : bool
            if True, show the time (default)  |n|
            if False, do not show the time

        show_menu_buttons : bool
            if True, show the menu buttons (default)  |n|
            if False, do not show the menu buttons

        maximum_number_of_bitmaps : int
            maximum number of tkinter bitmaps (default 4000)

        video : str
            if video is not omitted, a video with the name video
            will be created. |n|
            Normally, use .mp4 as extension. |n|
            If the extension is .gif or .png an animated gif / png file will be written, unless there
            is a * in the filename |n|
            If the extension is .gif, .jpg, .png, .bmp, .ico or .tiff and one * appears in the filename,
            individual frames will be written with
            a six digit sequence at the place of the asteriks in the file name.
            If the video extension is not .gif, .jpg, .png, .bmp, .ico or .tiff, a codec may be added
            by appending a plus sign and the four letter code name,
            like "myvideo.avi+DIVX". |n|
            If no codec is given, MJPG will be used for .avi files, otherwise .mp4v |n|
            Under PyDroid only .avi files are supported.

        video_repeat : int
            number of times animated gif or png should be repeated |n|
            0 means inifinite |n|
            at init of the environment video_repeat is 1 |n|
            this only applies to gif and png files production.

        video_pingpong : bool
            if True, all frames will be added reversed at the end of the video (useful for smooth loops)
            at init of the environment video_pingpong is False |n|
            this only applies to gif and png files production.

        audio : str
            name of file to be played (mp3 or wav files) |n|
            if the none string, the audio will be stopped |n|
            default: no change |n|
            for more information, see Environment.audio()

        visible : bool
            if True (start condition), the animation window will be visible |n|
            if False, the animation window will be hidden ('withdrawn')

        Note
        ----
        The y-coordinate of the upper right corner is determined automatically
        in such a way that the x and y scaling are the same.

        """
        frame_changed = False
        width_changed = False
        height_changed = False
        fps_changed = False

        if speed is not None:
            self._speed = speed
            self.set_start_animation()

        if show_fps is not None:
            self._show_fps = show_fps

        if show_time is not None:
            self._show_time = show_time

        if maximum_number_of_bitmaps is not None:
            self._maximum_number_of_bitmaps = maximum_number_of_bitmaps

        if synced is not None:
            self._synced = synced
            self.set_start_animation()

        if width is not None:
            if self._width != width:
                self._width = width
                frame_changed = True
                width_changed = True

        if height is not None:
            if self._height != height:
                self._height = height
                frame_changed = True
                height_changed = True

        if width3d is not None:
            if self._width != width:
                self._width3d = width3d
                if self._gl_initialized:
                    glut.glutReshapeWindow(self._width3d, self._height3d)

        if height3d is not None:
            if self._height != height:
                self._height3d = height3d
                if self._gl_initialized:
                    glut.glutReshapeWindow(self._width3d, self._height3d)

        if position is not None:
            if self._position != position:
                self._position = position
                if self.root is not None:
                    self.root.geometry(f"+{self._position[0]}+{self._position[1]}")

        if position3d is not None:
            self._position3d = position3d

        if video_width is not None:
            if self._video:
                raise ValueError("video_width may not be changed while recording video")
            self._video_width = video_width

        if video_height is not None:
            if self._video:
                raise ValueError("video_height may not be changed while recording video")
            self._video_height = video_height

        if video_mode is not None:
            if video_mode not in ("2d", "screen", "3d"):
                raise ValueError("video_mode " + video_mode + " not recognized")
            self._video_mode = video_mode

        if title is not None:
            if self._title != title:
                self._title = title
                frame_changed = True

        if show_menu_buttons is not None:
            if self._show_menu_buttons != show_menu_buttons:
                self._show_menu_buttons = show_menu_buttons
                frame_changed = True

        if fps is not None:
            if self._video:
                raise ValueError("video_repeat may not be changed while recording video")
            self._fps = fps

        if x0 is not None:
            if self._x0 != x0:
                self._x0 = x0
                self.uninstall_uios()

        if x1 is not None:
            if self._x1 != x1:
                self._x1 = x1
                self.uninstall_uios()

        if y0 is not None:
            if self._y0 != y0:
                self._y0 = y0
                self.uninstall_uios()

        if background_color is not None:
            if background_color in ("fg", "bg"):
                raise ValueError(background_color + "not allowed for background_color")
            if self._background_color != background_color:
                self._background_color = background_color
                frame_changed = True
            if foreground_color is None:
                self._foreground_color = "white" if self.is_dark("bg") else "black"

        if foreground_color is not None:
            if foreground_color in ("fg", "bg"):
                raise ValueError(foreground_color + "not allowed for foreground_color")
            self._foreground_color = foreground_color

        if background3d_color is not None:
            self._background3d_color = background3d_color

        if modelname is not None:
            self._modelname = modelname

        if use_toplevel is not None:
            self.use_toplevel = use_toplevel

        if animate_debug is not None:
            self._animate_debug = animate_debug

        if audio_speed is not None:
            if self._audio_speed != audio_speed:
                self._audio_speed = audio_speed
                if audio_speed != self._speed:
                    if self._audio is not None:
                        if Pythonista:
                            self._audio.player.pause()
                        if Windows:
                            self._audio.stop()
                self.set_start_animation()

        if audio is not None:
            if (self._audio is None and audio != "") or (self.audio is not None and self._audio.filename != audio):
                if self._audio is not None:
                    if Pythonista:
                        self._audio.player.pause()
                    if Windows:
                        self._audio.stop()
                    if self._video_out is not None:
                        self.audio_segments[-1].t1 = self.frame_number / self._fps
                if audio == "":
                    self._audio = None
                else:
                    if ">" not in audio:
                        audio = audio + ">0"
                    audio_filename, startstr = audio.split(">")
                    if not os.path.isfile(audio_filename):
                        raise FileNotFoundError(audio_filename)
                    if Pythonista:
                        import sound

                        class Play:
                            def __init__(self, s, repeat=-1):
                                self.player = sound.Player(s)
                                self.player.number_of_loops = repeat

                        self._audio = Play(audio_filename, repeat=0)
                        self._audio.duration = self._audio.player.duration
                        self._audio.player.play()
                        self._audio.player.current_time = 0

                    else:
                        self._audio = AudioClip(audio_filename)

                    self._audio.start = float(startstr)

                    self._audio.t0 = self._t

                    self._audio.filename = audio_filename

                    if self._video_out is not None:  # if video ist started here as well, the audio_segment is created later
                        self._audio.t0 = self.frame_number / self._fps
                        self.audio_segments.append(self._audio)
                    self.set_start_animation()

        if animate3d is not None:
            if animate3d == "?":
                animate3d = can_animate3d(try_only=True)
            self._animate3d = animate3d
            if not animate3d:
                glut.glutDestroyWindow(self.window3d)
                glut.glutMainLoopEvent()
                self._gl_initialized = False

        if animate is not None:
            if animate == "?":
                animate = can_animate(try_only=True)
            if animate != self._animate:
                frame_changed = True
                self._animate = animate

        self._scale = self._width / (self._x1 - self._x0)
        self._y1 = self._y0 + self._height / self._scale

        if g.animation_env is not self:
            if g.animation_env is not None:
                g.animation_env.video_close()
            if self._animate:
                frame_changed = True
            else:
                frame_changed = False  # no animation required, so leave running animation_env untouched

        if video_repeat is not None:
            if self._video:
                raise ValueError("video_repeat may not be changed while recording video")
            self._video_repeat = video_repeat

        if video_pingpong is not None:
            if self._video:
                raise ValueError("video_pingpong may not be changed while recording video")
            self._video_pingpong = video_pingpong

        if video is not None:
            if video != self._video:
                if self._video:
                    self.video_close()
                self._video = video

                if video:
                    if self._video_mode == "screen" and ImageGrab is None:
                        raise ValueError("video_mode='screen' not supported on this platform (ImageGrab does not exist)")
                    if self._video_width == "auto":
                        if self._video_mode == "3d":
                            self._video_width_real = self._width3d
                        elif self._video_mode == "2d":
                            self._video_width_real = self._width
                        else:
                            img = ImageGrab.grab()
                            self._video_width_real = img.size[0]
                    else:
                        self._video_width_real = self._video_width

                    if self._video_height == "auto":
                        if self._video_mode == "3d":
                            self._video_height_real = self._height3d
                        elif self._video_mode == "2d":
                            self._video_height_real = self._height
                        else:
                            img = ImageGrab.grab()
                            self._video_height_real = img.size[1]
                    else:
                        self._video_height_real = self._video_height
                    can_animate(try_only=False)

                    video_path = Path(video)
                    extension = video_path.suffix.lower()
                    self._video_name = video
                    video_path.parent.mkdir(parents=True, exist_ok=True)
                    if extension == ".gif" and not ("*" in video_path.stem):
                        self._video_out = "gif"
                        self._images = []

                    elif extension == ".png" and not ("*" in video_path.stem):
                        self._video_out = "png"
                        self._images = []
                    elif extension.lower() in (".jpg", ".png", ".bmp", ".ico", ".tiff", ".gif"):
                        if "*" in video_path.stem:
                            if video.count("*") > 1:
                                raise ValueError("more than one * found in " + video)
                            if "?" in video:
                                raise ValueError("? found in " + video)
                            self.video_name_format = video.replace("*", "{:06d}")
                            for file in video_path.parent.glob(video_path.name.replace("*", "??????")):
                                file.unlink()
                        else:
                            raise ValueError("incorrect video name (should contain a *) " + video)

                        self._video_out = "snapshots"

                    else:
                        if "+" in extension:
                            extension, codec = extension.split("+")
                            self._video_name = self._video_name[:-5]  # get rid of codec
                        else:
                            codec = "MJPG" if extension.lower() == ".avi" else "mp4v"
                        if PyDroid and extension.lower() != ".avi":
                            raise ValueError("PyDroid can only produce .avi videos, not " + extension)
                        can_video(try_only=False)
                        fourcc = cv2.VideoWriter_fourcc(*codec)
                        if video_path.is_file():
                            video_path.unlink()
                        self._video_name_temp = tempfile.NamedTemporaryFile(suffix=extension, delete=False).name
                        self._video_out = cv2.VideoWriter(self._video_name_temp, fourcc, self._fps, (self._video_width_real, self._video_height_real))
                        self.frame_number = 0
                        self.audio_segments = []
                        if self._audio is not None:
                            self._audio.start += self._t - self._audio.t0
                            self._audio.t0 = self.frame_number / self._fps
                            self.audio_segments.append(self._audio)
                            if Pythonista:
                                self._audio.player.pause()
                            if Windows:
                                self._audio.stop()

        if self._video:
            self.video_t = self._now

        if frame_changed:
            if g.animation_env is not None:
                g.animation_env._animate = self._animate
                if not Pythonista:
                    if g.animation_env.root is not None:  # for blind animation to work properly
                        g.animation_env.root.destroy()
                        g.animation_env.root = None
                g.animation_env = None

            if self._blind_animation:
                if self._animate:
                    if self._video != "":
                        save_trace = self.trace()
                        self.trace(False)
                        self._blind_video_maker.activate(process="process")
                        self.trace(save_trace)
                else:
                    self._blind_video_maker.cancel()
            else:
                if self._animate:
                    can_animate(try_only=False)  # install modules

                    g.animation_env = self
                    self._t = self._now  # for the call to set_start_animation
                    self.paused = False
                    self.set_start_animation()

                    if Pythonista:
                        if g.animation_scene is None:
                            g.animation_scene = AnimationScene(env=self)
                            scene.run(g.animation_scene, frame_interval=1, show_fps=False)

                    else:
                        if self.use_toplevel:
                            self.root = tkinter.Toplevel()
                        else:
                            self.root = tkinter.Tk()

                        if self._title:
                            self.root.title(self._title)
                        else:
                            self.root.overrideredirect(1)
                        self.root.geometry(f"+{self._position[0]}+{self._position[1]}")
                        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

                        self.root.bind("-", lambda self: g.animation_env.an_half())
                        self.root.bind("+", lambda self: g.animation_env.an_double())
                        self.root.bind("<space>", lambda self: g.animation_env.an_menu_go())
                        self.root.bind("s", lambda self: g.animation_env.an_single_step())
                        self.root.bind("<Control-c>", lambda self: g.animation_env.an_quit())

                        g.canvas = tkinter.Canvas(self.root, width=self._width, height=self._height)
                        g.canvas.configure(background=self.colorspec_to_hex("bg", False))
                        g.canvas.pack()
                        g.canvas_objects = []
                        g.canvas_object_overflow_image = None

                    self.uninstall_uios()  # this causes all ui objects to be (re)installed

                    if self._show_menu_buttons:
                        self.an_menu_buttons()
        if visible is not None:
            if Pythonista:
                raise ValueError("Pythonista does not support visible=False")
            if visible and self.root.wm_state() == "withdrawn":
                self.root.deiconify()
            if not visible and self.root.wm_state() != "withdrawn":
                self.root.withdraw()

    def video_close(self):
        """
        closes the current animation video recording, if any.
        """
        if self._video_out:
            if self._video_out == "gif":
                if self._images:
                    if self._video_pingpong:
                        self._images.extend(self._images[::-1])
                    if Pythonista:
                        import images2gif

                        images2gif.writeGif(self._video_name, self._images, duration=1 / self._fps, repeat=self._video_repeat)
                    else:
                        if self._video_repeat == 1:  # in case of repeat == 1, loop should not be specified (otherwise, it might show twice)
                            self._images[0].save(self._video_name, save_all=True, append_images=self._images[1:], duration=1000 / self._fps, optimize=False)
                        else:
                            self._images[0].save(
                                self._video_name,
                                save_all=True,
                                append_images=self._images[1:],
                                loop=self._video_repeat,
                                duration=1000 / self._fps,
                                optimize=False,
                            )

                    del self._images
            elif self._video_out == "png":

                if self._video_pingpong:
                    self._images.extend(self._images[::-1])
                this_apng = _APNG(num_plays=self._video_repeat)
                for image in self._images:
                    with io.BytesIO() as png_file:
                        image.save(png_file, "PNG", optimize=True)
                        this_apng.append(_APNG.PNG.from_bytes(png_file.getvalue()), delay=1, delay_den=int(self.fps()))
                this_apng.save(self._video_name)
                del self._images

            elif self._video_out == "snapshots":
                pass
            else:
                self._video_out.release()
                if self.audio_segments:
                    if self._audio:
                        self.audio_segments[-1].t1 = self.frame_number / self._fps
                    self.add_audio()
                shutil.move(self._video_name_temp, self._video_name)

            self._video_out = None
            self._video = ""

    def _capture_image(self, mode="RGBA", video_mode="2d", include_topleft=True):
        if video_mode == "3d":
            if not self._animate3d:
                raise ValueError("video_mode=='3d', but animate3d is not True")

            width = self._width3d
            height = self._height3d

            # https://stackoverflow.com/questions/41126090/how-to-write-pyopengl-in-to-jpg-image
            gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
            data = gl.glReadPixels(0, 0, width, height, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
            image = Image.frombytes("RGB", (width, height), data)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        elif video_mode == "screen":
            image = ImageGrab.grab()
        else:
            an_objects = sorted(self.an_objects, key=lambda obj: (-obj.layer(self._t), obj.sequence))
            image = Image.new("RGBA", (self._width, self._height), self.colorspec_to_tuple("bg"))
            for ao in an_objects:
                ao.make_pil_image(self.t())
                if ao._image_visible and (include_topleft or not ao.getattr("in_topleft", False)):
                    image.paste(ao._image, (int(ao._image_x), int(self._height - ao._image_y - ao._image.size[1])), ao._image)
        return image.convert(mode)

    def insert_frame(self, image, number_of_frames=1):
        """
        Insert image as frame(s) into video

        Parameters
        ----------
        image : Pillow image, str or Path object
            Image to be inserted

        nuumber_of_frames: int
            Number of 1/30 second long frames to be inserted
        """
        if self._video_out is None:
            raise ValueError("video not set")
        if isinstance(image, (Path, str)):
            image = Image.open(image)

        image = resize_with_pad(image, self._video_width_real, self._video_height_real)
        for _ in range(number_of_frames):
            if self._video_out == "gif":
                self._images.append(image.convert("RGB"))
            elif self._video_out == "png":
                self._images.append(image.convert("RGBA"))
            elif self._video_out == "snapshots":
                serialized_video_name = self.video_name_format.format(self.frame_number)
                if self._video_name.lower().endswith(".jpg"):
                    image.convert("RGB").save(serialized_video_name)
                else:
                    image.convert("RGBA").save(serialized_video_name)
                self.frame_number += 1
            else:
                image = image.convert("RGB")
                open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
                self._video_out.write(open_cv_image)

    def _save_frame(self):
        self._exclude_from_animation = "not in video"
        image = self._capture_image("RGBA", self._video_mode)
        self._exclude_from_animation = "only in video"
        self.insert_frame(image)

    def add_audio(self):
        if not Windows:
            return

        with tempfile.TemporaryDirectory() as tempdir:
            last_t = 0
            seq = 0
            for audio_segment in self.audio_segments:
                if hasattr(self, "debug_ffmpeg"):
                    print(
                        " audio_segment.filename = "
                        + str(audio_segment.filename)
                        + " .t0 = "
                        + str(audio_segment.t0)
                        + " .t1 = "
                        + str(audio_segment.t1)
                        + " .start = "
                        + str(audio_segment.start)
                    )
                end = min(audio_segment.duration, audio_segment.t1 - audio_segment.t0 + audio_segment.start)
                if end > audio_segment.start:
                    if audio_segment.t0 - last_t > 0:
                        command = (
                            "-f",
                            "lavfi",
                            "-i",
                            "aevalsrc=0:0::duration=" + str(audio_segment.t0 - last_t),
                            "-ab",
                            "128k",
                            tempdir + "\\temp" + str(seq) + ".mp3",
                        )
                        self.ffmpeg_execute(command)
                        seq += 1
                    command = (
                        "-ss",
                        str(audio_segment.start),
                        "-i",
                        audio_segment.filename,
                        "-t",
                        str(end - audio_segment.start),
                        "-c",
                        "copy",
                        tempdir + "\\temp" + str(seq) + ".mp3",
                    )
                    self.ffmpeg_execute(command)
                    seq += 1
                    last_t = audio_segment.t1

            if seq > 0:
                temp_filename = tempdir + "\\temp" + os.path.splitext(self._video_name)[1]
                shutil.copyfile(self._video_name_temp, temp_filename)

                with open(tempdir + "\\temp.txt", "w") as f:
                    f.write("\n".join("file '" + tempdir + "\\temp" + str(i) + ".mp3'" for i in range(seq)))
                if hasattr(self, "debug_ffmpeg"):
                    print("contents of temp.txt file")
                    with open(tempdir + "\\temp.txt", "r") as f:
                        print(f.read())

                command = ("-i", temp_filename, "-f", "concat", "-i", tempdir + "\\temp.txt", "-map", "0:v", "-map", "1:a", "-c", "copy", self._video_name_temp)
                self.ffmpeg_execute(command)

    def ffmpeg_execute(self, command):
        command = ("ffmpeg", "-y") + command + ("-loglevel", "quiet")
        if hasattr(self, "debug_ffmpeg"):
            print("command=" + str(command))
        try:
            subprocess.call(command, shell=False)
        except FileNotFoundError:
            raise FileNotFoundError("ffmpeg could not be loaded (refer to install procedure).")

    def uninstall_uios(self):
        for uio in self.ui_objects:
            uio.installed = False

    def x0(self, value=None):
        """
        x coordinate of lower left corner of animation

        Parameters
        ----------
        value : float
            new x coordinate

        Returns
        -------
        x coordinate of lower left corner of animation : float
        """
        if value is not None:
            self.animation_parameters(x0=value, animate=None)
        return self._x0

    def x1(self, value=None):
        """
        x coordinate of upper right corner of animation : float

        Parameters
        ----------
        value : float
            new x coordinate |n|
            if not specified, no change

        Returns
        -------
        x coordinate of upper right corner of animation : float
        """
        if value is not None:
            self.animation_parameters(x1=value, animate=None)
        return self._x1

    def y0(self, value=None):
        """
        y coordinate of lower left corner of animation

        Parameters
        ----------
        value : float
            new y coordinate |n|
            if not specified, no change

        Returns
        -------
        y coordinate of lower left corner of animation : float
        """
        if value is not None:
            self.animation_parameters(y0=value, animate=None)
        return self._y0

    def y1(self):
        """
        y coordinate of upper right corner of animation

        Returns
        -------
        y coordinate of upper right corner of animation : float

        Note
        ----
        It is not possible to set this value explicitely.
        """
        return self._y1

    def scale(self):
        """
        scale of the animation, i.e. width / (x1 - x0)

        Returns
        -------
        scale : float

        Note
        ----
        It is not possible to set this value explicitely.
        """
        return self._scale

    def user_to_screen_coordinates_x(self, userx):
        """
        converts a user x coordinate to a screen x coordinate

        Parameters
        ----------
        userx : float
            user x coordinate to be converted

        Returns
        -------
        screen x coordinate : float
        """
        return (userx - self._x0) * self._scale

    def user_to_screen_coordinates_y(self, usery):
        """
        converts a user x coordinate to a screen x coordinate

        Parameters
        ----------
        usery : float
            user y coordinate to be converted

        Returns
        -------
        screen y coordinate : float
        """
        return (usery - self._y0) * self._scale

    def user_to_screen_coordinates_size(self, usersize):
        """
        converts a user size to a value to be used with screen coordinates

        Parameters
        ----------
        usersize : float
            user size to be converted

        Returns
        -------
        value corresponding with usersize in screen coordinates : float
        """
        return usersize * self._scale

    def screen_to_user_coordinates_x(self, screenx):
        """
        converts a screen x coordinate to a user x coordinate

        Parameters
        ----------
        screenx : float
            screen x coordinate to be converted

        Returns
        -------
        user x coordinate : float
        """
        return self._x0 + screenx / self._scale

    def screen_to_user_coordinates_y(self, screeny):
        """
        converts a screen x coordinate to a user x coordinate

        Parameters
        ----------
        screeny : float
            screen y coordinate to be converted

        Returns
        -------
        user y coordinate : float
        """
        return self._y0 + screeny / self._scale

    def screen_to_user_coordinates_size(self, screensize):
        """
        converts a screen size to a value to be used with user coordinates

        Parameters
        ----------
        screensize : float
            screen size to be converted

        Returns
        -------
        value corresponding with screensize in user coordinates : float
        """
        return screensize / self._scale

    def width(self, value=None):
        """
        width of the animation in screen coordinates

        Parameters
        ----------
        value : int
            new width |n|
            if not specified, no change


        Returns
        -------
        width of animation : int
        """
        if value is not None:
            self.animation_parameters(width=value, animate=None)
        return self._width

    def height(self, value=None):
        """
        height of the animation in screen coordinates

        Parameters
        ----------
        value : int
            new height |n|
            if not specified, no change

        Returns
        -------
        height of animation : int
        """
        if value is not None:
            self.animation_parameters(height=value, animate=None)
        return self._height

    def width3d(self, value=None):
        """
        width of the 3d animation in screen coordinates

        Parameters
        ----------
        value : int
            new 3d width |n|
            if not specified, no change


        Returns
        -------
        width of 3d animation : int
        """
        if value is not None:
            self.animation_parameters(width3d=value, animate=None)
        return self._width3d

    def height3d(self, value=None):
        """
        height of the 3d animation in screen coordinates

        Parameters
        ----------
        value : int
            new 3d height |n|
            if not specified, no change

        Returns
        -------
        height of 3d animation : int
        """
        if value is not None:
            self.animation_parameters(height3d=value, animate=None)
        return self._height3d

    def width(self, value=None):
        """
        width of the animation in screen coordinates

        Parameters
        ----------
        value : int
            new width |n|
            if not specified, no change


        Returns
        -------
        width of animation : int
        """
        if value is not None:
            self.animation_parameters(width=value, animate=None)
        return self._width

    def visible(self, value=None):
        """
        controls visibility of the animation window

        Parameters
        ----------
        value : bool
            if True, the animation window will be visible |n|
            if False, the animation window will be hidden ('withdrawn')
            if None (default), no change

        Returns
        -------
        current visibility : bool
        """
        self.animation_parameters(visible=value)
        if Pythonista:
            return True
        else:
            return self.root.wm_state() != "withdrawn"

    def video_width(self, value=None):
        """
        width of the video animation in screen coordinates

        Parameters
        ----------
        value : int
            new width |n|
            if not specified, no change


        Returns
        -------
        width of video animation : int
        """
        if value is not None:
            self.animation_parameters(video_width=value, animate=None)
        return self._video_width

    def video_height(self, value=None):
        """
        height of the video animation in screen coordinates

        Parameters
        ----------
        value : int
            new width |n|
            if not specified, no change


        Returns
        -------
        height of video animation : int
        """
        if value is not None:
            self.animation_parameters(video_height=value, animate=None)
        return self._video_height

    def video_mode(self, value=None):
        """
        video_mode

        Parameters
        ----------
        value : int
            new video mode ("2d", "3d" or "screen") |n|
            if not specified, no change

        Returns
        -------
        video_mode : int
        """
        if value is not None:
            self.animation_parameters(video_mode=value, animate=None)
        return self._video_mode

    def position(self, value=None):
        """
        position of the animation window

        Parameters
        ----------
        value : tuple (x, y)
            new position |n|
            if not specified, no change

        Returns
        -------
        position of animation window: tuple (x,y)
        """
        if value is not None:
            self.animation_parameters(position=value, animate=None)
        return self._position

    def position3d(self, value=None):
        """
        position of the 3d animation window

        Parameters
        ----------
        value : tuple (x, y)
            new position |n|
            if not specified, no change

        Returns
        -------
        position of th 3d animation window: tuple (x,y)

        Note
        ----
        This must be given before the 3d animation is started.
        """
        if value is not None:
            self.animation_parameters(position3d=value, animate=None)
        return self._position3d

    def title(self, value=None):
        """
        title of the canvas window

        Parameters
        ----------
        value : str
            new title |n|
            if "", the title will be suppressed |n|
            if not specified, no change

        Returns
        -------
        title of canvas window : str

        Note
        ----
        No effect for Pythonista
        """
        if value is not None:
            self.animation_parameters(title=value, animate=None)
        return self._title

    def background_color(self, value=None):
        """
        background_color of the animation

        Parameters
        ----------
        value : colorspec
            new background_color |n|
            if not specified, no change

        Returns
        -------
        background_color of animation : colorspec
        """
        if value is not None:
            self.animation_parameters(background_color=value, animate=None)
        return self._background_color

    def background3d_color(self, value=None):
        """
        background3d_color of the animation

        Parameters
        ----------
        value : colorspec
            new background_color |n|
            if not specified, no change

        Returns
        -------
        background3d_color of animation : colorspec
        """
        if value is not None:
            self.animation_parameters(background3d_color=value)
        return self._background3d_color

    def foreground_color(self, value=None):
        """
        foreground_color of the animation

        Parameters
        ----------
        value : colorspec
            new foreground_color |n|
            if not specified, no change

        Returns
        -------
        foreground_color of animation : colorspec
        """
        if value is not None:
            self.animation_parameters(foreground_color=value, animate=None)
        return self._foreground_color

    def animate(self, value=None):
        """
        animate indicator

        Parameters
        ----------
        value : bool
            new animate indicator |n|
            if '?', animation will be set, if possible
            if not specified, no change

        Returns
        -------
        animate status : bool

        Note
        ----
        When the run is not issued, no action will be taken.
        """
        if value is not None:
            self.animation_parameters(animate=value)
        return self._animate

    def animate3d(self, value=None):
        """
        animate3d indicator

        Parameters
        ----------
        value : bool
            new animate3d indicator |n|
            if '?', 3D-animation will be set, if possible
            if not specified, no change

        Returns
        -------
        animate3d status : bool

        Note
        ----
        When the animate is not issued, no action will be taken.
        """

        if value is not None:
            self.animation_parameters(animate3d=value, animate=None)
        return self._animate3d

    def modelname(self, value=None):
        """
        modelname

        Parameters
        ----------
        value : str
            new modelname |n|
            if not specified, no change

        Returns
        -------
        modelname : str

        Note
        ----
        If modelname is the null string, nothing will be displayed.
        """
        if value is not None:
            self.animation_parameters(modelname=value, animate=None)
        return self._modelname

    def audio(self, filename):
        """
        Play audio during animation

        Parameters
        ----------
        filename : str
            name of file to be played (mp3 or wav files) |n|
            if "", the audio will be stopped |n|
            optionaly, a start time in seconds  may be given by appending the filename a > followed
            by the start time, like 'mytune.mp3>12.5'
            if not specified (None), no change

        Returns
        -------
        filename being played ("" if nothing is being played): str

        Note
        ----
        Only supported on Windows and Pythonista platforms. On other platforms, no effect. |n|
        Variable bit rate mp3 files may be played incorrectly on Windows platforms.
        Try and use fixed bit rates (e.g. 128 or 320 kbps)
        """
        self.animation_parameters(audio=filename, animate=None)
        if self._audio:
            return self._audio.filename
        return ""

    def audio_speed(self, value=None):
        """
        Play audio during animation

        Parameters
        ----------
        value : float
            animation speed at which the audio should be played |n|
            default: no change |n|
            initially: 1

        Returns
        -------
        speed being played: int
        """
        self.animation_parameters(audio_speed=value, animate=None)
        return self._audio_speed

    def animate_debug(self, value=None):
        """
        Animate debug

        Parameters
        ----------
        value : bool
            animate_debug |n|
            default: no change |n|
            initially: False

        Returns
        -------
        animate_debug : bool
        """
        self.animation_parameters(animate_debug=value, animate=None)
        return self._animate_debug

    class _Video:
        def __init__(self, env):
            self.env = env

        def __enter__(self):
            return self

        def __exit__(self, type, value, traceback):
            self.env.video_close()

    def is_videoing(self):
        """
        video recording status

        returns
        -------
        video recording status : bool |n|
            True, if video is being recorded |n|
            False, otherwise
        """
        return bool(self._video)

    def video(self, value):
        """
        video name

        Parameters
        ----------
        value : str, list or tuple
            new video name |n|
            for explanation see animation_parameters()

        Note
        ----
        If video is the null string ro None, the video (if any) will be closed. |n|
        The call can be also used as a context manager, which automatically opens and
        closes a file. E.g. ::

            with video("test.mp4"):
                env.run(100)
        """
        if value is None:
            value = ""
        self.animation_parameters(video=value, animate=None)
        return self._Video(env=self)

    def video_repeat(self, value=None):
        """
        video repeat

        Parameters
        ----------
        value : int
            new video repeat |n|
            if not specified, no change

        Returns
        -------
        video repeat : int

        Note
        ----
        Applies only to gif animation.
        """
        if value is not None:
            self.animation_parameters(video_repeat=value, animate=None)
        return self._video_repeat

    def video_pingpong(self, value=None):
        """
        video pingpong

        Parameters
        ----------
        value : bool
            new video pingpong |n|
            if not specified, no change

        Returns
        -------
        video pingpong : bool

        Note
        ----
        Applies only to gif animation.
        """
        if value is not None:
            self.animation_parameters(video_pingpong=value, animate=None)
        return self._video_pingpong

    def fps(self, value=None):
        """
        fps

        Parameters
        ----------
        value : int
            new fps |n|
            if not specified, no change

        Returns
        -------
        fps : bool
        """
        if value is not None:
            self.animation_parameters(fps=value, animate=None)
        return self._fps

    def show_time(self, value=None):
        """
        show_time

        Parameters
        ----------
        value : bool
            new show_time |n|
            if not specified, no change

        Returns
        -------
        show_time : bool
        """
        if value is not None:
            self.animation_parameters(show_time=value, animate=None)
        return self._show_time

    def show_fps(self, value=None):
        """
        show_fps

        Parameters
        ----------
        value : bool
            new show_fps |n|
            if not specified, no change

        Returns
        -------
        show_fps : bool
        """
        if value is not None:
            self.animation_parameters(show_fps=value, animate=None)
        return self._show_fps

    def show_menu_buttons(self, value=None):
        """
        controls menu buttons

        Parameters
        ----------
        value : bool
            if True, menu buttons are shown |n|
            if False, menu buttons are hidden |n|
            if not specified, no change

        Returns
        -------
        show menu button status : bool
        """
        if value is not None:
            self.animation_parameters(show_menu_buttons=value, animate=None)
        return self._show_menu_buttons

    def maximum_number_of_bitmaps(self, value=None):
        """
        maximum number of bitmaps (applies to animation with tkinter only)

        Parameters
        ----------
        value : int
            new maximum_number_of_bitmaps |n|
            if not specified, no change

        Returns
        -------
        maximum number of bitmaps : int
        """
        if value is not None:
            self.animation_parameters(maximum_number_of_bitmaps=value, animate=None)
        return self._maximum_number_of_bitmaps

    def synced(self, value=None):
        """
        synced

        Parameters
        ----------
        value : bool
            new synced |n|
            if not specified, no change

        Returns
        -------
        synced : bool
        """
        if value is not None:
            self.animation_parameters(synced=value, animate=None)
        return self._synced

    def speed(self, value=None):
        """
        speed

        Parameters
        ----------
        value : float
            new speed |n|
            if not specified, no change

        Returns
        -------
        speed : float
        """
        if value is not None:
            self.animation_parameters(speed=value, animate=None)
        return self._speed

    def peek(self):
        """
        returns the time of the next component to become current |n|
        if there are no more events, peek will return inf |n|
        Only for advance use with animation / GUI event loops
        """
        if len(self.env._pendingstandbylist) > 0:
            return self.env._now
        else:
            if self._event_list:
                return self._event_list[0][0]
            else:
                if self.end_on_empty_eventlist:
                    return self._now
                else:
                    return inf

    def main(self):
        """
        Returns
        -------
        the main component : Component
        """
        return self._main

    def now(self):
        """
        Returns
        -------
        the current simulation time : float
        """
        return self._now - self._offset

    def t(self):
        """
        Returns
        -------
        the current simulation animation time : float
        """
        return (self._t if self._animate else self._now) - self._offset

    def reset_now(self, new_now=0):
        """
        reset the current time

        Parameters
        ----------
        new_now : float or distribution
            now will be set to new_now |n|
            default: 0 |n|
            if distribution, the distribution is sampled

        Note
        ----
        Internally, salabim still works with the 'old' time. Only in the interface
        from and to the user program, a correction will be applied.

        The registered time in monitors will be always is the 'old' time.
        This is only relevant when using the time value in Monitor.xt() or Monitor.tx().
        """
        offset_before = self._offset
        if callable(new_now):
            new_now = new_now()
        self._offset = self._now - new_now

        if self._trace:
            self.print_trace("", "", f"now reset to {new_now:0.3f}", f"(all times are reduced by {(self._offset - offset_before):0.3f})")

        if self._datetime0:
            self._datetime0 += datetime.timedelta(seconds=self.to_seconds(self._offset - offset_before))
            self.print_trace("", "", "", f"(t=0 ==> to {self.time_to_str(0)})")

    def trace(self, value=None):
        """
        trace status

        Parameters
        ----------
        value : bool of file handle
            new trace status |n|
            defines whether to trace or not |n|
            if this a file handle (open for write), the trace output will be sent to this file. |n|
            if omitted, no change

        Returns
        -------
        trace status : bool or file handle

        Note
        ----
        If you want to test the status, always include
        parentheses, like

            ``if env.trace():``
        """
        if value is not None:
            self._trace = value
            self._buffered_trace = False
        return self._trace

    def suppress_trace_linenumbers(self, value=None):
        """
        indicates whether line numbers should be suppressed (False by default)

        Parameters
        ----------
        value : bool
            new suppress_trace_linenumbers status |n|
            if omitted, no change

        Returns
        -------
        suppress_trace_linenumbers status : bool

        Note
        ----
        By default, suppress_trace_linenumbers is False, meaning that line numbers are shown in the trace.
        In order to improve performance, line numbers can be suppressed.
        """
        if value is not None:
            self._suppress_trace_linenumbers = value
        return self._suppress_trace_linenumbers

    def suppress_trace_standby(self, value=None):
        """
        suppress_trace_standby status

        Parameters
        ----------
        value : bool
            new suppress_trace_standby status |n|
            if omitted, no change

        Returns
        -------
        suppress trace status : bool

        Note
        ----
        By default, suppress_trace_standby is True, meaning that standby components are
        (apart from when they become non standby) suppressed from the trace. |n|
        If you set suppress_trace_standby to False, standby components are fully traced.
        """
        if value is not None:
            self._suppress_trace_standby = value
            self._buffered_trace = False
        return self._suppress_trace_standby

    def current_component(self):
        """
        Returns
        -------
        the current_component : Component
        """
        return self._current_component

    def run(self, duration=None, till=None, priority=inf, urgent=False, cap_now=None):
        """
        start execution of the simulation

        Parameters
        ----------
        duration : float or distribution
            schedule with a delay of duration |n|
            if 0, now is used |n|
            if distribution, the distribution is sampled

        till : float or distribution
            schedule time |n|
            if omitted, inf is assumed. See also note below |n|
            if distribution, the distribution is sampled

        priority : float
            priority |n|
            default: inf |n|
            if a component has the same time on the event list, main is sorted accoring to
            the priority. The default value of inf makes that all components will finish before
            the run is ended

        urgent : bool
            urgency indicator |n|
            if False (default), main will be scheduled
            behind all other components scheduled with the same time and priority |n|
            if True, main will be scheduled
            in front of all components scheduled
            for the same time and priority

        cap_now : bool
            indicator whether times (till, duration) in the past are allowed. If, so now() will be used.
            default: sys.default_cap_now(), usualy False

        Note
        ----
        if neither till nor duration is specified, the main component will be reactivated at
        the time there are no more events on the eventlist, i.e. possibly not at inf. |n|
        if you want to run till inf (particularly when animating), issue run(sim.inf) |n|
        only issue run() from the main level
        """
        self.end_on_empty_eventlist = False
        extra = ""
        if till is None:
            if duration is None:
                scheduled_time = inf
                self.end_on_empty_eventlist = True
                extra = "*"
            else:
                if duration == inf:
                    scheduled_time = inf
                else:
                    if callable(duration):
                        duration = duration()
                    scheduled_time = self.env._now + duration
        else:
            if callable(till):
                till = till()
            if duration is None:
                scheduled_time = till + self.env._offset
            else:
                raise ValueError("both duration and till specified")

        self._main.frame = _get_caller_frame()
        self._main.status._value = scheduled
        self._main._reschedule(scheduled_time, priority, urgent, "run", cap_now, extra=extra)

        self.running = True
        while self.running:
            if self._animate and not self._blind_animation:
                self.do_simulate_and_animate()
            else:
                self.do_simulate()
        if self.stopped:
            self.quit()
            if self._video:
                self.video_close()
            raise SimulationStopped

    def do_simulate(self):
        if self._blind_animation:
            while self.running:
                self.step()
        else:
            while g.in_draw:
                pass
            while self.running and not self._animate:
                self.step()

    def do_simulate_and_animate(self):
        if Pythonista:
            if self._animate3d:
                self.running = False
                raise ImportError("3d animation not supported under Pythonista")
            while self.running and self._animate:
                pass
            if self.stopped:
                raise SimulationStopped
        else:
            self.root.after(0, self.simulate_and_animate_loop)
            self.root.mainloop()
            if self._animate and self.running:
                if self._video:
                    self.video_close()
                raise SimulationStopped

    def simulate_and_animate_loop(self):
        while True:
            if self._animate3d and not self._gl_initialized:
                self.animation3d_init()
                self._camera_control()
                self.start_animation_clocktime = time.time()
                self.start_animation_time = self._t

            tick_start = time.time()

            if self._synced or self._video:  # video forces synced
                if self._video:
                    self._t = self.video_t
                else:
                    if self.paused:
                        self._t = self.start_animation_time
                    else:
                        self._t = self.start_animation_time + ((time.time() - self.start_animation_clocktime) * self._speed)

                while self.peek() < self._t:
                    self.step()
                    if not (self.running and self._animate):
                        if self.root is not None:
                            self.root.quit()
                        return
                    if self.paused:
                        self._t = self.start_animation_time = self._now
                        break

            else:
                if self._step_pressed or (not self.paused):
                    self.step()

                    if not self._current_component._suppress_pause_at_step:
                        self._step_pressed = False
                    self._t = self._now

            if not (self.running and self._animate):
                if self.root is not None:
                    self.root.quit()
                return

            if not self.paused:
                self.frametimes.append(time.time())

            t = self.t()

            self.animation_pre_tick(t)
            self.animation_pre_tick_sys(t)

            an_objects = sorted(self.an_objects, key=lambda obj: (-obj.layer(self._t), obj.sequence))

            canvas_objects_iter = iter(g.canvas_objects[:])
            co = next(canvas_objects_iter, None)
            overflow_image = None
            for ao in an_objects:
                ao.make_pil_image(t)
                if ao._image_visible:
                    if co is None:
                        if len(g.canvas_objects) >= self._maximum_number_of_bitmaps:
                            if overflow_image is None:
                                overflow_image = Image.new("RGBA", (self._width, self._height), (0, 0, 0, 0))
                            overflow_image.paste(ao._image, (int(ao._image_x), int(self._height - ao._image_y - ao._image.size[1])), ao._image)
                            ao.canvas_object = None
                        else:
                            ao.im = ImageTk.PhotoImage(ao._image)
                            co1 = g.canvas.create_image(ao._image_x, self._height - ao._image_y, image=ao.im, anchor=tkinter.SW)
                            g.canvas_objects.append(co1)
                            ao.canvas_object = co1

                    else:
                        if ao.canvas_object == co:
                            if ao._image_ident != ao._image_ident_prev:
                                ao.im = ImageTk.PhotoImage(ao._image)
                                g.canvas.itemconfig(ao.canvas_object, image=ao.im)

                            if (ao._image_x != ao._image_x_prev) or (ao._image_y != ao._image_y_prev):
                                g.canvas.coords(ao.canvas_object, (ao._image_x, self._height - ao._image_y))

                        else:
                            ao.im = ImageTk.PhotoImage(ao._image)
                            ao.canvas_object = co
                            g.canvas.itemconfig(ao.canvas_object, image=ao.im)
                            g.canvas.coords(ao.canvas_object, (ao._image_x, self._height - ao._image_y))
                    co = next(canvas_objects_iter, None)
                else:
                    ao.canvas_object = None

            if overflow_image is None:
                if g.canvas_object_overflow_image is not None:
                    g.canvas.delete(g.canvas_object_overflow_image)
                    g.canvas_object_overflow_image = None

            else:
                im = ImageTk.PhotoImage(overflow_image)
                if g.canvas_object_overflow_image is None:
                    g.canvas_object_overflow_image = g.canvas.create_image(0, self._height, image=im, anchor=tkinter.SW)
                else:
                    g.canvas.itemconfig(g.canvas_object_overflow_image, image=im)

            if self._animate3d:
                self._exclude_from_animation = "*"  # makes that both video and non video over2d animation objects are shown
                an_objects3d = sorted(self.an_objects3d, key=lambda obj: (obj.layer(self._t), obj.sequence))
                for an in an_objects3d:
                    if an.keep(t):
                        if an.visible(t):
                            an.draw(t)
                    else:
                        an.remove()
                self._exclude_from_animation = "only in video"

            self.animation_post_tick(t)

            while co is not None:
                g.canvas.delete(co)
                g.canvas_objects.remove(co)
                co = next(canvas_objects_iter, None)

            for uio in self.ui_objects:
                if not uio.installed:
                    uio.install()

            for uio in self.ui_objects:
                if uio.type == "button":
                    thistext = uio.text()
                    if thistext != uio.lasttext:
                        uio.lasttext = thistext
                        uio.button.config(text=thistext)

            if self._video:
                if not self.paused:
                    self._save_frame()
                    self.video_t += self._speed / self._fps
                    self.frame_number += 1
            else:
                if self._synced:
                    tick_duration = time.time() - tick_start
                    if tick_duration < 1 / self._fps:
                        time.sleep(((1 / self._fps) - tick_duration) * 0.8)
                        # 0.8 compensation because of clock inaccuracy

            g.canvas.update()

    def snapshot(self, filename, video_mode="2d"):
        """
        Takes a snapshot of the current animated frame (at time = now()) and saves it to a file

        Parameters
        ----------
        filename : str
            file to save the current animated frame to. |n|
            The following formats are accepted: .png, .jpg, .bmp, .ico, .gif and .tiff.
            Other formats are not possible.
            Note that, apart from .JPG files. the background may be semi transparent by setting
            the alpha value to something else than 255.

        video_mode : str
            specifies what to save |n|
            if "2d" (default), the tkinter window will be saved |n|
            if "3d", the OpenGL window will be saved (provided animate3d is True) |n|
            if "screen" the complete screen will be saved (no need to be in animate mode)|n|
            no scaling will be applied.
        """
        if video_mode not in ("2d", "3d", "screen"):
            raise ValueError("video_mode " + video_mode + " not recognized")
        can_animate(try_only=False)

        if video_mode == "screen" and ImageGrab is None:
            raise ValueError("video_mode='screen' not supported on this platform (ImageGrab does not exist)")

        filename_path = Path(filename)
        extension = filename_path.suffix.lower()
        if extension in (".png", ".gif", ".bmp", ".ico", ".tiff"):
            mode = "RGBA"
        elif extension == ".jpg":
            mode = "RGB"
        else:
            raise ValueError("extension " + extension + "  not supported")
        filename_path.parent.mkdir(parents=True, exist_ok=True)
        self._capture_image(mode, video_mode).save(filename)

    def modelname_width(self):
        if Environment.cached_modelname_width[0] != self._modelname:
            Environment.cached_modelname_width = [self._modelname, self.env.getwidth(self._modelname + " : a ", font="", fontsize=18)]
        return Environment.cached_modelname_width[1]

    def an_modelname(self):
        """
        function to show the modelname |n|
        may be overridden to change the standard behaviour.
        """

        y = -68
        AnimateText(
            text=lambda: self._modelname + " : a",
            x=8,
            y=y,
            text_anchor="w",
            fontsize=18,
            font="",
            screen_coordinates=True,
            xy_anchor="nw",
            env=self,
            visible=lambda: self._modelname,
        )
        AnimateImage(
            image=lambda: self.salabim_logo(),
            x=lambda: self.modelname_width() + 8,
            y=y + 1,
            offsety=5,
            anchor="w",
            width=61,
            screen_coordinates=True,
            xy_anchor="nw",
            visible=lambda: self._modelname,
        )
        an = AnimateText(
            text=" model",
            x=lambda: self.modelname_width() + 69,
            y=y,
            text_anchor="w",
            fontsize=18,
            font="",
            screen_coordinates=True,
            xy_anchor="nw",
            visible=lambda: self._modelname,
            env=self,
        )

    def an_menu_buttons(self):
        """
        function to initialize the menu buttons |n|
        may be overridden to change the standard behaviour.
        """
        self.remove_topleft_buttons()
        if self.colorspec_to_tuple("bg")[:-1] == self.colorspec_to_tuple("blue")[:-1]:
            fillcolor = "white"
            color = "blue"
        else:
            fillcolor = "blue"
            color = "white"

        uio = AnimateButton(x=38, y=-21, text="Menu", width=50, action=self.env.an_menu, env=self, fillcolor=fillcolor, color=color, xy_anchor="nw")

        uio.in_topleft = True

    def an_unsynced_buttons(self):
        """
        function to initialize the unsynced buttons |n|
        may be overridden to change the standard behaviour.
        """
        self.remove_topleft_buttons()
        if self.colorspec_to_tuple("bg")[:-1] == self.colorspec_to_tuple("green")[:-1]:
            fillcolor = "lightgreen"
            color = "green"
        else:
            fillcolor = "green"
            color = "white"
        uio = AnimateButton(x=38, y=-21, text="Go", width=50, action=self.env.an_go, env=self, fillcolor=fillcolor, color=color, xy_anchor="nw")
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 1 * 60, y=-21, text="Step", width=50, action=self.env.an_step, env=self, xy_anchor="nw")
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 3 * 60, y=-21, text="Synced", width=50, action=self.env.an_synced_on, env=self, xy_anchor="nw")
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 4 * 60, y=-21, text="Trace", width=50, action=self.env.an_trace, env=self, xy_anchor="nw")
        uio.in_topleft = True

        if self.colorspec_to_tuple("bg")[:-1] == self.colorspec_to_tuple("red")[:-1]:
            fillcolor = "lightsalmon"
            color = "white"
        else:
            fillcolor = "red"
            color = "white"

        uio = AnimateButton(x=38 + 5 * 60, y=-21, text="Stop", width=50, action=self.env.an_quit, env=self, fillcolor=fillcolor, color=color, xy_anchor="nw")
        uio.in_topleft = True

        ao = AnimateText(x=38 + 3 * 60, y=-35, text=self.syncedtext, text_anchor="N", fontsize=15, font="", screen_coordinates=True, xy_anchor="nw")
        ao.in_topleft = True

        ao = AnimateText(x=38 + 4 * 60, y=-35, text=self.tracetext, text_anchor="N", fontsize=15, font="", screen_coordinates=True, xy_anchor="nw")
        ao.in_topleft = True

    def an_synced_buttons(self):
        """
        function to initialize the synced buttons |n|
        may be overridden to change the standard behaviour.
        """
        self.remove_topleft_buttons()
        if self.colorspec_to_tuple("bg")[:-1] == self.colorspec_to_tuple("green")[:-1]:
            fillcolor = "lightgreen"
            color = "green"
        else:
            fillcolor = "green"
            color = "white"

        uio = AnimateButton(x=38, y=-21, text="Go", width=50, action=self.env.an_go, env=self, fillcolor=fillcolor, color=color, xy_anchor="nw")
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 1 * 60, y=-21, text="/2", width=50, action=self.env.an_half, env=self, xy_anchor="nw")
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 2 * 60, y=-21, text="*2", width=50, action=self.env.an_double, env=self, xy_anchor="nw")
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 3 * 60, y=-21, text="Synced", width=50, action=self.env.an_synced_off, env=self, xy_anchor="nw")
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 4 * 60, y=-21, text="Trace", width=50, action=self.env.an_trace, env=self, xy_anchor="nw")
        uio.in_topleft = True

        if self.colorspec_to_tuple("bg") == self.colorspec_to_tuple("red"):
            fillcolor = "lightsalmon"
            color = "white"
        else:
            fillcolor = "red"
            color = "white"
        uio = AnimateButton(x=38 + 5 * 60, y=-21, text="Stop", width=50, action=self.env.an_quit, env=self, fillcolor=fillcolor, color=color, xy_anchor="nw")
        uio.in_topleft = True

        ao = AnimateText(
            x=38 + 1.5 * 60, y=-35, text=self.speedtext, textcolor="fg", text_anchor="N", fontsize=15, font="", screen_coordinates=True, xy_anchor="nw"
        )
        ao.in_topleft = True

        ao = AnimateText(x=38 + 3 * 60, y=-35, text=self.syncedtext, text_anchor="N", fontsize=15, font="", screen_coordinates=True, xy_anchor="nw")
        ao.in_topleft = True

        ao = AnimateText(x=38 + 4 * 60, y=-35, text=self.tracetext, text_anchor="N", fontsize=15, font="", screen_coordinates=True, xy_anchor="nw")
        ao.in_topleft = True

    def remove_topleft_buttons(self):
        for uio in self.ui_objects[:]:
            if getattr(uio, "in_topleft", False):
                uio.remove()

        for ao in self.an_objects.copy():
            if getattr(ao, "in_topleft", False):
                ao.remove()

    def an_clocktext(self):
        """
        function to initialize the system clocktext |n|
        called by run(), if animation is True. |n|
        may be overridden to change the standard behaviour.
        """
        ao = AnimateText(
            x=-30 if Pythonista else 0,
            y=-11 if Pythonista else 0,
            textcolor="fg",
            text=self.clocktext,
            fontsize=15,
            font="mono",
            text_anchor="ne",
            screen_coordinates=True,
            xy_anchor="ne",
            env=self,
        )
        ao.text = self.clocktext

    def an_half(self):
        self._speed /= 2
        self.set_start_animation()

    def an_double(self):
        self._speed *= 2
        self.set_start_animation()

    def an_go(self):
        self.paused = False
        if self._synced:
            self.set_start_animation()
        else:
            self._step_pressed = True  # force to next event
        self.an_menu_buttons()

    def an_quit(self):
        self._animate = False
        self.running = False
        self.stopped = True
        if not Pythonista:
            if self.root is not None:  # for blind animation to work properly
                self.root.destroy()
                self.root = None
        self.quit()

    def quit(self):
        if g.animation_env is not None:
            g.animation_env.animation_parameters(animate=False, video="")  # stop animation
        if Pythonista:
            if g.animation_scene is not None:
                g.animation_scene.view.close()

    def an_trace(self):
        self._trace = not self._trace

    def an_synced_on(self):
        self._synced = True
        self.an_synced_buttons()

    def an_synced_off(self):
        self._synced = False
        self.an_unsynced_buttons()

    def an_step(self):
        self._step_pressed = True

    def an_single_step(self):
        self._step_pressed = True
        self.step()
        self.paused = True
        self._t = self._now
        self.set_start_animation()

    def an_menu_go(self):
        if self.paused:
            self.an_go()
        else:
            self.an_menu()

    def an_menu(self):
        self.paused = True
        self.set_start_animation()
        if self._synced:
            self.an_synced_buttons()
        else:
            self.an_unsynced_buttons()

    def clocktext(self, t):
        s = ""
        if self._synced and (not self.paused) and self._show_fps:
            if len(self.frametimes) >= 2:
                fps = (len(self.frametimes) - 1) / (self.frametimes[-1] - self.frametimes[0])
            else:
                fps = 0
            s += f"fps={fps:.1f}"

        if self._show_time:
            if s != "":
                s += " "
            s += "t=" + self.time_to_str(t).lstrip()
        return s

    def tracetext(self, t):
        if self._trace:
            return "= on"
        else:
            return "= off"

    def syncedtext(self, t):
        if self._synced:
            return "= on"
        else:
            return "= off"

    def speedtext(self, t):
        return f"speed = {self._speed:.3f}"

    def set_start_animation(self):
        self.frametimes = collections.deque(maxlen=30)
        self.start_animation_time = self._t
        self.start_animation_clocktime = time.time()
        if self._audio:
            start_time = self._t - self._audio.t0 + self._audio.start
            if Pythonista:
                if self._animate and self._synced and (not self._video):
                    if self.paused:
                        self._audio.player.pause()
                    else:
                        if self._speed == self._audio_speed:
                            self._audio.player.current_time = start_time
                            self._audio.player.play()
            if Windows:
                if self._animate and self._synced and (not self._video):
                    if self.paused:
                        self._audio.pause()
                    else:
                        if self._speed == self._audio_speed:
                            if start_time < self._audio.duration:
                                self._audio.play(start=start_time)

    def xy_anchor_to_x(self, xy_anchor, screen_coordinates, over3d=False, retina_scale=False):
        scale = self.retina if (retina_scale and self.retina > 1) else 1
        if over3d:
            width = self._width3d
        else:
            width = self._width
        if xy_anchor in ("nw", "w", "sw"):
            if screen_coordinates:
                return 0
            else:
                return self._x0 / scale

        if xy_anchor in ("n", "c", "center", "s"):
            if screen_coordinates:
                return (width / 2) / scale
            else:
                return ((self._x0 + self._x1) / 2) / scale

        if xy_anchor in ("ne", "e", "se", ""):
            if screen_coordinates:
                return width / scale
            else:
                return self._x1 / scale

        raise ValueError("incorrect xy_anchor", xy_anchor)

    def xy_anchor_to_y(self, xy_anchor, screen_coordinates, over3d=False, retina_scale=False):
        scale = self.retina if (retina_scale and self.retina > 1) else 1
        if over3d:
            height = self._height3d
        else:
            height = self._height

        if xy_anchor in ("nw", "n", "ne"):
            if screen_coordinates:
                return height / scale
            else:
                return self._y1 / scale

        if xy_anchor in ("w", "c", "center", "e"):
            if screen_coordinates:
                return (height / 2) / scale
            else:
                return ((self._y0 + self._y1) / 2) / scale

        if xy_anchor in ("sw", "s", "se", ""):
            if screen_coordinates:
                return 0
            else:
                return self._y0 / scale

        raise ValueError("incorrect xy_anchor", xy_anchor)

    def salabim_logo(self):
        if self.is_dark("bg"):
            return salabim_logo_red_white_200()
        else:
            return salabim_logo_red_black_200()

    def colorspec_to_tuple(self, colorspec):
        """
        translates a colorspec to a tuple

        Parameters
        ----------
        colorspec: tuple, list or str
            ``#rrggbb`` ==> alpha = 255 (rr, gg, bb in hex) |n|
            ``#rrggbbaa`` ==> alpha = aa (rr, gg, bb, aa in hex) |n|
            ``colorname`` ==> alpha = 255 |n|
            ``(colorname, alpha)`` |n|
            ``(r, g, b)`` ==> alpha = 255 |n|
            ``(r, g, b, alpha)`` |n|
            ``"fg"`` ==> foreground_color |n|
            ``"bg"`` ==> background_color

        Returns
        -------
        (r, g, b, a)
        """
        if colorspec is None:
            colorspec = ""
        if colorspec == "fg":
            colorspec = self.colorspec_to_tuple(self._foreground_color)
        elif colorspec == "bg":
            colorspec = self.colorspec_to_tuple(self._background_color)
        if isinstance(colorspec, (tuple, list)):
            if len(colorspec) == 2:
                c = self.colorspec_to_tuple(colorspec[0])
                return (c[0], c[1], c[2], colorspec[1])
            elif len(colorspec) == 3:
                return (colorspec[0], colorspec[1], colorspec[2], 255)
            elif len(colorspec) == 4:
                return colorspec
        else:
            if (colorspec != "") and (colorspec[0]) == "#":
                if len(colorspec) == 7:
                    return (int(colorspec[1:3], 16), int(colorspec[3:5], 16), int(colorspec[5:7], 16), 255)
                elif len(colorspec) == 9:
                    return (int(colorspec[1:3], 16), int(colorspec[3:5], 16), int(colorspec[5:7], 16), int(colorspec[7:9], 16))
            else:
                s = colorspec.split("#")
                if len(s) == 2:
                    alpha = s[1]
                    colorspec = s[0]
                else:
                    alpha = "FF"
                try:
                    colorhex = colornames()[colorspec.replace(" ", "").lower()]
                    if len(colorhex) == 7:
                        colorhex = colorhex + alpha
                    return self.colorspec_to_tuple(colorhex)
                except KeyError:
                    pass

        raise ValueError("wrong color specification: " + str(colorspec))

    def colorinterpolate(self, t, t0, t1, v0, v1):
        """
        does linear interpolation of colorspecs

        Parameters
        ----------
        t : float
            value to be interpolated from

        t0: float
            f(t0)=v0

        t1: float
            f(t1)=v1

        v0: colorspec
            f(t0)=v0

        v1: colorspec
            f(t1)=v1

        Returns
        -------
        linear interpolation between v0 and v1 based on t between t0 and t : colorspec

        Note
        ----
        Note that no extrapolation is done, so if t<t0 ==> v0  and t>t1 ==> v1 |n|
        This function is heavily used during animation
        """
        if v0 == v1:
            return v0
        if t1 == inf:
            return v0
        if t0 == t1:
            return v1
        vt0 = self.colorspec_to_tuple(v0)
        vt1 = self.colorspec_to_tuple(v1)
        return tuple(int(c) for c in interpolate(t, t0, t1, vt0, vt1))

    def color_interp(self, x, xp, fp):
        """
        linear interpolation of a color

        Parameters
        ----------
        x : float
            target x-value

        xp : list of float, tuples or lists
            values on the x-axis

        fp : list of colorspecs
            values on the y-axis |n|
            should be same length as xp

        Returns
        -------
        interpolated color value : tuple

        Notes
        -----
        If x < xp[0], fp[0] will be returned |n|
        If x > xp[-1], fp[-1] will be returned |n|
        """
        fp_resolved = [self.colorspec_to_tuple(el) for el in fp]
        return tuple(map(int, interp(x, xp, fp_resolved)))

    def colorspec_to_hex(self, colorspec, withalpha=True):
        v = self.colorspec_to_tuple(colorspec)
        if withalpha:
            return f"#{int(v[0]):02x}{int(v[1]):02x}{int(v[2]):02x}{int(v[3]):02x}"
        else:
            return f"#{int(v[0]):02x}{int(v[1]):02x}{int(v[2]):02x}"

    def colorspec_to_gl_color(self, colorspec):
        color_tuple = self.colorspec_to_tuple(colorspec)
        return (color_tuple[0] / 255, color_tuple[1] / 255, color_tuple[2] / 255)

    def colorspec_to_gl_color_alpha(self, colorspec):
        color_tuple = self.colorspec_to_tuple(colorspec)
        return ((color_tuple[0] / 255, color_tuple[1] / 255, color_tuple[2] / 255), color_tuple[3])

    def pythonistacolor(self, colorspec):
        c = self.colorspec_to_tuple(colorspec)
        return (c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255)

    def is_dark(self, colorspec):
        """
        Arguments
        ---------
        colorspec : colorspec
            color to check

        Returns
        -------
        : bool
            True, if the colorspec is dark (rather black than white) |n|
            False, if the colorspec is light (rather white than black |n|
            if colorspec has alpha=0 (total transparent), the background_color will be tested
        """
        rgba = self.colorspec_to_tuple(colorspec)
        if rgba[3] == 0:
            return self.is_dark(self.colorspec_to_tuple(("bg", 255)))
        luma = ((0.299 * rgba[0]) + (0.587 * rgba[1]) + (0.114 * rgba[2])) / 255
        if luma > 0.5:
            return False
        else:
            return True

    def getwidth(self, text, font, fontsize, screen_coordinates=False):
        if not screen_coordinates:
            fontsize = fontsize * self._scale
        f, heightA = getfont(font, fontsize)
        if text == "":  # necessary because of bug in PIL >= 4.2.1
            thiswidth, thisheight = (0, 0)
        else:
            thiswidth, thisheight = f.getsize(text)
        if screen_coordinates:
            return thiswidth
        else:
            return thiswidth / self._scale

    def getheight(self, font, fontsize, screen_coordinates=False):
        if not screen_coordinates:
            fontsize = fontsize * self._scale
        f, heightA = getfont(font, fontsize)
        thiswidth, thisheight = f.getsize("Ap")
        if screen_coordinates:
            return thisheight
        else:
            return thisheight / self._scale

    def getfontsize_to_fit(self, text, width, font, screen_coordinates=False):
        if not screen_coordinates:
            width = width * self._scale

        lastwidth = 0
        for fontsize in range(1, 300):
            f = getfont(font, fontsize)
            thiswidth, thisheight = f.getsize(text)
            if thiswidth > width:
                break
            lastwidth = thiswidth
        fontsize = interpolate(width, lastwidth, thiswidth, fontsize - 1, fontsize)
        if screen_coordinates:
            return fontsize
        else:
            return fontsize / self._scale

    def name(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the environment
            if omitted, no change

        Returns
        -------
        Name of the environment : str

        Note
        ----
        base_name and sequence_number are not affected if the name is changed
        """
        if value is not None:
            self._name = value
        return self._name

    def base_name(self):
        """
        returns the base name of the environment (the name used at initialization)
        """
        return self._base_name

    def sequence_number(self):
        """
        Returns
        -------
        sequence_number of the environment : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        """
        return self._sequence_number

    def get_time_unit(self):
        """
        gets time unit

        Returns
        -------
        Current time unit dimension (default "n/a") : str
        """
        return self._time_unit_name

    def years(self, t):
        """
        convert the given time in years to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in years |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in years, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * 86400 * 365 * self._time_unit

    def weeks(self, t):
        """
        convert the given time in weeks to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in weeks |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in weeks, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * 86400 * 7 * self._time_unit

    def days(self, t):
        """
        convert the given time in days to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in days |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in days, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * 86400 * self._time_unit

    def hours(self, t):
        """
        convert the given time in hours to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in hours |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in hours, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * 3600 * self._time_unit

    def minutes(self, t):
        """
        convert the given time in minutes to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in minutes |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in minutes, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * 60 * self._time_unit

    def seconds(self, t):
        """
        convert the given time in seconds to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in seconds |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in secoonds, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * self._time_unit

    def milliseconds(self, t):
        """
        convert the given time in milliseconds to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in milliseconds |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in milliseconds, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * 1e-3 * self._time_unit

    def microseconds(self, t):
        """
        convert the given time in microseconds to the current time unit

        Parameters
        ----------
        t : float or distribution
            time in microseconds |n|
            if distribution, the distribution is sampled

        Returns
        -------
        time in microseconds, converted to the current time_unit : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * 1e-6 * self._time_unit

    def to_time_unit(self, time_unit, t):
        """
        convert time t to the time_unit specified

        Parameters
        ----------
        time_unit : str
            Supported time_units: |n|
            "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds"

        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to the time_unit specified : float
        """
        self._check_time_unit_na()
        if callable(t):
            t = t()
        return t * _time_unit_lookup(time_unit) / self._time_unit

    def to_years(self, t):
        """
        convert time t to years

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to years : float
        """
        return self.to_time_unit("years", t)

    def to_weeks(self, t):
        """
        convert time t to weeks

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to weeks : float
        """
        return self.to_time_unit("weeks", t)

    def to_days(self, t):
        """
        convert time t to days

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to days : float
        """
        return self.to_time_unit("days", t)

    def to_hours(self, t):
        """
        convert time t to hours

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to hours : float
        """
        return self.to_time_unit("hours", t)

    def to_minutes(self, t):
        """
        convert time t to minutes

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to minutes : float
        """
        return self.to_time_unit("minutes", t)

    def to_seconds(self, t):
        """
        convert time t to seconds

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to seconds : float
        """
        return self.to_time_unit("seconds", t)

    def to_milliseconds(self, t):
        """
        convert time t to milliseconds

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to milliseconds : float
        """
        return self.to_time_unit("milliseconds", t)

    def to_microseconds(self, t):
        """
        convert time t to microseconds

        Parameters
        ----------
        t : float or distribution
            time to be converted |n|
            if distribution, the distribution is sampled

        Returns
        -------
        Time t converted to microseconds : float
        """
        return self.to_time_unit("microseconds", t)

    def _check_time_unit_na(self):
        if self._time_unit is None:
            raise AttributeError("time_unit is not available")

    def print_trace_header(self):
        """
        print a (two line) header line as a legend |n|
        also the legend for line numbers will be printed |n|
        not that the header is only printed if trace=True
        """
        len_s1 = len(self.time_to_str(0))
        self.print_trace((len_s1 - 4) * " " + "time", "current component", "action", "information", "line#")
        self.print_trace(len_s1 * "-", 20 * "-", 35 * "-", 48 * "-", 6 * "-")
        for ref in range(len(self._source_files)):
            for fullfilename, iref in self._source_files.items():
                if ref == iref:
                    self._print_legend(iref)

    def _print_legend(self, ref):
        if ref:
            s = "line numbers prefixed by " + chr(ord("A") + ref - 1) + " refer to"
        else:
            s = "line numbers refers to"
        for fullfilename, iref in self._source_files.items():
            if ref == iref:
                self.print_trace("", "", s, (os.path.basename(fullfilename)), "")
                break

    def _frame_to_lineno(self, frame, add_filename=False):
        frameinfo = inspect.getframeinfo(frame)
        if add_filename:
            return str(frameinfo.lineno) + " in " + os.path.basename(frameinfo.filename)
        return self.filename_lineno_to_str(frameinfo.filename, frameinfo.lineno)

    def filename_lineno_to_str(self, filename, lineno):
        ref = self._source_files.get(filename)
        new_entry = False
        if ref is None:
            if self._source_files:
                ref = len(self._source_files)
            self._source_files[filename] = ref
            new_entry = True
        if ref == 0:
            pre = ""
        else:
            pre = chr(ref + ord("A") - 1)
        if new_entry:
            self._print_legend(ref)
        return rpad(pre + str(lineno), 5)

    def print_trace(self, s1="", s2="", s3="", s4="", s0=None, _optional=False):
        """
        prints a trace line

        Parameters
        ----------
        s1 : str
            part 1 (usually formatted  now), padded to 10 characters

        s2 : str
            part 2 (usually only used for the compoent that gets current), padded to 20 characters

        s3 : str
            part 3, padded to 35 characters

        s4 : str
            part 4

        s0 : str
            part 0. if omitted, the line number from where the call was given will be used at
            the start of the line. Otherwise s0, left padded to 7 characters will be used at
            the start of the line.

        _optional : bool
            for internal use only. Do not set this flag!

        Note
        ----
        if self.trace is False, nothing is printed |n|
        if the current component's suppress_trace is True, nothing is printed |n|
        """
        len_s1 = len(self.time_to_str(0))
        if self._trace:
            if not (hasattr(self, "_current_component") and self._current_component._suppress_trace):
                if s0 is None:
                    if self._suppress_trace_linenumbers:
                        s0 = ""
                    else:
                        #                        stack = inspect.stack()
                        #                        filename0 = inspect.getframeinfo(stack[0][0]).filename
                        #                        for i in range(len(inspect.stack())):
                        #                            frame = stack[i][0]
                        #                            if filename0 != inspect.getframeinfo(frame).filename:
                        #                                break

                        s0 = self._frame_to_lineno(_get_caller_frame())
                self.last_s0 = s0
                line = pad(s0, 7) + pad(s1, len_s1) + " " + pad(s2, 20) + " " + pad(s3, max(len(s3), 36)) + " " + s4.strip()
                if _optional:
                    self._buffered_trace = line
                else:
                    if self._buffered_trace:
                        if hasattr(self._trace, "write"):
                            print(self._buffered_trace, file=self._trace)
                        else:
                            print(self._buffered_trace)
                        logging.debug(self._buffered_trace)
                        self._buffered_trace = False
                    if hasattr(self._trace, "write"):
                        print(line, file=self._trace)
                    else:
                        print(line)
                    logging.debug(line)

    def time_to_str(self, t):
        """
        Parameters
        ----------
        t : float
            time to be converted to string in trace and animation

        Returns
        -------
        t in required format : str
            default: f"{t:10.3f}" if datetime0 is False |n|
            or date in the format "Day YYYY-MM-DD hh:mm:dd" otherwise

        Note
        ----
        May be overrridden. Make sure that the method always returns the same length!
        """
        if self._datetime0:
            if t == inf:
                return f"{'inf':23}"
            date = self.t_to_datetime(t)
            return f"{('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[date.weekday()]} {date.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"{t:10.3f}"

    def duration_to_str(self, duration):
        """
        Parameters
        ----------
        duration : float
            duration to be converted to string in trace

        Returns
        -------
        duration in required format : str
            default: f"{duration:.3f}" if datetime0 is False
            or duration in the format "hh:mm:dd" or "d hh:mm:ss"

        Note
        ----
        May be overrridden.
        """
        if self._datetime0:
            if duration == inf:
                return "inf"
            duration = self.to_seconds(duration)
            days, rem = divmod(duration, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            if days:
                return f"{int(days)} {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            else:
                return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        return f"{duration:.3f}"

    def datetime_to_t(self, datetime):
        """
        Parameters
        ----------
        datetime : datetime.datetime

        Returns
        -------
        datetime translated to simulation time in the current time_unit : float

        Raises
        ------
        ValueError
            if datetime0 is False
        """
        if self._datetime0:
            return self.seconds(datetime - self._datetime0).total_seconds()
        raise ValueError("datetime_to_t only possible if datetime0 is given")

    def timedelta_to_duration(self, timedelta):
        """
        Parameters
        ----------
        timedelta : datetime.timedelta

        Returns
        -------
        timedelta translated to simulation duration in the current time_unit : float

        Raises
        ------
        ValueError
            if datetime0 is False
        """
        if self._datetime0:
            return self.seconds(timedelta.total_seconds())
        raise ValueError("timestamp_to_duration only possible if datetime0 is given")

    def t_to_datetime(self, t):
        """
        Parameters
        ----------
        t : float
            time to convert

        Returns
        -------
        t (in the current time unit) translated to the corresponding datetime : float

        Raises
        ------
        ValueError
            if datetime0 is False
        """
        if self._datetime0:
            if t == inf:
                return t
            return self._datetime0 + datetime.timedelta(seconds=self.to_seconds(t))
        raise ValueError("datetime_to_t only possible if datetime0 is given")

    def duration_to_timedelta(self, duration):
        """
        Parameters
        ----------
        duration : float

        Returns
        -------
        timedelta corresponding to duration : datetime.timedelta

        Raises
        ------
        ValueError
            if time unit is not set
        """
        if self._time_unit:
            return datetime.timedelta(seconds=self.to_seconds(duration))
        raise ValueError("timestamp_to_duration only possible if time unit is given")

    def datetime0(self, datetime0=None):
        """
        Gets and/or sets datetime0

        Parameters
        ----------
        datetime0: bool or datetime.datetime
            if omitted, nothing will be set |n|
            if falsy, disabled |n|
            if True, the t=0 will correspond to 1 January 1970 |n|
            if no time_unit is specified, but datetime0 is not falsy, time_unit will be set to seconds

        Returns
        -------
        current value of datetime0 : bool or datetime.datetime
        """
        if datetime0 is not None:
            if datetime0:
                if datetime0 is True:
                    self._datetime0 = datetime.datetime(1970, 1, 1)
                else:
                    if not isinstance(datetime0, datetime.datetime):
                        raise ValueError(f"datetime0 should be datetime.datetime or True, not {type(datetime0)}")
                    self._datetime0 = datetime0
                if self._time_unit is None:
                    self._time_unit = _time_unit_lookup("seconds")
                    self._time_unit_name = "seconds"
            else:
                self._datetime0 = False
        return self._datetime0

    def beep(self):
        """
        Beeps

        Works only on Windows and iOS (Pythonista). For other platforms this is just a dummy method.
        """
        if Windows:
            try:
                import winsound

                winsound.Playaudio(os.environ["WINDIR"] + r"\media\Windows Ding.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

        elif Pythonista:
            try:
                import sound

                sound.stop_all_effects()
                sound.play_effect("game:Beep", pitch=0.3)
            except Exception:
                pass


class Animate2dBase(DynamicClass):
    def __init__(self, type, locals_, argument_default, attached_to=None, attach_text=True):
        super().__init__()
        self.type = type
        env = locals_["env"]
        arg = locals_["arg"]
        parent = locals_["parent"]
        if attached_to is None and parent is not None:
            if not isinstance(parent, Component):
                raise ValueError(repr(parent) + " is not a component")
            parent._animation_children.add(self)

        screen_coordinates = locals_["screen_coordinates"]
        over3d = locals_["over3d"]

        self.env = g.default_env if env is None else env
        self.sequence = self.env.serialize()
        self.arg = self if arg is None else arg
        self.over3d = _default_over3d if over3d is None else over3d
        self.screen_coordinates = screen_coordinates
        self.attached_to = attached_to
        if attached_to:
            for name in attached_to._dynamics:
                setattr(self, name, lambda arg, t, name=name: getattr(self.attached_to, name)(t))
                self.register_dynamic_attributes(name)

        else:
            for name, default in argument_default.items():
                if locals_[name] is None:
                    if not hasattr(self, name):
                        setattr(self, name, default)
                else:
                    setattr(self, name, locals_[name])
                self.register_dynamic_attributes(name)

        self._image_ident = None  # denotes no image yet
        self._image = None
        self._image_x = 0
        self._image_y = 0
        self.canvas_object = None

        if self.env._animate_debug:
            self.caller = self.env._frame_to_lineno(_get_caller_frame(), add_filename=True)
        else:
            self.caller = "?. use env.animate_debug(True) to get the originating Animate location"

        if attach_text:
            self.depending_object = Animate2dBase(type="text", locals_=locals_, argument_default={}, attached_to=self, attach_text=False)
        else:
            self.depending_object = None
        if not self.attached_to:
            self.show()

    def show(self):
        if self.depending_object:
            if self.over3d:
                self.env.an_objects_over3d.add(self.depending_object)
            else:
                self.env.an_objects.add(self.depending_object)
        if self.over3d:
            self.env.an_objects_over3d.add(self)
        else:
            self.env.an_objects.add(self)

    def remove(self):
        if self.depending_object:
            if self.over3d:
                self.env.an_objects_over3d.discard(self.depending_object)
            else:
                self.env.an_objects.discard(self.depending_object)
                self.canvas_object = None  # safety! even set for non tkinter

        if self.over3d:
            self.env.an_objects_over3d.discard(self)
        else:
            self.env.an_objects.discard(self)
            self.canvas_object = None  # safety! even set for non tkinter

    def is_removed(self):

        if self.over3d:
            return self not in self.env.an_over3d_objects
        else:
            return self not in self.env.an_objects

    def make_pil_image(self, t):  # new style
        try:
            if self.keep(t):
                visible = self.visible(t)
                if self.env._exclude_from_animation == visible:
                    visible = False
            else:
                self.remove()
                visible = False

            if visible:
                if self.type == "text":  # checked so early as to avoid evaluation of x, y, angle, ...
                    text = self.text(t)
                    if (text is None) or (text.strip() == ""):
                        self._image_visible = False
                        return

                self._image_ident_prev = self._image_ident

                self._image_x_prev = self._image_x
                self._image_y_prev = self._image_y

                x = self.x(t)
                y = self.y(t)
                xy_anchor = self.xy_anchor(t)
                if xy_anchor:
                    x += self.env.xy_anchor_to_x(xy_anchor, screen_coordinates=self.screen_coordinates, over3d=self.over3d)
                    y += self.env.xy_anchor_to_y(xy_anchor, screen_coordinates=self.screen_coordinates, over3d=self.over3d)

                offsetx = self.offsetx(t)
                offsety = self.offsety(t)
                if not self.screen_coordinates:
                    offsetx = offsetx * self.env._scale
                    offsety = offsety * self.env._scale

                angle = self.angle(t)

                if self.type in ("polygon", "rectangle", "line", "circle"):

                    if self.screen_coordinates:
                        linewidth = self.linewidth(t)
                    else:
                        linewidth = self.linewidth(t) * self.env._scale

                    linecolor = self.env.colorspec_to_tuple(self.linecolor(t))
                    fillcolor = self.env.colorspec_to_tuple(self.fillcolor(t))

                    cosa = math.cos(math.radians(angle))
                    sina = math.sin(math.radians(angle))

                    if self.screen_coordinates:
                        qx = x
                        qy = y
                    else:
                        qx = (x - self.env._x0) * self.env._scale
                        qy = (y - self.env._y0) * self.env._scale

                    if self.type == "rectangle":
                        as_points = self.as_points(t)

                        rectangle = tuple(de_none(self.spec(t)))
                        self._image_ident = (tuple(rectangle), linewidth, linecolor, fillcolor, as_points, angle, self.screen_coordinates)
                    elif self.type == "line":
                        as_points = self.as_points(t)
                        line = tuple(de_none(self.spec(t)))
                        fillcolor = (0, 0, 0, 0)
                        self._image_ident = (tuple(line), linewidth, linecolor, as_points, angle, self.screen_coordinates)
                    elif self.type == "polygon":
                        as_points = self.as_points(t)
                        polygon = tuple(de_none(self.spec(t)))
                        self._image_ident = (tuple(polygon), linewidth, linecolor, fillcolor, as_points, angle, self.screen_coordinates)
                    elif self.type == "circle":
                        as_points = False
                        radius0 = self.radius(t)
                        radius1 = self.radius1(t)
                        if radius1 is None:
                            radius1 = radius0
                        arc_angle0 = self.arc_angle0(t)
                        arc_angle1 = self.arc_angle1(t)
                        draw_arc = bool(self.draw_arc(t))

                        self._image_ident = (
                            radius0,
                            radius1,
                            arc_angle0,
                            arc_angle1,
                            draw_arc,
                            linewidth,
                            linecolor,
                            fillcolor,
                            angle,
                            self.screen_coordinates,
                        )

                    if self._image_ident != self._image_ident_prev:
                        if self.type == "rectangle":
                            p = [
                                rectangle[0],
                                rectangle[1],
                                rectangle[2],
                                rectangle[1],
                                rectangle[2],
                                rectangle[3],
                                rectangle[0],
                                rectangle[3],
                                rectangle[0],
                                rectangle[1],
                            ]

                        elif self.type == "line":
                            p = line

                        elif self.type == "polygon":
                            p = list(polygon)
                            if p[0:2] != p[-3:-1]:
                                p.append(p[0])  # close the polygon
                                p.append(p[1])

                        elif self.type == "circle":
                            if arc_angle0 > arc_angle1:
                                arc_angle0, arc_angle1 = arc_angle1, arc_angle0
                            arc_angle1 = min(arc_angle1, arc_angle0 + 360)

                            if self.screen_coordinates:
                                nsteps = int(math.sqrt(max(radius0, radius1)) * 6)
                            else:
                                nsteps = int(math.sqrt(max(radius0 * self.env._scale, radius1 * self.env._scale)) * 6)
                            tarc_angle = 360 / nsteps
                            p = [0, 0]

                            arc_angle = arc_angle0
                            ended = False
                            while True:
                                sint = math.sin(math.radians(arc_angle))
                                cost = math.cos(math.radians(arc_angle))
                                x, y = (radius0 * cost, radius1 * sint)
                                p.append(x)
                                p.append(y)
                                if ended:
                                    break
                                arc_angle += tarc_angle
                                if arc_angle >= arc_angle1:
                                    arc_angle = arc_angle1
                                    ended = True
                            p.append(0)
                            p.append(0)

                        r = []
                        minpx = inf
                        minpy = inf
                        maxpx = -inf
                        maxpy = -inf
                        minrx = inf
                        minry = inf
                        maxrx = -inf
                        maxry = -inf
                        for i in range(0, len(p), 2):
                            px = p[i]
                            py = p[i + 1]
                            if not self.screen_coordinates:
                                px *= self.env._scale
                                py *= self.env._scale
                            rx = px * cosa - py * sina
                            ry = px * sina + py * cosa
                            minpx = min(minpx, px)
                            maxpx = max(maxpx, px)
                            minpy = min(minpy, py)
                            maxpy = max(maxpy, py)
                            minrx = min(minrx, rx)
                            maxrx = max(maxrx, rx)
                            minry = min(minry, ry)
                            maxry = max(maxry, ry)
                            r.append(rx)
                            r.append(ry)
                        if maxrx == -inf:
                            maxpx = 0
                            minpx = 0
                            maxpy = 0
                            minpy = 0
                            maxrx = 0
                            minrx = 0
                            maxry = 0
                            minry = 0

                        rscaled = []
                        for i in range(0, len(r), 2):
                            rscaled.append(r[i] - minrx + linewidth)
                            rscaled.append(maxry - r[i + 1] + linewidth)
                        rscaled = tuple(rscaled)  # to make it hashable

                        if as_points:
                            self._image = Image.new("RGBA", (int(maxrx - minrx + 2 * linewidth), int(maxry - minry + 2 * linewidth)), (0, 0, 0, 0))
                            point_image = Image.new("RGBA", (int(linewidth), int(linewidth)), linecolor)

                            for i in range(0, len(r), 2):
                                rx = rscaled[i]
                                ry = rscaled[i + 1]
                                self._image.paste(point_image, (int(rx - 0.5 * linewidth), int(ry - 0.5 * linewidth)), point_image)

                        else:
                            self._image = Image.new("RGBA", (int(maxrx - minrx + 2 * linewidth), int(maxry - minry + 2 * linewidth)), (0, 0, 0, 0))
                            draw = ImageDraw.Draw(self._image)
                            if fillcolor[3] != 0:
                                draw.polygon(rscaled, fill=fillcolor)
                            if (round(linewidth) > 0) and (linecolor[3] != 0):
                                if self.type == "circle" and not draw_arc:
                                    draw.line(rscaled[2:-2], fill=linecolor, width=int(linewidth))
                                    # get rid of the first and last point (=center)
                                else:
                                    draw.line(rscaled, fill=linecolor, width=int(round(linewidth)))
                            del draw
                        self.minrx = minrx
                        self.minry = minry
                        self.maxrx = maxrx
                        self.maxry = maxry
                        self.minpx = minpx
                        self.minpy = minpy
                        self.maxpx = maxpx
                        self.maxpy = maxpy

                    if self.type == "circle":
                        self.env._centerx = qx
                        self.env._centery = qy
                        self.env._dimx = 2 * radius0
                        self.env._dimy = 2 * radius1
                    else:
                        self.env._centerx = qx + (self.minrx + self.maxrx) / 2
                        self.env._centery = qy + (self.minry + self.maxry) / 2
                        self.env._dimx = self.maxpx - self.minpx
                        self.env._dimy = self.maxpy - self.minpy

                    self._image_x = qx + self.minrx - linewidth + (offsetx * cosa - offsety * sina)
                    self._image_y = qy + self.minry - linewidth + (offsetx * sina + offsety * cosa)

                elif self.type == "image":
                    spec = self.image(t)
                    image = spec_to_image(spec)
                    width = self.width(t)
                    if width is None:
                        width = image.size[0]

                    height = width * image.size[1] / image.size[0]
                    if not self.screen_coordinates:
                        width *= self.env._scale
                        height *= self.env._scale

                    angle = self.angle(t)

                    anchor = self.anchor(t)
                    if self.screen_coordinates:
                        qx = x
                        qy = y
                    else:
                        qx = (x - self.env._x0) * self.env._scale
                        qy = (y - self.env._y0) * self.env._scale
                        offsetx = offsetx * self.env._scale
                        offsety = offsety * self.env._scale

                    alpha = int(self.alpha(t))
                    self._image_ident = (spec, width, height, angle, alpha)
                    if self._image_ident != self._image_ident_prev:
                        im1 = image.resize((int(width), int(height)), Image.ANTIALIAS)
                        self.imwidth, self.imheight = im1.size
                        if alpha != 255:
                            if has_numpy():
                                arr = numpy.asarray(im1).copy()
                                arr_alpha = arr[:, :, 3]
                                arr[:, :, 3] = arr_alpha * (alpha / 255)
                                im1 = Image.fromarray(numpy.uint8(arr))
                            else:
                                pix = im1.load()
                                for x in range(self.imwidth):
                                    for y in range(self.imheight):
                                        c = pix[x, y]
                                        pix[x, y] = (c[0], c[1], c[2], int(c[3] * alpha / 255))
                        self._image = im1.rotate(angle, expand=1)
                    anchor_to_dis = {
                        "ne": (-0.5, -0.5),
                        "n": (0, -0.5),
                        "nw": (0.5, -0.5),
                        "e": (-0.5, 0),
                        "center": (0, 0),
                        "c": (0, 0),
                        "w": (0.5, 0),
                        "se": (-0.5, 0.5),
                        "s": (0, 0.5),
                        "sw": (0.5, 0.5),
                    }
                    dx, dy = anchor_to_dis[anchor.lower()]
                    dx = dx * self.imwidth + offsetx
                    dy = dy * self.imheight + offsety
                    cosa = math.cos(math.radians(angle))
                    sina = math.sin(math.radians(angle))
                    ex = dx * cosa - dy * sina
                    ey = dx * sina + dy * cosa
                    imrwidth, imrheight = self._image.size

                    self.env._centerx = qx + ex
                    self.env._centery = qy + ey
                    self.env._dimx = width
                    self.env._dimy = height

                    self._image_x = qx + ex - imrwidth / 2
                    self._image_y = qy + ey - imrheight / 2

                elif self.type == "text":
                    # text contains self.text()
                    textcolor = self.env.colorspec_to_tuple(self.textcolor(t))
                    fontsize = self.fontsize(t)
                    angle = self.angle(t)
                    fontname = self.font(t)
                    if not self.screen_coordinates:
                        fontsize = fontsize * self.env._scale
                        offsetx = offsetx * self.env._scale
                        offsety = offsety * self.env._scale
                    text_anchor = self.text_anchor(t)

                    if self.attached_to:
                        text_offsetx = self.text_offsetx(t)
                        text_offsety = self.text_offsety(t)
                        if not self.screen_coordinates:
                            text_offsetx = text_offsetx * self.env._scale
                            text_offsety = text_offsety * self.env._scale
                        qx = self.env._centerx
                        qy = self.env._centery
                        anchor_to_dis = {
                            "ne": (0.5, 0.5),
                            "n": (0, 0.5),
                            "nw": (-0.5, 0.5),
                            "e": (0.5, 0),
                            "center": (0, 0),
                            "c": (0, 0),
                            "w": (-0.5, 0),
                            "se": (0.5, -0.5),
                            "s": (0, -0.5),
                            "sw": (-0.5, -0.5),
                        }
                        dis = anchor_to_dis[text_anchor.lower()]
                        offsetx += text_offsetx + dis[0] * self.env._dimx - dis[0] * 4  # 2 extra at east or west
                        offsety += text_offsety + dis[1] * self.env._dimy - (2 if dis[1] > 0 else 0)  # 2 extra at north
                    else:
                        if self.screen_coordinates:
                            qx = x
                            qy = y
                        else:
                            qx = (x - self.env._x0) * self.env._scale
                            qy = (y - self.env._y0) * self.env._scale
                    max_lines = self.max_lines(t)
                    self._image_ident = (text, fontname, fontsize, angle, textcolor, max_lines)
                    if self._image_ident != self._image_ident_prev:
                        font, heightA = getfont(fontname, fontsize)

                        lines = []
                        for item in deep_flatten(text):
                            for line in item.splitlines():
                                lines.append(line.rstrip())

                        if max_lines <= 0:  # 0 is all
                            lines = lines[max_lines:]
                        else:
                            lines = lines[:max_lines]

                        widths = [(font.getsize(line)[0] if line else 0) for line in lines]
                        if widths:
                            totwidth = max(widths)
                        else:
                            totwidth = 0
                        number_of_lines = len(lines)
                        lineheight = font.getsize("Ap")[1]
                        totheight = number_of_lines * lineheight
                        im = Image.new("RGBA", (int(totwidth + 0.1 * fontsize), int(totheight)), (0, 0, 0, 0))
                        imwidth, imheight = im.size
                        draw = ImageDraw.Draw(im)
                        pos = 0
                        for line, width in zip(lines, widths):
                            if line:
                                draw.text(xy=(0.1 * fontsize, pos), text=line, font=font, fill=textcolor)
                            pos += lineheight
                        # this code is to correct a bug in the rendering of text,
                        # leaving a kind of shadow around the text
                        del draw
                        if textcolor[:3] != (0, 0, 0):  # black is ok
                            if has_numpy():
                                arr = numpy.asarray(im).copy()
                                arr[:, :, 0] = textcolor[0]
                                arr[:, :, 1] = textcolor[1]
                                arr[:, :, 2] = textcolor[2]
                                im = Image.fromarray(numpy.uint8(arr))
                            else:
                                pix = im.load()
                                for y in range(imheight):
                                    for x in range(imwidth):
                                        pix[x, y] = (textcolor[0], textcolor[1], textcolor[2], pix[x, y][3])

                        # end of code to correct bug

                        self.imwidth, self.imheight = im.size
                        self.heightA = heightA

                        self._image = im.rotate(angle, expand=1)

                    anchor_to_dis = {
                        "ne": (-0.5, -0.5),
                        "n": (0, -0.5),
                        "nw": (0.5, -0.5),
                        "e": (-0.5, 0),
                        "center": (0, 0),
                        "c": (0, 0),
                        "w": (0.5, 0),
                        "se": (-0.5, 0.5),
                        "s": (0, 0.5),
                        "sw": (0.5, 0.5),
                    }
                    dx, dy = anchor_to_dis[text_anchor.lower()]
                    dx = dx * self.imwidth + offsetx - 0.1 * fontsize

                    dy = dy * self.imheight + offsety
                    cosa = math.cos(math.radians(angle))
                    sina = math.sin(math.radians(angle))
                    ex = dx * cosa - dy * sina
                    ey = dx * sina + dy * cosa
                    imrwidth, imrheight = self._image.size
                    self._image_x = qx + ex - imrwidth / 2
                    self._image_y = qy + ey - imrheight / 2
                else:
                    raise ValueError("Internal error: animate type" + self.type + "not recognized.")
                if self.over3d:
                    width = self.env._width3d
                    height = self.env._height3d
                else:
                    width = self.env._width
                    height = self.env._height

                self._image_visible = (
                    (self._image_x <= width)
                    and (self._image_y <= height)
                    and (self._image_x + self._image.size[0] >= 0)
                    and (self._image_y + self._image.size[1] >= 0)
                )
            else:
                self._image_visible = False
        except Exception as e:
            self.env._animate = False
            self.env.running = False
            traceback.print_exc()
            raise type(e)(str(e) + " [from " + self.type + " animation object created in line " + self.caller + "]") from e


class AnimateClassic(Animate2dBase):
    def __init__(self, master, locals_):
        super().__init__(locals_=locals_, type=master.type, argument_default={}, attach_text=False)
        self.master = master

    def text(self, t):
        return self.master.text(t)

    def x(self, t):
        return self.master.x(t)

    def y(self, t):
        return self.master.y(t)

    def layer(self, t):
        return self.master.layer(t)

    def visible(self, t):
        return self.master.visible(t)

    def keep(self, t):
        return self.master.keep(t)

    def xy_anchor(self, t):
        return self.master.xy_anchor(t)

    def offsetx(self, t):
        return self.master.offsetx(t)

    def offsety(self, t):
        return self.master.offsety(t)

    def angle(self, t):
        return self.master.angle(t)

    def textcolor(self, t):
        return self.master.textcolor(t)

    def text_anchor(self, t):
        return self.master.text_anchor(t)

    def fontsize(self, t):
        return self.master.fontsize(t)

    def font(self, t):
        return self.master.font0

    def max_lines(self, t):
        return self.master.max_lines(t)

    def image(self, t):
        return self.master.image(t)

    def width(self, t):
        return self.master.width(t)

    def anchor(self, t):
        return self.master.anchor(t)

    def alpha(self, t):
        return self.master.alpha(t)

    def linewidth(self, t):
        return self.master.linewidth(t)

    def linecolor(self, t):
        return self.master.linecolor(t)

    def fillcolor(self, t):
        return self.master.fillcolor(t)

    def as_points(self, t):
        return self.master.as_points(t)

    def spec(self, t):
        if self.type == "line":
            return self.master.line(t)
        if self.type == "rectangle":
            return self.master.rectangle(t)
        if self.type == "polygon":
            return self.master.polygon(t)

    def radius(self, t):
        circle = self.master.circle(t)
        try:
            return circle[0]
        except TypeError:
            return circle

    def radius1(self, t):
        circle = self.master.circle(t)
        try:
            return circle[1]
        except (TypeError, IndexError):
            return circle

    def arc_angle0(self, t):
        circle = self.master.circle(t)
        try:
            return circle[2]
        except (TypeError, IndexError):
            return 0

    def arc_angle1(self, t):
        circle = self.master.circle(t)
        try:
            return circle[3]
        except (TypeError, IndexError):
            return 360

    def draw_arc(self, t):
        circle = self.master.circle(t)
        try:
            return circle[4]
        except (TypeError, IndexError):
            return False


class Animate:
    """
    defines an animation object

    Parameters
    ----------
    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    layer : int
         layer value |n|
         lower layer values are on top of higher layer values (default 0)

    keep : bool
        keep |n|
        if False, animation object is hidden after t1, shown otherwise
        (default True)

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are use for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.

    xy_anchor : str
        specifies where x and y (i.e. x0, y0, x1 and y1) are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated

    t0 : float
        time of start of the animation (default: now)

    x0 : float
        x-coordinate of the origin at time t0 (default 0)

    y0 : float
        y-coordinate of the origin at time t0 (default 0)

    offsetx0 : float
        offsets the x-coordinate of the object at time t0 (default 0)

    offsety0 : float
        offsets the y-coordinate of the object at time t0 (default 0)

    circle0 : float or tuple/list
         the circle spec of the circle at time t0 |n|
         - radius |n|
         - one item tuple/list containing the radius |n|
         - five items tuple/list cntaining radius, radius1, arc_angle0, arc_angle1 and draw_arc
         (see class AnimateCircle for details)

    line0 : tuple
        the line(s) (xa,ya,xb,yb,xc,yc, ...) at time t0

    polygon0 : tuple
        the polygon (xa,ya,xb,yb,xc,yc, ...) at time t0 |n|
        the last point will be auto connected to the start

    rectangle0 : tuple
        the rectangle (xlowerleft,ylowerleft,xupperright,yupperright) at time t0 |n|

    image : str, pathlib.Path or PIL image
        the image to be displayed |n|
        This may be either a filename or a PIL image

    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the first -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    anchor : str
        anchor position |n|
        specifies where to put images or texts relative to the anchor
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    as_points : bool
         if False (default), lines in line, rectangle and polygon are drawn |n|
         if True, only the end points are shown in line, rectangle and polygon

    linewidth0 : float
        linewidth of the contour at time t0 (default 0 for polygon, rectangle and circle, 1 for line) |n|
        if as_point is True, the default size is 3

    fillcolor0 : colorspec
        color of interior at time t0 (default foreground_color) |n|
        if as_points is True, fillcolor0 defaults to transparent

    linecolor0 : colorspec
        color of the contour at time t0 (default foreground_color)

    textcolor0 : colorspec
        color of the text at time 0 (default foreground_color)

    angle0 : float
        angle of the polygon at time t0 (in degrees) (default 0)

    alpha0 : float
        alpha of the image at time t0 (0-255) (default 255)

    fontsize0 : float
        fontsize of text at time t0 (default 20)

    width0 : float
       width of the image to be displayed at time t0 |n|
       if omitted or None, no scaling

    t1 : float
        time of end of the animation (default inf) |n|
        if keep=True, the animation will continue (frozen) after t1

    x1 : float
        x-coordinate of the origin at time t1(default x0)

    y1 : float
        y-coordinate of the origin at time t1 (default y0)

    offsetx1 : float
        offsets the x-coordinate of the object at time t1 (default offsetx0)

    offsety1 : float
        offsets the y-coordinate of the object at time t1 (default offsety0)

    circle1 : float or tuple/list
         the circle spec of the circle at time t1 (default: circle0) |n|
         - radius |n|
         - one item tuple/list containing the radius |n|
         - five items tuple/list cntaining radius, radius1, arc_angle0, arc_angle1 and draw_arc
         (see class AnimateCircle for details)

    line1 : tuple
        the line(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: line0) |n|
        should have the same number of elements as line0

    polygon1 : tuple
        the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: polygon0) |n|
        should have the same number of elements as polygon0

    rectangle1 : tuple
        the rectangle (xlowerleft,ylowerleft,xupperright,yupperright) at time t1
        (default: rectangle0)

    linewidth1 : float
        linewidth of the contour at time t1 (default linewidth0)

    fillcolor1 : colorspec
        color of interior at time t1 (default fillcolor0)

    linecolor1 : colorspec
        color of the contour at time t1 (default linecolor0)

    textcolor1 : colorspec
        color of text at time t1 (default textcolor0)

    angle1 : float
        angle of the polygon at time t1 (in degrees) (default angle0)

    alpha1 : float
        alpha of the image at time t1 (0-255) (default alpha0)

    fontsize1 : float
        fontsize of text at time t1 (default: fontsize0)

    width1 : float
       width of the image to be displayed at time t1 (default: width0) |n|

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    Note
    ----
    one (and only one) of the following parameters is required:
         - circle0
         - image
         - line0
         - polygon0
         - rectangle0
         - text

    colors may be specified as a
        - valid colorname
        - hexname
        - tuple (R,G,B) or (R,G,B,A)
        - "fg" or "bg"

    colornames may contain an additional alpha, like ``red#7f`` |n|
    hexnames may be either 3 of 4 bytes long (``#rrggbb`` or ``#rrggbbaa``) |n|
    both colornames and hexnames may be given as a tuple with an
    additional alpha between 0 and 255,
    e.g. ``(255,0,255,128)``, ("red",127)`` or ``("#ff00ff",128)`` |n|
    fg is the foreground color |n|
    bg is the background color |n|

    Permitted parameters

    ======================  ========= ========= ========= ========= ========= =========
    parameter               circle    image     line      polygon   rectangle text
    ======================  ========= ========= ========= ========= ========= =========
    parent                  -         -         -         -         -         -
    layer                   -         -         -         -         -         -
    keep                    -         -         -         -         -         -
    screen_coordinates      -         -         -         -         -         -
    xy_anchor               -         -         -         -         -         -
    t0,t1                   -         -         -         -         -         -
    x0,x1                   -         -         -         -         -         -
    y0,y1                   -         -         -         -         -         -
    offsetx0,offsetx1       -         -         -         -         -         -
    offsety0,offsety1       -         -         -         -         -         -
    circle0,circle1         -
    image                             -
    line0,line1                                 -
    polygon0,polygon1                                     -
    rectangle0,rectangle1                                           -
    text                                                                      -
    anchor                            -                                       -
    linewidth0,linewidth1    -                  -         -         -
    fillcolor0,fillcolor1    -                            -         -
    linecolor0,linecolor1    -                  -         -         -
    textcolor0,textcolor1                                                     -
    angle0,angle1                     -         -         -         -         -
    alpha0,alpha1                     -
    as_points                                   -         -         -
    font                                                                      -
    fontsize0,fontsize1                                                       -
    width0,width1                     -
    ======================  ========= ========= ========= ========= ========= =========
    """

    def __init__(
        self,
        parent=None,
        layer=0,
        keep=True,
        visible=True,
        screen_coordinates=None,
        t0=None,
        x0=0,
        y0=0,
        offsetx0=0,
        offsety0=0,
        circle0=None,
        line0=None,
        polygon0=None,
        rectangle0=None,
        points0=None,
        image=None,
        text=None,
        font="",
        anchor="c",
        as_points=False,
        max_lines=0,
        text_anchor=None,
        linewidth0=None,
        fillcolor0=None,
        linecolor0="fg",
        textcolor0="fg",
        angle0=0,
        alpha0=255,
        fontsize0=20,
        width0=None,
        t1=None,
        x1=None,
        y1=None,
        offsetx1=None,
        offsety1=None,
        circle1=None,
        line1=None,
        polygon1=None,
        rectangle1=None,
        points1=None,
        linewidth1=None,
        fillcolor1=None,
        linecolor1=None,
        textcolor1=None,
        angle1=None,
        alpha1=None,
        fontsize1=None,
        width1=None,
        xy_anchor="",
        over3d=None,
        env=None,
    ):

        self.env = g.default_env if env is None else env
        self._image_ident = None  # denotes no image yet
        self._image = None
        self._image_x = 0
        self._image_y = 0
        self.canvas_object = None
        self.over3d = _default_over3d if over3d is None else over3d
        self.screen_coordinates = screen_coordinates

        self.type = self.settype(circle0, line0, polygon0, rectangle0, points0, image, text)
        if self.type == "":
            raise ValueError("no object specified")
        type1 = self.settype(circle1, line1, polygon1, rectangle1, points1, None, None)
        if (type1 != "") and (type1 != self.type):
            raise TypeError("incompatible types: " + self.type + " and " + type1)

        self.layer0 = layer
        if parent is not None:
            if not isinstance(parent, Component):
                raise ValueError(repr(parent) + " is not a component")
            parent._animation_children.add(self)
        self.keep0 = keep
        self.visible0 = visible
        self.screen_coordinates = screen_coordinates
        self.sequence = self.env.serialize()

        self.circle0 = circle0
        self.line0 = de_none(line0)
        self.polygon0 = de_none(polygon0)
        self.rectangle0 = de_none(rectangle0)
        self.points0 = de_none(points0)
        self.text0 = text

        if image is None:
            self.width0 = 0  # just to be able to interpolate
        else:
            self.image0 = image
            self.width0 = width0  # None means original size

        self.as_points0 = as_points
        self.font0 = font
        self.max_lines0 = max_lines
        self.anchor0 = anchor
        if self.type == "text":
            if text_anchor is None:
                self.text_anchor0 = self.anchor0
            else:
                self.text_anchor0 = text_anchor
        self.anchor0 = anchor
        self.xy_anchor0 = xy_anchor

        self.x0 = x0
        self.y0 = y0
        self.offsetx0 = offsetx0
        self.offsety0 = offsety0

        if fillcolor0 is None:
            if self.as_points0:
                self.fillcolor0 = ""
            else:
                self.fillcolor0 = "fg"
        else:
            self.fillcolor0 = fillcolor0
        self.linecolor0 = linecolor0
        self.textcolor0 = textcolor0
        if linewidth0 is None:
            if self.as_points0:
                self.linewidth0 = 3
            else:
                if self.type == "line":
                    self.linewidth0 = 1
                else:
                    self.linewidth0 = 0
        else:
            self.linewidth0 = linewidth0
        self.angle0 = angle0
        self.alpha0 = alpha0
        self.fontsize0 = fontsize0

        self.t0 = self.env._now if t0 is None else t0

        self.circle1 = self.circle0 if circle1 is None else circle1
        self.line1 = self.line0 if line1 is None else de_none(line1)
        self.polygon1 = self.polygon0 if polygon1 is None else de_none(polygon1)
        self.rectangle1 = self.rectangle0 if rectangle1 is None else de_none(rectangle1)
        self.points1 = self.points0 if points1 is None else de_none(points1)

        self.x1 = self.x0 if x1 is None else x1
        self.y1 = self.y0 if y1 is None else y1
        self.offsetx1 = self.offsetx0 if offsetx1 is None else offsetx1
        self.offsety1 = self.offsety0 if offsety1 is None else offsety1
        self.fillcolor1 = self.fillcolor0 if fillcolor1 is None else fillcolor1
        self.linecolor1 = self.linecolor0 if linecolor1 is None else linecolor1
        self.textcolor1 = self.textcolor0 if textcolor1 is None else textcolor1
        self.linewidth1 = self.linewidth0 if linewidth1 is None else linewidth1
        self.angle1 = self.angle0 if angle1 is None else angle1
        self.alpha1 = self.alpha0 if alpha1 is None else alpha1
        self.fontsize1 = self.fontsize0 if fontsize1 is None else fontsize1
        self.width1 = self.width0 if width1 is None else width1

        self.t1 = inf if t1 is None else t1
        if self.env._animate_debug:
            self.caller = self.env._frame_to_lineno(_get_caller_frame(), add_filename=True)
        else:
            self.caller = "?. use env.animate_debug(True) to get the originating Animate location"
        """
        if over3d:
            self.env.an_objects_over3d.append(self)
        else:
            self.env.an_objects.append(self)
        """

        arg = None  # just to make Animate2dBase happy

        self.animation_object = AnimateClassic(master=self, locals_=locals())

    def update(
        self,
        layer=None,
        keep=None,
        visible=None,
        t0=None,
        x0=None,
        y0=None,
        offsetx0=None,
        offsety0=None,
        circle0=None,
        line0=None,
        polygon0=None,
        rectangle0=None,
        points0=None,
        image=None,
        text=None,
        font=None,
        anchor=None,
        xy_anchor0=None,
        max_lines=None,
        text_anchor=None,
        linewidth0=None,
        fillcolor0=None,
        linecolor0=None,
        textcolor0=None,
        angle0=None,
        alpha0=None,
        fontsize0=None,
        width0=None,
        xy_anchor1=None,
        as_points=None,
        t1=None,
        x1=None,
        y1=None,
        offsetx1=None,
        offsety1=None,
        circle1=None,
        line1=None,
        polygon1=None,
        rectangle1=None,
        points1=None,
        linewidth1=None,
        fillcolor1=None,
        linecolor1=None,
        textcolor1=None,
        angle1=None,
        alpha1=None,
        fontsize1=None,
        width1=None,
    ):
        """
        updates an animation object

        Parameters
        ----------
        layer : int
            layer value |n|
            lower layer values are on top of higher layer values (default see below)

        keep : bool
            keep |n|
            if False, animation object is hidden after t1, shown otherwise
            (default see below)

        visible : bool
            visible |n|
            if False, animation object is not shown, shown otherwise
            (default see below)

        xy_anchor : str
            specifies where x and y (i.e. x0, y0, x1 and y1) are relative to |n|
            possible values are: |n|
            ``nw    n    ne`` |n|
            ``w     c     e`` |n|
            ``sw    s    se`` |n|
            If null string, the given coordimates are used untranslated |n|
            default see below

        t0 : float
            time of start of the animation (default: now)

        x0 : float
            x-coordinate of the origin at time t0 (default see below)

        y0 : float
            y-coordinate of the origin at time t0 (default see below)

        offsetx0 : float
            offsets the x-coordinate of the object at time t0 (default see below)

        offsety0 : float
            offsets the y-coordinate of the object at time t0 (default see below)

        circle0 : float or tuple/list
            the circle spec of the circle at time t0 |n|
            - radius |n|
            - one item tuple/list containing the radius |n|
            - five items tuple/list cntaining radius, radius1, arc_angle0, arc_angle1 and draw_arc
            (see class AnimateCircle for details)

        line0 : tuple
            the line(s) at time t0 (xa,ya,xb,yb,xc,yc, ...) (default see below)

        polygon0 : tuple
            the polygon at time t0 (xa,ya,xb,yb,xc,yc, ...) |n|
            the last point will be auto connected to the start (default see below)

        rectangle0 : tuple
            the rectangle at time t0 |n|
            (xlowerleft,ylowerlef,xupperright,yupperright) (default see below)

        points0 : tuple
            the points(s) at time t0 (xa,ya,xb,yb,xc,yc, ...) (default see below)

        image : str or PIL image
            the image to be displayed |n|
            This may be either a filename or a PIL image (default see below)

        text : str
            the text to be displayed (default see below)

        font : str or list/tuple
            font to be used for texts |n|
            Either a string or a list/tuple of fontnames. (default see below)
            If not found, uses calibri or arial

        max_lines : int
            the maximum of lines of text to be displayed |n|
            if positive, it refers to the first max_lines lines |n|
            if negative, it refers to the first -max_lines lines |n|
            if zero (default), all lines will be displayed

        anchor : str
            anchor position |n|
            specifies where to put images or texts relative to the anchor
            point (default see below) |n|
            possible values are (default: c): |n|
            ``nw    n    ne`` |n|
            ``w     c     e`` |n|
            ``sw    s    se``

        linewidth0 : float
            linewidth of the contour at time t0 (default see below)

        fillcolor0 : colorspec
            color of interior/text at time t0 (default see below)

        linecolor0 : colorspec
            color of the contour at time t0 (default see below)

        angle0 : float
            angle of the polygon at time t0 (in degrees) (default see below)

        fontsize0 : float
            fontsize of text at time t0 (default see below)

        width0 : float
            width of the image to be displayed at time t0 (default see below) |n|
            if None, the original width of the image will be used

        t1 : float
            time of end of the animation (default: inf) |n|
            if keep=True, the animation will continue (frozen) after t1

        x1 : float
            x-coordinate of the origin at time t1 (default x0)

        y1 : float
            y-coordinate of the origin at time t1 (default y0)

        offsetx1 : float
            offsets the x-coordinate of the object at time t1 (default offsetx0)

        offsety1 : float
            offsets the y-coordinate of the object at time t1 (default offset0)

        circle1 : float or tuple/ist
            the circle spec of the circle at time t1 |n|
            - radius |n|
            - one item tuple/list containing the radius |n|
            - five items tuple/list cntaining radius, radius1, arc_angle0, arc_angle1 and draw_arc
            (see class AnimateCircle for details)

        line1 : tuple
            the line(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: line0) |n|
            should have the same number of elements as line0

        polygon1 : tuple
            the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: polygon0) |n|
            should have the same number of elements as polygon0

        rectangle1 : tuple
            the rectangle at time t (xlowerleft,ylowerleft,xupperright,yupperright)
            (default: rectangle0) |n|

        points1 : tuple
            the points(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: points0) |n|
            should have the same number of elements as points1

        linewidth1 : float
            linewidth of the contour at time t1 (default linewidth0)

        fillcolor1 : colorspec
            color of interior/text at time t1 (default fillcolor0)

        linecolor1 : colorspec
            color of the contour at time t1 (default linecolor0)

        angle1 : float
            angle of the polygon at time t1 (in degrees) (default angle0)

        fontsize1 : float
            fontsize of text at time t1 (default: fontsize0)

        width1 : float
           width of the image to be displayed at time t1 (default: width0) |n|

        Note
        ----
        The type of the animation cannot be changed with this method. |n|
        The default value of most of the parameters is the current value (at time now)
        """

        t = self.env._now
        type0 = self.settype(circle0, line0, polygon0, rectangle0, points0, image, text)
        if (type0 != "") and (type0 != self.type):
            raise TypeError("incorrect type " + type0 + " (should be " + self.type)
        type1 = self.settype(circle1, line1, polygon1, rectangle1, points1, None, None)
        if (type1 != "") and (type1 != self.type):
            raise TypeError("incompatible types: " + self.type + " and " + type1)

        if layer is not None:
            self.layer0 = layer
        if keep is not None:
            self.keep0 = keep
        if visible is not None:
            self.visible0 = visible
        self.circle0 = self.circle() if circle0 is None else circle0
        self.line0 = self.line() if line0 is None else de_none(line0)
        self.polygon0 = self.polygon() if polygon0 is None else de_none(polygon0)
        self.rectangle0 = self.rectangle() if rectangle0 is None else de_none(rectangle0)
        self.points0 = self.points() if points0 is None else de_none(points0)
        if as_points is not None:
            self.as_points0 = as_points
        if text is not None:
            self.text0 = text
        if max_lines is not None:
            self.max_lines0 = max_lines

        self.width0 = self.width() if width0 is None else width0
        if image is not None:
            self.image0 = image

        if font is not None:
            self.font0 = font
        if anchor is not None:
            self.anchor0 = anchor
            if self.type == "text":
                if text_anchor is not None:
                    self.text_anchor0 = text_anchor
        if text_anchor is not None:
            self.text_anchor0 = text_anchor

        self.x0 = self.x(t) if x0 is None else x0
        self.y0 = self.y(t) if y0 is None else y0
        self.offsetx0 = self.offsetx(t) if offsetx0 is None else offsetx0
        self.offsety0 = self.offsety(t) if offsety0 is None else offsety0

        self.fillcolor0 = self.fillcolor(t) if fillcolor0 is None else fillcolor0
        self.linecolor0 = self.linecolor(t) if linecolor0 is None else linecolor0
        self.textcolor0 = self.textcolor(t) if textcolor0 is None else textcolor0
        self.linewidth0 = self.linewidth(t) if linewidth0 is None else linewidth0
        self.angle0 = self.angle(t) if angle0 is None else angle0
        self.alpha0 = self.alpha(t) if alpha0 is None else alpha0
        self.fontsize0 = self.fontsize(t) if fontsize0 is None else fontsize0
        self.t0 = self.env._now if t0 is None else t0
        self.xy_anchor0 = self.xy_anchor(t) if xy_anchor0 is None else xy_anchor0

        self.circle1 = self.circle0 if circle1 is None else circle1
        self.line1 = self.line0 if line1 is None else de_none(line1)
        self.polygon1 = self.polygon0 if polygon1 is None else de_none(polygon1)
        self.rectangle1 = self.rectangle0 if rectangle1 is None else de_none(rectangle1)
        self.points1 = self.points0 if points1 is None else de_none(points1)

        self.x1 = self.x0 if x1 is None else x1
        self.y1 = self.y0 if y1 is None else y1
        self.offsetx1 = self.offsetx0 if offsetx1 is None else offsetx1
        self.offsety1 = self.offsety0 if offsety1 is None else offsety1
        self.fillcolor1 = self.fillcolor0 if fillcolor1 is None else fillcolor1
        self.linecolor1 = self.linecolor0 if linecolor1 is None else linecolor1
        self.textcolor1 = self.textcolor0 if textcolor1 is None else textcolor1
        self.linewidth1 = self.linewidth0 if linewidth1 is None else linewidth1
        self.angle1 = self.angle0 if angle1 is None else angle1
        self.alpha1 = self.alpha0 if alpha1 is None else alpha1
        self.fontsize1 = self.fontsize0 if fontsize1 is None else fontsize1
        self.width1 = self.width0 if width1 is None else width1
        self.xy_anchor1 = self.xy_anchor0 if xy_anchor1 is None else xy_anchor1

        self.t1 = inf if t1 is None else t1

    def show(self):
        self.animation_object.show()

    def remove(self):
        """
        removes the animation object from the animation queue,
        so effectively ending this animation.

        Note
        ----
        The animation object might be still updated, if required
        """
        self.animation_object.remove()

    def is_removed(self):
        return self.animation_object.is_removed()

    def x(self, t=None):
        """
        x-position of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        x : float
            default behaviour: linear interpolation between self.x0 and self.x1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.x0, self.x1)

    def y(self, t=None):
        """
        y-position of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        y : float
            default behaviour: linear interpolation between self.y0 and self.y1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.y0, self.y1)

    def offsetx(self, t=None):
        """
        offsetx of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        offsetx : float
            default behaviour: linear interpolation between self.offsetx0 and self.offsetx1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.offsetx0, self.offsetx1)

    def offsety(self, t=None):
        """
        offsety of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        offsety : float
            default behaviour: linear interpolation between self.offsety0 and self.offsety1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.offsety0, self.offsety1)

    def angle(self, t=None):
        """
        angle of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        angle : float
            default behaviour: linear interpolation between self.angle0 and self.angle1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.angle0, self.angle1)

    def alpha(self, t=None):
        """
        alpha of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        alpha : float
            default behaviour: linear interpolation between self.alpha0 and self.alpha1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.alpha0, self.alpha1)

    def linewidth(self, t=None):
        """
        linewidth of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        linewidth : float
            default behaviour: linear interpolation between self.linewidth0 and self.linewidth1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.linewidth0, self.linewidth1)

    def linecolor(self, t=None):
        """
        linecolor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        linecolor : colorspec
            default behaviour: linear interpolation between self.linecolor0 and self.linecolor1
        """
        return self.env.colorinterpolate((self.env._now if t is None else t), self.t0, self.t1, self.linecolor0, self.linecolor1)

    def fillcolor(self, t=None):
        """
        fillcolor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        fillcolor : colorspec
            default behaviour: linear interpolation between self.fillcolor0 and self.fillcolor1
        """
        return self.env.colorinterpolate((self.env._now if t is None else t), self.t0, self.t1, self.fillcolor0, self.fillcolor1)

    def circle(self, t=None):
        """
        circle of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        circle : float or tuple/list
            either |n|
            - radius |n|
            - one item tuple/list containing the radius |n|
            - five items tuple/list cntaining radius, radius1, arc_angle0, arc_angle1 and draw_arc |n|
            (see class AnimateCircle for details) |n|
            default behaviour: linear interpolation between self.circle0 and self.circle1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.circle0, self.circle1)

    def textcolor(self, t=None):
        """
        textcolor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        textcolor : colorspec
            default behaviour: linear interpolation between self.textcolor0 and self.textcolor1
        """
        return self.env.colorinterpolate((self.env._now if t is None else t), self.t0, self.t1, self.textcolor0, self.textcolor1)

    def line(self, t=None):
        """
        line of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        line : tuple
            series of x- and y-coordinates (xa,ya,xb,yb,xc,yc, ...) |n|
            default behaviour: linear interpolation between self.line0 and self.line1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.line0, self.line1)

    def polygon(self, t=None):
        """
        polygon of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        polygon: tuple
            series of x- and y-coordinates describing the polygon (xa,ya,xb,yb,xc,yc, ...) |n|
            default behaviour: linear interpolation between self.polygon0 and self.polygon1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.polygon0, self.polygon1)

    def rectangle(self, t=None):
        """
        rectangle of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        rectangle: tuple
            (xlowerleft,ylowerlef,xupperright,yupperright) |n|
            default behaviour: linear interpolation between self.rectangle0 and self.rectangle1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.rectangle0, self.rectangle1)

    def points(self, t=None):
        """
        points of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        points : tuple
            series of x- and y-coordinates (xa,ya,xb,yb,xc,yc, ...) |n|
            default behaviour: linear interpolation between self.points0 and self.points1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.points0, self.points1)

    def width(self, t=None):
        """
        width position of an animated image object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        width : float
            default behaviour: linear interpolation between self.width0 and self.width1 |n|
            if None, the original width of the image will be used
        """
        width0 = self.width0
        width1 = self.width1
        if width0 is None and width1 is None:
            return None
        if width0 is None:
            width0 = spec_to_image_width(self.image0)
        if width1 is None:
            width1 = spec_to_image_width(self.image0)

        return interpolate((self.env._now if t is None else t), self.t0, self.t1, width0, width1)

    def fontsize(self, t=None):
        """
        fontsize of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        fontsize : float
            default behaviour: linear interpolation between self.fontsize0 and self.fontsize1
        """
        return interpolate((self.env._now if t is None else t), self.t0, self.t1, self.fontsize0, self.fontsize1)

    def as_points(self, t=None):
        """
        as_points of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        as_points : bool
            default behaviour: self.as_points (text given at creation or update)
        """
        return self.as_points0

    def text(self, t=None):
        """
        text of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        text : str
            default behaviour: self.text0 (text given at creation or update)
        """
        return self.text0

    def max_lines(self, t=None):
        """
        maximum number of lines to be displayed of text. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        max_lines : int
            default behaviour: self.max_lines0 (max_lines given at creation or update)
        """
        return self.max_lines0

    def anchor(self, t=None):
        """
        anchor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        anchor : str
            default behaviour: self.anchor0 (anchor given at creation or update)
        """

        return self.anchor0

    def text_anchor(self, t=None):
        """
        text_anchor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        text_anchor : str
            default behaviour: self.text_anchor0 (text_anchor given at creation or update)
        """

        return self.text_anchor0

    def layer(self, t=None):
        """
        layer of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        layer : int or float
            default behaviour: self.layer0 (layer given at creation or update)
        """
        return self.layer0

    def font(self, t=None):
        """
        font of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        font : str
            default behaviour: self.font0 (font given at creation or update)
        """
        return self.font0

    def xy_anchor(self, t=None):
        """
        xy_anchor attribute of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        xy_anchor : str
            default behaviour: self.xy_anchor0 (xy_anchor given at creation or update)
        """
        return self.xy_anchor0

    def visible(self, t=None):
        """
        visible attribute of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        visible : bool
            default behaviour: self.visible0 and t >= self.t0 (visible given at creation or update)
        """
        return self.visible0 and t >= self.t0

    def keep(self, t):
        """
        keep attribute of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        keep : bool
            default behaviour: self.keep0 or t <= self.t1 (visible given at creation or update)
        """
        return self.keep0 or t <= self.t1

    def image(self, t=None):
        """
        image of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        image : PIL.Image.Image
            use function spec_to_image to load a file
            default behaviour: self.image0 (image given at creation or update)
        """
        return self.image0

    def settype(self, circle, line, polygon, rectangle, points, image, text):
        n = 0
        t = ""
        if circle is not None:
            t = "circle"
            n += 1
        if line is not None:
            t = "line"
            n += 1
        if polygon is not None:
            t = "polygon"
            n += 1
        if rectangle is not None:
            t = "rectangle"
            n += 1
        if points is not None:
            t = "points"
            n += 1
        if image is not None:
            t = "image"
            n += 1
        if text is not None:
            t = "text"
            n += 1
        if n >= 2:
            raise ValueError("more than one object given")
        return t

    def remove_background(self, im):
        pixels = im.load()
        background = pixels[0, 0]
        imagewidth, imageheight = im.size
        for y in range(imageheight):
            for x in range(imagewidth):
                if abs(pixels[x, y][0] - background[0]) < 10:
                    if abs(pixels[x, y][1] - background[1]) < 10:
                        if abs(pixels[x, y][2] - background[2]) < 10:
                            pixels[x, y] = (255, 255, 255, 0)


class AnimateEntry:
    """
    defines a button

    Parameters
    ----------
    x : int
        x-coordinate of centre of the button in screen coordinates (default 0)

    y : int
        y-coordinate of centre of the button in screen coordinates (default 0)

    number_of_chars : int
        number of characters displayed in the entry field (default 20)

    fillcolor : colorspec
        color of the entry background (default foreground_color)

    color : colorspec
        color of the text (default background_color)

    value : str
        initial value of the text of the entry (default null string) |n|

    action :  function
        action to take when the Enter-key is pressed |n|
        the function should have no arguments |n|

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All measures are in screen coordinates |n|
    This class is not available under Pythonista.
    """

    def __init__(self, x=0, y=0, number_of_chars=20, value="", fillcolor="fg", color="bg", text="", action=None, env=None, xy_anchor="sw"):
        self.env = g.default_env if env is None else env
        self.env.ui_objects.append(self)
        self.type = "entry"
        self.value = value
        self.sequence = self.env.serialize()
        self.x = x
        self.y = y
        self.number_of_chars = number_of_chars
        self.fillcolor = self.env.colorspec_to_tuple(fillcolor)
        self.color = self.env.colorspec_to_tuple(color)
        self.action = action
        self.xy_anchor = xy_anchor
        self.installed = False

    def install(self):
        x = self.x + self.env.xy_anchor_to_x(self.xy_anchor, screen_coordinates=True)
        y = self.y + self.env.xy_anchor_to_y(self.xy_anchor, screen_coordinates=True)

        self.entry = tkinter.Entry(self.env.root)
        self.entry.configure(
            width=self.number_of_chars,
            foreground=self.env.colorspec_to_hex(self.color, False),
            background=self.env.colorspec_to_hex(self.fillcolor, False),
            relief=tkinter.FLAT,
        )
        self.entry.bind("<Return>", self.on_enter)
        self.entry_window = g.canvas.create_window(x, self.env._height - y, anchor=tkinter.SW, window=self.entry)
        self.entry.insert(0, self.value)
        self.installed = True

    def on_enter(self, ev):
        if self.action is not None:
            self.action()

    def get(self):
        """
        get the current value of the entry

        Returns
        -------
        Current value of the entry : str
        """
        return self.entry.get()

    def remove(self):
        """
        removes the entry object. |n|
        the ui object is removed from the ui queue,
        so effectively ending this ui
        """
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if self.installed:
            self.entry.destroy()
            self.installed = False


class AnimateButton:
    """
    defines a button

    Parameters
    ----------
    x : int
        x-coordinate of centre of the button in screen coordinates (default 0)

    y : int
        y-coordinate of centre of the button in screen coordinates (default 0)

    width : int
        width of button in screen coordinates (default 80)

    height : int
        height of button in screen coordinates (default 30)

    linewidth : int
        width of contour in screen coordinates (default 0=no contour)

    fillcolor : colorspec
        color of the interior (foreground_color)

    linecolor : colorspec
        color of contour (default foreground_color)

    color : colorspec
        color of the text (default background_color)

    text : str or function
        text of the button (default null string) |n|
        if text is an argumentless function, this will be called each time;
        the button is shown/updated

    font : str
        font of the text (default Helvetica)

    fontsize : int
        fontsize of the text (default 15)

    action :  function
        action to take when button is pressed |n|
        executed when the button is pressed (default None)
        the function should have no arguments |n|

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All measures are in screen coordinates |n|
    On Pythonista, this functionality is emulated by salabim
    On other platforms, the tkinter functionality is used.
    """

    def __init__(self, x=0, y=0, width=80, fillcolor="fg", color="bg", text="", font="", fontsize=15, action=None, env=None, xy_anchor="sw"):

        self.env = g.default_env if env is None else env
        self.type = "button"
        self.t0 = -inf
        self.t1 = inf
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.sequence = self.env.serialize()
        self.height = 30
        self.x = x - width / 2
        self.y = y - self.height / 2
        self.width = width
        self.fillcolor = self.env.colorspec_to_tuple(fillcolor)
        self.linecolor = self.env.colorspec_to_tuple("fg")
        self.color = self.env.colorspec_to_tuple(color)
        self.linewidth = 0
        self.font = font
        self.fontsize = fontsize
        self.text0 = text
        self.lasttext = "*"
        self.action = action
        self.xy_anchor = xy_anchor

        self.env.ui_objects.append(self)
        self.installed = False

    def text(self):
        return self.text0

    def install(self):
        if not Pythonista:
            x = self.x + self.env.xy_anchor_to_x(self.xy_anchor, screen_coordinates=True)
            y = self.y + self.env.xy_anchor_to_y(self.xy_anchor, screen_coordinates=True)
            if Chromebook:  # the Chromebook settings are not accurate for anything else than the menu buttons
                my_font = tkinter.font.Font(size=int(self.fontsize * 0.45))
                my_width = int(0.6 * self.width / self.fontsize)
                y = y + 8
            else:
                my_font = tkinter.font.Font(size=int(self.fontsize * 0.7))
                my_width = int(1.85 * self.width / self.fontsize)

            self.button = tkinter.Button(self.env.root, text=self.lasttext, command=self.action, anchor=tkinter.CENTER)
            self.button.configure(
                font=my_font,
                width=my_width,
                foreground=self.env.colorspec_to_hex(self.color, False),
                background=self.env.colorspec_to_hex(self.fillcolor, False),
                relief=tkinter.FLAT,
            )
            self.button_window = g.canvas.create_window(x + self.width, self.env._height - y - self.height, anchor=tkinter.NE, window=self.button)
        self.installed = True

    def remove(self):
        """
        removes the button object. |n|
        the ui object is removed from the ui queue,
        so effectively ending this ui
        """
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if self.installed:
            if not Pythonista:
                self.button.destroy()
            self.installed = False


class AnimateSlider:
    """
    defines a slider

    Parameters
    ----------
    x : int
        x-coordinate of centre of the slider in screen coordinates (default 0)

    y : int
        y-coordinate of centre of the slider in screen coordinates (default 0)

    vmin : float
        minimum value of the slider (default 0)

    vmax : float
        maximum value of the slider (default 0)

    v : float
        initial value of the slider (default 0) |n|
        should be between vmin and vmax

    resolution : float
        step size of value (default 1)

    width : float
        width of slider in screen coordinates (default 100)

    height : float
        height of slider in screen coordinates (default 20)

    foreground_color : colorspec
        color of the foreground (default "fg")

    background_color : colorspec
        color of the backgroundground (default "bg")

    trough_color : colorspec
        color of the trough (default "lightgrey")

    show_value : boolean
        if True (default), show values; if False don't show values

    label : str
        label if the slider (default null string) |n|

    font : str
         font of the text (default Helvetica)

    fontsize : int
         fontsize of the text (default 12)

    action : function
         function executed when the slider value is changed (default None) |n|
         the function should have one argument, being the new value |n|
         if None (default), no action

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    The current value of the slider is the v attibute of the slider. |n|
    All measures are in screen coordinates |n|
    On Pythonista, this functionality is emulated by salabim
    On other platforms, the tkinter functionality is used.
    """

    def __init__(
        self,
        x=0,
        y=0,
        width=100,
        height=20,
        vmin=0,
        vmax=10,
        v=None,
        resolution=1,
        background_color="bg",
        foreground_color="fg",
        trough_color="lightgray",
        show_value=True,
        label="",
        font="",
        fontsize=12,
        action=None,
        xy_anchor="sw",
        env=None,
        linecolor=None,  # only for backward compatibility
        labelcolor=None,  # only for backward compatibility
        layer=None,  # only for backward compatibility
    ):

        self.env = g.default_env if env is None else env
        n = round((vmax - vmin) / resolution) + 1
        self.vmin = vmin
        self.vmax = vmin + (n - 1) * resolution
        self._v = vmin if v is None else v
        self.xdelta = width / n
        self.resolution = resolution

        self.type = "slider"
        self.t0 = -inf
        self.t1 = inf
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.sequence = self.env.serialize()
        self.x = x
        self.y = y - fontsize
        self.width = width
        self.height = height
        self.background_color = background_color
        self.foreground_color = foreground_color
        self.trough_color = trough_color
        self.show_value = show_value
        self.font = font
        self.fontsize = fontsize
        self._label = label
        self.action = action
        self.installed = False
        self.xy_anchor = xy_anchor

        if Pythonista:
            self.y = self.y - height * 1.5

        self.env.ui_objects.append(self)

    def v(self, value=None):
        """
        value

        Parameters
        ----------
        value: float
            new value |n|
            if omitted, no change

        Returns
        -------
        Current value of the slider : float
        """
        if value is not None:
            if self.env._animate:
                if Pythonista:
                    self._v = value
                    if self.action is not None:
                        self.action(str(value))
                else:
                    self.slider.set(value)
            else:
                self._v = value

        if Pythonista:
            return repr(self._v)
        else:
            if self.env._animate:
                return self.slider.get()
            else:
                return self._v

    def label(self, text=None):
        if text is not None:
            self._label = text
            if hasattr(self, "slider"):
                self.slider.config(label=self._label)
        return self._label

    def install(self):
        if not Pythonista:
            x = self.x + self.env.xy_anchor_to_x(self.xy_anchor, screen_coordinates=True)
            y = self.y + self.env.xy_anchor_to_y(self.xy_anchor, screen_coordinates=True)
            self.slider = tkinter.Scale(
                self.env.root,
                from_=self.vmin,
                to=self.vmax,
                orient=tkinter.HORIZONTAL,
                resolution=self.resolution,
                command=self.action,
                length=self.width,
                width=self.height,
            )
            self.slider.window = g.canvas.create_window(x, self.env._height - y, anchor=tkinter.NW, window=self.slider)
            self.slider.config(
                font=(self.font, int(self.fontsize * 0.8)),
                foreground=self.env.colorspec_to_hex(self.env.colorspec_to_tuple(self.foreground_color), False),
                background=self.env.colorspec_to_hex(self.env.colorspec_to_tuple(self.background_color), False),
                highlightbackground=self.env.colorspec_to_hex(self.env.colorspec_to_tuple(self.background_color), False),
                troughcolor=self.env.colorspec_to_hex(self.env.colorspec_to_tuple(self.trough_color), False),
                showvalue=self.show_value,
                label=self._label,
            )

        self.installed = True
        self.v(self._v)

    def remove(self):
        """
        removes the slider object |n|
        The ui object is removed from the ui queue,
        so effectively ending this ui
        """
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if self.installed:
            if not Pythonista:
                self.slider.quit()
            self.installed = False


class AnimateQueue(DynamicClass):
    """
        Animates the component in a queue.

        Parameters
        ----------
        queue : Queue

        x : float
            x-position of the first component in the queue |n|
            default: 50

        y : float
            y-position of the first component in the queue |n|
            default: 50

        direction : str
            if "w", waiting line runs westwards (i.e. from right to left) |n|
            if "n", waiting line runs northeards (i.e. from bottom to top) |n|
            if "e", waiting line runs eastwards (i.e. from left to right) (default) |n|
            if "s", waiting line runs southwards (i.e. from top to bottom)
    :

        trajectory : Trajectory
            trajectory to be followed. Overrides any given directory

        reverse : bool
            if False (default), display in normal order. If True, reversed.

        max_length : int
            maximum number of components to be displayed

        xy_anchor : str
            specifies where x and y are relative to |n|
            possible values are (default: sw): |n|
            ``nw    n    ne`` |n|
            ``w     c     e`` |n|
            ``sw    s    se``

        titlecolor : colorspec
            color of the title (default foreground color)

        titlefont : font
            font of the title (default null string)

        titlefontsize : int
            size of the font of the title (default 15)

        title : str
            title to be shown above queue |n|
            default: name of the queue

        titleoffsetx : float
            x-offset of the title relative to the start of the queue |n|
            default: 25 if direction is w, -25 otherwise

        titleoffsety : float
            y-offset of the title relative to the start of the queue |n|
            default: -25 if direction is s, -25 otherwise

        id : any
            the animation works by calling the animation_objects method of each component, optionally
            with id. By default, this is self, but can be overriden, particularly with the queue

        arg : any
            this is used when a parameter is a function with two parameters, as the first argument or
            if a parameter is a method as the instance |n|
            default: self (instance itself)

        visible : bool
            if False, nothing will be shown |n|
            (default True)

        keep : bool
            if False, animation object will be taken from the animation objects. With show(), the animation can be reshown.
            (default True)

        parent : Component
            component where this animation object belongs to (default None) |n|
            if given, the animation object will be removed
            automatically when the parent component is no longer accessible

        Note
        ----
        All measures are in screen coordinates |n|

        All parameters, apart from queue, id, arg and parent can be specified as: |n|
        - a scalar, like 10 |n|
        - a function with zero arguments, like lambda: title |n|
        - a function with one argument, being the time t, like lambda t: t + 10 |n|
        - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
        - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(
        self,
        queue,
        x=50,
        y=50,
        direction="w",
        trajectory=None,
        max_length=None,
        xy_anchor="sw",
        reverse=False,
        title=None,
        titlecolor="fg",
        titlefontsize=15,
        titlefont="",
        titleoffsetx=None,
        titleoffsety=None,
        layer=0,
        id=None,
        arg=None,
        parent=None,
        over3d=None,
        keep=True,
        visible=True,
    ):
        super().__init__()
        _checkisqueue(queue)
        self._queue = queue
        self.xy_anchor = xy_anchor
        self.x = x
        self.y = y
        self.id = self if id is None else id
        self.arg = self if arg is None else arg
        self.max_length = max_length
        self.direction = direction
        self.reverse = reverse
        self.current_aos = {}
        if parent is not None:
            if not isinstance(parent, Component):
                raise ValueError(repr(parent) + " is not a component")
            parent._animation_children.add(self)
        self.env = queue.env

        self.titleoffsetx = titleoffsetx
        self.titleoffsety = titleoffsety
        self.titlefont = titlefont
        self.titlefontsize = titlefontsize
        self.titlecolor = titlecolor
        self.title = title
        self.layer = layer
        self.visible = visible
        self.keep = keep
        self.over3d = _default_over3d if over3d is None else over3d
        self.trajectory = trajectory
        self.register_dynamic_attributes(
            "xy_anchor x y id max_length direction reverse titleoffsetx titleoffsety titlefont titlefontsize titlecolor title layer visible keep"
        )

        self.ao_title = AnimateText(
            text=lambda t: self.title(t),
            textcolor=lambda t: self.titlecolor(t),
            x=lambda: self.x_t,
            y=lambda: self.y_t,
            text_anchor=lambda: self.text_anchor_t,
            angle=lambda: self.angle_t,
            screen_coordinates=True,
            fontsize=lambda t: self.titlefontsize(t),
            font=lambda t: self.titlefont(t),
            layer=lambda t: self.layer(t),
            over3d=self.over3d,
            visible=lambda: self.visible_t,
        )
        self.show()

    def update(self, t):
        if not self.keep(t):
            self.remove()
            return
        prev_aos = self.current_aos
        self.current_aos = {}
        xy_anchor = self.xy_anchor(t)
        max_length = self.max_length(t)
        direction = self.direction(t).lower()
        if self.trajectory is None:
            x = self.x(t)
            y = self.y(t)
        else:
            direction = "t"
            x = 0
            y = 0

            trajectory = self.trajectory

        reverse = self.reverse(t)
        self.visible_t = self.visible(t)
        titleoffsetx = self.titleoffsetx(t)
        titleoffsety = self.titleoffsety(t)

        x += self._queue.env.xy_anchor_to_x(xy_anchor, screen_coordinates=True, over3d=self.over3d)
        y += self._queue.env.xy_anchor_to_y(xy_anchor, screen_coordinates=True, over3d=self.over3d)

        if direction == "e":
            self.x_t = x + (-25 if titleoffsetx is None else titleoffsetx)
            self.y_t = y + (25 if titleoffsety is None else titleoffsety)
            self.text_anchor_t = "sw"
            self.angle_t = 0
        elif direction == "w":
            self.x_t = x + (25 if titleoffsetx is None else titleoffsetx)
            self.y_t = y + (25 if titleoffsety is None else titleoffsety)
            self.text_anchor_t = "se"
            self.angle_t = 0
        elif direction == "n":
            self.x_t = x + (-25 if titleoffsetx is None else titleoffsetx)
            self.y_t = y + (-25 if titleoffsety is None else titleoffsety)
            self.text_anchor_t = "sw"
            self.angle_t = 0
        elif direction == "s":
            self.x_t = x + (-25 if titleoffsetx is None else titleoffsetx)
            self.y_t = y + (25 if titleoffsety is None else titleoffsety)
            self.text_anchor_t = "sw"
            self.angle_t = 0
        elif direction == "t":
            self.x_t = trajectory.x(t=x, _t0=0) + (-25 if titleoffsetx is None else titleoffsetx)
            self.y_t = trajectory.y(t=x, _t0=0) + (25 if titleoffsety is None else titleoffsety)
            self.text_anchor_t = "sw"
            self.angle_t = 0
        n = 0
        for c in reversed(self._queue) if reverse else self._queue:
            if ((max_length is not None) and n >= max_length) or not self.visible_t:
                break

            if c not in prev_aos:
                nargs = c.animation_objects.__code__.co_argcount
                if nargs == 1:
                    animation_objects = self.current_aos[c] = c.animation_objects()
                else:
                    animation_objects = self.current_aos[c] = c.animation_objects(self.id(t))
            else:
                animation_objects = self.current_aos[c] = prev_aos[c]
                del prev_aos[c]

            dimx = _call(animation_objects[0], t, c)
            dimy = _call(animation_objects[1], t, c)
            for ao in animation_objects[2:]:
                if isinstance(ao, AnimateClassic):
                    if direction == "t":
                        ao.x0 = trajectory.x(t=x, _t0=0)
                        ao.y0 = trajectory.y(t=x, _t0=0)
                    else:
                        ao.x0 = x
                        ao.y0 = y
                else:
                    if direction == "t":
                        ao.x = trajectory.x(t=x, _t0=0)
                        ao.y = trajectory.y(t=x, _t0=0)
                        ao.angle = trajectory.angle(t=x, _t0=0)
                    else:
                        ao.x = x
                        ao.y = y

            if direction == "w":
                x -= dimx
            if direction == "s":
                y -= dimy
            if direction == "e":
                x += dimx
            if direction == "n":
                y += dimy
            if direction == "t":
                x += dimx

            n += 1

        for animation_objects in prev_aos.values():
            for ao in animation_objects[2:]:
                ao.remove()

    def show(self):
        """
        show (unremove)

        It is possible to use this method if already shown
        """
        self.ao_title.show()
        self.env.sys_objects.add(self)
        self.current_aos = {}

    def remove(self):
        self.env.sys_objects.discard(self)
        self.ao_title.remove()
        for animation_objects in self.current_aos.values():
            for ao in animation_objects[2:]:
                ao.remove()

    def is_removed(self):
        return self not in self.env.sys_objects


class Animate3dQueue(DynamicClass):
    """
    Animates the component in a queue.

    Parameters
    ----------
    queue : Queue

    x : float
        x-position of the first component in the queue |n|
        default: 0

    y : float
        y-position of the first component in the queue |n|
        default: 0

    z : float
        z-position of the first component in the queue |n|
        default: 0

    direction : str
        if "x+", waiting line runs in positive x direction (default) |n|
        if "x-", waiting line runs in negative x direction |n|
        if "y+", waiting line runs in positive y direction |n|
        if "y-", waiting line runs in negative y direction |n|
        if "z+", waiting line runs in positive z direction |n|
        if "z-", waiting line runs in negative z direction |n|

    reverse : bool
        if False (default), display in normal order. If True, reversed.

    max_length : int
        maximum number of components to be displayed

    layer : int
        layer (default 0)

    id : any
        the animation works by calling the animation_objects method of each component, optionally
        with id. By default, this is self, but can be overriden, particularly with the queue

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    visible : bool
        if False, nothing will be shown |n|
        (default True)

    keep : bool
        if False, animation object will be taken from the animation objects. With show(), the animation can be reshown.
        (default True)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    Note
    ----
    All parameters, apart from queue, id, arg and parent can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(self, queue, x=0, y=0, z=0, direction="x+", max_length=None, reverse=False, layer=0, id=None, arg=None, parent=None, visible=True, keep=True):
        super().__init__()
        _checkisqueue(queue)
        self._queue = queue
        self.x = x
        self.y = y
        self.z = z
        self.id = self if id is None else id
        self.arg = self if arg is None else arg
        self.max_length = max_length
        self.direction = direction
        self.visible = visible
        self.keep = keep
        self.reverse = reverse
        self.current_aos = {}
        if parent is not None:
            if not isinstance(parent, Component):
                raise ValueError(repr(parent) + " is not a component")
            parent._animation_children.add(self)
        self.env = queue.env
        self.layer = layer
        self.register_dynamic_attributes("x y z id max_length direction reverse layer visible keep")
        self.show()

    def update(self, t):
        if not self.keep(t):
            self.remove()
            return

        prev_aos = self.current_aos
        self.current_aos = {}
        max_length = self.max_length(t)
        x = self.x(t)
        y = self.y(t)
        z = self.z(t)

        direction = self.direction(t).lower()
        if direction not in ("x+ x- y+ y- z+ z-").split():
            raise ValueError(f"direction {direction} not recognized")

        reverse = self.reverse(t)

        n = 0
        for c in reversed(self._queue) if reverse else self._queue:
            if (max_length is not None) and n >= max_length:
                break
            if c not in prev_aos:
                nargs = c.animation3d_objects.__code__.co_argcount
                if nargs == 1:
                    animation_objects = self.current_aos[c] = c.animation3d_objects()
                else:
                    animation_objects = self.current_aos[c] = c.animation3d_objects(self.id(t))
            else:
                animation_objects = self.current_aos[c] = prev_aos[c]
                del prev_aos[c]
            dimx = _call(animation_objects[0], t, c)
            dimy = _call(animation_objects[1], t, c)
            dimz = _call(animation_objects[2], t, c)

            for ao in animation_objects[3:]:
                ao.x_offset = x
                ao.y_offset = y
                ao.z_offset = z

            if direction == "x+":
                x += dimx
            if direction == "x-":
                x -= dimx

            if direction == "y+":
                y += dimy
            if direction == "y-":
                y -= dimy

            if direction == "z+":
                z += dimz
            if direction == "z-":
                z -= dimz
            n += 1

        for animation_objects in prev_aos.values():
            for ao in animation_objects[3:]:
                ao.remove()

    def queue(self):
        """
        Returns
        -------
        the queue this object refers to. Can be useful in Component.animation3d_objects: queue
        """
        return self._queue

    def show(self):
        """
        show (unremove)

        It is possible to use this method if already shown
        """
        self.env.sys_objects.add(self)

    def remove(self):
        for animation_objects in self.current_aos.values():
            for ao in animation_objects[3:]:
                ao.remove()
        self.env.sys_objects.discard(self)

    def is_removed(self):
        return self not in self.env.sys_objects


class AnimateCombined:
    """
    Combines several Animate? objects

    Parameters
    ----------
    animation_objects : iterable
        iterable of Animate2dBase, Animate3dBase or AnimateCombined objects

    **kwargs : dict
        attributes to be set for objects in animation_objects

    Notes
    -----
    When an attribute of an AnimateCombined is assigned, it will propagate to all members,
    provided it has already that attribute. |n|
    When an attribute of an AnimateCombined is queried, the value of the attribute
    of the first animation_object of the list that has such an attribute will be returned. |n|
    If the attribute does not exist in any animation_object of the list, an AttributeError will be raised. |n|
    |n|
    It is possible to use animation_objects with ::

        an = sim.AnimationCombined(car.animation_objects[2:])
        an = sim.AnimationCombined(car.animation3d_objects[3:])
    """

    def __init__(self, animation_objects, **kwargs):
        self.animation_objects = animation_objects

        self.update(**kwargs)

    def update(self, **kwargs):
        """
        Updated one or more attributes

        Parameters
        ----------
        **kwargs : dict
            attributes to be set
        """

        for k, v in kwargs.items():
            for item in self.animation_objects:
                setattr(item, k, v)

    def __setattr__(self, key, value):
        if key == "animation_objects":
            super().__setattr__(key, value)
        else:
            for item in self.animation_objects:
                if hasattr(item, key):
                    setattr(item, key, value)

    def __getattr__(self, key):
        for item in self.animation_objects:
            if hasattr(item, key):
                return getattr(item, key)

        raise AttributeError(f"None of the AnimateCombined animation objects has an attribute {key!r}")

    def append(self, item):
        """
        Add Animate2dBase, Animate3dBase or AnimateCombined object

        Parameters
        ----------
        item : Animate2dBase, Animate3dBase or AnimateCombined
            to be added
        """
        if not isinstance(item, (AnimateCombined, Animate2dBase, Animate3dBase)):
            return NotImplemented
        self.animation_objects.append(item)

    def remove(self):
        """
        remove all members from the animation
        """
        for item in self.animation_objects:
            item.remove()

    def show(self):
        """
        show all members in the animation
        """
        for item in self.animation_objects:
            item.show()

    def is_removed(self):
        return all(item.is_removed() for item in self.animation_objects)

    def __repr__(self):
        return f"{self.__class__.__name__} ({','.join(repr(item) for item in self.animation_objects)})"


class AnimateText(Animate2dBase):
    """
    Displays a text

    Parameters
    ----------
    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines
        if text is tple or list, each item is displayed on a separate line

    x : float
        position of anchor point (default 0)

    y : float
        position of anchor point (default 0)

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated

    offsetx : float
        offsets the x-coordinate of the rectangle (default 0)

    offsety : float
        offsets the y-coordinate of the rectangle (default 0)

    angle : float
        angle of the text (in degrees) |n|
        default: 0

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the last -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    text_anchor : str
        anchor position of text|n|
        specifies where to texts relative to the rectangle
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    textcolor : colorspec
        color of the text (default foreground_color)

    fontsize : float
        fontsize of text (default 15)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are use for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called

    """

    def __init__(
        self,
        text=None,
        x=None,
        y=None,
        font=None,
        fontsize=None,
        textcolor=None,
        text_anchor=None,
        angle=None,
        xy_anchor=None,
        layer=None,
        max_lines=None,
        offsetx=None,
        offsety=None,
        arg=None,
        visible=None,
        keep=None,
        parent=None,
        env=None,
        screen_coordinates=False,
        over3d=None,
    ):
        super().__init__(
            locals_=locals(),
            type="text",
            argument_default=dict(
                text="",
                x=0,
                y=0,
                fontsize=15,
                textcolor="fg",
                font="mono",
                text_anchor="sw",
                angle=0,
                visible=True,
                keep=True,
                xy_anchor="",
                layer=0,
                offsetx=0,
                offsety=0,
                max_lines=0,
            ),
            attach_text=False,
        )


class AnimateRectangle(Animate2dBase):
    """
    Displays a rectangle, optionally with a text

    Parameters
    ----------
    spec : four item tuple or list
        should specify xlowerleft, ylowerleft, xupperright, yupperright

    x : float
        position of anchor point (default 0)

    y : float
        position of anchor point (default 0)

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated

    offsetx : float
        offsets the x-coordinate of the rectangle (default 0)

    offsety : float
        offsets the y-coordinate of the rectangle (default 0)

    linewidth : float
        linewidth of the contour |n|
        default 1

    fillcolor : colorspec
        color of interior (default foreground_color) |n|
        default transparent

    linecolor : colorspec
        color of the contour (default transparent)

    angle : float
        angle of the rectangle (in degrees) |n|
        default: 0

    as_points : bool
         if False (default), the contour lines are drawn |n|
         if True, only the corner points are shown

    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the last -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    text_anchor : str
        anchor position of text|n|
        specifies where to texts relative to the rectangle
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    textcolor : colorspec
        color of the text (default foreground_color)

    text_offsetx : float
        extra x offset to the text_anchor point

    text_offsety : float
        extra y offset to the text_anchor point

    fontsize : float
        fontsize of text (default 15)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(
        self,
        spec=None,
        x=None,
        y=None,
        fillcolor=None,
        linecolor=None,
        linewidth=None,
        text=None,
        fontsize=None,
        textcolor=None,
        font=None,
        angle=None,
        xy_anchor=None,
        layer=None,
        max_lines=None,
        offsetx=None,
        offsety=None,
        as_points=None,
        text_anchor=None,
        text_offsetx=None,
        text_offsety=None,
        arg=None,
        parent=None,
        visible=None,
        keep=None,
        env=None,
        screen_coordinates=False,
        over3d=None,
    ):

        super().__init__(
            locals_=locals(),
            type="rectangle",
            argument_default=dict(
                spec=(0, 0, 0, 0),
                x=0,
                y=0,
                fillcolor="fg",
                linecolor="",
                linewidth=1,
                text="",
                fontsize=15,
                textcolor="bg",
                font="",
                angle=0,
                xy_anchor="",
                layer=0,
                max_lines=0,
                offsetx=0,
                offsety=0,
                as_points=False,
                text_anchor="c",
                text_offsetx=0,
                text_offsety=0,
                visible=True,
                keep=True,
                parent=None,
            ),
            attach_text=True,
        )


class AnimatePolygon(Animate2dBase):
    """
    Displays a polygon, optionally with a text

    Parameters
    ----------
    spec : tuple or list
        should specify x0, y0, x1, y1, ...

    x : float
        position of anchor point (default 0)

    y : float
        position of anchor point (default 0)

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated

    offsetx : float
        offsets the x-coordinate of the polygon (default 0)

    offsety : float
        offsets the y-coordinate of the polygon (default 0)

    linewidth : float
        linewidth of the contour |n|
        default 1

    fillcolor : colorspec
        color of interior (default foreground_color) |n|
        default transparent

    linecolor : colorspec
        color of the contour (default transparent)

    angle : float
        angle of the polygon (in degrees) |n|
        default: 0

    as_points : bool
         if False (default), the contour lines are drawn |n|
         if True, only the corner points are shown

    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the last -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    text_anchor : str
        anchor position of text|n|
        specifies where to texts relative to the polygon
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    textcolor : colorspec
        color of the text (default foreground_color)

    text_offsetx : float
        extra x offset to the text_anchor point

    text_offsety : float
        extra y offset to the text_anchor point

    fontsize : float
        fontsize of text (default 15)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are use for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(
        self,
        spec=None,
        x=None,
        y=None,
        fillcolor=None,
        linecolor=None,
        linewidth=None,
        text=None,
        fontsize=None,
        textcolor=None,
        font=None,
        angle=None,
        xy_anchor=None,
        layer=None,
        max_lines=None,
        offsetx=None,
        offsety=None,
        as_points=None,
        text_anchor=None,
        text_offsetx=None,
        text_offsety=None,
        arg=None,
        parent=None,
        visible=None,
        keep=None,
        env=None,
        screen_coordinates=False,
        over3d=None,
    ):
        super().__init__(
            locals_=locals(),
            type="polygon",
            argument_default=dict(
                spec=(),
                x=0,
                y=0,
                linecolor="",
                linewidth=1,
                fillcolor="fg",
                text="",
                fontsize=15,
                textcolor="fg",
                font="",
                angle=0,
                xy_anchor="",
                layer=0,
                max_lines=0,
                offsetx=0,
                offsety=0,
                as_points=False,
                text_anchor="c",
                text_offsetx=0,
                text_offsety=0,
                visible=True,
                keep=True,
            ),
            attach_text=True,
        )


class AnimateLine(Animate2dBase):
    """
    Displays a line, optionally with a text

    Parameters
    ----------
    spec : tuple or list
        should specify x0, y0, x1, y1, ...

    x : float
        position of anchor point (default 0)

    y : float
        position of anchor point (default 0)

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated

    offsetx : float
        offsets the x-coordinate of the line (default 0)

    offsety : float
        offsets the y-coordinate of the line (default 0)

    linewidth : float
        linewidth of the contour |n|
        default 1

    linecolor : colorspec
        color of the contour (default foreground_color)

    angle : float
        angle of the line (in degrees) |n|
        default: 0

    as_points : bool
         if False (default), the contour lines are drawn |n|
         if True, only the corner points are shown

    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the last -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    text_anchor : str
        anchor position of text|n|
        specifies where to texts relative to the polygon
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    textcolor : colorspec
        color of the text (default foreground_color)

    text_offsetx : float
        extra x offset to the text_anchor point

    text_offsety : float
        extra y offset to the text_anchor point

    fontsize : float
        fontsize of text (default 15)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are use for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(
        self,
        spec=None,
        x=None,
        y=None,
        linecolor=None,
        linewidth=None,
        text=None,
        fontsize=None,
        textcolor=None,
        font=None,
        angle=None,
        xy_anchor=None,
        layer=None,
        max_lines=None,
        offsetx=None,
        offsety=None,
        as_points=None,
        text_anchor=None,
        text_offsetx=None,
        text_offsety=None,
        arg=None,
        parent=None,
        visible=None,
        keep=None,
        env=None,
        screen_coordinates=False,
        over3d=None,
    ):
        fillcolor = None  # required for make_pil_image

        super().__init__(
            locals_=locals(),
            type="line",
            argument_default=dict(
                spec=(),
                x=0,
                y=0,
                linecolor="fg",
                linewidth=1,
                fillcolor="",
                text="",
                fontsize=15,
                textcolor="fg",
                font="",
                angle=0,
                xy_anchor="",
                layer=0,
                max_lines=0,
                offsetx=0,
                offsety=0,
                as_points=False,
                text_anchor="c",
                text_offsetx=0,
                text_offsety=0,
                visible=True,
                keep=True,
            ),
            attach_text=True,
        )


class AnimatePoints(Animate2dBase):
    """
    Displays a series of points, optionally with a text

    Parameters
    ----------
    spec : tuple or list
        should specify x0, y0, x1, y1, ...

    x : float
        position of anchor point (default 0)

    y : float
        position of anchor point (default 0)

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated

    offsetx : float
        offsets the x-coordinate of the points (default 0)

    offsety : float
        offsets the y-coordinate of the points (default 0)

    linewidth : float
        width of the points |n|
        default 1

    linecolor : colorspec
        color of the points (default foreground_color)

    angle : float
        angle of the points (in degrees) |n|
        default: 0

    as_points : bool
         if False (default), the contour lines are drawn |n|
         if True, only the corner points are shown

    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the last -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    text_anchor : str
        anchor position of text|n|
        specifies where to texts relative to the polygon
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    textcolor : colorspec
        color of the text (default foreground_color)

    text_offsetx : float
        extra x offset to the text_anchor point

    text_offsety : float
        extra y offset to the text_anchor point

    fontsize : float
        fontsize of text (default 15)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are use for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(
        self,
        spec=None,
        x=None,
        y=None,
        linecolor=None,
        linewidth=None,
        text=None,
        fontsize=None,
        textcolor=None,
        font=None,
        angle=None,
        xy_anchor=None,
        layer=None,
        max_lines=None,
        offsetx=None,
        offsety=None,
        as_points=None,
        text_anchor=None,
        text_offsetx=None,
        text_offsety=None,
        arg=None,
        parent=None,
        visible=None,
        keep=None,
        env=None,
        screen_coordinates=False,
        over3d=None,
    ):
        fillcolor = None  # required for make_pil_image

        super().__init__(
            locals_=locals(),
            type="line",
            argument_default=dict(
                spec=(),
                x=0,
                y=0,
                linecolor="fg",
                linewidth=1,
                fillcolor="",
                text="",
                fontsize=15,
                textcolor="fg",
                font="",
                angle=0,
                xy_anchor="",
                layer=0,
                max_lines=0,
                offsetx=0,
                offsety=0,
                as_points=True,
                text_anchor="c",
                text_offsetx=0,
                text_offsety=0,
                visible=True,
                keep=True,
            ),
            attach_text=True,
        )


class AnimateCircle(Animate2dBase):
    """
    Displays a (partial) circle or (partial) ellipse , optionally with a text

    Parameters
    ----------
    radius : float
        radius of the circle

    radius1 : float
        the 'height' of the ellipse. If None (default), a circle will be drawn

    arc_angle0 : float
        start angle of the circle (default 0)

    arc_angle1 : float
        end angle of the circle (default 360) |n|
        when arc_angle1 > arc_angle0 + 360, only 360 degrees will be shown

    draw_arc : bool
        if False (default), no arcs will be drawn
        if True, the arcs from and to the center will be drawn

    x : float
        position of anchor point (default 0)

    y : float
        position of anchor point (default 0)

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated |n|
        The positions corresponds to a full circle even if arc_angle0 and/or arc_angle1 are specified.

    offsetx : float
        offsets the x-coordinate of the circle (default 0)

    offsety : float
        offsets the y-coordinate of the circle (default 0)

    linewidth : float
        linewidth of the contour |n|
        default 1

    fillcolor : colorspec
        color of interior (default foreground_color) |n|
        default transparent

    linecolor : colorspec
        color of the contour (default transparent)

    angle : float
        angle of the circle/ellipse and/or text (in degrees) |n|
        default: 0

    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the last -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    text_anchor : str
        anchor position of text|n|
        specifies where to texts relative to the polygon
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    textcolor : colorspec
        color of the text (default foreground_color)

    text_offsetx : float
        extra x offset to the text_anchor point

    text_offsety : float
        extra y offset to the text_anchor point

    fontsize : float
        fontsize of text (default 15)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are use for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(
        self,
        radius=None,
        radius1=None,
        arc_angle0=None,
        arc_angle1=None,
        draw_arc=None,
        x=None,
        y=None,
        fillcolor=None,
        linecolor=None,
        linewidth=None,
        text=None,
        fontsize=None,
        textcolor=None,
        font=None,
        angle=None,
        xy_anchor=None,
        layer=None,
        max_lines=None,
        offsetx=None,
        offsety=None,
        text_anchor=None,
        text_offsetx=None,
        text_offsety=None,
        arg=None,
        parent=None,
        visible=None,
        keep=None,
        env=None,
        screen_coordinates=False,
        over3d=None,
    ):

        super().__init__(
            locals_=locals(),
            type="circle",
            argument_default=dict(
                radius=100,
                radius1=None,
                arc_angle0=0,
                arc_angle1=360,
                draw_arc=False,
                x=0,
                y=0,
                fillcolor="fg",
                linecolor="",
                linewidth=1,
                text="",
                fontsize=15,
                textcolor="bg",
                font="",
                angle=0,
                xy_anchor="",
                layer=0,
                max_lines=0,
                offsetx=0,
                offsety=0,
                text_anchor="c",
                text_offsetx=0,
                text_offsety=0,
                visible=True,
                keep=True,
            ),
            attach_text=True,
        )


class AnimateImage(Animate2dBase):
    """
    Displays an image, optionally with a text

    Parameters
    ----------
    image : str, pathlib.Path or PIL Image
        image to be displayed |n|
        if used as function or method or in direct assigmnent,
        the image should be a file containing an image or a PIL image

    x : float
        position of anchor point (default 0)

    y : float
        position of anchor point (default 0)

    xy_anchor : str
        specifies where x and y are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If null string, the given coordimates are used untranslated

    anchor : str
        specifies where the x and refer to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|

    offsetx : float
        offsets the x-coordinate of the circle (default 0)

    offsety : float
        offsets the y-coordinate of the circle (default 0)

    angle : float
        angle of the image (in degrees) (default 0)

    alpha : float
        alpha of the image (0-255) (default 255)

    width : float
       width of the image (default: None = no scaling) |n|

    text : str, tuple or list
        the text to be displayed |n|
        if text is str, the text may contain linefeeds, which are shown as individual lines

    max_lines : int
        the maximum of lines of text to be displayed |n|
        if positive, it refers to the first max_lines lines |n|
        if negative, it refers to the last -max_lines lines |n|
        if zero (default), all lines will be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    text_anchor : str
        anchor position of text|n|
        specifies where to texts relative to the polygon
        point |n|
        possible values are (default: c): |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se``

    textcolor : colorspec
        color of the text (default foreground_color)

    text_offsetx : float
        extra x offset to the text_anchor point

    text_offsety : float
        extra y offset to the text_anchor point

    fontsize : float
        fontsize of text (default 15)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are used for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.

    over3d : bool
        if True, this object will be rendered to the OpenGL window |n|
        if False (default), the normal 2D plane will be used.

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    """

    def __init__(
        self,
        image=None,
        x=None,
        y=None,
        width=None,
        text=None,
        fontsize=None,
        textcolor=None,
        font=None,
        angle=None,
        alpha=None,
        xy_anchor=None,
        layer=None,
        max_lines=None,
        offsetx=None,
        offsety=None,
        text_anchor=None,
        text_offsetx=None,
        text_offsety=None,
        anchor=None,
        visible=None,
        keep=None,
        env=None,
        arg=None,
        screen_coordinates=False,
        over3d=None,
        parent=None,
    ):

        super().__init__(
            locals_=locals(),
            type="image",
            argument_default=dict(
                image="",
                x=0,
                y=0,
                width=None,
                text="",
                fontsize=15,
                textcolor="bg",
                font="",
                angle=0,
                alpha=255,
                xy_anchor="",
                layer=0,
                max_lines=0,
                offsetx=0,
                offsety=0,
                text_anchor="c",
                text_offsetx=0,
                text_offsety=0,
                anchor="sw",
                visible=True,
                keep=True,
            ),
            attach_text=True,
        )


class Component:
    """Component object

    A salabim component is used as component (primarily for queueing)
    or as a component with a process |n|
    Usually, a component will be defined as a subclass of Component.

    Parameters
    ----------
    name : str
        name of the component. |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

    at : float or distribution
        schedule time |n|
        if omitted, now is used |n|
        if distribution, the distribution is sampled

    delay : float or distributiom
        schedule with a delay |n|
        if omitted, no delay |n|
        if distribution, the distribution is sampled

    priority : float
        priority |n|
        default: 0 |n|
        if a component has the same time on the event list, this component is sorted accoring to
        the priority.

    urgent : bool
        urgency indicator |n|
        if False (default), the component will be scheduled
        behind all other components scheduled
        for the same time and priority |n|
        if True, the component will be scheduled
        in front of all components scheduled
        for the same time and priority

    process : str
        name of process to be started. |n|
        if None (default), it will try to start self.process() |n|
        if null string, no process will be started even if self.process() exists,
        i.e. become a data component. |n|

    suppress_trace : bool
        suppress_trace indicator |n|
        if True, this component will be excluded from the trace |n|
        If False (default), the component will be traced |n|
        Can be queried or set later with the suppress_trace method.

    suppress_pause_at_step : bool
        suppress_pause_at_step indicator |n|
        if True, if this component becomes current, do not pause when stepping |n|
        If False (default), the component will be paused when stepping |n|
        Can be queried or set later with the suppress_pause_at_step method.

    skip_standby : bool
        skip_standby indicator |n|
        if True, after this component became current, do not activate standby components |n|
        If False (default), after the component became current  activate standby components |n|
        Can be queried or set later with the skip_standby method.

    mode : str preferred
        mode |n|
        will be used in trace and can be used in animations |n|
        if omitted, the mode will be "". |n|
        also mode_time will be set to now.

    cap_now : bool
        indicator whether times (at, delay) in the past are allowed. If, so now() will be used.
        default: sys.default_cap_now(), usualy False

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used
    """

    overridden_lineno = None

    def __init__(
        self,
        name=None,
        at=None,
        delay=None,
        priority=None,
        urgent=None,
        process=None,
        suppress_trace=False,
        suppress_pause_at_step=False,
        skip_standby=False,
        mode="",
        cap_now=None,
        env=None,
        **kwargs,
    ):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        _set_name(name, self.env._nameserializeComponent, self)
        self._qmembers = {}
        self._process = None
        self.status = _StatusMonitor(name=self.name() + ".status", level=True, initial_tally=data, env=self.env)
        self._requests = collections.OrderedDict()
        self._claims = collections.OrderedDict()
        self._waits = []
        self._on_event_list = False
        self._scheduled_time = inf
        self._failed = False
        self._skip_standby = skip_standby
        self._creation_time = self.env._now
        self._suppress_trace = suppress_trace
        self._suppress_pause_at_step = suppress_pause_at_step
        self.mode = _ModeMonitor(name=self.name() + ".mode", level=True, initial_tally=mode, env=self.env)
        self._mode_time = self.env._now
        self._aos = {}
        self._animation_children = set()

        if process is None:
            if hasattr(self, "process"):
                p = self.process
                process_name = "process"
            else:
                p = None
        else:
            if process == "":
                p = None
            else:
                try:
                    p = getattr(self, process)
                    process_name = process
                except AttributeError:
                    raise AttributeError("self." + process + " does not exist")
        if p is None:
            if at is not None:
                raise TypeError("at is not allowed for a data component")
            if delay is not None:
                raise TypeError("delay is not allowed for a data component")
            if urgent is not None:
                raise TypeError("urgent is not allowed for a data component")
            if priority is not None:
                raise TypeError("priority is not allowed for a data component")
            if self.env._trace:
                if self._name == "main":
                    self.env.print_trace("", "", self.name() + " create", self._modetxt())
                else:
                    self.env.print_trace("", "", self.name() + " create data component", self._modetxt())
        else:
            self.env.print_trace("", "", self.name() + " create", self._modetxt())

            kwargs_p = {}
            if kwargs:
                try:
                    parameters = inspect.signature(p).parameters
                except AttributeError:
                    parameters = inspect.getargspec(p)[0]  # pre Python 3.4

                for kwarg in list(kwargs):
                    if kwarg in parameters:
                        kwargs_p[kwarg] = kwargs[kwarg]
                        del kwargs[kwarg]  # here kwargs consumes the used arguments

            if inspect.isgeneratorfunction(p):
                self._process = p(**kwargs_p)
                self._process_isgenerator = True
            else:
                self._process = p
                self._process_isgenerator = False
                self._process_kwargs = kwargs_p

            extra = "process=" + process_name

            urgent = bool(urgent)
            if priority is None:
                priority = 0

            if delay is None:
                delay = 0
            elif callable(delay):
                delay = delay()
            if at is None:
                scheduled_time = self.env._now + delay
            else:
                if callable(at):
                    at = at()
                scheduled_time = at + self.env._offset + delay
            self.status._value = scheduled
            self._reschedule(scheduled_time, priority, urgent, "activate", cap_now, extra=extra)
        self.setup(**kwargs)

    def animation_objects(self, id):
        """
        defines how to display a component in AnimateQueue

        Parameters
        ----------
        id : any
            id as given by AnimateQueue. Note that by default this the reference to the AnimateQueue object.

        Returns
        -------
        List or tuple containg |n|
            size_x : how much to displace the next component in x-direction, if applicable |n|
            size_y : how much to displace the next component in y-direction, if applicable |n|
            animation objects : instances of Animate class |n|
            default behaviour: |n|
            square of size 40 (displacements 50), with the sequence number centered.

        Note
        ----
        If you override this method, be sure to use the same header, either with or without the id parameter. |n|
        """
        size_x = 50
        size_y = 50
        ao0 = AnimateRectangle(text=str(self.sequence_number()), textcolor="bg", spec=(-20, -20, 20, 20), linewidth=0, fillcolor="fg")
        return (size_x, size_y, ao0)

    def animation3d_objects(self, id):
        """
        defines how to display a component in Animate3dQueue

        Parameters
        ----------
        id : any
            id as given by Animate3dQueue. Note that by default this the reference to the Animate3dQueue object.

        Returns
        -------
        List or tuple containg |n|
            size_x : how much to displace the next component in x-direction, if applicable |n|
            size_y : how much to displace the next component in y-direction, if applicable |n|
            size_z : how much to displace the next component in z-direction, if applicable |n|
            animation objects : instances of Animate3dBase class |n|
            default behaviour: |n|
            white 3dbox of size 8, placed on the z=0 plane (displacements 10).

        Note
        ----
        If you override this method, be sure to use the same header, either with or without the id parameter. |n|

        Note
        ----
        The animation object should support the x_offset, y_offset and z_offset attributes, in order to be able
        to position the object correctly. All native salabim Animate3d classes are offset aware.
        """
        size_x = 10
        size_y = 10
        size_z = 10
        ao0 = Animate3dBox(x_len=8, y_len=8, z_len=8, x_ref=0, y_ref=0, z_ref=1, color="white", shaded=True)
        return (size_x, size_y, size_z, ao0)

    def _remove_from_aos(self, q):
        if q in self._aos:
            for ao in self._aos[q][2:]:
                ao.remove()
            del self._aos[q]

    def setup(self):
        """
        called immediately after initialization of a component.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments will be passed

        Example
        -------
            class Car(sim.Component):
                def setup(self, color):
                    self.color = color

                def process(self):
                    ...

            redcar=Car(color="red") |n|
            bluecar=Car(color="blue")
        """
        pass

    def __repr__(self):
        return object_to_str(self) + " (" + self.name() + ")"

    def register(self, registry):
        """
        registers the component in the registry

        Parameters
        ----------
        registry : list
            list of (to be) registered objects

        Returns
        -------
        component (self) : Component

        Note
        ----
        Use Component.deregister if component does not longer need to be registered.
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self in registry:
            raise ValueError(self.name() + " already in registry")
        registry.append(self)
        return self

    def deregister(self, registry):
        """
        deregisters the component in the registry

        Parameters
        ----------
        registry : list
            list of registered components

        Returns
        -------
        component (self) : Component
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self not in registry:
            raise ValueError(self.name() + " not in registry")
        registry.remove(self)
        return self

    def print_info(self, as_str=False, file=None):
        """
        prints information about the component

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append(object_to_str(self) + " " + hex(id(self)))
        result.append("  name=" + self.name())
        result.append("  class=" + str(type(self)).split(".")[-1].split("'")[0])
        result.append("  suppress_trace=" + str(self._suppress_trace))
        result.append("  suppress_pause_at_step=" + str(self._suppress_pause_at_step))
        result.append("  status=" + self.status())
        result.append("  mode=" + self.mode())
        result.append("  mode_time=" + self.env.time_to_str(self.mode_time()))
        result.append("  creation_time=" + self.env.time_to_str(self.creation_time()))
        result.append("  scheduled_time=" + self.env.time_to_str(self.scheduled_time()))
        if len(self._qmembers) > 0:
            result.append("  member of queue(s):")
            for q in sorted(self._qmembers, key=lambda obj: obj.name().lower()):
                result.append(
                    "    "
                    + pad(q.name(), 20)
                    + " enter_time="
                    + self.env.time_to_str(self._qmembers[q].enter_time - self.env._offset)
                    + " priority="
                    + str(self._qmembers[q].priority)
                )
        if len(self._requests) > 0:
            result.append("  requesting resource(s):")

            for r in sorted(list(self._requests), key=lambda obj: obj.name().lower()):
                result.append("    " + pad(r.name(), 20) + " quantity=" + str(self._requests[r]))
        if len(self._claims) > 0:
            result.append("  claiming resource(s):")

            for r in sorted(list(self._claims), key=lambda obj: obj.name().lower()):
                result.append("    " + pad(r.name(), 20) + " quantity=" + str(self._claims[r]))
        if len(self._waits) > 0:
            if self._wait_all:
                result.append("  waiting for all of state(s):")
            else:
                result.append("  waiting for any of state(s):")
            for s, value, _ in self._waits:
                result.append("    " + pad(s.name(), 20) + " value=" + str(value))
        return return_or_print(result, as_str, file)

    def _push(self, t, priority, urgent):
        self.env._seq += 1
        if urgent:
            seq = -self.env._seq
        else:
            seq = self.env._seq
        self._on_event_list = True
        heapq.heappush(self.env._event_list, (t, priority, seq, self))

    def _remove(self):
        if self._on_event_list:
            for i in range(len(self.env._event_list)):
                if self.env._event_list[i][3] == self:
                    self.env._event_list[i] = self.env._event_list[0]
                    self.env._event_list.pop(0)
                    heapq.heapify(self.env._event_list)
                    self._on_event_list = False
                    return
            raise Exception("remove error", self.name())
        if self.status == standby:
            if self in self.env._standby_list:
                self.env._standby_list(self).remove(self)
            if self in self.env._pending_standby_list:
                self.env._pending_standby_list(self).remove(self)

    def _check_fail(self):
        if self._requests:
            if self.env._trace:
                self.env.print_trace("", "", self.name(), "request failed")
            for r in list(self._requests):
                self.leave(r._requesters)
                if r._requesters._length == 0:
                    r._minq = inf
            self._requests = collections.OrderedDict()
            self._failed = True

        if self._waits:
            if self.env._trace:
                self.env.print_trace("", "", self.name(), "wait failed")
            for state, _, _ in self._waits:
                if self in state._waiters:  # there might be more values for this state
                    self.leave(state._waiters)
            self._waits = []
            self._failed = True

    def _reschedule(self, scheduled_time, priority, urgent, caller, cap_now, extra="", s0=None):
        if scheduled_time < self.env._now:
            if cap_now is None:
                cap_now = _default_cap_now
            if cap_now:
                scheduled_time = self.env._now
            else:
                raise ValueError(f"scheduled time ({scheduled_time:0.3f}) before now ({self.env._now:0.3f})")
        self._scheduled_time = scheduled_time
        if scheduled_time != inf:
            self._push(scheduled_time, priority, urgent)
        if self.env._trace:
            if extra == "*":
                scheduled_time_str = "ends on no events left  "
                extra = " "
            else:
                scheduled_time_str = "scheduled for " + self.env.time_to_str(scheduled_time - self.env._offset).strip()
            if (scheduled_time == self.env._now) or (scheduled_time == inf):
                delta = ""
            else:
                delta = f" +{self.env.duration_to_str(scheduled_time - self.env._now)}"
            lineno = self.lineno_txt(add_at=True)
            self.env.print_trace(
                "",
                "",
                self.name() + " " + caller + delta,
                merge_blanks(scheduled_time_str + _prioritytxt(priority) + _urgenttxt(urgent) + lineno, self._modetxt(), extra),
                s0=s0,
            )

    def activate(self, at=None, delay=0, priority=0, urgent=False, process=None, keep_request=False, keep_wait=False, mode=None, cap_now=None, **kwargs):
        """
        activate component

        Parameters
        ----------
        at : float or distribution
            schedule time |n|
            if omitted, now is used |n|
            inf is allowed |n|
            if distribution, the distribution is sampled

        delay : float or distribution
            schedule with a delay |n|
            if omitted, no delay |n|
            if distribution, the distribution is sampled

        priority : float
            priority |n|
            default: 0 |n|
            if a component has the same time on the event list, this component is sorted accoring to
            the priority.

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time and priority |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time and priority

        process : str
            name of process to be started. |n|
            if None (default), process will not be changed |n|
            if the component is a data component, the
            generator function process will be used as the default process. |n|
            note that the function *must* be a generator,
            i.e. contains at least one yield.

        keep_request : bool
            this affects only components that are requesting. |n|
            if True, the requests will be kept and thus the status will remain requesting |n|
            if False (the default), the request(s) will be canceled and the status will become scheduled

        keep_wait : bool
            this affects only components that are waiting. |n|
            if True, the waits will be kept and thus the status will remain waiting |n|
            if False (the default), the wait(s) will be canceled and the status will become scheduled

        cap_now : bool
            indicator whether times (at, delay) in the past are allowed. If, so now() will be used.
            default: sys.default_cap_now(), usualy False

        mode : str preferred
            mode |n|
            will be used in the trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        if to be applied to the current component, use ``yield self.activate()``. |n|
        if both at and delay are specified, the component becomes current at the sum
        of the two values.
        """
        p = None
        if process is None:
            if self.status.value == data:
                if hasattr(self, "process"):
                    p = self.process
                    process_name = "process"
                else:
                    raise AttributeError("no process for data component")
        else:
            try:
                p = getattr(self, process)
                process_name = process
            except AttributeError:
                raise AttributeError("self." + process + " does not exist")

        if p is None:
            extra = ""
        else:
            if kwargs:
                try:
                    parameters = inspect.signature(p).parameters
                except AttributeError:
                    parameters = inspect.getargspec(p)[0]  # pre Python 3.4

                for kwarg in kwargs:
                    if kwarg not in parameters:
                        raise TypeError("unexpected keyword argument '" + kwarg + "'")

            if inspect.isgeneratorfunction(p):
                self._process = p(**kwargs)
                self._process_isgenerator = True
            else:
                self._process = p
                self._process_isgenerator = False
                self._process_kwargs = kwargs

            extra = "process=" + process_name

        if self.status.value != current:
            self._remove()
            if p is None:
                if not (keep_request or keep_wait):
                    self._check_fail()
            else:
                self._check_fail()

        self.set_mode(mode)

        if callable(delay):
            delay = delay()

        if at is None:
            scheduled_time = self.env._now + delay
        else:
            if callable(at):
                at = at()
            scheduled_time = at + self.env._offset + delay

        self.status._value = scheduled
        self._reschedule(scheduled_time, priority, urgent, "activate", cap_now, extra=extra)

    def hold(self, duration=None, till=None, priority=0, urgent=False, mode=None, cap_now=None):
        """
        hold the component

        Parameters
        ----------
        duration : float or distribution
            specifies the duration |n|
            if omitted, 0 is used |n|
            inf is allowed |n|
            if distribution, the distribution is sampled

        till : float or distribution
            specifies at what time the component will become current |n|
            if omitted, now is used |n|
            inf is allowed |n|
            if distribution, the distribution is sampled

        priority : float
            priority |n|
            default: 0 |n|
            if a component has the same time on the event list, this component is sorted accoring to
            the priority.

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time and priority |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time and priority

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        cap_now : bool
            indicator whether times (duration, till) in the past are allowed. If, so now() will be used.
            default: sys.default_cap_now(), usualy False

        Note
        ----
        if to be used for the current component, use ``yield self.hold(...)``. |n|

        if both duration and till are specified, the component will become current at the sum of
        these two.
        """
        if self.status.value != passive:
            if self.status != current:
                self._checkisnotdata()
                self._remove()
                self._check_fail()

        self.set_mode(mode)

        if till is None:
            if duration is None:
                scheduled_time = self.env._now
            else:
                if callable(duration):
                    duration = duration()
                scheduled_time = self.env._now + duration
        else:
            if duration is None:
                if callable(till):
                    till = till()
                scheduled_time = till + self.env._offset
            else:
                raise ValueError("both duration and till specified")
        self.status._value = scheduled
        self._reschedule(scheduled_time, priority, urgent, "hold", cap_now)

    def passivate(self, mode=None):
        """
        passivate the component

        Parameters
        ----------
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing is specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        if to be used for the current component (nearly always the case), use ``yield self.passivate()``.
        """
        if self.status.value == current:
            self._remaining_duration = 0
        else:
            self._checkisnotdata()
            self._remove()
            self._check_fail()
            self._remaining_duration = self._scheduled_time - self.env._now
        self._scheduled_time = inf

        self.set_mode(mode)
        if self.env._trace:
            lineno = self.lineno_txt(add_at=True)
            self.env.print_trace("", "", self.name() + " passivate", merge_blanks(lineno, self._modetxt()))
        self.status._value = passive

    def interrupt(self, mode=None):
        """
        interrupt the component

        Parameters
        ----------
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing is specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        Cannot be applied on the current component. |n|
        Use resume() to resume
        """
        if self.status.value == current:
            raise ValueError(self.name() + " current component cannot be interrupted")
        else:
            self.set_mode(mode)
            if self.status.value == interrupted:
                self._interrupt_level += 1
                extra = "." + str(self._interrupt_level)
            else:
                self._checkisnotdata()
                self._remove()
                self._remaining_duration = self._scheduled_time - self.env._now
                self._interrupted_status = self.status.value
                self._interrupt_level = 1
                self.status._value = interrupted
                extra = ""
            lineno = self.lineno_txt(add_at=True)
            self.env.print_trace("", "", self.name() + " interrupt" + extra, merge_blanks(lineno, self._modetxt()))

    def resume(self, all=False, mode=None, priority=0, urgent=False):
        """
        resumes an interrupted component

        Parameters
        ----------
        all : bool
            if True, the component returns to the original status, regardless of the number of interrupt levels |n|
            if False (default), the interrupt level will be decremented and if the level reaches 0,
            the component will return to the original status.

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing is specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        priority : float
            priority |n|
            default: 0 |n|
            if a component has the same time on the event list, this component is sorted accoring to
            the priority.


        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time and priority |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time and priority

        Note
        ----
        Can be only applied to interrupted components. |n|
        """
        if self.status.value == interrupted:
            self.set_mode(mode)
            self._interrupt_level -= 1
            if self._interrupt_level and (not all):
                self.env.print_trace("", "", self.name() + " resume (interrupted." + str(self._interrupt_level) + ")", merge_blanks(self._modetxt()))
            else:
                self.status._value = self._interrupted_status
                lineno = self.lineno_txt(add_at=True)
                self.env.print_trace("", "", self.name() + " resume (" + self.status() + ")", merge_blanks(lineno, self._modetxt()))
                if self.status.value == passive:
                    self.env.print_trace("", "", self.name() + " passivate", merge_blanks(lineno, self._modetxt()))
                elif self.status.value == standby:
                    self._scheduled_time = self.env._now
                    self.env._standbylist.append(self)
                    self.env.print_trace("", "", self.name() + " standby", merge_blanks(lineno, self._modetxt()))
                elif self.status.value in (scheduled, waiting, requesting):
                    if self.status.value == waiting:
                        if self._waits:
                            if self._trywait():
                                return
                            reason = "wait"
                    elif self.status.value == requesting:
                        if self._tryrequest():
                            return
                        reason = "request"
                    elif self.status.value == scheduled:
                        reason = "hold"
                    self._reschedule(self.env._now + self._remaining_duration, priority, urgent, reason, False)
                else:
                    raise Exception(self.name() + " unexpected interrupted_status", self.status.value())
        else:
            raise ValueError(self.name() + " not interrupted")

    def cancel(self, mode=None):
        """
        cancel component (makes the component data)

        Parameters
        ----------
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        if to be used for the current component, use ``yield self.cancel()``.
        """
        if self.status.value != current:
            self._checkisnotdata()
            self._remove()
            self._check_fail()
        self._process = None
        self._scheduled_time = inf
        self.set_mode(mode)
        if self.env._trace:
            self.env.print_trace("", "", "cancel " + self.name() + " " + self._modetxt())
        self.status._value = data

    def standby(self, mode=None):
        """
        puts the component in standby mode

        Parameters
        ----------
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        Not allowed for data components or main.

        if to be used for the current component
        (which will be nearly always the case),
        use ``yield self.standby()``.
        """
        if self.status.value != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()
        self._scheduled_time = self.env._now
        self.env._standbylist.append(self)
        self.set_mode(mode)
        if self.env._trace:
            if self.env._buffered_trace:
                self.env._buffered_trace = False
            else:
                lineno = self.lineno_txt(add_at=True)
                self.env.print_trace("", "", "standby", merge_blanks(lineno, self._modetxt()))
        self.status._value = standby

    def request(self, *args, **kwargs):
        """
        request from a resource or resources

        Parameters
        ----------
        args : sequence of items where each item can be:
            - resource, where quantity=1, priority=tail of requesters queue
            - tuples/list containing a resource, a quantity and optionally a priority.
                if the priority is not specified, the request
                for the resource be added to the tail of
                the requesters queue |n|

        priority : float
            priority of the fail event|n|
            default: 0 |n|
            if a component has the same time on the event list, this component is sorted according to
            the priority.

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time and priority |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time and priority

        fail_at : float or distribution
            time out |n|
            if the request is not honored before fail_at,
            the request will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the request will not time out. |n|
            if distribution, the distribution is sampled

        fail_delay : float or distribution
            time out |n|
            if the request is not honored before now+fail_delay,
            the request will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the request will not time out. |n|
            if distribution, the distribution is sampled

        oneof : bool
            if oneof is True, just one of the requests has to be met (or condition),
            where honoring follows the order given. |n|
            if oneof is False (default), all requests have to be met to be honored

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        cap_now : bool
            indicator whether times (fail_at, fail_delay) in the past are allowed. If, so now() will be used.
            default: sys.default_cap_now(), usualy False

        Note
        ----
        Not allowed for data components or main.

        If to be used for the current component
        (which will be nearly always the case),
        use ``yield self.request(...)``.

        If the same resource is specified more that once, the quantities are summed |n|

        The requested quantity may exceed the current capacity of a resource |n|

        The parameter failed will be reset by a calling request or wait

        Example
        -------
        ``yield self.request(r1)`` |n|
        --> requests 1 from r1 |n|
        ``yield self.request(r1,r2)`` |n|
        --> requests 1 from r1 and 1 from r2 |n|
        ``yield self.request(r1,(r2,2),(r3,3,100))`` |n|
        --> requests 1 from r1, 2 from r2 and 3 from r3 with priority 100 |n|
        ``yield self.request((r1,1),(r2,2))`` |n|
        --> requests 1 from r1, 2 from r2 |n|
        ``yield self.request(r1, r2, r3, oneoff=True)`` |n|
        --> requests 1 from r1, r2 or r3 |n|
        """
        fail_at = kwargs.pop("fail_at", None)
        fail_delay = kwargs.pop("fail_delay", None)
        mode = kwargs.pop("mode", None)
        urgent = kwargs.pop("urgent", False)
        schedule_priority = kwargs.pop("priority", 0)
        cap_now = kwargs.pop("cap_now", None)

        self.oneof_request = kwargs.pop("oneof", False)
        called_from = kwargs.pop("called_from", "request")
        if kwargs:
            raise TypeError(called_from + "() got an unexpected keyword argument '" + tuple(kwargs)[0] + "'")

        if self.status.value != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()
        if fail_at is None:
            if fail_delay is None:
                scheduled_time = inf
            else:
                if fail_delay == inf:
                    scheduled_time = inf
                else:
                    if callable(fail_delay):
                        fail_delay = fail_delay()
                    scheduled_time = self.env._now + fail_delay
        else:
            if fail_delay is None:
                if callable(fail_at):
                    fail_at = fail_at()
                scheduled_time = fail_at + self.env._offset
            else:
                raise ValueError("both fail_at and fail_delay specified")

        self.set_mode(mode)

        self._failed = False
        for arg in args:
            q = 1
            priority = inf
            if isinstance(arg, Resource):
                r = arg
            elif isinstance(arg, (tuple, list)):
                r = arg[0]
                if len(arg) >= 2:
                    q = arg[1]
                if len(arg) >= 3:
                    priority = arg[2]
            else:
                raise TypeError("incorrect specifier", arg)

            if r._preemptive:
                if len(args) > 1:
                    raise ValueError("preemptive resources do not support multiple resource requests")

            if called_from == "put":
                q = -q

            if q < 0 and not r._anonymous:
                raise ValueError("quantity " + str(q) + " <0")
            if r in self._requests:
                self._requests[r] += q  # is same resource is specified several times, just add them up
            else:
                self._requests[r] = q
            if called_from == "request":
                req_text = "request " + str(q) + " from "
            elif called_from == "put":
                req_text = "put (request) " + str(-q) + " to "
            elif called_from == "get":
                req_text = "get (request) " + str(q) + " from "

            addstring = ""
            addstring += " priority=" + str(priority)

            if self.oneof_request:
                addstring += " (oneof)"

            self.enter_sorted(r._requesters, priority)
            if self.env._trace:
                self.env.print_trace("", "", self.name(), req_text + r.name() + addstring)

            if r._preemptive:
                av = r.available_quantity()
                this_claimers = r.claimers()
                bump_candidates = []
                for c in reversed(r.claimers()):

                    if av >= q:
                        break
                    if priority >= c.priority(this_claimers):
                        break
                    av += c.claimed_quantity(this_claimers)
                    bump_candidates.append(c)
                if av >= 0:
                    for c in bump_candidates:
                        c._release(r, bumped_by=self)
                        c.activate()
        for r, q in self._requests.items():
            if q < r._minq:
                r._minq = q

        self._tryrequest()

        if self._requests:
            self.status._value = requesting
            self._reschedule(scheduled_time, schedule_priority, urgent, "request", cap_now)

    def isbumped(self, resource=None):
        """
        check whether component is bumped from resource

        Parameters
        ----------
        resource : Resource
            resource to be checked
            if omitted, checks whether component belongs to any resource claimers

        Returns
        -------
        True if this component is not in the resource claimers : bool
            False otherwise
        """
        return not self.isclaiming(resource)

    def isclaiming(self, resource=None):
        """
        check whether component is claiming from resource

        Parameters
        ----------
        resource : Resource
            resource to be checked
            if omitted, checks whether component is in any resource claimers

        Returns
        -------
        True if this component is in the resource claimers : bool
            False otherwise
        """
        if resource is None:
            for q in self._qmembers:
                if hasattr(q, "_isclaimers"):
                    return True
            return False
        else:
            return self in resource.claimers()

    def get(self, *args, **kwargs):
        """
        equivalent to request
        """
        return self.request(*args, called_from="get", **kwargs)

    def put(self, *args, **kwargs):
        """
        equivalent to request, but anonymous quantities are negated
        """
        return self.request(*args, called_from="put", **kwargs)

    def honor_all(self):
        for r in self._requests:
            if r._honor_only_first and r._requesters[0] != self:
                return []
            self_prio = self.priority(r._requesters)
            if r._honor_only_highest_priority and self_prio != r._requesters._head.successor.priority:
                return []
            if self._requests[r] > 0:
                if self._requests[r] > (r._capacity - r._claimed_quantity + 1e-8):
                    return []
            else:
                if -self._requests[r] > r._claimed_quantity + 1e-8:
                    return []
        return list(self._requests.keys())

    def honor_any(self):
        for r in self._requests:
            if r._honor_only_first and r._requesters[0] != self:
                continue
            self_prio = self.priority(r._requesters)
            if r._honor_only_highest_priority and self_prio != r._requesters._head.successor.priority:
                continue

            if self._requests[r] > 0:
                if self._requests[r] <= (r._capacity - r._claimed_quantity + 1e-8):
                    return [r]
            else:
                if -self._requests[r] <= r._claimed_quantity + 1e-8:
                    return [r]
        return []

    def _tryrequest(self):  # this is Component._tryrequest
        if self.status.value == interrupted:
            return False

        if self.oneof_request:
            r_honor = self.honor_any()
        else:
            r_honor = self.honor_all()

        if r_honor:
            anonymous_resources = []
            for r in list(self._requests):
                if r._anonymous:
                    anonymous_resources.append(r)
                if r in r_honor:
                    r._claimed_quantity += self._requests[r]
                    this_prio = self.priority(r._requesters)
                    if r._anonymous:
                        prio_trace = ""
                    else:
                        if r in self._claims:
                            self._claims[r] += self._requests[r]
                        else:
                            self._claims[r] = self._requests[r]
                        mx = self._member(r._claimers)
                        if mx is None:
                            self.enter_sorted(r._claimers, this_prio)
                        prio_trace = " priority=" + str(this_prio)
                    r.claimed_quantity.tally(r._claimed_quantity)
                    r.occupancy.tally(0 if r._capacity <= 0 else r._claimed_quantity / r._capacity)
                    r.available_quantity.tally(r._capacity - r._claimed_quantity)
                    if self.env._trace:
                        self.env.print_trace("", "", self.name(), "claim " + str(r._claimed_quantity) + " from " + r.name() + prio_trace)
                self.leave(r._requesters)
                if r._requesters._length == 0:
                    r._minq = inf

            self._requests = collections.OrderedDict()
            self._remove()
            honoredstr = r_honor[0].name() + (len(r_honor) > 1) * " ++"
            self.status._value = scheduled
            self._reschedule(self.env._now, 0, False, "request honor " + honoredstr, False, s0=self.env.last_s0)
            for r in anonymous_resources:
                r._tryrequest()
            return True
        else:
            return False

    def _release(self, r, q=None, s0=None, bumped_by=None):
        if r not in self._claims:
            raise ValueError(self.name() + " not claiming from resource " + r.name())
        if q is None:
            q = self._claims[r]
        if q > self._claims[r]:
            q = self._claims[r]
        r._claimed_quantity -= q
        self._claims[r] -= q
        if self._claims[r] < 1e-8:
            self.leave(r._claimers)
            if r._claimers._length == 0:
                r._claimed_quantity = 0  # to avoid rounding problems
            del self._claims[r]
        r.claimed_quantity.tally(r._claimed_quantity)
        r.occupancy.tally(0 if r._capacity <= 0 else r._claimed_quantity / r._capacity)
        r.available_quantity.tally(r._capacity - r._claimed_quantity)
        extra = " bumped by " + bumped_by.name() if bumped_by else ""
        if self.env._trace:
            if bumped_by:
                self.env.print_trace("", "", self.name(), "bumped from " + r.name() + " by " + bumped_by.name() + " (release " + str(q) + ")", s0=s0)
            else:
                self.env.print_trace("", "", self.name(), "release " + str(q) + " from " + r.name() + extra, s0=s0)
        if not bumped_by:
            r._tryrequest()

    def release(self, *args):
        """
        release a quantity from a resource or resources

        Parameters
        ----------
        args : sequence of items, where each items can be
            - a resources, where quantity=current claimed quantity
            - a tuple/list containing a resource and the quantity to be released

        Note
        ----
        It is not possible to release from an anonymous resource, this way.
        Use Resource.release() in that case.

        Example
        -------
        yield self.request(r1,(r2,2),(r3,3,100)) |n|
        --> requests 1 from r1, 2 from r2 and 3 from r3 with priority 100 |n|

        c1.release |n|
        --> releases 1 from r1, 2 from r2 and 3 from r3 |n|

        yield self.request(r1,(r2,2),(r3,3,100)) |n|
        c1.release((r2,1)) |n|
        --> releases 1 from r2 |n|

        yield self.request(r1,(r2,2),(r3,3,100)) |n|
        c1.release((r2,1),r3) |n|
        --> releases 2 from r2,and 3 from r3
        """
        if args:
            for arg in args:
                q = None
                if isinstance(arg, Resource):
                    r = arg
                elif isinstance(arg, (tuple, list)):
                    r = arg[0]
                    if len(arg) >= 2:
                        q = arg[1]
                else:
                    raise TypeError("incorrect specifier" + arg)
                if r._anonymous:
                    raise ValueError("not possible to release anonymous resources " + r.name())
                self._release(r, q)
        else:
            for r in list(self._claims):
                self._release(r)

    def wait(self, *args, **kwargs):
        """
        wait for any or all of the given state values are met

        Parameters
        ----------
        args : sequence of items, where each item can be
            - a state, where value=True, priority=tail of waiters queue)
            - a tuple/list containing |n|
                state, a value and optionally a priority. |n|
                if the priority is not specified, this component will
                be added to the tail of
                the waiters queue |n|

        priority : float
            priority of the fail event|n|
            default: 0 |n|
            if a component has the same time on the event list, this component is sorted accoring to
            the priority.

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time and priority |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time and priority

        fail_at : float or distribution
            time out |n|
            if the wait is not honored before fail_at,
            the wait will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the wait will not time out. |n|
            if distribution, the distribution is sampled

        fail_delay : float or distribution
            time out |n|
            if the wait is not honored before now+fail_delay,
            the request will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the wait will not time out. |n|
            if distribution, the distribution is sampled

        all : bool
            if False (default), continue, if any of the given state/values is met |n|
            if True, continue if all of the given state/values are met

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        cap_now : bool
            indicator whether times (fail_at, fail_duration) in the past are allowed. If, so now() will be used.
            default: sys.default_cap_now(), usualy False

        Note
        ----
        Not allowed for data components or main.

        If to be used for the current component
        (which will be nearly always the case),
        use ``yield self.wait(...)``.

        It is allowed to wait for more than one value of a state |n|
        the parameter failed will be reset by a calling wait

        If you want to check for all components to meet a value (and clause),
        use Component.wait(..., all=True)

        The value may be specified in three different ways:

        * constant, that value is just compared to state.value() |n|
          yield self.wait((light,"red"))
        * an expression, containg one or more $-signs
          the $ is replaced by state.value(), each time the condition is tested. |n|
          self refers to the component under test, state refers to the state
          under test. |n|
          yield self.wait((light,'$ in ("red","yellow")')) |n|
          yield self.wait((level,"$<30")) |n|
        * a function. In that case the parameter should function that
          should accept three arguments: the value, the component under test and the
          state under test. |n|
          usually the function will be a lambda function, but that's not
          a requirement. |n|
          yield self.wait((light,lambda t, comp, state: t in ("red","yellow"))) |n|
          yield self.wait((level,lambda t, comp, state: t < 30)) |n|

        Example
        -------
        ``yield self.wait(s1)`` |n|
        --> waits for s1.value()==True |n|
        ``yield self.wait(s1,s2)`` |n|
        --> waits for s1.value()==True or s2.value==True |n|
        ``yield self.wait((s1,False,100),(s2,"on"),s3)`` |n|
        --> waits for s1.value()==False or s2.value=="on" or s3.value()==True |n|
        s1 is at the tail of waiters, because of the set priority |n|
        ``yield self.wait(s1,s2,all=True)`` |n|
        --> waits for s1.value()==True and s2.value==True |n|
        """
        fail_at = kwargs.pop("fail_at", None)
        fail_delay = kwargs.pop("fail_delay", None)
        all = kwargs.pop("all", False)
        mode = kwargs.pop("mode", None)
        urgent = kwargs.pop("urgent", False)
        schedule_priority = kwargs.pop("priority", 0)
        cap_now = kwargs.pop("cap_now", None)

        if kwargs:
            raise TypeError("wait() got an unexpected keyword argument '" + tuple(kwargs)[0] + "'")

        if self.status.value != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()

        self._wait_all = all
        self._failed = False

        if fail_at is None:
            if fail_delay is None:
                scheduled_time = inf
            else:
                if fail_delay == inf:
                    scheduled_time = inf
                else:
                    if callable(fail_delay):
                        fail_delay = fail_delay()
                    scheduled_time = self.env._now + fail_delay
        else:
            if fail_delay is None:
                if callable(fail_at):
                    fail_at = fail_at()
                scheduled_time = fail_at + self.env._offset
            else:
                raise ValueError("both fail_at and fail_delay specified")

        self.set_mode(mode)

        for arg in args:
            value = True
            priority = None
            if isinstance(arg, State):
                state = arg
            elif isinstance(arg, (tuple, list)):
                state = arg[0]
                if not isinstance(state, State):
                    raise TypeError("incorrect specifier", arg)
                if len(arg) >= 2:
                    value = arg[1]
                if len(arg) >= 3:
                    priority = arg[2]
                if len(arg) >= 4:
                    raise TypeError("incorrect specifier", arg)
            else:
                raise TypeError("incorrect specifier", arg)

            for (statex, _, _) in self._waits:
                if statex == state:
                    break
            else:
                if priority is None:
                    self.enter(state._waiters)
                else:
                    self.enter_sorted(state._waiters, priority)
            if inspect.isfunction(value):
                self._waits.append((state, value, 2))
            elif "$" in str(value):
                self._waits.append((state, value, 1))
            else:
                self._waits.append((state, value, 0))

        if not self._waits:
            raise TypeError("no states specified")
        self._trywait()

        if self._waits:
            self.status._value = waiting
            self._reschedule(scheduled_time, schedule_priority, urgent, "wait", cap_now)

    def _trywait(self):
        if self.status.value == interrupted:
            return False
        if self._wait_all:
            honored = True
            for state, value, valuetype in self._waits:
                if valuetype == 0:
                    if value != state._value:
                        honored = False
                        break
                elif valuetype == 1:
                    if eval(value.replace("$", "state._value")):
                        honored = False
                        break
                elif valuetype == 2:
                    if not value(state._value, self, state):
                        honored = False
                        break

        else:
            honored = False
            for state, value, valuetype in self._waits:
                if valuetype == 0:
                    if value == state._value:
                        honored = True
                        break
                elif valuetype == 1:
                    if eval(value.replace("$", str(state._value))):
                        honored = True
                        break
                elif valuetype == 2:
                    if value(state._value, self, state):
                        honored = True
                        break

        if honored:
            for s, _, _ in self._waits:
                if self in s._waiters:  # there might be more values for this state
                    self.leave(s._waiters)
            self._waits = []
            self._remove()
            self.status._value = scheduled
            self._reschedule(self.env._now, 0, False, "wait honor", False, s0=self.env.last_s0)

        return honored

    def claimed_quantity(self, resource):
        """
        Parameters
        ----------
        resource : Resoure
            resource to be queried

        Returns
        -------
        the claimed quantity from a resource : float or int
            if the resource is not claimed, 0 will be returned
        """
        return self._claims.get(resource, 0)

    def claimed_resources(self):
        """
        Returns
        -------
        list of claimed resources : list
        """
        return list(self._claims)

    def requested_resources(self):
        """
        Returns
        -------
        list of requested resources : list
        """
        return list(self._requests)

    def requested_quantity(self, resource):
        """
        Parameters
        ----------
        resource : Resoure
            resource to be queried

        Returns
        -------
        the requested (not yet honored) quantity from a resource : float or int
            if there is no request for the resource, 0 will be returned
        """
        return self._requests.get(resource, 0)

    def failed(self):
        """
        Returns
        -------
        True, if the latest request/wait has failed (either by timeout or external) : bool
        False, otherwise
        """
        return self._failed

    def name(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the component
            if omitted, no change

        Returns
        -------
        Name of the component : str

        Note
        ----
        base_name and sequence_number are not affected if the name is changed
        """
        if value is not None:
            self._name = value
        return self._name

    def base_name(self):
        """
        Returns
        -------
        base name of the component (the name used at initialization): str
        """
        return self._base_name

    def sequence_number(self):
        """
        Returns
        -------
        sequence_number of the component : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dotcomma at the end)
            will be numbered)
        """
        return self._sequence_number

    def running_process(self):
        """
        Returns
        -------
        name of the running process : str
            if data component, None
        """
        if self._process is None:
            return None
        else:
            return self._process.__name__

    def remove_animation_children(self):
        """
        removes animation children

        Note
        ----
        Normally, the animation_children are removed automatically upon termination of a component (when it terminates)
        """
        for ao in self._animation_children:
            ao.remove()
        self._animation_children = set()

    def suppress_trace(self, value=None):
        """
        Parameters
        ----------
        value: bool
            new suppress_trace value |n|
            if omitted, no change

        Returns
        -------
        suppress_trace : bool
            components with the suppress_status of True, will be ignored in the trace
        """
        if value is not None:
            self._suppress_trace = value
        return self._suppress_trace

    def suppress_pause_at_step(self, value=None):
        """
        Parameters
        ----------
        value: bool
            new suppress_trace value |n|
            if omitted, no change

        Returns
        -------
        suppress_pause_at_step : bool
            components with the suppress_pause_at_step of True, will be ignored in a step
        """
        if value is not None:
            self._suppress_pause_at_step = value
        return self._suppress_pause_at_step

    def skip_standby(self, value=None):
        """
        Parameters
        ----------
        value: bool
            new skip_standby value |n|
            if omitted, no change

        Returns
        -------
        skip_standby indicator : bool
            components with the skip_standby indicator of True, will not activate standby components after
            the component became current.
        """
        if value is not None:
            self._skip_standby = value
        return self._skip_standby

    def set_mode(self, value=None):
        """
        Parameters
        ----------
        value: any, str recommended
            new mode |n|
            mode_time will be set to now
            if omitted, no change
        """
        if value is not None:
            self._mode_time = self.env._now
            self.mode.tally(value)

    def _modetxt(self):
        if self.mode() == "":
            return ""
        else:
            return "mode=" + str(self.mode())

    def ispassive(self):
        """
        Returns
        -------
        True if status is passive, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        """
        return self.status.value == passive

    def iscurrent(self):
        """
        Returns
        -------
        True if status is current, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        """
        return self.status.value == current

    def isrequesting(self):
        """
        Returns
        -------
        True if status is requesting, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        """
        return self.status.value == requesting

    def iswaiting(self):
        """
        Returns
        -------
        True if status is waiting, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        """
        return self.status.value == waiting

    def isscheduled(self):
        """
        Returns
        -------
        True if status is scheduled, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        """
        return self.status.value == scheduled

    def isstandby(self):
        """
        Returns
        -------
        True if status is standby, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True
        """
        return self.status.value == standby

    def isinterrupted(self):
        """
        Returns
        -------
        True if status is interrupted, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True
        """
        return self.status.value == interrupted

    def isdata(self):
        """
        Returns
        -------
        True if status is data, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        """
        return self.status.value == data

    def queues(self):
        """
        Returns
        -------
        set of queues where the component belongs to : set
        """
        return set(self._qmembers)

    def count(self, q=None):
        """
        queue count

        Parameters
        ----------
        q : Queue
            queue to check or |n|
            if omitted, the number of queues where the component is in

        Returns
        -------
        1 if component is in q, 0 otherwise : int
            |n|
            if q is omitted, the number of queues where the component is in
        """
        if q is None:
            return len(self._qmembers)
        else:
            return 1 if self in q else 0

    def index(self, q):
        """
        Parameters
        ----------
        q : Queue
            queue to be queried

        Returns
        -------
        index of component in q : int
            if component belongs to q |n|
            -1 if component does not belong to q
        """
        m1 = self._member(q)
        if m1 is None:
            return -1
        else:
            mx = q._head.successor
            index = 0
            while mx != m1:
                mx = mx.successor
                index += 1
            return index

    def enter(self, q):
        """
        enters a queue at the tail

        Parameters
        ----------
        q : Queue
            queue to enter

        Note
        ----
        the priority will be set to
        the priority of the tail component of the queue, if any
        or 0 if queue is empty
        """
        self._checknotinqueue(q)
        priority = q._tail.predecessor.priority
        Qmember().insert_in_front_of(q._tail, self, q, priority)
        return self

    def enter_at_head(self, q):
        """
        enters a queue at the head

        Parameters
        ----------
        q : Queue
            queue to enter

        Note
        ----
        the priority will be set to
        the priority of the head component of the queue, if any
        or 0 if queue is empty
        """

        self._checknotinqueue(q)
        priority = q._head.successor.priority
        Qmember().insert_in_front_of(q._head.successor, self, q, priority)
        return self

    def enter_in_front_of(self, q, poscomponent):
        """
        enters a queue in front of a component

        Parameters
        ----------
        q : Queue
            queue to enter

        poscomponent : Component
            component to be entered in front of

        Note
        ----
        the priority will be set to the priority of poscomponent
        """

        self._checknotinqueue(q)
        m2 = poscomponent._checkinqueue(q)
        priority = m2.priority
        Qmember().insert_in_front_of(m2, self, q, priority)
        return self

    def enter_behind(self, q, poscomponent):
        """
        enters a queue behind a component

        Parameters
        ----------
        q : Queue
            queue to enter

        poscomponent : Component
            component to be entered behind

        Note
        ----
        the priority will be set to the priority of poscomponent
        """

        self._checknotinqueue(q)
        m1 = poscomponent._checkinqueue(q)
        priority = m1.priority
        Qmember().insert_in_front_of(m1.successor, self, q, priority)
        return self

    def enter_sorted(self, q, priority):
        """
        enters a queue, according to the priority

        Parameters
        ----------
        q : Queue
            queue to enter

        priority: type that can be compared with other priorities in the queue
            priority in the queue

        Note
        ----
        The component is placed just before the first component with a priority > given priority
        """

        self._checknotinqueue(q)
        m2 = q._head.successor
        while (m2 != q._tail) and (m2.priority <= priority):
            m2 = m2.successor
        Qmember().insert_in_front_of(m2, self, q, priority)
        return self

    def leave(self, q=None):
        """
        leave queue

        Parameters
        ----------
        q : Queue
            queue to leave

        Note
        ----
        statistics are updated accordingly
        """
        if q is None:
            for q in list(self._qmembers):
                if not q._isinternal:
                    self.leave(q)
            return self

        mx = self._checkinqueue(q)
        m1 = mx.predecessor
        m2 = mx.successor
        m1.successor = m2
        m2.predecessor = m1
        mx.component = None
        # signal for components method that member is not in the queue
        q._length -= 1
        del self._qmembers[q]
        if self.env._trace:
            if not q._isinternal:
                self.env.print_trace("", "", self.name(), "leave " + q.name())
        length_of_stay = self.env._now - mx.enter_time
        q.length_of_stay.tally(length_of_stay)
        q.length.tally(q._length)
        q.available_quantity.tally(q.capacity._tally-q._length)
        q.number_of_departures += 1
        return self

    def priority(self, q, priority=None):
        """
        gets/sets the priority of a component in a queue

        Parameters
        ----------
        q : Queue
            queue where the component belongs to

        priority : type that can be compared with other priorities in the queue
            priority in queue |n|
            if omitted, no change

        Returns
        -------
        the priority of the component in the queue : float

        Note
        ----
        if you change the priority, the order of the queue may change
        """

        mx = self._checkinqueue(q)
        if priority is not None:
            if priority != mx.priority:
                # leave.sort is not possible, because statistics will be affected
                mx.predecessor.successor = mx.successor
                mx.successor.predecessor = mx.predecessor

                m2 = q._head.successor
                while (m2 != q._tail) and (m2.priority <= priority):
                    m2 = m2.successor

                m1 = m2.predecessor
                m1.successor = mx
                m2.predecessor = mx
                mx.predecessor = m1
                mx.successor = m2
                mx.priority = priority
                for iter in q._iter_touched:
                    q._iter_touched[iter] = True
        return mx.priority

    def successor(self, q):
        """
        Parameters
        ----------
        q : Queue
            queue where the component belongs to

        Returns
        -------
        the successor of the component in the queue: Component
            if component is not at the tail. |n|
            returns None if component is at the tail.
        """

        mx = self._checkinqueue(q)
        return mx.successor.component

    def predecessor(self, q):
        """
        Parameters
        ----------
        q : Queue
            queue where the component belongs to

        Returns : Component
            predecessor of the component in the queue
            if component is not at the head. |n|
            returns None if component is at the head.
        """

        mx = self._checkinqueue(q)
        return mx.predecessor.component

    def enter_time(self, q):
        """
        Parameters
        ----------
        q : Queue
            queue where component belongs to

        Returns
        -------
        time the component entered the queue : float
        """
        mx = self._checkinqueue(q)
        return mx.enter_time - self.env._offset

    def creation_time(self):
        """
        Returns
        -------
        time the component was created : float
        """
        return self._creation_time - self.env._offset

    def scheduled_time(self):
        """
        Returns
        -------
        time the component scheduled for, if it is scheduled : float
            returns inf otherwise
        """
        return self._scheduled_time - self.env._offset

    def scheduled_priority(self):
        """
        Returns
        -------
        priority the component is scheduled with : float
            returns None otherwise

        Note
        ----
        The method has to traverse the event list, so performance may be an issue.
        """
        for t, priority, seq, component in self.env._event_list:
            if component is self:
                return priority
        return None

    def remaining_duration(self, value=None, priority=0, urgent=False):
        """
        Parameters
        ----------
        value : float
            set the remaining_duration |n|
            The action depends on the status where the component is in: |n|
            - passive: the remaining duration is update according to the given value |n|
            - standby and current: not allowed |n|
            - scheduled: the component is rescheduled according to the given value |n|
            - waiting or requesting: the fail_at is set according to the given value |n|
            - interrupted: the remaining_duration is updated according to the given value |n|

        priority : float
            priority |n|
            default: 0 |n|
            if a component has the same time on the event list, this component is sorted accoring to
            the priority.

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time and priority |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time and priority

        Returns
        -------
        remaining duration : float
            if passive, remaining time at time of passivate |n|
            if scheduled, remaing time till scheduled time |n|
            if requesting or waiting, time till fail_at time |n|
            else: 0

        Note
        ----
        This method is useful for interrupting a process and then resuming it,
        after some (breakdown) time
        """
        if value is not None:
            if self.status.value in (passive, interrupted):
                self._remaining_duration = value
            elif self.status.value == current:
                raise ValueError("setting remaining_duration not allowed for current component (" + self.name() + ")")
            elif self.status.value == standby:
                raise ValueError("setting remaining_duration not allowed for standby component (" + self.name() + ")")
            else:
                self._remove()
                self._reschedule(value + self.env._now, priority, urgent, "set remaining_duration", False, extra="")

        if self.status.value in (passive, interrupted):
            return self._remaining_duration
        elif self.status.value in (scheduled, waiting, requesting):
            return self._scheduled_time - self.env._now
        else:
            return 0

    def mode_time(self):
        """
        Returns
        -------
        time the component got it's latest mode : float
            For a new component this is
            the time the component was created. |n|
            this function is particularly useful for animations.
        """
        return self._mode_time - self.env._offset

    def status(self):
        """
        returns the status of a component

        possible values are
            - data
            - passive
            - scheduled
            - requesting
            - waiting
            - current
            - standby
            - interrupted
        """
        return self.status.value

    def interrupted_status(self):
        """
        returns the original status of an interrupted component

        possible values are
            - passive
            - scheduled
            - requesting
            - waiting
            - standby
        """
        if self.status.value != interrupted:
            raise ValueError(self.name() + "not interrupted")

        return self._interrupted_status

    def interrupt_level(self):
        """
        returns interrupt level of an interrupted component |n|
        non interrupted components return 0
        """
        if self.status.value == interrupted:
            return self._interrupt_level
        else:
            return 0

    def _member(self, q):
        return self._qmembers.get(q, None)

    def _checknotinqueue(self, q):
        mx = self._member(q)
        if mx is None:
            pass
        else:
            raise ValueError(self.name() + " is already member of " + q.name())

    def _checkinqueue(self, q):
        mx = self._member(q)
        if mx is None:
            raise ValueError(self.name() + " is not member of " + q.name())
        else:
            return mx

    def _checkisnotdata(self):
        if self.status.value == data:
            raise ValueError(self.name() + " data component not allowed")

    def _checkisnotmain(self):
        if self == self.env._main:
            raise ValueError(self.name() + " main component not allowed")

    def lineno_txt(self, add_at=False):
        if self.env._suppress_trace_linenumbers:
            return ""
        if self.overridden_lineno:
            return ""

        plus = "+"
        if self == self.env._main:
            frame = self.frame
        else:
            if self.isdata():
                return "N/A"
            if self._process_isgenerator:
                frame = self._process.gi_frame
                if frame.f_lasti == -1:  # checks whether generator is created
                    plus = " "
            else:
                gs = inspect.getsourcelines(self._process)
                s0 = self.env.filename_lineno_to_str(self._process.__code__.co_filename, gs[1]) + " "
                return f"{'@' if add_at else ''}{s0}"
        return f"{'@' if add_at else ''}{self.env._frame_to_lineno(frame)}{plus}"

    def line_number(self):
        """
        current line number of the process

        Returns
        -------
        Current line number : str
            for data components, "" will be returned
        """
        save_suppress_trace_linenumbers = self.env._suppress_trace_linenumbers
        self.env._suppress_trace_linenumbers = False
        s = self.lineno_txt().strip()
        self.env._suppress_trace_linenumbers = save_suppress_trace_linenumbers
        return s


class ComponentGenerator(Component):
    """Component generator object

    A component generator can be used to genetate components |n|
    There are two ways of generating components: |n|
    - according to a given inter arrival time (iat) value or distribution
    - random spread over a given time interval

    Parameters
    ----------
    component_class : callable, usually a subclass of Component or Pdf or Cdf distribution
        the type of components to be generated |n|
        in case of a distribution, the Pdf or Cdf should return a callable

    generator_name : str
        name of the component generator. |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the name of the component_class, padded with '.generator'

    at : float or distribution
        time where the generator starts time |n|
        if omitted, now is used |n|
        if distribution, the distribution is sampled

    delay : float or distribution
        delay where the generator starts (at = now + delay) |n|
        if omitted, no delay |n|
        if distribution, the distribution is sampled

    till : float or distribution
        time up to which components should be generated |n|
        if omitted, no end |n|
        if distribution, the distribution is sampled

    duration : float or distribution
        duration to which components should be generated (till = now + duration) |n|
        if omitted, no end |n|
        if distribution, the distribution is sampled

    number : int or distribution
        (maximum) number of components to be generated |n|
        if distribution, the distribution is sampled

    iat : float or distribution
        inter arrival time (distribution). |n|
        if None (default), a random spread over the interval (at, till) will be used |n|

    force_at : bool
        for iat generation: |n|
            if False (default), the first component will be generated at time = at + sample from the iat |n|
            if True, the first component will be generated at time = at |n|
        for random spread generation: |n|
            if False (default), no force for time = at |n|
            if True, force the first generation at time = at |n|

    force_till : bool
        only possible for random spread generation: |n|
        if False (default), no force for time = till |n|
        if True, force the last generated component at time = till |n|

    disturbance : callable (usually a distribution)
        for each component to be generated, the disturbance call (sampling) is added
        to the actual generation time. |n|
        disturbance may only be used together with iat. The force_at parameter is not
        allowed in that case.

    suppress_trace : bool
        suppress_trace indicator |n|
        if True, the component generator events will be excluded from the trace |n|
        If False (default), the component generator will be traced |n|
        Can be queried or set later with the suppress_trace method.

    suppress_pause_at_step : bool
        suppress_pause_at_step indicator |n|
        if True, if this component generator becomes current, do not pause when stepping |n|
        If False (default), the component generator will be paused when stepping |n|
        Can be queried or set later with the suppress_pause_at_step method.

    cap_now : bool
        indicator whether times (activation) in the past are allowed. If, so now() will be used.
        default: sys.default_cap_now(), usualy False

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    For iat distributions: if till/duration and number are specified, the generation stops whichever condition
    comes first.
    """

    def __init__(
        self,
        component_class,
        generator_name=None,
        at=None,
        delay=None,
        till=None,
        duration=None,
        number=None,
        iat=None,
        force_at=False,
        force_till=False,
        suppress_trace=False,
        suppress_pause_at_step=False,
        disturbance=None,
        #        cap_now=None,
        env=None,
        **kwargs,
    ):
        if generator_name is None:
            if inspect.isclass(component_class) and issubclass(component_class, Component):
                generator_name = str(component_class).split(".")[-1][:-2] + ".generator."
            elif isinstance(component_class, _Distribution):
                generator_name = str(component_class) + ".generator."
            else:
                generator_name = component_class.__name__ + ".generator."
        if env is None:
            env = g.default_env
        self.overridden_lineno = env._frame_to_lineno(_get_caller_frame())

        if not callable(component_class):
            raise ValueError("component_class must be a callable")
        self.component_class = component_class
        self.iat = iat
        self.disturbance = disturbance
        self.force_at = force_at

        if disturbance:  # falsy values are interpreted as no disturbance
            if iat is None:
                raise ValueError("disturbance can only be used with an iat")
            if not issubclass(component_class, Component):
                raise ValueError("component_class haas to be a Component subclass if disturbance is specified.")
        if callable(at):
            at = at()
        if callable(delay):
            delay = delay()
        if delay is not None and at is not None:
            raise ValueError("delay and at specified.")
        if delay is None:
            delay = 0
        at = env._now + delay if at is None else at + env._offset
        if callable(till):
            till = till()
        if callable(duration):
            duration = duration()
        if till is None:
            if duration is None:
                self.till = inf
            else:
                self.till = at + duration
        else:
            if duration is None:
                self.till = till + env._offset
            else:
                raise ValueError("till and duration specified.")
        if callable(number):
            self.number = int(number())
        else:
            self.number = inf if number is None else int(number)
        if self.till < at:
            raise ValueError("at > till")
        if self.number < 0:
            raise ValueError("number < 0")
        if self.number < 1:
            at = None
            process = ""
        else:
            if self.iat is None:
                if till == inf or self.number == inf:
                    raise ValueError("iat not specified --> till and number need to be specified")
                if disturbance is not None:
                    raise ValueError("iat not specified --> disturbance not allowed")

                samples = sorted([Uniform(at, till)() for _ in range(self.number)])
                if force_at or force_till:
                    if number == 1:
                        if force_at and force_till:
                            raise ValueError("force_at and force_till does not allow number=1")
                        samples = [at] if force_at else [till]
                    else:
                        v_at = at if force_at else samples[0]
                        v_till = till if force_till else samples[-1]
                        min_sample = samples[0]
                        max_sample = samples[-1]
                        samples = [interpolate(sample, min_sample, max_sample, v_at, v_till) for sample in samples]
                self.intervals = [t1 - t0 for t0, t1 in zip([0] + samples, samples)]
                at = 0  # self.intervals.pop(0)
                process = "do_spread"
            else:
                if force_till:
                    raise ValueError("force_till is not allowed for iat generators")
                if not force_at:
                    if not self.disturbance:
                        if callable(self.iat):
                            at += self.iat()
                        else:
                            at += self.iat
                if at > self.till:
                    at = self.till
                    process = "do_finalize"
                else:
                    if self.disturbance:
                        process = "do_iat_disturbance"
                    else:
                        process = "do_iat"
        self.kwargs = kwargs

        super().__init__(name=generator_name, env=env, process=process, at=at, suppress_trace=suppress_trace, suppress_pause_at_step=suppress_pause_at_step)

    def do_spread(self):
        for interval in self.intervals:
            yield self.hold(interval)
            if isinstance(self.component_class, _Distribution):
                self.component_class()(**self.kwargs)
            else:
                self.component_class(**self.kwargs)
        self.env.print_trace("", "", "all components generated")

    def do_iat(self):
        n = 0
        while True:
            if isinstance(self.component_class, _Distribution):
                self.component_class()(**self.kwargs)
            else:
                self.component_class(**self.kwargs)
            n += 1
            if n >= self.number:
                self.env.print_trace("", "", f"{n} components generated")
                return
            if callable(self.iat):
                t = self.env._now + self.iat()
            else:
                t = self.env._now + self.iat
            if t > self.till:
                yield self.activate(process="do_finalize", at=self.till)

            yield self.hold(till=t)

    def do_iat_disturbance(self):
        n = 0
        while True:
            if callable(self.iat):
                iat = self.iat()
            else:
                iat = self.iat
            if callable(self.disturbance):
                disturbance = self.disturbance()
            else:
                disturbance = self.disturbance
            if self.force_at:
                at = self.env._now + disturbance
            else:
                at = self.env._now + iat + disturbance
            if at > self.till:
                yield self.activate(process="do_finalize", at=self.till)
            if isinstance(self.component_class, _Distribution):
                component_class = self.component_class()
            else:
                component_class = self.component_class
            component_class(at=at, **self.kwargs)
            n += 1
            if n >= self.number:
                self.env.print_trace("", "", str(n) + " components generated")
                return
            t = self.env._now + iat

            yield self.hold(till=t)

    def do_finalize(self):
        self.env.print_trace("", "", "till reached")

    def print_info(self, as_str=False, file=None):
        """
        prints information about the component generator

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append(object_to_str(self) + " " + hex(id(self)))
        result.append("  name=" + self.name())

        result.append("  class of components=" + str(self.component_class).split(".")[-1][:-2])
        result.append("  iat=" + repr(self.iat))
        result.append("  suppress_trace=" + str(self._suppress_trace))
        result.append("  suppress_pause_at_step=" + str(self._suppress_pause_at_step))
        result.append("  status=" + self.status.value)
        result.append("  mode=" + self._modetxt().strip())
        result.append("  mode_time=" + self.env.time_to_str(self.mode_time()))
        result.append("  creation_time=" + self.env.time_to_str(self.creation_time()))
        result.append("  scheduled_time=" + self.env.time_to_str(self.scheduled_time()))
        return return_or_print(result, as_str, file)


class _BlindVideoMaker(Component):
    def process(self):
        while True:
            self.env._t = self.env._now
            self.env.animation_pre_tick_sys(self.env.t())  # required to update sys objects, like AnimateQueue
            if self.env._animate3d:
                if not self.env._gl_initialized:
                    self.env.animation3d_init()

                self.env._exclude_from_animation = "*"  # makes that both video and non video over2d animation objects are shown

                an_objects3d = sorted(self.env.an_objects3d, key=lambda obj: (obj.layer(self.env._t), obj.sequence))
                for an in an_objects3d:
                    if an.keep(self.env._t):
                        if an.visible(self.env._t):
                            an.draw(self.env._t)
                    else:
                        an.remove()
                self.env._exclude_from_animation = "only in video"

            self.env._save_frame()
            yield self.hold(self.env._speed / self.env._fps)


class Random(random.Random):
    """
    defines a randomstream, equivalent to random.Random()

    Parameters
    ----------
    seed : any hashable
        default: None
    """

    def __init__(self, seed=None):
        random.Random.__init__(self, seed)


class _Distribution:
    def bounded_sample(self, lowerbound=None, upperbound=None, fail_value=None, number_of_retries=None, include_lowerbound=True, include_upperbound=True):
        """
        Parameters
        ----------
        lowerbound : float
            sample values < lowerbound will be rejected (at most 100 retries) |n|
            if omitted, no lowerbound check

        upperbound : float
            sample values > upperbound will be rejected (at most 100 retries) |n|
            if omitted, no upperbound check

        fail_value : float
            value to be used if. after number_of_tries retries, sample is still not within bounds |n|
            default: lowerbound, if specified, otherwise upperbound

        number_of_tries : int
            number of tries before fail_value is returned |n|
            default: 100

        include_lowerbound : bool
            if True (default), the lowerbound may be included.
            if False, the lowerbound will be excluded.

        include_upperbound : bool
            if True (default), the upperbound may be included.
            if False, the upperbound will be excluded.

        Returns
        -------
        Bounded sample of a distribution : depending on distribution type (usually float)

        Note
        ----
        If, after number_of_tries retries, the sampled value is still not within the given bounds,
        fail_value  will be returned |n|
        Samples that cannot be converted (only possible with Pdf and CumPdf) to float
        are assumed to be within the bounds.
        """
        return Bounded(self, lowerbound, upperbound, fail_value, number_of_retries, include_lowerbound, include_upperbound).sample()

    def __call__(self, *args, **kwargs):
        return self.sample(*args, **kwargs)

    def __pos__(self):
        return _Expression(self, 0, operator.add)

    def __neg__(self):
        return _Expression(0, self, operator.sub)

    def __add__(self, other):
        return _Expression(self, other, operator.add)

    def __radd__(self, other):
        return _Expression(other, self, operator.add)

    def __sub__(self, other):
        return _Expression(self, other, operator.sub)

    def __rsub__(self, other):
        return _Expression(other, self, operator.sub)

    def __mul__(self, other):
        return _Expression(self, other, operator.mul)

    def __rmul__(self, other):
        return _Expression(other, self, operator.mul)

    def __truediv__(self, other):
        return _Expression(self, other, operator.truediv)

    def __rtruediv__(self, other):
        return _Expression(other, self, operator.truediv)

    def __floordiv__(self, other):
        return _Expression(self, other, operator.floordiv)

    def __rfloordiv__(self, other):
        return _Expression(other, self, operator.floordiv)

    def __pow__(self, other):
        return _Expression(self, other, operator.pow)

    def __rpow__(self, other):
        return _Expression(other, self, operator.pow)

    def register_time_unit(self, time_unit, env):
        self.time_unit = "" if time_unit is None else time_unit
        self.time_unit_factor = _time_unit_factor(time_unit, env)


class _Expression(_Distribution):
    """
    expression distribution

    This class is only created when using an expression with one ore more distributions.

    Note
    ----
    The randomstream of the distribution(s) in the expression are used.
    """

    def __init__(self, dis0, dis1, op):
        if isinstance(dis0, Constant):
            self.dis0 = dis0._mean
        else:
            self.dis0 = dis0
        if isinstance(dis1, Constant):
            self.dis1 = dis1._mean
        else:
            self.dis1 = dis1
        self.op = op

    def sample(self):
        """
        Returns
        -------
        Sample of the expression of distribution(s) : float
        """
        if isinstance(self.dis0, _Distribution):
            v0 = self.dis0.sample()
        else:
            v0 = self.dis0
        if isinstance(self.dis1, _Distribution):
            v1 = self.dis1.sample()
        else:
            v1 = self.dis1
        return self.op(v0, v1)

    def mean(self):
        """
        Returns
        -------
        Mean of the expression of distribution(s) : float
            returns nan if mean can't be calculated
        """
        if isinstance(self.dis0, _Distribution):
            m0 = self.dis0.mean()
        else:
            m0 = self.dis0
        if isinstance(self.dis1, _Distribution):
            m1 = self.dis1.mean()
        else:
            m1 = self.dis1

        if self.op == operator.add:
            return m0 + m1

        if self.op == operator.sub:
            return m0 - m1

        if self.op == operator.mul:
            if isinstance(self.dis0, _Distribution) and isinstance(self.dis1, _Distribution):
                return nan
            else:
                return m0 * m1

        if self.op == operator.truediv:
            if isinstance(self.dis1, _Distribution):
                return nan
            else:
                return m0 / m1

        if self.op == operator.floordiv:
            return nan

        if self.op == operator.pow:
            return nan

    def __repr__(self):
        return "_Expression"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the expression of distribution(s)

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("_Expression " + hex(id(self)))
        result.append("  mean=" + str(self.mean()))
        return return_or_print(result, as_str, file)


class Map(_Distribution):
    """
    Parameters
    ----------
    dis : distribution
        distribution to be mapped

    function : function
        function to be applied on each sampled value

    Examples
    --------
    d = sim.Map(sim.Normal(10,3), lambda x: x if x > 0 else 0)  # map negative samples to zero
    d = sim.Map(sim.Uniform(1,7), int)  # die simulator
    """

    def __init__(self, dis, function):
        self.dis = dis
        self.function = function

    def sample(self):
        sample = self.dis.sample()
        return self.function(sample)

    def mean(self):
        return nan

    def __repr__(self):
        return "Map " + self.dis.__repr__()


class Bounded(_Distribution):
    """
    Parameters
    ----------
    dis : distribution
        distribution to be bounded

    lowerbound : float
        sample values < lowerbound will be rejected (at most 100 retries) |n|
        if omitted, no lowerbound check

    upperbound : float
        sample values > upperbound will be rejected (at most 100 retries) |n|
        if omitted, no upperbound check

    fail_value : float
        value to be used if. after number_of_tries retries, sample is still not within bounds |n|
        default: lowerbound, if specified, otherwise upperbound

    number_of_tries : int
        number of tries before fail_value is returned |n|
        default: 100

    include_lowerbound : bool
        if True (default), the lowerbound may be included.
        if False, the lowerbound will be excluded.

    include_upperbound : bool
        if True (default), the upperbound may be included.
        if False, the upperbound will be excluded.

    time_unit : str
        specifies the time unit of the lowerbound or upperbound|n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    Note
    ----
    If, after number_of_tries retries, the sampled value is still not within the given bounds,
    fail_value  will be returned |n|
    Samples that cannot be converted to float (only possible with Pdf and CumPdf)
    are assumed to be within the bounds.
    """

    def __init__(
        self,
        dis,
        lowerbound=None,
        upperbound=None,
        fail_value=None,
        number_of_retries=None,
        include_lowerbound=None,
        include_upperbound=None,
        time_unit=None,
        env=None,
    ):
        self.register_time_unit(time_unit, env)
        self.lowerbound = -inf if lowerbound is None else lowerbound * self.time_unit_factor
        self.upperbound = inf if upperbound is None else upperbound * self.time_unit_factor

        if self.lowerbound > self.upperbound:
            raise ValueError("lowerbound > upperbound")

        if fail_value is None:
            self.fail_value = self.upperbound if self.lowerbound == -inf else self.lowerbound
        else:
            self.fail_value = fail_value

        self.dis = dis
        self.lowerbound_op = operator.ge if include_lowerbound else operator.gt
        self.upperbound_op = operator.le if include_upperbound else operator.lt
        self.number_of_retries = 100 if number_of_retries is None else number_of_retries

    def sample(self):
        if (self.lowerbound == -inf) and (self.upperbound == inf):
            return self.dis.sample()
        for _ in range(self.number_of_retries):
            sample = self.dis.sample()
            try:
                samplefloat = float(sample)
            except (ValueError, TypeError):
                return sample  # a value that cannot be converted to a float is sampled is assumed to be correct

            if self.lowerbound_op(samplefloat, self.lowerbound) and self.upperbound_op(samplefloat, self.upperbound):
                return sample

        return self.fail_value

    def mean(self):
        """
        Returns
        -------
        Mean of the expression of bounded distribution : float
            unless no bounds are specified, returns nan
        """
        if (self.lowerbound == -inf) and (self.upperbound == inf):
            return self.dis.mean()
        return nan

    def __repr__(self):
        return "Bounded " + self.dis.__repr__()

    def print_info(self, as_str=False, file=None):
        """
        prints information about the expression of distribution(s)

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Bounded " + self.dis.__repr__() + " " + hex(id(self)))
        result.append("  mean=" + str(self.mean()))
        return return_or_print(result, as_str, file)


class Exponential(_Distribution):
    """
    exponential distribution

    Parameters
    ----------
    mean : float
        mean of the distribtion (beta)|n|
        if omitted, the rate is used |n|
        must be >0

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    rate : float
        rate of the distribution (lambda)|n|
        if omitted, the mean is used |n|
        must be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used

    Note
    ----
    Either mean or rate has to be specified, not both
    """

    def __init__(self, mean=None, time_unit=None, rate=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        if mean is None:
            if rate is None:
                raise TypeError("neither mean nor rate are specified")
            else:
                if rate <= 0:
                    raise ValueError("rate<=0")
                self._mean = 1 / rate
        else:
            if rate is None:
                if mean <= 0:
                    raise ValueError("mean<=0")
                self._mean = mean
            else:
                raise TypeError("both mean and rate are specified")

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

    def __repr__(self):
        return "Exponential"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Exponential distribution " + hex(id(self)))
        result.append("  mean=" + str(self._mean) + " " + self.time_unit)
        result.append("  rate (lambda)=" + str(1 / self._mean) + (" " if self.time_unit == "" else " /" + self.time_unit))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : float
        """
        return self.randomstream.expovariate(1 / (self._mean)) * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean * self.time_unit_factor


class Normal(_Distribution):
    """
    normal distribution

    Parameters
    ----------
    mean : float
        mean of the distribution

    standard_deviation : float
        standard deviation of the distribution |n|
        if omitted, coefficient_of_variation, is used to specify the variation
        if neither standard_devation nor coefficient_of_variation is given, 0 is used,
        thus effectively a contant distribution |n|
        must be >=0

    coefficient_of_variation : float
        coefficient of variation of the distribution |n|
        if omitted, standard_deviation is used to specify variation |n|
        the resulting standard_deviation must be >=0

    use_gauss : bool
        if False (default), use the random.normalvariate method |n|
        if True, use the random.gauss method |n|
        the documentation for random states that the gauss method should be slightly faster,
        although that statement is doubtful.

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, mean, standard_deviation=None, time_unit=None, coefficient_of_variation=None, use_gauss=False, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._use_gauss = use_gauss
        self._mean = mean
        if standard_deviation is None:
            if coefficient_of_variation is None:
                self._standard_deviation = 0
            else:
                if mean == 0:
                    raise ValueError("coefficient_of_variation not allowed with mean = 0")
                self._standard_deviation = coefficient_of_variation * mean
        else:
            if coefficient_of_variation is None:
                self._standard_deviation = standard_deviation
            else:
                raise TypeError("both standard_deviation and coefficient_of_variation specified")
        if self._standard_deviation < 0:
            raise ValueError("standard_deviation < 0")
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

    def __repr__(self):
        return "Normal"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Normal distribution " + hex(id(self)))
        result.append("  mean=" + str(self._mean) + " " + self.time_unit)
        result.append("  standard_deviation=" + str(self._standard_deviation) + " " + self.time_unit)
        if self._mean == 0:
            result.append("  coefficient of variation= N/A")
        else:
            result.append("  coefficient_of_variation=" + str(self._standard_deviation / self._mean))
        if self._use_gauss:
            result.append("  use_gauss=True")
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : float
        """
        if self._use_gauss:
            return self.randomstream.gauss(self._mean, self._standard_deviation) * self.time_unit_factor
        else:
            return self.randomstream.normalvariate(self._mean, self._standard_deviation) * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean * self.time_unit_factor


class IntUniform(_Distribution):
    """
    integer uniform distribution, i.e. sample integer values between lowerbound and upperbound (inclusive)

    Parameters
    ----------
    lowerbound : int
        lowerbound of the distribution

    upperbound : int
        upperbound of the distribution |n|
        if omitted, lowerbound will be used |n|
        must be >= lowerbound

    time_unit : str
        specifies the time unit. the sampled integer value will be multiplied by the appropriate factor |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used

    Note
    ----
    In contrast to range, the upperbound is included.

    Example
    -------
    die = sim.IntUniform(1,6)
    for _ in range(10):
        print (die())

    This will print 10 throws of a die.
    """

    def __init__(self, lowerbound, upperbound=None, randomstream=None, time_unit=None, env=None):
        self.register_time_unit(time_unit, env)
        self._lowerbound = lowerbound
        if upperbound is None:
            self._upperbound = lowerbound
        else:
            self._upperbound = upperbound
        if self._lowerbound > self._upperbound:
            raise ValueError("lowerbound>upperbound")
        if self._lowerbound != int(self._lowerbound):
            raise TypeError("lowerbound not integer")
        if self._upperbound != int(self._upperbound):
            raise TypeError("upperbound not integer")

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = (self._lowerbound + self._upperbound) / 2

    def __repr__(self):
        return "IntUniform"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("IntUniform distribution " + hex(id(self)))
        result.append("  lowerbound=" + str(self._lowerbound) + " " + self.time_unit)
        result.append("  upperbound=" + str(self._upperbound) + " " + self.time_unit)
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution: int
        """
        return self.randomstream.randint(self._lowerbound, self._upperbound) * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean * self.time_unit_factor


class Uniform(_Distribution):
    """
    uniform distribution

    Parameters
    ----------
    lowerbound : float
        lowerbound of the distribution

    upperbound : float
        upperbound of the distribution |n|
        if omitted, lowerbound will be used |n|
        must be >= lowerbound

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, lowerbound, upperbound=None, time_unit=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._lowerbound = lowerbound
        if upperbound is None:
            self._upperbound = lowerbound
        else:
            self._upperbound = upperbound
        if self._lowerbound > self._upperbound:
            raise ValueError("lowerbound>upperbound")
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = (self._lowerbound + self._upperbound) / 2

    def __repr__(self):
        return "Uniform"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Uniform distribution " + hex(id(self)))
        result.append("  lowerbound=" + str(self._lowerbound) + " " + self.time_unit)
        result.append("  upperbound=" + str(self._upperbound) + " " + self.time_unit)
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution: float
        """
        return self.randomstream.uniform(self._lowerbound, self._upperbound) * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean * self.time_unit_factor


class Triangular(_Distribution):
    """
    triangular distribution

    Parameters
    ----------
    low : float
        lowerbound of the distribution

    high : float
        upperbound of the distribution |n|
        if omitted, low will be used, thus effectively a constant distribution |n|
        high must be >= low

    mode : float
        mode of the distribution |n|
        if omitted, the average of low and high will be used, thus a symmetric triangular distribution |n|
        mode must be between low and high

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, low, high=None, mode=None, time_unit=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._low = low
        if high is None:
            self._high = low
        else:
            self._high = high
        if mode is None:
            self._mode = (self._high + self._low) / 2
        else:
            self._mode = mode
        if self._low > self._high:
            raise ValueError("low>high")
        if self._low > self._mode:
            raise ValueError("low>mode")
        if self._high < self._mode:
            raise ValueError("high<mode")
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = (self._low + self._mode + self._high) / 3

    def __repr__(self):
        return "Triangular"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Triangular distribution " + hex(id(self)))
        result.append("  low=" + str(self._low) + " " + self.time_unit)
        result.append("  high=" + str(self._high) + " " + self.time_unit)
        result.append("  mode=" + str(self._mode) + " " + self.time_unit)
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribtion : float
        """
        return self.randomstream.triangular(self._low, self._high, self._mode) * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean * self.time_unit_factor


class Constant(_Distribution):
    """
    constant distribution

    Parameters
    ----------
    value : float
        value to be returned in sample

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed |n|
        Note that this is only for compatibility with other distributions

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, value, time_unit=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._value = value
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = value
        self._mean *= self.time_unit_factor

    def __repr__(self):
        return "Constant"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Constant distribution " + hex(id(self)))
        result.append("  value=" + str(self._value) + " " + self.time_unit)
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        sample of the distribution (= the specified constant) : float
        """
        return self._value * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        mean of the distribution (= the specified constant) : float
        """
        return self._mean * self.time_unit_factor


class Poisson(_Distribution):
    """
    Poisson distribution

    Parameters
    ----------
    mean: float
        mean (lambda) of the distribution

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    Note
    ----
    The run time of this function increases when mean (lambda) increases. |n|
    It is not recommended to use mean (lambda) > 100
    """

    def __init__(self, mean, randomstream=None):
        if mean <= 0:
            raise ValueError("mean (lambda) <=0")

        self._mean = mean

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

    def __repr__(self):
        return "Poisson"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Poisson distribution " + hex(id(self)))
        result.append("  mean (lambda)" + str(self._lambda_))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : int
        """
        t = math.exp(-self._mean)
        s = t
        k = 0

        u = self.randomstream.random()
        last_s = inf
        while s < u:
            k += 1
            t *= self._mean / k
            s += t
            if last_s == s:  # avoid infinite loops
                break
            last_s = s
        return k

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean


class Weibull(_Distribution):
    """
    weibull distribution

    Parameters
    ----------
    scale: float
        scale of the distribution (alpha or k)

    shape: float
        shape of the distribution (beta or lambda)|n|
        should be >0

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, scale, shape, time_unit=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._scale = scale
        if shape <= 0:
            raise ValueError("shape<=0")

        self._shape = shape
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = self._scale * math.gamma((1 / self._shape) + 1)

    def __repr__(self):
        return "Weibull"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Weibull distribution " + hex(id(self)))
        result.append("  scale (alpha or k)=" + str(self._scale) + " " + self.time_unit)
        result.append("  shape (beta or lambda)=" + str(self._shape))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : float
        """
        return self.randomstream.weibullvariate(self._scale, self._shape) * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean * self.time_unit_factor


class Gamma(_Distribution):
    """
    gamma distribution

    Parameters
    ----------
    shape: float
        shape of the distribution (k) |n|
        should be >0

    scale: float
        scale of the distribution (teta) |n|
        should be >0

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    rate : float
        rate of the distribution (beta) |n|
        should be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed


    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used

    Note
    ----
    Either scale or rate has to be specified, not both.
    """

    def __init__(self, shape, scale=None, time_unit=None, rate=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        if shape <= 0:
            raise ValueError("shape<=0")
        self._shape = shape
        if rate is None:
            if scale is None:
                raise TypeError("neither scale nor rate specified")
            else:
                if scale <= 0:
                    raise ValueError("scale<=0")
                self._scale = scale
        else:
            if scale is None:
                if rate <= 0:
                    raise ValueError("rate<=0")
                self._scale = 1 / rate
            else:
                raise TypeError("both scale and rate specified")

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        self._mean = self._shape * self._scale

    def __repr__(self):
        return "Gamma"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Gamma distribution " + hex(id(self)))
        result.append("  shape (k)=" + str(self._shape))
        result.append("  scale (teta)=" + str(self._scale) + " " + self.time_unit)
        result.append("  rate (beta)=" + str(1 / self._scale) + ("" if self.time_unit == "" else " /" + self.time_unit))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : float
        """
        return self.randomstream.gammavariate(self._shape, self._scale) * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean * self.time_unit_factor


class Beta(_Distribution):
    """
    beta distribution

    Parameters
    ----------
    alpha: float
        alpha shape of the distribution |n|
        should be >0

    beta: float
        beta shape of the distribution |n|
        should be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    """

    def __init__(self, alpha, beta, randomstream=None):
        if alpha <= 0:
            raise ValueError("alpha<=0")
        self._alpha = alpha
        if beta <= 0:
            raise ValueError("beta<>=0")
        self._beta = beta

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        self._mean = self._alpha / (self._alpha + self._beta)

    def __repr__(self):
        return "Beta"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Beta distribution " + hex(id(self)))
        result.append("  alpha=" + str(self._alpha))
        result.append("  beta=" + str(self._beta))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : float
        """
        return self.randomstream.betavariate(self._alpha, self._beta)

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean


class Erlang(_Distribution):
    """
    erlang distribution

    Parameters
    ----------
    shape: int
        shape of the distribution (k) |n|
        should be >0

    rate: float
        rate parameter (lambda) |n|
        if omitted, the scale is used |n|
        should be >0

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    scale: float
        scale of the distribution (mu) |n|
        if omitted, the rate is used |n|
        should be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used

    Note
    ----
    Either rate or scale has to be specified, not both.
    """

    def __init__(self, shape, rate=None, time_unit=None, scale=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        if int(shape) != shape:
            raise TypeError("shape not integer")
        if shape <= 0:
            raise ValueError("shape <=0")
        self._shape = shape
        if rate is None:
            if scale is None:
                raise TypeError("neither rate nor scale specified")
            else:
                if scale <= 0:
                    raise ValueError("scale<=0")
                self._rate = 1 / scale
        else:
            if scale is None:
                if rate <= 0:
                    raise ValueError("rate<=0")
                self._rate = rate
            else:
                raise ValueError("both rate and scale specified")

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        self._mean = self._shape / self._rate

    def __repr__(self):
        return "Erlang"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Erlang distribution " + hex(id(self)))
        result.append("  shape (k)=" + str(self._shape))
        result.append("  rate (lambda)=" + str(self._rate) + ("" if self.time_unit == "" else " /" + self.time_unit))
        result.append("  scale (mu)=" + str(1 / self._rate))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : float
        """
        return self.randomstream.gammavariate(self._shape, 1 / self._rate) / self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean / self.time_unit_factor


class Cdf(_Distribution):
    """
    Cumulative distribution function

    Parameters
    ----------
    spec : list or tuple
        list with x-values and corresponding cumulative density
        (x1,c1,x2,c2, ...xn,cn) |n|
        Requirements:

            x1<=x2<= ...<=xn |n|
            c1<=c2<=cn |n|
            c1=0 |n|
            cn>0 |n|
            all cumulative densities are auto scaled according to cn,
            so no need to set cn to 1 or 100.

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream: randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it defines a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, spec, time_unit=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._x = []
        self._cum = []
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        lastcum = 0
        lastx = -inf
        spec = list(spec)
        if not spec:
            raise TypeError("no arguments specified")
        if spec[1] != 0:
            raise ValueError("first cumulative value should be 0")
        while len(spec) > 0:
            x = spec.pop(0) * self.time_unit_factor
            if not spec:
                raise ValueError("uneven number of parameters specified")
            if x < lastx:
                raise ValueError(f"x value {x} is smaller than previous value {lastx}")
            cum = spec.pop(0)
            if cum < lastcum:
                raise ValueError(f"cumulative value {cum} is smaller than previous value {lastcum}")
            self._x.append(x)
            self._cum.append(cum)
            lastx = x
            lastcum = cum
        if lastcum == 0:
            raise ValueError("last cumulative value should be > 0")
        self._cum = [x / lastcum for x in self._cum]
        self._mean = 0
        for i in range(len(self._cum) - 1):
            self._mean += ((self._x[i] + self._x[i + 1]) / 2) * (self._cum[i + 1] - self._cum[i])

    def __repr__(self):
        return "Cdf"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Cdf distribution " + hex(id(self)))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : float
        """
        r = self.randomstream.random()
        for i in range(len(self._cum)):
            if r < self._cum[i]:
                return interpolate(r, self._cum[i - 1], self._cum[i], self._x[i - 1], self._x[i])
        return self._x[i]

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean


class Pdf(_Distribution):
    """
    Probability distribution function

    Parameters
    ----------
    spec : list, tuple or dict
        either

        -   if no probabilities specified: |n|
            list/tuple with x-values and corresponding probability
            dict where the keys are re x-values and the values are probabilities
            (x0, p0, x1, p1, ...xn,pn) |n|
        -   if probabilities is specified: |n|
            list with x-values

    probabilities : iterable or float
        if omitted, spec contains the probabilities |n|
        the iterable (p0, p1, ...pn) contains the probabilities of the corresponding
        x-values from spec. |n|
        alternatively, if a float is given (e.g. 1), all x-values
        have equal probability. The value is not important.

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream : randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used

    Note
    ----
    p0+p1=...+pn>0 |n|
    all densities are auto scaled according to the sum of p0 to pn,
    so no need to have p0 to pn add up to 1 or 100. |n|
    The x-values can be any type. |n|
    If it is a salabim distribution, not the distribution,
    but a sample will be returned when calling sample.
    """

    def __init__(self, spec, probabilities=None, time_unit=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._x = []
        self._cum = []
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        sump = 0
        sumxp = 0
        hasmean = True
        if probabilities is None:
            if not spec:
                raise TypeError("no arguments specified")
            if isinstance(spec, dict):
                xs = list(spec.keys())
                probabilities = list(spec.values())
            else:
                xs = spec[::2]
                probabilities = spec[1::2]
                if len(xs) != len(probabilities):
                    raise ValueError("uneven number of parameters specified")
        else:
            xs = list(spec)
            if hasattr(probabilities, "__iter__") and not isinstance(probabilities, str):
                probabilities = list(probabilities)
                if len(xs) != len(probabilities):
                    raise ValueError("length of x-values does not match length of probabilities")
            else:
                probabilities = len(spec) * [1]

        self.supports_n = probabilities[1:] == probabilities[:-1]

        for x, p in zip(xs, probabilities):
            if time_unit is not None:
                if isinstance(x, _Distribution):
                    raise TypeError("time_unit can't be combined with distribution value")
                try:
                    x = float(x) * self.time_unit_factor
                except (ValueError, TypeError):
                    raise TypeError("time_unit can't be combined with non numeric value")

            self._x.append(x)
            sump += p
            self._cum.append(sump)
            if isinstance(x, _Distribution):
                x = x._mean
            try:
                sumxp += float(x) * p
            except (ValueError, TypeError):
                hasmean = False

        if sump == 0:
            raise ValueError("at least one probability should be >0")

        self._cum = [x / sump for x in self._cum]
        if hasmean:
            self._mean = sumxp / sump
        else:
            self._mean = nan

    def __repr__(self):
        return "Pdf"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("Pdf distribution " + hex(id(self)))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self, n=None):
        """
        Parameters
        ----------
        n : number of samples : int
            if not specified, specifies just return one sample, as usual |n|
            if specified, return a list of n sampled values from the distribution without replacement.
            This requires that all probabilities are equal. |n|
            If n > number of values in the Pdf distribution, n is assumed to be the number of values
            in the distribution. |n|
            If a sampled value is a distribution, a sample from that distribution will be returned.

        Returns
        -------
        Sample of the distribution : any (usually float) or list
            In case n is specified, returns a list of n values

        """
        if self.supports_n:
            if n is None:
                return self.randomstream.sample(self._x, 1)[0]
            else:
                if n < 0:
                    raise ValueError("n < 0")
                n = min(n, len(self._x))
                xs = self.randomstream.sample(self._x, n)
                return [x.sample() if isinstance(x, _Distribution) else x for x in xs]
        else:
            if n is None:
                r = self.randomstream.random()
                for cum, x in zip([0] + self._cum, [0] + self._x):
                    if r <= cum:
                        if isinstance(x, _Distribution):
                            return x.sample()
                        return x
            else:
                raise ValueError("not all probabilities are the same")

    def mean(self):
        """
        Returns
        -------
        mean of the distribution : float
            if the mean can't be calculated (if not all x-values are scalars or distributions),
            nan will be returned.
        """
        return self._mean


class CumPdf(_Distribution):
    """
    Cumulative Probability distribution function

    Parameters
    ----------
    spec : list or tuple
        either

        -   if no cumprobabilities specified: |n|
            list with x-values and corresponding cumulative probability
            (x0, p0, x1, p1, ...xn,pn) |n|
        -   if cumprobabilities is specified: |n|
            list with x-values

    cumprobabilities : list, tuple or float
        if omitted, spec contains the probabilities |n|
        the list (p0, p1, ...pn) contains the cumulative probabilities of the corresponding
        x-values from spec. |n|

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    randomstream : randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used

    Note
    ----
    p0<=p1<=..pn>0 |n|
    all densities are auto scaled according to pn,
    so no need to have pn be 1 or 100. |n|
    The x-values can be any type. |n|
    If it is a salabim distribution, not the distribution,
    but a sample will be returned when calling sample.
    """

    def __init__(self, spec, cumprobabilities=None, time_unit=None, randomstream=None, env=None):
        self.register_time_unit(time_unit, env)
        self._x = []
        self._cum = []
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        sump = 0
        sumxp = 0
        hasmean = True
        if not spec:
            raise TypeError("no arguments specified")
        if cumprobabilities is None:
            xs = spec[::2]
            cumprobabilities = spec[1::2]
            if len(xs) != len(cumprobabilities):
                raise ValueError("uneven number of parameters specified")
        else:
            if isinstance(cumprobabilities, (list, tuple)):
                cumprobabilities = list(cumprobabilities)
            else:
                raise TypeError("wrong type for cumulative probabilities")
            xs = list(spec)

            if len(xs) != len(cumprobabilities):
                raise ValueError("length of x-values does not match length of cumulative probabilities")

        for x, p in zip(xs, cumprobabilities):
            if time_unit is not None:
                if isinstance(x, _Distribution):
                    raise TypeError("time_unit can't be combined with distribution value")
                try:
                    x = float(x) * self.time_unit_factor
                except (ValueError, TypeError):
                    raise TypeError("time_unit can't be combined with non numeric value")
            self._x.append(x)
            p = p - sump
            if p < 0:
                raise ValueError("non increasing cumulative probabilities")
            sump += p
            self._cum.append(sump)
            if isinstance(x, _Distribution):
                x = x._mean
            try:
                sumxp += float(x) * p
            except (ValueError, TypeError):
                hasmean = False

        if sump == 0:
            raise ValueError("last cumulative probability should be >0")

        self._cum = [p / sump for p in self._cum]
        if hasmean:
            self._mean = sumxp / sump
        else:
            self._mean = nan

    def __repr__(self):
        return "CumPdf"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append("CumPdf distribution " + hex(id(self)))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution : any (usually float)
        """
        r = self.randomstream.random()
        for cum, x in zip([0] + self._cum, [0] + self._x):
            if r <= cum:
                if isinstance(x, _Distribution):
                    return x.sample()
                return x

    def mean(self):
        """
        Returns
        -------
        mean of the distribution : float
            if the mean can't be calculated (if not all x-values are scalars or distributions),
            nan will be returned.
        """
        return self._mean


class External(_Distribution):
    """
    External distribution function

    This distribution allows distributions from other modules, notably random, numpy.random and scipy.stats
    to be used as were they salabim distributions.

    Parameters
    ----------
    dis : external distribution
        either

        -   random.xxx |n|
        -   numpy.random.xxx |n|
        -   scipy.stats.xxx

    *args : any
        positional arguments to be passed to the dis distribution

    **kwargs : any
        keyword arguments to be passed to the dis distribution

    time_unit : str
        specifies the time unit |n|
        must be one of "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        default : no conversion |n|

    env : Environment
        environment where the distribution is defined |n|
        if omitted, default_env will be used
    """

    def __init__(self, dis, *args, **kwargs):
        self.dis_is_scipy = False
        if "scipy" in sys.modules:
            import scipy

            self.dis_is_scipy = isinstance(dis, (scipy.stats.rv_continuous, scipy.stats.rv_discrete))
        self.dis = dis
        self.time_unit = None
        time_unit = None
        env = None
        for kwarg in list(kwargs.keys()):
            if kwarg == "time_unit":
                time_unit = kwargs[kwarg]
                del kwargs[kwarg]
            if kwarg == "env":
                env = kwargs[kwarg]
                del kwargs[kwarg]
        self.args = args
        self.kwargs = kwargs
        self.register_time_unit(time_unit, env)
        self.samples = []
        if self.dis_is_scipy:
            self._mean = self.dis.mean(**{k: v for k, v in self.kwargs.items() if k not in ("size", "random_state")})
        else:
            self._mean = nan

    def sample(self):
        """
        Returns
        -------
        Sample of the distribution via external distribution method : any (usually float)
        """
        if not self.samples:
            if self.dis_is_scipy:
                samples = self.dis.rvs(*self.args, **self.kwargs)
            else:
                samples = self.dis(*self.args, **self.kwargs)
            if has_numpy() and isinstance(samples, numpy.ndarray):
                self.samples = samples.tolist()
            else:
                self.samples = [samples]
        return self.samples.pop() * self.time_unit_factor

    def mean(self):
        """
        Returns
        -------
        mean of the distribution : float
            only available for scipy.stats distribution. Otherwise nan will be returned.
        """
        return self._mean * self.time_unit_factor

    def __repr__(self):
        try:
            descr = self.dis.__name__
        except AttributeError:
            descr = self.dis.name  # for scipy.stats distributions
        return "External(" + descr + ")"

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        try:
            descr = [self.dis.__name__]
        except AttributeError:
            descr = [self.dis.name]  # for scipy.stats distributions
        for arg in self.args:
            descr.append(repr(arg))
        for kwarg in self.kwargs:
            descr.append(kwarg + "=" + repr(self.kwargs[kwarg]))
        if self.time_unit != "":
            descr.append("time_unit=" + repr(self.time_unit))
        result.append("External(" + ", ".join(descr) + ") distribution " + hex(id(self)))
        return return_or_print(result, as_str, file)


class Distribution(_Distribution):
    """
    Generate a distribution from a string

    Parameters
    ----------
    spec : str
        - string containing a valid salabim distribution, where only the first
          letters are relevant and casing is not important. Note that Erlang,
          Cdf, CumPdf and Poisson require at least two letters
          (Er, Cd, Cu and Po)
        - string containing one float (c1), resulting in Constant(c1)
        - string containing two floats seperated by a comma (c1,c2),
          resulting in a Uniform(c1,c2)
        - string containing three floats, separated by commas (c1,c2,c3),
          resulting in a Triangular(c1,c2,c3)

    time_unit : str
        Supported time_units: |n|
        "years", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds" |n|
        if spec has a time_unit as well, this parameter is ignored

    randomstream : randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed |n|

    Note
    ----
    The randomstream in the specifying string is ignored. |n|
    It is possible to use expressions in the specification, as long these
    are valid within the context of the salabim module, which usually implies
    a global variable of the salabim package.

    Examples
    --------
    Uniform(13)  ==> Uniform(13) |n|
    Uni(12,15)   ==> Uniform(12,15) |n|
    UNIF(12,15)  ==> Uniform(12,15) |n|
    N(12,3)      ==> Normal(12,3) |n|
    Tri(10,20).  ==> Triangular(10,20,15) |n|
    10.          ==> Constant(10) |n|
    12,15        ==> Uniform(12,15) |n|
    (12,15)      ==> Uniform(12,15) |n|
    Exp(a)       ==> Exponential(100), provided sim.a=100 |n|
    E(2)         ==> Exponential(2)
    Er(2,3)      ==> Erlang(2,3)
    """

    def __init__(self, spec, randomstream=None, time_unit=None):

        spec_orig = spec

        sp = spec.split("(")
        pre = sp[0].upper().strip()

        # here we have either a string starting with a ( of no ( at all
        if (pre == "") or not ("(" in spec):
            spec = spec.replace(")", "")  # get rid of closing parenthesis
            spec = spec.replace("(", "")  # get rid of starting parenthesis
            sp = spec.split(",")
            if len(sp) == 1:
                c1 = sp[0]
                spec = f"Constant({c1})"
            elif len(sp) == 2:
                c1 = sp[0]
                c2 = sp[1]
                spec = f"Uniform({c1}, {c2})"
            elif len(sp) == 3:
                c1 = sp[0]
                c2 = sp[1]
                c3 = sp[2]
                spec = f"Triangular({c1}, {c2}, {c3})"
            else:
                raise ValueError("incorrect specifier", spec_orig)

        else:
            for distype in (
                "Uniform",
                "Constant",
                "Triangular",
                "Exponential",
                "Normal",
                "Cdf",
                "Pdf",
                "CumPdf",
                "Weibull",
                "Gamma",
                "Erlang",
                "Beta",
                "IntUniform",
                "Poisson",
                "External",
            ):
                if pre == distype.upper()[: len(pre)]:
                    sp[0] = distype
                    spec = "(".join(sp)
                    break
        if time_unit is None:
            d = eval(spec)
        else:
            try:
                # try and add the time_unit=... parameter at the end
                d = eval(spec.strip()[:-1] + ", time_unit=" + repr(time_unit) + ")")
            except SyntaxError as e:
                if str(e).startswith("keyword argument repeated"):
                    d = eval(spec)
                else:
                    raise
            except TypeError as e:
                if "got multiple values" in str(e):
                    d = eval(spec)
                else:
                    raise

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._distribution = d
        try:
            self._mean = d._mean
        except AttributeError:
            self._mean = nan

    def __repr__(self):
        return self._distribution.__repr__()

    def print_info(self, as_str=False, file=None):
        """
        prints information about the distribution

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        return self._distribution.print_info(as_str=as_str, file=file)

    def sample(self):
        """
        Returns
        -------
        Sample of the  distribution : any (usually float)
        """
        self._distribution.randomstream = self.randomstream
        return self._distribution.sample()

    def mean(self):
        """
        Returns
        -------
        Mean of the distribution : float
        """
        return self._mean


class State:
    """
    State

    Parameters
    ----------
    name : str
        name of the state |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

    value : any, preferably printable
        initial value of the state |n|
        if omitted, False

    monitor : bool
        if True (default) , the waiters queue and the value are monitored |n|
        if False, monitoring is disabled.

    type : str
        specifies how the state values are monitored. Using a
        int, uint of float type results in less memory usage and better
        performance. Note that you should avoid the number not to use
        as this is used to indicate 'off'

        -  "any" (default) stores values in a list. This allows for
           non numeric values. In calculations the values are
           forced to a numeric value (0 if not possible) do not use -inf
        -  "bool" bool (False, True). Actually integer >= 0 <= 254 1 byte do not use 255
        -  "int8" integer >= -127 <= 127 1 byte do not use -128
        -  "uint8" integer >= 0 <= 254 1 byte do not use 255
        -  "int16" integer >= -32767 <= 32767 2 bytes do not use -32768
        -  "uint16" integer >= 0 <= 65534 2 bytes do not use 65535
        -  "int32" integer >= -2147483647 <= 2147483647 4 bytes do not use -2147483648
        -  "uint32" integer >= 0 <= 4294967294 4 bytes do not use 4294967295
        -  "int64" integer >= -9223372036854775807 <= 9223372036854775807 8 bytes do not use -9223372036854775808
        -  "uint64" integer >= 0 <= 18446744073709551614 8 bytes do not use 18446744073709551615
        -  "float" float 8 bytes do not use -inf

    env : Environment
        environment to be used |n|
        if omitted, default_env is used
    """

    def __init__(self, name=None, value=False, type="any", monitor=True, env=None, *args, **kwargs):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        _set_name(name, self.env._nameserializeState, self)
        self._value = value
        savetrace = self.env._trace
        self.env._trace = False
        self._waiters = Queue(name="waiters of " + self.name(), monitor=monitor, env=self.env)
        self._waiters._isinternal = True
        self.env._trace = savetrace
        self.value = _SystemMonitor(name="Value of " + self.name(), level=True, initial_tally=value, monitor=monitor, type=type, env=self.env)
        if self.env._trace:
            self.env.print_trace("", "", self.name() + " create", "value = " + repr(self._value))
        self.setup(*args, **kwargs)

    def setup(self):
        """
        called immediately after initialization of a state.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments will be passed
        """
        pass

    def register(self, registry):
        """
        registers the state in the registry

        Parameters
        ----------
        registry : list
            list of (to be) registered objetcs

        Returns
        -------
        state (self) : State

        Note
        ----
        Use State.deregister if state does not longer need to be registered.
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self in registry:
            raise ValueError(self.name() + " already in registry")
        registry.append(self)
        return self

    def deregister(self, registry):
        """
        deregisters the state in the registry

        Parameters
        ----------
        registry : list
            list of registered states

        Returns
        -------
        state (self) : State
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self not in registry:
            raise ValueError(self.name() + " not in registry")
        registry.remove(self)
        return self

    def __repr__(self):
        return object_to_str(self) + " (" + self.name() + ")"

    def print_histograms(self, exclude=(), as_str=False, file=None):
        """
        print histograms of the waiters queue and the value monitor

        Parameters
        ----------
        exclude : tuple or list
            specifies which queues or monitors to exclude |n|
            default: ()

        as_str: bool
            if False (default), print the histograms
            if True, return a string containing the histograms

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        histograms (if as_str is True) : str
        """
        result = []
        if self.waiters() not in exclude:
            result.append(self.waiters().print_histograms(exclude=exclude, as_str=True))
        if self.value not in exclude:
            result.append(self.value.print_histogram(as_str=True))
        return return_or_print(result, as_str, file)

    def print_info(self, as_str=False, file=None):
        """
        prints info about the state

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append(object_to_str(self) + " " + hex(id(self)))
        result.append("  name=" + self.name())
        result.append("  value=" + str(self._value))
        if self._waiters:
            result.append("  waiting component(s):")
            mx = self._waiters._head.successor
            while mx != self._waiters._tail:
                c = mx.component
                mx = mx.successor
                values = ""
                for s, value, valuetype in c._waits:
                    if s == self:
                        if values != "":
                            values = values + ", "
                        values = values + str(value)

                result.append("    " + pad(c.name(), 20), " value(s): " + values)
        else:
            result.append("  no waiting components")
        return return_or_print(result, as_str, file)

    def __call__(self):
        return self._value

    def get(self):
        """
        get value of the state

        Returns
        -------
        value of the state : any
            Instead of this method, the state can also be called directly, like |n|

            level = sim.State("level") |n|
            ... |n|
            print(level()) |n|
            print(level.get())  # identical |n|
        """
        return self._value

    def set(self, value=True):
        """
        set the value of the state

        Parameters
        ----------
        value : any (preferably printable)
            if omitted, True |n|
            if there is a change, the waiters queue will be checked
            to see whether there are waiting components to be honored

        Note
        ----
        This method is identical to reset, except the default value is True.
        """
        if self.env._trace:
            self.env.print_trace("", "", self.name() + " set", "value = " + repr(value))
        if self._value != value:
            self._value = value
            self.value.tally(value)
            self._trywait()

    def reset(self, value=False):
        """
        reset the value of the state

        Parameters
        ----------
        value : any (preferably printable)
            if omitted, False |n|
            if there is a change, the waiters queue will be checked
            to see whether there are waiting components to be honored

        Note
        ----
        This method is identical to set, except the default value is False.
        """
        if self.env._trace:
            self.env.print_trace("", "", self.name() + " reset", "value = " + repr(value))
        if self._value != value:
            self._value = value
            self.value.tally(value)
            self._trywait()

    def trigger(self, value=True, value_after=None, max=inf):
        """
        triggers the value of the state

        Parameters
        ----------
        value : any (preferably printable)
            if omitted, True |n|

        value_after : any (preferably printable)
            after the trigger, this will be the new value. |n|
            if omitted, return to the the before the trigger.

        max : int
            maximum number of components to be honored for the trigger value |n|
            default: inf

        Note
        ----
            The value of the state will be set to value, then at most
            max waiting components for this state  will be honored and next
            the value will be set to value_after and again checked for possible
            honors.
        """
        if value_after is None:
            value_after = self._value
        if self.env._trace:
            self.env.print_trace("", "", self.name() + " trigger", " value = " + str(value) + " --> " + str(value_after) + " allow " + str(max) + " components")
        self._value = value
        self.value.tally(value)  # strictly speaking, not required
        self._trywait(max)
        self._value = value_after
        self.value.tally(value_after)
        self._trywait()

    def _trywait(self, max=inf):
        mx = self._waiters._head.successor
        while mx != self._waiters._tail:
            c = mx.component
            mx = mx.successor
            if c._trywait():
                max -= 1
                if max == 0:
                    return

    def monitor(self, value=None):
        """
        enables/disables the state monitors and value monitor

        Parameters
        ----------
        value : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if not specified, no change

        Note
        ----
        it is possible to individually control requesters().monitor(),
            value.monitor()
        """
        self.waiters().monitor(value)
        self.value.monitor(value)

    def all_monitors(self):
        """
        returns all mononitors belonging to the state

        Returns
        -------
        all monitors : tuple of monitors
        """
        return (self.waiters().length, self.waiters().length_of_stay, self.value)

    def reset_monitors(self, monitor=None, stats_only=None):
        """
        resets the monitor for the state's value and the monitors of the waiters queue

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change of monitoring state

        stats_only : bool
            if True, only statistics will be collected (using less memory, but also less functionality) |n|
            if False, full functionality |n|
            if omittted, no change of stats_only
        """
        self._waiters.reset_monitors(monitor=monitor, stats_only=stats_only)
        self.value.reset(monitor=monitor, stats_only=stats_only)

    def _get_value(self):
        return self._value

    def name(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the state
            if omitted, no change

        Returns
        -------
        Name of the state : str

        Note
        ----
        base_name and sequence_number are not affected if the name is changed |n|
        All derived named are updated as well.
        """
        if value is not None:
            self._name = value
            self._waiters.name("waiters of " + value)
            self.value.name("Value of " + value)

        return self._name

    def base_name(self):
        """
        Returns
        -------
        base name of the state (the name used at initialization): str
        """
        return self._base_name

    def sequence_number(self):
        """
        Returns
        -------
        sequence_number of the state : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        """
        return self._sequence_number

    def print_statistics(self, as_str=False, file=None):
        """
        prints a summary of statistics of the state

        Parameters
        ----------
        as_str: bool
            if False (default), print the statistics
            if True, return a string containing the statistics

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        statistics (if as_str is True) : str
        """
        result = []
        result.append(f"Statistics of {self.name()} at {fn(self.env._now - self.env._offset, 13, 3)}")
        result.append(self.waiters().length.print_statistics(show_header=False, show_legend=True, do_indent=True, as_str=True))
        result.append("")
        result.append(self.waiters().length_of_stay.print_statistics(show_header=False, show_legend=False, do_indent=True, as_str=True))
        result.append("")
        result.append(self.value.print_statistics(show_header=False, show_legend=False, do_indent=True, as_str=True))
        return return_or_print(result, as_str, file)

    def waiters(self):
        """
        Returns
        -------
        queue containing all components waiting for this state : Queue
        """
        return self._waiters


class Resource:
    """
    Resource

    Parameters
    ----------
    name : str
        name of the resource |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

    capacity : float
        capacity of the resource |n|
        if omitted, 1

    initial_claimed_quantity : float
        initial claimed quantity. Only allowed to be non zero for anonymous resources |n|
        if omitted, 0

    anonymous : bool
        anonymous specifier |n|
        if True, claims are not related to any component. This is useful
        if the resource is actually just a level. |n|
        if False, claims belong to a component.

    prememptive : bool
        if True, components with a lower priority will be bumped out of the claimers queue if possible
        if False (default), no bumping

    honor_only_first : bool
        if True, only the first component of requesters will be honoured (default: False)

    honor_only_highest_priority : bool
        if True, only component with the priority of the first requester will be honoured (default: False)
        Note: only respected if honor_only_first is False

    monitor : bool
        if True (default), the requesters queue, the claimers queue,
        the capacity, the available_quantity and the claimed_quantity are monitored |n|
        if False, monitoring is disabled.

    env : Environment
        environment to be used |n|
        if omitted, default_env is used
    """

    def __init__(
        self,
        name=None,
        capacity=1,
        initial_claimed_quantity=0,
        anonymous=False,
        preemptive=False,
        honor_only_first=False,
        honor_only_highest_priority=False,
        monitor=True,
        env=None,
        *args,
        **kwargs,
    ):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env

        if initial_claimed_quantity != 0:
            if not anonymous:
                raise ValueError("initial_claimed_quantity != 0 only allowed for anonymous resources")

        self._capacity = capacity
        self._honor_only_first = honor_only_first
        self._honor_only_highest_priority = honor_only_highest_priority

        _set_name(name, self.env._nameserializeResource, self)
        savetrace = self.env._trace
        self.env._trace = False
        self._requesters = Queue(name="requesters of " + self.name(), monitor=monitor, env=self.env)
        self._requesters._isinternal = True
        self._claimers = Queue(name="claimers of " + self.name(), monitor=monitor, env=self.env)
        self._claimers._isinternal = True
        self._claimers._isclaimers = True  # used by Component.isbumped()
        self.env._trace = savetrace
        self._claimed_quantity = initial_claimed_quantity
        self._anonymous = anonymous
        self._preemptive = preemptive
        self._minq = inf
        self._trying = False

        self.capacity = _CapacityMonitor("Capacity of " + self.name(), level=True, initial_tally=capacity, monitor=monitor, type="float", env=self.env)
        self.capacity.parent = self
        self.claimed_quantity = _SystemMonitor(
            "Claimed quantity of " + self.name(), level=True, initial_tally=initial_claimed_quantity, monitor=monitor, type="float", env=self.env
        )
        self.available_quantity = _SystemMonitor(
            "Available quantity of " + self.name(), level=True, initial_tally=capacity - initial_claimed_quantity, monitor=monitor, type="float", env=self.env
        )

        self.occupancy = _SystemMonitor("Occupancy of " + self.name(), level=True, initial_tally=0, monitor=monitor, type="float", env=self.env)
        if self.env._trace:
            self.env.print_trace("", "", self.name() + " create", "capacity=" + str(self._capacity) + (" anonymous" if self._anonymous else ""))
        self.setup(*args, **kwargs)

    def ispreemptive(self):
        """
        Returns
        -------
        True if preemptive, False otherwise : bool
        """

        return self._preemptive

    def setup(self):
        """
        called immediately after initialization of a resource.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        """
        pass

    def all_monitors(self):
        """
        returns all mononitors belonging to the resource

        Returns
        -------
        all monitors : tuple of monitors
        """
        return (
            self.requesters().length,
            self.requesters().length_of_stay,
            self.claimers().length,
            self.claimers().length_of_stay,
            self.capacity,
            self.available_quantity,
            self.claimed_quantity,
            self.occupancy,
        )

    def reset_monitors(self, monitor=None, stats_only=None):
        """
        resets the resource monitors

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change of monitoring state

        stats_only : bool
            if True, only statistics will be collected (using less memory, but also less functionality) |n|
            if False, full functionality |n|
            if omittted, no change of stats_only

        Note
        ----
            it is possible to reset individual monitoring with
            claimers().reset_monitors(),
            requesters().reset_monitors,
            capacity.reset(),
            available_quantity.reset() or
            claimed_quantity.reset() or
            occupancy.reset()
        """

        self.requesters().reset_monitors(monitor=monitor, stats_only=stats_only)
        self.claimers().reset_monitors(monitor=monitor, stats_only=stats_only)
        for m in (self.capacity, self.available_quantity, self.claimed_quantity, self.occupancy):
            m.reset(monitor=monitor, stats_only=stats_only)

    def print_statistics(self, as_str=False, file=None):
        """
        prints a summary of statistics of a resource

        Parameters
        ----------
        as_str: bool
            if False (default), print the statistics
            if True, return a string containing the statistics

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        statistics (if as_str is True) : str
        """
        result = []
        result.append(f"Statistics of {self.name()} at {(self.env._now - self.env._offset):13.3f}")
        show_legend = True
        for q in [self.requesters(), self.claimers()]:
            result.append(q.length.print_statistics(show_header=False, show_legend=show_legend, do_indent=True, as_str=True))
            show_legend = False
            result.append("")
            result.append(q.length_of_stay.print_statistics(show_header=False, show_legend=show_legend, do_indent=True, as_str=True))
            result.append("")

        for m in (self.capacity, self.available_quantity, self.claimed_quantity, self.occupancy):
            result.append(m.print_statistics(show_header=False, show_legend=show_legend, do_indent=True, as_str=True))
            result.append("")
        return return_or_print(result, as_str, file)

    def print_histograms(self, exclude=(), as_str=False, file=None):
        """
        prints histograms of the requesters and claimers queue as well as
        the capacity, available_quantity and claimed_quantity timstamped monitors of the resource

        Parameters
        ----------
        exclude : tuple or list
            specifies which queues or monitors to exclude |n|
            default: ()

        as_str: bool
            if False (default), print the histograms
            if True, return a string containing the histograms

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        histograms (if as_str is True) : str
        """
        result = []
        for q in (self.requesters(), self.claimers()):
            if q not in exclude:
                result.append(q.print_histograms(exclude=exclude, as_str=True))
        for m in (self.capacity, self.available_quantity, self.claimed_quantity, self.occupancy):
            if m not in exclude:
                result.append(m.print_histogram(as_str=True))
        return return_or_print(result, as_str, file)

    def monitor(self, value):
        """
        enables/disables the resource monitors

        Parameters
        ----------
        value : bool
            if True, monitoring is enabled |n|
            if False, monitoring is disabled |n|

        Note
        ----
        it is possible to individually control monitoring with claimers().monitor()
        and requesters().monitor(), capacity.monitor(), available_quantity.monitor),
        claimed_quantity.monitor() or occupancy.monitor()
        """
        self.requesters().monitor(value)
        self.claimers().monitor(value)
        for m in (self.capacity, self.available_quantity, self.claimed_quantity, self.occupancy):
            m.monitor(value)

    def register(self, registry):
        """
        registers the resource in the registry

        Parameters
        ----------
        registry : list
            list of (to be) registered objects

        Returns
        -------
        resource (self) : Resource

        Note
        ----
        Use Resource.deregister if resource does not longer need to be registered.
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self in registry:
            raise ValueError(self.name() + " already in registry")
        registry.append(self)
        return self

    def deregister(self, registry):
        """
        deregisters the resource in the registry

        Parameters
        ----------
        registry : list
            list of registered components

        Returns
        -------
        resource (self) : Resource
        """
        if not isinstance(registry, list):
            raise TypeError("registry not list")
        if self not in registry:
            raise ValueError(self.name() + " not in registry")
        registry.remove(self)
        return self

    def __repr__(self):
        return object_to_str(self) + " (" + self.name() + ")"

    def print_info(self, as_str=False, file=None):
        """
        prints info about the resource

        Parameters
        ----------
        as_str: bool
            if False (default), print the info
            if True, return a string containing the info

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        info (if as_str is True) : str
        """
        result = []
        result.append(object_to_str(self) + " " + hex(id(self)))
        result.append("  name=" + self.name())
        result.append("  capacity=" + str(self._capacity))
        if self._requesters:
            result.append("  requesting component(s):")
            mx = self._requesters._head.successor
            while mx != self._requesters._tail:
                c = mx.component
                mx = mx.successor
                result.append("    " + pad(c.name(), 20) + " quantity=" + str(c._requests[self]))
        else:
            result.append("  no requesting components")

        result.append("  claimed_quantity=" + str(self._claimed_quantity))
        if self._claimed_quantity >= 0:
            if self._anonymous:
                result.append("  not claimed by any components," + " because the resource is anonymous")
            else:
                result.append("  claimed by:")
                mx = self._claimers._head.successor
                while mx != self._claimers._tail:
                    c = mx.component
                    mx = mx.successor
                    result.append("    " + pad(c.name(), 20) + " quantity=" + str(c._claims[self]))
        return return_or_print(result, as_str, file)

    def _tryrequest(self):  # this is Resource._tryrequest
        if self._anonymous:
            if not self._trying:
                self._trying = True
                mx = mx_first = self._requesters._head.successor
                mx_first_priority = mx_first.priority
                while mx != self._requesters._tail:
                    if self._honor_only_first and mx != mx_first:
                        break
                    if self._honor_only_highest_priority and mx.priority != mx_first_priority:
                        break
                    c = mx.component
                    mx = mx.successor
                    c._tryrequest()
                    if c not in self._requesters:
                        mx = self._requesters._head.successor  # start again

                self._trying = False
        else:
            mx = mx_first = self._requesters._head.successor
            mx_first_priority = mx_first.priority

            while mx != self._requesters._tail:
                if self._honor_only_first and mx != mx_first:
                    break
                if self._honor_only_highest_priority and mx.priority != mx_first_priority:
                    break
                if self._minq > (self._capacity - self._claimed_quantity + 1e-8):
                    break  # inpossible to honor any more requests
                c = mx.component
                mx = mx.successor
                c._tryrequest()

    def release(self, quantity=None):
        """
        releases all claims or a specified quantity

        Parameters
        ----------
        quantity : float
            quantity to be released |n|
            if not specified, the resource will be emptied completely |n|
            for non-anonymous resources, all components claiming from this resource
            will be released.

        Note
        ----
        quantity may not be specified for a non-anonymous resoure
        """

        if self._anonymous:
            if quantity is None:
                q = self._claimed_quantity
            else:
                q = quantity

            self._claimed_quantity -= q
            if self._claimed_quantity < 1e-8:
                self._claimed_quantity = 0
            self.claimed_quantity.tally(self._claimed_quantity)
            self.occupancy.tally(0 if self._capacity <= 0 else self._claimed_quantity / self._capacity)
            self.available_quantity.tally(self._capacity - self._claimed_quantity)
            self._tryrequest()

        else:
            if quantity is not None:
                raise ValueError("no quantity allowed for non-anonymous resource")

            mx = self._claimers._head.successor
            while mx != self._tail:
                c = mx.component
                mx = mx.successor
                c.release(self)

    def requesters(self):
        """
        Return
        ------
        queue containing all components with not yet honored requests: Queue
        """
        return self._requesters

    def claimers(self):
        """
        Returns
        -------
        queue with all components claiming from the resource: Queue
            will be an empty queue for an anonymous resource
        """
        return self._claimers

    def set_capacity(self, cap):
        """
        Parameters
        ----------
        cap : float or int
            capacity of the resource |n|
            this may lead to honoring one or more requests. |n|
            if omitted, no change
        """
        self._capacity = cap
        self.capacity.tally(self._capacity)
        self.available_quantity.tally(self._capacity - self._claimed_quantity)
        self.occupancy.tally(0 if self._capacity <= 0 else self._claimed_quantity / self._capacity)
        self._tryrequest()

    def name(self, value=None):
        """
        Parameters
        ----------
        value : str
            new name of the resource
            if omitted, no change

        Returns
        -------
        Name of the resource : str

        Note
        ----
        base_name and sequence_number are not affected if the name is changed |n|
        All derived named are updated as well.
        """
        if value is not None:
            self._name = value
            self._requesters.name("requesters of " + value)
            self._claimers.name("claimers of " + value)
            self.capacity.name("Capacity of " + value)
            self.claimed_quantity.name("Clamed quantity of " + value)
            self.available_quantity.name("Available quantity of " + value)
            self.occupancy.name("Occupancy of " + value)

        return self._name

    def base_name(self):
        """
        Returns
        -------
        base name of the resource (the name used at initialization): str
        """
        return self._base_name

    def sequence_number(self):
        """
        Returns
        -------
        sequence_number of the resource : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        """
        return self._sequence_number


class _PeriodComponent(Component):
    def setup(self, pm):
        self.pm = pm

    def process(self):
        for iperiod, duration in itertools.cycle(enumerate(self.pm.periods)):
            self.pm.perperiod[self.pm.iperiod].monitor(False)
            self.pm.iperiod = iperiod
            if self.pm.m._level:
                self.pm.perperiod[self.pm.iperiod].tally(self.pm.m())
            self.pm.perperiod[self.pm.iperiod].monitor(True)
            yield self.hold(duration)


class PeriodMonitor:
    """
    defines a number of period monitors for a given monitor.

    Parameters
    ----------
    parent_monitor : Monitor
        parent_monitor to be divided into several period monitors for given time periods.

    periods : list or tuple of floats
        specifies the length of the period intervals. |n|
        default: 24 * [1], meaning periods 0-1, 1-2, ..., 23-24 |n|
        the periods do not have to be all the same.

    period_monitor_names : list or tuple of string
        specifies the names of the period monitors.
        It is required that the length of period equals the length of period_monitor_names.
        By default the names are composed of the name of the parent monitor

    Note
    ----
    The period monitors can be accessed by indexing the instance of PeriodMonitor.
    """

    @staticmethod
    def new_tally(self, x, weight=1):
        for m in self.period_monitors:
            m.perperiod[m.iperiod].tally(x, weight)
        self.org_tally(x, weight)

    @staticmethod
    def new_reset(self, monitor=None, stats_only=None):
        for m in self.period_monitors:
            for iperiod in range(len(m.periods)):
                m.perperiod[iperiod].reset(stats_only=stats_only)
                # the individual monitors do not follow the monitor flag

        self.org_reset(monitor=monitor, stats_only=stats_only)

    def __getitem__(self, i):
        return self.perperiod[i]

    def remove(self):
        """
        removes the period monitor
        """
        self.pc.cancel()
        del self.periods
        self.m.period_monitors.remove(self)

    def __init__(self, parent_monitor, periods=None, period_monitor_names=None, env=None):
        self.pc = _PeriodComponent(pm=self, skip_standby=True, suppress_trace=True)
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        if periods is None:
            periods = 24 * [1]
        self.periods = periods
        cum = 0
        if period_monitor_names is None:
            period_monitor_names = []
            for duration in periods:
                period_monitor_names.append(parent_monitor.name() + ".period [" + str(cum) + " - " + str(cum + duration) + "]")
                cum += duration

        self.m = parent_monitor
        if not hasattr(self, "period_monitors"):
            self.m.period_monitors = []
            self.m.org_tally = self.m.tally
            self.m.tally = types.MethodType(self.new_tally, self.m)
            self.m.org_reset = self.m.reset
            self.m.reset = types.MethodType(self.new_reset, self.m)
            self.m.period_monitors.append(self)

        self.iperiod = 0
        if self.m._level:
            self.perperiod = [Monitor(name=period_monitor_name, level=True, monitor=False, env=self.env) for period_monitor_name in period_monitor_names]
        else:
            self.perperiod = [Monitor(name=period_monitor_name, monitor=False, env=self.env) for period_monitor_name in period_monitor_names]


class AudioClip:
    @staticmethod
    def send(command):
        buffer = ctypes.c_buffer(255)
        errorcode = ctypes.windll.winmm.mciSendStringA(str(command).encode(), buffer, 254, 0)
        if errorcode:
            return errorcode, AudioClip.get_error(errorcode)
        else:
            return errorcode, buffer.value

    @staticmethod
    def get_error(error):
        error = int(error)
        buffer = ctypes.c_buffer(255)
        ctypes.windll.winmm.mciGetErrorStringA(error, buffer, 254)
        return buffer.value

    @staticmethod
    def directsend(*args):
        command = " ".join(str(arg) for arg in args)
        (err, buf) = AudioClip.send(command)
        if err != 0:
            print("Error " + str(err) + " for" + command + " : " + str(buf))
        return (err, buf)

    seq = 1

    def __init__(self, filename):
        filename = filename.replace("/", "\\")
        if not os.path.isfile(filename):
            raise FileNotFoundError(filename)

        if not Windows:
            self.duration = 0
            self._alias = 0  # signal to dummy all methods`
            return  # on Unix and MacOS this is just dummy

        self._alias = str(AudioClip.seq)
        AudioClip.seq += 1

        AudioClip.directsend("open", '"' + filename + '"', "alias", self._alias)
        AudioClip.directsend("set", self._alias, "time format milliseconds")

        err, buf = AudioClip.directsend("status", self._alias, "length")
        self.duration = int(buf) / 1000

    def volume(self, level):
        """Sets the volume between 0 and 100."""
        if self._alias:
            AudioClip.directsend("setaudio", self._alias, "volume to ", level * 10)

    def play(self, start=None, end=None):
        if self._alias:
            start_ms = (0 if start is None else min(start, self.duration)) * 1000
            end_ms = (self.duration if end is None else min(end, self.duration)) * 1000
            err, buf = AudioClip.directsend("play", self._alias, "from", int(start_ms), "to", int(end_ms))

    def isplaying(self):
        return self._mode() == "playing"

    def _mode(self):
        if self._alias:
            err, buf = AudioClip.directsend("status", self._alias, "mode")
            return buf
        return "?"

    def pause(self):
        if self._alias:
            AudioClip.directsend("pause", self._alias)

    def unpause(self):
        if self._alias:
            AudioClip.directsend("resume", self._alias)

    def ispaused(self):
        return self._mode() == "paused"

    def stop(self):
        if self._alias:
            AudioClip.directsend("stop", self._alias)
            AudioClip.directsend("seek", self._alias, "to start")

    # TODO: this closes the file even if we're still playing.
    # no good.  detect isplaying(), and don't die till then!


#    def __del__(self):
#        AudioClip.directsend(f"close {self._alias}")


def audio_duration(filename):
    """
    duration of a audio file (usually mp3)

    Parameters
    ----------
    filename : str
        must be a valid audio file (usually mp3)

    Returns
    -------
    duration in seconds : float

    Note
    ----
    Only supported on Windows and Pythonista. On other platform returns 0
    """
    if Pythonista:
        import sound

        return sound.Player(filename).duration
    audioclip = AudioClip(filename)
    return audioclip.duration


class AudioSegment:
    def __init__(self, start, t0, filename, duration):
        self.start = start
        self.t0 = t0
        self.filename = filename
        self.duration = duration


class _APNG:
    # The  _APNG class is derived from (more or less an excerpt) from the py_APNG module
    class Chunk(collections.namedtuple("Chunk", ["type", "data"])):
        pass

    class PNG:
        def __init__(self):
            self.hdr = None
            self.end = None
            self.width = None
            self.height = None
            self.chunks = []

        def init(self):
            for type_, data in self.chunks:
                if type_ == "IHDR":
                    self.hdr = data
                elif type_ == "IEND":
                    self.end = data

            if self.hdr:
                # grab w, h info
                self.width, self.height = struct.unpack("!II", self.hdr[8:16])

        @staticmethod
        def parse_chunks(b):
            i = 8
            while i < len(b):
                (data_len,) = struct.unpack("!I", b[i : i + 4])
                type_ = b[i + 4 : i + 8].decode("latin-1")
                yield _APNG.Chunk(type_, b[i : i + data_len + 12])
                i += data_len + 12

        @classmethod
        def from_bytes(cls, b):
            im = cls()
            im.chunks = list(cls.parse_chunks(b))
            im.init()
            return im

    class FrameControl:
        def __init__(self, width=None, height=None, x_offset=0, y_offset=0, delay=100, delay_den=1000, depose_op=1, blend_op=0):
            self.width = width
            self.height = height
            self.x_offset = x_offset
            self.y_offset = y_offset
            self.delay = delay
            self.delay_den = delay_den
            self.depose_op = depose_op
            self.blend_op = blend_op

        def to_bytes(self):
            return struct.pack("!IIIIHHbb", self.width, self.height, self.x_offset, self.y_offset, self.delay, self.delay_den, self.depose_op, self.blend_op)

    def __init__(self, num_plays=0):
        self.frames = []
        self.num_plays = num_plays

    @staticmethod
    def make_chunk(chunk_type, chunk_data):
        out = struct.pack("!I", len(chunk_data))
        chunk_data = chunk_type.encode("latin-1") + chunk_data
        out += chunk_data + struct.pack("!I", binascii.crc32(chunk_data) & 0xFFFFFFFF)
        return out

    def append(self, png, **options):
        if not isinstance(png, _APNG.PNG):
            raise TypeError(f"Expected an instance of `PNG` but got `{png}`")
        control = _APNG.FrameControl(**options)
        if control.width is None:
            control.width = png.width
        if control.height is None:
            control.height = png.height
        self.frames.append((png, control))

    def to_bytes(self):
        CHUNK_BEFORE_IDAT = {"cHRM", "gAMA", "iCCP", "sBIT", "sRGB", "bKGD", "hIST", "tRNS", "pHYs", "sPLT", "tIME", "PLTE"}
        PNG_SIGN = b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
        out = [PNG_SIGN]
        other_chunks = []
        seq = 0
        png, control = self.frames[0]
        out.append(png.hdr)
        out.append(self.make_chunk("acTL", struct.pack("!II", len(self.frames), self.num_plays)))
        if control:
            out.append(self.make_chunk("fcTL", struct.pack("!I", seq) + control.to_bytes()))
            seq += 1
        idat_chunks = []
        for type_, data in png.chunks:
            if type_ in ("IHDR", "IEND"):
                continue
            if type_ == "IDAT":
                # put at last
                idat_chunks.append(data)
                continue
            out.append(data)
        out.extend(idat_chunks)
        for png, control in self.frames[1:]:
            out.append(self.make_chunk("fcTL", struct.pack("!I", seq) + control.to_bytes()))
            seq += 1
            for type_, data in png.chunks:
                if type_ in ("IHDR", "IEND") or type_ in CHUNK_BEFORE_IDAT:
                    continue

                if type_ == "IDAT":
                    out.append(self.make_chunk("fdAT", struct.pack("!I", seq) + data[8:-4]))
                    seq += 1
                else:
                    other_chunks.append(data)

        out.extend(other_chunks)
        out.append(png.end)

        return b"".join(out)

    def save(self, file):
        b = self.to_bytes()
        if hasattr(file, "write_bytes"):
            file.write_bytes(b)
        elif hasattr(file, "write"):
            file.write(b)
        else:
            with open(file, "wb") as f:
                f.write(b)


def colornames():
    """
    available colornames

    Returns
    -------
    dict with name of color as key, #rrggbb or #rrggbbaa as value : dict
    """
    if not hasattr(colornames, "cached"):
        colornames.cached = pickle.loads(
            b"(dp0\nVfuchsia\np1\nV#FF00FF\np2\nsV\np3\nV#00000000\np4\nsVtransparent\np5\ng4\nsVpalevioletred\np6\nV#DB7093\np7\nsVskyblue\np8\nV#87CEEB\np9\nsVpaleturquoise\np10\nV#AFEEEE\np11\nsVcadetblue\np12\nV#5F9EA0\np13\nsVorangered\np14\nV#FF4500\np15\nsVsteelblue\np16\nV#4682B4\np17\nsVdimgray\np18\nV#696969\np19\nsVdarkseagreen\np20\nV#8FBC8F\np21\nsV60%gray\np22\nV#999999\np23\nsVroyalblue\np24\nV#4169E1\np25\nsVmediumblue\np26\nV#0000CD\np27\nsVgoldenrod\np28\nV#DAA520\np29\nsVmediumvioletred\np30\nV#C71585\np31\nsVblueviolet\np32\nV#8A2BE2\np33\nsVgainsboro\np34\nV#DCDCDC\np35\nsVdarkred\np36\nV#8B0000\np37\nsVrosybrown\np38\nV#BC8F8F\np39\nsVgold\np40\nV#FFD700\np41\nsVcoral\np42\nV#FF7F50\np43\nsVwhite\np44\nV#FFFFFF\np45\nsVdarkcyan\np46\nV#008B8B\np47\nsVblack\np48\nV#000000\np49\nsVorchid\np50\nV#DA70D6\np51\nsVmediumturquoise\np52\nV#48D1CC\np53\nsVlightgreen\np54\nV#90EE90\np55\nsVlime\np56\nV#00FF00\np57\nsVpapayawhip\np58\nV#FFEFD5\np59\nsVchocolate\np60\nV#D2691E\np61\nsV40%gray\np62\nV#666666\np63\nsVoldlace\np64\nV#FDF5E6\np65\nsVdarkblue\np66\nV#00008B\np67\nsVsilver\np68\nV#C0C0C0\np69\nsVaquamarine\np70\nV#7FFFD4\np71\nsVlightcoral\np72\nV#F08080\np73\nsVcyan\np74\nV#00FFFF\np75\nsVdodgerblue\np76\nV#1E90FF\np77\nsV10%gray\np78\nV#191919\np79\nsVmidnightblue\np80\nV#191970\np81\nsVgreen\np82\nV#008000\np83\nsVlightsalmon\np84\nV#FFA07A\np85\nsVazure\np86\nV#F0FFFF\np87\nsVred\np88\nV#FF0000\np89\nsVlightpink\np90\nV#FFB6C1\np91\nsVwhitesmoke\np92\nV#F5F5F5\np93\nsVyellow\np94\nV#FFFF00\np95\nsVlawngreen\np96\nV#7CFC00\np97\nsVmagenta\np98\ng2\nsVlightsteelblue\np99\nV#B0C4DE\np100\nsVolivedrab\np101\nV#6B8E23\np102\nsVlightslategray\np103\nV#778899\np104\nsVslategray\np105\nV#708090\np106\nsVlightblue\np107\nV#ADD8E6\np108\nsVmoccasin\np109\nV#FFE4B5\np110\nsVmediumspringgreen\np111\nV#00FA9A\np112\nsVlightgray\np113\nV#D3D3D3\np114\nsVseashell\np115\nV#FFF5EE\np116\nsVdarkkhaki\np117\nV#BDB76B\np118\nsVslateblue\np119\nV#6A5ACD\np120\nsVaqua\np121\ng75\nsVpalegoldenrod\np122\nV#EEE8AA\np123\nsVdeeppink\np124\nV#FF1493\np125\nsVdarkgreen\np126\nV#006400\np127\nsVblanchedalmond\np128\nV#FFEBCD\np129\nsVturquoise\np130\nV#40E0D0\np131\nsVnavy\np132\nV#000080\np133\nsVtomato\np134\nV#FF6347\np135\nsVyellowgreen\np136\nV#9ACD32\np137\nsVpeachpuff\np138\nV#FFDAB9\np139\nsV30%gray\np140\nV#464646\np141\nsVpink\np142\nV#FFC0CB\np143\nsVpalegreen\np144\nV#98FB98\np145\nsVlightskyblue\np146\nV#87CEFA\np147\nsVchartreuse\np148\nV#7FFF00\np149\nsVmediumorchid\np150\nV#BA55D3\np151\nsVolive\np152\nV#808000\np153\nsVdarkorange\np154\nV#FF8C00\np155\nsVbeige\np156\nV#F5F5DC\np157\nsVforestgreen\np158\nV#228B22\np159\nsVmediumpurple\np160\nV#9370DB\np161\nsVmintcream\np162\nV#F5FFFA\np163\nsVhotpink\np164\nV#FF69B4\np165\nsVdarkgoldenrod\np166\nV#B8860B\np167\nsVpowderblue\np168\nV#B0E0E6\np169\nsVhoneydew\np170\nV#F0FFF0\np171\nsVsalmon\np172\nV#FA8072\np173\nsVsnow\np174\nV#FFFAFA\np175\nsVmistyrose\np176\nV#FFE4E1\np177\nsVkhaki\np178\nV#F0E68C\np179\nsVmediumaquamarine\np180\nV#66CDAA\np181\nsVdarksalmon\np182\nV#E9967A\np183\nsValiceblue\np184\nV#F0F8FF\np185\nsVdarkturquoise\np186\nV#00CED1\np187\nsVlightyellow\np188\nV#FFFFE0\np189\nsVwheat\np190\nV#F5DEB3\np191\nsVlightseagreen\np192\nV#20B2AA\np193\nsVlightcyan\np194\nV#E0FFFF\np195\nsVantiquewhite\np196\nV#FAEBD7\np197\nsVsaddlebrown\np198\nV#8B4513\np199\nsVmediumseagreen\np200\nV#3CB371\np201\nsV70%gray\np202\nV#B2B2B2\np203\nsVsienna\np204\nV#A0522D\np205\nsVcornflowerblue\np206\nV#6495ED\np207\nsVseagreen\np208\nV#2E8B57\np209\nsVfloralwhite\np210\nV#FFFAF0\np211\nsVivory\np212\nV#FFFFF0\np213\nsVcornsilk\np214\nV#FFF8DC\np215\nsVindianred\np216\nV#CD5C5C\np217\nsVplum\np218\nV#DDA0DD\np219\nsV90%gray\np220\nV#E6E6E6\np221\nsVgreenyellow\np222\nV#ADFF2F\np223\nsVteal\np224\nV#008080\np225\nsVbrown\np226\nV#A52A2A\np227\nsVdarkslategray\np228\nV#2F4F4F\np229\nsVpurple\np230\nV#800080\np231\nsVviolet\np232\nV#EE82EE\np233\nsVdeepskyblue\np234\nV#00BFFF\np235\nsVghostwhite\np236\nV#F8F8FF\np237\nsVburlywood\np238\nV#DEB887\np239\nsVblue\np240\nV#0000FF\np241\nsVcrimson\np242\nV#DC143C\np243\nsVindigo\np244\nV#4B0082\np245\nsV20%gray\np246\nV#333333\np247\nsVdarkmagenta\np248\nV#8B008B\np249\nsV80%gray\np250\nV#CCCCCC\np251\nsVlightgoldenrodyellow\np252\nV#FAFAD2\np253\nsVtan\np254\nV#D2B48C\np255\nsVlimegreen\np256\nV#32CD32\np257\nsVlemonchiffon\np258\nV#FFFACD\np259\nsVbisque\np260\nV#FFE4C4\np261\nsVfirebrick\np262\nV#B22222\np263\nsVnavajowhite\np264\nV#FFDEAD\np265\nsVnone\np266\ng4\nsVmaroon\np267\nV#800000\np268\nsV50%gray\np269\nV#7F7F7F\np270\nsVdarkgray\np271\nV#A9A9A9\np272\nsVorange\np273\nV#FFA500\np274\nsVlavenderblush\np275\nV#FFF0F5\np276\nsVdarkorchid\np277\nV#9932CC\np278\nsVlavender\np279\nV#E6E6FA\np280\nsVspringgreen\np281\nV#00FF7F\np282\nsVthistle\np283\nV#D8BFD8\np284\nsVlinen\np285\nV#FAF0E6\np286\nsVdarkolivegreen\np287\nV#556B2F\np288\nsVdarkslateblue\np289\nV#483D8B\np290\nsVgray\np291\nV#808080\np292\nsVdarkviolet\np293\nV#9400D3\np294\nsVperu\np295\nV#CD853F\np296\nsVsandybrown\np297\nV#F4A460\np298\nsVmediumslateblue\np299\nV#7B68EE\np300\nsVlightgrey\np301\ng114\ns."
        )
    return colornames.cached


def salabim_logo_red_white_200():
    #  picture created from salabim logo red white 200.png
    from PIL import Image
    import io
    import base64

    if not hasattr(salabim_logo_red_white_200, "cached"):
        salabim_logo_red_white_200.cached = Image.open(
            io.BytesIO(
                base64.b64decode(
                    ""
                    "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"  # NOQA
                    "".encode("ascii")
                )
            )
        ).convert("RGBA")
    return salabim_logo_red_white_200.cached


def salabim_logo_red_black_200():
    #  picture created from salabim logo red black 200.png
    from PIL import Image
    import io
    import base64

    if not hasattr(salabim_logo_red_black_200, "cached"):
        salabim_logo_red_black_200.cached = Image.open(
            io.BytesIO(
                base64.b64decode(
                    ""
                    "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"  # NOQA
                    "".encode("ascii")
                )
            )
        ).convert("RGBA")
    return salabim_logo_red_black_200.cached


def hex_to_rgb(v):
    if v == "":
        return (0, 0, 0, 0)
    if v[0] == "#":
        v = v[1:]
    if len(v) == 6:
        return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    if len(v) == 8:
        return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16), int(v[6:8], 16)
    raise ValueError("Incorrect value" + str(v))


spec_to_image_cache = {}


def spec_to_image(spec):
    """
    convert an image specification to an image

    Parameters
    ----------
    image : str or PIL.Image.Image
        if str: filename of file to be loaded |n|
        if null string: dummy image will be returned |n|
        if PIL.Image.Image: return this image untranslated

    Returns
    -------
    image : PIL.Image.Image
    """
    can_animate(try_only=True)  # to load PIL
    if isinstance(spec, (str, Path)):
        if spec not in spec_to_image_cache:
            if spec == "":
                im = Image.new("RGBA", (1, 1), (0, 0, 0, 0))  # (0, 0) raises an error on some platforms
            else:
                if Path(spec).suffix.lower() == ".heic":
                    if Pythonista:
                        raise ImportError(".heic files not supported under Pythonista.")
                    try:
                        from pillow_heif import register_heif_opener
                    except ImportError:
                        raise ImportError("pillow_heif is required for reading .heic files. Install with pip install pillow_heif")
                    register_heif_opener()
                im = Image.open(spec)
                im = im.convert("RGBA")
            spec_to_image_cache[spec] = im

        return spec_to_image_cache[spec]
    else:
        return spec


def spec_to_image_width(spec):
    image = spec_to_image(spec)
    return image.size[0]


def _time_unit_lookup(descr):

    lookup = {
        "years": 1 / (86400 * 365),
        "weeks": 1 / (86400 * 7),
        "days": 1 / 86400,
        "hours": 1 / 3600,
        "minutes": 1 / 60,
        "seconds": 1,
        "milliseconds": 1e3,
        "microseconds": 1e6,
        "n/a": None,
    }

    if descr not in lookup:
        raise ValueError("time_unit " + descr + " not supported")
    return lookup[descr]


def _time_unit_factor(time_unit, env):
    if env is None:
        env = g.default_env
    if time_unit is None:
        return 1
    if (env is None) or (env._time_unit is None):
        raise AttributeError("time unit not set.")

    return env._time_unit / _time_unit_lookup(time_unit)


def _i(p, v0, v1):
    if v0 == v1:
        return v0  # avoid rounding problems
    if (v0 is None) or (v1 is None):
        return None
    return (1 - p) * v0 + p * v1


def interpolate(t, t0, t1, v0, v1):
    """
    does linear interpolation

    Parameters
    ----------
    t : float
        value to be interpolated from

    t0: float
        f(t0)=v0

    t1: float
        f(t1)=v1

    v0: float, list or tuple
        f(t0)=v0

    v1: float, list or tuple
        f(t1)=v1 |n|
        if list or tuple, len(v0) should equal len(v1)

    Returns
    -------
    linear interpolation between v0 and v1 based on t between t0 and t1 : float or tuple

    Note
    ----
    Note that no extrapolation is done, so if t<t0 ==> v0  and t>t1 ==> v1 |n|
    This function is heavily used during animation.
    """
    if v0 == v1:
        return v0

    if t0 > t1:
        (t0, t1) = (t1, t0)
        (v0, v1) = (v1, v0)
    if t1 == inf:
        return v0
    if t0 == t1:
        return v1
    if t <= t0:
        return v0
    if t >= t1:
        return v1
    p = (0.0 + t - t0) / (t1 - t0)
    if isinstance(v0, (list, tuple)):
        return tuple((_i(p, x0, x1) for x0, x1 in zip(v0, v1)))
    else:
        return _i(p, v0, v1)


def searchsorted(a, v, side="left"):
    """
    search sorted

    Parameters
    ----------
    a : iterable
        iterable to be searched in, must be non descending

    v : float
        value to be searched for

    side : string
        If ‘left’ (default) the index of the first suitable location found is given.
        If ‘right’, return the last such index.
        If there is no suitable index, return either 0 or N (where N is the length of a).

    Returns
    -------
    Index where v should be inserted to maintain order : int

    Note
    ----
    If numpy is installed, uses numpy.searchstarted
    """

    if has_numpy():
        return numpy.searchsorted(a, v, side)

    if side == "left":
        return bisect.bisect_left(a, v)
    if side == "right":
        return bisect.bisect_right(a, v)
    raise ValueError(f"{repr(side)} is an invalid value for the keyword 'side'")


def arange(start, stop, step=1):
    """
    arange (like numpy)

    Parameters
    ----------
    start : float
        start value

    stop: : float
        stop value

    step : float
        default: 1

    Returns
    -------
    Iterable

    Note
    ----
    If numpy is installed, uses numpy.arange
    """
    if has_numpy():
        return numpy.arange(start, stop, step)

    result = []
    value = start
    while True:
        if (step > 0 and value >= stop) or (step < 0 and value <= stop):
            return result
        result.append(value)
        value += step


def linspace(start, stop, num, endpoint=True):
    """
    like numpy.linspace, but returns a list

    Parameters
    ----------
    start : float
        start of the space

    stop : float
        stop of the space

    num : int
        number of points in the space

    endpoint : bool
        if True (default), stop is last point in the space |n|
        if False, space ends before stop
    """
    if num == 0:
        return []
    if num == 1:
        return [start]
    if endpoint:
        step = (stop - start) / (num - 1)
    else:
        step = (stop - start) / num

    return [start + step * i for i in range(num)]


def interp(x, xp, fp, left=None, right=None):
    """
    linear interpolatation

    Parameters
    ----------
    x : float
        target x-value

    xp : list of float, tuples or lists
        values on the x-axis

    fp : list of float, tuples of lists
        values on the y-axis |n|
        should be same length as  p

    Returns
    -------
    interpolated value : float, tuple or list

    Notes
    -----
    If x < xp[0], fp[0] will be returned |n|
    If x > xp[-1], fp[-1] will be returned |n|

    This function is similar to the numpy interp function.
    """
    if len(xp) != len(fp):
        raise ValueError("xp and yp are not the same length")
    if len(xp) == 0:
        raise ValueError("list of sample points is empty")

    if x < xp[0]:
        return fp[0] if left is None else left
    if x > xp[-1]:
        return fp[-1] if right is None else right
    if len(xp) == 1:
        return fp[0]

    i = bisect.bisect_right(xp, x)

    if i >= len(xp):
        return fp[-1]

    if isinstance(fp[0], (tuple, list)):
        return type(fp[0])(el_i_min_1 + (el_i - el_i_min_1) * (x - xp[i - 1]) / (xp[i] - xp[i - 1]) for el_i_min_1, el_i in zip(fp[i - 1], fp[i]))

    return fp[i - 1] + (fp[i] - fp[i - 1]) * (x - xp[i - 1]) / (xp[i] - xp[i - 1])


def _set_name(name, _nameserialize, object):
    if name is None:
        name = object_to_str(object).lower() + "."
    elif len(name) <= 1:
        if name == "":
            name = object_to_str(object).lower()
        elif name == ".":
            name = object_to_str(object).lower() + "."
        elif name == ",":
            name = object_to_str(object).lower() + ","

    object._base_name = name

    if name in _nameserialize:
        sequence_number = _nameserialize[name] + 1
    else:
        if name.endswith(","):
            sequence_number = 1
        else:
            sequence_number = 0

    _nameserialize[name] = sequence_number
    if name.endswith("."):
        object._name = name + str(sequence_number)
    elif name.endswith(","):
        object._name = name[:-1] + "." + str(sequence_number)
    else:
        object._name = name
    object._sequence_number = sequence_number


def pad(txt, n):
    if n <= 0:
        return ""
    else:
        return txt.ljust(n)[:n]


def rpad(txt, n):
    return txt.rjust(n)[:n]


def fn(x, length, d):
    if math.isnan(x):
        return ("{:" + str(length) + "s}").format("")
    if x >= 10 ** (length - d - 1):
        return ("{:" + str(length) + "." + str(length - d - 3) + "e}").format(x)
    if x == int(x):
        return ("{:" + str(length - d - 1) + "d}{:" + str(d + 1) + "s}").format(int(x), "")
    return ("{:" + str(length) + "." + str(d) + "f}").format(x)


def _checkrandomstream(randomstream):
    if not isinstance(randomstream, random.Random):
        raise TypeError("Type randomstream or random.Random expected, got " + str(type(randomstream)))


def _checkismonitor(monitor):
    if not isinstance(monitor, Monitor):
        raise TypeError("Type Monitor expected, got " + str(type(monitor)))


def _checkisqueue(queue):
    if not isinstance(queue, Queue):
        raise TypeError("Type Queue expected, got " + str(type(queue)))


def type_to_typecode_off(type):
    lookup = {
        "bool": ("B", 255),
        "int8": ("b", -128),
        "uint8": ("B", 255),
        "int16": ("h", -32768),
        "uint16": ("H", 65535),
        "int32": ("i", -2147483648),
        "uint32": ("I", 4294967295),
        "int64": ("l", -9223372036854775808),
        "uint64": ("L", 18446744073709551615),
        "float": ("d", -inf),
        "double": ("d", -inf),
        "any": ("", -inf),
    }
    return lookup[type]


def do_force_numeric(arg):
    result = []
    for v in arg:
        if isinstance(v, numbers.Number):
            result.append(v)
        else:
            try:
                if int(v) == float(v):
                    result.append(int(v))
                else:
                    result.append(float(v))
            except (ValueError, TypeError):
                result.append(0)

    return result


def deep_flatten(arg):
    if hasattr(arg, "__iter__") and not isinstance(arg, str):
        for x in arg:
            #  the two following lines are equivalent to 'yield from deep_flatten(x)' (not supported in Python 2.7)
            for xx in deep_flatten(x):
                yield xx
    else:
        yield arg


def merge_blanks(*arg):
    """
    merges all non blank elements of l, separated by a blank

    Parameters
    ----------
    *arg : elements to be merged : str

    Returns
    -------
    string with merged elements of arg : str
    """
    return " ".join(x for x in arg if x)


def normalize(s):
    return "".join(c for c in s.upper() if c.isalpha() or c.isdigit())


def _urgenttxt(urgent):
    if urgent:
        return "!"
    else:
        return " "


def _prioritytxt(priority):
    return ""


def object_to_str(object, quoted=False):
    add = '"' if quoted else ""
    return add + type(object).__name__ + add


def _get_caller_frame():
    stack = inspect.stack()
    filename0 = inspect.getframeinfo(stack[0][0]).filename
    for i in range(len(inspect.stack())):
        frame = stack[i][0]
        if filename0 != inspect.getframeinfo(frame).filename:
            break
    return frame


def return_or_print(result, as_str, file):
    result = "\n".join(result)
    if as_str:
        return result
    else:
        if file is None:
            print(result)
        else:
            print(result, file=file)


def _call(c, t, self):
    """
    special function to support scalars, methods (with one parameter) and function with zero, one or two parameters
    """
    if callable(c):
        if inspect.isfunction(c):
            nargs = c.__code__.co_argcount
            if nargs == 0:
                return c()
            if nargs == 1:
                return c(t)
            return c(self, t)
        if inspect.ismethod(c):
            return c(t)
    return c


def de_none(lst):
    if lst is None:
        return None
    lst = list(lst)  # it is necessary to convert to list, because input maybe a tuple or even a deque
    result = lst[:2]
    for item in lst[2:]:
        if item is None:
            result.append(result[-2])
        else:
            result.append(item)
    return result


def statuses():
    """
    tuple of all statuses a component can be in, in alphabetical order.
    """

    return tuple("current data interrupted passive requesting scheduled standby waiting".split(" "))


current = "current"
data = "data"
interrupted = "interrupted"
passive = "passive"
requesting = "requesting"
scheduled = "scheduled"
standby = "standby"
waiting = "waiting"


def random_seed(seed=None, randomstream=None, set_numpy_random_seed=True):
    """
    Reseeds a randomstream

    Parameters
    ----------
    seed : hashable object, usually int
        the seed for random, equivalent to random.seed() |n|
        if "*", a purely random value (based on the current time) will be used
        (not reproducable) |n|
        if the null string, no action on random is taken |n|
        if None (the default), 1234567 will be used.

    set_numpy_random_seed : bool
        if True (default), numpy.random.seed() will be called with the given seed. |n|
        This is particularly useful when using External distributions. |n|
        If numpy is not installed, this parameter is ignored |n|
        if False, numpy.random.seed is not called.

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
    """
    if randomstream is None:
        randomstream = random
    if seed != "":
        if seed is None:
            seed = 1234567
        elif seed == "*":
            seed = None
        random.seed(seed)
        if set_numpy_random_seed and has_numpy():
            numpy.random.seed(seed)


_random_seed = random_seed  # used by Environment.__init__


def resize_with_pad(im, target_width, target_height):
    """
    Resize PIL image keeping ratio and using black background.
    """
    if im.height == target_width and im.width == target_height:
        return im
    target_ratio = target_height / target_width
    im_ratio = im.height / im.width
    if target_ratio > im_ratio:
        # It must be fixed by width
        resize_width = target_width
        resize_height = round(resize_width * im_ratio)
    else:
        # Fixed by height
        resize_height = target_height
        resize_width = round(resize_height / im_ratio)

    image_resize = im.resize((resize_width, resize_height), Image.ANTIALIAS)
    background = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 255))
    offset = (round((target_width - resize_width) / 2), round((target_height - resize_height) / 2))
    background.paste(image_resize, offset)
    return background.convert("RGB")


class _AnimateIntro(Animate3dBase):
    def __init__(self, env):
        self.env = env
        super().__init__()

    def setup(self):
        self.layer = -math.inf
        self.field_of_view_y = 45
        self.z_near = 0.1
        self.z_far = 100000
        self.x_eye = 4
        self.y_eye = 4
        self.z_eye = 4
        self.x_center = 0
        self.y_center = 0
        self.z_center = 0
        self.model_lights_pname = None
        self.model_lights_param = (0.42, 0.42, 0.42, 1)
        self.lights_light = None
        self.lights_pname = None
        self.lights_param = (-1, -1, 1, 0)
        self.lag = 1

        self.register_dynamic_attributes("field_of_view_y z_near z_far x_eye y_eye z_eye x_center y_center z_center")
        self.register_dynamic_attributes("model_lights_pname model_lights_param lights_light lights_pname lights_param")

    def draw(self, t):
        x_eye = self.x_eye(t)
        y_eye = self.y_eye(t)
        z_eye = self.z_eye(t)
        x_center = self.x_center(t)
        y_center = self.y_center(t)
        z_center = self.z_center(t)
        x_up = 0
        y_up = 0

        dx = x_eye - x_center
        dy = y_eye - y_center
        dz = z_eye - z_center
        dxy = math.hypot(dx, dy)
        if dy > 0:
            dxy = -dxy
        alpha = math.degrees(math.atan2(dxy, dz))
        if alpha < 0:
            z_up = +1
        else:
            z_up = 1

        if self.model_lights_pname(t) is None:
            self.model_lights_pname = gl.GL_LIGHT_MODEL_AMBIENT  # in principal only at first call
        if self.lights_light(t) is None:
            self.lights_light = gl.GL_LIGHT0  # in principal only at first call
        if self.lights_pname(t) is None:
            self.lights_pname = gl.GL_POSITION  # in principal only at first call

        background_color = list(self.env.colorspec_to_gl_color(self.env._background3d_color)) + [0.0]
        gl.glClearColor(*background_color)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glMatrixMode(gl.GL_PROJECTION)

        gl.glLoadIdentity()
        glu.gluPerspective(self.field_of_view_y(t), glut.glutGet(glut.GLUT_WINDOW_WIDTH) / glut.glutGet(glut.GLUT_WINDOW_HEIGHT), self.z_near(t), self.z_far(t))

        glu.gluLookAt(x_eye, y_eye, z_eye, x_center, y_center, z_center, x_up, y_up, z_up)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glLightModelfv(self.model_lights_pname(t), self.model_lights_param(t))
        gl.glLightfv(self.lights_light(t), self.lights_pname(t), self.lights_param(t))
        gl.glEnable(gl.GL_LIGHT0)

        gl.glMatrixMode(gl.GL_MODELVIEW)

        gl.glLoadIdentity()


class _AnimateExtro(Animate3dBase):
    def __init__(self, env):
        self.env = env
        super().__init__()

    def setup(self):
        self.layer = math.inf

    def draw(self, t):
        if self.env.an_objects_over3d:
            for ao in sorted(self.env.an_objects_over3d, key=lambda obj: (-obj.layer(t), obj.sequence)):
                ao.make_pil_image(t - self.env._offset)

                if ao._image_visible:
                    ao.x1 = ao._image_x
                    ao.x2 = ao._image_x + ao._image.size[0]
                    ao.y1 = ao._image_y
                    ao.y2 = ao._image_y + ao._image.size[1]

            overlap = False
            ao2_set = self.env.an_objects_over3d.copy()
            for ao1 in self.env.an_objects_over3d:
                ao2_set.discard(ao1)
                if ao1._image_visible:
                    for ao2 in ao2_set:
                        if ao2._image_visible and ao1 != ao2:
                            x_match = ao1.x1 <= ao2.x2 and ao2.x1 <= ao1.x2
                            y_match = ao1.y1 <= ao2.y2 and ao2.y1 <= ao1.y2
                            if x_match and y_match:
                                overlap = True
                                break
                    if overlap:
                        break

            gl.glEnable(gl.GL_TEXTURE_2D)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()

            gl.glOrtho(0, self.env._width3d, 0, self.env._height3d, -1, 1)
            if overlap:
                overlay_image = Image.new("RGBA", (self.env._width3d, self.env._height3d), (0, 0, 0, 0))
                for ao in sorted(self.env.an_objects_over3d, key=lambda obj: (-obj.layer(t), obj.sequence)):
                    if ao._image_visible:
                        overlay_image.paste(ao._image, (int(ao._image_x), int(self.env._height3d - ao._image_y - ao._image.size[1])), ao._image)
                    imdata = overlay_image.tobytes("raw", "RGBA", 0, -1)

                w = overlay_image.size[0]
                h = overlay_image.size[1]

                gl.glRasterPos(0, 0)
                gl.glDrawPixels(w, h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, imdata)

            else:
                for ao in sorted(self.env.an_objects_over3d, key=lambda obj: (-obj.layer(self.env._t), obj.sequence)):
                    if ao._image_visible:
                        imdata = ao._image.tobytes("raw", "RGBA", 0, -1)
                        w = ao._image.size[0]
                        h = ao._image.size[1]
                        gl.glRasterPos(int(ao._image_x), int(ao._image_y))
                        gl.glDrawPixels(w, h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, imdata)

            gl.glDisable(gl.GL_BLEND)

        glut.glutSwapBuffers()
        glut.glutMainLoopEvent()


class Animate3dObj(Animate3dBase):
    """
    Creates a 3D animation object from an .obj file

    Parameters
    ----------
    filename : str or Path
        obj file to be read (default extension .obj) |n|
        if there are .mtl or .jpg required by this file, they should be available

    x : float
        x position (default 0)

    y : float
        y position (default 0)

    z : float
        z position (default 0)

    x_angle : float
        angle along x axis (default: 0)

    y_angle : float
        angle along y axis (default: 0)

    z_angle : float
        angle along z axis (default: 0)

    x_translate : float
        translation in x direction (default: 0)

    y_translate : float
        translation in y direction (default: 0)

    z_translate : float
        translation in z direction (default: 0)

    x_scale : float
        scaling in x direction (default: 1)

    y_translate : float
        translation in y direction (default: 1)

    z_translate : float
        translation in z direction (default: 1)

    show_warnings : bool
        as pywavefront does not support all obj commands, reading the file sometimes leads
        to (many) warning log messages |n|
        with this flag, they can be turned off (the deafult)

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|

    Note
    ----
    This method requires the pywavefront and pyglet module to be installed
    """

    def __init__(
        self,
        filename,
        x=0,
        y=0,
        z=0,
        x_angle=0,
        y_angle=0,
        z_angle=0,
        x_translate=0,
        y_translate=0,
        z_translate=0,
        x_scale=1,
        y_scale=1,
        z_scale=1,
        show_warnings=False,
        visible=True,
        arg=None,
        layer=0,
        parent=None,
        env=None,
        **kwargs,
    ):

        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)

        self.x = x
        self.y = y
        self.z = z
        self.x_angle = x_angle
        self.y_angle = y_angle
        self.z_angle = z_angle
        self.x_translate = x_translate
        self.y_translate = y_translate
        self.z_translate = z_translate

        self.x_scale = x_scale
        self.y_scale = y_scale
        self.z_scale = z_scale
        self.filename = filename
        self.show_warnings = show_warnings

        self.register_dynamic_attributes("x y z x_angle y_angle z_angle x_translate y_translate z_translate x_scale y_scale z_scale filename show_warnings")
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0

        if "pywavefront" not in sys.modules:
            global pywavefront
            global visualization
            try:
                import pywavefront
                from pywavefront import visualization
            except ImportError:
                pywavefront = None

    def draw(self, t):
        if pywavefront is None:
            raise ImportError("Animate3dObj requires pywavefront. Not found")

        obj_filename = Path(self.filename(t))
        if not obj_filename.suffix:
            obj_filename = obj_filename.with_suffix(".obj")
        obj_filename = obj_filename.resolve()

        if obj_filename not in self.env.obj_filenames:
            save_logging_level = logging.root.level
            if not self.show_warnings(t):
                logging.basicConfig(level=logging.ERROR)

            with open(obj_filename, "r") as obj_file:

                create_materials = False
                obj_file_path = Path(obj_filename).resolve().parent
                save_cwd = os.getcwd()
                os.chdir(obj_file_path)
                for f in obj_file:
                    if f.startswith("mtllib "):
                        mtllib_filename = Path(f[7:].strip())
                        if mtllib_filename.is_file():
                            create_materials = True
                        break
            os.chdir(save_cwd)
            logging.basicConfig(level=save_logging_level)

            self.env.obj_filenames[obj_filename] = pywavefront.Wavefront(obj_filename, create_materials=create_materials)

        obj = self.env.obj_filenames[obj_filename]

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glTranslate(self.x(t) + self.x_offset, self.y(t) + self.y_offset, self.z(t) + self.z_offset)
        gl.glRotate(self.z_angle(t), 0.0, 0.0, 1.0)
        gl.glRotate(self.y_angle(t), 0.0, 1.0, 0.0)
        gl.glRotate(self.x_angle(t), 1.0, 0.0, 0.0)
        gl.glTranslate(self.x_translate(t), self.y_translate(t), self.z_translate(t))
        gl.glScale(self.x_scale(t), self.y_scale(t), self.z_scale(t))
        visualization.draw(obj)
        gl.glPopMatrix()


class Animate3dRectangle(Animate3dBase):
    """
    Creates a 3D rectangle

    Parameters
    ----------
    x0 : float
        lower left x position (default 0)

    y0 : float
        lower left y position (default 0)

    x1 : float
        upper right x position (default 1)

    y1 : float
        upper right y position (default 1)

    z : float
        z position of rectangle (default 0)

    color : colorspec
        color of the rectangle (default "white")

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|
    """

    def __init__(self, x0=0, y0=0, x1=1, y1=1, z=0, color="white", visible=True, arg=None, layer=0, parent=None, env=None, **kwargs):
        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)

        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.z = z
        self.color = color
        self.register_dynamic_attributes("x0 y0 x1 y1 z color")

    def draw(self, t):
        gl_color = self.env.colorspec_to_gl_color(self.color(t))
        x0 = self.x0(t)
        y0 = self.y0(t)
        x1 = self.x1(t)
        y1 = self.y1(t)
        z = self.z(t)
        draw_rectangle3d(x0=x0, y0=y0, z=z, x1=x1, y1=y1, gl_color=gl_color)


class Animate3dLine(Animate3dBase):
    """
    Creates a 3D line

    Parameters
    ----------
    x0 : float
        x coordinate of start point (default 0)

    y0 : float
        y coordinate of start point (default 0)

    z0 : float
        z coordinate of start point (default 0)

    x1 : float
        x coordinate of end point (default 0)

    y1 : float
        y coordinate of end point (default 0)

    z1 : float
        z coordinate of end point (default 0)

    color : colorspec
        color of the line (default "white")

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|
    """

    def __init__(self, x0=0, y0=0, z0=0, x1=1, y1=1, z1=0, color="white", visible=True, arg=None, layer=0, parent=None, env=None, **kwargs):
        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)

        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.color = color
        self.register_dynamic_attributes("x0 y0 z0 x1 y1 z1 color")

    def draw(self, t):
        gl_color = self.env.colorspec_to_gl_color(self.color(t))
        x0 = self.x0(t)
        y0 = self.y0(t)
        z0 = self.z0(t)
        x1 = self.x1(t)
        y1 = self.y1(t)
        z1 = self.z1(t)
        draw_line3d(x0=x0, y0=y0, z0=z0, x1=x1, y1=y1, z1=z1, gl_color=gl_color)


class Animate3dGrid(Animate3dBase):
    """
    Creates a 3D grid

    Parameters
    ----------
    x_range : iterable
        x coordinates of grid lines (default [0])

    y_range : iterable
        y coordinates of grid lines (default [0])

    z_range : iterable
        z coordinates of grid lines (default [0])

    color : colorspec
        color of the line (default "white")

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|
    """

    def __init__(self, x_range=[0], y_range=[0], z_range=[0], color="white", visible=True, arg=None, layer=0, parent=None, env=None, **kwargs):
        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)

        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.color = color
        self.register_dynamic_attributes("x_range y_range z_range color")

    def draw(self, t):
        gl_color = self.env.colorspec_to_gl_color(self.color(t))
        x_range = list(self.x_range(t))
        y_range = list(self.y_range(t))
        z_range = list(self.z_range(t))

        for x in x_range:
            for y in y_range:
                draw_line3d(x0=x, y0=y, z0=min(z_range), x1=x, y1=y, z1=max(z_range), gl_color=gl_color)

            for z in z_range:
                draw_line3d(x0=x, y0=min(y_range), z0=z, x1=x, y1=max(y_range), z1=z, gl_color=gl_color)

        for y in y_range:
            for x in x_range:
                draw_line3d(x0=x, y0=y, z0=min(z_range), x1=x, y1=y, z1=max(z_range), gl_color=gl_color)

            for z in z_range:
                draw_line3d(x0=min(x_range), y0=y, z0=z, x1=max(x_range), y1=y, z1=z, gl_color=gl_color)

        for z in z_range:
            for x in x_range:
                draw_line3d(x0=x, y0=min(y_range), z0=z, x1=x, y1=max(y_range), z1=z, gl_color=gl_color)

            for y in y_range:
                draw_line3d(x0=min(x_range), y0=y, z0=z, x1=max(x_range), y1=y, z1=z, gl_color=gl_color)


class Animate3dBox(Animate3dBase):
    """
    Creates a 3D box

    Parameters
    ----------
    x_len : float
        length of the box in x direction (deffult 1)

    y_len : float
        length of the box in y direction (default 1)

    z_len : float
        length of the box in z direction (default 1)

    x : float
        x position of the box (default 0)

    y : float
        y position of the box (default 0)

    z : float
        z position of the box (default 0)

    z_angle : float
        angle around the z-axis (default 0)

    x_ref : int
        if -1, the x parameter refers to the 'end' of the box |n|
        if  0, the x parameter refers to the center of the box (default) |n|
        if  1, the x parameter refers to the 'start' of the box

    y_ref : int
        if -1, the y parameter refers to the 'end' of the box |n|
        if  0, the y parameter refers to the center of the box (default) |n|
        if  1, the y parameter refers to the 'start' of the box

    z_ref : int
        if -1, the z parameter refers to the 'end' of the box |n|
        if  0, the z parameter refers to the center of the box (default) |n|
        if  1, the z parameter refers to the 'start' of the box

    color : colorspec
        color of the box (default "white") |n|
        if the color is "" (or the alpha is 0), the sides will not be colored at all

    edge_color : colorspec
        color of the edges of the (default "") |n|
        if the color is "" (or the alpha is 0), the edges will not be drawn at all

    shaded : bool
        if False (default), all sides will be colored with color
        if True, the various sides will have a sligtly different darkness, thus resulting in a pseudo shaded object

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|
    """

    def __init__(
        self,
        x_len=1,
        y_len=1,
        z_len=1,
        x=0,
        y=0,
        z=0,
        z_angle=0,
        x_ref=0,
        y_ref=0,
        z_ref=0,
        color="white",
        edge_color="",
        shaded=False,
        visible=True,
        arg=None,
        layer=0,
        parent=None,
        env=None,
        **kwargs,
    ):
        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)

        self.x_len = x_len
        self.y_len = y_len
        self.z_len = z_len
        self.x = x
        self.y = y
        self.z = z
        self.z_angle = z_angle
        self.x_ref = x_ref
        self.y_ref = y_ref
        self.z_ref = z_ref
        self.color = color
        self.edge_color = edge_color
        self.shaded = shaded
        self.register_dynamic_attributes("x_len y_len z_len x y z z_angle x_ref y_ref z_ref color edge_color shaded")
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0

    def draw(self, t):
        gl_color, show = self.env.colorspec_to_gl_color_alpha(self.color(t))
        gl_edge_color, show_edge = self.env.colorspec_to_gl_color_alpha(self.edge_color(t))

        draw_box3d(
            x_len=self.x_len(t),
            y_len=self.y_len(t),
            z_len=self.z_len(t),
            x=self.x(t) + self.x_offset,
            y=self.y(t) + self.y_offset,
            z=self.z(t) + self.z_offset,
            x_angle=0,
            y_angle=0,
            z_angle=self.z_angle(t),
            x_ref=self.x_ref(t),
            y_ref=self.y_ref(t),
            z_ref=self.z_ref(t),
            gl_color=gl_color,
            show=show,
            edge_gl_color=gl_edge_color,
            show_edge=show_edge,
            shaded=self.shaded(t),
        )


class Animate3dBar(Animate3dBase):
    """
    Creates a 3D bar between two given points

    Parameters
    ----------
    x0 : float
        x coordinate of start point (default 0)

    y0 : float
        y coordinate of start point (default 0)

    z0 : float
        z coordinate of start point (default 0)

    x1 : float
        x coordinate of end point (default 0)

    y1 : float
        y coordinate of end point (default 0)

    z1 : float
        z coordinate of end point (default 0)

    color : colorspec
        color of the bar (default "white") |n|
        if the color is "" (or the alpha is 0), the sides will not be colored at all

    edge_color : colorspec
        color of the edges of the (default "") |n|
        if the color is "" (or the alpha is 0), the edges will not be drawn at all

    shaded : bool
        if False (default), all sides will be colored with color
        if True, the various sides will have a sligtly different darkness, thus resulting in a pseudo shaded object

    bar_width : float
        width of the bar (default 1)

    bar_width_2 : float
        if not specified both sides will have equal width (bar_width) |n|
        if specified, the bar will have width bar_width and bar_width_2

    rotation_angle : float
        rotation of the bar in degrees (default 0)

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|
    """

    def __init__(
        self,
        x0=0,
        y0=0,
        z0=0,
        x1=1,
        y1=1,
        z1=1,
        color="white",
        edge_color="",
        bar_width=1,
        bar_width_2=None,
        shaded=False,
        rotation_angle=0,
        show_lids=True,
        visible=True,
        arg=None,
        layer=0,
        parent=None,
        env=None,
        **kwargs,
    ):
        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)

        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.color = color
        self.edge_color = edge_color
        self.bar_width = bar_width
        self.bar_width_2 = bar_width_2
        self.shaded = shaded
        self.rotation_angle = rotation_angle
        self.show_lids = show_lids
        self.register_dynamic_attributes("x0 y0 z0 x1 y1 z1 color bar_width bar_width_2 edge_color shaded rotation_angle show_lids")
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0

    def draw(self, t):
        x0, x1 = self.x0(t) + self.x_offset, self.x1(t) + self.x_offset
        y0, y1 = self.y0(t) + self.y_offset, self.y1(t) + self.y_offset
        z0, z1 = self.z0(t) + self.z_offset, self.z1(t) + self.z_offset

        bar_width = self.bar_width(t)
        bar_width_2 = self.bar_width_2(t)
        gl_color, show = self.env.colorspec_to_gl_color_alpha(self.color(t))
        edge_gl_color, show_edge = self.env.colorspec_to_gl_color_alpha(self.edge_color(t))
        shaded = self.shaded(t)
        rotation_angle = self.rotation_angle(t)
        show_lids = self.show_lids(t)
        draw_bar3d(
            x0=x0,
            y0=y0,
            z0=z0,
            x1=x1,
            y1=y1,
            z1=z1,
            bar_width=bar_width,
            bar_width_2=bar_width_2,
            gl_color=gl_color,
            show=show,
            edge_gl_color=edge_gl_color,
            show_edge=show_edge,
            shaded=shaded,
            rotation_angle=rotation_angle,
            show_lids=show_lids,
        )


class Animate3dCylinder(Animate3dBase):
    """
    Creates a 3D cylinder between two given points

    Parameters
    ----------
    x0 : float
        x coordinate of start point (default 0)

    y0 : float
        y coordinate of start point (default 0)

    z0 : float
        z coordinate of start point (default 0)

    x1 : float
        x coordinate of end point (default 0)

    y1 : float
        y coordinate of end point (default 0)

    z1 : float
        z coordinate of end point (default 0)

    color : colorspec
        color of the cylinder (default "white")

    number_of_sides : int
        number of sides of the cylinder (default 8) |n|
        must be >= 3

    rotation_angle : float
        rotation of the bar in degrees (default 0)

    show_lids : bool
        if True (default), the lids will be drawn
        if False, tyhe cylinder will be open at both sides

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|
    """

    def __init__(
        self,
        x0=0,
        y0=0,
        z0=0,
        x1=1,
        y1=1,
        z1=1,
        color="white",
        radius=1,
        number_of_sides=8,
        rotation_angle=0,
        show_lids=True,
        visible=True,
        arg=None,
        layer=0,
        parent=None,
        env=None,
        **kwargs,
    ):
        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.color = color
        self.radius = radius
        self.number_of_sides = number_of_sides
        self.rotation_angle = rotation_angle
        self.show_lids = show_lids
        self.register_dynamic_attributes("x0 y0 z0 x1 y1 z1 color radius number_of_sides rotation_angle show_lids")
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0

    def draw(self, t):
        x0, x1 = self.x0(t) + self.x_offset, self.x1(t) + self.x_offset
        y0, y1 = self.y0(t) + self.y_offset, self.y1(t) + self.y_offset
        z0, z1 = self.z0(t) + self.z_offset, self.z1(t) + self.z_offset

        gl_color = self.env.colorspec_to_gl_color(self.color(t))
        rotation_angle = self.rotation_angle(t)
        radius = self.radius(t)
        number_of_sides = self.number_of_sides(t)
        show_lids = self.show_lids(t)
        draw_cylinder3d(
            x0=x0,
            y0=y0,
            z0=z0,
            x1=x1,
            y1=y1,
            z1=z1,
            radius=radius,
            number_of_sides=number_of_sides,
            gl_color=gl_color,
            rotation_angle=rotation_angle,
            show_lids=show_lids,
        )


class Animate3dSphere(Animate3dBase):
    """
    Creates a 3D box

    Parameters
    ----------
    radius : float
        radius of the sphere

    x : float
        x position of the box (default 0)

    y : float
        y position of the box (default 0)

    z : float
        z position of the box (default 0)

    color : colorspec
        color of the sphere (default "white")

    visible : bool
        visible |n|
        if False, animation object is not shown, shown otherwise
        (default True)

    layer : int
         layer value |n|
         lower layer values are displayed later in the frame (default 0)

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically when the parent component is no longer accessible

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used

    Note
    ----
    All parameters, apart from parent, arg and env can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: my_x |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called |n|
    """

    def __init__(
        self,
        radius=1,
        x=0,
        y=0,
        z=0,
        color="white",
        number_of_slices=32,
        number_of_stacks=None,
        visible=True,
        arg=None,
        layer=0,
        parent=None,
        env=None,
        **kwargs,
    ):
        super().__init__(visible=visible, arg=arg, layer=layer, parent=parent, env=env, **kwargs)

        self.radius = radius
        self.x = x
        self.y = y
        self.z = z
        self.color = color
        self.number_of_slices = number_of_slices
        self.number_of_stacks = number_of_stacks
        self.register_dynamic_attributes("radius x y z color number_of_slices number_of_stacks")
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0

    def draw(self, t):
        gl_color = self.env.colorspec_to_gl_color(self.color(t))
        draw_sphere3d(
            radius=self.radius(t),
            x=self.x(t) + self.x_offset,
            y=self.y(t) + self.y_offset,
            z=self.z(t) + self.z_offset,
            gl_color=gl_color,
            number_of_slices=self.number_of_slices(t),
            number_of_stacks=self.number_of_stacks(t),
        )


def draw_bar3d(
    x0=0,
    y0=0,
    z0=0,
    x1=1,
    y1=1,
    z1=1,
    gl_color=(1, 1, 1),
    show=True,
    edge_gl_color=(1, 1, 1),
    show_edge=False,
    bar_width=1,
    bar_width_2=None,
    rotation_angle=0,
    shaded=False,
    show_lids=True,
):
    """
    draws a 3d bar (should be added to the event loop by encapsulating with Animate3dBase)

    Parameters
    ----------
    x0 : int, optional
        [description], by default 0
    y0 : int, optional
        [description], by default 0
    z0 : int, optional
        [description], by default 0
    x1 : int, optional
        [description], by default 1
    y1 : int, optional
        [description], by default 1
    z1 : int, optional
        [description], by default 1
    gl_color : tuple, optional
        [description], by default (1, 1, 1)
    show : bool, optional
        [description], by default True
    edge_gl_color : tuple, optional
        [description], by default (1, 1, 1)
    show_edge : bool, optional
        [description], by default False
    bar_width : int, optional
        [description], by default 1
    bar_width_2 : [type], optional
        [description], by default None
    rotation_angle : int, optional
        [description], by default 0
    shaded : bool, optional
        [description], by default False
    show_lids : bool, optional
        [description], by default True
    """
    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0

    length = math.sqrt(dx**2 + dy**2 + dz**2)
    y_angle = -math.degrees(math.atan2(dz, math.sqrt(dx**2 + dy**2)))
    z_angle = math.degrees(math.atan2(dy, dx))
    bar_width_2 = bar_width if bar_width_2 is None else bar_width_2

    draw_box3d(
        x=x0,
        y=y0,
        z=z0,
        x_len=length,
        y_len=bar_width,
        z_len=bar_width_2,
        x_angle=rotation_angle,
        y_angle=y_angle,
        z_angle=z_angle,
        x_ref=1,
        y_ref=0,
        z_ref=0,
        gl_color=gl_color,
        show=show,
        edge_gl_color=edge_gl_color,
        show_edge=show_edge,
        shaded=shaded,
        _show_lids=show_lids,
    )


def draw_cylinder3d(x0=0, y0=0, z0=0, x1=1, y1=1, z1=1, gl_color=(1, 1, 1), radius=1, number_of_sides=8, rotation_angle=0, show_lids=True):
    """
    draws a 3d cylinder (should be added to the event loop by encapsulating with Animate3dBase)

    Parameters
    ----------
    x0 : int, optional
        [description], by default 0
    y0 : int, optional
        [description], by default 0
    z0 : int, optional
        [description], by default 0
    x1 : int, optional
        [description], by default 1
    y1 : int, optional
        [description], by default 1
    z1 : int, optional
        [description], by default 1
    gl_color : tuple, optional
        [description], by default (1, 1, 1)
    radius : int, optional
        [description], by default 1
    number_of_sides : int, optional
        [description], by default 8
    rotation_angle : int, optional
        [description], by default 0
    show_lids : bool, optional
        [description], by default True
    """
    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0

    length = math.sqrt(dx**2 + dy**2 + dz**2)
    y_angle = -math.degrees(math.atan2(dz, math.sqrt(dx**2 + dy**2)))
    z_angle = math.degrees(math.atan2(dy, dx))
    x_angle = rotation_angle
    gl.glPushMatrix()
    gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color)

    gl.glTranslate(x0, y0, z0)
    if z_angle:
        gl.glRotate(z_angle, 0.0, 0.0, 1.0)
    if y_angle:
        gl.glRotate(y_angle, 0.0, 1.0, 0.0)
    if x_angle:
        gl.glRotate(x_angle, 1.0, 0.0, 0.0)

    step_angle = 360 / number_of_sides
    start_angle = -90 + step_angle / 2

    two_d_vertices = []
    for i in range(number_of_sides):
        angle = math.radians((i * step_angle + start_angle))
        two_d_vertices.append((radius * math.cos(angle), radius * math.sin(angle)))
    two_d_vertices.append(two_d_vertices[0])

    if show_lids:
        """draw front lid"""
        gl.glBegin(gl.GL_TRIANGLE_FAN)
        gl.glNormal3f(-1, 0, 0)
        for two_d_vertex in two_d_vertices:
            gl.glVertex3f(0, two_d_vertex[0], two_d_vertex[1])
        gl.glEnd()

        """ draw back lid """
        gl.glBegin(gl.GL_TRIANGLE_FAN)
        gl.glNormal3f(1, 0, 0)
        for two_d_vertex in two_d_vertices:
            gl.glVertex3f(length, two_d_vertex[0], two_d_vertex[1])
        gl.glEnd()

    """ draw sides """
    gl.glBegin(gl.GL_QUADS)
    for i, (two_d_vertex0, two_d_vertex1) in enumerate(zip(two_d_vertices, two_d_vertices[1:])):
        a1 = math.radians((start_angle + (i + 0.5) * step_angle))
        gl.glNormal3f(0, math.cos(a1), math.sin(a1))
        gl.glVertex3f(0, *two_d_vertex0)
        gl.glVertex3f(length, *two_d_vertex0)
        gl.glVertex3f(length, *two_d_vertex1)
        gl.glVertex3f(0, *two_d_vertex1)
    gl.glEnd()

    gl.glPopMatrix()


def draw_line3d(x0=0, y0=0, z0=0, x1=1, y1=1, z1=1, gl_color=(1, 1, 1)):
    """
    draws a 3d line (should be added to the event loop by encapsulating with Animate3dBase)

    Parameters
    ----------
    x0 : int, optional
        [description], by default 0
    y0 : int, optional
        [description], by default 0
    z0 : int, optional
        [description], by default 0
    x1 : int, optional
        [description], by default 1
    y1 : int, optional
        [description], by default 1
    z1 : int, optional
        [description], by default 1
    gl_color : tuple, optional
        [description], by default (1, 1, 1)
    """
    gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color)

    gl.glBegin(gl.GL_LINES)
    gl.glVertex3f(x0, y0, z0)
    gl.glVertex3f(x1, y1, z1)
    gl.glEnd()


def draw_rectangle3d(x0=0, y0=0, z=0, x1=1, y1=1, gl_color=(1, 1, 1)):
    """
    draws a 3d rectangle (should be added to the event loop by encapsulating with Animate3dBase)

    Parameters
    ----------
    x0 : int, optional
        [description], by default 0
    y0 : int, optional
        [description], by default 0
    z : int, optional
        [description], by default 0
    x1 : int, optional
        [description], by default 1
    y1 : int, optional
        [description], by default 1
    gl_color : tuple, optional
        [description], by default (1, 1, 1)
    """
    gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color)

    gl.glBegin(gl.GL_QUADS)
    gl.glVertex3f(x0, y0, z)
    gl.glVertex3f(x1, y0, z)
    gl.glVertex3f(x1, y1, z)
    gl.glVertex3f(x0, y1, z)
    gl.glEnd()


def draw_box3d(
    x_len=1,
    y_len=1,
    z_len=1,
    x=0,
    y=0,
    z=0,
    x_angle=0,
    y_angle=0,
    z_angle=0,
    x_ref=0,
    y_ref=0,
    z_ref=0,
    gl_color=(1, 1, 1),
    show=True,
    edge_gl_color=(1, 1, 1),
    show_edge=False,
    shaded=False,
    _show_lids=True,
):
    """
    draws a 3d box (should be added to the event loop by encapsulating with Animate3dBase)

    Parameters
    ----------
    x_len : int, optional
        [description], by default 1
    y_len : int, optional
        [description], by default 1
    z_len : int, optional
        [description], by default 1
    x : int, optional
        [description], by default 0
    y : int, optional
        [description], by default 0
    z : int, optional
        [description], by default 0
    x_angle : int, optional
        [description], by default 0
    y_angle : int, optional
        [description], by default 0
    z_angle : int, optional
        [description], by default 0
    x_ref : int, optional
        [description], by default 0
    y_ref : int, optional
        [description], by default 0
    z_ref : int, optional
        [description], by default 0
    gl_color : tuple, optional
        [description], by default (1, 1, 1)
    show : bool, optional
        [description], by default True
    edge_gl_color : tuple, optional
        [description], by default (1, 1, 1)
    show_edge : bool, optional
        [description], by default False
    shaded : bool, optional
        [description], by default False
    _show_lids : bool, optional
        [description], by default True
    """
    gl_color0 = gl_color
    if shaded:
        gl_color1 = (gl_color0[0] * 0.9, gl_color0[1] * 0.9, gl_color0[2] * 0.9)
        gl_color2 = (gl_color0[0] * 0.8, gl_color0[1] * 0.8, gl_color0[2] * 0.8)
    else:
        gl_color1 = gl_color2 = gl_color0

    x1 = ((x_ref - 1) / 2) * x_len
    x2 = ((x_ref + 1) / 2) * x_len

    y1 = ((y_ref - 1) / 2) * y_len
    y2 = ((y_ref + 1) / 2) * y_len

    z1 = ((z_ref - 1) / 2) * z_len
    z2 = ((z_ref + 1) / 2) * z_len

    bv = [[x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1], [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2]]

    gl.glPushMatrix()

    gl.glTranslate(x, y, z)
    if z_angle:
        gl.glRotate(z_angle, 0.0, 0.0, 1.0)
    if y_angle:
        gl.glRotate(y_angle, 0.0, 1.0, 0.0)
    if x_angle:
        gl.glRotate(x_angle, 1.0, 0.0, 0.0)

    if show:
        gl.glBegin(gl.GL_QUADS)

        # bottom z-
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color0)
        gl.glNormal(0, 0, -1)
        gl.glVertex3f(*bv[0])
        gl.glVertex3f(*bv[1])
        gl.glVertex3f(*bv[2])
        gl.glVertex3f(*bv[3])

        # top z+
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color0)
        gl.glNormal3f(0, 0, 1)
        gl.glVertex3f(*bv[4])
        gl.glVertex3f(*bv[5])
        gl.glVertex3f(*bv[6])
        gl.glVertex3f(*bv[7])

        # left y-
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color1)
        gl.glNormal3f(0, -1, 0)
        gl.glVertex3f(*bv[0])
        gl.glVertex3f(*bv[1])
        gl.glVertex3f(*bv[5])
        gl.glVertex3f(*bv[4])

        # right y+
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color1)
        gl.glNormal3f(0, 1, 0)
        gl.glVertex3f(*bv[2])
        gl.glVertex3f(*bv[3])
        gl.glVertex3f(*bv[7])
        gl.glVertex3f(*bv[6])

        if _show_lids:
            # front x+
            gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color2)
            gl.glNormal3f(1, 0, 0)
            gl.glVertex3f(*bv[1])
            gl.glVertex3f(*bv[2])
            gl.glVertex3f(*bv[6])
            gl.glVertex3f(*bv[5])

            # front x-
            gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color2)
            gl.glNormal3f(-1, 0, 0)
            gl.glVertex3f(*bv[3])
            gl.glVertex3f(*bv[0])
            gl.glVertex3f(*bv[4])
            gl.glVertex3f(*bv[7])

        gl.glEnd()

    if show_edge:
        gl.glBegin(gl.GL_LINES)
        gl_color = (1, 0, 1)
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, edge_gl_color)

        gl.glVertex3f(*bv[0])
        gl.glVertex3f(*bv[4])

        gl.glVertex3f(*bv[4])
        gl.glVertex3f(*bv[7])

        gl.glVertex3f(*bv[7])
        gl.glVertex3f(*bv[3])

        gl.glVertex3f(*bv[3])
        gl.glVertex3f(*bv[0])

        gl.glVertex3f(*bv[5])
        gl.glVertex3f(*bv[6])

        gl.glVertex3f(*bv[6])
        gl.glVertex3f(*bv[2])

        gl.glVertex3f(*bv[2])
        gl.glVertex3f(*bv[1])

        gl.glVertex3f(*bv[1])
        gl.glVertex3f(*bv[5])

        gl.glVertex3f(*bv[0])
        gl.glVertex3f(*bv[1])

        gl.glVertex3f(*bv[4])
        gl.glVertex3f(*bv[5])

        gl.glVertex3f(*bv[7])
        gl.glVertex3f(*bv[6])

        gl.glVertex3f(*bv[3])
        gl.glVertex3f(*bv[2])

        gl.glEnd()

    gl.glPopMatrix()


def draw_sphere3d(x=0, y=0, z=0, radius=1, number_of_slices=32, number_of_stacks=None, gl_color=(1, 1, 1)):
    """
    draws a 3d spere (should be added to the event loop by encapsulating with Animate3dBase)

    Parameters
    ----------
    radius : float, optional
    """
    quadratic = glu.gluNewQuadric()
    glu.gluQuadricNormals(quadratic, glu.GLU_SMOOTH)
    glu.gluQuadricTexture(quadratic, gl.GL_TRUE)

    gl.glPushMatrix()

    gl.glTranslate(x, y, z)
    gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color)

    glu.gluSphere(quadratic, radius, number_of_slices, number_of_slices if number_of_stacks is None else number_of_stacks)

    gl.glPopMatrix()


def _std_fonts():
    # the names of the standard fonts are generated by ttf fontdict.py on the standard development machine
    if not hasattr(_std_fonts, "cached"):
        _std_fonts.cached = pickle.loads(
            b"(dp0\nVHuxley_Titling\np1\nVHuxley Titling\np2\nsVGlock___\np3\nVGlockenspiel\np4\nsVPENLIIT_\np5\nVPenultimateLightItal\np6\nsVERASMD\np7\nVEras Medium ITC\np8\nsVNirmala\np9\nVNirmala UI\np10\nsVebrimabd\np11\nVEbrima Bold\np12\nsVostrich-dashed\np13\nVOstrich Sans Dashed Medium\np14\nsVLato-Hairline\np15\nVLato Hairline\np16\nsVLTYPEO\np17\nVLucida Sans Typewriter Oblique\np18\nsVbnmachine\np19\nVBN Machine\np20\nsVLTYPEB\np21\nVLucida Sans Typewriter Bold\np22\nsVBOOKOSI\np23\nVBookman Old Style Italic\np24\nsVEmmett__\np25\nVEmmett\np26\nsVCURLZ___\np27\nVCurlz MT\np28\nsVhandmeds\np29\nVHand Me Down S (BRK)\np30\nsVsegoesc\np31\nVSegoe Script\np32\nsVTCM_____\np33\nVTw Cen MT\np34\nsVJosefinSlab-ThinItalic\np35\nVJosefin Slab Thin Italic\np36\nsVSTENCIL\np37\nVStencil\np38\nsVsanss___\np39\nVSansSerif\np40\nsVBOD_CI\np41\nVBodoni MT Condensed Italic\np42\nsVGreek_i\np43\nVGreek Diner Inline TT\np44\nsVHTOWERT\np45\nVHigh Tower Text\np46\nsVTCCB____\np47\nVTw Cen MT Condensed Bold\np48\nsVCools___\np49\nVCoolsville\np50\nsVbnjinx\np51\nVBN Jinx\np52\nsVFREESCPT\np53\nVFreestyle Script\np54\nsVGARA\np55\nVGaramond\np56\nsVDejaVuSansMono\np57\nVDejaVu Sans Mono Book\np58\nsVCALVIN__\np59\nVCalvin\np60\nsVGIL_____\np61\nVGill Sans MT\np62\nsVCandaraz\np63\nVCandara Bold Italic\np64\nsVVollkorn-Bold\np65\nVVollkorn Bold\np66\nsVariblk\np67\nVArial Black\np68\nsVGOTHIC\np69\nVCentury Gothic\np70\nsVMAIAN\np71\nVMaiandra GD\np72\nsVBSSYM7\np73\nVBookshelf Symbol 7\np74\nsVAcme____\np75\nVAcmeFont\np76\nsVDetente_\np77\nVDetente\np78\nsVCandarai\np79\nVCandara Italic\np80\nsVFTLTLT\np81\nVFootlight MT Light\np82\nsVGILC____\np83\nVGill Sans MT Condensed\np84\nsVLFAXD\np85\nVLucida Fax Demibold\np86\nsVNIAGSOL\np87\nVNiagara Solid\np88\nsVLFAXI\np89\nVLucida Fax Italic\np90\nsVCandarab\np91\nVCandara Bold\np92\nsVFRSCRIPT\np93\nVFrench Script MT\np94\nsVLBRITE\np95\nVLucida Bright\np96\nsVFRABK\np97\nVFranklin Gothic Book\np98\nsVostrich-bold\np99\nVOstrich Sans Bold\np100\nsVTCCM____\np101\nVTw Cen MT Condensed\np102\nsVcorbelz\np103\nVCorbel Bold Italic\np104\nsVTCMI____\np105\nVTw Cen MT Italic\np106\nsVethnocen\np107\nVEthnocentric\np108\nsVVINERITC\np109\nVViner Hand ITC\np110\nsVROCKB\np111\nVRockwell Bold\np112\nsVconsola\np113\nVConsolas\np114\nsVcorbeli\np115\nVCorbel Italic\np116\nsVPENUL___\np117\nVPenultimate\np118\nsVMAGNETOB\np119\nVMagneto Bold\np120\nsVisocp___\np121\nVISOCP\np122\nsVQUIVEIT_\np123\nVQuiverItal\np124\nsVARLRDBD\np125\nVArial Rounded MT Bold\np126\nsVJosefinSlab-SemiBold\np127\nVJosefin Slab SemiBold\np128\nsVntailub\np129\nVMicrosoft New Tai Lue Bold\np130\nsVflubber\np131\nVFlubber\np132\nsVBASKVILL\np133\nVBaskerville Old Face\np134\nsVGILB____\np135\nVGill Sans MT Bold\np136\nsVPERTILI\np137\nVPerpetua Titling MT Light\np138\nsVLato-HairlineItalic\np139\nVLato Hairline Italic\np140\nsVComfortaa-Light\np141\nVComfortaa Light\np142\nsVtrebucit\np143\nVTrebuchet MS Italic\np144\nsVmalgunbd\np145\nVMalgun Gothic Bold\np146\nsVITCBLKAD\np147\nVBlackadder ITC\np148\nsVsansso__\np149\nVSansSerif Oblique\np150\nsVCALISTBI\np151\nVCalisto MT Bold Italic\np152\nsVsyastro_\np153\nVSyastro\np154\nsVSamsungIF_Md\np155\nVSamsung InterFace Medium\np156\nsVHombre__\np157\nVHombre\np158\nsVseguiemj\np159\nVSegoe UI Emoji\np160\nsVFRAHVIT\np161\nVFranklin Gothic Heavy Italic\np162\nsVJUICE___\np163\nVJuice ITC\np164\nsVFRAMDCN\np165\nVFranklin Gothic Medium Cond\np166\nsVseguisb\np167\nVSegoe UI Semibold\np168\nsVconsolai\np169\nVConsolas Italic\np170\nsVGLECB\np171\nVGloucester MT Extra Condensed\np172\nsVframd\np173\nVFranklin Gothic Medium\np174\nsVSCHLBKI\np175\nVCentury Schoolbook Italic\np176\nsVCENTAUR\np177\nVCentaur\np178\nsVromantic\np179\nVRomantic\np180\nsVBOD_CB\np181\nVBodoni MT Condensed Bold\np182\nsVverdana\np183\nVVerdana\np184\nsVTangerine_Regular\np185\nVTangerine\np186\nsVseguili\np187\nVSegoe UI Light Italic\np188\nsVNunito-Regular\np189\nVNunito\np190\nsVSCHLBKB\np191\nVCentury Schoolbook Bold\np192\nsVGOTHICB\np193\nVCentury Gothic Bold\np194\nsVpalai\np195\nVPalatino Linotype Italic\np196\nsVBKANT\np197\nVBook Antiqua\np198\nsVLato-Italic\np199\nVLato Italic\np200\nsVPERBI___\np201\nVPerpetua Bold Italic\np202\nsVGOTHICI\np203\nVCentury Gothic Italic\np204\nsVROCKBI\np205\nVRockwell Bold Italic\np206\nsVLTYPEBO\np207\nVLucida Sans Typewriter Bold Oblique\np208\nsVAmeth___\np209\nVAmethyst\np210\nsVyearsupplyoffairycakes\np211\nVYear supply of fairy cakes\np212\nsVGILBI___\np213\nVGill Sans MT Bold Italic\np214\nsVBOOKOS\np215\nVBookman Old Style\np216\nsVVollkorn-Italic\np217\nVVollkorn Italic\np218\nsVswiss\np219\nVSwis721 BT Roman\np220\nsVcomsc\np221\nVCommercialScript BT\np222\nsVchinyen\np223\nVChinyen Normal\np224\nsVeurr____\np225\nVEuroRoman\np226\nsVROCK\np227\nVRockwell\np228\nsVPERTIBD\np229\nVPerpetua Titling MT Bold\np230\nsVCHILLER\np231\nVChiller\np232\nsVtechb___\np233\nVTechnicBold\np234\nsVLato-Light\np235\nVLato Light\np236\nsVOUTLOOK\np237\nVMS Outlook\np238\nsVmtproxy6\np239\nVProxy 6\np240\nsVdutcheb\np241\nVDutch801 XBd BT Extra Bold\np242\nsVgadugib\np243\nVGadugi Bold\np244\nsVBOD_CR\np245\nVBodoni MT Condensed\np246\nsVmtproxy7\np247\nVProxy 7\np248\nsVnobile_bold\np249\nVNobile Bold\np250\nsVELEPHNT\np251\nVElephant\np252\nsVCOPRGTL\np253\nVCopperplate Gothic Light\np254\nsVMTCORSVA\np255\nVMonotype Corsiva\np256\nsVconsolaz\np257\nVConsolas Bold Italic\np258\nsVBOOKOSBI\np259\nVBookman Old Style Bold Italic\np260\nsVtrebuc\np261\nVTrebuchet MS\np262\nsVcomici\np263\nVComic Sans MS Italic\np264\nsVJosefinSlab-BoldItalic\np265\nVJosefin Slab Bold Italic\np266\nsVMycalc__\np267\nVMycalc\np268\nsVmarlett\np269\nVMarlett\np270\nsVsymeteo_\np271\nVSymeteo\np272\nsVcandles_\np273\nVCandles\np274\nsVbobcat\np275\nVBobcat Normal\np276\nsVLSANSDI\np277\nVLucida Sans Demibold Italic\np278\nsVINFROMAN\np279\nVInformal Roman\np280\nsVsf movie poster2\np281\nVSF Movie Poster\np282\nsVcomicz\np283\nVComic Sans MS Bold Italic\np284\nsVcracj___\np285\nVCracked Johnnie\np286\nsVcourbd\np287\nVCourier New Bold\np288\nsVItali___\np289\nVItalianate\np290\nsVITCEDSCR\np291\nVEdwardian Script ITC\np292\nsVcourbi\np293\nVCourier New Bold Italic\np294\nsVcalibrili\np295\nVCalibri Light Italic\np296\nsVgazzarelli\np297\nVGazzarelli\np298\nsVGabriola\np299\nVGabriola\np300\nsVVollkorn-BoldItalic\np301\nVVollkorn Bold Italic\np302\nsVromant__\np303\nVRomanT\np304\nsVisoct3__\np305\nVISOCT3\np306\nsVsegoeuib\np307\nVSegoe UI Bold\np308\nsVtimesbd\np309\nVTimes New Roman Bold\np310\nsVgoodtime\np311\nVGood Times\np312\nsVsegoeuii\np313\nVSegoe UI Italic\np314\nsVBOD_BLAR\np315\nVBodoni MT Black\np316\nsVhimalaya\np317\nVMicrosoft Himalaya\np318\nsVsegoeuil\np319\nVSegoe UI Light\np320\nsVPermanentMarker\np321\nVPermanent Marker\np322\nsVBOD_BLAI\np323\nVBodoni MT Black Italic\np324\nsVTCBI____\np325\nVTw Cen MT Bold Italic\np326\nsVarial\np327\nVArial\np328\nsVBrand___\np329\nVBrandish\np330\nsVsegoeuiz\np331\nVSegoe UI Bold Italic\np332\nsVswisscb\np333\nVSwis721 Cn BT Bold\np334\nsVPAPYRUS\np335\nVPapyrus\np336\nsVANTIC___\np337\nVAnticFont\np338\nsVGIGI\np339\nVGigi\np340\nsVENGR\np341\nVEngravers MT\np342\nsVsegmdl2\np343\nVSegoe MDL2 Assets\np344\nsVBRLNSDB\np345\nVBerlin Sans FB Demi Bold\np346\nsVLato-BoldItalic\np347\nVLato Bold Italic\np348\nsVholomdl2\np349\nVHoloLens MDL2 Assets\np350\nsVBRITANIC\np351\nVBritannic Bold\np352\nsVNirmalaB\np353\nVNirmala UI Bold\np354\nsVVollkorn-Regular\np355\nVVollkorn\np356\nsVStephen_\np357\nVStephen\np358\nsVbabyk___\np359\nVBaby Kruffy\np360\nsVHARVEST_\np361\nVHarvest\np362\nsVKUNSTLER\np363\nVKunstler Script\np364\nsVstylu\np365\nVStylus BT Roman\np366\nsVWINGDNG3\np367\nVWingdings 3\np368\nsVWINGDNG2\np369\nVWingdings 2\np370\nsVlucon\np371\nVLucida Console\np372\nsVCandara\np373\nVCandara\np374\nsVBERNHC\np375\nVBernard MT Condensed\np376\nsVtechnic_\np377\nVTechnic\np378\nsVLimou___\np379\nVLimousine\np380\nsVTCB_____\np381\nVTw Cen MT Bold\np382\nsVPirate__\np383\nVPirate\np384\nsVFrnkvent\np385\nVFrankfurter Venetian TT\np386\nsVromand__\np387\nVRomanD\np388\nsVLTYPE\np389\nVLucida Sans Typewriter\np390\nsVSHOWG\np391\nVShowcard Gothic\np392\nsVMOD20\np393\nVModern No. 20\np394\nsVostrich-rounded\np395\nVOstrich Sans Rounded Medium\np396\nsVJosefinSlab-Italic\np397\nVJosefin Slab Italic\np398\nsVneon2\np399\nVNeon Lights\np400\nsVpalabi\np401\nVPalatino Linotype Bold Italic\np402\nsVwoodcut\np403\nVWoodcut\np404\nsVToledo__\np405\nVToledo\np406\nsVverdanai\np407\nVVerdana Italic\np408\nsVSamsungIF_Rg\np409\nVSamsung InterFace\np410\nsVtrebucbd\np411\nVTrebuchet MS Bold\np412\nsVPALSCRI\np413\nVPalace Script MT\np414\nsVComfortaa-Regular\np415\nVComfortaa\np416\nsVmicross\np417\nVMicrosoft Sans Serif\np418\nsVseguisli\np419\nVSegoe UI Semilight Italic\np420\nsVtaile\np421\nVMicrosoft Tai Le\np422\nsVcour\np423\nVCourier New\np424\nsVparryhotter\np425\nVParry Hotter\np426\nsVgreekc__\np427\nVGreekC\np428\nsVRAGE\np429\nVRage Italic\np430\nsVMATURASC\np431\nVMatura MT Script Capitals\np432\nsVBASTION_\np433\nVBastion\np434\nsVREFSAN\np435\nVMS Reference Sans Serif\np436\nsVterminat\np437\nVTerminator Two\np438\nsVmmrtextb\np439\nVMyanmar Text Bold\np440\nsVgothici_\np441\nVGothicI\np442\nsVmonotxt_\np443\nVMonotxt\np444\nsVcorbelb\np445\nVCorbel Bold\np446\nsVVALKEN__\np447\nVValken\np448\nsVRowdyhe_\np449\nVRowdyHeavy\np450\nsVLato-Black\np451\nVLato Black\np452\nsVswisski\np453\nVSwis721 Blk BT Black Italic\np454\nsVcouri\np455\nVCourier New Italic\np456\nsVMTEXTRA\np457\nVMT Extra\np458\nsVsanssbo_\np459\nVSansSerif BoldOblique\np460\nsVl_10646\np461\nVLucida Sans Unicode\np462\nsVLato-BlackItalic\np463\nVLato Black Italic\np464\nsVseguibli\np465\nVSegoe UI Black Italic\np466\nsVGeotype\np467\nVGeotype TT\np468\nsVxfiles\np469\nVX-Files\np470\nsVjavatext\np471\nVJavanese Text\np472\nsVseguisym\np473\nVSegoe UI Symbol\np474\nsVverdanaz\np475\nVVerdana Bold Italic\np476\nsVGILI____\np477\nVGill Sans MT Italic\np478\nsVALGER\np479\nVAlgerian\np480\nsVAGENCYR\np481\nVAgency FB\np482\nsVnobile\np483\nVNobile\np484\nsVHaxton\np485\nVHaxton Logos TT\np486\nsVswissbo\np487\nVSwis721 BdOul BT Bold\np488\nsVBELLI\np489\nVBell MT Italic\np490\nsVBROADW\np491\nVBroadway\np492\nsVsegoepr\np493\nVSegoe Print\np494\nsVGILLUBCD\np495\nVGill Sans Ultra Bold Condensed\np496\nsVverdanab\np497\nVVerdana Bold\np498\nsVSalina__\np499\nVSalina\np500\nsVAGENCYB\np501\nVAgency FB Bold\np502\nsVAutumn__\np503\nVAutumn\np504\nsVGOUDOS\np505\nVGoudy Old Style\np506\nsVconstanz\np507\nVConstantia Bold Italic\np508\nsVPOORICH\np509\nVPoor Richard\np510\nsVPRISTINA\np511\nVPristina\np512\nsVLATINWD\np513\nVWide Latin\np514\nsVromanc__\np515\nVRomanC\np516\nsVLeelawUI\np517\nVLeelawadee UI\np518\nsVitalict_\np519\nVItalicT\np520\nsVostrich-regular\np521\nVOstrich Sans Medium\np522\nsVmonosbi\np523\nVMonospac821 BT Bold Italic\np524\nsVcambriai\np525\nVCambria Italic\np526\nsVisocp2__\np527\nVISOCP2\np528\nsVltromatic\np529\nVLetterOMatic!\np530\nsVbgothm\np531\nVBankGothic Md BT Medium\np532\nsVbgothl\np533\nVBankGothic Lt BT Light\np534\nsVSwkeys1\np535\nVSWGamekeys MT\np536\nsVCENSCBK\np537\nVCentury Schoolbook\np538\nsVgothicg_\np539\nVGothicG\np540\nsValmosnow\np541\nVAlmonte Snow\np542\nsVTangerine_Bold\np543\nVTangerine Bold\np544\nsVswisseb\np545\nVSwis721 Ex BT Bold\np546\nsVCOLONNA\np547\nVColonna MT\np548\nsVsupef___\np549\nVSuperFrench\np550\nsVTCCEB\np551\nVTw Cen MT Condensed Extra Bold\np552\nsVsylfaen\np553\nVSylfaen\np554\nsVcomicbd\np555\nVComic Sans MS Bold\np556\nsVRoland__\np557\nVRoland\np558\nsVELEPHNTI\np559\nVElephant Italic\np560\nsVmmrtext\np561\nVMyanmar Text\np562\nsVsymap___\np563\nVSymap\np564\nsVswissko\np565\nVSwis721 BlkOul BT Black\np566\nsVswissck\np567\nVSwis721 BlkCn BT Black\np568\nsVWhimsy\np569\nVWhimsy TT\np570\nsVsanssb__\np571\nVSansSerif Bold\np572\nsVtaileb\np573\nVMicrosoft Tai Le Bold\np574\nsVcomic\np575\nVComic Sans MS\np576\nsVGLSNECB\np577\nVGill Sans MT Ext Condensed Bold\np578\nsVColbert_\np579\nVColbert\np580\nsVJOKERMAN\np581\nVJokerman\np582\nsVARIALNB\np583\nVArial Narrow Bold\np584\nsVDOMIN___\np585\nVDominican\np586\nsVBRUSHSCI\np587\nVBrush Script MT Italic\np588\nsVCALLI___\np589\nVCalligraphic\np590\nsVFRADM\np591\nVFranklin Gothic Demi\np592\nsVJosefinSlab-LightItalic\np593\nVJosefin Slab Light Italic\np594\nsVsimplex_\np595\nVSimplex\np596\nsVphagspab\np597\nVMicrosoft PhagsPa Bold\np598\nsVswissek\np599\nVSwis721 BlkEx BT Black\np600\nsVscripts_\np601\nVScriptS\np602\nsVswisscl\np603\nVSwis721 LtCn BT Light\np604\nsVCASTELAR\np605\nVCastellar\np606\nsVdutchi\np607\nVDutch801 Rm BT Italic\np608\nsVnasaliza\np609\nVNasalization Medium\np610\nsVariali\np611\nVArial Italic\np612\nsVOpinehe_\np613\nVOpineHeavy\np614\nsVPLAYBILL\np615\nVPlaybill\np616\nsVROCCB___\np617\nVRockwell Condensed Bold\np618\nsVCALIST\np619\nVCalisto MT\np620\nsVCALISTB\np621\nVCalisto MT Bold\np622\nsVHATTEN\np623\nVHaettenschweiler\np624\nsVntailu\np625\nVMicrosoft New Tai Lue\np626\nsVCALISTI\np627\nVCalisto MT Italic\np628\nsVsegoeprb\np629\nVSegoe Print Bold\np630\nsVDAYTON__\np631\nVDayton\np632\nsVswissel\np633\nVSwis721 LtEx BT Light\np634\nsVmael____\np635\nVMael\np636\nsVisoct2__\np637\nVISOCT2\np638\nsVBorea___\np639\nVBorealis\np640\nsVwingding\np641\nVWingdings\np642\nsVONYX\np643\nVOnyx\np644\nsVmonosi\np645\nVMonospac821 BT Italic\np646\nsVtimesi\np647\nVTimes New Roman Italic\np648\nsVostrich-light\np649\nVOstrich Sans Condensed Light\np650\nsVseguihis\np651\nVSegoe UI Historic\np652\nsVNovem___\np653\nVNovember\np654\nsVOCRAEXT\np655\nVOCR A Extended\np656\nsVostrich-black\np657\nVOstrich Sans Black\np658\nsVnarrow\np659\nVPR Celtic Narrow Normal\np660\nsVitalic__\np661\nVItalic\np662\nsVmonosb\np663\nVMonospac821 BT Bold\np664\nsVPERB____\np665\nVPerpetua Bold\np666\nsVCreteRound-Regular\np667\nVCrete Round\np668\nsVcalibri\np669\nVCalibri\np670\nsVSCRIPTBL\np671\nVScript MT Bold\np672\nsVComfortaa-Bold\np673\nVComfortaa Bold\np674\nsVARIALN\np675\nVArial Narrow\np676\nsVHARNGTON\np677\nVHarrington\np678\nsVJosefinSlab-Bold\np679\nVJosefin Slab Bold\np680\nsVVIVALDII\np681\nVVivaldi Italic\np682\nsVhollh___\np683\nVHollywood Hills\np684\nsVBOD_R\np685\nVBodoni MT\np686\nsVSkinny__\np687\nVSkinny\np688\nsVLBRITED\np689\nVLucida Bright Demibold\np690\nsVframdit\np691\nVFranklin Gothic Medium Italic\np692\nsVsymusic_\np693\nVSymusic\np694\nsVgadugi\np695\nVGadugi\np696\nsVswissbi\np697\nVSwis721 BT Bold Italic\np698\nsVBOD_B\np699\nVBodoni MT Bold\np700\nsVERASDEMI\np701\nVEras Demi ITC\np702\nsVWaverly_\np703\nVWaverly\np704\nsVcompi\np705\nVCommercialPi BT\np706\nsVBOD_I\np707\nVBodoni MT Italic\np708\nsVconstan\np709\nVConstantia\np710\nsVARIALNBI\np711\nVArial Narrow Bold Italic\np712\nsVarialbi\np713\nVArial Bold Italic\np714\nsVJosefinSlab-Light\np715\nVJosefin Slab Light\np716\nsVBOD_CBI\np717\nVBodoni MT Condensed Bold Italic\np718\nsVwebdings\np719\nVWebdings\np720\nsVRAVIE\np721\nVRavie\np722\nsVROCC____\np723\nVRockwell Condensed\np724\nsVFELIXTI\np725\nVFelix Titling\np726\nsVRussrite\np727\nVRussel Write TT\np728\nsVisocteur\np729\nVISOCTEUR\np730\nsVLSANSD\np731\nVLucida Sans Demibold Roman\np732\nsVmalgun\np733\nVMalgun Gothic\np734\nsVheavyhea2\np735\nVHeavy Heap\np736\nsVGOUDYSTO\np737\nVGoudy Stout\np738\nsVVLADIMIR\np739\nVVladimir Script\np740\nsVARIALUNI\np741\nVArial Unicode MS\np742\nsVJosefinSlab-Thin\np743\nVJosefin Slab Thin\np744\nsVFRADMCN\np745\nVFranklin Gothic Demi Cond\np746\nsVBlackout-2am\np747\nVBlackout 2 AM\np748\nsVpalab\np749\nVPalatino Linotype Bold\np750\nsVDejaVuSansMono-Oblique\np751\nVDejaVu Sans Mono Oblique\np752\nsVANTQUABI\np753\nVBook Antiqua Bold Italic\np754\nsVswissc\np755\nVSwis721 Cn BT Roman\np756\nsVSPLASH__\np757\nVSplash\np758\nsVNIAGENG\np759\nVNiagara Engraved\np760\nsVCOPRGTB\np761\nVCopperplate Gothic Bold\np762\nsVBruss___\np763\nVBrussels\np764\nsVconsolab\np765\nVConsolas Bold\np766\nsVGOTHICBI\np767\nVCentury Gothic Bold Italic\np768\nsVmtproxy4\np769\nVProxy 4\np770\nsVmtproxy5\np771\nVProxy 5\np772\nsVromai___\np773\nVRomantic Italic\np774\nsVFRABKIT\np775\nVFranklin Gothic Book Italic\np776\nsVBELL\np777\nVBell MT\np778\nsVmtproxy1\np779\nVProxy 1\np780\nsVmtproxy2\np781\nVProxy 2\np782\nsVmtproxy3\np783\nVProxy 3\np784\nsVLCALLIG\np785\nVLucida Calligraphy Italic\np786\nsVphagspa\np787\nVMicrosoft PhagsPa\np788\nsVANTQUAI\np789\nVBook Antiqua Italic\np790\nsVmtproxy8\np791\nVProxy 8\np792\nsVmtproxy9\np793\nVProxy 9\np794\nsVLato-Bold\np795\nVLato Bold\np796\nsVtxt_____\np797\nVTxt\np798\nsVconstanb\np799\nVConstantia Bold\np800\nsVERASBD\np801\nVEras Bold ITC\np802\nsVLato-LightItalic\np803\nVLato Light Italic\np804\nsVRONDALO_\np805\nVRondalo\np806\nsVconstani\np807\nVConstantia Italic\np808\nsVBRLNSB\np809\nVBerlin Sans FB Bold\np810\nsVgeorgiaz\np811\nVGeorgia Bold Italic\np812\nsVgothice_\np813\nVGothicE\np814\nsVcalibriz\np815\nVCalibri Bold Italic\np816\nsVgeorgiab\np817\nVGeorgia Bold\np818\nsVLeelaUIb\np819\nVLeelawadee UI Bold\np820\nsVtimesbi\np821\nVTimes New Roman Bold Italic\np822\nsVPERI____\np823\nVPerpetua Italic\np824\nsVromab___\np825\nVRomantic Bold\np826\nsVBRLNSR\np827\nVBerlin Sans FB\np828\nsVBELLB\np829\nVBell MT Bold\np830\nsVgeorgiai\np831\nVGeorgia Italic\np832\nsVNirmalaS\np833\nVNirmala UI Semilight\np834\nsVdutchb\np835\nVDutch801 Rm BT Bold\np836\nsVdigifit\np837\nVDigifit Normal\np838\nsVROCKEB\np839\nVRockwell Extra Bold\np840\nsVgdt_____\np841\nVGDT\np842\nsVmonbaiti\np843\nVMongolian Baiti\np844\nsVsegoescb\np845\nVSegoe Script Bold\np846\nsVsymath__\np847\nVSymath\np848\nsVisoct___\np849\nVISOCT\np850\nsVTarzan__\np851\nVTarzan\np852\nsVsnowdrft\np853\nVSnowdrift\np854\nsVHTOWERTI\np855\nVHigh Tower Text Italic\np856\nsVCENTURY\np857\nVCentury\np858\nsVmalgunsl\np859\nVMalgun Gothic Semilight\np860\nsVseguibl\np861\nVSegoe UI Black\np862\nsVCreteRound-Italic\np863\nVCrete Round Italic\np864\nsVAlfredo_\np865\nVAlfredo\np866\nsVCOMMONS_\np867\nVCommons\np868\nsVLFAX\np869\nVLucida Fax\np870\nsVLBRITEI\np871\nVLucida Bright Italic\np872\nsVFRAHV\np873\nVFranklin Gothic Heavy\np874\nsVisocteui\np875\nVISOCTEUR Italic\np876\nsVManorly_\np877\nVManorly\np878\nsVBolstbo_\np879\nVBolsterBold Bold\np880\nsVsegoeui\np881\nVSegoe UI\np882\nsVNunito-Light\np883\nVNunito Light\np884\nsVIMPRISHA\np885\nVImprint MT Shadow\np886\nsVgeorgia\np887\nVGeorgia\np888\nsV18cents\np889\nV18thCentury\np890\nsVMOONB___\np891\nVMoonbeam\np892\nsVPER_____\np893\nVPerpetua\np894\nsVHansen__\np895\nVHansen\np896\nsVLato-Regular\np897\nVLato\np898\nsVBOUTON_International_symbols\np899\nVBOUTON International Symbols\np900\nsVCOOPBL\np901\nVCooper Black\np902\nsVmonos\np903\nVMonospac821 BT Roman\np904\nsVtahoma\np905\nVTahoma\np906\nsVcityb___\np907\nVCityBlueprint\np908\nsVswisscbi\np909\nVSwis721 Cn BT Bold Italic\np910\nsVEnliven_\np911\nVEnliven\np912\nsVLeelUIsl\np913\nVLeelawadee UI Semilight\np914\nsVCALIFR\np915\nVCalifornian FB\np916\nsVumath\np917\nVUniversalMath1 BT\np918\nsVswisscbo\np919\nVSwis721 BdCnOul BT Bold Outline\np920\nsVcomplex_\np921\nVComplex\np922\nsVBOOKOSB\np923\nVBookman Old Style Bold\np924\nsVMartina_\np925\nVMartina\np926\nsVromans__\np927\nVRomanS\np928\nsVmvboli\np929\nVMV Boli\np930\nsVCALIFI\np931\nVCalifornian FB Italic\np932\nsVGARABD\np933\nVGaramond Bold\np934\nsVebrima\np935\nVEbrima\np936\nsVTEMPSITC\np937\nVTempus Sans ITC\np938\nsVCALIFB\np939\nVCalifornian FB Bold\np940\nsVitalicc_\np941\nVItalicC\np942\nsVisocp3__\np943\nVISOCP3\np944\nsVscriptc_\np945\nVScriptC\np946\nsValiee13\np947\nVAlien Encounters\np948\nsVnobile_italic\np949\nVNobile Italic\np950\nsVGARAIT\np951\nVGaramond Italic\np952\nsVswissli\np953\nVSwis721 Lt BT Light Italic\np954\nsVCabinSketch-Bold\np955\nVCabinSketch Bold\np956\nsVcorbel\np957\nVCorbel\np958\nsVseguisbi\np959\nVSegoe UI Semibold Italic\np960\nsVSCHLBKBI\np961\nVCentury Schoolbook Bold Italic\np962\nsVasimov\np963\nVAsimov\np964\nsVLFAXDI\np965\nVLucida Fax Demibold Italic\np966\nsVBRADHITC\np967\nVBradley Hand ITC\np968\nsVswisscki\np969\nVSwis721 BlkCn BT Black Italic\np970\nsVGILSANUB\np971\nVGill Sans Ultra Bold\np972\nsVHARLOWSI\np973\nVHarlow Solid Italic Italic\np974\nsVHARVEIT_\np975\nVHarvestItal\np976\nsVcambriab\np977\nVCambria Bold\np978\nsVswissci\np979\nVSwis721 Cn BT Italic\np980\nsVcounb___\np981\nVCountryBlueprint\np982\nsVNotram__\np983\nVNotram\np984\nsVPENULLI_\np985\nVPenultimateLight\np986\nsVtahomabd\np987\nVTahoma Bold\np988\nsVMISTRAL\np989\nVMistral\np990\nsVpala\np991\nVPalatino Linotype\np992\nsVOLDENGL\np993\nVOld English Text MT\np994\nsVinductio\np995\nVInduction Normal\np996\nsVJosefinSlab-SemiBoldItalic\np997\nVJosefin Slab SemiBold Italic\np998\nsVMinerva_\np999\nVMinerva\np1000\nsVsymbol\np1001\nVSymbol\np1002\nsVcambriaz\np1003\nVCambria Bold Italic\np1004\nsVtrebucbi\np1005\nVTrebuchet MS Bold Italic\np1006\nsVtimes\np1007\nVTimes New Roman\np1008\nsVERASLGHT\np1009\nVEras Light ITC\np1010\nsVSteppes\np1011\nVSteppes TT\np1012\nsVREFSPCL\np1013\nVMS Reference Specialty\np1014\nsVPARCHM\np1015\nVParchment\np1016\nsVDejaVuSansMono-Bold\np1017\nVDejaVu Sans Mono Bold\np1018\nsVswisscli\np1019\nVSwis721 LtCn BT Light Italic\np1020\nsVLSANS\np1021\nVLucida Sans\np1022\nsVPhrasme_\np1023\nVPhrasticMedium\np1024\nsVDejaVuSansMono-BoldOblique\np1025\nVDejaVu Sans Mono Bold Oblique\np1026\nsVarialbd\np1027\nVArial Bold\np1028\nsVSNAP____\np1029\nVSnap ITC\np1030\nsVArchitectsDaughter\np1031\nVArchitects Daughter\np1032\nsVCorpo___\np1033\nVCorporate\np1034\nsVeurro___\np1035\nVEuroRoman Oblique\np1036\nsVimpact\np1037\nVImpact\np1038\nsVlittlelo\np1039\nVLittleLordFontleroy\np1040\nsVsimsunb\np1041\nVSimSun-ExtB\np1042\nsVARIALNI\np1043\nVArial Narrow Italic\np1044\nsVdutchbi\np1045\nVDutch801 Rm BT Bold Italic\np1046\nsVcalibrii\np1047\nVCalibri Italic\np1048\nsVDeneane_\np1049\nVDeneane\np1050\nsVFRADMIT\np1051\nVFranklin Gothic Demi Italic\np1052\nsVANTQUAB\np1053\nVBook Antiqua Bold\np1054\nsVcalibril\np1055\nVCalibri Light\np1056\nsVisocpeui\np1057\nVISOCPEUR Italic\np1058\nsVpanroman\np1059\nVPanRoman\np1060\nsVMelodbo_\np1061\nVMelodBold Bold\np1062\nsVcalibrib\np1063\nVCalibri Bold\np1064\nsVdistant galaxy 2\np1065\nVDistant Galaxy\np1066\nsVPacifico\np1067\nVPacifico\np1068\nsVnobile_bold_italic\np1069\nVNobile Bold Italic\np1070\nsVmsyi\np1071\nVMicrosoft Yi Baiti\np1072\nsVBOD_PSTC\np1073\nVBodoni MT Poster Compressed\np1074\nsVLSANSI\np1075\nVLucida Sans Italic\np1076\nsVcreerg__\np1077\nVCreepygirl\np1078\nsVsegoeuisl\np1079\nVSegoe UI Semilight\np1080\nsVvinet\np1081\nVVineta BT\np1082\nsVisocpeur\np1083\nVISOCPEUR\np1084\nsVtechl___\np1085\nVTechnicLite\np1086\nsVswissb\np1087\nVSwis721 BT Bold\np1088\nsVCLARE___\np1089\nVClarendon\np1090\nsVdutch\np1091\nVDutch801 Rm BT Roman\np1092\nsVLBRITEDI\np1093\nVLucida Bright Demibold Italic\np1094\nsVswisse\np1095\nVSwis721 Ex BT Roman\np1096\nsVswissk\np1097\nVSwis721 Blk BT Black\np1098\nsVswissi\np1099\nVSwis721 BT Italic\np1100\nsVfingerpop2\np1101\nVFingerpop\np1102\nsVswissl\np1103\nVSwis721 Lt BT Light\np1104\nsVBAUHS93\np1105\nVBauhaus 93\np1106\nsVVivian__\np1107\nVVivian\np1108\nsVgreeks__\np1109\nVGreekS\np1110\nsVGOUDOSI\np1111\nVGoudy Old Style Italic\np1112\nsVBOD_BI\np1113\nVBodoni MT Bold Italic\np1114\nsVLHANDW\np1115\nVLucida Handwriting Italic\np1116\nsVITCKRIST\np1117\nVKristen ITC\np1118\nsVBALTH___\np1119\nVBalthazar\np1120\nsVFORTE\np1121\nVForte\np1122\nsVJosefinSlab-Regular\np1123\nVJosefin Slab\np1124\nsVROCKI\np1125\nVRockwell Italic\np1126\nsVGOUDOSB\np1127\nVGoudy Old Style Bold\np1128\nsVLEELAWAD\np1129\nVLeelawadee\np1130\nsVLEELAWDB\np1131\nVLeelawadee Bold\np1132\nsVmarlett_0\np1133\nVMarlett\np1134\nsVmplus-1m-bold\np1135\nVM+ 1m bold\np1136\nsVmplus-1m-light\np1137\nVM+ 1m light\np1138\nsVmplus-1m-medium\np1139\nVM+ 1m medium\np1140\nsVmplus-1m-regular\np1141\nVM+ 1m\np1142\nsVmplus-1m-thin\np1143\nVM+ 1m thin\np1144\nsVMSUIGHUB\np1145\nVMicrosoft Uighur Bold\np1146\nsVMSUIGHUR\np1147\nVMicrosoft Uighur\np1148\nsVSamsungIF_Md_0\np1149\nVSamsung InterFace Medium\np1150\nsVSamsungIF_Rg_0\np1151\nVSamsung InterFace\np1152\nsVbahnschrift\np1153\nVBahnschrift\np1154\nsVBowlbyOneSC-Regular\np1155\nVBowlby One SC\np1156\nsVCabinSketch-Regular\np1157\nVCabin Sketch\np1158\nsVCookie-Regular\np1159\nVCookie\np1160\nsVCourgette-Regular\np1161\nVCourgette\np1162\nsVdead\np1163\nVDead Kansas\np1164\nsVDoppioOne-Regular\np1165\nVDoppio One\np1166\nsVeuphorig\np1167\nVEuphorigenic\np1168\nsVGreatVibes-Regular\np1169\nVGreat Vibes\np1170\nsVKalam-Bold\np1171\nVKalam Bold\np1172\nsVKalam-Light\np1173\nVKalam Light\np1174\nsVKalam-Regular\np1175\nVKalam\np1176\nsVLemon-Regular\np1177\nVLemon\np1178\nsVLimelight-Regular\np1179\nVLimelight\np1180\nsVMegrim\np1181\nVMegrim Medium\np1182\nsVMontserratSubrayada-Bold\np1183\nVMontserrat Subrayada Bold\np1184\nsVNotoSans-Regular\np1185\nVNoto Sans\np1186\nsVRussoOne-Regular\np1187\nVRusso One\np1188\nsVSigmarOne-Regular\np1189\nVSigmar One\np1190\nsVYellowtail-Regular\np1191\nVYellowtail\np1192\ns."  # NOQA
        )
    return _std_fonts.cached


def fonts():
    if not hasattr(fonts, "font_list"):
        fonts.font_list = []
        if Pythonista:
            UIFont = objc_util.ObjCClass("UIFont")
            for family in UIFont.familyNames():
                family = str(family)
                try:
                    ImageFont.truetype(family)
                    fonts.font_list.append(((family,), family))
                except Exception:
                    pass

                for name in UIFont.fontNamesForFamilyName_(family):
                    name = str(name)
                    fonts.font_list.append(((name,), name))

        salabim_dir = Path(__file__).parent
        cur_dir = Path.cwd()
        dir_recursives = [(salabim_dir, False)]
        if cur_dir != salabim_dir:
            dir_recursives.append((cur_dir, False))
        if Windows:
            dir_recursives.append((Path("c:/windows/fonts"), True))
        else:
            dir_recursives.append((Path("/usr/share/fonts"), True))  # for linux
            dir_recursives.append((Path("/system/fonts"), True))  # for android

        for dir, recursive in dir_recursives:
            for file_path in dir.glob("**/*.*" if recursive else "*.*"):
                if file_path.suffix.lower() == ".ttf":
                    file = str(file_path)
                    fn = os.path.basename(file).split(".")[0]
                    if fn in _std_fonts():
                        fullname = _std_fonts()[fn]
                    else:
                        try:
                            f = ImageFont.truetype(file, 12)
                        except OSError:  # to avoid PyDroid problems
                            continue
                        if f is None:
                            fullname = ""
                        else:
                            if str(f.font.style).lower() == "regular":
                                fullname = str(f.font.family)
                            else:
                                fullname = str(f.font.family) + " " + str(f.font.style)
                    if fullname != "":
                        if fn.lower() == fullname.lower():
                            fonts.font_list.append(((fullname,), file))
                        else:
                            fonts.font_list.append(((fn, fullname), file))
    return fonts.font_list


def standardfonts():
    return {"": "Calibri", "std": "Calibri", "mono": "DejaVuSansMono", "narrow": "mplus-1m-regular"}


def getfont(fontname, fontsize):  # fontsize in screen_coordinates!
    if hasattr(getfont, "lookup"):
        if (fontname, fontsize) in getfont.lookup:
            return getfont.lookup[(fontname, fontsize)]
    else:
        getfont.lookup = {}

    if isinstance(fontname, str):
        fontlist1 = [fontname]
    else:
        fontlist1 = list(fontname)

    fontlist1.extend(["calibri", "arial"])

    fontlist = [standardfonts().get(f.lower(), f) for f in fontlist1]

    result = None

    for ifont in fontlist:
        try:
            result = ImageFont.truetype(font=ifont, size=int(fontsize))
            break
        except Exception:
            pass

        filename = ""
        for fns, ifilename in fonts():
            for fn in fns:
                if normalize(fn) == normalize(ifont):
                    filename = ifilename
                    break
            if filename != "":
                break
        if filename != "":
            try:
                if Pythonista:
                    result = ImageFont.truetype(filename, size=int(fontsize))
                else:

                    #  refer to https://github.com/python-pillow/Pillow/issues/3730 for explanation (in order to load >= 500 fonts)
                    result = ImageFont.truetype(font=io.BytesIO(open(filename, "rb").read()), size=int(fontsize))
                break
            except Exception:
                raise

    if result is None:
        result = ImageFont.load_default()  # last resort

    heightA = result.getsize("A")[1]
    getfont.lookup[(fontname, fontsize)] = result, heightA
    return result, heightA


def show_fonts():
    """
    show (print) all available fonts on this machine
    """
    can_animate(try_only=False)
    fontnames = []
    for fns, ifilename in fonts():
        for fn in fns:
            fontnames.append(fn)
    fontnames.extend(list(standardfonts()))
    last = ""
    for font in sorted(fontnames, key=normalize):
        if font != last:  # remove duplicates
            print(font)
            last = font


def show_colornames():
    """
    show (print) all available color names and their value.
    """
    names = sorted(colornames())
    for name in names:
        print(f"{name:22s}{colornames()[name]}")


def arrow_polygon(size):
    """
    creates a polygon tuple with a centered arrow for use with sim.Animate

    Parameters
    ----------
    size : float
        length of the arrow
    """
    size /= 4
    return (-2 * size, -size, 0, -size, 0, -2 * size, 2 * size, 0, 0, 2 * size, 0, size, -2 * size, size)


def centered_rectangle(width, height):
    """
    creates a rectangle tuple with a centered rectangle for use with sim.Animate

    Parameters
    ----------
    width : float
        width of the rectangle

    height : float
        height of the rectangle
    """
    return -width / 2, -height / 2, width / 2, height / 2


def regular_polygon(radius=1, number_of_sides=3, initial_angle=0):
    """
    creates a polygon tuple with a regular polygon (within a circle) for use with sim.Animate

    Parameters
    ----------
    radius : float
        radius of the corner points of the polygon |n|
        default : 1

    number_of_sides : int
        number of sides (corners) |n|
        must be >= 3 |n|
        default : 3

    initial_angle : float
        angle of the first corner point, relative to the origin |n|
        default : 0
    """
    number_of_sides = int(number_of_sides)
    if number_of_sides < 3:
        raise ValueError("number of sides < 3")
    tangle = 2 * math.pi / number_of_sides
    sint = math.sin(tangle)
    cost = math.cos(tangle)
    p = []
    x = radius * math.cos(math.radians(initial_angle))
    y = radius * math.sin(math.radians(initial_angle))

    for i in range(number_of_sides):
        x, y = (x * cost - y * sint, x * sint + y * cost)
        p.append(x + radius)
        p.append(y + radius)

    return p


def can_animate(try_only=True):
    """
    Tests whether animation is supported.

    Parameters
    ----------
    try_only : bool
        if True (default), the function does not raise an error when the required modules cannot be imported |n|
        if False, the function will only return if the required modules could be imported.

    Returns
    -------
    True, if required modules could be imported, False otherwise : bool
    """
    global Image
    global ImageDraw
    global ImageFont
    global GifImagePlugin
    global ImageGrab
    global ImageTk
    global tkinter
    try:
        import PIL  # NOQA
        from PIL import Image
        from PIL import ImageDraw
        from PIL import ImageFont
        from PIL import GifImagePlugin

        try:
            from PIL import ImageGrab
        except ImportError:
            ImageGrab = None

        if not Pythonista:
            from PIL import ImageTk
    except ImportError:
        if try_only:
            return False
        raise ImportError("PIL is required for animation. Install with pip install Pillow or see salabim manual")

    if not Pythonista:
        if PyDroid:
            if not g.tkinter_loaded:
                if try_only:
                    return False
                raise ImportError("PyDroid animation requires that the main program imports tkinter")
        try:
            import tkinter
            import tkinter.font

        except ImportError:
            try:
                import Tkinter as tkinter

            except ImportError:
                if try_only:
                    return False
                raise ImportError("tkinter is required for animation")

    return True


def can_animate3d(try_only=True):
    """
    Tests whether 3d animation is supported.

    Parameters
    ----------
    try_only : bool
        if True (default), the function does not raise an error when the required modules cannot be imported |n|
        if False, the function will only return if the required modules could be imported.

    Returns
    -------
    True, if required modules were imported, False otherwise : bool
    """
    global gl
    global glu
    global glut
    if can_animate(try_only=True):
        try:
            import OpenGL.GL as gl
            import OpenGL.GLU as glu
            import OpenGL.GLUT as glut
        except ImportError:
            if try_only:
                return False
            else:
                raise ImportError("OpenGL is required for animation3d. Install with pip install PyOpenGL or see salabim manual")
        return True
    else:
        if try_only:
            return False
        else:
            raise ImportError("cannot even animate, let alone animate3d")


def can_video(try_only=True):
    """
    Tests whether video is supported.

    Parameters
    ----------
    try_only : bool
        if True (default), the function does not raise an error when the required modules cannot be imported |n|
        if False, the function will only return if the required modules could be imported.

    Returns
    -------
    True, if required modules could be imported, False otherwise : bool
    """
    global cv2
    global numpy
    if Pythonista:
        if try_only:
            return False
        raise NotImplementedError("video production not supported on Pythonista")
    else:
        try:
            import cv2
            import numpy
        except ImportError:
            if try_only:
                return False
            if platform.python_implementation == "PyPy":
                raise NotImplementedError("video production is not supported under PyPy.")
            else:
                raise ImportError("cv2 required for video production. Install with pip install opencv-python")
    return True


def has_numpy():
    """
    Tests whether numpy is installed. If so, the global numpy is set accordingly.
    If not, the global numpy is set to False.

    Returns
    -------
    True, if numpy is installed. False otherwise.
    """
    global numpy
    try:
        return bool(numpy)
    except NameError:
        try:
            import numpy

            return True
        except ModuleNotFoundError:
            numpy = False  # we now know numpy doesn't exist
            return False


def default_env():
    """
    Returns
    -------
    default environment : Environment
    """
    return g.default_env


@contextlib.contextmanager
def over3d(val=True):
    """
    context manager to change temporarily default_over3d

    Parameters
    ----------
    val : bool
        temporary value of default_over3d |n|
        default: True

    Notes
    -----
    Use as ::

        with over3d():
            an = AnimateText('test')
    """
    save_default_over3d = default_over3d()
    default_over3d(val)
    yield
    default_over3d(save_default_over3d)


_default_over3d = False


def default_over3d(val=None):
    """
    Set default_over3d

    Parameters
    ----------
    val : bool
        if not None, set the default_over3d to val

    Returns
    -------
    Current (new) value of default_over3d
    """
    global _default_over3d
    if val is not None:
        _default_over3d = val
    return _default_over3d


@contextlib.contextmanager
def cap_now(val=True):
    """
    context manager to change temporarily default_cap_now

    Parameters
    ----------
    val : bool
        temporary value of default_cap_now |n|
        default: True

    Notes
    -----
    Use as ::

        with cap_now():
            an = AnimateText('test')
    """
    save_default_cap_now = default_cap_now()
    default_cap_now(val)
    yield
    default_cap_now(save_default_cap_now)


_default_cap_now = False


def default_cap_now(val=None):
    """
    Set default_cap_now

    Parameters
    ----------
    val : bool
        if not None, set the default_cap_now to val

    Returns
    -------
    Current (new) value of default_cap_now
    """
    global _default_cap_now
    if val is not None:
        _default_cap_now = val
    return _default_cap_now


def reset():
    """
    resets global variables

    used internally at import of salabim

    might be useful for REPLs or for Pythonista
    """
    try:
        g.default_env.video_close()
    except Exception:
        pass

    try:
        g.animation_env.root.destroy()
    except Exception:
        pass
    g.default_env = None
    g.animation_env = None
    g.animation_scene = None
    g.in_draw = False
    g.tkinter_loaded = "?"
    random_seed()  # always start with seed 1234567


reset()

if __name__ == "__main__":
    try:
        import salabim_exp
    except Exception as e:
        print("salabim_exp.py not found or ?")
        raise e

    try:
        salabim_exp.__dict__["exp"]
    except KeyError:
        print("salabim_exp.exp() not found")
        quit()

    salabim_exp.exp()
