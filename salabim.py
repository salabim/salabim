'''
salabim  discrete event simulation

The MIT License (MIT)

Copyright (c) 2017 Ruud van der Ham, ruud@salabim.org

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to who the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

see www.salabim.org for more information, the manual and updates.
'''
from __future__ import print_function  # compatibility with Python 2.x
from __future__ import division  # compatibility with Python 2.x

__version__ = '2.2.7'

import heapq
import random
import time
import math
import array
import collections
import glob
import os
import inspect
import platform
import sys

Pythonista = (sys.platform == 'ios')
Windows = (sys.platform.startswith('win'))

try:
    import numpy as np
except ImportError:
    pass

try:
    import cv2
except ImportError:
    pass

try:
    import PIL  # NOQA
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
    if not Pythonista:
        from PIL import ImageTk
except ImportError:
    pass

try:
    import tkinter
except ImportError:
    pass

try:
    import Tkinter as tkinter  # NOQA
except ImportError:
    pass

if Pythonista:
    import scene
    import ui
    import objc_util

inf = float('inf')
nan = float('nan')
omitted = ['omitted']


class SalabimError(Exception):
    pass


class Monitor(object):
    '''
    Monitor object

    Parameters
    ----------
    name : str
        name of the monitor |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name monitor. (serialized)

    monitor : bool
        if True (default), monitoring will be on. |n|
        if False, monitoring is disabled |n|
        it is possible to control monitoring later,
        with the monitor method

    type : str
        specifies how tallied values are to be stored
            - 'any' (default) stores values in a list. This allows
               non numeric values. In calculations the values are
               forced to a numeric value (0 if not possible)
            - 'bool' (True, False) Actually integer >= 0 <= 255 1 byte
            - 'int8' integer >= -128 <= 127 1 byte
            - 'uint8' integer >= 0 <= 255 1 byte
            - 'int16' integer >= -32768 <= 32767 2 bytes
            - 'uint16' integer >= 0 <= 65535 2 bytes
            - 'int32' integer >= -2147483648<= 2147483647 4 bytes
            - 'uint32' integer >= 0 <= 4294967295 4 bytes
            - 'int64' integer >= -9223372036854775808 <= 9223372036854775807 8 bytes
            - 'uint64' integer >= 0 <= 18446744073709551615 8 bytes
            - 'float' float 8 bytes

    env : Environment
        environment where the monitor is defined |n|
        if omitted, default_env will be used
    '''

    cached_x = [(0, 0), (0, 0)]  # index=ex0, value=[hash,x]

    def __init__(self, name=omitted, monitor=True, type='any', env=omitted):
        if env is omitted:
            self.env = _default_env
        else:
            self.env = env
        if name is omitted:
            name = 'monitor.'
        self.name(name)
        try:
            self.xtypecode, _ = type_to_typecode_off(type)
        except KeyError:
            raise SalabimError('type (' + type + ') not recognized')
        self._timestamp = False
        self.reset(monitor)

    def reset(self, monitor=omitted):
        '''
        resets monitor

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled
            if omitted, no change of monitoring state
        '''

        if monitor is omitted:
            monitor = self._monitor
        if self.xtypecode:
            self._x = array.array(self.xtypecode)
        else:
            self._x = []
        self.monitor(monitor)

    def monitor(self, value=omitted):
        '''
        enables/disabled monitor

        Parameters
        ----------
        value : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change

        Returns
        -------
        True, if monitoring enabled. False, if not : bool
        '''
        if value is not omitted:
            self._monitor = value
        return self.monitor

    def tally(self, x):
        '''
        Parameters
        ----------
        x : any, preferably int, float or translatable into int or float
            value to be tallied
        '''
        if self._monitor:
            self._x.append(x)

    def name(self, txt=omitted):
        '''
        Parameters
        ----------
        txt : str
            name of the monitor |n|
            if txt ends with a period, the name will be serialized |n|
            if omittted, no change

        Returns
        -------
        Name of the monitor : str
        '''

        if txt is not omitted:
            _set_name(txt, self.env._nameserializeMonitor, self)
        return _decode_name(self._name)

    def mean(self, ex0=False):
        '''
        mean of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        mean : float
        '''

        x = self.x(ex0=ex0)
        if x:
            return sum(x) / len(x)
        else:
            return nan

    def std(self, ex0=False):
        '''
        standard deviation of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        standard deviation : float
        '''
        x = self.x(ex0=ex0)
        if x:
            wmean = self.mean(ex0)
            wvar = sum(((vx - wmean)**2) for vx in x) / len(x)
            return math.sqrt(wvar)
        else:
            return nan

    def minimum(self, ex0=False):
        '''
        minimum of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        minimum : float
        '''
        x = self.x(ex0=ex0)
        if x:
            return min(x)
        else:
            return nan

    def maximum(self, ex0=False):
        '''
        maximum of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        maximum : float
        '''

        x = self.x(ex0=ex0)
        if x:
            return max(x)
        else:
            return nan

    def median(self, ex0=False):
        '''
        median of tallied values weighted wioth their durations

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        median : float
        '''
        return self.percentile(50, ex0=ex0)

    def percentile(self, q, ex0=False):
        '''
        q-th percentile of tallied values

        Parameters
        ----------
        q : float
            percentage of the distribution |n|
            values <0 are treated a 0 |n|
            values >100 are treated as 100

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        q-th percentile: float
            0 returns the minimum, 50 the median and 100 the maximum
        '''

        q = max(0, min(q, 100))
        if self._timestamp:
            x, weights = self.xduration(ex0=ex0)
        else:
            x = self.x(ex0=ex0)
            weights = [1] * len(x)
        if len(x) == 1:
            return x[0]
        sumweights = sum(weights)
        if not sumweights:
            return nan

        xweights = sorted(zip(x, weights), key=lambda v: v[0])
        x_sorted, weights_sorted = zip(*xweights)
        weights_sorted = [0] + list(weights_sorted)
        threshold = sumweights * q / 100
        vcum_imin1 = 0
        for i, v in enumerate(weights_sorted):
            vcum_i = vcum_imin1 + v
            if vcum_i > threshold:
                break
            vcum_imin1 = vcum_i
        return interpolate(threshold, vcum_imin1, vcum_i, x_sorted[i - 1], x_sorted[min(i, len(x_sorted) - 1)])

    def bin_count(self, lowerbound, upperbound, ex0=False):
        '''
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
        '''
        x = self.x(ex0=ex0)
        return sum(1 for vx in x if (vx > lowerbound) and (vx <= upperbound))

    def number_of_entries(self, ex0=False):
        '''
        count of the number of entries

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        number of entries : int
        '''
        return len(self.x(ex0=ex0))

    def number_of_entries_zero(self):
        '''
        count of the number of zero entries

        Returns
        -------
        number of zero entries : int
        '''
        return self.number_of_entries() - self.number_of_entries(ex0=True)

    def print_statistics(self, show_header=True, show_legend=True, do_indent=False):
        '''
        print monitor statistics

        Parameters
        ----------
        show_header: bool
            primarily for internal use

        show_legend: bool
            primarily for internal use

        do_indent: bool
            primarily for internal use
        '''
        if do_indent:
            l = 45
        else:
            l = 0
        indent = pad('', l)

        if show_header:
            print(indent + 'Statistics of {} at {}'.format(self.name(), fn(self.env._now, 13, 3)))

        if show_legend:
            print(
                indent + '                        all    excl.zero         zero')
            print(
                pad('-' * (l - 1) + ' ', l) + '-------------- ------------ ------------ ------------')

        if self._timestamp:
            if self.duration() == 0:
                print(pad(self.name(), l) + 'no data')
                return
            else:
                print(pad(self.name(), l) + 'duration      {}{}{}'.
                    format(fn(self.duration(), 13, 3),
                    fn(self.duration(ex0=True), 13, 3), fn(self.duration_zero(), 13, 3)))
        else:
            if self.number_of_entries() == 0:
                print(pad(self.name(), l) + 'no entries')
                return
            else:
                print(pad(self.name(), l) + 'entries       {}{}{}'.
                    format(fn(self.number_of_entries(), 13, 3),
                    fn(self.number_of_entries(ex0=True), 13, 3), fn(self.number_of_entries_zero(), 13, 3)))

        print(indent + 'mean          {}{}'.
              format(fn(self.mean(), 13, 3), fn(self.mean(ex0=True), 13, 3)))
        print(indent + 'std.deviation {}{}'.
              format(fn(self.std(), 13, 3), fn(self.std(ex0=True), 13, 3)))
        print()
        print(indent + 'minimum       {}{}'.
              format(fn(self.minimum(), 13, 3), fn(self.minimum(ex0=True), 13, 3)))
        print(indent + 'median        {}{}'.
              format(fn(self.percentile(50), 13, 3), fn(self.percentile(50, ex0=True), 13, 3)))
        print(indent + '90% percentile{}{}'.
              format(fn(self.percentile(90), 13, 3), fn(self.percentile(90, ex0=True), 13, 3)))
        print(indent + '95% percentile{}{}'.
              format(fn(self.percentile(95), 13, 3), fn(self.percentile(95, ex0=True), 13, 3)))
        print(indent + 'maximum       {}{}'.
              format(fn(self.maximum(), 13, 3), fn(self.maximum(ex0=True), 13, 3)))

    def print_histogram(self, number_of_bins=30, lowerbound=0, bin_width=1, ex0=False):
        '''
        print monitor statistics and histogram

        Parameters
        ----------
        number_of_bins : int
            number of bins |n|
            if 0, also the header of the histogram will be surpressed

        lowerbound: float
            first bin

        bin_width : float
            width of the bins

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes
        '''
        if self._timestamp:
            x, weights = self.xduration(ex0=ex0)
            weight_total = sum(weights)
        else:
            x = self.x(ex0=ex0)
            weight_total = len(x)

        print('Histogram of', self.name())
        if weight_total == 0:
            print()
            if self._timestamp:
                print('no data')
            else:
                print('no entries')
            return

        self.print_statistics(show_header=False, show_legend=True, do_indent=False)
        if number_of_bins > 0:
            print()
            if self._timestamp:
                print('           <=      duration     %  cum%')
            else:
                print('           <=       entries     %  cum%')

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
                count = self.bin_count(lb, ub)
                if weight_total == 0:
                    perc = nan
                    cumperc = nan
                    s = '|'
                else:
                    perc = count / weight_total
                    cumperc += perc
                    scale = 80
                    n = int(perc * scale)
                    ncum = int(cumperc * scale) + 1
                    s = ('*' * n) + (' ' * (scale - n))
                    s = s[:ncum - 1] + '|' + s[ncum + 1:]

                print('{} {}{}{} {}'.
                      format(fn(ub, 13, 3), fn(count, 13, 3), fn(perc * 100, 6, 1), fn(cumperc * 100, 6, 1), s))

    def x(self, ex0=False, force_numeric=True):
        '''
        array/list of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        convert_to_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        Returns
        -------
        all tallied values : array/list
        '''
        thishash = hash((tuple(self._x), force_numeric))

        if Monitor.cached_x[ex0][0] == thishash:
            return Monitor.cached_x[ex0][1]

        if self.xtypecode or (not force_numeric):
            xall = self._x
            typecode = self.xtypecode
        else:
            xall = list_to_array(self._x)
            typecode = xall.typecode

        if ex0:
            x = [vx for vx in xall if vx != 0]
            if typecode:
                x = array.array(typecode, x)
        else:
            x = xall

        Monitor.cached_x[ex0] = (hash, x)
        return x


class MonitorTimestamp(Monitor):
    '''
    monitortimestamp object

    Parameters
    ----------
    name : str
        name to be used at print_histogram

    getter : function
        this function must return the current value |n|
        usually this will be a method of an object

    monitor : bool
        if True (default), monitoring will be on. |n|
        if False, monitoring is disabled |n|
        it is possible to control monitoring later,
        with the monitor method

    type : str
        specifies how tallied values are to be stored
        Using a int, uint of float type results in less memory usage and better
        performance. Note that the getter should never return the number not to use
        as this is used to indicate 'off'

            - 'any' (default) stores values in a list. This allows for
               non numeric values. In calculations the values are
               forced to a numeric value (0 if not possible) do not use -inf
            - 'bool' bool (False, True). Actually integer >= 0 <= 254 1 byte do not use 255
            - 'int8' integer >= -127 <= 127 1 byte do not use -128
            - 'uint8' integer >= 0 <= 254 1 byte do not use 255
            - 'int16' integer >= -32767 <= 32767 2 bytes do not use -32768
            - 'uint16' integer >= 0 <= 65534 2 bytes do not use 65535
            - 'int32' integer >= -2147483647 <= 2147483647 4 bytes do not use -2147483648
            - 'uint32' integer >= 0 <= 4294967294 4 bytes do not use 4294967295
            - 'int64' integer >= -9223372036854775807 <= 9223372036854775807 8 bytes do not use -9223372036854775808
            - 'uint64' integer >= 0 <= 18446744073709551614 8 bytes do not use 18446744073709551615
            - 'float' float 8 bytes do not use -inf

    env : Environment
        environment where the monitor is defined |n|
        if omitted, default_env will be used

    Note
    ----
    A MonitorTimestamp collects both the value and the time.
    All statistics are based on the durations as weights.

    Example
    -------
        Tallied at time   0: 10 (xnow in definition of monitortimestamp) |n|
        Tallied at time  50: 11 |n|
        Tallied at time  70: 12 |n|
        Tallied at time  80: 10 |n|
        Now = 100

        This results in:  |n|
        x=  10 duration 50 |n|
        x=  11 duration 20 |n|
        x=  12 duration 10 |n|
        x=  10 duration 20

        And thus a mean of (10*50+11*20+12*10+10*20)/(50+20+10+20)
    '''

    cached_xduration = [(0, ()), (0, ())]  # index=ex0, value=[hash,(x,duration)]

    def __init__(self, name, getter, monitor=True, type='any', env=omitted):
        if name is omitted:
            name = 'monitortimestamp.'
        if env is omitted:
            self.env = _default_env
        else:
            self.env = env
        try:
            self.xtypecode, self.off = type_to_typecode_off(type)
        except KeyError:
            raise SalabimError('type (' + type + ') not recognized')

        self.name(name)
        self._timestamp = True
        self._getter = getter
        self.reset(monitor=monitor)

    def __call__(self):  # direct moneypatching __call__ doesn't work
        return self._getter()

    def reset(self, monitor=omitted):
        '''
        resets timestamped monitor

        Parameters
        ----------
        monitor : bool
            if True (default), monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, the monitor state remains unchanged
        '''
        if monitor is not omitted:
            self._monitor = monitor
        if self.xtypecode:
            self._x = array.array(self.xtypecode)
        else:
            self._x = []

        if self._monitor:
            self._x.append(self._getter())
        else:
            self._x.append(self.off)
        self._t = array.array('d')
        self._t.append(self.env._now)

    def monitor(self, value=omitted):
        '''
        enables/disabled timestamped monitor

        Parameters
        ----------
        value : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change

        Returns
        -------
        True, if monitoring enabled. False, if not : bool
        '''

        if value is not omitted:
            self._monitor = value
            if self._monitor:
                self.tally()
            else:
                self._tally_off()
        return self.monitor

    def tally(self):
        '''
        tally the current value, if monitor is on
        '''
        if self._monitor:
            x = self._getter()
            t = self.env._now
            if self._t[-1] == t:
                self._x[-1] = x
            else:
                self._x.append(x)
                self._t.append(t)

    def _tally_off(self):
        t = self.env._now
        if self._t[-1] == t:
            self._x[-1] = self.off
        else:
            self._x.append(self.off)
            self._t.append(t)

    def name(self, txt=omitted):
        '''
        Parameters
        ----------
        txt : str
            name of the monitor |n|
            if txt ends with a period, the name will be serialized |n|
            if omittted, no change

        Returns
        -------
        Name of the monitor : str
        '''
        if txt is not omitted:
            _set_name(txt, self.env._nameserializeMonitorTimestamp, self)
        return _decode_name(self._name)

    def mean(self, ex0=False):
        '''
        mean of tallied values, weighted with their durations

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        mean : float
        '''
        x, duration = self.xduration(ex0=ex0)
        sumduration = sum(duration)
        if sumduration:
            return sum(vx * vduration for vx, vduration in zip(x, duration)) / sumduration
        else:
            return nan

    def std(self, ex0=False):
        '''
        standard deviation of tallied values, weighted with their durations

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        standard deviation : float
        '''
        x, duration = self.xduration(ex0=ex0)
        sumduration = sum(duration)
        if sumduration:
            wmean = self.mean(ex0)
            wvar = sum((vduration * (vx - wmean)**2) for vx, vduration in zip(x, duration)) / sumduration
            return math.sqrt(wvar)
        else:
            return nan

    def minimum(self, ex0=False):
        '''
        minimum of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        minimum : float
        '''
        x, duration = self.xduration(ex0=ex0)
        if x:
            return min(x)
        else:
            return nan

    def maximum(self, ex0=False):
        '''
        maximum of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        maximum : float
        '''
        x, duration = self.xduration(ex0=ex0)
        if x:
            return max(x)
        else:
            return nan

    def median(self, ex0=False):
        '''
        median of tallied values weighted with their durations

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        median : float
        '''
        return self.percentile(50, ex0=ex0)

    def percentile(self, q, ex0=False):
        '''
        q-th percentile of tallied values, weighted with their durations

        Parameters
        ----------
        q : float
            percentage of the distribution |n|
            values <0 are treated a 0 |n|
            values >100 are treated as 100

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        q-th percentile: float
            0 returns the minimum, 50 the median and 100 the maximum
        '''
        return Monitor.percentile(self, q, ex0=ex0)

    def bin_count(self, lowerbound, upperbound, ex0=False):
        '''
        count of the number of tallied values,
        weighted with the duration in range (lowerbound,upperbound]

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
        number of values >lowerbound and <=upperbound: int
        '''
        x, duration = self.xduration(ex0=ex0)
        return sum((vduration for vx, vduration in zip(x, duration) if (vx > lowerbound) and (vx <= upperbound)))

    def duration(self, ex0=False):
        '''
        total duration

        Parameters
        ----------
        ex0 : bool
            if False (default), include samples with value 0. if True, exclude zero samples.

        Returns
        -------
        total duration
        '''
        _, duration = self.xduration(ex0=ex0)
        return sum(duration)

    def duration_zero(self):
        '''
        total duration of samples with value 0

        Returns
        -------
        total duration of zero samples
        '''
        return self.duration() - self.duration(ex0=True)

    def xduration(self, ex0=False, force_numeric=True):
        '''
        tuple of array with x-values and array with durations

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        Returns
        -------
        array/list with x-values and array with durations : tuple
        '''

        thishash = hash((tuple(self._x), tuple(self._t), force_numeric))

        if MonitorTimestamp.cached_xduration[ex0][0] == thishash:
            return MonitorTimestamp.cached_xduration[ex0][1]

        durationall = array.array('d')
        for i, t in enumerate(self._t):
            if i != 0:
                durationall.append(t - lastt)  # NOQA
            lastt = t

        durationall.append(self.env._now - lastt)

        if self.xtypecode or (not force_numeric):
            xall = self._x
            typecode = self.xtypecode
        else:
            xall = list_to_array(self._x)
            typecode = xall.typecode

        duration = array.array('d')
        if typecode:
            x = array.array(typecode)
        else:
            x = []

        for vx, vduration in zip(xall, durationall):
            if vx != self.off:
                if (not ex0) or (vx != 0):
                    x.append(vx)
                    duration.append(vduration)

        MonitorTimestamp.cached_xduration[ex0] = (thishash, (x, duration))
        return x, duration

    def xt(self, ex0=False, exoff=False, force_numeric=True):
        '''
        tuple of array/list with x-values and array with timestamp

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        exoff : bool
            if False (default), include self.off. if True, exclude self.off's

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        Returns
        -------
        array/list with x-values and array with timestamps : tuple

        Note
        ----
        The value self.off is stored when monitoring is turned off
        '''
        if self.xtypecode or (not force_numeric):
            xall = self._x
            typecode = self.xtypecode
        else:
            xall = list_to_array(self._x)
            typecode = xall.typecode

        if typecode:
            x = array.array(typecode)
        else:
            x = []
        t = array.array('d')
        for vx, vt in zip(xall, self._t):
            if vx != self.off:
                if not ex0 or (vx != 0):
                    x.append(vx)
                    t.append(vt)

        return x, t

    def tx(self, ex0=False, exoff=False, force_numeric=False):
        '''
        tuple of array with timestamps and array/list with x-values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        exoff : bool
            if False (default), include self.off. if True, exclude self.off's

        force_numeric : bool
            if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0 |n|
            if False, do not interpret x-values, return as list if type is list

        Returns
        -------
        array with timestamps and array/list with x-values : tuple

        Note
        ----
        The value self.off is stored when monitoring is turned off
        '''
        return tuple(reversed(self.xt(ex0=ex0, exoff=exoff, force_numeric=force_numeric)))

    def print_statistics(self, show_header=True, show_legend=True, do_indent=False):
        '''
        print timestamped monitor statistics

        Parameters
        ----------
        show_header: bool
            primarily for internal use

        show_legend: bool
            primarily for internal use

        do_indent: bool
            primarily for internal use
        '''

        Monitor.print_statistics(self, show_header, show_legend, do_indent)

    def print_histogram(self, number_of_bins=30, lowerbound=0, bin_width=1, ex0=False):
        '''
        print timestamped monitor statistics and histogram

        Parameters
        ----------
        number_of_bins : int
            number of bins |n|
            if 0, also the header of the histogram will be surpressed

        lowerbound: float
            first bin

        bin_width : float
            width of the bins

        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes
        '''
        Monitor.print_histogram(self, number_of_bins, lowerbound, bin_width, ex0)


if Pythonista:

    class MyScene(scene.Scene):

        def __init__(self, *args, **kwargs):
            scene.Scene.__init__(self, *args, **kwargs)
            MyScene.this_scene = self

        def setup(self):
            pass

        def touch_ended(self, touch):
            for uio in an_env.ui_objects:
                if uio.type == 'button':
                    if touch.location in \
                            scene.Rect(uio.x - 2, uio.y - 2, uio.width + 2, uio.height + 2):
                        uio.action()
                if uio.type == 'slider':
                    if touch.location in\
                            scene.Rect(uio.x - 2, uio.y - 2, uio.width + 4, uio.height + 4):
                        xsel = touch.location[0] - uio.x
                        uio._v = uio.vmin + \
                            round(-0.5 + xsel / uio.xdelta) * uio.resolution
                        uio._v = max(min(uio._v, uio.vmax), uio.vmin)
                        if uio.action is not None:
                            uio.action(uio._v)

        def draw(self):

            if an_env is not None:
                scene.background(pythonistacolor(
                    colorspec_to_tuple(an_env.background_color)))
                if an_env.paused:
                    an_env.t = an_env.start_animation_time
                else:
                    an_env.t = \
                        an_env.start_animation_time +\
                        ((time.time() -
                          an_env.start_animation_clocktime) * an_env.speed)

                while an_env.peek() < an_env.t:
                    an_env.step()
                    if an_env._current_component == an_env._main:
                        an_env.print_trace(
                            '{:10.3f}'.format(an_env._now),
                            an_env._main.name(), 'current')
                        an_env._main._scheduled_time = inf
                        an_env._main._status = current
                        an_env.an_quit()
                        return

                if not an_env.paused:
                    an_env.frametimes.append(time.time())

                an_env.an_objects.sort(
                    key=lambda obj: (-obj.layer(an_env.t), obj.sequence))
                touchvalues = self.touches.values()

                capture_image = Image.new('RGB',
                    (an_env.width, an_env.height), colorspec_to_tuple(an_env.background_color))

                an_env.animation_pre_tick(an_env.t)
                for ao in an_env.an_objects:
                    ao.make_pil_image(an_env.t)
                    if ao._image_visible:
                        capture_image.paste(ao._image,
                            (int(ao._image_x),
                            int(an_env.height - ao._image_y - ao._image.size[1])),
                            ao._image)
                an_env.animation_post_tick(an_env.t)

                ims = scene.load_pil_image(capture_image)
                scene.image(ims, 0, 0, *capture_image.size)

                for uio in an_env.ui_objects:

                    if uio.type == 'button':
                        linewidth = uio.linewidth

                        scene.push_matrix()
                        scene.fill(pythonistacolor(uio.fillcolor))
                        scene.stroke(pythonistacolor(uio.linecolor))
                        scene.stroke_weight(linewidth)
                        scene.rect(uio.x, uio.y, uio.width, uio.height)
                        scene.tint(uio.color)
                        scene.translate(uio.x + uio.width / 2,
                                        uio.y + uio.height / 2)
                        scene.text(uio.text(), uio.font,
                                   uio.fontsize, alignment=5)
                        scene.tint(1, 1, 1, 1)
                        # required for proper loading of images
                        scene.pop_matrix()
                    elif uio.type == 'slider':
                        scene.push_matrix()
                        scene.tint(pythonistacolor(uio.labelcolor))
                        v = uio.vmin
                        x = uio.x + uio.xdelta / 2
                        y = uio.y
                        mindist = inf
                        v = uio.vmin
                        while v <= uio.vmax:
                            if abs(v - uio._v) < mindist:
                                mindist = abs(v - uio._v)
                                vsel = v
                            v += uio.resolution
                        thisv = uio._v
                        for touch in touchvalues:
                            if touch.location in\
                                    scene.Rect(uio.x, uio.y, uio.width, uio.height):
                                xsel = touch.location[0] - uio.x
                                vsel = round(-0.5 + xsel /
                                             uio.xdelta) * uio.resolution
                                thisv = vsel
                        scene.stroke(pythonistacolor(uio.linecolor))
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
                        scene.translate(xfirst, uio.y + uio.height + 2)
                        scene.text(uio.label, uio.font,
                                   uio.fontsize, alignment=9)
                        scene.pop_matrix()
                        scene.translate(uio.x + uio.width, y + uio.height + 2)
                        scene.text(str(thisv) + ' ',
                                   uio.font, uio.fontsize, alignment=7)
                        scene.tint(1, 1, 1, 1)
                        # required for proper loading of images later
                        scene.pop_matrix()


class Qmember():
    def __init__(self):
        pass

    def insert_in_front_of(self, m2, c, q, priority):
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
        q.env.print_trace('', '', c.name(), 'enter ' + q.name())
        q.length.tally()
        if q._animate_on:
            q._animate_update()


class Queue(object):
    '''
    Queue object

    Parameters
    ----------
    name : str
        name of the queue |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name queue. (serialized)

    monitor : bool
        if True (default) , both length and length_of_stay are monitored |n|
        if False, monitoring is disabled.

    env : Environment
        environment where the queue is defined |n|
        if omitted, default_env will be used

    _isinternal : bool
        for internal use only
    '''

    def __init__(self, name=omitted, monitor=True, env=omitted, _isinternal=False):
        if env is omitted:
            self.env = _default_env
        else:
            self.env = env
        if name is omitted:
            name = 'queue.'
        self.name(name)
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
        self._animate_on = False
        self.length = MonitorTimestamp(
            ('Length of ', self), getter=self._getlength, monitor=monitor, type='uint32', env=self.env)
        self.length_of_stay = Monitor(
            ('Length of stay in ', self), monitor=monitor, type='float')
        if not _isinternal:
            self.env.print_trace('', '', self.name() + ' create')

    def _animate_update(self):
        if self._animate_reverse:
            q = reversed(self)
        else:
            q = self
        x = self._animate_x
        y = self._animate_y
        for c in q:
            if self not in c._aos:
                c._aos[self] = c.animation_objects(self)
                if isinstance(c._aos[self], (tuple, list)):
                    if len(c._aos[self]) <= 1:
                        raise SalabimError('at least 2 elements (sizex, sizey) required')
                    for i, el in enumerate(c._aos[self]):
                        if i == 0:
                            try:
                                float(el)
                            except ValueError:
                                raise SalabimError('element #0 (sizex) of tuple/list not numeric')
                        elif i == 1:
                            try:
                                float(el)
                            except ValueError:
                                raise SalabimError('element #1 (sizey) of tuple/list not numeric')
                        else:
                            if not isinstance(el, Animate):
                                raise SalabimError('element #{} of tuple/list is not Animate type'.format(i))
                else:
                    raise SalabimError('animation_objects should return list or tuple')

            for ao in c._aos[self][2:]:
                ao.x0 = x
                ao.y0 = y
            x += self._displacement_x * c._aos[self][0]
            y += self._displacement_y * c._aos[self][1]

    def animate(self, x=500, y=100, direction='w', on=True, reverse=False):
        '''
        turns on/off animation for the queue

        Parameters
        ----------
        x : float
            x-position of the first component in the queue |n|
            default: 500

        y : float
            y-position of the first component in the queue |n|
            default: 100

        direction : str
            if 'w', waitling line runs westwards (i.e. from right to left) (default) |n|
            if 'n', waitling line runs northeards (i.e. from bottom to top) |n|
            if 'e', waitling line runs eastwards (i.e. from left to right) |n|
            if 's', waitling line runs southwards (i.e. from top to bottom)

        on : bool
            if True (default) do animate the queue. If False, do not animate.

        reverse : bool
            if False (default), display in normal order. If True, reversed.
        '''

        self._animate_on = on
        if on:
            self._animate_x = x
            self._animate_y = y
            self._displacement_x, self._displacement_y = \
                {'w': (-1, 0), 'n': (0, 1), 'e': (1, 0), 's': (0, -1)}[direction.lower()]

            self._animate_reverse = reverse
            self._animate_update()
        else:
            for c in self:
                c._remove_from_aos(self)

    def _getlength(self):
        return self._length

    def reset_monitors(self, monitor=omitted):
        '''
        resets queue monitor length_of_stay and time stamped monitor length

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change of monitoring state

        Note
        ----
        it is possible to reset individual monitoring with length_of_stay.reset() and length.reset()
        '''
        self.length.reset(monitor=monitor)
        self.length_of_stay.reset(monitor=monitor)

    def monitor(self, value):
        '''
        enables/disables monitoring of length_of_stay and length

        Parameters
        ----------
        value : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|

        Note
        ----
        it is possible to individually control monitoring with length_of_stay.monitor() and length.monitor()
        '''

        self.length.monitor(value=value)
        self.length_of_stay.monitor(value=value)

    def __repr__(self):
        return 'Queue(' + self.name() + ')'

    def print_info(self):
        print('Queue ' + hex(id(self)))
        print('  name=' + self.name())
        if self._length:
            print('  component(s):')
            mx = self._head.successor
            while mx != self._tail:
                print('    ' + pad(mx.component.name(), 20) +
                    ' enter_time' + time_to_string(mx.enter_time) +
                    ' priority=' + str(mx.priority))
                mx = mx.successor
        else:
            print('  no components')

    def print_statistics(self):
        '''
        prints a summary of statistics of a queue
        '''
        print('Statistics of {} at {}'.format(self.name(), fn(self.env._now, 13, 3)))
        self.length.print_statistics(
            show_header=False, show_legend=True, do_indent=True)

        print()
        self.length_of_stay.print_statistics(
            show_header=False, show_legend=False, do_indent=True)

    def name(self, txt=omitted):
        '''
        Parameters
        ----------
        txt : str
            name of the queue |n|
            if txt ends with a period, the name will be serialized |n|
            if omittted, no change

        Returns
        -------
        Name of the queue : str
        '''

        if txt is not omitted:
            _set_name(txt, self.env._nameserializeQueue, self)
        return _decode_name(self._name)

    def base_name(self):
        '''
        Returns
        -------
        base name of the queue (the name used at init or name): str
        '''
        return self._base_namee

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the queue : int
            (the sequence number at init or name) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot at the end)
            will be numbered)
        '''
        return self._sequence_number

    def add(self, component):
        '''
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
        or 0 if queue is empty
        '''
        component.enter(self)

    def add_at_head(self, component):
        '''
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
        '''
        component.enter_to_head(self)

    def add_in_front_of(self, component, poscomponent):
        '''
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
        '''
        component.enter_in_front_off(self, poscomponent)

    def add_behind(self, component, poscomponent):
        '''
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

        '''
        component.enter_behind(self, poscomponent)

    def add_sorted(self, component, priority):
        '''
        adds a component to a queue, according to the priority

        Parameters
        ----------
        component : Component
            component to be added to the queue |n|
            may not be member of the queue yet

        priority : float
            priority of the component |n|

        Note
        ----
        component will be placed just after the last component with
        a priority <= priority
        '''
        component.enter_sorted(self, priority)

    def remove(self, component):
        '''
        removes component from the queue

        Parameters
        ----------
        component : Component
            component to be removed |n|
            must be member of the queue
        '''
        component.leave(self)

    def head(self):
        '''
        Returns
        -------
        the head component of the queue, if any. None otherwise : Component

        Note
        ----
        q[0] is a more Pythonic way to access the head of the queue
        '''
        return self._head.successor.component

    def tail(self):
        '''
        Returns
        -------
        the tail component of the queue, if any. None otherwise : Component

        Note
        -----
        q[-1] is a more Pythonic way to access the tail of the queue
        '''
        return self._tail.predecessor.component

    def pop(self):
        '''
        removes the head component, if any. |n|

        Returns
        -------
        The head component : Component
            None if the queue is empty
        '''
        c = self._head.successor.component
        if c is not None:
            c.leave(self)
        return c

    def successor(self, component):
        '''
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
        '''
        return component.successor(self)

    def predecessor(self, component):
        '''
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
        '''
        return component.predecessor(self)

    def __contains__(self, component):
        return component._member(self) is not None

    def __getitem__(self, key):
        if isinstance(key, slice):
            # Get the start, stop, and step from the slice
            startval, endval, incval = key.indices(self._length)
            if incval > 0:
                l = []
                targetval = startval
                mx = self._head.successor
                count = 0
                while mx != self._tail:
                    if targetval >= endval:
                        break
                    if targetval == count:
                        l.append(mx.component)
                        targetval += incval
                    count += 1
                    mx = mx.successor
            else:
                l = []
                targetval = startval
                mx = self._tail.predecessor
                count = self._length - 1
                while mx != self._head:
                    if targetval <= endval:
                        break
                    if targetval == count:
                        l.append(mx.component)
                        targetval += incval  # incval is negative here!
                    count -= 1
                    mx = mx.predecessor

            return list(l)

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
            raise TypeError('Invalid argument type.')

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
        while len(iter_list) > iter_index:
            if self._iter_touched[iter_sequence]:
                # place all taken qmembers on the list
                iter_list = iter_list[:iter_index]
                mx = self._tail.predecessor
                while mx != self._head:
                    if mx not in iter_list:
                        iter_list.append(mx)
                    mx = mx.precessor
                self._iter_touched[iter_sequence] = False
            else:
                c = iter_list[iter_index].component
                if c is not None:  # skip deleted components
                    yield c
                iter_index += 1

        del self._iter_touched[iter_sequence]

    def index(self, component):
        '''
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
        '''
        return component.index_in_queue(self)

    def component_with_name(self, txt):
        '''
        returns a component in the queue according to its name

        Parameters
        ----------
        txt : str
            name of component to be retrieved

        Returns
        -------
        the first component in the queue with name txt : Component |n|
            returns None if not found
        '''
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
        while len(iter_list) > iter_index:
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

    def union(self, q, name):
        '''
        Parameters
        ----------
        q : Queue
            queue to be unioned with self

        name :str
            name of the  new queue

        Returns
        -------
        queue containing all elements of self and q : Queue

        Note
        ----
        the priority will be set to 0 for all components in the
        resulting  queue |n|
        the order of the resulting queue is as follows |n|:
        first all components of self, in that order,
        followed by all components in q that are not in self,
        in that order.
        '''
        save_trace = self.env._trace
        self.env._trace = False
        q1 = Queue(name=name, env=self.env)
        components = []
        mx = self._head.successor
        while mx != self._tail:
            components.append(mx.component)
            mx = mx.successor
        mx = q._head.successor
        while mx != q._tail:
            if mx.component not in components:
                components.append(mx.component)
            mx = mx.successor
        for c in components:
            Qmember().insert_in_front_of(q1._tail, c, q1, 0)
        self.env._trace = save_trace
        return q1

    def intersect(self, q, name):
        '''
        returns the intersect of two queues

        Parameters
        ----------
        q : Queue
            queue to be intersected with self

        name :str
            name of the  new queue

        the resulting queue will contain all elements that
        are in self and q |n|
        the priority will be set to 0 for all components in the
        resulting  queue |n|
        the order of the resulting queue is as follows |n|:
        in the same order as in self.
        '''
        save_trace = self.env._trace
        self.env._trace = False
        q1 = Queue(name=name, env=self.env)
        components = []
        mx = q._head.successor
        while mx != q._tail:
            components.append(mx.component)
            mx = mx.successor
        mx = self._head.successor
        while mx != self._tail:
            if mx.component in components:
                Qmember().insert_in_front_of(q1._tail, mx.component, q1, 0)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def difference(self, q, name):
        '''
        returns the difference of two queues

        Parameters
        ----------
        q : Queue
            queue to be 'subtracted' from self

        name :str
            name of the  new queue

        the resulting queue will contain all elements of self that are not
        in q |n|
        the priority will be copied from the original queue.
        Also, the order will be maintained.
        '''
        save_trace = self.env._trace
        self.env._trace = False
        q1 = Queue(name=name, env=self.env)
        components = []
        mx = q._head.successor
        while mx != q._tail:
            components.append(mx.component)
            mx = mx.successor

        mx = self._head.successor
        while mx != self._tail:
            if mx.component not in components:
                Qmember().insert_in_front_of(
                    q1._tail, mx.component, q1, mx.priority)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def copy(self, name):
        '''
        returns a copy of two queues

        Parameters
        ----------
        name : str
            name of the new queue

        the resulting queue will contain all elements of self |n|
        The priority will be copied from original queue.
        Also, the order will be maintained.
        '''
        save_trace = self.env._trace
        self.env._trace = False
        q1 = Queue(name=name, env=self.env)
        mx = self._head.successor
        while mx != self._tail:
            Qmember().insert_in_front_of(q1._tail, mx.component, q1, mx.priority)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def move(self, name):
        '''
        makes a copy of a queue and empties the original

        Parameters
        ----------
        name : str
            name of the new queue

        the resulting queue will contain all elements of self,
        with the proper priority |n|
        self will be emptied
        '''
        q1 = self.copy(name)
        self.clear()
        return q1

    def clear(self):
        '''
        empties a queue

        removes all components from a queue
        '''
        mx = self._head.successor
        while mx != self._tail:
            c = mx.component
            mx = mx.successor
            c._leave(self)


def finish():
    if Pythonista:
        if MyScene.this_scene is not None:
            MyScene.this_scene.view.close()
    print('stopped by user')
    exit()


class Environment(object):
    '''
    environment object

    Parameters
    ----------
    trace : bool
        defines whether to trace or not |n|
        if omitted, False

    random_seed : hashable object, usually int
        the seed for random, equivalent to random.seed() |n|
        if None, a purely random value (based on the current time) will be used
        (not reproducable) |n|
        if the null string (''), no action on random is taken |n|
        if omitted, 1234567 will be used.

    name : str
        name of the environment |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name ``environment.`` (serialized)

    is_default_env : bool
        if True, this environment becomes the default environment |n|
        if False, no change |n|
        if omitted, this environment becomes the default environment |n|

    Note
    ----
    The trace may be switched on/off later with trace |n|
    The seed may be later set with random_seed() |n|
    Initially, the random stream will be seeded with the value 1234567.
    If required to be purely, not not reproducable, values, use
    random_seed=None.
    '''
    global an_env

    _nameserialize = {}
    an_env = None

    def __init__(self, trace=False, random_seed=omitted, name=omitted, is_default_env=True):
        global _default_env
        if is_default_env:
            _default_env = self
        if name is omitted:
            if is_default_env:
                name = 'Default environment'
            else:
                name = 'environment.'
        self._trace = trace
        if random_seed != '':
            if random_seed is omitted:
                random_seed = 1234567
            random.seed(random_seed)
        self.name(name)
        self.env = self
        # just to allow main to be created; will be reset later
        self._nameserializeComponent = {}
        self._now = 0
        self._main = Component(name='main', env=self, process=None)
        self._main._status = current
        self._current_component = self._main
        self.ui_objects = []
        self.print_trace('{:10.3f}'.format(self._now), 'main', 'current')
        self._nameserializeQueue = {}
        self._nameserializeComponent = {}
        self._nameserializeResource = {}
        self._nameserializeState = {}
        self._nameserializeMonitor = {}
        self._nameserializeMonitorTimestamp = {}
        self._seq = 0
        self._event_list = []
        self._standbylist = []
        self._pendingstandbylist = []

        self.an_objects = []
        self.ui_objects = []
        self.serial = 0
        self.speed = 1
        self.animate = False
        if Pythonista:
            self.width, self.height = ui.get_screen_size()
            self.width = int(self.width)
            self.height = int(self.height)
        else:
            self.width = 1024
            self.height = 768
        self.x0 = 0
        self.y0 = 0
        self.x1 = self.width
        self.background_color = 'white'
        self.fps = 30
        self.modelname = ''
        self.use_toplevel = False
        self.show_fps = True
        self.show_speed = True
        self.show_time = True
        self.video = ''

    def serialize(self):
        self.serial += 1
        return self.serial

    def __repr__(self):
        return 'Environment(' + self.name() + ')'

    def animation_pre_tick(self, t):
        '''
        called just before the animation object loop. |n|
        Default behaviour: just return

        Parameters
        ----------
        t : float
            Current (animation) time.
        '''
        return

    def animation_post_tick(self, t):
        '''
        called just after the animation object loop. |n|
        Default behaviour: just return

        Parameters
        ----------
        t : float
            Current (animation) time.
        '''
        return

    def print_info(self):
        print('Environment ' + hex(id(self)))
        print('  name=' + self.name() +
            (' (animation environment)' if self == an_env else ''))
        print('  now=' + time_to_string(self._now))
        print('  current_component=' + self._current_component.name())
        print('  trace=' + str(self._trace))

    def step(self):
        '''
        executes the next step of the future event list

        for advanced use with animation / GUI loops
        '''
        if len(self.env._pendingstandbylist) > 0:
            c = self.env._pendingstandbylist.pop(0)
            if c._status == standby:  # skip cancelled components
                c._status = current
                c._scheduled_time = inf
                self.env._current_component = c
                self.print_trace('{:10.3f}'.format(self._now), c.name(),
                                 'current (standby)')
                try:
                    next(c._process)
                    return
                except StopIteration:
                    c.release()
                    self.print_trace('{:10.3f}'.format(
                        self._now), c.name(), 'ended')
                    c._status = data
                    c._scheduled_time = inf
                    c._process = None
                    if an_env == self:
                        for ao in self.an_objects[:]:
                            if ao.parent == c:
                                self.an_objects.remove(ao)
                    return
        if len(self.env._standbylist) > 0:
            self._pendingstandbylist = list(self.env._standbylist)
            self._standbylist = []

        if self._event_list:
            (t, _, c) = heapq.heappop(self._event_list)
        else:
            t = inf
            c = self._main
        c._on_event_list = False
        self.env._now = t

        try:
            self._current_component = c
            if c._process is None:  # denotes end condition
                return

            c._status = current
            self.print_trace('{:10.3f}'.format(self._now), c.name(),
                             'current')
            c._check_fail()
            c._scheduled_time = inf
            next(c._process)
            return
        except StopIteration:
            c.release()
            self.print_trace('{:10.3f}'.format(self._now), c.name(), 'ended')
            c._status = data
            c._scheduled_time = inf
            c._process = None
            if an_env == self:
                for ao in self.an_objects[:]:
                    if ao.parent == c:
                        self.an_objects.remove(ao)
            return

    def _print_event_list(self, s):
        print('eventlist ', s)
        for (t, seq, comp) in self._event_list:
            print('{:10.3f} {}'.format(t, comp.name()))

    def animation_parameters(self,
                             animate=omitted, speed=omitted, width=omitted, height=omitted,
                             x0=omitted, y0=0, x1=omitted, background_color=omitted,
                             fps=omitted, modelname=omitted, use_toplevel=omitted,
                             show_fps=omitted, show_speed=omitted, show_time=omitted,
                             video=omitted):
        '''
        set animation parameters

        Parameters
        ----------
        animate : bool
            animate indicator |n|
            if omitted, True, i.e. animation on |n|
            Installation of PIL is required for animation.

        speed : float
            speed |n|
            specifies how much faster or slower than real time the animation will run.
            e.g. if 2, 2 simulation time units will be displayed per second.

        width : int
            width of the animation in screen coordinates |n|
            if omitted, no change. At init of the environment, the width will be
            set to 1024 for CPython and the current screen width for Pythonista.

        height : int
            height of the animation in screen coordinates |n|
            if omitted, no change. At init of the environment, the height will be
            set to 768 for CPython and the current screen height for Pythonista.

        x0 : float
            user x-coordinate of the lower left corner |n|
            if omitted, no change. At init of the environment, x0 will be set to 0.

        y0 : float
            user y_coordinate of the lower left corner |n|
            if omitted, no change. At init of the environment, y0 will be set to 0.

        x1 : float
            user x-coordinate of the lower right corner |n|
            if omitted, no change. At init of the environment, x1 will be set to 1024
            for CPython and the current screen width for Pythonista.

        background_color : colorspec
            color of the background |n|
            if omitted, no change. At init of the environment, this will be set to white.

        fps : float
            number of frames per second

        modelname : str
            name of model to be shown in upper left corner,
            along with text 'a salabim model' |n|
            if omitted, no change. At init of the environment, this will be set
            to the null string, which implies suppression of this feature.

        use_toplevel : bool
            if salabim animation is used in parallel with
            other modules using tkinter, it might be necessary to
            initialize the root with tkinter.TopLevel().
            In that case, set this parameter to True. |n|
            if False (default), the root will be initialized with tkinter.Tk()

        show_fps : bool
            if True, show the number of frames per second (default)  |n|
            if False, do not show the number of frames per second

        show_speed: bool
            if True, show the animation speed (default)  |n|
            if False, do not show the animation speed

        show_time: bool
            if True, show the time (default)  |n|
            if False, do not show the time

        video : str
            if video is not omitted, a mp4 format video with the name video
            will be created. |n|
            The video has to have a .mp4 etension |n|
            This requires installation of opencv (cv2) and numpy.

        Note
        ----
        The y-coordinate of the upper right corner is determined automatically
        in such a way that the x and scaling are the same. |n|

        Note that changing the parameters x0, x1, y0, width, height, background_color, modelname,
        use_toplevelmand video, animate has no effect on the current animation.
        So to avoid confusion, do not use change these parameters when an animation is running. |n|
        On the other hand, changing speed, show_fps, show_time, show_speed and fps can be useful in
        a running animation.
        '''
        if speed is not omitted:
            self.speed = speed
            if an_env == self:
                an_env.set_start_animation()

        if show_fps is not omitted:
            self.show_fps = show_fps
        if show_speed is not omitted:
            self.show_speed = show_speed
        if show_time is not omitted:
            self.show_time = show_time

        if animate is omitted:
            self.animate = True
        else:
            self.animate = animate
        if width is not omitted:
            self.width = width
        if height is not omitted:
            self.height = height
        if x0 is not omitted:
            self.x0 = x0
        if x1 is not omitted:
            self.x1 = x1
        if y0 is not omitted:
            self.y0 = y0
        if background_color is not omitted:
            self.background_color = background_color
        if fps is not omitted:
            self.fps = fps
        if modelname is not omitted:
            self.modelname = modelname
        if use_toplevel is not omitted:
            self.use_toplevel = use_toplevel
        if video is not omitted:
            self.video = video

    def peek(self):
        '''
        returns the time of the next component to become current |n|
        if there are no more events, peek will return inf |n|
        for advance use with animation / GUI event loops
        '''
        if len(self.env._pendingstandbylist) > 0:
            return self.env._now
        else:
            if self._event_list:
                return self._event_list[0][0]
            else:
                return inf

    def main(self):
        '''
        Returns
        -------
        the main component : Component
        '''
        return self._main

    def now(self):
        '''
        Returns
        -------
        the current simulation time : float
        '''
        return self._now

    def trace(self, value=omitted):
        '''
        trace status

        Parameters
        ----------
        value : bool
            new trace status |n|
            if omitted, no change

        Returns
        -------
        trace status : bool

        Note
        ----
        If you want to test the status, always include
        parentheses, like

            ``if env.trace():``
        '''
        if value is not omitted:
            self._trace = value
        return self._trace

    def current_component(self):
        '''
        Returns
        -------
        the current_component : Component
        '''
        return self._current_component

    def run(self, duration=omitted, till=omitted):
        '''
        start execution of the simulation

        Parameters
        ----------
        duration : float
            schedule with a delay of duration |n|
            if 0, now is used

        till : float
            schedule time |n|
            if omitted, inf is assumed

        Note
        ----
        only issue run() from the main level
        '''
        global an_env
        if till is omitted:
            if duration is omitted:
                scheduled_time = inf
            else:
                if duration == inf:
                    scheduled_time = inf
                else:
                    scheduled_time = self.env._now + duration
        else:
            if duration is omitted:
                scheduled_time = till
            else:
                raise SalabimError('both duration and till specified')

        self._main._reschedule(scheduled_time, False, 'run')

        if self.animate:
            if 'PIL' not in sys.modules:
                raise SalabimError('PIL is required for animation. Install with pip install Pillow.')
            if not (('tkinter' in sys.modules) or ('Tkinter' in sys.modules) or Pythonista):
                raise SalabimError('tkinter is required for animation.')
            if self.video == '':
                self.dovideo = False
            else:
                self.dovideo = True
                if Pythonista:
                    raise SalabimError(
                        'video production is not supported under Pythonista.')
                if platform.python_implementation == 'PyPy':
                    raise SalabimError(
                        'video production is not supported under PyPy.')
                if 'cv2' not in sys.modules:
                    raise SalabimError(
                        'cv2 required for video production. Install with pip install opencv-python.')
                if 'numpy' not in sys.modules:
                    raise SalabimError(
                        'numpy required for video production. Install with pip install numpy.')

            self.t = self._now  # for the call to set_start_animation
            self.set_start_animation()
            self.stopped = False
            self.running = True
            self.paused = False
            self.scale = self.width / (self.x1 - self.x0)
            an_env = self

            if Pythonista:
                try:
                    scene.run(MyScene(), frame_interval=60 / self.fps, show_fps=False)
                except:
                    pass
            else:
                if self.use_toplevel:
                    self.root = tkinter.Toplevel()
                else:
                    self.root = tkinter.Tk()
                self.canvas = tkinter.Canvas(
                    self.root, width=self.width, height=self.height)
                self.canvas.configure(background=colorspec_to_hex(
                    self.background_color, False))
                self.canvas.pack()
                self.canvas_objects = []

            for uio in self.ui_objects:
                if not Pythonista:
                    uio.install()

            self.system_an_objects = []
            self.system_ui_objects = []

            self.an_system_modelname()
            self.an_system_buttons()
            self.an_system_clocktext()

            if self.dovideo:
                self.video_sequence = 0
                fourcc = cv2.VideoWriter_fourcc(*'MP4V')
                self.out = cv2.VideoWriter(
                    self.video, fourcc, self.fps, (self.width, self.height))

            if Pythonista:
                while self.running:
                    pass
            else:
                self.root.after(0, self.simulate_and_animate_loop)
                self.root.mainloop()
                if self.dovideo:
                    self.out.release()
            if self.stopped:
                finish()
        else:
            self.simulate_loop()

    def simulate_loop(self):
        while True:
            self.step()
            if self._current_component == self._main:
                self.print_trace('{:10.3f}'.format(
                    self._now), self._main.name(), 'current')
                self._scheduled_time = inf
                self._status = current
                return

    def simulate_and_animate_loop(self):
        self.running = True

        while self.running:
            tick_start = time.time()

            if self.dovideo:
                self.t = self.start_animation_time + self.video_sequence * self.speed / self.fps
            else:
                if self.paused:
                    self.t = self.start_animation_time
                else:
                    self.t = self.start_animation_time +\
                        ((time.time() - self.start_animation_clocktime) *
                         self.speed)

            while self.peek() < self.t:
                self.step()
                if self._current_component == self._main:
                    self.print_trace('{:10.3f}'.format(self._now),
                        self._main.name(), 'current')
                    self._scheduled_time = inf
                    self._status = current
                    self.running = False
                    self.an_quit()
                    return
            if not self.running:
                break

            if self.dovideo:
                capture_image = Image.new(
                    'RGB', (self.width, self.height), colorspec_to_tuple(self.background_color))

            if not self.paused:
                self.frametimes.append(time.time())

            self.an_objects.sort(
                key=lambda obj: (-obj.layer(self.t), obj.sequence))

            canvas_objects_iter = iter(self.canvas_objects[:])
            co = next(canvas_objects_iter, None)
            self.animation_pre_tick(self.t)
            for ao in self.an_objects:
                ao.make_pil_image(self.t)
                if ao._image_visible:
                    if co is None:
                        ao.im = ImageTk.PhotoImage(ao._image)
                        co1 = self.canvas.create_image(
                            ao._image_x, self.height - ao._image_y, image=ao.im, anchor=tkinter.SW)
                        self.canvas_objects.append(co1)
                        ao.canvas_object = co1

                    else:
                        if ao.canvas_object == co:
                            if ao._image_ident != ao._image_ident_prev:
                                ao.im = ImageTk.PhotoImage(ao._image)
                                self.canvas.itemconfig(
                                    ao.canvas_object, image=ao.im)

                            if (ao._image_x != ao._image_x_prev) or (ao._image_y != ao._image_y_prev):
                                self.canvas.coords(
                                    ao.canvas_object, (ao._image_x, self.height - ao._image_y))

                        else:
                            ao.im = ImageTk.PhotoImage(ao._image)
                            ao.canvas_object = co
                            self.canvas.itemconfig(
                                ao.canvas_object, image=ao.im)
                            self.canvas.coords(
                                ao.canvas_object, (ao._image_x, self.height - ao._image_y))
                    co = next(canvas_objects_iter, None)

                    if self.dovideo:
                        capture_image.paste(ao._image,
                            (int(ao._image_x), int(self.height - ao._image_y - ao._image.size[1])),
                            ao._image)
                else:
                    ao.canvas_object = None

            self.animation_post_tick(self.t)

            for co in canvas_objects_iter:
                self.canvas.delete(co)
                self.canvas_objects.remove(co)

            for uio in self.ui_objects:
                if not uio.installed:
                    uio.install()

            for uio in self.ui_objects:
                if uio.type == 'button':
                    thistext = uio.text()
                    if thistext != uio.lasttext:
                        uio.lasttext = thistext
                        uio.button.config(text=thistext)

            if self.dovideo:
                open_cv_image = cv2.cvtColor(
                    np.array(capture_image), cv2.COLOR_RGB2BGR)
                self.out.write(open_cv_image)
                self.video_sequence += 1

            self.canvas.update()
            if not self.dovideo:
                tick_duration = time.time() - tick_start
                if tick_duration < 1 / self.fps:
                    time.sleep(((1 / self.fps) - tick_duration) * 0.8)  # 0.8 compensation because of clock inaccuracy

    def an_system_modelname(self):
        '''
        function to show the modelname |n|
        called by run(), if animation is True. |n|
        may be overridden to change the standard behaviour.
        '''
        if self.modelname != '':
            ao = Animate(text=self.modelname,
                         x0=8, y0=self.height - 60,
                         anchor='w', fontsize0=30, textcolor0='black',
                         screen_coordinates=True, env=self)
            self.system_an_objects.append(ao)
            ao = Animate(text='a salabim model',
                         x0=8, y0=self.height - 78,
                         anchor='w', fontsize0=16, textcolor0='red',
                         screen_coordinates=True, env=self)
            self.system_an_objects.append(ao)

    def an_system_buttons(self):
        '''
        function to initialize the system animation buttons |n|
        called by run(), if animation is True. |n|
        may be overridden to change the standard behaviour.
        '''
        uio = AnimateButton(x=48, y=self.height - 21, text='Stop',
                            action=self.env.an_stop, env=self)
        self.system_ui_objects.append(uio)
        uio = AnimateButton(x=48 + 1 * 90, y=self.height - 21, text='Anim/2',
                            action=self.env.an_half, env=self)
        self.system_ui_objects.append(uio)
        uio = AnimateButton(x=48 + 2 * 90, y=self.height - 21, text='Anim*2',
                            action=self.env.an_double, env=self)
        self.system_ui_objects.append(uio)
        uio = AnimateButton(x=48 + 3 * 90, y=self.height - 21, text='',
                            action=self.env.an_pause, env=self)
        self.system_ui_objects.append(uio)
        uio.text = lambda: pausetext()
        uio = AnimateButton(x=48 + 4 * 90, y=self.height - 21, text='',
                            action=self.env.an_trace, env=self)
        self.system_ui_objects.append(uio)
        uio.text = tracetext

    def an_system_clocktext(self):
        '''
        function to initialize the system clocktext |n|
        called by run(), if animation is True. |n|
        may be overridden to change the standard behaviour.
        '''
        ao = Animate(x0=self.width, y0=self.height - 5, fillcolor0='black',
                     text='', fontsize0=15, font='narrow', anchor='ne',
                     screen_coordinates=True, env=self)
        self.system_an_objects.append(ao)
        ao.text = clocktext

    def an_quit(self):
        global an_env
        self.running = False

        for ao in self.system_an_objects:
            ao.remove()
        for uio in self.system_ui_objects:
            uio.remove()

        for uio in self.ui_objects:
            if uio.type == 'slider':
                uio._v = uio.v
            uio.installed = False

        if not Pythonista:
            self.root.destroy()
        an_env = None

    def an_half(self):
        if self.paused:
            self.paused = False
        else:
            self.speed /= 2
            self.set_start_animation()

    def an_double(self):
        if self.paused:
            self.paused = False
        else:
            self.speed *= 2
            self.set_start_animation()

    def an_pause(self):
        self.paused = not self.paused
        self.set_start_animation()

    def an_stop(self):
        self.an_quit()
        self.stopped = True

    def an_trace(self):
        self._trace = not self._trace

    def set_start_animation(self):
        self.frametimes = collections.deque(maxlen=30)
        self.start_animation_time = self.t
        self.start_animation_clocktime = time.time()

    def getwidth(self, text, font='', fontsize=20, screen_coordinates=False):
        if not screen_coordinates:
            fontsize = fontsize * self.scale
        f = self.getfont(font, fontsize)
        if text == '':  # necessary because of bug in PIL >= 4.2.1
            thiswidth, thisheight = (0, 0)
        else:
            thiswidth, thisheight = f.getsize(text)
        if screen_coordinates:
            return thiswidth
        else:
            return thiswidth / self.scale

    def getfontsize_to_fit(self, text, width, font='', screen_coordinates=False):
        if not screen_coordinates:
            width = width * self.scale

        lastwidth = 0
        for fontsize in range(1, 300):
            f = self.getfont(font, fontsize)
            thiswidth, thisheight = f.getsize(text)
            if thiswidth > width:
                break
            lastwidth = thiswidth
        fontsize = interpolate(
            width, lastwidth, thiswidth, fontsize - 1, fontsize)
        if screen_coordinates:
            return fontsize
        else:
            return fontsize / self.scale

    def name(self, txt=omitted):
        '''
        Parameters
        ----------
        txt : str
            name of the environment |n|
            if txt ends with a period, the name will be serialized |n|
            if omittted, no change

        Returns
        -------
        Name of the environment : str
        '''

        if txt is not omitted:
            _set_name(txt, Environment._nameserialize, self)
        return _decode_name(self._name)

    def base_name(self):
        '''
        returns the base name of the environment (the name used at init or name)
        '''
        return self._base_namee

    def sequence_number(self):
        '''
        returns the sequence_number of the environment
        (the sequence number at init or name) |n|
        normally this will be the integer value of a serialized name,
        but also non serialized names (without a dot at the end)
        will be numbered)
        '''
        return self._sequence_number

    def print_trace(self, s1='', s2='', s3='', s4=''):
        '''
        prints a trace line

        Parameters
        ----------
        s1 : str
            part 1 (usually formatted  now), padded to 10 characters

        s2 : str
            part 2 (usually formatted  now), padded to 20 characters

        s3 : str
            part 3 (usually formatted  now), padded to 35 characters

        s4 : str
            part 4 (usually formatted  now)

        Note
        ----
        if the current component's suppress_trace is True, nothing is printed
        '''
        if self._trace:
            if hasattr(self, '_current_component'):
                if not self._current_component._suppress_trace:
                    print(pad(s1, 10) + ' ' + pad(s2, 20) + ' ' +
                          pad(s3, max(len(s3), 36)) + ' ' + s4.strip())


class Animate(object):
    '''
    defines an animation object

    Parameters
    ----------
    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically upon termination of the parent

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

    t0 : float
        time of start of the animation (default: now)

    x0 : float
        x-coordinate of the origin (default 0) at time t0

    y0 : float
        y-coordinate of the origin (default 0) at time t0

    offsetx0 : float
        offsets the x-coordinate of the object (default 0) at time t0

    offsety0 : float
        offsets the y-coordinate of the object (default 0) at time t0

    circle0 : tuple
         the circle at time t0 specified as a tuple (radius,)

    line0 : tuple
        the line(s) at time t0 (xa,ya,xb,yb,xc,yc, ...)

    polygon0 : tuple
        the polygon at time t0 (xa,ya,xb,yb,xc,yc, ...) |n|
        the last point will be auto connected to the start

    rectangle0 : tuple
        the rectangle at time t0 |n|
        (xlowerleft,ylowerlef,xupperright,yupperright)

    image : str or PIL image
        the image to be displayed |n|
        This may be either a filename or a PIL image

    text : str
        the text to be displayed

    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial

    anchor : str
        anchor position |n|
        specifies where to put images or texts relative to the anchor
        point |n|
        possible values are (default: center) |n|:
        ``nw    n    ne`` |n|
        ``w   center  e`` |n|
        ``sw    s    se``

    linewidth0 : float
        linewidth of the contour at time t0 (default 0 = no contour)

    fillcolor0 : colorspec
        color of interior at time t0 (default black)

    linecolor0 : colorspec
        color of the contour at time t0 (default black)

    textcolor0 : colorspec
        color of the text at time 0 (default black)

    angle0 : float
        angle of the polygon at time t0 (in degrees) (default 0)

    fontsize0 : float
        fontsize of text at time t0 (default: 20)

    width0 : float
       width of the image to be displayed at time t0 (default: no scaling)

    t1 : float
        time of end of the animation (default: inf) |n|
        if keep=True, the animation will continue (frozen) after t1

    x1 : float
        x-coordinate of the origin (default x0) at time t1

    y1 : float
        y-coordinate of the origin (default y0) at time t1

    offsetx1 : float
        offsets the x-coordinate of the object (default offsetx0) at time t1

    offsety1 : float
        offsets the y-coordinate of the object (default offsety0) at time t1

    circl10 : tuple
         the circle at time t1 specified as a tuple (radius,)

    line1 : tuple
        the line(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: line0) |n|
        should have the same length as line0

    polygon1 : tuple
        the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: polygon0) |n|
        should have the same length as polygon0

    rectangle1 : tuple
        the rectangle at time t1 (default: rectangle0) |n|
        (xlowerleft,ylowerlef,xupperright,yupperright)

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

    fontsize1 : float
        fontsize of text at time t1 (default: fontsize0)

    width1 : float
       width of the image to be displayed at time t1 (default: width0) |n|

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

    colornames may contain an additional alpha, like ``red#7f``
    hexnames may be either 3 of 4 bytes long (RGB or RGBA)
    both colornames and hexnames may be given as a tuple with an
    additional alpha between 0 and 255,
    e.g. ``(255,0,255,128)``, ('red',127)`` or ``('#ff00ff',128)``

    Permitted parameters

    ======================  ========= ========= ========= ========= ========= =========
    parameter               circle    image     line      polygon   rectangle text
    ======================  ========= ========= ========= ========= ========= =========
    parent                  -         -         -         -         -         -
    layer                   -         -         -         -         -         -
    keep                    -         -         -         -         -         -
    scree_coordinates       -         -         -         -         -         -
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
    font
    anchor                            -                                       -
    linewidth0,linewidth1    -                  -         -         -
    fillcolor0,fillcolor1    -                            -         -
    linecolor0,linecolor1    -                  -         -         -
    textcolor0,textcolor1.                                                    -
    angle0,angle1                     -         -         -         -         -
    font                                                                      -
    fontsize0,fontsize1                                                       -
    width0,width1                     -
    ======================  ========= ========= ========= ========= ========= =========
    '''

    def __init__(self, parent=omitted, layer=0, keep=True, visible=True,
                 screen_coordinates=False,
                 t0=omitted, x0=0, y0=0, offsetx0=0, offsety0=0,
                 circle0=omitted, line0=omitted, polygon0=omitted, rectangle0=omitted,
                 image=omitted, text=omitted,
                 font='', anchor='center',
                 linewidth0=1, fillcolor0='black', linecolor0='black', textcolor0='black',
                 angle0=0, fontsize0=20, width0=omitted,
                 t1=omitted, x1=omitted, y1=omitted, offsetx1=omitted, offsety1=omitted,
                 circle1=omitted, line1=omitted, polygon1=omitted, rectangle1=omitted,
                 linewidth1=omitted, fillcolor1=omitted, linecolor1=omitted, textcolor1=omitted,
                 angle1=omitted, fontsize1=omitted, width1=omitted, env=omitted):

        self.env = _default_env if env is omitted else env
        self._image_ident = None  # denotes no image yet
        self._image = None
        self._image_x = 0
        self._image_y = 0
        self.canvas_object = None

        self.type = self.settype(
            circle0, line0, polygon0, rectangle0, image, text)
        if self.type == '':
            raise SalabimError('no object specified')
        type1 = self.settype(circle1, line1, polygon1, rectangle1, omitted, omitted)
        if (type1 != '') and (type1 != self.type):
            raise SalabimError('incompatible types: ' +
                self.type + ' and ' + type1)

        self.layer0 = layer
        self.parent = (None if parent is omitted else parent)
        self.keep = keep
        self.visible0 = visible
        self.screen_coordinates = screen_coordinates
        self.sequence = self.env.serialize()

        self.circle0 = circle0
        self.line0 = line0
        self.polygon0 = polygon0
        self.rectangle0 = rectangle0
        self.text0 = text

        if image is omitted:
            self.width0 = 0  # just to be able to interpolate
        else:
            self.image0 = spec_to_image(image)
            self.image_serial0 = self.env.serialize()
            self.width0 = self.image0.size[0] if width0 is omitted else width0

        self.font0 = font
        self.anchor0 = anchor

        self.x0 = x0
        self.y0 = y0
        self.offsetx0 = offsetx0
        self.offsety0 = offsety0

        self.fillcolor0 = fillcolor0
        self.linecolor0 = linecolor0
        self.textcolor0 = textcolor0
        self.linewidth0 = linewidth0
        self.angle0 = angle0
        self.fontsize0 = fontsize0

        self.t0 = self.env._now if t0 is omitted else t0

        self.circle1 = self.circle0 if circle1 is omitted else circle1
        self.line1 = self.line0 if line1 is omitted else line1
        self.polygon1 = self.polygon0 if polygon1 is omitted else polygon1
        self.rectangle1 = self.rectangle0 if rectangle1 is omitted else rectangle1

        self.x1 = self.x0 if x1 is omitted else x1
        self.y1 = self.y0 if y1 is omitted else y1
        self.offsetx1 = self.offsetx0 if offsetx1 is omitted else offsetx1
        self.offsety1 = self.offsety0 if offsety1 is omitted else offsety1
        self.fillcolor1 =\
            self.fillcolor0 if fillcolor1 is omitted else fillcolor1
        self.linecolor1 =\
            self.linecolor0 if linecolor1 is omitted else linecolor1
        self.textcolor1 =\
            self.textcolor0 if textcolor1 is omitted else textcolor1
        self.linewidth1 =\
            self.linewidth0 if linewidth1 is omitted else linewidth1
        self.angle1 = self.angle0 if angle1 is omitted else angle1
        self.fontsize1 =\
            self.fontsize0 if fontsize1 is omitted else fontsize1
        self.width1 = self.width0 if width1 is omitted else width1

        self.t1 = inf if t1 is omitted else t1

        self.env.an_objects.append(self)

    def update(self, layer=omitted, keep=omitted, visible=omitted,
               t0=omitted, x0=omitted, y0=omitted, offsetx0=omitted, offsety0=omitted,
               circle0=omitted, line0=omitted, polygon0=omitted, rectangle0=omitted,
               image=omitted, text=omitted, font=omitted, anchor=omitted,
               linewidth0=omitted, fillcolor0=omitted, linecolor0=omitted, textcolor0=omitted,
               angle0=omitted, fontsize0=omitted, width0=omitted,
               t1=omitted, x1=omitted, y1=omitted, offsetx1=omitted, offsety1=omitted,
               circle1=omitted, line1=omitted, polygon1=omitted, rectangle1=omitted,
               linewidth1=omitted, fillcolor1=omitted, linecolor1=omitted, textcolor1=omitted,
               angle1=omitted, fontsize1=omitted, width1=omitted):
        '''
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

        t0 : float
            time of start of the animation (default: now)

        x0 : float
            x-coordinate of the origin (default see below) at time t0

        y0 : float
            y-coordinate of the origin (default see below) at time t0

        offsetx0 : float
            offsets the x-coordinate of the object (default see below) at time t0

        offsety0 : float
            offsets the y-coordinate of the object (default see below) at time t0

        circle0 : tuple
            the circle at time t0 specified as a tuple (radius,) (default see below)

        line0 : tuple
            the line(s) at time t0 (xa,ya,xb,yb,xc,yc, ...) (default see below)

        polygon0 : tuple
            the polygon at time t0 (xa,ya,xb,yb,xc,yc, ...) |n|
            the last point will be auto connected to the start (default see below)

        rectangle0 : tuple
            the rectangle at time t0 |n|
            (xlowerleft,ylowerlef,xupperright,yupperright) (default see below)

        image : str or PIL image
            the image to be displayed |n|
            This may be either a filename or a PIL image (default see below)

        text : str
            the text to be displayed (default see below)

        font : str or list/tuple
            font to be used for texts |n|
            Either a string or a list/tuple of fontnames. (default see below)
            If not found, uses calibri or arial

        anchor : str
            anchor position |n|
            specifies where to put images or texts relative to the anchor
            point (default see below) |n|
            possible values are (default: center) |n|:
            ``nw    n    ne`` |n|
            ``w   center  e`` |n|
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
            width of the image to be displayed at time t0 (default see below)

        t1 : float
            time of end of the animation (default: inf) |n|
            if keep=True, the animation will continue (frozen) after t1

        x1 : float
            x-coordinate of the origin (default x0) at time t1

        y1 : float
            y-coordinate of the origin (default y0) at time t1

        offsetx1 : float
            offsets the x-coordinate of the object (default offsetx0) at time t1

        offsety1 : float
            offsets the y-coordinate of the object (default offsety0) at time t1

        circle1: tuple
             the circle at time t1 specified as a tuple (radius,)

        line1 : tuple
            the line(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: line0) |n|
            should have the same length as line0

        polygon1 : tuple
            the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: polygon0) |n|
            should have the same length as polygon0

        rectangle1 : tuple
            the rectangle at time t1 (default: rectangle0) |n|
            (xlowerleft,ylowerlef,xupperright,yupperright)

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
        '''

        t = self.env._now
        type0 = self.settype(circle0, line0, polygon0, rectangle0, image, text)
        if (type0 != '') and (type0 != self.type):
            raise SalabimError('incorrect type ' +
                type0 + ' (should be ' + self.type)
        type1 = self.settype(circle1, line1, polygon1, rectangle1, omitted, omitted)
        if (type1 != '') and (type1 != self.type):
            raise SalabimError('incompatible types: ' +
                self.type + ' and ' + type1)

        if layer is not omitted:
            self.layer0 = layer
        if keep is not omitted:
            self.keep = keep
        if visible is not omitted:
            self.visible0 = visible
        self.circle0 = self.circle() if circle0 is omitted else circle0
        self.line0 = self.line() if line0 is omitted else line0
        self.polygon0 = self.polygon() if polygon0 is omitted else polygon0
        self.rectangle0 =\
            self.rectangle() if rectangle0 is omitted else rectangle0
        if text is not omitted:
            self.text0 = text
        self.width0 = self.width() if width0 is omitted else width0
        if image is not omitted:
            self.image0 = spec_to_image(image)
            self.image_serial0 = self.env.serialize()
            self.width0 = self.image0.size[0] if width0 is omitted else width0

        if font is not omitted:
            self.font0 = font
        if anchor is not omitted:
            self.anchor0 = anchor

        self.x0 = self.x(t) if x0 is omitted else x0
        self.y0 = self.y(t) if y0 is omitted else y0
        self.offsetx0 = self.offsetx(t) if offsetx0 is omitted else offsetx0
        self.offsety0 = self.offsety(t) if offsety0 is omitted else offsety0

        self.fillcolor0 =\
            self.fillcolor(t) if fillcolor0 is omitted else fillcolor0
        self.linecolor0 = self.linecolor(
            t) if linecolor0 is omitted else linecolor0
        self.linewidth0 = self.linewidth(t) if linewidth0 is omitted else\
            linewidth0
        self.textcolor0 =\
            self.textcolor(t) if textcolor0 is omitted else textcolor0
        self.angle0 = self.angle(t) if angle0 is omitted else angle0
        self.fontsize0 = self.fontsize(t) if fontsize0 is omitted else fontsize0
        self.t0 = self.env._now if t0 is omitted else t0

        self.circle1 = self.circle0 if circle1 is omitted else circle1
        self.line1 = self.line0 if line1 is omitted else line1
        self.polygon1 = self.polygon0 if polygon1 is omitted else polygon1
        self.rectangle1 =\
            self.rectangle0 if rectangle1 is omitted else rectangle1

        self.x1 = self.x0 if x1 is omitted else x1
        self.y1 = self.y0 if y1 is omitted else y1
        self.offsetx1 = self.offsetx0 if offsetx1 is omitted else offsetx1
        self.offsety1 = self.offsety0 if offsety1 is omitted else offsety1
        self.fillcolor1 =\
            self.fillcolor0 if fillcolor1 is omitted else fillcolor1
        self.linecolor1 =\
            self.linecolor0 if linecolor1 is omitted else linecolor1
        self.textcolor1 =\
            self.textcolor0 if textcolor1 is omitted else textcolor1
        self.linewidth1 =\
            self.linewidth0 if linewidth1 is omitted else linewidth1
        self.angle1 = self.angle0 if angle1 is omitted else angle1
        self.fontsize1 =\
            self.fontsize0 if fontsize1 is omitted else fontsize1
        self.width1 = self.width0 if width1 is omitted else width1

        self.t1 = inf if t1 is omitted else t1
        if self not in self.env.an_objects:
            self.env.an_objects.append(self)

    def remove(self):
        '''
        removes the animation object from the animation queue,
        so effectively ending this animation.

        Note
        ----
        The animation object might be still updated, if required
        '''
        if self in self.env.an_objects:
            self.env.an_objects.remove(self)

    def x(self, t=omitted):
        '''
        x-position of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        x : float
            default behaviour: linear interpolation between self.x0 and self.x1

        '''
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.x0, self.x1)

    def y(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.y0, self.y1)

    def offsetx(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.offsetx0, self.offsetx1)

    def offsety(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.offsety0, self.offsety1)

    def angle(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.angle0, self.angle1)

    def linewidth(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.linewidth0, self.linewidth1)

    def linecolor(self, t=omitted):
        return colorinterpolate((self.env._now if t is omitted else t),
                                self.t0, self.t1, self.linecolor0, self.linecolor1)

    def fillcolor(self, t=omitted):
        return colorinterpolate((self.env._now if t is omitted else t),
                                self.t0, self.t1, self.fillcolor0, self.fillcolor1)

    def circle(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.circle0, self.circle1)

    def textcolor(self, t=omitted):
        return colorinterpolate((self.env._now if t is omitted else t),
                                self.t0, self.t1, self.textcolor0, self.textcolor1)

    def line(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.line0, self.line1)

    def polygon(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.polygon0, self.polygon1)

    def rectangle(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.rectangle0, self.rectangle1)

    def width(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.width0, self.width1)

    def fontsize(self, t=omitted):
        return interpolate((self.env._now if t is omitted else t),
                           self.t0, self.t1, self.fontsize0, self.fontsize1)

    def text(self, t=omitted):
        return self.text0

    def anchor(self, t=omitted):
        return self.anchor0

    def layer(self, t=omitted):
        return self.layer0

    def font(self, t=omitted):
        return self.font0

    def visible(self, t=omitted):
        return self.visible0

    def image(self, t=omitted):
        '''
        returns image and a serial number at time t
        use the function spec_to_image to change the image here |n|
        if there's a change in the image, a new serial number should be returned
        if there's no change, do not update the serial number
        '''
        return self.image0, self.image_serial0

    def settype(self, circle, line, polygon, rectangle, image, text):
        n = 0
        t = ''
        if circle is not omitted:
            t = 'circle'
            n += 1
        if line is not omitted:
            t = 'line'
            n += 1
        if polygon is not omitted:
            t = 'polygon'
            n += 1
        if rectangle is not omitted:
            t = 'rectangle'
            n += 1
        if image is not omitted:
            t = 'image'
            n += 1
        if text is not omitted:
            t = 'text'
            n += 1
        if n >= 2:
            raise SalabimError('more than one object given')
        return t

    def make_pil_image(self, t):

        visible = self.visible(t)

        if (t >= self.t0) and ((t <= self.t1) or self.keep) and visible:
            self._image_visible = True
            self._image_x_prev = self._image_x
            self._image_y_prev = self._image_y
            self._image_ident_prev = self._image_ident

            x = self.x(t)
            y = self.y(t)
            offsetx = self.offsetx(t)
            offsety = self.offsety(t)
            angle = self.angle(t)

            if (self.type == 'polygon') or (self.type == 'rectangle') or (self.type == 'line'):
                linewidth = self.linewidth(t) * self.env.scale
                linecolor = colorspec_to_tuple(self.linecolor(t))
                fillcolor = colorspec_to_tuple(self.fillcolor(t))

                cosa = math.cos(angle * math.pi / 180)
                sina = math.sin(angle * math.pi / 180)

                if self.type == 'rectangle':
                    rectangle = self.rectangle(t)
                    p = [
                        rectangle[0], rectangle[1],
                        rectangle[2], rectangle[1],
                        rectangle[2], rectangle[3],
                        rectangle[0], rectangle[3],
                        rectangle[0], rectangle[1]]

                elif self.type == 'line':
                    p = self.line(t)
                    fillcolor = (0, 0, 0, 0)

                else:
                    p = self.polygon(t)

                if self.screen_coordinates:
                    qx = x
                    qy = y
                else:
                    qx = (x - self.env.x0) * self.env.scale
                    qy = (y - self.env.y0) * self.env.scale

                r = []
                minrx = inf
                minry = inf
                maxrx = -inf
                maxry = -inf
                for i in range(0, len(p), 2):
                    px = p[i]
                    py = p[i + 1]
                    rx = px * cosa - py * sina
                    ry = px * sina + py * cosa
                    if not self.screen_coordinates:
                        rx = rx * self.env.scale
                        ry = ry * self.env.scale
                    minrx = min(minrx, rx)
                    maxrx = max(maxrx, rx)
                    minry = min(minry, ry)
                    maxry = max(maxry, ry)
                    r.append(rx)
                    r.append(ry)
                if self.type == 'polygon':
                    if (r[0] != r[len(r) - 2]) or (r[1] != r[len(r) - 1]):
                        r.append(r[0])
                        r.append(r[1])

                rscaled = []
                for i in range(0, len(r), 2):
                    rscaled.append(r[i] - minrx + linewidth)
                    rscaled.append(maxry - r[i + 1] + linewidth)
                rscaled = tuple(rscaled)  # to make it hashable

                self._image_ident = (rscaled, minrx, maxrx, minry, maxry,
                                     fillcolor, linecolor, linewidth)
                if self._image_ident != self._image_ident_prev:
                    self._image = Image.new('RGBA', (int(maxrx - minrx + 2 * linewidth),
                                                     int(maxry - minry + 2 * linewidth)), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(self._image)
                    if fillcolor[3] != 0:
                        draw.polygon(rscaled, fill=fillcolor)
                    if (linewidth > 0) and (linecolor[3] != 0):
                        draw.line(rscaled, fill=linecolor,
                                  width=int(linewidth))

                self._image_x = qx + minrx - linewidth + \
                    (offsetx * cosa - offsety * sina)
                self._image_y = qy + minry - linewidth + \
                    (offsetx * sina + offsety * cosa)

            elif self.type == 'circle':
                linewidth = self.linewidth(t) * self.env.scale
                fillcolor = colorspec_to_tuple(self.fillcolor(t))
                linecolor = colorspec_to_tuple(self.linecolor(t))
                circle = self.circle(t)
                radius = circle[0]

                if self.screen_coordinates:
                    qx = x
                    qy = y
                else:
                    qx = (x - self.env.x0) * self.env.scale
                    qy = (y - self.env.y0) * self.env.scale
                    linewidth *= self.env.scale
                    radius *= self.env.scale

                self._image_ident = (radius, linewidth, linecolor, fillcolor)
                if self._image_ident != self._image_ident_prev:
                    nsteps = int(math.sqrt(radius) * 6)
                    tangle = 2 * math.pi / nsteps
                    sint = math.sin(tangle)
                    cost = math.cos(tangle)
                    p = []
                    x = radius
                    y = 0

                    for i in range(nsteps + 1):
                        x, y = (x * cost - y * sint, x * sint + y * cost)
                        p.append(x + radius + linewidth)
                        p.append(y + radius + linewidth)

                    self._image = Image.new('RGBA', (int(radius * 2 + 2 * linewidth),
                                                     int(radius * 2 + 2 * linewidth)), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(self._image)
                    if fillcolor[3] != 0:
                        draw.polygon(p, fill=fillcolor)
                    if (linewidth > 0) and (linecolor[3] != 0):
                        draw.line(p, fill=linecolor, width=int(linewidth))

                dx = offsetx
                dy = offsety
                cosa = math.cos(angle * math.pi / 180)
                sina = math.sin(angle * math.pi / 180)
                ex = dx * cosa - dy * sina
                ey = dx * sina + dy * cosa
                self._image_x = qx + ex - radius - linewidth - 1
                self._image_y = qy + ey - radius - linewidth - 1

            elif self.type == 'image':
                image, image_serial = self.image(t)
                width = self.width(t)
                height = width * image.size[1] / image.size[0]
                angle = self.angle(t)

                anchor = self.anchor(t)
                if self.screen_coordinates:
                    qx = x
                    qy = y
                else:
                    qx = (x - self.env.x0) * self.env.scale
                    qy = (y - self.env.y0) * self.env.scale
                    offsetx = offsetx * self.env.scale
                    offsety = offsety * self.env.scale

                self._image_ident = (image_serial, width, height, angle)
                if self._image_ident != self._image_ident_prev:
                    if not self.screen_coordinates:
                        width *= self.env.scale
                        height *= self.env.scale
                    im1 = image.resize(
                        (int(width), int(height)), Image.ANTIALIAS)
                    self.imwidth, self.imheight = im1.size

                    self._image = im1.rotate(angle, expand=1)

                anchor_to_dis = {
                    'ne': (-0.5, -0.5),
                    'n': (0, -0.5),
                    'nw': (0.5, -0.5),
                    'e': (-0.5, 0),
                    'center': (0, 0),
                    'w': (0.5, 0),
                    'se': (-0.5, 0.5),
                    's': (0, 0.5),
                    'sw': (0.5, 0.5)}
                dx, dy = anchor_to_dis[anchor.lower()]
                dx = dx * self.imwidth + offsetx
                dy = dy * self.imheight + offsety
                cosa = math.cos(angle * math.pi / 180)
                sina = math.sin(angle * math.pi / 180)
                ex = dx * cosa - dy * sina
                ey = dx * sina + dy * cosa
                imrwidth, imrheight = self._image.size

                self._image_x = qx + ex - imrwidth / 2
                self._image_y = qy + ey - imrheight / 2

            elif self.type == 'text':
                textcolor = colorspec_to_tuple(self.textcolor(t))
                fontsize = self.fontsize(t)
                angle = self.angle(t)
                anchor = self.anchor(t)
                fontname = self.font(t)

                text = self.text(t)
                if self.screen_coordinates:
                    qx = x
                    qy = y
                else:
                    qx = (x - self.env.x0) * self.env.scale
                    qy = (y - self.env.y0) * self.env.scale
                    fontsize = fontsize * self.env.scale
                    offsetx = offsetx * self.env.scale
                    offsety = offsety * self.env.scale

                self._image_ident = (
                    text, fontname, fontsize, angle, textcolor)
                if self._image_ident != self._image_ident_prev:
                    font = getfont(fontname, fontsize)
                    if text == '':  # this code is a workarond for a bug in PIL >= 4.2.1
                        im = Image.new(
                            'RGBA', (0, 0), (0, 0, 0, 0))
                    else:
                        width, height = font.getsize(text)
                        im = Image.new(
                            'RGBA', (int(width), int(height)), (0, 0, 0, 0))
                        imwidth, imheight = im.size
                        draw = ImageDraw.Draw(im)
                        draw.text(xy=(0, 0), text=text, font=font, fill=textcolor)
                        # this code is to correct a bug in the rendering of text,
                        # leaving a kind of shadow around the text
                        textcolor3 = textcolor[0:3]
                        if textcolor3 != (0, 0, 0):  # black is ok
                            for y in range(imheight):
                                for x in range(imwidth):
                                    c = im.getpixel((x, y))
                                    if not c[0:3] in (textcolor3, (0, 0, 0)):
                                        im.putpixel((x, y), (textcolor3[0], textcolor3[1], textcolor3[2], c[3]))
                        # end of code to correct bug

                    self.imwidth, self.imheight = im.size

                    self._image = im.rotate(angle, expand=1)

                anchor_to_dis = {
                    'ne': (-0.5, -0.5),
                    'n': (0, -0.5),
                    'nw': (0.5, -0.5),
                    'e': (-0.5, 0),
                    'center': (0, 0),
                    'w': (0.5, 0),
                    'se': (-0.5, 0.5),
                    's': (0, 0.5),
                    'sw': (0.5, 0.5)}

                dx, dy = anchor_to_dis[anchor.lower()]
                dx = dx * self.imwidth + offsetx
                dy = dy * self.imheight + offsety
                cosa = math.cos(angle * math.pi / 180)
                sina = math.sin(angle * math.pi / 180)
                ex = dx * cosa - dy * sina
                ey = dx * sina + dy * cosa
                imrwidth, imrheight = self._image.size
                self._image_x = qx + ex - imrwidth / 2
                self._image_y = qy + ey - imrheight / 2
            else:
                self._image_visible = False  # should never occur

        else:
            self._image_visible = False

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


class AnimateButton(object):
    '''
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
        color of the interior (default 40%gray)

    linecolor : colorspec
        color of contour (default black)

    color : colorspec
        color of the text (default white)

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

    Note
    ----
    On CPython/PyPy platforms, the tkinter functionality is used.
    On Pythonista, this is emulated by salabim
    '''

    def __init__(self, x=0, y=0, width=80, height=30,
                 linewidth=0, fillcolor='40%gray',
                 linecolor='black', color='white', text='', font='',
                 fontsize=15, action=None, env=omitted):

        self.env = _default_env if env is omitted else env
        self.type = 'button'
        self.t0 = -inf
        self.t1 = inf
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.sequence = self.env.serialize()
        self.x = x - width / 2
        self.y = y - height / 2
        self.width = width
        self.height = height
        self.fillcolor = colorspec_to_tuple(fillcolor)
        self.linecolor = colorspec_to_tuple(linecolor)
        self.color = colorspec_to_tuple(color)
        self.linewidth = linewidth
        self.font = font
        self.fontsize = fontsize
        self.text0 = text
        self.lasttext = '*'
        self.action = action

        self.env.ui_objects.append(self)
        self.installed = False

    def text(self):
        return self.text0

    def install(self):
        self.button = tkinter.Button(
            self.env.root, text=self.lasttext, command=self.action, anchor=tkinter.CENTER)
        self.button.configure(
            width=int(2.2 * self.width / self.fontsize),
            foreground=colorspec_to_hex(self.color, False),
            background=colorspec_to_hex(self.fillcolor, False),
            relief=tkinter.FLAT)
        self.button_window = self.env.canvas.create_window(
            self.x + self.width, self.env.height - self.y - self.height,
            anchor=tkinter.NE, window=self.button)
        self.installed = True

    def remove(self):
        '''
        removes the button object. |n|
        the ui object is removed from the ui queue,
        so effectively ending this ui
        '''
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if not Pythonista:
            self.button.destroy()


class AnimateSlider(object):
    '''
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

    linewidth : float
        width of contour in screen coordinate (default 0 = no contour)

    fillcolor : colorspec
        color of the interior (default 40%gray)

    linecolor : colorspec
        color of contour (default black)

    labelcolor : colorspec
        color of the label (default black)

    label : str
        label if the slider (default null string) |n|
        if label is an argumentless function, this function
        will be used to display as label, otherwise the
        label plus the current value of the slider will be shown

    font : str
         font of the text (default Helvetica)

    fontsize : int
         fontsize of the text (default 12)

    action : function
         function executed when the slider value is changed (default None) |n|
         the function should one arguments, being the new value |n|
         if None (default), no action

    Note
    ----
    The current value of the slider is the v attibute of the slider. |n|
    On CPython/PyPy platforms, the tkinter functionality is used. |n|
    On Pythonista, this is emulated by salabim
    '''

    def __init__(self, layer=0, x=0, y=0, width=100, height=20,
                 vmin=0, vmax=10, v=omitted, resolution=1,
                 linecolor='black', labelcolor='black', label='',
                 font='', fontsize=12, action=None, env=omitted):

        self.env = _default_env if env is omitted else env
        n = round((vmax - vmin) / resolution) + 1
        self.vmin = vmin
        self.vmax = vmin + (n - 1) * resolution
        self._v = vmin if v is omitted else v
        self.xdelta = width / n
        self.resolution = resolution

        self.type = 'slider'
        self.t0 = -inf
        self.t1 = inf
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.sequence = self.env.serialize()
        self.x = x - width / 2
        self.y = y - height / 2
        self.width = width
        self.height = height
        self.linecolor = colorspec_to_tuple(linecolor)
        self.labelcolor = colorspec_to_tuple(labelcolor)
        self.font = font
        self.fontsize = fontsize
        self.label = label
        self.action = action
        self.installed = False

        if Pythonista:
            self.y = self.y - height * 1.5

        self.env.ui_objects.append(self)

    def v(self, value=omitted):
        '''
        value |n|

        Parameters
        ----------
        value: float
            new value |n|
            if omitted, no change

        Returns
        -------
        Current value of the slider : float
        '''
        if value is not omitted:
            if Pythonista:
                self._v = value
            else:
                if an_env == self.env:
                    self.slider.set(value)
                else:
                    self._v = value

        if Pythonista:
            return self._v
        else:
            if an_env == self.env:
                return self.slider.get()
            else:
                return self._v

    def install(self):
        self.slider = tkinter.Scale(
            self.env.root,
            from_=self.vmin, to=self.vmax,
            orient=tkinter.HORIZONTAL,
            label=self.label,
            resolution=self.resolution,
            command=self.action)
        self.slider.window = self.env.canvas.create_window(
            self.x, self.env.height - self.y,
            anchor=tkinter.NW, window=self.slider)
        self.slider.config(
            font=(self.font, int(self.fontsize * 0.8)),
            background=colorspec_to_hex(self.env.background_color, False),
            highlightbackground=colorspec_to_hex(self.env.background_color, False))
        self.slider.set(self._v)
        self.installed = True

    def remove(self):
        '''
        removes the slider object |n|
        The ui object is removed from the ui queue,
        so effectively ending this ui
        '''
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if not Pythonista:
            self.slider.destroy()


class Component(object):
    '''Component object

    A salabim component is used as a data component (primarily for queueing)
    or as a component with a process |n|
    Usually, a component will be defined as a subclass of Component.

    Parameters
    ----------
    name : str
        name of the component. |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

    at : float
        schedule time |n|
        if omitted, now is used

    delay : float
        schedule with a delay |n|
        if omitted, no delay

    urgent : bool
        urgency indicator |n|
        if False (default), the component will be scheduled
        behind all other components scheduled
        for the same time |n|
        if True, the component will be scheduled
        in front of all components scheduled
        for the same time

    process : str
        name of process to be started. |n|
        if omitted, it will try to start self.process() |n|
        if None, no process will be started even if self.process() exists,
        i.e. become a data component. |n|
        note that the function *must* be a generator,
        i.e. contains at least one yield.

    suppress_trace : bool
        suppress_trace indicator |n|
        if True, this component will be excluded from the trace |n|
        If False (default), the component will be traced |n|
        Can be queried or set later with the suppress_trace method.

    mode : str preferred
        mode |n|
        will be used in trace and can be used in animations |n|
        if omitted, the mode will be None. |n|
        also mode_time will be set to now.

    env : Environment
        environment where the component is defined |n|
        if omitted, _default_env will be used
    '''

    def __init__(self, name=omitted, at=omitted, delay=0, urgent=False,
      process=omitted, suppress_trace=False, mode=None, env=omitted, *args, **kwargs):
        if env is omitted:
            self.env = _default_env
        else:
            self.env = env
        if name is omitted:
            name = str(type(self)).split('.')[-1].split("'")[0].lower() + '.'
        self.name(name)
        self._qmembers = {}
        self._process = None
        self._status = data
        self._requests = collections.defaultdict(int)
        self._claims = collections.defaultdict(int)
        self._waits = []
        self._on_event_list = False
        self._scheduled_time = inf
        self._failed = False
        self._creation_time = self.env._now
        self._suppress_trace = suppress_trace
        self._mode = mode
        self._mode_time = self.env._now
        self._aos = {}
        self.env.print_trace('', '', self.name() +
            ' create', _modetxt(self._mode))
        if process is omitted:
            if self.hasprocess():
                process = 'process'
            else:
                process = None
        if process is not None:
            self.activate(process=process, at=at, delay=delay, urgent=urgent)
        self.setup(*args, **kwargs)

    def animation_objects(self, q):
        '''
        defines how to display a component when animating a queue

        Parameters
        ----------
        q : Queue
            queue to be visualized. This may be ignored.

        Returns
        -------
        List or tuple containg |n|
            size_x : how much to displace the next component in x-direction, if applicable|n|
            size_y : how much to displace the next component in y-direction, if applicable |n|
            animation objects0 : instance of Animate class |n|
            ...|n|
            default behaviour: |n|
            green square of size 40 (displacements 50), with the sequence number centered in white.

        Note
        ----
        If you override this method, be sure to use the same header. |n|
        '''
        size_x = 50
        size_y = 50
        ao1 = Animate(rectangle0=(-20, -20, 20, 20), linewidth0=0, fillcolor0='black')
        ao2 = Animate(text=str(self.sequence_number()), textcolor0='white', anchor='center')
        return (size_x, size_y, ao1, ao2)

    def _remove_from_aos(self, q):
        if q in self._aos:
            for ao in self._aos[q][2:]:
                ao.remove()
            del self._aos[q]

    def setup(self, *args, **kwargs):
        '''
        called immediately after initialization of a component.

        by default this is a dummy method, but it can be overridden.

        Example
        -------
            class Car(sim.Component):
                def setup(self, color):
                    self.color = color

                def process(self):
                    ...

            redcar=Car(color='red') |n|
            bluecar=Car(color='blue')
        '''
        pass

    def __repr__(self):
        return 'Component(' + self.name() + ')'

    def print_info(self):
        print('Component ' + hex(id(self)))
        print('  name=' + self.name())
        print('  class=' + str(type(self)).split('.')[-1].split("'")[0])
        print('  suppress_trace=' + str(self._suppress_trace))
        print('  status=' + self._status())
        print('  mode=' + _modetxt(self._mode).strip())
        print('  mode_time=' + time_to_string(self._mode_time))
        print('  creation_time=' + time_to_string(self._creation_time))
        print('  scheduled_time=' +
            time_to_string(self._scheduled_time))
        if len(self._qmembers) > 0:
            print('  member of queue(s):')
            for q in sorted(self._qmembers, key=lambda obj: obj.name().lower()):
                print('    ' + pad(q.name(), 20) + ' enter_time=' +
                    time_to_string(self._qmembers[q].enter_time) +
                    ' priority=' + str(self._qmembers[q].priority))
        if len(self._requests) > 0:
            print('  requesting resource(s):')

            for r in sorted(list(self._requests),
              key=lambda obj: obj.name().lower()):
                print('    ' + pad(r.name(), 20) + ' quantity=' +
                    str(self._requests[r]))
        if len(self._claims) > 0:
            print('  claiming resource(s):')

            for r in sorted(list(self._claims), key=lambda obj: obj.name().lower()):
                print('    ' + pad(r.name(), 20) +
                    ' quantity=' + str(self._claims[r]))
        if len(self._waits) > 0:
            if self._wait_all:
                print('  waiting for all of state(s):')
            else:
                print('  waiting for any of state(s):')
            for s, value, _ in self._waits:
                print('    ' + pad(s.name(), 20) +
                    ' value=' + str(value))

    def hasprocess(self):
        if hasattr(self, 'process'):
            if inspect.isgeneratorfunction(self.process):
                return True
            else:
                raise SalabimError('process has no yield statement')
        return False

    def _push(self, t, urgent):
        self.env._seq += 1
        if urgent:
            seq = -self.env._seq
        else:
            seq = self.env._seq
        self._on_event_list = True
        heapq.heappush(self.env._event_list, (t, seq, self))

    def _remove(self):
        if self._on_event_list:
            for i in range(len(self.env._event_list)):
                if self.env._event_list[i][2] == self:
                    self.env._event_list[i] = self.env._event_list[0]
                    self.env._event_list.pop(0)
                    heapq.heapify(self.env._event_list)
                    self._on_event_list = False
                    return
            raise SalabimError('remove error', self.name())
        if self.status == standby:
            if self in self.env._standby_list:
                self.env._standby_list(self)
            if self in self.env._pending_standby_list:
                self.env._pending_standby_list(self)

    def _check_fail(self):
        if self._requests:
            self.env.print_trace('', '', self.name(), 'request failed')
            for r in list(self._requests.keys()):
                self._leave(r._requesters)
                if r._requesters._length == 0:
                    r._minq = inf
            self._requests = collections.defaultdict(int)
            self._failed = True

        if self._waits:
            self.env.print_trace('', '', self.name(), 'wait failed')
            for state, _, _ in self._waits:
                if self in state._waiters:  # there might be more values for this state
                    self._leave(state._waiters)
            self._waits = []
            self._failed = True

    def _reschedule(self, scheduled_time, urgent, caller, extra=''):
        if scheduled_time < self.env._now:
            raise SalabimError(
                'scheduled time ({:0.3f}) before now ({:0.3f})'.
                format(scheduled_time, self.env._now))
        self._scheduled_time = scheduled_time
        if scheduled_time != inf:
            self._push(scheduled_time, urgent)
        self._status = scheduled
        self.env.print_trace(
            '', '', self.name() + ' ' + caller,
            'scheduled for {:10.3f}'.format(scheduled_time) + extra +
            _urgenttxt(urgent) + _modetxt(self._mode))

    def activate(self, at=omitted, delay=0, urgent=False, process=omitted,
      keep_request=False, keep_wait=False, mode=omitted):
        '''
        activate component

        Parameters
        ----------
        at : float
           schedule time |n|
           if omitted, now is used |n|
           inf is allowed

        delay : float
           schedule with a delay |n|
           if omitted, no delay

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time

        process : str
            name of process to be started. |n|
            if omitted, process will not be changed |n|
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

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        if to be applied for the current component, use yield self.activate(). |n|
        if both at and delay are specified, the component becomes current at the sum
        of the two values.
        '''
        p = None
        if process is omitted:
            if self._status == data:
                if self.hasprocess():
                    p = self.process
                else:
                    raise SalabimError('no process for data component')
        else:
            try:
                p = eval('self.' + process)
            except:
                raise SalabimError('self.' + process + ' not found')

        if p is None:
            extra = ''
        else:
            if not inspect.isgeneratorfunction(p):
                raise SalabimError(process, 'has no yield statement')
            self._process = p()
            extra = ' @' + process

        if self._status != current:
            self._remove()
            if p is None:
                if not (keep_request or keep_wait):
                    self._check_fail()
            else:
                self._check_fail()

        if mode is not omitted:
            self._mode = mode
            self._mode_time = self.env._now

        if at is omitted:
            scheduled_time = self.env._now + delay
        else:
            scheduled_time = at + delay

        self._reschedule(scheduled_time, urgent, 'activate', extra)

    def hold(self, duration=omitted, till=omitted, urgent=False, mode=omitted):
        '''
        hold the component

        Parameters
        ----------
        duration : float
           specifies the duration |n|
           if omitted, 0 is used |n|
           inf is allowed

        till : float
           specifies at what time the component will become current |n|
           if omitted, now is used |n|
           inf is allowed

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        if to be used for the current component, use ``yield self.hold(...)``. |n|

        if both duration and till are specified, the component will become current at the sum of
        these two.
        '''
        if self._status != passive:
            if self.status != current:
                self._checkisnotdata()
                self._remove()
                self._check_fail()
        if mode is not omitted:
            self._mode = mode
            self._mode_time = self.env._now

        if till is omitted:
            if duration is omitted:
                scheduled_time = self.env._now
            else:
                scheduled_time = self.env._now + duration
        else:
            if duration is omitted:
                scheduled_time = till
            else:
                raise SalabimError('both duration and till specified')

        self._reschedule(scheduled_time, urgent, 'hold')

    def passivate(self, mode=omitted):
        '''
        passivate the component

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing is specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

        Note
        ----
        if to be used for the current component (nearly always the case), use ``yield self.passivate(...)``.
        '''
        if self._status != current:
            self._checkisnotdata()
            self._remove()
            self._check_fail()
        self.env.print_trace('', '', self.name() +
                             ' passivate', _modetxt(self._mode))
        self._scheduled_time = inf
        if mode is not omitted:
            self._mode = mode
            self._mode_time = self.env._now

        self._status = passive

    def cancel(self, mode=omitted):
        '''
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
        if to be used for the current component, use ``yield self.cancel(...)``.
        '''
        if self._status != current:
            self._checkisnotdata()
            self._remove()
            self._check_fail()
        self.env.print_trace('', '', 'cancel ' +
                             self.name() + ' ' + _modetxt(self._mode))
        self._process = None
        self._scheduled_time = inf
        if mode is not omitted:
            self._mode = mode
            self._mode_time = self.env._now
        self._status = data
        if an_env == self.env:
            for ao in self.env.an_objects[:]:
                if ao.parent == self:
                    self.env.an_objects.remove(ao)

    def standby(self, mode=omitted):
        '''
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
        use ``yield self.standby(...)``.
        '''
        if self._status != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()
        self.env.print_trace('', '', 'standby', _modetxt(self._mode))
        self._scheduled_time = self.env._now
        self.env._standbylist.append(self)
        if mode is not omitted:
            self._mode = mode
            self._mode_time = self.env._now
        self._status = standby

    def request(self, *args, **kwargs):
        '''
        request from a resource or resources

        Parameters
        ----------
        args : sequence
            - sequence of resources, where quantity=1, priority=tail of requesters queue)
            - sequence of tuples/lists containing
                resource, a quantity and optionally a priority.
                if the priority is not specified, this request
                for the resources be added to the tail of
                the requesters queue |n|

        fail_at : float
            time out |n|
            if the request is not honored before fail_at,
            the request will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the request will not time out.

        fail_delay : float
            time out |n|
            if the request is not honored before now+fail_delay,
            the request will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the request will not time out.

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

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
        yield self.request(r1) |n|
        --> requests 1 from r1 |n|
        yield self.request(r1,r2) |n|
        --> requests 1 from r1 and 1 from r2 |n|
        yield self.request(r1,(r2,2),(r3,3,100)) |n|
        --> requests 1 from r1, 2 from r2 and 3 from r3 with priority 100 |n|
        yield self.request((r1,1),(r2,2)) |n|
        --> requests 1 from r1, 2 from r2 |n|

        '''
        fail_at = kwargs.pop('fail_at', omitted)
        fail_delay = kwargs.pop('fail_delay', omitted)
        mode = kwargs.pop('mode', omitted)
        assert not kwargs

        if self._status != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()
        if fail_at is omitted:
            if fail_delay is omitted:
                scheduled_time = inf
            else:
                if fail_delay == inf:
                    scheduled_time = inf
                else:
                    scheduled_time = self.env._now + fail_delay
        else:
            if fail_delay is omitted:
                scheduled_time = fail_at
            else:
                raise SalabimError('both fail_at and fail_delay specified')

        if mode is not omitted:
            self._mode = mode
            self._mode_time = self.env._now

        self._failed = False
        i = 0
        for i in range(len(args)):
            q = 1
            priority = None
            argsi = args[i]
            if isinstance(argsi, Resource):
                r = argsi
            elif isinstance(argsi, (tuple, list)):
                r = argsi[0]
                if len(argsi) >= 2:
                    q = argsi[1]
                if len(argsi) >= 3:
                    priority = argsi[2]
            else:
                raise SalabimError('incorrect specifier', argsi)

            if q <= 0:
                raise SalabimError('quantity ' + str(q) + ' <=0')
            self._requests[r] += q  # is same resource is specified several times, just add them up
            addstring = ''
            if priority is None:
                self._enter(r._requesters)
            else:
                addstring = addstring + ' priority=' + str(priority)
                self._enter_sorted(r._requesters, priority)
            self.env.print_trace(
                '', '', self.name(),
                'request for ' + str(q) + ' from ' + r.name() + addstring +
                ' ' + _modetxt(self._mode))

        for r, q in self._requests.items():
            if q < r._minq:
                r._minq = q

        self._tryrequest()

        if self._requests:
            self._reschedule(scheduled_time, False, 'request')

    def _tryrequest(self):
        honored = True
        for r in self._requests:
            if self._requests[r] > (r._capacity - r._claimed_quantity + 1e-8):
                honored = False
                break
        if honored:
            for r in list(self._requests):
                r._claimed_quantity += self._requests[r]

                self._leave(r._requesters)
                if not r._anonymous:
                    self._claims[r] += self._requests[r]
                    self._enter(r._claimers)
                if r._requesters._length == 0:
                    r._minq = inf
                r.claimed_quantity.tally()
                r.available_quantity.tally()
            self._requests = collections.defaultdict(int)
            self._remove()
            self._reschedule(self.env._now, False, 'request honour')

    def _release(self, r, q=omitted):
        if r not in self._claims:
            raise SalabimError(self.name() +
                ' not claiming from resource ' + r.name())
        if q is omitted:
            q = self._claims[r]
        if q > self._claims[r]:
            q = self._claims[r]
        r._claimed_quantity -= q
        self._claims[r] -= q
        if self._claims[r] < 1e-8:
            self._leave(r._claimers)
            if r._claimers._length == 0:
                r._claimed_quantity = 0  # to avoid rounding problems
            del self._claims[r]
        r.claimed_quantity.tally()
        r.available_quantity.tally()
        self.env.print_trace('', '', self.name(),
            'release ' + str(q) + ' from ' + r.name())
        r._tryrequest()

    def release(self, *args):
        '''
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
        '''
        if args:
            for i in range(len(args)):
                q = None
                argsi = args[i]
                if isinstance(argsi, Resource):
                    r = argsi
                elif isinstance(argsi, (tuple, list)):
                    r = argsi[0]
                    if len(argsi) >= 2:
                        q = argsi[1]
                else:
                    raise SalabimError('incorrect specifier' + argsi)
                if r._anonymous:
                    raise SalabimError(
                        'not possible to release anonymous resources ' + r.name())
                self._release(r, q)
        else:
            for r in list(self._claims.keys()):
                self._release(r)

    def wait(self, *args, **kwargs):
        '''
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

        fail_at : float
            time out |n|
            if the wait is not honored before fail_at,
            the wait will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the wait will not time out.

        fail_delay : float
            time out |n|
            if the wait is not honored before now+fail_delay,
            the request will be cancelled and the
            parameter failed will be set. |n|
            if not specified, the wait will not time out.

        all : bool
            if False (default), continue, if any of the given state/values is met |n|
            if True, continue if all of the given state/values are met

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations |n|
            if nothing specified, the mode will be unchanged. |n|
            also mode_time will be set to now, if mode is set.

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
          yield self.wait((light,'red'))
        * an expression, containg one or more $-signs
          the $ is replaced by state.value(), each time the condition is tested. |n|
          self refers to the component under test, state refers to the state
          under test. |n|
          yield self.wait((light,'$ in ("red","yellow")')) |n|
          yield self.wait((level,'$<30')) |n|
        * a function. In that case the parameter should function that
          should accept three arguments: the value, the component under test and the
          state under test. |n|
          usually the function will be a lambda function, but that's not
          a requirement. |n|
          yield self.wait((light,lambda t, comp, state: t in ('red','yellow'))) |n|
          yield self.wait((level,lambda t, comp, state: t < 30)) |n|

        Example
        -------
        yield self.wait(s1) |n|
        --> waits for s1.value()==True |n|
        yield self.wait(s1,s2) |n|
        --> waits for s1.value()==True or s2.value==True |n|
        yield self.wait((s1,False,100),(s2,'on'),s3) |n|
        --> waits for s1.value()==False or s2.value=='on' or s3.value()==True
        s1 is at the tail of waiters, because of the set priority
        yield self.wait(s1,s2,all=True) |n|
        --> waits for s1.value()==True and s2.value==True |n|
        '''
        fail_at = kwargs.pop('fail_at', omitted)
        fail_delay = kwargs.pop('fail_delay', omitted)
        all = kwargs.pop('all', False)
        mode = kwargs.pop('mode', omitted)
        assert not kwargs

        if self._status != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()

        self._wait_all = all
        self._fail = False

        if fail_at is omitted:
            if fail_delay is omitted:
                scheduled_time = inf
            else:
                if fail_delay == inf:
                    scheduled_time = inf
                else:
                    scheduled_time = self.env._now + fail_delay
        else:
            if fail_delay is omitted:
                scheduled_time = fail_at
            else:
                raise SalabimError('both fail_at and fail_delay specified')

        if mode is not omitted:
            self._mode = mode
            self._mode_time = self.env._now

        for i in range(len(args)):
            value = True
            priority = None
            argsi = args[i]
            if isinstance(argsi, State):
                state = argsi
            elif isinstance(argsi, (tuple, list)):
                state = argsi[0]
                if len(argsi) >= 2:
                    value = argsi[1]
                if len(argsi) >= 3:
                    priority = argsi[2]
            else:
                raise SalabimError('incorrect specifier', args)

            for (statex, _, _) in self._waits:
                if statex == state:
                    break
            else:
                if priority is None:
                    self._enter(state._waiters)
                else:
                    self._enter_sorted(state._waiters, priority)
            if inspect.isfunction(value):
                self._waits.append((state, value, 2))
            elif '$' in str(value):
                self._waits.append((state, value, 1))
            else:
                self._waits.append((state, value, 0))

        if not self._waits:
            raise SalabimError('no states specified')
        self._trywait()

        if self._waits:
            self._reschedule(scheduled_time, False, 'wait')

    def _trywait(self):
        if self._wait_all:
            honored = True
            for state, value, valuetype in self._waits:
                if valuetype == 0:
                    if value != state._value:
                        honored = False
                        break
                elif valuetype == 1:
                    if eval(value.replace('$', 'state.value()')):
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
                    if eval(value.replace('$', str(state._value))):
                        honored = True
                        break
                elif valuetype == 2:
                    if value(state._value, self, state):
                        honored = True
                        break

        if honored:
            for s, _, _ in self._waits:
                if self in s._waiters:  # there might be more values for this state
                    self._leave(s._waiters)
            self._waits = []
            self._remove()
            self._reschedule(self.env._now, False, 'wait honor')

        return honored

    def claimed_quantity(self, resource):
        '''
        Parameters
        ----------
        resource : Resoure
            resource to be queried

        Returns
        -------
        the claimed quantity from a resource : float or int
            if the resource is not claimed, 0 will be returned
        '''
        return self._claims.get(resource, 0)

    def claimed_resources(self):
        '''
        Returns
        -------
        list of claimed resources : list
        '''
        return self._claims.keys()

    def requested_resources(self):
        '''
        Returns
        -------
        list of requested resources : list
        '''
        return self._requests.keys()

    def requested_quantity(self, resource):
        '''
        Parameters
        ----------
        resource : Resoure
            resource to be queried

        Returns
        -------
        the requested (not yet honored) quantity from a resource : float or int
            if there is no request for the resource, 0 will be returned
        '''
        return self._requests.get(resource, 0)

    def failed(self):
        '''
        Returns
        -------
        True, if the latest request/wait has failed (either by timeout or external) : bool
        False, otherwise
        '''
        return self._failed

    def name(self, txt=omitted):
        '''
        Parameters
        ----------
        txt : str
            name of the component |n|
            if txt ends with a period, the name will be serialized |n|
            if omittted, no change

        Returns
        -------
        Name of the component : str
        '''

        if txt is not omitted:
            _set_name(txt, self.env._nameserializeComponent, self)
        return _decode_name(self._name)

    def base_name(self):
        '''
        Returns
        -------
        base name of the component (the name used at init or name): str
        '''
        return self._base_namee

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the component : int
            (the sequence number at init or name) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot at the end)
            will be numbered)
        '''
        return self._sequence_number

    def running_process(self):
        '''
        Returns
        -------
        name of the running process : str
            if data component, None
        '''
        if self._process is None:
            return None
        else:
            return self._process.__name__

    def suppress_trace(self, value=omitted):
        '''
        Parameters
        ----------
        value: bool
            new suppress_trace value |n|
            if omitted, no change

        Returns
        -------
        suppress_status : bool
            components with the suppress_status of False, will be ignored in the trace
        '''
        if value is not omitted:
            self._suppress_trace = value
        return self._suppress_trace

    def mode(self, value=omitted):
        '''
        Parameters
        ----------
        value: any, str recommended
            new mode |n|
            if omitted, no change |n|
            mode_time will be set if a new mode is specified

        Returns
        -------
        mode of the component : any, usually str
            the mode is useful for tracing and animations. |n|
            Usually the mode will be set in a call to passivate, hold, activate, request or standby.
        '''
        if value is not omitted:
            self._mode_time = self.env._now
            self._mode = value

        return self._mode

    def ispassive(self):
        '''
        Returns
        -------
        True if status is passive, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        '''
        return self._status == passive

    def iscurrent(self):
        '''
        Returns
        -------
        True if status is current, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        '''
        return self._status == current

    def isrequesting(self):
        '''
        Returns
        -------
        True if status is requesting, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        '''
        return bool(self._requests)

    def iswaiting(self):
        '''
        Returns
        -------
        True if status is waiting, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        '''
        return bool(self._waits)

    def isscheduled(self):
        '''
        Returns
        -------
        True if status is scheduled, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        '''
        return (self._status == scheduled) and (not self._requests) and (not self._waits)

    def isstandby(self):
        '''
        Returns
        -------
        True if status is standby, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True
        '''
        return self._status == standby

    def isdata(self):
        '''
        Returns
        -------
        True if status is data, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True!
        '''
        return self._status == data

    def index_in_queue(self, q):
        '''
        Parameters
        ----------
        q : Queue
            queue to be queried

        Returns
        -------
        index of component in q : int
            if component belongs to q |n|
            -1 if component does not belong to q
        '''
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

    def _enter(self, q):
        savetrace = self.env._trace
        self.env._trace = False
        self.enter(q)
        self.env._trace = savetrace

    def enter(self, q):
        '''
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
        '''
        self._checknotinqueue(q)
        priority = q._tail.predecessor.priority
        Qmember().insert_in_front_of(q._tail, self, q, priority)

    def enter_at_head(self, q):
        '''
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
        '''

        self._checknotinqueue(q)
        priority = q._head.successor.priority
        Qmember().insert_in_front_of(q._head.successor, self, q, priority)

    def enter_in_front_of(self, q, poscomponent):
        '''
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
        '''

        self._checknotinqueue(q)
        m2 = poscomponent._checkinqueue(q)
        priority = m2.priority
        Qmember().insert_in_front_of(m2, self, q, priority)

    def enter_behind(self, q, poscomponent):
        '''
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
        '''

        self._checknotinqueue(q)
        m1 = poscomponent._checkinqueue(q)
        priority = m1.priority
        Qmember().insert_in_front_of(m1.successor, self, q, priority)

    def enter_sorted(self, q, priority):
        '''
        enters a queue, according to the priority

        Parameters
        ----------
        q : Queue
            queue to enter

        priority: float
            priority in the queue

        Note
        ----
        The component is placed just before the first component with a priority > given priority
        '''

        self._checknotinqueue(q)
        m2 = q._head.successor
        while (m2 != q._tail) and (m2.priority <= priority):
            m2 = m2.successor
        Qmember().insert_in_front_of(m2, self, q, priority)

    def _enter_sorted(self, q, priority):
        savetrace = self.env._trace
        self.env._trace = False
        self.enter_sorted(q, priority)
        self.env._trace = savetrace

    def _leave(self, q):
        savetrace = self.env._trace
        self.env._trace = False
        self.leave(q)
        self.env._trace = savetrace

    def leave(self, q):
        '''
        leave queue

        Parameters
        ----------
        q : Queue
            queue to leave

        Note
        ----
        statistics are updated accordingly
        '''

        mx = self._checkinqueue(q)
        m1 = mx.predecessor
        m2 = mx.successor
        m1.successor = m2
        m2.predecessor = m1
        mx.component = None
        # signal for components method that member is not in the queue
        q._length -= 1
        del self._qmembers[q]
        self.env.print_trace('', '', self.name(), 'leave ' + q.name())
        length_of_stay = self.env._now - mx.enter_time
        q.length_of_stay.tally(length_of_stay)
        q.length.tally()
        if q._animate_on:
            self._remove_from_aos(q)
            q._animate_update()

    def priority(self, q, priority=omitted):
        '''
        gets/sets the priority of a component in a queue

        Parameters
        ----------
        q : Queue
            queue where the component belongs to

        priority : float
            priority in queue |n|
            if omitted, no change

        Returns
        -------
        the priority of the component in the queue : float

        Note
        ----
        if you change the priority, the order of the queue may change
        '''

        mx = self._checkinqueue(q)
        if priority is not omitted:
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
        '''
        Parameters
        ----------
        q : Queue
            queue where the component belongs to

        Returns
        -------
        the successor of the component in the queue: Component
            if component is not at the tail. |n|
            returns None if component is at the tail.
        '''

        mx = self._checkinqueue(q)
        return mx.successor.component

    def predecessor(self, q):
        '''
        Parameters
        ----------
        q : Queue
            queue where the component belongs to

        Returns : Component
            predecessor of the component in the queue
            if component is not at the head. |n|
            returns None if component is at the head.
        '''

        mx = self._checkinqueue(q)
        return mx.predecessor.component

    def enter_time(self, q):
        '''
        Parameters
        ----------
        q : Queue
            queue where component belongs to

        Returns
        -------
        time the component entered the queue : float
        '''
        mx = self._checkinqueue(q)
        return mx.enter_time

    def creation_time(self):
        '''
        Returns
        -------
        time the component was created : float
        '''
        return self._creation_time

    def scheduled_time(self):
        '''
        Returns
        -------
        time the component scheduled for, if it is scheduled : float
            returns inf otherwise
        '''
        return self._scheduled_time

    def mode_time(self):
        '''
        Returns
        -------
        time the component got it's latest mode : float
            For a new component this is
            the time the component was created. |n|
            this function is particularly useful for animations.
        '''
        return self._mode_time

    def status(self):
        '''
        returns the status of a component

        possible values are
            - data
            - passive
            - scheduled
            - requesting
            - current
            - standby
        '''

        if len(self._requests) > 0:
            return requesting
        if len(self._waits) > 0:
            return waiting
        return self._status

    def _member(self, q):
        return self._qmembers.get(q, None)

    def _checknotinqueue(self, q):
        mx = self._member(q)
        if mx is None:
            pass
        else:
            raise SalabimError(
                self.name() + ' is already member of ' + q.name())

    def _checkinqueue(self, q):
        mx = self._member(q)
        if mx is None:
            raise SalabimError(self.name() + ' is not member of ' + q.name())
        else:
            return mx

    def _checkisnotdata(self):
        if self._status == data:
            raise SalabimError(self.name() + ' data component not allowed')

    def _checkisnotmain(self):
        if self == self.env._main:
            raise SalabimError(self.name() + ' main component not allowed')


class _Distribution():
    pass


class Exponential(_Distribution):
    '''
    exponential distribution

    Exponential(mean,randomstream)

    Parameters
    ----------
    mean :float
        mean of the distribtion |n|
        must be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''

    def __init__(self, mean, randomstream=omitted):
        if mean <= 0:
            raise SalabimError('mean<=0')
        self._mean = mean
        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream

    def __repr__(self):
        return('Exponential')

    def print_info(self):
        print('Exponential distribution ' + hex(id(self)))
        print('  mean=' + str(self._mean))
        print('  randomstream=' + hex(id(self.randomstream)))

    def sample(self):
        '''
        returns sample
        '''
        return self.randomstream.expovariate(1 / (self._mean))

    def mean(self):
        '''
        returns the mean of the distribution
        '''
        return self._mean


class Normal(_Distribution):
    '''
    normal distribution

    Normal(mean,standard_deviation,randomstream)

    Parameters
    ----------
    mean : float
        mean of the distribution

    standard_deviation : float
        standard deviation of the distribution |n|
        if omitted, 0 is used, thus effectively a contant distributiin |n|
        must be >=0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''

    def __init__(self, mean, standard_deviation=omitted, randomstream=omitted):
        self._mean = mean
        if standard_deviation is omitted:
            self._standard_deviation = 0
        else:
            self._standard_deviation = standard_deviation
        if self._standard_deviation < 0:
            raise SalabimError('standard_deviation<0')
        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream

    def __repr__(self):
        return 'Normal'

    def print_info(self):
        print('Normal distribution ' + hex(id(self)))
        print('  mean=' + str(self._mean))
        print('  standard_deviation=' + str(self._standard_deviation))
        print('  randomstream=' + hex(id(self.randomstream)))

    def sample(self):
        '''
        returns sample
        '''
        return self.randomstream.normalvariate(self._mean, self._standard_deviation)

    def mean(self):
        '''
        returns the mean of the distribution
        '''
        return self._mean


class Uniform(_Distribution):
    '''
    uniform distribution

    Uniform(lowerbound,upperboud,seed)

    Parameters
    ----------
    lowerbound : float
        lowerbound of the distribution

    upperbound : float
        upperbound of the distribution |n|
        if omitted, lowerbound will be used |n|
        must be >= lowerbound

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''

    def __init__(self, lowerbound, upperbound=omitted, randomstream=omitted):
        self._lowerbound = lowerbound
        if upperbound is omitted:
            self._upperbound = lowerbound
        else:
            self._upperbound = upperbound
        if self._lowerbound > self._upperbound:
            raise SalabimError('lowerbound>upperbound')
        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream
        self._mean = (self._lowerbound + self._upperbound) / 2

    def __repr__(self):
        return 'Uniform'

    def print_info(self):
        print('Uniform distribution ' + hex(id(self)))
        print('  lowerbound=' + str(self._lowerbound))
        print('  upperbound=' + str(self._upperbound))
        print('  randomstream=' + hex(id(self.randomstream)))

    def sample(self):
        '''
        returns sample
        '''
        return self.randomstream.uniform(self._lowerbound, self._upperbound)

    def mean(self):
        '''
        returns the mean of the distribution
        '''
        return self._mean


class Triangular(_Distribution):
    '''
    triangular distribution

    Triangular(low,high,mode,seed)

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

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''

    def __init__(self, low, high=omitted, mode=omitted, randomstream=omitted):
        self._low = low
        if high is omitted:
            self._high = low
        else:
            self._high = high
        if mode is omitted:
            self._mode = (self._high + self._low) / 2
        else:
            self._mode = mode
        if self._low > self._high:
            raise SalabimError('low>high')
        if self._low > self._mode:
            raise SalabimError('low>mode')
        if self._high < self._mode:
            raise SalabimError('high<mode')
        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream
        self._mean = (self._low + self._mode + self._high) / 3

    def __repr__(self):
        return 'Triangular'

    def print_info(self):
        print('Triangular distribution ' + hex(id(self)))
        print('  low=' + str(self._low))
        print('  high=' + str(self._high))
        print('  mode=' + str(self._mode))
        print('  randomstream=' + hex(id(self.randomstream)))

    def sample(self):
        '''
        returns sample
        '''
        return self.randomstream.triangular(self._low, self._high, self._mode)

    def mean(self):
        '''
        returns the mean of the distribution
        '''
        return self._mean


class Constant(_Distribution):
    '''
    constant distribution

    Constant(value,randomstream)

    Parameters
    ----------
    value : float
        value to be returned in sample

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed |n|
        Note that this is only for compatibility with other distributions

    '''

    def __init__(self, value, randomstream=omitted):
        self._value = value
        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream
        self._mean = value

    def __repr__(self):
        return 'Constant'

    def print_info(self):
        print('Constant distribution ' + hex(id(self)))
        print('  value=' + str(self._value))
        print('  randomstream=' + hex(id(self.randomstream)))

    def sample(self):
        '''
        returns sample (is always the specified constant)
        '''
        return(self._value)

    def mean(self):
        '''
        returns the mean of the distribution
        '''
        return self._mean


class Cdf(_Distribution):
    '''
    Cumulative distribution function

    Cdf(spec,seed)

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

    randomstream: randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it defines a new stream with the specified seed

    '''

    def __init__(self, spec, randomstream=omitted):
        self._x = []
        self._cum = []
        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream

        lastcum = 0
        lastx = -inf
        spec = list(spec)
        if not spec:
            raise SalabimError('no arguments specified')
        if spec[1] != 0:
            raise SalabimError('first cumulative value should be 0')
        while len(spec) > 0:
            x = spec.pop(0)
            if not spec:
                raise SalabimError('uneven number of parameters specified')
            if x < lastx:
                raise SalabimError(
                    'x value {} is smaller than previous value {}'.format(x, lastx))
            cum = spec.pop(0)
            if cum < lastcum:
                raise SalabimError('cumulative value {} is smaller than previous value {}'
                    .format(cum, lastcum))
            self._x.append(x)
            self._cum.append(cum)
            lastx = x
            lastcum = cum
        if lastcum == 0:
            raise SalabimError('last cumulative value should be >0')
        for i in range(len(self._cum)):
            self._cum[i] = self._cum[i] / lastcum
        self._mean = 0
        for i in range(len(self._cum) - 1):
            self._mean +=\
                ((self._x[i] + self._x[i + 1]) / 2) * \
                (self._cum[i + 1] - self._cum[i])

    def __repr__(self):
        return 'Cdf'

    def print_info(self):
        print('Cdf distribution ' + hex(id(self)))
        print('  randomstream=' + hex(id(self.randomstream)))

    def sample(self):
        '''
        Returns
        -------
        sample : float
        '''
        r = self.randomstream.random()
        for i in range(len(self._cum)):
            if r < self._cum[i]:
                return interpolate(r, self._cum[i - 1], self._cum[i], self._x[i - 1], self._x[i])
        return self._x[i]

    def mean(self):
        '''
        Returns
        -------
        mean of the distribution : float
        '''
        return self._mean


class Pdf(_Distribution):
    '''
    Probability distribution function

    Pdf(spec,probabilities,seed)

    Parameters
    ----------
    spec : list or tuple
        either

        -   if no probabilities specified |n|:
            list with x-values and corresponding probability
            (x0, p0, x1, p1, ...xn,pn) |n|
        -   if probabilities is specified |n|:
            list with x-values

    probabilities : list, tuple or float
        if omitted, spec contains the probabilities |n|
        the list (p0, p1, ...pn) contains the probabilities of the corresponding
        x-values from spec. |n|
        alternatively, if a float is given (e.g. 1), all x-values
        have equal probability. The value is not important.

    randomstream : randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    Note
    ----
    p0+p1=...+pn>0 |n|
    all densities are auto scaled according to the sum of p0 to pn,
    so no need to have p0 to pn add up to 1 or 100. |n|
    The x-values may be any type. |n|
    If it is a salabim distribution, not the distribution,
    but a sample will be returned when calling sample.
    '''

    def __init__(self, spec, probabilities=omitted, randomstream=omitted):
        self._x = [0]  # just a place holder
        self._cum = [0]
        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream

        sump = 0
        sumxp = 0
        hasmean = True
        if probabilities is omitted:
            spec = list(spec)

            if not spec:
                raise SalabimError('no arguments specified')
            while len(spec) > 0:
                x = spec.pop(0)
                if not spec:
                    raise SalabimError(
                        'uneven number of parameters specified')
                self._x.append(x)
                p = spec.pop(0)
                sump += p
                self._cum.append(sump)
                if isinstance(x, _Distribution):
                    x = x._mean
                try:
                    sumxp += float(x) * p
                except:
                    hasmean = False
        else:
            spec = list(spec)
            if isinstance(probabilities, (list, tuple)):
                probabilities = list(probabilities)
            else:
                probabilities = len(spec) * [1]
            if len(spec) != len(probabilities):
                raise SalabimError(
                    'length of x-values does not match length of probabilities')

            while len(spec) > 0:
                x = spec.pop(0)
                self._x.append(x)
                p = probabilities.pop(0)
                sump += p
                self._cum.append(sump)
                if isinstance(x, _Distribution):
                    x = x._mean
                try:
                    sumxp += float(x) * p
                except:
                    hasmean = False

        if sump == 0:
            raise SalabimError('at least one probability should be >0')

        for i in range(len(self._cum)):
            self._cum[i] = self._cum[i] / sump
        if hasmean:
            self._mean = sumxp / sump
        else:
            self._mean = nan

    def __repr__(self):
        return 'Pdf'

    def print_info(self):
        print('Pdf distribution ' + hex(id(self)))
        print('  randomstream=' + hex(id(self.randomstream)))

    def sample(self):
        '''
        Returns
        -------
        sample : any (usually float)
        '''
        r = self.randomstream.random()
        for i in range(len(self._cum)):
            if r <= self._cum[i]:
                if isinstance(self._x[i], _Distribution):
                    return self._x[i].sample()
                return self._x[i]

    def mean(self):
        '''
        Returns
        -------
        mean of the distribution : float
            if the mean can't be calculated (if not all x-values are scalars or distributions),
            nan will be returned.
        '''
        return self._mean


class Distribution(_Distribution):
    '''
    Generate a distribution from a string

    Distribution(spec,randomstream)

    Parameters
    ----------
    spec : str
        - string containing a valid salabim distribution, where only the first
          letters are relevant and casing is not important
        - string containing one float (c1), resulting in Constant(c1)
        - string containing two floats seperated by a comma (c1,c2),
          resulting in a Uniform(c1,c2)
        - string containing three floats, separated by commas (c1,c2,c3),
          resulting in a Triangular(c1,c2,c3)

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
    '''

    def __init__(self, spec, randomstream=omitted):

        spec_orig = spec

        sp = spec.split('(')
        pre = sp[0].upper().strip()

        # here we have either a string starting with a ( of no ( at all
        if (pre == '') or not('(' in spec):
            spec = spec.replace(')', '')  # get rid of closing parenthesis
            spec = spec.replace('(', '')  # get rid of starting parenthesis
            sp = spec.split(',')
            if len(sp) == 1:
                c1 = sp[0]
                spec = 'Constant({})'.format(c1)
            elif len(sp) == 2:
                c1 = sp[0]
                c2 = sp[1]
                spec = 'Uniform({},{})'.format(c1, c2)
            elif len(sp) == 3:
                c1 = sp[0]
                c2 = sp[1]
                c3 = sp[2]
                spec = 'Triangular({},{},{})'.format(c1, c2, c3)
            else:
                raise SalabimError('incorrect specifier', spec_orig)

        else:
            for distype in ('Uniform', 'Constant', 'Triangular', 'Exponential', 'Normal', 'Cdf', 'Pdf'):
                if pre == distype.upper()[:len(pre)]:
                    sp[0] = distype
                    spec = '('.join(sp)
                    break

        d = eval(spec)

        if randomstream is omitted:
            self.randomstream = random
        else:
            assert isinstance(randomstream, random.Random)
            self.randomstream = randomstream
        self._distribution = d
        self._mean = d._mean

    def __repr__(self):
        return self._distribution.__repr__()

    def print_info(self):
        self._distribution.print_info()

    def sample(self):
        '''
        Returns
        -------
        sample : float
        '''
        self._distribution.randomstream = self.randomstream
        return self._distribution.sample()

    def mean(self):
        '''
        Returns
        -------
        mean of the distribution : float
        '''
        return self._mean


class State(object):
    '''
    State

    Parameters
    ----------
    name : str
        name of the state |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name state. will be used

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

        -  'any' (default) stores values in a list. This allows for
           non numeric values. In calculations the values are
           forced to a numeric value (0 if not possible) do not use -inf
        -  'bool' bool (False, True). Actually integer >= 0 <= 254 1 byte do not use 255
        -  'int8' integer >= -127 <= 127 1 byte do not use -128
        -  'uint8' integer >= 0 <= 254 1 byte do not use 255
        -  'int16' integer >= -32767 <= 32767 2 bytes do not use -32768
        -  'uint16' integer >= 0 <= 65534 2 bytes do not use 65535
        -  'int32' integer >= -2147483647 <= 2147483647 4 bytes do not use -2147483648
        -  'uint32' integer >= 0 <= 4294967294 4 bytes do not use 4294967295
        -  'int64' integer >= -9223372036854775807 <= 9223372036854775807 8 bytes do not use -9223372036854775808
        -  'uint64' integer >= 0 <= 18446744073709551614 8 bytes do not use 18446744073709551615
        -  'float' float 8 bytes do not use -inf
        
    animation_objects : list or tuple
        overrides the deafult animation_object method |n|
        the method should have a header like |n|
        ``def animation_objects(self, value):`` |n|
        and should return a list or tuple of animation objects, which
        will be used when the state changes value. |n|
        The default method displays a square of size 40. If the value
        is a valid color, that will be the color of the square. Otherwise,
        the square will be black with the value displayed in white in
        the centre.

    env : Environment
        environment to be used |n|
        if omitted, _default_env is used
    '''
    def __init__(self, name=omitted, value=False, type='any',
      monitor=True, animation_objects=omitted, env=omitted):
        if env is omitted:
            self.env = _default_env
        else:
            self.env = env
        if name is omitted:
            name = 'state.'
        self.name(name)
        self._value = value
        self._animate_on = False
        self._aos = []
        self._waiters = Queue(
            name=('waiters of ', self),
            monitor=monitor, env=self.env, _isinternal=True)
        self.value = MonitorTimestamp(
            name=('Value of ', self),
            getter=self._get_value, monitor=monitor, type=type, env=self.env)
        if animation_objects is not omitted:
            self.animation_objects = animation_objects.__get__(self, State)
        self.env.print_trace(
            '', '', self.name() + ' create',
            'value= ' + str(self._value))

    def animate(self, x=500, y=100, on=True):
        '''
        turns on/off animation for the state

        Parameters
        ----------
        x : float
            x-position of the animation|n|
            default: 500

        y : float
            y-position of the animation |n|
            default: 100

        on : bool
            if True (default) do animate the state. If False, do not animate.
        '''

        self._animate_on = on
        if on:
            self._animate_x = x
            self._animate_y = y
            self._animate_update()
        else:
            self._remove_from_aos()

    def _remove_from_aos(self):
        for ao in self._aos:
            ao.remove()
        self._aos = []

    def animation_objects(self, value):
        if str(value).lower() in colornames():
            ao1 = Animate(rectangle0=(-20, -20, 20, 20), fillcolor0=value, linewidth0=0)
            return (ao1,)
        else:
            ao1 = Animate(rectangle0=(-20, -20, 20, 20), fillcolor0='black', linewidth0=0)
            ao2 = Animate(text=str(value), textcolor0='white', anchor='center')
            return ao1, ao2

    def _animate_update(self):
        self._remove_from_aos()
        for ao in self.animation_objects(self._value):
            ao.x0 = self._animate_x
            ao.y0 = self._animate_y
            self._aos.append(ao)

    def __repr__(self):
        return 'State(' + self.name() + ')'

    def print_info(self):
        print('State ' + hex(id(self)))
        print('  name=' + self.name())
        print('  value=' + str(self._value))
        if self._waiters:
            print('  waiting component(s):')
            mx = self._waiters._head.successor
            while mx != self._waiters._tail:
                c = mx.component
                mx = mx.successor
                values = ''
                for s, value, valuetype in c._waits:
                    if s == self:
                        if values != '':
                            values = values + ', '
                        values = values + str(value)

                print('    ' + pad(c.name(), 20), ' value(s): ' + values)
        else:
            print('  no waiting components')

    def __call__(self):
        return self._value

    def get(self):
        '''
        get value of the state

        Returns
        -------
        value of the state : any
        '''
        return self._value

    def set(self, value=True):
        '''
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
        '''
        self.env.print_trace('', '', self.name() + ' set', 'value = ' + str(value))
        if self._value != value:
            self._value = value
            self.value.tally()
            if self._animate_on:
                self._animate_update()
            self._trywait()

    def reset(self, value=False):
        '''
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
        '''
        self.env.print_trace('', '', self.name() + ' reset', 'value = ' + str(value))
        if self._value != value:
            self._value = value
            self.value.tally()
            if self._animate_on:
                self._animate_update()
            self._trywait()

    def trigger(self, value=True, value_after=omitted, max=inf):
        '''
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
        '''
        if value_after is omitted:
            value_after = self._value
        self.env.print_trace('', '', self.name() + ' trigger',
            ' value = ' + str(value) + ' --> ' + str(value_after) +
            ' allow ' + str(max) + ' components')
        self._value = value
        self.value.tally()  # strictly speaking, not required
        self._trywait(max)
        self._value = value_after
        self.value.tally()
        if self._animate_on:
            self._animate_update()
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

    def monitor(self, value=omitted):
        '''
        enables/disables the state monitors and timestamped monitors

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
        '''
        self.requesters().monitor(value)
        self.value.monitor(value)

    def reset_monitors(self, monitor=omitted):
        '''
        resets the timestamped monitor for the state's value and the monitors of the requesters queue

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change of monitoring state

        '''
        self.requesters().reset_monitors(monitor)
        self.value.reset()

    def _get_value(self):
        return self._value

    def name(self, txt=omitted):
        '''
        Parameters
        ----------
        txt : str
            name of the state |n|
            if txt ends with a period, the name will be serialized |n|
            if omittted, no change

        Returns
        -------
        Name of the state : str
        '''
        if txt is not omitted:
            _set_name(txt, self.env._nameserializeState, self)
        return _decode_name(self._name)

    def base_name(self):
        '''
        Returns
        -------
        base name of the state (the name used at init or name): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the state : int
            (the sequence number at init or name) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot at the end)
            will be numbered)
        '''
        return self._sequence_number

    def print_statistics(self):
        '''
        prints a summary of statistics of the state
        '''
        print('Statistics of {} at {}'.format(self.name(), fn(self.env._now, 13, 3)))
        self.waiters().length.print_statistics(show_header=False, show_legend=True, do_indent=True)
        print()
        self.waiters().length_of_stay.print_statistics(show_header=False, show_legend=False, do_indent=True)
        print()
        self.value.print_statistics(show_header=False, show_legend=False, do_indent=True)

    def waiters(self):
        '''
        Returns
        -------
        queue containing all components waiting for this state : Queue
        '''
        return self._waiters


class Resource(object):
    '''
    Resource

    Parameters
    ----------
    name : str
        name of the resource |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
    if omitted, the name resource. will be used

    capacity : float
        capacity of the resouce |n|
        if omitted, 1

    anonymous : bool
        anonymous specifier |n|
        if True, claims are not related to any component. This is useful
        if the resource is actually just a level. |n|
        if False, claims belong to a component.

    monitor : bool
        if True (default) , the requesters queue, the claimers queue,
        the capacity, the available_quantity and the claimed_quantity are monitored |n|
        if False, monitoring is disabled.

    env : Environment
        environment to be used |n|
        if omitted, _default_env is used
    '''

    def __init__(self, name=omitted, capacity=1,
                 anonymous=False, monitor=True, env=omitted):
        if env is omitted:
            self.env = _default_env
        else:
            self.env = env
        if name is omitted:
            name = 'resource.'
        self._capacity = capacity
        self.name(name)
        self._requesters = Queue(
            name='requesters of ' + name,
            monitor=monitor, env=self.env, _isinternal=True)
        self._claimers = Queue(
            name='claimers of ' + name,
            monitor=monitor, env=self.env, _isinternal=True)
        self._claimed_quantity = 0
        self._anonymous = anonymous
        self._minq = inf
        self.capacity = MonitorTimestamp(
            ('Capacity of ', self),
            getter=self._get_capacity, monitor=monitor, type='float', env=self.env)
        self.claimed_quantity = MonitorTimestamp(
            ('Claimed quantity of ', self),
            getter=self._get_claimed_quantity, monitor=monitor, type='float', env=self.env)
        self.available_quantity = MonitorTimestamp(
            ('Available quantity of ', self),
            getter=self._get_available_quantity, monitor=monitor, type='float', env=self.env)
        self.env.print_trace(
            '', '', self.name() + ' create',
            'capacity=' + str(self._capacity) + (' anonymous' if self._anonymous else ''))

    def reset_monitors(self, monitor=omitted):
        '''
        resets the resource monitors  and timestamped monitors

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change of monitoring state

        Note
        ----
            it is possible to reset individual monitoring with
            claimers().reset_monitors(),
            requesters().reset_monitors,
            capacity.reset(),
            available_quantity.reset() or
            claimed_quantity.reset()
        '''

        self.requesters().reset_monitors(monitor)
        self.claimers().reset_monitors(monitor)
        self.capacity.reset(monitor)
        self.available_quantity.reset(monitor)
        self.claimed_quantity.reset(monitor)

    def print_statistics(self):
        '''
        prints a summary of statistics of a resource
        '''
        print('Statistics of {} at {:13.3f}'.format(self.name(), self.env._now))
        show_legend = True
        for q in [self.requesters(), self.claimers()]:
            q.length.print_statistics(show_header=False, show_legend=show_legend, do_indent=True)
            show_legend = False
            print()
            q.length_of_stay.print_statistics(show_header=False, show_legend=show_legend, do_indent=True)
            print()

        for m in [self.capacity, self.available_quantity, self.claimed_quantity]:
            m.print_statistics(show_header=False, show_legend=show_legend, do_indent=True)
            print()

    def monitor(self, value):
        '''
        enables/disables the resource monitors  and timestamped monitors

        Parameters
        ----------
        value : bool
            if True, monitoring is enabled |n|
            if False, monitoring is disabled |n|

        Note
        ----
        it is possible to individually control monitoring with claimers().monitor()
        and requesters().monitor(), capacity.monitor(), available_quantity.monitor)
        or claimed_quantity.monitor()
        '''
        self.requesters().monitor(value)
        self.claimers().monitor(value)
        self.capacity.monitor(value)
        self.available_quantity.monitor(value)
        self.claimed_quantity.monitor(value)

    def __repr__(self):
        return 'Resource(' + self.name() + ')'

    def print_info(self):
        print('Resource ' + hex(id(self)))
        print('  name=' + self.name())
        print('  capacity=' + str(self._capacity))
        if self._requesters:
            print('  requesting component(s):')
            mx = self._requesters._head.successor
            while mx != self._requesters._tail:
                c = mx.component
                mx = mx.successor
                print('    ' + pad(c.name(), 20) +
                    ' quantity=' + str(c._requests[self]))
        else:
            print('  no requesting components')

        print('  claimed_quantity=' + str(self._claimed_quantity))
        if self._claimed_quantity >= 0:
            if self._anonymous:
                print('  not claimed by any components,' +
                    ' because the resource is anonymous')
            else:
                print('  claimed by:')
                mx = self._claimers._head.successor
                while mx != self._claimers._tail:
                    c = mx.component
                    mx = mx.successor
                    print('    ' + pad(c.name(), 20) +
                        ' quantity=' + str(c._claims[self]))

    def _tryrequest(self):
        mx = self._requesters._head.successor
        while mx != self._requesters._tail:
            if self._minq > (self._capacity - self._claimed_quantity + 1e-8):
                break  # inpossible to honor any more requests
            c = mx.component
            mx = mx.successor
            c._tryrequest()

    def release(self, quantity=omitted):
        '''
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
        quantity may not be specified for a non-anomymous resoure
        '''

        if self._anonymous:
            if quantity is omitted:
                q = self._claimed_quantity
            else:
                q = quantity

            self._claimed_quantity -= q
            if self._claimed_quantity < 1e-8:
                self._claimed_quantity = 0
            self.claimed_quantity.tally()
            self.available_quantity.tally()
            self._tryrequest()

        else:
            if quantity is not omitted:
                raise SalabimError(
                    'no quantity allowed for non-anonymous resource')

            mx = self._claimers._head.successor
            while mx != self._tail:
                c = mx.component
                mx = mx.successor
                c.release(self)

    def requesters(self):
        '''
        Return
        ------
        queue containing all components with not yet honored requests: Queue
        '''
        return self._requesters

    def claimers(self):
        '''
        Returns
        -------
        queue with all components claiming from the resource: Queue
            will be an empty queue for an anonymous resource
        '''
        return self._claimers

    def _get_capacity(self):
        return self._capacity

    def _get_claimed_quantity(self):
        return self._claimed_quantity

    def _get_available_quantity(self):
        return self._capacity - self._claimed_quantity

    def set_capacity(self, cap):
        '''
        Parameters
        ----------
        cap : float or int
            capacity of the resource |n|
            this may lead to honoring one or more requests. |n|
            if omitted, no change
        '''
        self._capacity = cap
        self.capacity.tally()
        self.available_quantity.tally()
        self._tryrequest()

    def name(self, txt=omitted):
        '''
        Parameters
        ----------
        txt : str
            name of the resource |n|
            if txt ends with a period, the name will be serialized |n|
            if omittted, no change

        Returns
        -------
        Name of the resource : str
        '''
        if txt is not omitted:
            _set_name(txt, self.env._nameserializeResource, self)
        return _decode_name(self._name)

    def base_name(self):
        '''
        Returns
        -------
        base name of the resource (the name used at init or name): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the resource : int
            (the sequence number at init or name) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot at the end)
            will be numbered)
        '''
        return self._sequence_number


def colornames():
    return {'': '#00000000', '10%gray': '#191919', '20%gray': '#333333',
     '30%gray': '#464646', '40%gray': '#666666', '50%gray': '#7F7F7F',
     '60%gray': '#999999', '70%gray': '#B2B2B2', '80%gray': '#CCCCCC',
     '90%gray': '#E6E6E6', 'aliceblue': '#F0F8FF', 'antiquewhite': '#FAEBD7',
     'aqua': '#00FFFF', 'aquamarine': '#7FFFD4', 'azure': '#F0FFFF',
     'beige': '#F5F5DC', 'bisque': '#FFE4C4', 'black': '#000000',
     'blanchedalmond': '#FFEBCD', 'blue': '#0000FF', 'blueviolet': '#8A2BE2',
     'brown': '#A52A2A', 'burlywood': '#DEB887', 'cadetblue': '#5F9EA0',
     'chartreuse': '#7FFF00', 'chocolate': '#D2691E', 'coral': '#FF7F50',
     'cornflowerblue': '#6495ED', 'cornsilk': '#FFF8DC', 'crimson': '#DC143C',
     'cyan': '#00FFFF', 'darkblue': '#00008B', 'darkcyan': '#008B8B',
     'darkgoldenrod': '#B8860B', 'darkgray': '#A9A9A9',
     'darkgreen': '#006400', 'darkkhaki': '#BDB76B', 'darkmagenta': '#8B008B',
     'darkolivegreen': '#556B2F', 'darkorange': '#FF8C00',
     'darkorchid': '#9932CC', 'darkred': '#8B0000', 'darksalmon': '#E9967A',
     'darkseagreen': '#8FBC8F', 'darkslateblue': '#483D8B',
     'darkslategray': '#2F4F4F', 'darkturquoise': '#00CED1',
     'darkviolet': '#9400D3', 'deeppink': '#FF1493', 'deepskyblue': '#00BFFF',
     'dimgray': '#696969', 'dodgerblue': '#1E90FF', 'firebrick': '#B22222',
     'floralwhite': '#FFFAF0', 'forestgreen': '#228B22', 'fuchsia': '#FF00FF',
     'gainsboro': '#DCDCDC', 'ghostwhite': '#F8F8FF', 'gold': '#FFD700',
     'goldenrod': '#DAA520', 'gray': '#808080', 'green': '#008000',
     'greenyellow': '#ADFF2F', 'honeydew': '#F0FFF0', 'hotpink': '#FF69B4',
     'indianred': '#CD5C5C', 'indigo': '#4B0082', 'ivory': '#FFFFF0',
     'khaki': '#F0E68C', 'lavender': '#E6E6FA', 'lavenderblush': '#FFF0F5',
     'lawngreen': '#7CFC00', 'lemonchiffon': '#FFFACD',
     'lightblue': '#ADD8E6', 'lightcoral': '#F08080', 'lightcyan': '#E0FFFF',
     'lightgoldenrodyellow': '#FAFAD2', 'lightgray': '#D3D3D3',
     'lightgreen': '#90EE90', 'lightpink': '#FFB6C1',
     'lightsalmon': '#FFA07A', 'lightseagreen': '#20B2AA',
     'lightskyblue': '#87CEFA', 'lightslategray': '#778899',
     'lightsteelblue': '#B0C4DE', 'lightyellow': '#FFFFE0', 'lime': '#00FF00',
     'limegreen': '#32CD32', 'linen': '#FAF0E6', 'magenta': '#FF00FF',
     'maroon': '#800000', 'mediumaquamarine': '#66CDAA',
     'mediumblue': '#0000CD', 'mediumorchid': '#BA55D3',
     'mediumpurple': '#9370DB', 'mediumseagreen': '#3CB371',
     'mediumslateblue': '#7B68EE', 'mediumspringgreen': '#00FA9A',
     'mediumturquoise': '#48D1CC', 'mediumvioletred': '#C71585',
     'midnightblue': '#191970', 'mintcream': '#F5FFFA',
     'mistyrose': '#FFE4E1', 'moccasin': '#FFE4B5', 'navajowhite': '#FFDEAD',
     'navy': '#000080', 'none': '#00000000', 'oldlace': '#FDF5E6',
     'olive': '#808000', 'olivedrab': '#6B8E23', 'orange': '#FFA500',
     'orangered': '#FF4500', 'orchid': '#DA70D6', 'palegoldenrod': '#EEE8AA',
     'palegreen': '#98FB98', 'paleturquoise': '#AFEEEE',
     'palevioletred': '#DB7093', 'papayawhip': '#FFEFD5',
     'peachpuff': '#FFDAB9', 'peru': '#CD853F', 'pink': '#FFC0CB',
     'plum': '#DDA0DD', 'powderblue': '#B0E0E6', 'purple': '#800080',
     'red': '#FF0000', 'rosybrown': '#BC8F8F', 'royalblue': '#4169E1',
     'saddlebrown': '#8B4513', 'salmon': '#FA8072', 'sandybrown': '#FAA460',
     'seagreen': '#2E8B57', 'seashell': '#FFF5EE', 'sienna': '#A0522D',
     'silver': '#C0C0C0', 'skyblue': '#87CEEB', 'slateblue': '#6A5ACD',
     'slategray': '#708090', 'snow': '#FFFAFA', 'springgreen': '#00FF7F',
     'steelblue': '#4682B4', 'tan': '#D2B48C', 'teal': '#008080',
     'thistle': '#D8BFD8', 'tomato': '#FF6347', 'transparent': '#00000000',
     'turquoise': '#40E0D0', 'violet': '#EE82EE', 'wheat': '#F5DEB3',
     'white': '#FFFFFF', 'whitesmoke': '#F5F5F5', 'yellow': '#FFFF00',
     'yellowgreen': '#9ACD32'}


def colorspec_to_tuple(colorspec):
    if isinstance(colorspec, (tuple, list)):
        if len(colorspec) == 2:
            c = colorspec_to_tuple(colorspec[0])
            return (c[0], c[1], c[2], colorspec[1])
        elif len(colorspec) == 3:
            return (colorspec[0], colorspec[1], colorspec[2], 255)
        elif len(colorspec) == 4:
            return colorspec
    else:
        if (colorspec != '') and (colorspec[0]) == '#':
            if len(colorspec) == 7:
                return (int(colorspec[1:3], 16), int(colorspec[3:5], 16),
                        int(colorspec[5:7], 16))
            elif len(colorspec) == 9:
                return (int(colorspec[1:3], 16), int(colorspec[3:5], 16),
                        int(colorspec[5:7], 16), int(colorspec[7:9], 16))
        else:
            s = colorspec.split('#')
            if len(s) == 2:
                alpha = s[1]
                colorspec = s[0]
            else:
                alpha = 'FF'
            colorhex = colornames()[colorspec.replace(' ', '').lower()]
            if len(colorhex) == 7:
                colorhex = colorhex + alpha
            return colorspec_to_tuple(colorhex)
    raise SalabimError('wrong spec for color')


def hex_to_rgb(v):
    if v == '':
        return(0, 0, 0, 0)
    if v[0] == '#':
        v = v[1:]
    if len(v) == 6:
        return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    if len(v) == 8:
        return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16), int(v[6:8], 16)
    raise SalabimError('Incorrect value' + str(v))


def colorspec_to_hex(colorspec, withalpha=True):
    v = colorspec_to_tuple(colorspec)
    if withalpha:
        return '#{:02x}{:02x}{:02x}{:02x}'.\
            format(int(v[0]), int(v[1]), int(v[2]), int(v[3]))
    else:
        return '#{:02x}{:02x}{:02x}'.\
            format(int(v[0]), int(v[1]), int(v[2]))


def spec_to_image(image):
    if isinstance(image, str):
        im = Image.open(image)
        im = im.convert('RGBA')
        return im
    else:
        return image


def _i(p, v0, v1):
    if v0 == v1:
        v = v0  # avoid rounding problems
    v = (1 - p) * v0 + p * v1
    return v


def colorinterpolate(t, t0, t1, v0, v1):
    '''
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
    f(t) : float

    Note
    ----
    Note that no extrapolation is done, i.e f(t)=v0 for t<t0 and f(t)=v1 for
    t>t1. |n|
    This function is heavily used during animation.
    '''
    vt0 = colorspec_to_tuple(v0)
    vt1 = colorspec_to_tuple(v1)
    return tuple(int(c) for c in interpolate(t, t0, t1, vt0, vt1))


def interpolate(t, t0, t1, v0, v1):
    '''
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
    f(t) : float or tuple

    Note
    ----
    Note that no extrapolation is done, i.e f(t)=v0 for t<t0 and f(t)=v1 for
    t>t1. |n|
    This function is used during animation.
    '''
    if (v0 is None) or (v1 is None):
        return None
    if t0 == t1:
        return v1
    if t0 > t1:
        (t0, t1) = (t1, t0)
        (v0, v1) = (v1, v0)
    if t <= t0:
        return v0
    if t >= t1:
        return v1
    if t1 == inf:
        return v0
    p = (0.0 + t - t0) / (t1 - t0)
    if isinstance(v0, (list, tuple)):
        return tuple((_i(p, x0, x1) for x0, x1 in zip(v0, v1)))
    else:
        return _i(p, v0, v1)


def clocktext(t):
    s = ''
    if (not an_env.paused) or (int(time.time() * 2) % 2 == 0):

        if (not an_env.paused) and an_env.show_fps:
            if len(an_env.frametimes) >= 2:
                fps = (len(an_env.frametimes) - 1) / \
                    (an_env.frametimes[-1] - an_env.frametimes[0])
            else:
                fps = 0
            s += 'fps={:.1f}'.format(fps)
        if an_env.show_speed:
            if s != '':
                s += ' '
            s += '*{:.3f}'.format(an_env.speed)
        if an_env.show_time:
            if s != '':
                s += ' '
            s += 't={:.3f}'.format(t)
    return s


def pausetext():
    if an_env.paused:
        return 'Resume'
    else:
        return 'Pause'


def tracetext():
    if an_env._trace:
        return 'Trace off'
    else:
        return 'Trace on'


def _set_name(name, _nameserialize, object):
    oldname = getattr(object, '_base_name', None)
    if isinstance(name, tuple):
        auto = False
    else:
        auto = (('*' + name)[-1] == '.')  # * added to allow for null string

    if name in _nameserialize:
        sequence_number, object0 = _nameserialize[name]
        sequence_number += 1
        _nameserialize[name] = sequence_number, None
    else:
        sequence_number = 0
        _nameserialize[name] = sequence_number, (object if auto else None)

    if auto:
        if sequence_number == 0:
            newname = name[:-1]
        else:
            if sequence_number == 1:
                if object0._base_name == name:
                    newname0 = name + str(0)
                    object0.env.print_trace(
                        '', '', object0._name + ' rename to ' + newname0)
                    object0._name = newname0
            newname = name + str(sequence_number)
    else:
        newname = name
    if (oldname is not None) and (_nameserialize != Environment._nameserialize):
        object.env.print_trace('', '', oldname + ' rename to', newname)
    object._name = newname
    object._base_name = name
    object._sequence_number = sequence_number


def _decode_name(name):
    if isinstance(name, tuple):
        return name[0] + name[1].name()
    else:
        return name


def pad(txt, n):
    if n <= 0:
        return ''
    else:
        return txt.ljust(n)[:n]


def rpad(txt, n):
    return txt.rjust(n)[:n]


def fn(x, l, d):
    if math.isnan(x):
        return ('{:' + str(l) + 's}').format('')
    if x >= 10**(l - d - 1):
        return ('{:' + str(l) + '.' + str(l - d - 3) + 'e}').format(x)
    if x == int(x):
        return ('{:' + str(l - d - 1) + 'd}{:' + str(d + 1) + 's}').format(int(x), '')
    return ('{:' + str(l) + '.' + str(d) + 'f}').format(x)


def type_to_typecode_off(type):
    lookup = {
        'bool': ('B', 255),
        'int8': ('b', -128),
        'uint8': ('B', 255),
        'int16': ('h', -32768),
        'uint16': ('H', 65535),
        'int32': ('i', -2147483648),
        'uint32': ('I', 4294967295),
        'int64': ('l', -9223372036854775808),
        'uint64': ('L', 18446744073709551615),
        'float': ('d', -inf),
        'double': ('d', -inf),
        'any': ('', -inf)
        }
    return lookup[type]


def list_to_array(l):
    float_result = array.array('d')
    int_result = array.array('l')
    int_ok = True
    for v in l:
        try:
            vfloat = float(v)
        except:
            vfloat = 0
        float_result.append(vfloat)
        if int_ok:
            try:
                vint = int(v)
            except:
                vint = 0
            if vint == vfloat:
                try:
                    int_result.append(vint)  # this may fail in case of a too large value
                except:
                    int_ok = False
            else:
                int_ok = False

    if int_ok:
        return int_result
    else:
        return float_result


def normalize(s):
    res = ''
    for c in s.upper():
        if (c.isalpha() or c.isdigit()):
            res = res + c
    return res


def time_to_string(t):
    if t == inf:
        s = 'inf'
    else:
        s = '{:10.3f}'.format(t)
    return rpad(s, 10)


def _urgenttxt(urgent):
    if urgent:
        return ' urgent'
    else:
        return ''


def _modetxt(mode):
    if mode is None:
        return ''
    else:
        return ' mode=' + str(mode)


def data():
    return 'data'


def current():
    return 'current'


def standby():
    return 'standby'


def passive():
    return 'passive'


def scheduled():
    return 'scheduled'


def requesting():
    return 'requesting'


def waiting():
    return 'waiting'


def random_seed(seed, randomstream=omitted):
    '''
    Parameters
    ----------
    seed : hashable object, usually int
        the seed for random, equivalent to random.seed() |n|
        if None, a purely random value (based on the current time) will be used
        (not reproducable) |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''
    if randomstream is omitted:
        randomstream = random
    randomstream.seed(seed)


def pythonistacolor(c):
    return (c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255)


def _std_fonts():
    # the names of the standard fonts are generated by ttf fontdict.py on the standard development machine
    return {'18cents': '18thCentury', 'Acme____': 'AcmeFont',
     'AGENCYB': 'Agency FB Bold', 'AGENCYR': 'Agency FB',
     'Alfredo_': 'Alfredo', 'ALGER': 'Algerian',
     'aliee13': 'Alien Encounters', 'almosnow': 'Almonte Snow',
     'Ameth___': 'Amethyst', 'ANTIC___': 'AnticFont',
     'ANTQUAB': 'Book Antiqua Bold', 'ANTQUABI': 'Book Antiqua Bold Italic',
     'ANTQUAI': 'Book Antiqua Italic',
     'ArchitectsDaughter': 'Architects Daughter', 'arial': 'Arial',
     'arialbd': 'Arial Bold', 'arialbi': 'Arial Bold Italic',
     'ariali': 'Arial Italic', 'ARIALN': 'Arial Narrow',
     'ARIALNB': 'Arial Narrow Bold', 'ARIALNBI': 'Arial Narrow Bold Italic',
     'ARIALNI': 'Arial Narrow Italic', 'ARIALUNI': 'Arial Unicode MS',
     'ariblk': 'Arial Black', 'ARLRDBD': 'Arial Rounded MT Bold',
     'asimov': 'Asimov', 'Autumn__': 'Autumn', 'babyk___': 'Baby Kruffy',
     'BALTH___': 'Balthazar', 'BASKVILL': 'Baskerville Old Face',
     'BASTION_': 'Bastion', 'BAUHS93': 'Bauhaus 93', 'BELL': 'Bell MT',
     'BELLB': 'Bell MT Bold', 'BELLI': 'Bell MT Italic',
     'BERNHC': 'Bernard MT Condensed', 'bgothl': 'BankGothic Lt BT Light',
     'bgothm': 'BankGothic Md BT Medium', 'BKANT': 'Book Antiqua',
     'Blackout-2am': 'Blackout 2 AM', 'bnjinx': 'BN Jinx',
     'bnmachine': 'BN Machine', 'bobcat': 'Bobcat Normal',
     'BOD_B': 'Bodoni MT Bold', 'BOD_BI': 'Bodoni MT Bold Italic',
     'BOD_BLAI': 'Bodoni MT Black Italic', 'BOD_BLAR': 'Bodoni MT Black',
     'BOD_CB': 'Bodoni MT Condensed Bold',
     'BOD_CBI': 'Bodoni MT Condensed Bold Italic',
     'BOD_CI': 'Bodoni MT Condensed Italic', 'BOD_CR': 'Bodoni MT Condensed',
     'BOD_I': 'Bodoni MT Italic', 'BOD_PSTC': 'Bodoni MT Poster Compressed',
     'BOD_R': 'Bodoni MT', 'Bolstbo_': 'BolsterBold Bold',
     'BOOKOS': 'Bookman Old Style', 'BOOKOSB': 'Bookman Old Style Bold',
     'BOOKOSBI': 'Bookman Old Style Bold Italic',
     'BOOKOSI': 'Bookman Old Style Italic', 'Borea___': 'Borealis',
     'BOUTON_International_symbols': 'BOUTON International Symbols',
     'BRADHITC': 'Bradley Hand ITC', 'Brand___': 'Brandish',
     'BRITANIC': 'Britannic Bold', 'BRLNSB': 'Berlin Sans FB Bold',
     'BRLNSDB': 'Berlin Sans FB Demi Bold', 'BRLNSR': 'Berlin Sans FB',
     'BROADW': 'Broadway', 'BRUSHSCI': 'Brush Script MT Italic',
     'Bruss___': 'Brussels', 'BSSYM7': 'Bookshelf Symbol 7',
     'CabinSketch-Bold': 'CabinSketch Bold', 'calibri': 'Calibri',
     'calibrib': 'Calibri Bold', 'calibrii': 'Calibri Italic',
     'calibril': 'Calibri Light', 'calibrili': 'Calibri Light Italic',
     'calibriz': 'Calibri Bold Italic', 'CALIFB': 'Californian FB Bold',
     'CALIFI': 'Californian FB Italic', 'CALIFR': 'Californian FB',
     'CALIST': 'Calisto MT', 'CALISTB': 'Calisto MT Bold',
     'CALISTBI': 'Calisto MT Bold Italic', 'CALISTI': 'Calisto MT Italic',
     'CALLI___': 'Calligraphic', 'CALVIN__': 'Calvin',
     'cambriab': 'Cambria Bold', 'cambriai': 'Cambria Italic',
     'cambriaz': 'Cambria Bold Italic', 'Candara': 'Candara',
     'Candarab': 'Candara Bold', 'Candarai': 'Candara Italic',
     'Candaraz': 'Candara Bold Italic', 'candles_': 'Candles',
     'CASTELAR': 'Castellar', 'CENSCBK': 'Century Schoolbook',
     'CENTAUR': 'Centaur', 'CENTURY': 'Century', 'CHILLER': 'Chiller',
     'chinyen': 'Chinyen Normal', 'cityb___': 'CityBlueprint',
     'CLARE___': 'Clarendon', 'Colbert_': 'Colbert', 'COLONNA': 'Colonna MT',
     'Comfortaa-Bold': 'Comfortaa Bold', 'Comfortaa-Light': 'Comfortaa Light',
     'Comfortaa-Regular': 'Comfortaa', 'comic': 'Comic Sans MS',
     'comicbd': 'Comic Sans MS Bold', 'comici': 'Comic Sans MS Italic',
     'comicz': 'Comic Sans MS Bold Italic', 'COMMONS_': 'Commons',
     'compi': 'CommercialPi BT', 'complex_': 'Complex',
     'comsc': 'CommercialScript BT', 'consola': 'Consolas',
     'consolab': 'Consolas Bold', 'consolai': 'Consolas Italic',
     'consolaz': 'Consolas Bold Italic', 'constan': 'Constantia',
     'constanb': 'Constantia Bold', 'constani': 'Constantia Italic',
     'constanz': 'Constantia Bold Italic', 'Cools___': 'Coolsville',
     'COOPBL': 'Cooper Black', 'COPRGTB': 'Copperplate Gothic Bold',
     'COPRGTL': 'Copperplate Gothic Light', 'corbel': 'Corbel',
     'corbelb': 'Corbel Bold', 'corbeli': 'Corbel Italic',
     'corbelz': 'Corbel Bold Italic', 'Corpo___': 'Corporate',
     'counb___': 'CountryBlueprint', 'cour': 'Courier New',
     'courbd': 'Courier New Bold', 'courbi': 'Courier New Bold Italic',
     'couri': 'Courier New Italic', 'cracj___': 'Cracked Johnnie',
     'creerg__': 'Creepygirl', 'CreteRound-Italic': 'Crete Round Italic',
     'CreteRound-Regular': 'Crete Round', 'CURLZ___': 'Curlz MT',
     'DAYTON__': 'Dayton', 'DejaVuSansMono': 'DejaVu Sans Mono Book',
     'DejaVuSansMono-Bold': 'DejaVu Sans Mono Bold',
     'DejaVuSansMono-BoldOblique': 'DejaVu Sans Mono Bold Oblique',
     'DejaVuSansMono-Oblique': 'DejaVu Sans Mono Oblique',
     'Deneane_': 'Deneane', 'Detente_': 'Detente',
     'digifit': 'Digifit Normal', 'distant galaxy 2': 'Distant Galaxy',
     'DOMIN___': 'Dominican', 'dutch': 'Dutch801 Rm BT Roman',
     'dutchb': 'Dutch801 Rm BT Bold', 'dutchbi': 'Dutch801 Rm BT Bold Italic',
     'dutcheb': 'Dutch801 XBd BT Extra Bold',
     'dutchi': 'Dutch801 Rm BT Italic', 'ebrima': 'Ebrima',
     'ebrimabd': 'Ebrima Bold', 'ELEPHNT': 'Elephant',
     'ELEPHNTI': 'Elephant Italic', 'Emmett__': 'Emmett',
     'ENGR': 'Engravers MT', 'Enliven_': 'Enliven', 'ERASBD': 'Eras Bold ITC',
     'ERASDEMI': 'Eras Demi ITC', 'ERASLGHT': 'Eras Light ITC',
     'ERASMD': 'Eras Medium ITC', 'ethnocen': 'Ethnocentric',
     'eurro___': 'EuroRoman Oblique', 'eurr____': 'EuroRoman',
     'FELIXTI': 'Felix Titling', 'fingerpop2': 'Fingerpop',
     'flubber': 'Flubber', 'FORTE': 'Forte', 'FRABK': 'Franklin Gothic Book',
     'FRABKIT': 'Franklin Gothic Book Italic',
     'FRADM': 'Franklin Gothic Demi', 'FRADMCN': 'Franklin Gothic Demi Cond',
     'FRADMIT': 'Franklin Gothic Demi Italic',
     'FRAHV': 'Franklin Gothic Heavy',
     'FRAHVIT': 'Franklin Gothic Heavy Italic',
     'framd': 'Franklin Gothic Medium',
     'FRAMDCN': 'Franklin Gothic Medium Cond',
     'framdit': 'Franklin Gothic Medium Italic',
     'FREESCPT': 'Freestyle Script', 'Frnkvent': 'Frankfurter Venetian TT',
     'FRSCRIPT': 'French Script MT', 'FTLTLT': 'Footlight MT Light',
     'Gabriola': 'Gabriola', 'gadugi': 'Gadugi', 'gadugib': 'Gadugi Bold',
     'GARA': 'Garamond', 'GARABD': 'Garamond Bold',
     'GARAIT': 'Garamond Italic', 'gazzarelli': 'Gazzarelli',
     'gdt_____': 'GDT', 'georgia': 'Georgia', 'georgiab': 'Georgia Bold',
     'georgiai': 'Georgia Italic', 'georgiaz': 'Georgia Bold Italic',
     'Geotype': 'Geotype TT', 'GIGI': 'Gigi',
     'GILBI___': 'Gill Sans MT Bold Italic', 'GILB____': 'Gill Sans MT Bold',
     'GILC____': 'Gill Sans MT Condensed', 'GILI____': 'Gill Sans MT Italic',
     'GILLUBCD': 'Gill Sans Ultra Bold Condensed',
     'GILSANUB': 'Gill Sans Ultra Bold', 'GIL_____': 'Gill Sans MT',
     'GLECB': 'Gloucester MT Extra Condensed', 'Glock___': 'Glockenspiel',
     'GLSNECB': 'Gill Sans MT Ext Condensed Bold', 'goodtime': 'Good Times',
     'GOTHIC': 'Century Gothic', 'GOTHICB': 'Century Gothic Bold',
     'GOTHICBI': 'Century Gothic Bold Italic', 'gothice_': 'GothicE',
     'gothicg_': 'GothicG', 'GOTHICI': 'Century Gothic Italic',
     'gothici_': 'GothicI', 'GOUDOS': 'Goudy Old Style',
     'GOUDOSB': 'Goudy Old Style Bold', 'GOUDOSI': 'Goudy Old Style Italic',
     'GOUDYSTO': 'Goudy Stout', 'greekc__': 'GreekC', 'greeks__': 'GreekS',
     'Greek_i': 'Greek Diner Inline TT', 'handmeds': 'Hand Me Down S (BRK)',
     'Hansen__': 'Hansen', 'HARLOWSI': 'Harlow Solid Italic Italic',
     'HARNGTON': 'Harrington', 'HARVEIT_': 'HarvestItal',
     'HARVEST_': 'Harvest', 'HATTEN': 'Haettenschweiler',
     'Haxton': 'Haxton Logos TT', 'heavyhea2': 'Heavy Heap',
     'himalaya': 'Microsoft Himalaya', 'hollh___': 'Hollywood Hills',
     'holomdl2': 'HoloLens MDL2 Assets', 'Hombre__': 'Hombre',
     'HTOWERT': 'High Tower Text', 'HTOWERTI': 'High Tower Text Italic',
     'Huxley_Titling': 'Huxley Titling', 'impact': 'Impact',
     'IMPRISHA': 'Imprint MT Shadow', 'inductio': 'Induction Normal',
     'INFROMAN': 'Informal Roman', 'isocp2__': 'ISOCP2', 'isocp3__': 'ISOCP3',
     'isocpeui': 'ISOCPEUR Italic', 'isocpeur': 'ISOCPEUR',
     'isocp___': 'ISOCP', 'isoct2__': 'ISOCT2', 'isoct3__': 'ISOCT3',
     'isocteui': 'ISOCTEUR Italic', 'isocteur': 'ISOCTEUR',
     'isoct___': 'ISOCT', 'italicc_': 'ItalicC', 'italict_': 'ItalicT',
     'italic__': 'Italic', 'Itali___': 'Italianate',
     'ITCBLKAD': 'Blackadder ITC', 'ITCEDSCR': 'Edwardian Script ITC',
     'ITCKRIST': 'Kristen ITC', 'javatext': 'Javanese Text',
     'JOKERMAN': 'Jokerman', 'JosefinSlab-Bold': 'Josefin Slab Bold',
     'JosefinSlab-BoldItalic': 'Josefin Slab Bold Italic',
     'JosefinSlab-Italic': 'Josefin Slab Italic',
     'JosefinSlab-Light': 'Josefin Slab Light',
     'JosefinSlab-LightItalic': 'Josefin Slab Light Italic',
     'JosefinSlab-Regular': 'Josefin Slab',
     'JosefinSlab-SemiBold': 'Josefin Slab SemiBold',
     'JosefinSlab-SemiBoldItalic': 'Josefin Slab SemiBold Italic',
     'JosefinSlab-Thin': 'Josefin Slab Thin',
     'JosefinSlab-ThinItalic': 'Josefin Slab Thin Italic',
     'JUICE___': 'Juice ITC', 'KUNSTLER': 'Kunstler Script',
     'LATINWD': 'Wide Latin', 'Lato-Black': 'Lato Black',
     'Lato-BlackItalic': 'Lato Black Italic', 'Lato-Bold': 'Lato Bold',
     'Lato-BoldItalic': 'Lato Bold Italic', 'Lato-Hairline': 'Lato Hairline',
     'Lato-HairlineItalic': 'Lato Hairline Italic',
     'Lato-Italic': 'Lato Italic', 'Lato-Light': 'Lato Light',
     'Lato-LightItalic': 'Lato Light Italic', 'Lato-Regular': 'Lato',
     'LBRITE': 'Lucida Bright', 'LBRITED': 'Lucida Bright Demibold',
     'LBRITEDI': 'Lucida Bright Demibold Italic',
     'LBRITEI': 'Lucida Bright Italic',
     'LCALLIG': 'Lucida Calligraphy Italic', 'LeelaUIb': 'Leelawadee UI Bold',
     'LEELAWAD': 'Leelawadee', 'LEELAWDB': 'Leelawadee Bold',
     'LeelawUI': 'Leelawadee UI', 'LeelUIsl': 'Leelawadee UI Semilight',
     'LFAX': 'Lucida Fax', 'LFAXD': 'Lucida Fax Demibold',
     'LFAXDI': 'Lucida Fax Demibold Italic', 'LFAXI': 'Lucida Fax Italic',
     'LHANDW': 'Lucida Handwriting Italic', 'Limou___': 'Limousine',
     'littlelo': 'LittleLordFontleroy', 'LSANS': 'Lucida Sans',
     'LSANSD': 'Lucida Sans Demibold Roman',
     'LSANSDI': 'Lucida Sans Demibold Italic', 'LSANSI': 'Lucida Sans Italic',
     'ltromatic': 'LetterOMatic!', 'LTYPE': 'Lucida Sans Typewriter',
     'LTYPEB': 'Lucida Sans Typewriter Bold',
     'LTYPEBO': 'Lucida Sans Typewriter Bold Oblique',
     'LTYPEO': 'Lucida Sans Typewriter Oblique', 'lucon': 'Lucida Console',
     'l_10646': 'Lucida Sans Unicode', 'mael____': 'Mael',
     'MAGNETOB': 'Magneto Bold', 'MAIAN': 'Maiandra GD',
     'malgun': 'Malgun Gothic', 'malgunbd': 'Malgun Gothic Bold',
     'malgunsl': 'Malgun Gothic Semilight', 'Manorly_': 'Manorly',
     'marlett': 'Marlett', 'marlett_0': 'Marlett', 'Martina_': 'Martina',
     'MATURASC': 'Matura MT Script Capitals', 'Melodbo_': 'MelodBold Bold',
     'micross': 'Microsoft Sans Serif', 'Minerva_': 'Minerva',
     'MISTRAL': 'Mistral', 'mmrtext': 'Myanmar Text',
     'mmrtextb': 'Myanmar Text Bold', 'MOD20': 'Modern No. 20',
     'monbaiti': 'Mongolian Baiti', 'monos': 'Monospac821 BT Roman',
     'monosb': 'Monospac821 BT Bold', 'monosbi': 'Monospac821 BT Bold Italic',
     'monosi': 'Monospac821 BT Italic', 'monotxt_': 'Monotxt',
     'MOONB___': 'Moonbeam', 'mplus-1m-bold': 'M+ 1m bold',
     'mplus-1m-light': 'M+ 1m light', 'mplus-1m-medium': 'M+ 1m medium',
     'mplus-1m-regular': 'M+ 1m', 'mplus-1m-thin': 'M+ 1m thin',
     'MSUIGHUB': 'Microsoft Uighur Bold', 'MSUIGHUR': 'Microsoft Uighur',
     'msyi': 'Microsoft Yi Baiti', 'MTCORSVA': 'Monotype Corsiva',
     'MTEXTRA': 'MT Extra', 'mtproxy1': 'Proxy 1', 'mtproxy2': 'Proxy 2',
     'mtproxy3': 'Proxy 3', 'mtproxy4': 'Proxy 4', 'mtproxy5': 'Proxy 5',
     'mtproxy6': 'Proxy 6', 'mtproxy7': 'Proxy 7', 'mtproxy8': 'Proxy 8',
     'mtproxy9': 'Proxy 9', 'mvboli': 'MV Boli', 'Mycalc__': 'Mycalc',
     'narrow': 'PR Celtic Narrow Normal', 'nasaliza': 'Nasalization Medium',
     'neon2': 'Neon Lights', 'NIAGENG': 'Niagara Engraved',
     'NIAGSOL': 'Niagara Solid', 'Nirmala': 'Nirmala UI',
     'NirmalaB': 'Nirmala UI Bold', 'NirmalaS': 'Nirmala UI Semilight',
     'nobile': 'Nobile', 'nobile_bold': 'Nobile Bold',
     'nobile_bold_italic': 'Nobile Bold Italic',
     'nobile_italic': 'Nobile Italic', 'Notram__': 'Notram',
     'Novem___': 'November', 'ntailu': 'Microsoft New Tai Lue',
     'ntailub': 'Microsoft New Tai Lue Bold', 'Nunito-Light': 'Nunito Light',
     'Nunito-Regular': 'Nunito', 'OCRAEXT': 'OCR A Extended',
     'OLDENGL': 'Old English Text MT', 'ONYX': 'Onyx',
     'Opinehe_': 'OpineHeavy', 'ostrich-black': 'Ostrich Sans Black',
     'ostrich-bold': 'Ostrich Sans Bold',
     'ostrich-dashed': 'Ostrich Sans Dashed Medium',
     'ostrich-light': 'Ostrich Sans Condensed Light',
     'ostrich-regular': 'Ostrich Sans Medium',
     'ostrich-rounded': 'Ostrich Sans Rounded Medium',
     'OUTLOOK': 'MS Outlook', 'Pacifico': 'Pacifico',
     'pala': 'Palatino Linotype', 'palab': 'Palatino Linotype Bold',
     'palabi': 'Palatino Linotype Bold Italic',
     'palai': 'Palatino Linotype Italic', 'PALSCRI': 'Palace Script MT',
     'panroman': 'PanRoman', 'PAPYRUS': 'Papyrus', 'PARCHM': 'Parchment',
     'parryhotter': 'Parry Hotter', 'PENLIIT_': 'PenultimateLightItal',
     'PENULLI_': 'PenultimateLight', 'PENUL___': 'Penultimate',
     'PERBI___': 'Perpetua Bold Italic', 'PERB____': 'Perpetua Bold',
     'PERI____': 'Perpetua Italic', 'PermanentMarker': 'Permanent Marker',
     'PERTIBD': 'Perpetua Titling MT Bold',
     'PERTILI': 'Perpetua Titling MT Light', 'PER_____': 'Perpetua',
     'phagspa': 'Microsoft PhagsPa', 'phagspab': 'Microsoft PhagsPa Bold',
     'Phrasme_': 'PhrasticMedium', 'Pirate__': 'Pirate',
     'PLAYBILL': 'Playbill', 'POORICH': 'Poor Richard',
     'PRISTINA': 'Pristina', 'QUIVEIT_': 'QuiverItal', 'RAGE': 'Rage Italic',
     'RAVIE': 'Ravie', 'REFSAN': 'MS Reference Sans Serif',
     'REFSPCL': 'MS Reference Specialty',
     'ROCCB___': 'Rockwell Condensed Bold', 'ROCC____': 'Rockwell Condensed',
     'ROCK': 'Rockwell', 'ROCKB': 'Rockwell Bold',
     'ROCKBI': 'Rockwell Bold Italic', 'ROCKEB': 'Rockwell Extra Bold',
     'ROCKI': 'Rockwell Italic', 'Roland__': 'Roland',
     'romab___': 'Romantic Bold', 'romai___': 'Romantic Italic',
     'romanc__': 'RomanC', 'romand__': 'RomanD', 'romans__': 'RomanS',
     'romantic': 'Romantic', 'romant__': 'RomanT', 'RONDALO_': 'Rondalo',
     'Rowdyhe_': 'RowdyHeavy', 'Russrite': 'Russel Write TT',
     'Salina__': 'Salina', 'SamsungIF_Md': 'Samsung InterFace Medium',
     'SamsungIF_Md_0': 'Samsung InterFace Medium',
     'SamsungIF_Rg': 'Samsung InterFace',
     'SamsungIF_Rg_0': 'Samsung InterFace',
     'sanssbo_': 'SansSerif BoldOblique', 'sanssb__': 'SansSerif Bold',
     'sansso__': 'SansSerif Oblique', 'sanss___': 'SansSerif',
     'SCHLBKB': 'Century Schoolbook Bold',
     'SCHLBKBI': 'Century Schoolbook Bold Italic',
     'SCHLBKI': 'Century Schoolbook Italic', 'SCRIPTBL': 'Script MT Bold',
     'scriptc_': 'ScriptC', 'scripts_': 'ScriptS',
     'segmdl2': 'Segoe MDL2 Assets', 'segoepr': 'Segoe Print',
     'segoeprb': 'Segoe Print Bold', 'segoesc': 'Segoe Script',
     'segoescb': 'Segoe Script Bold', 'segoeui': 'Segoe UI',
     'segoeuib': 'Segoe UI Bold', 'segoeuii': 'Segoe UI Italic',
     'segoeuil': 'Segoe UI Light', 'segoeuisl': 'Segoe UI Semilight',
     'segoeuiz': 'Segoe UI Bold Italic', 'seguibl': 'Segoe UI Black',
     'seguibli': 'Segoe UI Black Italic', 'seguiemj': 'Segoe UI Emoji',
     'seguihis': 'Segoe UI Historic', 'seguili': 'Segoe UI Light Italic',
     'seguisb': 'Segoe UI Semibold', 'seguisbi': 'Segoe UI Semibold Italic',
     'seguisli': 'Segoe UI Semilight Italic', 'seguisym': 'Segoe UI Symbol',
     'sf movie poster2': 'SF Movie Poster', 'SHOWG': 'Showcard Gothic',
     'simplex_': 'Simplex', 'simsunb': 'SimSun-ExtB', 'Skinny__': 'Skinny',
     'SNAP____': 'Snap ITC', 'snowdrft': 'Snowdrift', 'SPLASH__': 'Splash',
     'STENCIL': 'Stencil', 'Stephen_': 'Stephen', 'Steppes': 'Steppes TT',
     'stylu': 'Stylus BT Roman', 'supef___': 'SuperFrench',
     'swiss': 'Swis721 BT Roman', 'swissb': 'Swis721 BT Bold',
     'swissbi': 'Swis721 BT Bold Italic', 'swissbo': 'Swis721 BdOul BT Bold',
     'swissc': 'Swis721 Cn BT Roman', 'swisscb': 'Swis721 Cn BT Bold',
     'swisscbi': 'Swis721 Cn BT Bold Italic',
     'swisscbo': 'Swis721 BdCnOul BT Bold Outline',
     'swissci': 'Swis721 Cn BT Italic', 'swissck': 'Swis721 BlkCn BT Black',
     'swisscki': 'Swis721 BlkCn BT Black Italic',
     'swisscl': 'Swis721 LtCn BT Light',
     'swisscli': 'Swis721 LtCn BT Light Italic',
     'swisse': 'Swis721 Ex BT Roman', 'swisseb': 'Swis721 Ex BT Bold',
     'swissek': 'Swis721 BlkEx BT Black', 'swissel': 'Swis721 LtEx BT Light',
     'swissi': 'Swis721 BT Italic', 'swissk': 'Swis721 Blk BT Black',
     'swisski': 'Swis721 Blk BT Black Italic',
     'swissko': 'Swis721 BlkOul BT Black', 'swissl': 'Swis721 Lt BT Light',
     'swissli': 'Swis721 Lt BT Light Italic', 'Swkeys1': 'SWGamekeys MT',
     'syastro_': 'Syastro', 'sylfaen': 'Sylfaen', 'symap___': 'Symap',
     'symath__': 'Symath', 'symbol': 'Symbol', 'symeteo_': 'Symeteo',
     'symusic_': 'Symusic', 'tahoma': 'Tahoma', 'tahomabd': 'Tahoma Bold',
     'taile': 'Microsoft Tai Le', 'taileb': 'Microsoft Tai Le Bold',
     'Tangerine_Bold': 'Tangerine Bold', 'Tangerine_Regular': 'Tangerine',
     'Tarzan__': 'Tarzan', 'TCBI____': 'Tw Cen MT Bold Italic',
     'TCB_____': 'Tw Cen MT Bold', 'TCCB____': 'Tw Cen MT Condensed Bold',
     'TCCEB': 'Tw Cen MT Condensed Extra Bold',
     'TCCM____': 'Tw Cen MT Condensed', 'TCMI____': 'Tw Cen MT Italic',
     'TCM_____': 'Tw Cen MT', 'techb___': 'TechnicBold',
     'techl___': 'TechnicLite', 'technic_': 'Technic',
     'TEMPSITC': 'Tempus Sans ITC', 'terminat': 'Terminator Two',
     'times': 'Times New Roman', 'timesbd': 'Times New Roman Bold',
     'timesbi': 'Times New Roman Bold Italic',
     'timesi': 'Times New Roman Italic', 'Toledo__': 'Toledo',
     'trebuc': 'Trebuchet MS', 'trebucbd': 'Trebuchet MS Bold',
     'trebucbi': 'Trebuchet MS Bold Italic',
     'trebucit': 'Trebuchet MS Italic', 'txt_____': 'Txt',
     'umath': 'UniversalMath1 BT', 'VALKEN__': 'Valken', 'verdana': 'Verdana',
     'verdanab': 'Verdana Bold', 'verdanai': 'Verdana Italic',
     'verdanaz': 'Verdana Bold Italic', 'VINERITC': 'Viner Hand ITC',
     'vinet': 'Vineta BT', 'VIVALDII': 'Vivaldi Italic', 'Vivian__': 'Vivian',
     'VLADIMIR': 'Vladimir Script', 'Vollkorn-Bold': 'Vollkorn Bold',
     'Vollkorn-BoldItalic': 'Vollkorn Bold Italic',
     'Vollkorn-Italic': 'Vollkorn Italic', 'Vollkorn-Regular': 'Vollkorn',
     'Waverly_': 'Waverly', 'webdings': 'Webdings', 'Whimsy': 'Whimsy TT',
     'wingding': 'Wingdings', 'WINGDNG2': 'Wingdings 2',
     'WINGDNG3': 'Wingdings 3', 'woodcut': 'Woodcut', 'xfiles': 'X-Files',
     'yearsupplyoffairycakes': 'Year supply of fairy cakes'}


def fonts():
    if not hasattr(fonts, 'font_list'):
        fonts.font_list = []
        if Pythonista:
            UIFont = objc_util.ObjCClass('UIFont')
            for family in UIFont.familyNames():
                family = str(family)
                try:
                    ImageFont.truetype(family)
                    fonts.font_list.append(((family,), family))
                except:
                    pass

                for name in UIFont.fontNamesForFamilyName_(family):
                    name = str(name)
                    fonts.font_list.append(((name,), name))

        salabim_dir = os.path.dirname(__file__)
        cur_dir = os.getcwd()
        dirs = [salabim_dir]
        if cur_dir != salabim_dir:
            dirs.append(cur_dir)
        if Windows:
            dirs.append(r'c:\windows\fonts')

        for dir in dirs:
            for file in glob.glob(dir + os.sep + '*.ttf'):
                fn = os.path.basename(file).split('.')[0]
                if fn in _std_fonts():
                    fullname = _std_fonts()[fn]
                else:
                    f = ImageFont.truetype(file, 12)
                    if f is None:
                        fullname = ''
                    else:
                        if str(f.font.style).lower() == 'regular':
                            fullname = str(f.font.family)
                        else:
                            fullname = str(f.font.family) + ' ' + str(f.font.style)
                if fullname != '':
                    if fn.lower() == fullname.lower():
                        fonts.font_list.append(((fullname,), file))
                    else:
                        fonts.font_list.append(((fn, fullname), file))
    return fonts.font_list


def standardfonts():
    return {
        '': 'calibri',
        'std': 'calibri',
        'mono': 'DejaVuSansMono',
        'narrow': 'mplus-1m-regular'
    }


def getfont(fontname, fontsize):  # fontsize in screen_coordinates!
    if hasattr(getfont, 'lookup'):
        if (fontname, fontsize) in getfont.lookup:
            return getfont.lookup[(fontname, fontsize)]
    else:
        getfont.lookup = {}

    if isinstance(fontname, str):
        fontlist1 = (fontname,)
    else:
        fontlist1 = fontname

    fontlist = [standardfonts().get(f.lower(), f) for f in fontlist1]

    result = None

    for ifont in fontlist:

        try:
            result = ImageFont.truetype(font=ifont, size=int(fontsize))
            break
        except:
            pass

        filename = ''
        for fns, ifilename in fonts():
            for fn in fns:
                if normalize(fn) == normalize(ifont):
                    filename = ifilename
                    break
            if filename != '':
                break
        if filename != '':
            try:
                result = ImageFont.truetype(font=filename, size=int(fontsize))
                break
            except:
                pass

    if result is None:
        result = ImageFont.load_default()  # last resort

    getfont.lookup[(fontname, fontsize)] = result
    return result


def show_fonts():
    '''
    show (print) all available fonts on this machine
    '''
    fontnames = []
    for fns, ifilename in fonts():
        for fn in fns:
            fontnames.append(fn)
    fontnames.extend(standardfonts().keys())
    last = ''
    for font in sorted(fontnames, key=normalize):
        if font != last:  # remove duplicates
            print(font)
            last = font


def show_colornames():
    '''
    show (print) all available color names and their value.
    '''
    names = sorted(colornames().keys())
    for name in names:
        print('{:22s}{}'.format(name, colornames()[name]))


def default_env():
    '''
    Returns
    -------
    default environment : Environment
    '''
    return _default_env


if __name__ == '__main__':
    try:
        import salabim_test
    except:
        print('test.py not found')
    else:
        salabim_test.test()
