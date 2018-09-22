'''          _         _      _            
 ___   __ _ | |  __ _ | |__  (_) _ __ ___  
/ __| / _` || | / _` || '_ \ | || '_ ` _ \ 
\__ \| (_| || || (_| || |_) || || | | | | |
|___/ \__,_||_| \__,_||_.__/ |_||_| |_| |_|
Discrete event simulation in Python

see www.salabim.org for more information, the documentation, updates and license information.
'''
from __future__ import print_function  # compatibility with Python 2.x
from __future__ import division  # compatibility with Python 2.x

__version__ = '2.3.4.1'

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
import itertools
import io
import pickle
import logging
import types

Pythonista = (sys.platform == 'ios')
Windows = (sys.platform.startswith('win'))


class SalabimError(Exception):
    pass


class g():
    pass


if Pythonista:
    import scene
    import ui
    import objc_util

inf = float('inf')
nan = float('nan')


class ItemFile(object):
    '''
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

        with sim.ItemFile('experiment0.txt') as f:
            run_length = f.read_item_float() |n|
            run_name = f.read_item() |n|

    Alternatively, the file can be opened and closed explicitely, like ::

        f = sim.ItemFile('experiment0.txt')
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
        'Item 2'
            Item3 Item4 # comment
        Item5 {five} Item6 {six}
        'Double quote" in item'
        "Single quote' in item"
        True
    '''

    def __init__(self, filename):
        self.iter = self._nextread()
        if '\n' in filename:
            self.open_file = io.StringIO(filename)
        else:
            self.open_file = open(filename, 'r')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.open_file.close()

    def close(self):
        self.open_file.close()

    def read_item_int(self):
        '''
        read next field from the ItemFile as int.

        if the end of file is reached, EOFError is raised
        '''
        return int(self.read_item().replace(',', '.'))

    def read_item_float(self):
        '''
        read next item from the ItemFile as float

        if the end of file is reached, EOFError is raised
        '''

        return float(self.read_item().replace(',', '.'))

    def read_item_bool(self):
        '''
        read next item from the ItemFile as bool

        A value of False (not case sensitive) will return False |n|
        A value of 0 will return False |n|
        The null string will return False |n|
        Any other value will return True

        if the end of file is reached, EOFError is raised
        '''
        result = self.read_item().strip().lower()
        if result == 'false':
            return False
        try:
            if float(result) == 0:
                return False
        except:
            pass
        if result == '':
            return False
        return True

    def read_item(self):
        '''
        read next item from the ItemFile

        if the end of file is reached, EOFError is raised
        '''
        try:
            return next(self.iter)
        except StopIteration:
            raise EOFError

    def _nextread(self):
        remove = '\r\n'
        quotes = '\'"'

        for line in self.open_file:
            mode = '.'
            result = ''
            for c in line:
                if c not in remove:
                    if mode in quotes:
                        if c == mode:
                            mode = '.'
                            yield result  # even return the null string
                            result = ''
                        else:
                            result += c
                    elif mode == '{':
                        if c == '}':
                            mode = '.'
                    else:
                        if c == '#':
                            break
                        if c in quotes:
                            if result:
                                yield result
                            result = ''
                            mode = c
                        elif c == '{':
                            if result:
                                yield result
                            result = ''
                            mode = c

                        elif c in (' ', '\t'):
                            if result:
                                yield result
                            result = ''
                        else:
                            result += c
            if result:
                yield result


class Monitor(object):
    '''
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

    weighted : bool
        if True, tallied values may be given weight.
        if False (default), weights are not allowed

    weight_legend : str
        used in print_statistics and print_histogram to indicate the dimension of weight,
        e.g. duration or minutes. Default: weight.

    merge: list, tuple or set
        the monitor will be created by merging the monitors mentioned in the list |n|
        note that the types of all to be merged monitors should be the same and
        that either all to be merged monitors are weighted or all to be merged monitors
        are non weighted. |n|
        default: no merge

    env : Environment
        environment where the monitor is defined |n|
        if omitted, default_env will be used
    '''

    cached_xweight = {(ex0, force_numeric): (0, 0) for ex0 in (False, True) for force_numeric in (False, True)}

    def __init__(self, name=None, monitor=True, type=None, merge=None, weighted=False, weight_legend='weight',
        env=None, *args, **kwargs):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        _set_name(name, self.env._nameserializeMonitor, self)
        self._timestamp = False
        self.weighted = weighted
        self.weight_legend = weight_legend
        if merge is None:
            if type is None:
                type = 'any'
            try:
                self.xtypecode, _ = type_to_typecode_off(type)
            except KeyError:
                raise SalabimError('type (' + type + ') not recognized')
            self.reset(monitor)
        else:
            if not merge:
                raise SalabimError('merge list empty')
            for m in merge:
                if not isinstance(m, Monitor):
                    raise SalabimError('non Monitor item found in merge list')

            self.xtypecode = merge[0].xtypecode
            self.weighted = merge[0].weighted
            for m in merge:
                if m.xtypecode != self.xtypecode:
                    raise SalabimError('not all types in merge list are equal')
                if m.weighted != self.weighted:
                    raise SalabimError('not all weighted flags in merge list are equal')
            if type is not None:
                if type_to_typecode_off(type)[0] != self.xtypecode:
                    raise SalabimError('type does not match the type of the monitors in the merge list')
            if self.xtypecode:
                self._x = array.array(self.xtypecode, itertools.chain(*[m._x for m in merge]))
            else:
                self._x = list(itertools.chain(*[m._x for m in merge]))
            if self.weighted:
                self._weight = array.array('float', itertools.chain(*[m._weight for m in merge]))
            self._monitor = monitor
        self.setup(*args, **kwargs)

    def setup(self):
        '''
        called immediately after initialization of a monitor.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        '''
        pass

    def register(self, registry):
        '''
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
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self in registry:
            raise SalabimError(self.name() + ' already in registry')
        registry.append(self)
        return self

    def deregister(self, registry):
        '''
        deregisters the monitor in the registry

        Parameters
        ----------
        registry : list
            list of registered objects

        Returns
        -------
        monitor (self) : Monitor
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self not in registry:
            raise SalabimError(self.name() + ' not in registry')
        registry.remove(self)
        return self

    def __repr__(self):
        return objectclass_to_str(self) + ' (' + self.name() + ')'

    def reset_monitors(self, monitor=None):
        '''
        resets monitor

        Parameters
        ----------
        monitor : bool
            if True (default), monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, the monitor state remains unchanged

        Note
        ----
        Exactly same functionality as Monitor.reset()
        '''
        self.reset(monitor)

    def reset(self, monitor=None):
        '''
        resets monitor

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled
            if omitted, no change of monitoring state
        '''

        if monitor is None:
            monitor = self._monitor
        if self.xtypecode:
            self._x = array.array(self.xtypecode)
        else:
            self._x = []
        if self.weighted:
            self._weight = array.array('d')
        self.monitor(monitor)
        Monitor.cached_xweight = {(ex0, force_numeric): (0, 0)
            for ex0 in (False, True) for force_numeric in (False, True)}  # invalidate the cache

    def monitor(self, value=None):
        '''
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
        '''
        if value is not None:
            self._monitor = value
        return self.monitor

    def tally(self, x, weight=1):
        '''
        Parameters
        ----------
        x : any, preferably int, float or translatable into int or float
            value to be tallied
        '''
        if self._monitor:
            self._x.append(x)
            if self.weighted:
                self._weight.append(1 if weight is None else weight)
            else:
                if weight != 1:
                    raise SalabimError('incorrect weight for non weighted monitor')

    def name(self, value=None):
        '''
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
        '''
        if value is not None:
            self._name = value
        return self._name

    def base_name(self):
        '''
        Returns
        -------
        base name of the monitor (the name used at initialization): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the monitor : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        '''
        return self._sequence_number

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

        Note
        ----
        For weighted monitors, the weighted mean is returned
        '''
        if self.weighted:
            x, weight = self.xweight(ex0=ex0)
            sumweight = sum(weight)
            if sumweight:
                return sum(vx * vweight for vx, vweight in zip(x, weight)) / sumweight
            else:
                return nan
        else:
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

        Note
        ----
        For weighted monitors, the weighted standard deviation is returned
        '''
        if self.weighted:
            x, weight = self.xweight(ex0=ex0)
            sumweight = sum(weight)
            if sumweight:
                wmean = self.mean(ex0=ex0)
                wvar = sum((vweight * (vx - wmean)**2) for vx, vweight in zip(x, weight)) / sumweight
                return math.sqrt(wvar)
            else:
                return nan
        else:
            x = self.x(ex0=ex0)
            if x:
                wmean = self.mean(ex0=ex0)
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
        median of tallied values

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        median : float

        Note
        ----
        For weighted monitors, the weighted median is returned
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
        : float
            q-th percentile |n|
            0 returns the minimum, 50 the median and 100 the maximum

        Note
        ----
        For weighted monitors, the weighted percentile is returned
        '''
        # algorithm based on
        # https://stats.stackexchange.com/questions/13169/defining-quantiles-over-a-weighted-sample
        q = max(0, min(q, 100))
        x, weight = self.xweight(ex0=ex0)
        if len(x) == 1:
            return x[0]
        sumweight = sum(weight)
        n = len(weight)
        if not sumweight:
            return nan
        xweight = sorted(zip(x, weight), key=lambda v: v[0])

        x_sorted, weight_sorted = zip(*xweight)

        cum = 0
        s = []
        for k in range(n):
            s.append((k * weight_sorted[k] + cum))
            cum += (n -1) * weight_sorted[k]
            
        for k in range(n-1):
            if s[k + 1] > s[n - 1] * q / 100:
                break
        
        return x_sorted[k] + (x_sorted[k+1] - x_sorted[k]) * (q/100 * s[n - 1] - s[k]) / (s[k + 1] - s[k])

    def bin_number_of_entries(self, lowerbound, upperbound, ex0=False):
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

    def bin_weight(self, lowerbound, upperbound):
        '''
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
        '''
        x, weight = self.xweight()
        return sum((vweight for vx, vweight in zip(x, weight) if (vx > lowerbound) and (vx <= upperbound)))

    def value_number_of_entries(self, value):
        '''
        count of the number of tallied values equal to value or in value

        Parameters
        ----------
        value : any
            if list, tuple or set, check whether the tallied value is in value |n|
            otherwise, check whether the tallied value equals the given value

        Returns
        -------
        number of tallied values in value or equal to value : int
        '''
        if isinstance(value, (list, tuple, set)):
            value = [str(v) for v in value]
        else:
            value = [str(value)]

        x = self.x(force_numeric=False)
        return sum(1 for vx in x if (str(vx).strip() in value))

    def value_weight(self, value):
        '''
        total weight of tallied values equal to value or in value

        Parameters
        ----------
        value : any
            if list, tuple or set, check whether the tallied value is in value |n|
            otherwise, check whether the tallied value equals the given value

        Returns
        -------
        total of weights of tallied values in value or equal to value : int
        '''
        x, weight = self.xweight(force_numeric=False)  # can't use self._weight, because of MonitorTimestamp
        if isinstance(value, (list, tuple, set)):
            value = [str(v) for v in value]
        else:
            value = [str(value)]

        return sum(vweight for (vx, vweight) in zip(x, weight) if (str(vx).strip() in value))

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

    def weight(self, ex0=False):
        '''
        sum of weights

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        sum of weights : float
        '''
        x, weight = self.xweight(ex0=ex0)
        return sum(weight)

    def weight_zero(self):
        '''
        sum of weights of zero entries

        Returns
        -------
        sum of weights of zero entries : float
        '''
        return self.weight() - self.weight(ex0=True)

    def print_statistics(self, show_header=True, show_legend=True, do_indent=False, as_str=False, file=None):
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

        as_str: bool
            if False (default), print the statistics
            if True, return a string containing the statistics

        file: file
            if Noneb(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        statistics (if as_str is True) : str
        '''
        result = []
        if do_indent:
            l = 45
        else:
            l = 0
        indent = pad('', l)

        if show_header:
            result.append(
                indent + 'Statistics of {} at {}'.format(self.name(), fn(self.env._now - self.env._offset, 13, 3)))

        if show_legend:
            result.append(
                indent + '                        all    excl.zero         zero')
            result.append(
                pad('-' * (l - 1) + ' ', l) + '-------------- ------------ ------------ ------------')

        if self.weight() == 0:
            result.append(pad(self.name(), l) + 'no data')
            return return_or_print(result, as_str, file)
        if self.weighted:
            result.append(pad(self.name(), l) + pad(self.weight_legend, 14) +
              '{}{}{}'.format(fn(self.weight(), 13, 3),
              fn(self.weight(ex0=True), 13, 3), fn(self.weight_zero(), 13, 3)))
        else:
            result.append(pad(self.name(), l) + pad('entries', 14) +
              '{}{}{}'.format(fn(self.number_of_entries(), 13, 3),
                fn(self.number_of_entries(ex0=True), 13, 3), fn(self.number_of_entries_zero(), 13, 3)))

        result.append(indent + 'mean          {}{}'.
              format(fn(self.mean(), 13, 3), fn(self.mean(ex0=True), 13, 3)))
        result.append(indent + 'std.deviation {}{}'.
              format(fn(self.std(), 13, 3), fn(self.std(ex0=True), 13, 3)))
        result.append('')
        result.append(indent + 'minimum       {}{}'.
              format(fn(self.minimum(), 13, 3), fn(self.minimum(ex0=True), 13, 3)))
        result.append(indent + 'median        {}{}'.
              format(fn(self.percentile(50), 13, 3), fn(self.percentile(50, ex0=True), 13, 3)))
        result.append(indent + '90% percentile{}{}'.
              format(fn(self.percentile(90), 13, 3), fn(self.percentile(90, ex0=True), 13, 3)))
        result.append(indent + '95% percentile{}{}'.
              format(fn(self.percentile(95), 13, 3), fn(self.percentile(95, ex0=True), 13, 3)))
        result.append(indent + 'maximum       {}{}'.
              format(fn(self.maximum(), 13, 3), fn(self.maximum(ex0=True), 13, 3)))
        return return_or_print(result, as_str, file)

    def histogram_autoscale(self, ex0=False):
        '''
        used by histogram_print to autoscale |n|
        may be overridden.

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        bin_width, lowerbound, number_of_bins : tuple
        '''
        xmax = self.maximum(ex0=ex0)
        xmin = self.minimum(ex0=ex0)

        done = False
        for i in range(10):
            exp = 10 ** i
            for bin_width in (exp, exp * 2, exp * 5):
                lowerbound = math.floor(xmin / bin_width) * bin_width
                number_of_bins = int(math.ceil((xmax - lowerbound) / bin_width))
                if number_of_bins <= 30:
                    done = True
                    break
            if done:
                break
        return bin_width, lowerbound, number_of_bins

    def print_histograms(self, number_of_bins=None,
        lowerbound=None, bin_width=None, values=False, ex0=False, as_str=False, file=None):
        '''
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
        '''
        return self.print_histogram(number_of_bins, lowerbound, bin_width, values, ex0, as_str=as_str, file=file)

    def print_histogram(self, number_of_bins=None,
      lowerbound=None, bin_width=None, values=False, ex0=False, as_str=False, file=None):
        '''
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
            if True, the individual values will be shown (in the right order).
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
        with a maximum of 30 classes.
        '''
        result = []
        result.append('Histogram of ' + self.name() + ('[ex0]' if ex0 else ''))

        x, weight = self.xweight(ex0=ex0, force_numeric=not values)
        weight_total = sum(weight)

        if weight_total == 0:
            result.append('')
            result.append('no data')
        else:

            if values:
                nentries = len(x)
                if self.weighted:
                    result.append(pad(self.weight_legend, 13) +
                        '{}'.format(fn(weight_total, 13, 3)))
                result.append(pad('entries', 13) + '{}'.
                    format(fn(nentries, 13, 3)))
                result.append('')
                if self.weighted:
                    result.append('value                ' + rpad(self.weight_legend, 13) + '        entries')
                else:
                    result.append('value               entries')
                as_set = {str(x).strip() for x in set(x)}

                values = sorted(list(as_set), key=self.key)

                for value in values:
                    if self.weighted:
                        count = self.value_weight(value)
                        count_entries = self.value_number_of_entries(value)
                    else:
                        count = self.value_number_of_entries(value)

                    perc = count / weight_total
                    scale = 80
                    n = int(perc * scale)
                    s = ('*' * n) + (' ' * (scale - n))

                    if self.weighted:
                        result.append(pad(str(value), 20) + fn(count, 14, 3) + '(' + fn(perc * 100, 5, 1) + '%)' +
                           rpad(str(count_entries), 7) + '(' + fn(count_entries * 100 / nentries, 5, 1) + '%) ' + s)
                    else:
                        result.append(
                            pad(str(value), 20) + rpad(str(count), 7) + '(' + fn(perc * 100, 5, 1) + '%) ' + s)
            else:
                bin_width, lowerbound, number_of_bins = self.histogram_autoscale()
                result.append(self.print_statistics(show_header=False, show_legend=True, do_indent=False, as_str=True))
                if number_of_bins >= 0:
                    result.append('')
                    if self.weighted:
                        result.append('           <= ' + rpad(self.weight_legend, 13) + '     %  cum%')
                    else:
                        result.append('           <=       entries     %  cum%')

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
                        if self.weighted:
                            count = self.bin_weight(lb, ub)
                        else:
                            count = self.bin_number_of_entries(lb, ub)

                        perc = count / weight_total
                        if weight_total == inf:
                            s = ''
                        else:
                            cumperc += perc
                            scale = 80
                            n = int(perc * scale)
                            ncum = int(cumperc * scale) + 1
                            s = ('*' * n) + (' ' * (scale - n))
                            s = s[:ncum - 1] + '|' + s[ncum + 1:]

                        result.append('{} {}{}{} {}'.
                              format(fn(ub, 13, 3), fn(count, 13, 3), fn(perc * 100, 6, 1), fn(cumperc * 100, 6, 1), s))
        result.append('')
        return return_or_print(result, as_str=as_str, file=file)

    def key(self, x):
        try:
            x1 = float(x)
            x2 = ''
        except:
            x1 = math.inf
            x2 = x
        return(x1, x2)

    def animate(self, *args, **kwargs):
        '''
        animates the monitor in a panel

        Parameters
        ----------
        linecolor : colorspec
            color of the line or points (default foreground color)

        linewidth : int
            width of the line or points (default 1 for line, 3 for points)

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
            font of the title (default '')

        titlefontsize : int
            size of the font of the title (default 15)

        as_points : bool
            if False, lines will be drawn between the points |n|
            if True (default),  only the points will be shown

        as_level : bool
            if True (default for lines), the timestamped monitor is considered to be a level
            if False (default for points), just the tallied values will be shown, and connected (for lines)

        title : str
            title to be shown above panel |n|
            default: name of the monitor

        x : int
            x-coordinate of panel, relative to xy_anchor, default 0

        y : int
            y-coordinate of panel, relative to xy_anchor. default 0

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
            for timescaled monitors the relative horizontal position of time t within the panel is on
            t * horizontal_scale, possibly shifted (default 1)|n|
            for non timescaled monitors, the relative horizontal position of index i within the panel is on
            i * horizontal_scale, possibly shifted (default 5)|n|

        width : int
            width of the panel (default 200)

        height : int
            height of the panel (default 75)

        layer : int
            layer (default 0)

        Returns
        -------
        reference to AnimateMonitor object : AnimateMonitor

        Note
        ----
        It is recommended to use sim.AnimateMonitor instead |n|

        All measures are in screen coordinates |n|
        '''

        return AnimateMonitor(monitor=self, *args, **kwargs)

    def x(self, ex0=False, force_numeric=True):
        '''
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
        '''
        return self.xweight(ex0=ex0, force_numeric=force_numeric)[0]

    def xweight(self, ex0=False, force_numeric=True):
        '''
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
        '''
        thishash = hash((self, len(self._x)))

        if Monitor.cached_xweight[(ex0, force_numeric)][0] == thishash:
            return Monitor.cached_xweight[(ex0, force_numeric)][1]

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

        if self.weighted:
            if ex0:
                xweight = (x, array.array('d', [vweight for vx, vweight in zip(x, self._weight) if vx != 0]))
            else:
                xweight = (x, self._weight)
        else:
            xweight = (x, array.array('d', (1,) * len(x)))

        Monitor.cached_xweight[(ex0, force_numeric)] = (thishash, xweight)
        return xweight


class MonitorTimestamp(Monitor):
    '''
    monitortimestamp object

    Parameters
    ----------
    name : str
        name of the timestamped monitor
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

    initial_tally : any, usually float
        initial value to be tallied (default 0) |n|
        if it important to provide the value at time=now

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

    merge: list, tuple or set
        the monitor will be created by merging the monitors mentioned in the list |n|
        merging means summing the available x-values|n|
        note that the types of all to be merged monitors should be the same. |n|
        initial_tally may not be specified when merge is specified. |n|
        default: no merge

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

    def __init__(self, name=None, initial_tally=None, monitor=True, type=None,
        merge=None, env=None, *args, **kwargs):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        self._timestamp = True
        self.weighted = True
        self.weight_legend = 'duration'
        _set_name(name, self.env._nameserializeComponent, self)
        if merge is None:
            if type is None:
                type = 'any'
            try:
                self.xtypecode, self.off = type_to_typecode_off(type)
            except KeyError:
                raise SalabimError('type (' + type + ') not recognized')

            if initial_tally is None:
                self._tally = 0
            else:
                self._tally = initial_tally
            self.reset(monitor=monitor)
        else:
            if initial_tally is not None:
                raise SalabimError('initial_tally cannot be combined with merge')
            if not merge:
                raise SalabimError('merge list empty')

            for m in merge:
                if not isinstance(m, MonitorTimestamp):
                    raise SalabimError('non MonitorTimestamp item found in merge list')

            self.xtypecode = merge[0].xtypecode
            for m in merge:
                if m.xtypecode != self.xtypecode:
                    raise SalabimError('not all types in merge list are equal')
            if type is not None:
                if type != self.xtypecode:
                    raise SalabimError('type does not match the type of the monitors in the merge list')
            self.off = merge[0].off
            if self.xtypecode:
                self._xw = array.array(self.xtypecode)
            else:
                self._xw = []
            self.x_weight_t = None

            curx = [self.off] * len(merge)
            self._t = array.array('d')
            for t, index, x in heapq.merge(
                *[zip(merge[index]._t, itertools.repeat(index), merge[index]._xw) for index in range(len(merge))]):
                if self.xtypecode:
                    curx[index] = x
                else:
                    try:
                        curx[index] = float(x)
                    except:
                        curx[index] = 0

                sum = 0
                for xi in curx:
                    if xi is self.off:
                        sum = self.off
                        break
                    sum += xi

                if self._t and (t == self._t[-1]):
                    self._xw[-1] = sum
                else:
                    self._t.append(t)
                    self._xw.append(sum)
            if not monitor:
                self._t.append(self.env._now)
                self._xw.append(self.off)

        self.setup(*args, **kwargs)

    def setup(self):
        '''
        called immediately after initialization of a monitortimestamp.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        '''
        pass

    def register(self, *args, **kwargs):
        '''
        registers the timestamped monitor in the registry

        Parameters
        ----------
        registry : list
            list of (to be) registered objects

        Returns
        -------
        timestamped monitor (self) : MonitorTimestamped

        Note
        ----
        Use MonitorTimestamped.deregister if timestamped monitor does not longer need to be registered.
        '''
        return Monitor.register(self, *args, **kwargs)

    def deregister(self, *args, **kwargs):
        '''
        deregisters the timestamped monitor in the registry

        Parameters
        ----------
        registry : list
            list of registered objects

        Returns
        -------
        timestamped monitor (self): MonitorTimestamped
        '''
        return Monitor.deregister(self, *args, **kwargs)

    def __repr__(self):
        return objectclass_to_str(self) + ' (' + self.name() + ')'

    def __call__(self):  # direct moneypatching __call__ doesn't work
        return self._tally

    def get(self):
        '''
        Returns
        -------
        last tallied value : any, usually float

            Instead of this method, the timestamped monitor can also be called directly, like |n|

            level = sim.MonitorTimestamp('level') |n|
            ... |n|
            print(level()) |n|
            print(level.get())  # identical |n|
        '''
        return self._tally

    def reset_monitors(self, monitor=None):
        '''
        resets timestamped monitor

        Parameters
        ----------
        monitor : bool
            if True (default), monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, the monitor state remains unchanged

        Note
        ----
        Exactly same functionality as MonitorTimestamped.reset()
        '''
        self.reset(monitor)

    def reset(self, monitor=None):
        '''
        resets timestamped monitor

        Parameters
        ----------
        monitor : bool
            if True (default), monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, the monitor state remains unchanged
        '''
        if monitor is not None:
            self._monitor = monitor
        if self.xtypecode:
            self._xw = array.array(self.xtypecode)
        else:
            self._xw = []

        if self._monitor:
            self._xw.append(self._tally)
        else:
            self._xw.append(self.off)
        self._t = array.array('d')
        self._t.append(self.env._now)
        self.x_weight_t = None  # invalidate _x and _weight

    def monitor(self, value=None):
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

        if value is not None:
            self._monitor = value
            if self._monitor:
                self.tally(self._tally)
            else:
                self._tally_off()  # can't use tally() here because self._tally should be untouched
        return self.monitor

    def tally(self, value):
        '''
        tally value

        Arguments
        ---------
        value : any, usually float
        '''
        self._tally = value
        if self._monitor:
            t = self.env._now
            if self._t[-1] == t:
                self._xw[-1] = value
            else:
                self._xw.append(value)
                self._t.append(t)

    def _tally_off(self):
        t = self.env._now
        if self._t[-1] == t:
            self._xw[-1] = self.off
        else:
            self._xw.append(self.off)
            self._t.append(t)

    def name(self, value=None):
        '''
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
        '''
        if value is not None:
            self._name = value
        return self._name

    def base_name(self):
        '''
        Returns
        -------
        base name of the monitortimestamp (the name used at initialization): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the monitortimestamp : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        '''
        return self._sequence_number

    def mean(self, *args, **kwargs):
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
        self.set_x_weight()
        return Monitor.mean(self, *args, **kwargs)

    def std(self, *args, **kwargs):
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
        self.set_x_weight()
        return Monitor.std(self, *args, **kwargs)

    def minimum(self, *args, **kwargs):
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
        self.set_x_weight()
        return Monitor.minimum(self, *args, **kwargs)

    def maximum(self, *args, **kwargs):
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
        self.set_x_weight()
        return Monitor.maximum(self, *args, **kwargs)

    def median(self, *args, **kwargs):
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
        self.set_x_weight()
        return Monitor.median(self, *args, **kwargs)

    def percentile(self, *args, **kwargs):
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
        self.set_x_weight()
        return Monitor.percentile(self, *args, **kwargs)

    def bin_duration(self, *args, **kwargs):
        '''
        duration of tallied values with the value in range (lowerbound,upperbound]

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
        duration of values >lowerbound and <=upperbound: float
        '''
        self.set_x_weight()
        return Monitor.bin_weight(self, *args, **kwargs)

    def value_duration(self, *args, **kwargs):
        '''
        duration of tallied values equal to value or in value

        Parameters
        ----------
        value : any
            if list, tuple or set, check whether the tallied value is in value |n|
            otherwise, check whether the tallied value equals the given value

        Returns
        -------
        duration of tallied values in value or equal to value : float
        '''
        self.set_x_weight()
        return Monitor.value_weight(self, *args, **kwargs)

    def value_number_of_entries(self, *args, **kwargs):
        '''
        count of tallied values equal to value or in value

        Parameters
        ----------
        value : any
            if list, tuple or set, check whether the tallied value is in value |n|
            otherwise, check whether the tallied value equals the given value

        Returns
        -------
        count of tallied values in value or equal to value : float
        '''
        self.set_x_weight()
        return Monitor.value_number_of_entries(self, *args, **kwargs)

    def duration(self, *args, **kwargs):
        '''
        total duration

        Parameters
        ----------
        ex0 : bool
            if False (default), include samples with value 0. if True, exclude zero samples.

        Returns
        -------
        total duration : float
        '''
        self.set_x_weight()
        return Monitor.weight(self, *args, **kwargs)

    def duration_zero(self, *args, **kwargs):
        '''
        total duration of samples with value 0

        Returns
        -------
        total duration of zero samples : float
        '''
        self.set_x_weight()
        return Monitor.duration_zero(self, *args, **kwargs)

    def number_of_entries(self, *args, **kwargs):
        '''
        count of the number of entries (duration type)

        Parameters
        ----------
        ex0 : bool
            if False (default), include zeroes. if True, exclude zeroes

        Returns
        -------
        number of entries : int
        '''
        self.set_x_weight()
        return Monitor.number_of_entries(self, *args, **kwargs)

    def number_of_entries_zero(self, *args, **kwargs):
        '''
        count of the number of zero entries (duration type)

        Returns
        -------
        number of zero entries : int
        '''
        self.set_x_weight()
        return Monitor.number_of_entries_zero(self, *args, **kwargs)

    def animate(self, *args, **kwargs):
        '''
        animates the timestamed monitor in a panel

        Parameters
        ----------
        linecolor : colorspec
            color of the line or points (default foreground color)

        linewidth : int
            width of the line or points (default 1 for line, 3 for points)

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
            font of the title (default '')

        titlefontsize : int
            size of the font of the title (default 15)

        as_points : bool
            if False (default), lines will be drawn between the points |n|
            if True,  only the points will be shown

        title : str
            title to be shown above panel |n|
            default: name of the monitor

        x : int
            x-coordinate of panel, relative to xy_anchor, default 0

        y : int
            y-coordinate of panel, relative to xy_anchor. default 0

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
            for timescaled monitors the relative horizontal position of time t within the panel is on
            t * horizontal_scale, possibly shifted (default 1)|n|
            for non timescaled monitors, the relative horizontal position of index i within the panel is on
            i * horizontal_scale, possibly shifted (default 5)|n|

        width : int
            width of the panel (default 200)

        height : int
            height of the panel (default 75)

        layer : int
            layer (default 0)

        Returns
        -------
        reference to AnimateMonitor object : AnimateMonitor

        Note
        ----
        It is recommended to use sim.AnimateMonitor instead |n|

        All measures are in screen coordinates |n|
        '''

        return AnimateMonitor(monitor=self, *args, **kwargs)

    def xduration(self, *args, **kwargs):
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
        return Monitor.xweight(self, *args, **kwargs)

    def xweight(self, *args, **kwargs):
        self.set_x_weight()
        return Monitor.xweight(self, *args, **kwargs)

    def set_x_weight(self):
        if self.x_weight_t == self.env.t:
            return
        self.x_weight_t = self.env.t   # stay valid until new t detected or invalidated
        Monitor.cached_xweight = {(ex0, force_numeric): (0, 0)
            for ex0 in (False, True) for force_numeric in (False, True)}  # invalidate the cache

        weightall = array.array('d')
        lastt = None
        for t in self._t:
            if lastt is not None:
                weightall.append(t - lastt)
            lastt = t

        weightall.append(self.env._now - lastt)

        self._weight = array.array('d')
        if self.xtypecode:
            self._x = array.array(self.xtypecode)
        else:
            self._x = []

        for vx, vweight in zip(self._xw, weightall):
            if vx != self.off:
                self._x.append(vx)
                self._weight.append(vweight)

    def xt(self, ex0=False, exoff=False, force_numeric=True, add_now=True):
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

        add_now : bool
            if True (default), the last tallied x-value and the current time is added to the result |n|
            if False, the result ends with the last tallied value and the time that was tallied

        Returns
        -------
        array/list with x-values and array with timestamps : tuple

        Note
        ----
        The value self.off is stored when monitoring is turned off |n|
        The timestamps are not corrected for any reset_now() adjustment.
        '''
        if self.xtypecode or (not force_numeric):
            xall = self._xw
            typecode = self.xtypecode
            off = self.off
        else:
            xall = list_to_array(self._xw)
            typecode = xall.typecode
            off = -inf  # float

        if typecode:
            x = array.array(typecode)
        else:
            x = []
        t = array.array('d')
        if add_now:
            addx = [xall[-1]]
            addt = [self.env._now]
        else:
            addx = []
            addt = []
        for vx, vt in zip(itertools.chain(xall, addx), itertools.chain(self._t, addt)):
            if not ex0 or (vx != 0):
                if not exoff or (vx != off):
                    x.append(vx)
                    t.append(vt)

        return x, t

    def tx(self, ex0=False, exoff=False, force_numeric=False, add_now=True):
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

        add_now : bool
            if True (default), the current time and the last tallied x-value added to the result |n|
            if False, the result ends with the time of the last tally and the last tallied x-value

        Returns
        -------
        array with timestamps and array/list with x-values : tuple

        Note
        ----
        The value self.off is stored when monitoring is turned off |n|
        The timestamps are not corrected for any reset_now() adjustment.
        '''
        return tuple(reversed(self.xt(ex0=ex0, exoff=exoff, force_numeric=force_numeric, add_now=add_now)))

    def print_statistics(self, show_header=True, show_legend=True, do_indent=False, as_str=False, file=None):
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

        as_str: bool
            if False (default), print the statistics
            if True, return a string containing the statistics

        file: file
            if None(default), all output is directed to stdout |n|
            otherwise, the output is directed to the file

        Returns
        -------
        statistics (if as_str is True) : str
        '''

        self.set_x_weight()
        return Monitor.print_statistics(self, show_header, show_legend, do_indent, as_str=as_str, file=file)

    def print_histograms(self, number_of_bins=None,
      lowerbound=None, bin_width=None, values=False, ex0=False, as_str=False, file=None):
        '''
        print timedstamped monitor statistics and histogram

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
            if True, the individual values will be shown (in the right order).
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
        Exactly same functionality as MonitorTimestamped.print_histogram()
        '''
        return self.print_histogram(number_of_bins, lowerbound, bin_width, values, ex0, as_str=as_str, file=file)

    def print_histogram(
        self, number_of_bins=None, lowerbound=None, bin_width=None, values=False, ex0=False, as_str=False, file=None):
        '''
        print timestamped monitor statistics and histogram

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
            if True, the individual values will be shown (in the right order).
            in that case, nu cumulative values will be given |n|

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
        with a maximum of 30 classes.
        '''
        self.set_x_weight()
        return Monitor.print_histogram(
            self, number_of_bins, lowerbound, bin_width, values, ex0, as_str=as_str, file=file)


class AnimateMonitor(object):
    '''
    animates a (timestamped) monitor in a panel

    Parameters
    ----------
    linecolor : colorspec
        color of the line or points (default foreground color)

    linewidth : int
        width of the line or points (default 1 for line, 3 for points)

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
        font of the title (default '')

    titlefontsize : int
        size of the font of the title (default 15)

    as_points : bool
        if False (default for timestamped monitors), lines will be drawn between the points |n|
        if True (default for non timestamped monitors),  only the points will be shown

    as_level : bool
        if True (default for lines), the timestamped monitor is considered to be a level
        if False (default for points), just the tallied values will be shown, and connected (for lines)

    title : str
        title to be shown above panel |n|
        default: name of the monitor

    x : int
        x-coordinate of panel, relative to xy_anchor, default 0

    y : int
        y-coordinate of panel, relative to xy_anchor. default 0

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
        for timescaled monitors the relative horizontal position of time t within the panel is on
        t * horizontal_scale, possibly shifted (default 1)|n|
        for non timescaled monitors, the relative horizontal position of index i within the panel is on
        i * horizontal_scale, possibly shifted (default 5)|n|

    width : int
        width of the panel (default 200)

    height : int
        height of the panel (default 75)

    layer : int
        layer (default 0)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|
    '''

    def __init__(self, monitor, linecolor='fg', linewidth=None, fillcolor='', bordercolor='fg', borderlinewidth=1,
        titlecolor='fg', nowcolor='red',
        titlefont='', titlefontsize=15,
        as_points=None, as_level=None, title=None, x=0, y=0, vertical_offset=2, parent=None,
        vertical_scale=5, horizontal_scale=None, width=200, height=75, xy_anchor='sw', layer=0):

        _checkismonitor(monitor)

        if title is None:
            title = monitor.name()

        if as_points is None:
            as_points = not monitor._timestamp

        if as_level is None:
            as_level = not as_points

        if linewidth is None:
            linewidth = 3 if as_points else 1

        if horizontal_scale is None:
            horizontal_scale = 1 if monitor._timestamp else 5

        xll = x + monitor.env.xy_anchor_to_x(xy_anchor, screen_coordinates=True)
        yll = y + monitor.env.xy_anchor_to_y(xy_anchor, screen_coordinates=True)

        self.aos = []
        self.parent = parent
        self.env = monitor.env
        self.aos.append(AnimateRectangle(spec=(0, 0, width, height), offsetx=xll, offsety=yll,
            fillcolor=fillcolor, linewidth=borderlinewidth, linecolor=bordercolor,
            screen_coordinates=True, layer=layer))
        self.aos.append(AnimateText(text=title, textcolor=titlecolor,
            offsetx=xll, offsety=yll + height + titlefontsize * 0.15, text_anchor='sw',
            screen_coordinates=True, fontsize=titlefontsize, font=titlefont, layer=layer))
        if monitor._timestamp:
            self.aos.append(_Animate_t_Line(line0=(), linecolor0=nowcolor,
                monitor=monitor, width=width, height=height, t_scale=horizontal_scale,
                layer=layer, offsetx0=xll, offsety0=yll,
                screen_coordinates=True))
            self.aos.append(_Animate_t_x_Line(monitor=monitor, linecolor0=linecolor, line0=(),
                linewidth0=linewidth,
                screen_coordinates=True, offsetx0=xll, offsety0=yll,
                width=width, height=height, value_offsety=vertical_offset, value_scale=vertical_scale,
                as_points=as_points, as_level=as_level,
                linewidth=linewidth, t_scale=horizontal_scale, layer=layer))
        else:
            self.aos.append(_Animate_index_x_Line(monitor=monitor, line0=(), linecolor0=linecolor,
                linewidth0=linewidth,
                screen_coordinates=True, xll=xll, yll=yll,
                as_points=as_points,
                width=width, height=height, value_offsety=vertical_offset, value_scale=vertical_scale,
                index_scale=horizontal_scale, layer=layer, linewidth=linewidth))
        self.env.sys_objects.append(self)

    def update(self, t):
        pass

    def remove(self):
        '''
        removes the animate object and thus closes this animation
        '''
        for ao in self.aos:
            ao.remove()
        self.env.sys_objects.remove(self)


if Pythonista:

    class AnimationScene(scene.Scene):

        def __init__(self, env, *args, **kwargs):
            scene.Scene.__init__(self, *args, **kwargs)

        def setup(self):
            pass

        def touch_ended(self, touch):
            env = g.animation_env
            if env is not None:
                for uio in env.ui_objects:
                    ux = uio.x + env.xy_anchor_to_x(uio.xy_anchor, screen_coordinates=True)
                    uy = uio.y + env.xy_anchor_to_y(uio.xy_anchor, screen_coordinates=True)
                    if uio.type == 'button':
                        if touch.location in \
                                scene.Rect(ux - 2, uy - 2, uio.width + 2, uio.height + 2):
                            uio.action()
                            break  # new buttons might have been installed
                    if uio.type == 'slider':
                        if touch.location in\
                                scene.Rect(ux - 2, uy - 2, uio.width + 4, uio.height + 4):
                            xsel = touch.location[0] - ux
                            uio._v = uio.vmin + \
                                round(-0.5 + xsel / uio.xdelta) * uio.resolution
                            uio._v = max(min(uio._v, uio.vmax), uio.vmin)
                            if uio.action is not None:
                                uio.action(uio._v)
                                break  # new items might have been installed

        def draw(self):
            env = g.animation_env
            g.in_draw = True
            if (env is not None) and env._animate and env.running:
                scene.background(env.pythonistacolor('bg'))

                if env._synced or env._video:  # video forces synced
                    if env._video:
                        env.t = env.video_t
                    else:
                        if env.paused:
                            env.t = env.start_animation_time
                        else:
                            env.t = \
                                env.start_animation_time +\
                                ((time.time() -
                                  env.start_animation_clocktime) * env._speed)
                    while (env.peek() < env.t) and env.running and env._animate:
                        env.step()
                else:
                    if (env._step_pressed or (not env.paused)) and env._animate:
                        env.step()
                        if not env._current_component._suppress_pause_at_step:
                            env._step_pressed = False
                        env.t = env._now
                if not env.paused:
                    env.frametimes.append(time.time())

                env.an_objects.sort(
                    key=lambda obj: (-obj.layer(env.t), obj.sequence))
                touchvalues = self.touches.values()

                capture_image = Image.new('RGB',
                    (env._width, env._height), env.colorspec_to_tuple('bg'))

                env.animation_pre_tick(env.t)
                env.animation_pre_tick_sys(env.t)
                for ao in env.an_objects:
                    ao.make_pil_image(env.t)
                    if ao._image_visible:
                        capture_image.paste(ao._image,
                            (int(ao._image_x),
                            int(env._height - ao._image_y - ao._image.size[1])),
                            ao._image)
                env.animation_post_tick(env.t)

                ims = scene.load_pil_image(capture_image)
                scene.image(ims, 0, 0, *capture_image.size)
                scene.unload_image(ims)
                if env._video and (not env.paused):
                    if env._video_out == 'gif':  # just to be sure
                        env._images.append(capture_image.convert('RGB'))
                for uio in env.ui_objects:
                    ux = uio.x + env.xy_anchor_to_x(uio.xy_anchor, screen_coordinates=True)
                    uy = uio.y + env.xy_anchor_to_y(uio.xy_anchor, screen_coordinates=True)

                    if uio.type == 'entry':
                        raise SalabimError('AnimateEntry not supported on Pythonista')
                    if uio.type == 'button':
                        linewidth = uio.linewidth

                        scene.push_matrix()
                        scene.fill(env.pythonistacolor(uio.fillcolor))
                        scene.stroke(env.pythonistacolor(uio.linecolor))
                        scene.stroke_weight(linewidth)
                        scene.rect(ux - 4, uy + 2, uio.width + 8, uio.height - 4)
                        scene.tint(env.pythonistacolor(uio.color))
                        scene.translate(ux + uio.width / 2,
                                        uy + uio.height / 2)
                        scene.text(uio.text(), uio.font,
                                   uio.fontsize, alignment=5)
                        scene.tint(1, 1, 1, 1)
                        # required for proper loading of images
                        scene.pop_matrix()
                    elif uio.type == 'slider':
                        scene.push_matrix()
                        scene.tint(env.pythonistacolor(uio.labelcolor))
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
                            if touch.location in\
                                    scene.Rect(ux, uy, uio.width, uio.height):
                                xsel = touch.location[0] - ux
                                vsel = round(-0.5 + xsel /
                                             uio.xdelta) * uio.resolution
                                thisv = vsel
                        scene.stroke(env.pythonistacolor(uio.linecolor))
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
                        scene.translate(xfirst, uy + uio.height + 2)
                        if uio.label:
                            scene.text(uio.label, uio.font, uio.fontsize, alignment=9)
                        scene.pop_matrix()
                        scene.translate(ux + uio.width, uy + uio.height + 2)
                        scene.text(str(thisv) + ' ',
                                   uio.font, uio.fontsize, alignment=7)
                        scene.tint(1, 1, 1, 1)
                        # required for proper loading of images later
                        scene.pop_matrix()
            else:
                width, height = ui.get_screen_size()
                scene.pop_matrix()
                scene.tint(1, 1, 1, 1)
                scene.translate(width / 2, height / 2)
                scene.text('salabim animation paused/stopped')
                scene.pop_matrix()
                scene.tint(1, 1, 1, 1)
            if env is not None:
                if env._video:
                    if not env.paused:
                        env.video_t += env._speed / env._fps
            g.in_draw = False


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
        if q.env._trace:
            if not q._isinternal:
                q.env.print_trace('', '', c.name(), 'enter ' + q.name())
        q.length.tally(q._length)


class Queue(object):
    '''
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

    monitor : bool
        if True (default) , both length and length_of_stay are monitored |n|
        if False, monitoring is disabled.

    env : Environment
        environment where the queue is defined |n|
        if omitted, default_env will be used
    '''

    def __init__(self, name=None, monitor=True, fill=None, env=None, *args, **kwargs):
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
        self.length = MonitorTimestamp(
            'Length of ' + self.name(), initial_tally=0, monitor=monitor, type='uint32', env=self.env)
        self.length_of_stay = Monitor(
            'Length of stay in ' + self.name(), monitor=monitor, type='float')
        if fill is not None:
            savetrace = self.env._trace
            self.env._trace = False
            for c in fill:
                c.enter(self)
            self.env._trace = savetrace
        if self.env._trace:
            self.env.print_trace('', '', self.name() + ' create')
        self.setup(*args, **kwargs)

    def setup(self):
        '''
        called immediately after initialization of a queue.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        '''
        pass

    def animate(self, *args, **kwargs):
        '''
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
            if 'w', waiting line runs westwards (i.e. from right to left) |n|
            if 'n', waiting line runs northeards (i.e. from bottom to top) |n|
            if 'e', waiting line runs eastwards (i.e. from left to right) (default) |n|
            if 's', waiting line runs southwards (i.e. from top to bottom)

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

        '''
        return AnimateQueue(self, *args, **kwargs)

    def reset_monitors(self, monitor=None):
        '''
        resets queue monitor length_of_stay and timestamped monitor length

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

    def register(self, registry):
        '''
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
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self in registry:
            raise SalabimError(self.name() + ' already in registry')
        registry.append(self)
        return self

    def deregister(self, registry):
        '''
        deregisters the queue in the registry

        Parameters
        ----------
        registry : list
            list of registered queues

        Returns
        -------
        queue (self) : Queue
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self not in registry:
            raise SalabimError(self.name() + ' not in registry')
        registry.remove(self)
        return self

    def __repr__(self):
        return objectclass_to_str(self) + '(' + self.name() + ')'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append(objectclass_to_str(self) + ' ' + hex(id(self)))
        result.append('  name=' + self.name())
        if self._length:
            result.append('  component(s):')
            mx = self._head.successor
            while mx != self._tail:
                result.append('    ' + pad(mx.component.name(), 20) +
                    ' enter_time' + time_to_string(mx.enter_time - self.env._offset) +
                    ' priority=' + str(mx.priority))
                mx = mx.successor
        else:
            result.append('  no components')
        return return_or_print(result, as_str, file)

    def print_statistics(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Statistics of {} at {}'.format(self.name(), fn(self.env._now - self.env._offset, 13, 3)))
        result.append(self.length.print_statistics(
            show_header=False, show_legend=True, do_indent=True, as_str=True))

        result.append('')
        result.append(self.length_of_stay.print_statistics(
            show_header=False, show_legend=False, do_indent=True, as_str=True))
        return return_or_print(result, as_str, file)

    def print_histograms(self, exclude=(), as_str=False, file=None):
        '''
        prints the histograms of the length timestamped and length_of_stay monitor of the queue

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
        '''
        result = []
        for m in (self.length, self.length_of_stay):
            if m not in exclude:
                result.append(m.print_histogram(as_str=True))
        return return_or_print(result, as_str, file)

    def name(self, value=None):
        '''
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
        '''
        if value is not None:
            self._name = value
            self.length.name('Length of ' + self.name())
            self.length_of_stay.name('Length of stay of ' + self.name())
        return self._name

    def base_name(self):
        '''
        Returns
        -------
        base name of the queue (the name used at initialization): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the queue : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
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
        or 0 if queue is empty |n|
        This method is equivalent to append()
        '''
        component.enter(self)

    def append(self, component):
        '''
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
        component.enter_at_head(self)

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
        component.enter_in_front_of(self, poscomponent)

    def insert(self, index, component):
        '''
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
        '''
        if index < 0:
            raise SalabimError('index <0')
        if index > self._length:
            raise SalabimError('index > lengh of queue')
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

        priority: type that can be compared with other priorities in the queue
            priority in the queue

        Note
        ----
        The component is placed just before the first component with a priority > given priority
        '''
        component.enter_sorted(self, priority)

    def remove(self, component=None):
        '''
        removes component from the queue

        Parameters
        ----------
        component : Component
            component to be removed |n|
            if omitted, all components will be removed.

        Note
        ----
        component must be member of the queue
        '''
        if component is None:
            self.clear()
        else:
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

    def pop(self, index=None):
        '''
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
        '''
        if index is None:
            c = self._head.successor.component
        else:
            c = self[index]
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

    def __delitem__(self, key):
        if isinstance(key, slice):
            for c in self[key]:
                self.remove(c)
        elif isinstance(key, int):
            self.remove(self[key])
        else:
            raise SalabimError('Invalid argument type')

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

    def __add__(self, q):
        return self.union(q)

    def __or__(self, q):
        return self.union(q)

    def __sub__(self, q):
        return self.difference(q)

    def __and__(self, q):
        return self.intersection(q)

    def __xor__(self, q):
        return self.symmetric_difference(q)

    def count(self, component):
        '''
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
        '''
        return component.count(self)

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
        return component.index(self)

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

    def extend(self, q):
        '''
        extends the queue with components of q that are not already in self

        Parameters
        ----------
        q : queue, list or tuple

        Note
        ----
        The components added to the queue will get the priority of the tail of self.
        '''
        savetrace = self.env._trace
        self.env._trace = False
        for c in q:
            if c not in self:
                c.enter(q)
        self.env._trace = savetrace

    def as_set(self):
        return {c for c in self}

    def as_list(self):
        return [c for c in self]

    def union(self, q, name=None, monitor=False):
        '''
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
        '''
        save_trace = self.env._trace
        self.env._trace = False
        if name is None:
            name = self.name() + ' | ' + q.name()
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
        '''
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
        '''
        save_trace = self.env._trace
        self.env._trace = False
        if name is None:
            name = self.name() + ' & ' + q.name()
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
        '''
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
        '''
        if name is None:
            name = self.name() + ' - ' + q.name()
        save_trace = self.env._trace
        self.env._trace = False
        q1 = type(self)(name=name, monitor=monitor, env=self.env)
        q_set = q.as_set()
        mx = self._head.successor
        while mx != self._tail:
            if mx.component not in q_set:
                Qmember().insert_in_front_of(
                    q1._tail, mx.component, q1, mx.priority)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def symmetric_difference(self, q, name=None, monitor=monitor):
        '''
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
        '''
        if name is None:
            name = self.name() + ' ^ ' + q.name()
        save_trace = self.env._trace
        self.env._trace = False
        q1 = type(self)(name=name, monitor=monitor, env=self.env)

        intersection_set = self.as_set() & q.as_set()
        mx = self._head.successor
        while mx != self._tail:
            if mx.component not in intersection_set:
                Qmember().insert_in_front_of(
                    q1._tail, mx.component, q1, 0)
            mx = mx.successor
        mx = q._head.successor
        while mx != q._tail:
            if mx.component not in intersection_set:
                Qmember().insert_in_front_of(
                    q1._tail, mx.component, q1, 0)
            mx = mx.successor

        self.env._trace = save_trace
        return q1

    def copy(self, name=None, monitor=monitor):
        '''
        returns a copy of two queues

        Parameters
        ----------
        name : str
            name of the new queue |n|
            if omitted, 'copy of ' + self.name()

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the queue

        Returns
        -------
        queue with all elements of self : Queue

        Note
        ----
        The priority will be copied from original queue.
        Also, the order will be maintained.
        '''
        save_trace = self.env._trace
        self.env._trace = False
        if name is None:
            name = 'copy of ' + self.name()
        q1 = type(self)(name=name, env=self.env)
        mx = self._head.successor
        while mx != self._tail:
            Qmember().insert_in_front_of(q1._tail, mx.component, q1, mx.priority)
            mx = mx.successor
        self.env._trace = save_trace
        return q1

    def move(self, name=None, monitor=monitor):
        '''
        makes a copy of a queue and empties the original

        Parameters
        ----------
        name : str
            name of the new queue

        monitor : bool
            if True, monitor the queue |n|
            if False (default), do not monitor the yqueue

        Returns
        -------
        queue containing all elements of self: Queue

        Note
        ----
        Priorities will be kept |n|
        self will be emptied
        '''
        q1 = self.copy(name, monitor=monitor)
        self.clear()
        return q1

    def clear(self):
        '''
        empties a queue

        removes all components from a queue
        '''
        savetrace = self.env._trace
        self.env._trace = False
        mx = self._head.successor
        while mx != self._tail:
            c = mx.component
            mx = mx.successor
            c.leave(self)
        self._trace = savetrace
        if self.env._trace:
            self.env.print_trace('', '', self.name() + ' clear')


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
        if '*', a purely random value (based on the current time) will be used
        (not reproducable) |n|
        if the null string (''), no action on random is taken |n|
        if None (the default), 1234567 will be used.

    name : str
        name of the environment |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class (lowercased)
        or 'default environment' if isdefault_env is True.

    print_trace_header : bool
        if True (default) print a (two line) header line as a legend |n|
        if False, do not print a header |n|
        note that the header is only printed if trace=True

    isdefault_env : bool
        if True (default), this environment becomes the default environment |n|
        if False, this environment will not be the default environment |n|
        if omitted, this environment becomes the default environment |n|

    Note
    ----
    The trace may be switched on/off later with trace |n|
    The seed may be later set with random_seed() |n|
    Initially, the random stream will be seeded with the value 1234567.
    If required to be purely, not not reproducable, values, use
    random_seed='*'.
    '''
    _nameserialize = {}
    cached_modelname_width = [None, None]

    def __init__(self, trace=False, random_seed=None, name=None,
      print_trace_header=True, isdefault_env=True, *args, **kwargs):
        if isdefault_env:
            g.default_env = self
        if name is None:
            if isdefault_env:
                name = 'default environment'
        self._trace = trace
        self._source_files = {inspect.getframeinfo(_get_caller_frame()).filename: 0}
        if random_seed != '':
            if random_seed is None:
                random_seed = 1234567
            elif random_seed == '*':
                random_seed = None
            random.seed(random_seed)
        _set_name(name, Environment._nameserialize, self)
        self._buffered_trace = False
        self._suppress_trace_standby = True
        if self._trace:
            if print_trace_header:
                self.print_trace_header()
            self.print_trace('', '', self.name() + ' initialize')
        self.env = self
        # just to allow main to be created; will be reset later
        self._nameserializeComponent = {}
        self._now = 0
        self._offset = 0
        self._main = Component(name='main', env=self, process=None)
        self._main._status = current
        self._main.frame = _get_caller_frame()
        self._current_component = self._main
        if self._trace:
            self.print_trace('{:10.3f}'.format(0), 'main', 'current')
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
        self.sys_objects = []
        self.serial = 0
        self._speed = 1
        self._animate = False
        self.running = False
        self.t = 0
        self.video_t = 0
        self._synced = True
        self._step_pressed = False
        self.stopped = False
        self.last_s0 = ''
        if Pythonista:
            self._width, self._height = ui.get_screen_size()
            self._width = int(self._width)
            self._height = int(self._height)
        else:
            self._width = 1024
            self._height = 768
        self._x0 = 0
        self._y0 = 0
        self._x1 = self._width
        self._scale = 1
        self._y1 = self._y0 + self._height
        self._background_color = 'white'
        self._foreground_color = 'black'
        self._fps = 30
        self._modelname = ''
        self.use_toplevel = False
        self._show_fps = False
        self._show_time = True
        self._video = ''
        self._video_out = None
        self._video_repeat = 1
        self._video_pingpong = False
        self.an_modelname()
        self.an_clocktext()

        self.setup(*args, **kwargs)

    def setup(self):
        '''
        called immediately after initialization of an environment.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        '''
        pass

    def serialize(self):
        self.serial += 1
        return self.serial

    def __repr__(self):
        return objectclass_to_str(self) + ' (' + self.name() + ')'

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

    def animation_pre_tick_sys(self, t):
        for ao in self.sys_objects:
            ao.update(t)

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append(objectclass_to_str(self) + ' ' + hex(id(self)))
        result.append('  name=' + self.name())
        result.append('  now=' + time_to_string(self._now - self._offset))
        result.append('  current_component=' + self._current_component.name())
        result.append('  trace=' + str(self._trace))
        return return_or_print(result, as_str, file)

    def step(self):
        '''
        executes the next step of the future event list

        for advanced use with animation / GUI loops
        '''
        if not self._current_component._skip_standby:
            if len(self.env._pendingstandbylist) > 0:
                c = self.env._pendingstandbylist.pop(0)
                if c._status == standby:  # skip cancelled components
                    c._status = current
                    c._scheduled_time = inf
                    self.env._current_component = c
                    if self._trace:
                        self.print_trace('{:10.3f}'.format(self._now - self.env._offset), c.name(),
                            'current (standby)', s0=c.lineno_txt(), _optional=self._suppress_trace_standby)
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
            (t, _, c) = heapq.heappop(self._event_list)
        else:
            c = self._main
            if self.end_on_empty_eventlist:
                t = self.env._now
                self.print_trace('', '', 'run ended', 'no events left', s0=c.lineno_txt())
            else:
                t = inf
        c._on_event_list = False
        self.env._now = t

        self._current_component = c

        c._status = current
        c._scheduled_time = inf
        if self._trace:
            self.print_trace('{:10.3f}'.format(self._now - self._offset), c.name(),
              'current', s0=c.lineno_txt())
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

    def _terminate(self, c):
        if c._process_isgenerator:
            if self._trace:
                gi_code = c._process.gi_code
                gs = inspect.getsourcelines(gi_code)
                s0 = self.filename_lineno_to_str(gi_code.co_filename, len(gs[0]) + gs[1] - 1) + '+'
            else:
                s0 = None
        else:
            if self._trace:
                gs = inspect.getsourcelines(c._process)
                s0 = self.filename_lineno_to_str(c._process.__code__.co_filename, len(gs[0]) + gs[1] - 1) + '+'
            else:
                s0 = None

        for r in list(c._claims):
            c._release(r, s0=s0)
        if self._trace:
            self.print_trace('', '', c.name() + ' ended', s0=s0)
        c._status = data
        c._scheduled_time = inf
        c._process = None
        for ao in self.an_objects[:]:
            if ao.parent == c:
                self.an_objects.remove(ao)
        for so in self.sys_objects[:]:
            if so.parent == c:
                so.remove()

    def _print_event_list(self, s):
        print('eventlist ', s)
        for (t, seq, comp) in self._event_list:
            print('{:10.3f} {}'.format(t, comp.name()))

    def animation_parameters(self,
      animate=True, synced=None, speed=None, width=None, height=None,
      x0=None, y0=None, x1=None, background_color=None, foreground_color=None,
      fps=None, modelname=None, use_toplevel=None,
      show_fps=None, show_time=None,
      video=None, video_repeat=None, video_pingpong=None):
        '''
        set animation parameters

        Parameters
        ----------
        animate : bool
            animate indicator |n|
            if not specified, set animate on |n|

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
            if True, show the number of frames per second |n|
            if False, do not show the number of frames per second (default)

        show_time: bool
            if True, show the time (default)  |n|
            if False, do not show the time

        video : str
            if video is not omitted, a video with the name video
            will be created. |n|
            Normally, use .mp4 as extension. |n|
            If the video extension is not .gif, a codec may be added
            by appending a plus sign and the four letter code name,
            like 'myvideo.avi+DIVX'. |n|
            If no codec is given, MP4V will be used as codec.

        video_repeat : int
            number of times gif should be repeated |n|
            0 means inifinite |n|
            at init of the environment video_repeat is 1 |n|
            this only applies to gif files production.

        video_pingpong : bool
            if True, all frames will be added reversed at the end of the video (useful for smooth loops)
            at init of the environment video_pingpong is False |n|
            this only applies to gif files production.

        Note
        ----
        The y-coordinate of the upper right corner is determined automatically
        in such a way that the x and scaling are the same. |n|
        '''
        frame_changed = False
        width_changed = False
        height_changed = False
        fps_changed = False
        if speed is not None:
            self._speed = speed
            self.set_start_animation()

        if show_fps is not None:
            if show_fps != show_fps:
                self._show_fps = show_fps

        if show_time is not None:
            self._show_time = show_time

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

        if fps is not None:
            if self._fps != fps:
                self._fps = fps
                fps_changed = True

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
            if background_color in ('fg', 'bg'):
                raise SalabimError(background_color + 'not allowed for background_color')
            if self._background_color != background_color:
                self._background_color = background_color
                frame_changed = True
            if foreground_color is None:
                self._foreground_color = 'white' if self.is_dark('bg') else 'black'

        if foreground_color is not None:
            if foreground_color in ('fg', 'bg'):
                raise SalabimError(foreground_color + 'not allowed for foreground_color')
            self._foreground_color = foreground_color

        if modelname is not None:
            self._modelname = modelname

        if use_toplevel is not None:
            self.use_toplevel = use_toplevel

        if animate is None:
            animate = self._animate  # no change
        else:
            if animate != self._animate:
                frame_changed = True

        self._scale = self._width / (self._x1 - self._x0)
        self._y1 = self._y0 + self._height / self._scale

        if g.animation_env is not self:
            if g.animation_env is not None:
                g.animation_env.video_close()
            if animate:
                frame_changed = True
            else:
                frame_changed = False  # no animation required, so leave running animation_env untouched

        if video_repeat is not None:
            self._video_repeat = video_repeat

        if video_pingpong is not None:
            self._video_pingpong = video_pingpong

        video_opened = False
        if video is not None:
            if video != self._video:
                if self._video:
                    self.video_close()
                self._video = video

                if video:
                    video_opened = True
                    extension = os.path.splitext(video)[1].lower()
                    if extension == '.gif':
                        self._video_name = video
                        can_animate(try_only=False)
                        self._video_out = 'gif'
                        self._images = []
                    else:
                        if len(video.split('+')) == 2:
                            self._video_name, codec = video.split('+')
                        else:
                            self._video_name = video
                            codec = 'MP4V'
                        can_video(try_only=False)
                        fourcc = cv2.VideoWriter_fourcc(*codec)
                        self._video_out = cv2.VideoWriter(
                            self._video_name, fourcc, self._fps, (self._width, self._height))

        if self._video and (not video_opened):
            if width_changed:
                raise SalabimError('width changed while recording video.')
            if height_changed:
                raise SalabimError('height changed while recording video.')
            if fps_changed and self._video_out != 'gif':
                raise SalabimError('fps changed while recording video.')

        if self._video:
            self.video_t = self.t

        if frame_changed:
            if g.animation_env is not None:
                g.animation_env._animate = animate
                if not Pythonista:
                    g.animation_env.root.destroy()
                g.animation_env = None

            if animate:
                can_animate(try_only=False)  # install modules

                g.animation_env = self
                self.t = self._now  # for the call to set_start_animation
                self.set_start_animation()

                self.paused = False

                if Pythonista:
                    if g.animation_scene is None:
                        g.animation_scene = AnimationScene(env=self)
                        scene.run(g.animation_scene, frame_interval=1, show_fps=False)

                else:
                    if self.use_toplevel:
                        self.root = tkinter.Toplevel()
                    else:
                        self.root = tkinter.Tk()
                    g.canvas = tkinter.Canvas(
                        self.root, width=self._width, height=self._height)
                    g.canvas.configure(background=self.colorspec_to_hex('bg', False))
                    g.canvas.pack()
                    g.canvas_objects = []

                self.uninstall_uios()  # this causes all ui objects to be (re)installed

                self.an_menu_buttons()

        self._animate = animate

    def video_close(self):
        '''
        closes the current animation video recording, if any.
        '''
        if self._video_out:
            if self._video_out == 'gif':
                if self._images:
                    if self._video_pingpong:
                        self._images.extend(self._images[::-1])
                    if Pythonista:
                        import images2gif
                        images2gif.writeGif(self._video_name, self._images,
                           duration=1 / self._fps, repeat=self._video_repeat)
                    else:
                        self._images[0].save(self._video_name, save_all=True,
                            append_images=self._images[1:], loop=self._video_repeat, duration=1000 / self._fps)
                    self._images = []  # release memory
            else:
                self._video_out.release()
            self._video_out = None
            self._video = ''

    def uninstall_uios(self):
        for uio in self.ui_objects:
            uio.installed = False

    def x0(self, value=None):
        '''
        x coordinate of lower left corner of animation

        Parameters
        ----------
        value : float
            new x coordinate

        Returns
        -------
        x coordinate of lower left corner of animation : float
        '''
        if value is not None:
            self.animation_parameters(x0=value, animate=None)
        return self._x0

    def x1(self, value=None):
        '''
        x coordinate of upper right corner of animation : float

        Parameters
        ----------
        value : float
            new x coordinate |n|
            if not specified, no change

        Returns
        -------
        x coordinate of upper right corner of animation : float
        '''
        if value is not None:
            self.animation_parameters(x1=value, animate=None)
        return self._x1

    def y0(self, value=None):
        '''
        y coordinate of lower left corner of animation

        Parameters
        ----------
        value : float
            new y coordinate |n|
            if not specified, no change

        Returns
        -------
        y coordinate of lower left corner of animation : float
        '''
        if value is not None:
            self.animation_parameters(y0=value, animate=None)
        return self._y0

    def y1(self):
        '''
        y coordinate of upper right corner of animation

        Returns
        -------
        y coordinate of upper right corner of animation : float

        Note
        ----
        It is not possible to set this value explicitely.
        '''
        return self._y1

    def scale(self):
        '''
        scale of the animation, i.e. width / (x1 - x0)

        Returns
        -------
        scale : float

        Note
        ----
        It is not possible to set this value explicitely.
        '''
        return self._scale

    def user_to_screencoordinates_x(self, userx):
        '''
        converts a user x coordinate to a screen x coordinate

        Parameters
        ----------
        userx : float
            user x coordinate to be converted

        Returns
        -------
        screen x coordinate : float
        '''
        return (userx - self._x0) * self._scale

    def user_to_screencoordinates_y(self, usery):
        '''
        converts a user x coordinate to a screen x coordinate

        Parameters
        ----------
        usery : float
            user y coordinate to be converted

        Returns
        -------
        screen y coordinate : float
        '''
        return (usery - self._y0) * self._scale

    def user_to_screencoordinates_size(self, usersize):
        '''
        converts a user size to a value to be used with screen coordinates

        Parameters
        ----------
        usersize : float
            user size to be converted

        Returns
        -------
        value corresponding with usersize in screen coordinates : float
        '''
        return usersize * self._scale

    def screen_to_usercoordinates_x(self, screenx):
        '''
        converts a screen x coordinate to a user x coordinate

        Parameters
        ----------
        screenx : float
            screen x coordinate to be converted

        Returns
        -------
        user x coordinate : float
        '''
        return self._x0 + screenx / self._scale

    def screen_to_usercoordinates_y(self, screeny):
        '''
        converts a screen x coordinate to a user x coordinate

        Parameters
        ----------
        screeny : float
            screen y coordinate to be converted

        Returns
        -------
        user y coordinate : float
        '''
        return self._y0 + screeny / self._scale

    def screen_to_usercoordinates_size(self, screensize):
        '''
        converts a screen size to a value to be used with user coordinates

        Parameters
        ----------
        screensize : float
            screen size to be converted

        Returns
        -------
        value corresponding with screensize in user coordinates : float
        '''
        return screensize / self._scale

    def width(self, value=None):
        '''
        width of the animation in screen coordinates

        Parameters
        ----------
        value : int
            new width |n|
            if not specified, no change


        Returns
        -------
        width of animation : int
        '''
        if value is not None:
            self.animation_parameters(width=value, animate=None)
        return self._width

    def height(self, value=None):
        '''
        height of the animation in screen coordinates

        Parameters
        ----------
        value : int
            new height |n|
            if not specified, no change

        Returns
        -------
        height of animation : int
        '''
        if value is not None:
            self.animation_parameters(height=value, animate=None)
        return self._height

    def background_color(self, value=None):
        '''
        background_color of the animation

        Parameters
        ----------
        value : colorspec
            new background_color |n|
            if not specified, no change

        Returns
        -------
        background_color of animation : colorspec
        '''
        if value is not None:
            self.animation_parameters(background_color=value, animate=None)
        return self._background_color

    def foreground_color(self, value=None):
        '''
        foreground_color of the animation

        Parameters
        ----------
        value : colorspec
            new foreground_color |n|
            if not specified, no change

        Returns
        -------
        foreground_color of animation : colorspec
        '''
        if value is not None:
            self.animation_parameters(foreground_color=value, animate=None)
        return self._foreground_color

    def animate(self, value=None):
        '''
        animate indicator

        Parameters
        ----------
        value : bool
            new animate indicator |n|
            if not specified, no change

        Returns
        -------
        animate status : bool

        Note
        ----
        When the run is not issued, no acction will be taken.
        '''
        if value is not None:
            self.animation_parameters(animate=value)
        return self._animate

    def modelname(self, value=None):
        '''
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
        '''
        if value is not None:
            self.animation_parameters(modelname=value, animate=None)
        return self._modelname

    def video(self, value=None):
        '''
        video name

        Parameters
        ----------
        value : str, list or tuple
            new video name |n|
            if not specified, no change |n|
            for explanation see animation_parameters()

        Returns
        -------
        video : str, list or tuple

        Note
        ----
        If video is the null string, the video (if any) will be closed.
        '''
        if value is not None:
            self.animation_parameters(video=value, animate=None)
        return self._video

    def video_repeat(self, value=None):
        '''
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
        '''
        if value is not None:
            self.animation_parameters(video_repeat=value, animate=None)
        return self._video_repeat

    def video_pingpong(self, value=None):
        '''
        video pingponf

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
        '''
        if value is not None:
            self.animation_parameters(video_pingpong=value, animate=None)
        return self._video_pingpong

    def fps(self, value=None):
        '''
        fps

        Parameters
        ----------
        value : int
            new fps |n|
            if not specified, no change

        Returns
        -------
        fps : bool
        '''
        if value is not None:
            self.animation_parameters(fps=value, animate=None)
        return self._fps

    def show_time(self, value=None):
        '''
        show_time

        Parameters
        ----------
        value : bool
            new show_time |n|
            if not specified, no change

        Returns
        -------
        show_time : bool
        '''
        if value is not None:
            self.animation_parameters(show_time=value, animate=None)
        return self._show_time

    def show_fps(self, value=None):
        '''
        show_fps

        Parameters
        ----------
        value : bool
            new show_fps |n|
            if not specified, no change

        Returns
        -------
        show_fps : bool
        '''
        if value is not None:
            self.animation_parameters(show_fps=value, animate=None)
        return self._show_fps

    def synced(self, value=None):
        '''
        synced

        Parameters
        ----------
        value : bool
            new synced |n|
            if not specified, no change

        Returns
        -------
        synced : bool
        '''
        if value is not None:
            self.animation_parameters(synced=value, animate=None)
        return self._synced

    def speed(self, value=None):
        '''
        speed

        Parameters
        ----------
        value : float
            new speed |n|
            if not specified, no change

        Returns
        -------
        speed : float
        '''
        if value is not None:
            self.animation_parameters(speed=value, animate=None)
        return self._speed

    def peek(self):
        '''
        returns the time of the next component to become current |n|
        if there are no more events, peek will return inf |n|
        Only for advance use with animation / GUI event loops
        '''
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
        return self._now - self.env._offset

    def reset_now(self, new_now=0):
        '''
        reset the current time

        Parameters
        ----------
        new_now : float
            now will be set to new_now |n|
            default: 0

        Note
        ----
        Internally, salabim still works with the 'old' time. Only in the interface
        from and to the user program, a correction will be applied.

        The registered time in timestamped monitors will be always is the 'old' time.
        This is only relevant when using the time value in MonitorTimestamp.xt() or
        MonitorTimestamp.tx().
        '''
        offset_before = self._offset
        self._offset = self._now - new_now

        if self._trace:
            self.print_trace(
                '', '', 'now reset to {:0.3f}'.format(new_now),
                '(all times are reduced by {:0.3f})'.format(self._offset - offset_before))

    def trace(self, value=None):
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
        if value is not None:
            self._trace = value
            self._buffered_trace = False
        return self._trace

    def suppress_trace_standby(self, value=None):
        '''
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
        '''
        if value is not None:
            self._suppress_trace_standby = value
            self._buffered_trace = False
        return self._suppress_trace_standby

    def current_component(self):
        '''
        Returns
        -------
        the current_component : Component
        '''
        return self._current_component

    def run(self, duration=None, till=None, urgent=False):
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

        urgent : bool
            urgency indicator |n|
            if False (default), main will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, main will be scheduled
            in front of all components scheduled
            for the same time

        Note
        ----
        if neither till nor duration is specified, the main component will be reactivated at
        the time there are no more events on the eventlist, i.e. usualy not at inf. |n|
        if you want to run till inf, issue run(sim.inf) |n|
        only issue run() from the main level
        '''

        self.end_on_empty_eventlist = False
        extra = ''
        if till is None:
            if duration is None:
                scheduled_time = inf
                self.end_on_empty_eventlist = True
                extra = '*'
            else:
                if duration == inf:
                    scheduled_time = inf
                else:
                    scheduled_time = self.env._now + duration
        else:
            if duration is None:
                scheduled_time = till + self.env._offset
            else:
                raise SalabimError('both duration and till specified')

        self._main.frame = _get_caller_frame()
        self._main._reschedule(scheduled_time, urgent, 'run', extra=extra)

        self.running = True
        while self.running:
            if self._animate:
                self.do_simulate_and_animate()
            else:
                self.do_simulate()
        if self.stopped:
            self.quit()

    def do_simulate(self):
        while g.in_draw:
            pass
        while self.running and not self._animate:
            self.step()

    def do_simulate_and_animate(self):
        if Pythonista:
            while self.running and self._animate:
                pass
        else:
            self.root.after(0, self.simulate_and_animate_loop)
            self.root.mainloop()

    def simulate_and_animate_loop(self):

        while True:
            tick_start = time.time()

            if self._synced or self._video:  # video forces synced
                if self._video:
                    self.t = self.video_t
                else:
                    if self.paused:
                        self.t = self.start_animation_time
                    else:
                        self.t = self.start_animation_time +\
                            ((time.time() - self.start_animation_clocktime) *
                            self._speed)

                while self.peek() < self.t:
                    self.step()
                    if not (self.running and self._animate):
                        self.root.quit()
                        return
            else:
                if self._step_pressed or (not self.paused):
                    self.step()

                    if not self._current_component._suppress_pause_at_step:
                        self._step_pressed = False
                    self.t = self._now

            if not (self.running and self._animate):
                self.root.quit()
                return

            if self._video:
                capture_image = Image.new(
                    'RGB', (self._width, self._height), self.colorspec_to_tuple('bg'))
            if not self.paused:
                self.frametimes.append(time.time())

            self.an_objects.sort(
                key=lambda obj: (-obj.layer(self.t), obj.sequence))

            canvas_objects_iter = iter(g.canvas_objects[:])
            co = next(canvas_objects_iter, None)
            self.animation_pre_tick(self.t)
            self.animation_pre_tick_sys(self.t)
            for ao in self.an_objects:
                ao.make_pil_image(self.t)

                if ao._image_visible:
                    if co is None:
                        ao.im = ImageTk.PhotoImage(ao._image)
                        co1 = g.canvas.create_image(
                            ao._image_x, self._height - ao._image_y, image=ao.im, anchor=tkinter.SW)
                        g.canvas_objects.append(co1)
                        ao.canvas_object = co1

                    else:
                        if ao.canvas_object == co:
                            if ao._image_ident != ao._image_ident_prev:
                                ao.im = ImageTk.PhotoImage(ao._image)
                                g.canvas.itemconfig(
                                    ao.canvas_object, image=ao.im)

                            if (ao._image_x != ao._image_x_prev) or (ao._image_y != ao._image_y_prev):
                                g.canvas.coords(
                                    ao.canvas_object, (ao._image_x, self._height - ao._image_y))

                        else:
                            ao.im = ImageTk.PhotoImage(ao._image)
                            ao.canvas_object = co
                            g.canvas.itemconfig(
                                ao.canvas_object, image=ao.im)
                            g.canvas.coords(
                                ao.canvas_object, (ao._image_x, self._height - ao._image_y))
                    co = next(canvas_objects_iter, None)

                    if self._video:
                        capture_image.paste(ao._image,
                            (int(ao._image_x), int(self._height - ao._image_y - ao._image.size[1])),
                            ao._image)
                else:
                    ao.canvas_object = None

            self.animation_post_tick(self.t)

            while co is not None:
                g.canvas.delete(co)
                g.canvas_objects.remove(co)
                co = next(canvas_objects_iter, None)

            for uio in self.ui_objects:
                if not uio.installed:
                    uio.install()

            for uio in self.ui_objects:
                if uio.type == 'button':
                    thistext = uio.text()
                    if thistext != uio.lasttext:
                        uio.lasttext = thistext
                        uio.button.config(text=thistext)

            if self._video and (not self.paused):
                if self._video_out == 'gif':
                    self._images.append(capture_image)
                else:
                    open_cv_image = cv2.cvtColor(
                        np.array(capture_image), cv2.COLOR_RGB2BGR)
                    self._video_out.write(open_cv_image)

            g.canvas.update()
            if self._video:
                if not self.paused:
                    self.video_t += self._speed / self._fps
            else:
                if self._synced:
                    tick_duration = time.time() - tick_start
                    if tick_duration < 1 / self._fps:
                        time.sleep(((1 / self._fps) - tick_duration) * 0.8)
                        # 0.8 compensation because of clock inaccuracy

    def snapshot(self, filename):
        '''
        Takes a snapshot of the current animated frame (at time = now()) and saves it to a file

        Parameters
        ----------
        filename : str
            file to save the current animated frame to. |n|
            The following formats are accepted: .PNG, .JPG, .BMP, .GIF and .TIFF are supported.
            Other formats are not possible.
            Note that, apart from .JPG files. the background may be semi transparent by setting
            the alpha value to something else than 255.
        '''
        can_animate(try_only=False)
        extension = os.path.splitext(filename)[1].lower()
        if extension in ('.png', '.gif', '.bmp', '.tiff'):
            mode = 'RGBA'
        elif extension == '.jpg':
            mode = 'RGB'
        else:
            raise SalabimError('extension ' + extension + '  not supported')
        capture_image = Image.new(
            mode, (self._width, self._height), self.colorspec_to_tuple('bg'))
        self.an_objects.sort(
            key=lambda obj: (-obj.layer(self.t), obj.sequence))
        self.animation_pre_tick(self._now)
        self.animation_pre_tick_sys(self._now)
        for ao in self.an_objects:
            ao.make_pil_image(self._now)
            if ao._image_visible:
                capture_image.paste(ao._image,
                    (int(ao._image_x), int(self._height - ao._image_y - ao._image.size[1])),
                    ao._image)
        capture_image.save(filename)

    def modelname_width(self):
        if Environment.cached_modelname_width[0] != self._modelname:
            Environment.cached_modelname_width = \
                [self._modelname, self.env.getwidth(self._modelname + ' : a ', font='', fontsize=18)]
        return Environment.cached_modelname_width[1]

    def modelname_text(self, t):
        return self._modelname + ' : a'

    def modelname_visible(self, t):
        return self._modelname != ''

    def modelname_x_logo(self, t):
        return self.modelname_width() + 8

    def modelname_x_model(self, t):
        return self.modelname_width() + 69

    def modelname_image(self, t):
        return self.salabim_logo()

    def an_modelname(self):
        '''
        function to show the modelname |n|
        called by run(), if animation is True. |n|
        may be overridden to change the standard behaviour.
        '''

        y = -68
        an = Animate(text='',
             x0=8, y0=y,
             anchor='w', fontsize0=18,
             screen_coordinates=True, xy_anchor='nw', env=self)
        an.visible = self.modelname_visible
        an.text = self.modelname_text
        an = Animate(image='',
             y0=y + 1, offsety0=5,
             anchor='w', width0=61,
             screen_coordinates=True, xy_anchor='nw', env=self)
        an.visible = self.modelname_visible
        an.x = self.modelname_x_logo
        an.image = self.modelname_image
        an = Animate(text=' model',
             y0=y,
             anchor='w', fontsize0=18,
             screen_coordinates=True, xy_anchor='nw', env=self)
        an.visible = self.modelname_visible
        an.x = self.modelname_x_model

    def an_menu_buttons(self):
        '''
        function to initialize the menu buttons |n|
        may be overridden to change the standard behaviour.
        '''
        self.remove_topleft_buttons()
        if self.colorspec_to_tuple('bg')[:-1] == self.colorspec_to_tuple('blue')[:-1]:
            fillcolor = 'white'
            color = 'blue'
        else:
            fillcolor = 'blue'
            color = 'white'
        uio = AnimateButton(x=38, y=-21, text='Menu',
            width=50, action=self.env.an_menu, env=self, fillcolor=fillcolor, color=color, xy_anchor='nw')

        uio.in_topleft = True

    def an_unsynced_buttons(self):
        '''
        function to initialize the unsynced buttons |n|
        may be overridden to change the standard behaviour.
        '''
        self.remove_topleft_buttons()
        if self.colorspec_to_tuple('bg')[:-1] == self.colorspec_to_tuple('green')[:-1]:
            fillcolor = 'lightgreen'
            color = 'green'
        else:
            fillcolor = 'green'
            color = 'white'
        uio = AnimateButton(x=38, y=-21, text='Go',
          width=50, action=self.env.an_go, env=self, fillcolor=fillcolor, color=color, xy_anchor='nw')
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 1 * 60, y=-21, text='Step',
          width=50, action=self.env.an_step, env=self, xy_anchor='nw')
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 3 * 60, y=-21, text='Synced',
          width=50, action=self.env.an_synced_on, env=self, xy_anchor='nw')
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 4 * 60, y=-21, text='Trace',
          width=50, action=self.env.an_trace, env=self, xy_anchor='nw')
        uio.in_topleft = True

        if self.colorspec_to_tuple('bg')[:-1] == self.colorspec_to_tuple('red')[:-1]:
            fillcolor = 'lightsalmon'
            color = 'white'
        else:
            fillcolor = 'red'
            color = 'white'
        uio = AnimateButton(x=38 + 5 * 60, y=-21, text='Stop',
          width=50, action=self.env.quit, env=self, fillcolor=fillcolor, color=color, xy_anchor='nw')
        uio.in_topleft = True

        uio = Animate(x0=38 + 3 * 60, y0=-35, text='',
          anchor='N', fontsize0=15,
          screen_coordinates=True, xy_anchor='nw')
        uio.text = self.syncedtext
        uio.in_topleft = True

        uio = Animate(x0=38 + 4 * 60, y0=-35, text='',
          anchor='N', fontsize0=15,
          screen_coordinates=True, xy_anchor='nw')
        uio.text = self.tracetext
        uio.in_topleft = True

    def an_synced_buttons(self):
        '''
        function to initialize the synced buttons |n|
        may be overridden to change the standard behaviour.
        '''
        self.remove_topleft_buttons()
        if self.colorspec_to_tuple('bg')[:-1] == self.colorspec_to_tuple('green')[:-1]:
            fillcolor = 'lightgreen'
            color = 'green'
        else:
            fillcolor = 'green'
            color = 'white'

        uio = AnimateButton(x=38, y=-21, text='Go',
          width=50, action=self.env.an_go, env=self, fillcolor=fillcolor, color=color, xy_anchor='nw')
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 1 * 60, y=-21, text='/2',
          width=50, action=self.env.an_half, env=self, xy_anchor='nw')
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 2 * 60, y=-21, text='*2',
          width=50, action=self.env.an_double, env=self, xy_anchor='nw')
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 3 * 60, y=-21, text='Synced',
          width=50, action=self.env.an_synced_off, env=self, xy_anchor='nw')
        uio.in_topleft = True

        uio = AnimateButton(x=38 + 4 * 60, y=-21, text='Trace',
          width=50, action=self.env.an_trace, env=self, xy_anchor='nw')
        uio.in_topleft = True

        if self.colorspec_to_tuple('bg') == self.colorspec_to_tuple('red'):
            fillcolor = 'lightsalmon'
            color = 'white'
        else:
            fillcolor = 'red'
            color = 'white'
        uio = AnimateButton(x=38 + 5 * 60, y=-21, text='Stop',
          width=50, action=self.env.an_quit, env=self, fillcolor=fillcolor, color=color, xy_anchor='nw')
        uio.in_topleft = True

        uio = Animate(x0=38 + 1.5 * 60, y0=-35, text='',
          textcolor0='fg', anchor='N', fontsize0=15,
          screen_coordinates=True, xy_anchor='nw')
        uio.text = self.speedtext
        uio.in_topleft = True

        uio = Animate(x0=38 + 3 * 60, y0=-35, text='',
          anchor='N', fontsize0=15,
          screen_coordinates=True, xy_anchor='nw')
        uio.text = self.syncedtext
        uio.in_topleft = True

        uio = Animate(x0=38 + 4 * 60, y0=-35, text='',
          anchor='N', fontsize0=15,
          screen_coordinates=True, xy_anchor='nw')
        uio.text = self.tracetext
        uio.in_topleft = True

    def remove_topleft_buttons(self):
        for uio in self.ui_objects[:]:
            if getattr(uio, 'in_topleft', False):
                uio.remove()

        for ao in self.an_objects[:]:
            if getattr(ao, 'in_topleft', False):
                ao.remove()

    def an_clocktext(self):
        '''
        function to initialize the system clocktext |n|
        called by run(), if animation is True. |n|
        may be overridden to change the standard behaviour.
        '''
        ao = Animate(x0=-30 if Pythonista else 0, y0=-11 if Pythonista else 0, textcolor0='fg',
            text='', fontsize0=15, font='mono', anchor='ne',
            screen_coordinates=True, xy_anchor='ne', env=self)
        ao.text = self.clocktext

    def an_half(self):
        self._speed /= 2

    def an_double(self):
        self._speed *= 2

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
            self.root.destroy()
        self.quit()

    def quit(self):
        if g.animation_env is not None:
            g.animation_env.animation_parameters(animate=False, video='')  # stop animation
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

    def an_menu(self):
        self.paused = True
        self.set_start_animation()
        if self._synced:
            self.an_synced_buttons()
        else:
            self.an_unsynced_buttons()

    def clocktext(self, t):
        s = ''
        if self._synced and (not self.paused) and self._show_fps:
            if len(self.frametimes) >= 2:
                fps = (len(self.frametimes) - 1) / \
                    (self.frametimes[-1] - self.frametimes[0])
            else:
                fps = 0
            s += 'fps={:.1f}'.format(fps)

        if self._show_time:
            if s != '':
                s += ' '
            s += 't={:.3f}'.format(t - self.env._offset)
        return s

    def tracetext(self, t):
        if self._trace:
            return '= on'
        else:
            return '= off'

    def syncedtext(self, t):
        if self._synced:
            return '= on'
        else:
            return '= off'

    def speedtext(self, t):
        return 'speed = {:.3f}'.format(self._speed)

    def set_start_animation(self):
        self.frametimes = collections.deque(maxlen=30)
        self.start_animation_time = self.t
        self.start_animation_clocktime = time.time()

    def xy_anchor_to_x(self, xy_anchor, screen_coordinates):
        if xy_anchor in ('nw', 'w', 'sw'):
            if screen_coordinates:
                return 0
            else:
                return self._x0

        if xy_anchor in ('n', 'c', 'center', 's'):
            if screen_coordinates:
                return self._width / 2
            else:
                return (self._x0 + self._x1) / 2

        if xy_anchor in ('ne', 'e', 'se', ''):
            if screen_coordinates:
                return self._width
            else:
                return self._x1

        raise SalabimError('incorrect xy_anchor', xy_anchor)

    def xy_anchor_to_y(self, xy_anchor, screen_coordinates):
        if xy_anchor in ('nw', 'n', 'ne'):
            if screen_coordinates:
                return self._height
            else:
                return self._y1

        if xy_anchor in ('w', 'c', 'center', 'e'):
            if screen_coordinates:
                return self._height / 2
            else:
                return (self._y0 + self._y1) / 2

        if xy_anchor in ('sw', 's', 'se', ''):
            if screen_coordinates:
                return 0
            else:
                return self._y0

        raise SalabimError('incorrect xy_anchor', xy_anchor)

    def salabim_logo(self):
        if self.is_dark('bg'):
            return salabim_logo_red_white_200()
        else:
            return salabim_logo_red_black_200()

    def colorspec_to_tuple(self, colorspec):
        '''
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
            ``'fg'`` ==> foreground_color |n|
            ``'bg'`` ==> background_color

        Returns
        -------
        (r, g, b, a)
        '''
        if colorspec is None:
            colorspec = ''
        if colorspec == 'fg':
            colorspec = self.colorspec_to_tuple(self._foreground_color)
        elif colorspec == 'bg':
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
            if (colorspec != '') and (colorspec[0]) == '#':
                if len(colorspec) == 7:
                    return (int(colorspec[1:3], 16), int(colorspec[3:5], 16),
                            int(colorspec[5:7], 16), 255)
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
                try:
                    colorhex = colornames()[colorspec.replace(' ', '').lower()]
                    if len(colorhex) == 7:
                        colorhex = colorhex + alpha
                    return self.colorspec_to_tuple(colorhex)
                except:
                    pass

        raise SalabimError('wrong color specification: ' + str(colorspec))

    def colorinterpolate(self, t, t0, t1, v0, v1):
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
        linear interpolation between v0 and v1 based on t between t0 and t : colorspec

        Note
        ----
        Note that no extrapolation is done, so if t<t0 ==> v0  and t>t1 ==> v1 |n|
        This function is heavily used during animation
        '''
        if v0 == v1:
            return v0
        if t1 == inf:
            return v0
        if t0 == t1:
            return v1
        vt0 = self.colorspec_to_tuple(v0)
        vt1 = self.colorspec_to_tuple(v1)
        return tuple(int(c) for c in interpolate(t, t0, t1, vt0, vt1))

    def colorspec_to_hex(self, colorspec, withalpha=True):
        v = self.colorspec_to_tuple(colorspec)
        if withalpha:
            return '#{:02x}{:02x}{:02x}{:02x}'.\
                format(int(v[0]), int(v[1]), int(v[2]), int(v[3]))
        else:
            return '#{:02x}{:02x}{:02x}'.\
                format(int(v[0]), int(v[1]), int(v[2]))

    def pythonistacolor(self, colorspec):
        c = self.colorspec_to_tuple(colorspec)
        return (c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255)

    def is_dark(self, colorspec):
        '''
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
        '''
        rgba = self.colorspec_to_tuple(colorspec)
        if rgba[3] == 0:
            return self.is_dark(self.colorspec_to_tuple(('bg', 255)))
        luma = ((0.299 * rgba[0]) + (0.587 * rgba[1]) + (0.114 * rgba[2])) / 255
        if luma > 0.5:
            return False
        else:
            return True

    def getwidth(self, text, font, fontsize, screen_coordinates=False):
        if not screen_coordinates:
            fontsize = fontsize * self._scale
        f, heightA = getfont(font, fontsize)
        if text == '':  # necessary because of bug in PIL >= 4.2.1
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
        thiswidth, thisheight = f.getsize('Ap')
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
        fontsize = interpolate(
            width, lastwidth, thiswidth, fontsize - 1, fontsize)
        if screen_coordinates:
            return fontsize
        else:
            return fontsize / self._scale

    def name(self, value=None):
        '''
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
        '''
        if value is not None:
            self._name = value
        return self._name

    def base_name(self):
        '''
        returns the base name of the environment (the name used at initialization)
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the environment : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        '''
        return self._sequence_number

    def print_trace_header(self):
        '''
        print a (two line) header line as a legend |n|
        also the legend for line numbers will be printed |n|
        not that the header is only printed if trace=True
        '''
        self.print_trace('      time', 'current component', 'action', 'information', 'line#')
        self.print_trace(10 * '-', 20 * '-', 35 * '-', 48 * '-', 6 * '-')
        for ref in range(len(self._source_files)):
            for fullfilename, iref in self._source_files.items():
                if ref == iref:
                    self._print_legend(iref)

    def _print_legend(self, ref):
        if ref:
            s = 'line numbers prefixed by ' + chr(ord('A') + ref - 1) + ' refer to'
        else:
            s = 'line numbers refers to'
        for fullfilename, iref in self._source_files.items():
            if ref == iref:
                self.print_trace('', '', s, (os.path.basename(fullfilename)), '')
                break

    def _frame_to_lineno(self, frame):
        frameinfo = inspect.getframeinfo(frame)
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
            pre = ''
        else:
            pre = chr(ref + ord('A') - 1)
        if new_entry:
            self._print_legend(ref)
        return rpad(pre + str(lineno), 5)

    def print_trace(self, s1='', s2='', s3='', s4='', s0=None, _optional=False):
        '''
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

        '''
        if self._trace:
            if not (hasattr(self, '_current_component') and self._current_component._suppress_trace):
                if s0 is None:
                    stack = inspect.stack()
                    filename0 = inspect.getframeinfo(stack[0][0]).filename
                    for i in range(len(inspect.stack())):
                        frame = stack[i][0]
                        if filename0 != inspect.getframeinfo(frame).filename:
                            break

                    s0 = self._frame_to_lineno(_get_caller_frame())
                self.last_s0 = s0
                line = pad(s0, 7) + pad(s1, 10) + ' ' + pad(s2, 20) + ' ' + \
                    pad(s3, max(len(s3), 36)) + ' ' + s4.strip()
                if _optional:
                    self._buffered_trace = line
                else:
                    if self._buffered_trace:
                        print(self._buffered_trace)
                        logging.debug(self._buffered_trace)
                        self._buffered_trace = False
                    print(line)
                    logging.debug(line)

    def beep(self):
        '''
        Beeps

        Works only on Windows and iOS (Pythonista). For other platforms this is just a dummy method.
        '''
        if Windows:
            try:
                import winsound
                winsound.PlaySound(
                    os.environ['WINDIR'] + r'\media\Windows Ding.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
            except:
                pass

        elif Pythonista:
            try:
                import sound
                sound.stop_all_effects()
                sound.play_effect('game:Beep', pitch=0.3)
            except:
                pass


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

    xy_anchor : str
        specifies where x and y (i.e. x0, y0, x1 and y1) are relative to |n|
        possible values are (default: sw) : |n|
        ``nw    n    ne`` |n|
        ``w     c     e`` |n|
        ``sw    s    se`` |n|
        If '', the given coordimates are used untranslated

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

    image : str or PIL image
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
        - 'fg' or 'bg'

    colornames may contain an additional alpha, like ``red#7f`` |n|
    hexnames may be either 3 of 4 bytes long (``#rrggbb`` or ``#rrggbbaa``) |n|
    both colornames and hexnames may be given as a tuple with an
    additional alpha between 0 and 255,
    e.g. ``(255,0,255,128)``, ('red',127)`` or ``('#ff00ff',128)`` |n|
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
    as_points                                   -         -         -
    font                                                                      -
    fontsize0,fontsize1                                                       -
    width0,width1                     -
    ======================  ========= ========= ========= ========= ========= =========
    '''

    def __init__(self, parent=None, layer=0, keep=True, visible=True,
                 screen_coordinates=False,
                 t0=None, x0=0, y0=0, offsetx0=0, offsety0=0,
                 circle0=None, line0=None, polygon0=None, rectangle0=None, points0=None,
                 image=None, text=None,
                 font='', anchor='c', as_points=False, max_lines=0, text_anchor=None,
                 linewidth0=None, fillcolor0=None, linecolor0='fg', textcolor0='fg',
                 angle0=0, fontsize0=20, width0=None,
                 t1=None, x1=None, y1=None, offsetx1=None, offsety1=None,
                 circle1=None, line1=None, polygon1=None, rectangle1=None, points1=None,
                 linewidth1=None, fillcolor1=None, linecolor1=None, textcolor1=None,
                 angle1=None, fontsize1=None, width1=None, xy_anchor='', env=None):

        self.env = g.default_env if env is None else env
        self._image_ident = None  # denotes no image yet
        self._image = None
        self._image_x = 0
        self._image_y = 0
        self.canvas_object = None

        self.type = self.settype(
            circle0, line0, polygon0, rectangle0, points0, image, text)
        if self.type == '':
            raise SalabimError('no object specified')
        type1 = self.settype(circle1, line1, polygon1, rectangle1, points1, None, None)
        if (type1 != '') and (type1 != self.type):
            raise SalabimError('incompatible types: ' +
                self.type + ' and ' + type1)

        self.layer0 = layer
        self.parent = parent
        self.keep = keep
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
            self.image0 = spec_to_image(image)
            self.width0 = None if width0 is None else width0  # None means original size

        self.as_points0 = as_points
        self.font0 = font
        self.max_lines0 = max_lines
        self.anchor0 = anchor
        if self.type == 'text':
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
                self.fillcolor0 = ''
            else:
                self.fillcolor0 = 'fg'
        else:
            self.fillcolor0 = fillcolor0
        self.linecolor0 = linecolor0
        self.textcolor0 = textcolor0
        if linewidth0 is None:
            if self.as_points0:
                self.linewidth0 = 3
            else:
                if self.type == 'line':
                    self.linewidth0 = 1
                else:
                    self.linewidth0 = 0
        else:
            self.linewidth0 = linewidth0
        self.angle0 = angle0
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
        self.fillcolor1 =\
            self.fillcolor0 if fillcolor1 is None else fillcolor1
        self.linecolor1 =\
            self.linecolor0 if linecolor1 is None else linecolor1
        self.textcolor1 =\
            self.textcolor0 if textcolor1 is None else textcolor1
        self.linewidth1 =\
            self.linewidth0 if linewidth1 is None else linewidth1
        self.angle1 = self.angle0 if angle1 is None else angle1
        self.fontsize1 =\
            self.fontsize0 if fontsize1 is None else fontsize1
        self.width1 = self.width0 if width1 is None else width1

        self.t1 = inf if t1 is None else t1

        self.env.an_objects.append(self)

    def update(self, layer=None, keep=None, visible=None,
               t0=None, x0=None, y0=None, offsetx0=None, offsety0=None,
               circle0=None, line0=None, polygon0=None, rectangle0=None, points0=None,
               image=None, text=None, font=None, anchor=None, max_lines=None, text_anchor=None,
               linewidth0=None, fillcolor0=None, linecolor0=None, textcolor0=None,
               angle0=None, fontsize0=None, width0=None, as_points=None,
               t1=None, x1=None, y1=None, offsetx1=None, offsety1=None,
               circle1=None, line1=None, polygon1=None, rectangle1=None, points1=None,
               linewidth1=None, fillcolor1=None, linecolor1=None, textcolor1=None,
               angle1=None, fontsize1=None, width1=None, xy_anchor=None):
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

        xy_anchor : str
            specifies where x and y (i.e. x0, y0, x1 and y1) are relative to |n|
            possible values are: |n|
            ``nw    n    ne`` |n|
            ``w     c     e`` |n|
            ``sw    s    se`` |n|
            If '', the given coordimates are used untranslated |n|
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
        '''

        t = self.env._now
        type0 = self.settype(circle0, line0, polygon0, rectangle0, points0, image, text)
        if (type0 != '') and (type0 != self.type):
            raise SalabimError('incorrect type ' +
                type0 + ' (should be ' + self.type)
        type1 = self.settype(circle1, line1, polygon1, rectangle1, points1, None, None)
        if (type1 != '') and (type1 != self.type):
            raise SalabimError('incompatible types: ' +
                self.type + ' and ' + type1)

        if layer is not None:
            self.layer0 = layer
        if keep is not None:
            self.keep = keep
        if visible is not None:
            self.visible0 = visible
        self.circle0 = self.circle() if circle0 is None else circle0
        self.line0 = self.line() if line0 is None else de_none(line0)
        self.polygon0 = self.polygon() if polygon0 is None else de_none(polygon0)
        self.rectangle0 =\
            self.rectangle() if rectangle0 is None else de_none(rectangle0)
        self.points0 = self.points() if points0 is None else de_none(points0)
        if as_points is not None:
            self.as_points0 = as_points
        if text is not None:
            self.text0 = text
        if max_lines is not None:
            self.max_lines0 = max_lines
        self.width0 = self.width() if width0 is None else width0
        if image is not None:
            self.image0 = spec_to_image(image)
            self.width0 = self.image0.size[0] if width0 is None else width0

        if font is not None:
            self.font0 = font
        if anchor is not None:
            self.anchor0 = anchor
            if self.type == 'text':
                if text_anchor is not None:
                    self.text_anchor0 = text_anchor
        if text_anchor is not None:
            self.text_anchor0 = text_anchor

        self.x0 = self.x(t) if x0 is None else x0
        self.y0 = self.y(t) if y0 is None else y0
        self.offsetx0 = self.offsetx(t) if offsetx0 is None else offsetx0
        self.offsety0 = self.offsety(t) if offsety0 is None else offsety0

        self.fillcolor0 =\
            self.fillcolor(t) if fillcolor0 is None else fillcolor0
        self.linecolor0 =\
            self.linecolor(t) if linecolor0 is None else linecolor0
        self.textcolor0 =\
            self.textcolor(t) if textcolor0 is None else textcolor0
        self.linewidth0 =\
            self.linewidth(t) if linewidth0 is None else linewidth0
        self.angle0 = self.angle(t) if angle0 is None else angle0
        self.fontsize0 = self.fontsize(t) if fontsize0 is None else fontsize0
        self.t0 = self.env._now if t0 is None else t0

        self.circle1 = self.circle0 if circle1 is None else circle1
        self.line1 = self.line0 if line1 is None else de_none(line1)
        self.polygon1 = self.polygon0 if polygon1 is None else de_none(polygon1)
        self.rectangle1 =\
            self.rectangle0 if rectangle1 is None else de_none(rectangle1)
        self.points1 = self.points0 if points1 is None else de_none(points1)

        self.x1 = self.x0 if x1 is None else x1
        self.y1 = self.y0 if y1 is None else y1
        self.offsetx1 = self.offsetx0 if offsetx1 is None else offsetx1
        self.offsety1 = self.offsety0 if offsety1 is None else offsety1
        self.fillcolor1 =\
            self.fillcolor0 if fillcolor1 is None else fillcolor1
        self.linecolor1 =\
            self.linecolor0 if linecolor1 is None else linecolor1
        self.textcolor1 =\
            self.textcolor0 if textcolor1 is None else textcolor1
        self.linewidth1 =\
            self.linewidth0 if linewidth1 is None else linewidth1
        self.angle1 = self.angle0 if angle1 is None else angle1
        self.fontsize1 =\
            self.fontsize0 if fontsize1 is None else fontsize1
        self.width1 = self.width0 if width1 is None else width1

        self.t1 = inf if t1 is None else t1
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
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if self in self.env.an_objects:
            self.env.an_objects.remove(self)

    def x(self, t=None):
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
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.x0, self.x1)

    def y(self, t=None):
        '''
        y-position of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        y : float
            default behaviour: linear interpolation between self.y0 and self.y1
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.y0, self.y1)

    def offsetx(self, t=None):
        '''
        offsetx of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        offsetx : float
            default behaviour: linear interpolation between self.offsetx0 and self.offsetx1
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.offsetx0, self.offsetx1)

    def offsety(self, t=None):
        '''
        offsety of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        offsety : float
            default behaviour: linear interpolation between self.offsety0 and self.offsety1
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.offsety0, self.offsety1)

    def angle(self, t=None):
        '''
        angle of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        angle : float
            default behaviour: linear interpolation between self.angle0 and self.angle1
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.angle0, self.angle1)

    def linewidth(self, t=None):
        '''
        linewidth of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        linewidth : float
            default behaviour: linear interpolation between self.linewidth0 and self.linewidth1
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.linewidth0, self.linewidth1)

    def linecolor(self, t=None):
        '''
        linecolor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        linecolor : colorspec
            default behaviour: linear interpolation between self.linecolor0 and self.linecolor1
        '''
        return self.env.colorinterpolate((self.env._now if t is None else t),
                                self.t0, self.t1, self.linecolor0, self.linecolor1)

    def fillcolor(self, t=None):
        '''
        fillcolor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        fillcolor : colorspec
            default behaviour: linear interpolation between self.fillcolor0 and self.fillcolor1
        '''
        return self.env.colorinterpolate((self.env._now if t is None else t),
                                self.t0, self.t1, self.fillcolor0, self.fillcolor1)

    def circle(self, t=None):
        '''
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
        '''
        return interpolate(
            (self.env._now if t is None else t),
            self.t0, self.t1,
            self.circle0,
            self.circle1)

    def textcolor(self, t=None):
        '''
        textcolor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        textcolor : colorspec
            default behaviour: linear interpolation between self.textcolor0 and self.textcolor1
        '''
        return self.env.colorinterpolate((self.env._now if t is None else t),
                                self.t0, self.t1, self.textcolor0, self.textcolor1)

    def line(self, t=None):
        '''
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
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.line0, self.line1)

    def polygon(self, t=None):
        '''
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
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.polygon0, self.polygon1)

    def rectangle(self, t=None):
        '''
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
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.rectangle0, self.rectangle1)

    def points(self, t=None):
        '''
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
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.points0, self.points1)

    def width(self, t=None):
        '''
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
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.width0, self.width1)

    def fontsize(self, t=None):
        '''
        fontsize of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        fontsize : float
            default behaviour: linear interpolation between self.fontsize0 and self.fontsize1
        '''
        return interpolate((self.env._now if t is None else t),
                           self.t0, self.t1, self.fontsize0, self.fontsize1)

    def as_points(self, t=None):
        '''
        as_points of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        as_points : bool
            default behaviour: self.as_points (text given at creation or update)
        '''
        return self.as_points0

    def text(self, t=None):
        '''
        text of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        text : str
            default behaviour: self.text0 (text given at creation or update)
        '''
        return self.text0

    def max_lines(self, t=None):
        '''
        maximum number of lines to be displayed of text. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        max_lines : int
            default behaviour: self.max_lines0 (max_lines given at creation or update)
        '''
        return self.max_lines0

    def anchor(self, t=None):
        '''
        anchor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        anchor : str
            default behaviour: self.anchor0 (anchor given at creation or update)
        '''

        return self.anchor0

    def text_anchor(self, t=None):
        '''
        text_anchor of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        text_anchor : str
            default behaviour: self.text_anchor0 (text_anchor given at creation or update)
        '''

        return self.text_anchor0

    def layer(self, t=None):
        '''
        layer of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        layer : int or float
            default behaviour: self.layer0 (layer given at creation or update)
        '''
        return self.layer0

    def font(self, t=None):
        '''
        font of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        font : str
            default behaviour: self.font0 (font given at creation or update)
        '''
        return self.font0

    def xy_anchor(self, t=None):
        '''
        xy_anchor attribute of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        xy_anchor : str
            default behaviour: self.xy_anchor0 (xy_anchor given at creation or update)
        '''
        return self.xy_anchor0

    def visible(self, t=None):
        '''
        visible attribute of an animate object. May be overridden.

        Parameters
        ----------
        t : float
            current time

        Returns
        -------
        visible : bool
            default behaviour: self.visible0 (visible given at creation or update)
        '''
        return self.visible0

    def image(self, t=None):
        '''
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
        '''
        return self.image0

    def settype(self, circle, line, polygon, rectangle, points, image, text):
        n = 0
        t = ''
        if circle is not None:
            t = 'circle'
            n += 1
        if line is not None:
            t = 'line'
            n += 1
        if polygon is not None:
            t = 'polygon'
            n += 1
        if rectangle is not None:
            t = 'rectangle'
            n += 1
        if points is not None:
            t = 'points'
            n += 1
        if image is not None:
            t = 'image'
            n += 1
        if text is not None:
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
            xy_anchor = self.xy_anchor(t)
            if xy_anchor:
                x += self.env.xy_anchor_to_x(xy_anchor, screen_coordinates=self.screen_coordinates)
                y += self.env.xy_anchor_to_y(xy_anchor, screen_coordinates=self.screen_coordinates)

            offsetx = self.offsetx(t)
            offsety = self.offsety(t)
            angle = self.angle(t)
            as_points = self.as_points(t)

            if self.type in ('polygon', 'rectangle', 'line', 'circle'):
                if self.screen_coordinates:
                    linewidth = self.linewidth(t)
                else:
                    linewidth = self.linewidth(t) * self.env._scale

                linecolor = self.env.colorspec_to_tuple(self.linecolor(t))
                fillcolor = self.env.colorspec_to_tuple(self.fillcolor(t))

                cosa = math.cos(angle * math.pi / 180)
                sina = math.sin(angle * math.pi / 180)
                if self.screen_coordinates:
                    qx = x
                    qy = y
                else:
                    qx = (x - self.env._x0) * self.env._scale
                    qy = (y - self.env._y0) * self.env._scale

                if self.type == 'rectangle':
                    rectangle = tuple(self.rectangle(t))
                    self._image_ident = (tuple(rectangle), linewidth, linecolor, fillcolor,
                        as_points, angle, self.screen_coordinates)
                elif self.type == 'line':
                    line = tuple(self.line(t))
                    fillcolor = (0, 0, 0, 0)
                    self._image_ident = (tuple(line), linewidth, linecolor,
                        as_points, angle, self.screen_coordinates)
                elif self.type == 'polygon':
                    polygon = tuple(self.polygon(t))
                    self._image_ident = (tuple(polygon), linewidth, linecolor, fillcolor,
                        as_points, angle, self.screen_coordinates)
                elif self.type == 'circle':
                    circle = self.circle(t)
                    if isinstance(circle, list):
                        circle = tuple(circle)
                    self._image_ident = (circle, linewidth, linecolor, fillcolor,
                        angle, self.screen_coordinates)

                if self._image_ident != self._image_ident_prev:
                    if self.type == 'rectangle':
                        p = [
                            rectangle[0], rectangle[1],
                            rectangle[2], rectangle[1],
                            rectangle[2], rectangle[3],
                            rectangle[0], rectangle[3],
                            rectangle[0], rectangle[1]]

                    elif self.type == 'line':
                        p = line

                    elif self.type == 'polygon':
                        p = list(polygon)
                        if p[0:1] != p[-2:-1]:
                            p.append(p[0])  # close the polygon
                            p.append(p[1])

                    elif self.type == 'circle':
                        arc_angle0 = 0
                        arc_angle1 = 360
                        draw_arc = False
                        if isinstance(circle, (list, tuple)):
                            radius0 = radius1 = circle[0]
                            if len(circle) > 1:
                                if circle[1] is not None:
                                    radius1 = circle[1]
                            if len(circle) > 3:
                                arc_angle0 = circle[2]
                                arc_angle1 = circle[3]
                            if len(circle) > 4:
                                draw_arc = bool(circle[4])
                        else:
                            radius0 = radius1 = circle
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
                            arc_angle_radians = math.pi * arc_angle / 180
                            sint = math.sin(arc_angle_radians)
                            cost = math.cos(arc_angle_radians)
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
                        self._image = Image.new('RGBA', (int(maxrx - minrx + 2 * linewidth),
                          int(maxry - minry + 2 * linewidth)), (0, 0, 0, 0))
                        point_image = Image.new('RGBA', (int(linewidth), int(linewidth)), linecolor)

                        for i in range(0, len(r), 2):
                            rx = rscaled[i]
                            ry = rscaled[i + 1]
                            self._image.paste(point_image,
                              (int(rx - 0.5 * linewidth), int(ry - 0.5 * linewidth)), point_image)

                    else:
                        self._image = Image.new('RGBA', (int(maxrx - minrx + 2 * linewidth),
                            int(maxry - minry + 2 * linewidth)), (0, 0, 0, 0))
                        draw = ImageDraw.Draw(self._image)
                        if fillcolor[3] != 0:
                            draw.polygon(rscaled, fill=fillcolor)
                        if (round(linewidth) > 0) and (linecolor[3] != 0):
                            if self.type == 'circle' and not draw_arc:
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
                    if self.type == 'circle':
                        self.radius0 = radius0
                        self.radius1 = radius1

                if self.type == 'circle':
                    self.env._centerx = qx
                    self.env._centery = qy
                    self.env._dimx = 2 * self.radius0
                    self.env._dimy = 2 * self.radius1
                else:
                    self.env._centerx = qx + (self.minrx + self.maxrx) / 2
                    self.env._centery = qy + (self.minry + self.maxry) / 2
                    self.env._dimx = self.maxpx - self.minpx
                    self.env._dimy = self.maxpy - self.minpy

                self._image_x = qx + self.minrx - linewidth + \
                    (offsetx * cosa - offsety * sina)
                self._image_y = qy + self.minry - linewidth + \
                    (offsetx * sina + offsety * cosa)

            elif self.type == 'image':
                image = self.image(t)
                if isinstance(image, (tuple, list)):
                    image = image[0]  # ignore serial number (for compatibility with pre 2.2.9 versions)
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

                self._image_ident = (image, width, height, angle)
                if self._image_ident != self._image_ident_prev:
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
                    'c': (0, 0),
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

                self.env._centerx = qx + ex
                self.env._centery = qy + ey
                self.env._dimx = width
                self.env._dimy = height

                self._image_x = qx + ex - imrwidth / 2
                self._image_y = qy + ey - imrheight / 2

            elif self.type == 'text':
                textcolor = self.env.colorspec_to_tuple(self.textcolor(t))
                fontsize = self.fontsize(t)
                angle = self.angle(t)
                fontname = self.font(t)
                if not self.screen_coordinates:
                    fontsize = fontsize * self.env._scale
                    offsetx = offsetx * self.env._scale
                    offsety = offsety * self.env._scale
                text = self.text(t)
                text_anchor = self.text_anchor(t)

                if hasattr(self, 'dependent'):
                    text_offsetx = self.text_offsetx(t)
                    text_offsety = self.text_offsety(t)
                    if not self.screen_coordinates:
                        text_offsetx = text_offsetx * self.env._scale
                        text_offsety = text_offsety * self.env._scale
                    qx = self.env._centerx
                    qy = self.env._centery
                    anchor_to_dis = {
                        'ne': (0.5, 0.5),
                        'n': (0, 0.5),
                        'nw': (-0.5, 0.5),
                        'e': (0.5, 0),
                        'center': (0, 0),
                        'c': (0, 0),
                        'w': (-0.5, 0),
                        'se': (0.5, -0.5),
                        's': (0, -0.5),
                        'sw': (-0.5, -0.5)}
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
                self._image_ident = (
                    text, fontname, fontsize, angle, textcolor, max_lines)
                if self._image_ident != self._image_ident_prev:
                    font, heightA = getfont(fontname, fontsize)
                    if text == '' or text is None:  # this code is a workaround for a bug in PIL >= 4.2.1
                        im = Image.new(
                            'RGBA', (0, 0), (0, 0, 0, 0))
                    else:
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
                        lineheight = font.getsize('Ap')[1]
                        totheight = number_of_lines * lineheight
                        im = Image.new(
                            'RGBA', (int(totwidth + 0.1 * fontsize), int(totheight)), (0, 0, 0, 0))
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
                        textcolor3 = textcolor[0:3]
                        if textcolor3 != (0, 0, 0):  # black is ok
                            for y in range(imheight):
                                for x in range(imwidth):
                                    c = im.getpixel((x, y))
                                    if not c[0:3] in (textcolor3, (0, 0, 0)):
                                        im.putpixel((x, y), (textcolor3[0], textcolor3[1], textcolor3[2], c[3]))
                        # end of code to correct bug

                    self.imwidth, self.imheight = im.size
                    self.heightA = heightA

                    self._image = im.rotate(angle, expand=1)

                anchor_to_dis = {
                    'ne': (-0.5, -0.5),
                    'n': (0, -0.5),
                    'nw': (0.5, -0.5),
                    'e': (-0.5, 0),
                    'center': (0, 0),
                    'c': (0, 0),
                    'w': (0.5, 0),
                    'se': (-0.5, 0.5),
                    's': (0, 0.5),
                    'sw': (0.5, 0.5)}
                dx, dy = anchor_to_dis[text_anchor.lower()]
                dx = dx * self.imwidth + offsetx - 0.1 * fontsize

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


class AnimateEntry(object):
    '''
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
    '''
    def __init__(self, x=0, y=0, number_of_chars=20, value='',
        fillcolor='fg', color='bg', text='', action=None, env=None, xy_anchor='sw'):
        self.env = g.default_env if env is None else env
        self.env.ui_objects.append(self)
        self.type = 'entry'
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

        self.entry = tkinter.Entry(
            self.env.root)
        self.entry.configure(
            width=self.number_of_chars,
            foreground=self.env.colorspec_to_hex(self.color, False),
            background=self.env.colorspec_to_hex(self.fillcolor, False),
            relief=tkinter.FLAT)
        self.entry.bind("<Return>", self.on_enter)
        self.entry_window = g.canvas.create_window(
            x, self.env._height - y,
            anchor=tkinter.SW, window=self.entry)
        self.entry.insert(0, self.value)
        self.installed = True

    def on_enter(self, ev):
        if self.action is not None:
            self.action()

    def get(self):
        '''
        get the current value of the entry

        Returns
        -------
        Current value of the entry : str
        '''
        return(self.entry.get())

    def remove(self):
        '''
        removes the entry object. |n|
        the ui object is removed from the ui queue,
        so effectively ending this ui
        '''
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if self.installed:
            self.entry.destroy()
            self.installed = False


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
    '''

    def __init__(self, x=0, y=0, width=80, height=30,
                 linewidth=0, fillcolor='fg',
                 linecolor='fg', color='bg', text='', font='',
                 fontsize=15, action=None, env=None, xy_anchor='sw'):

        self.env = g.default_env if env is None else env
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
        self.fillcolor = self.env.colorspec_to_tuple(fillcolor)
        self.linecolor = self.env.colorspec_to_tuple(linecolor)
        self.color = self.env.colorspec_to_tuple(color)
        self.linewidth = linewidth
        self.font = font
        self.fontsize = fontsize
        self.text0 = text
        self.lasttext = '*'
        self.action = action
        self.xy_anchor = xy_anchor

        self.env.ui_objects.append(self)
        self.installed = False

    def text(self):
        return self.text0

    def install(self):
        x = self.x + self.env.xy_anchor_to_x(self.xy_anchor, screen_coordinates=True)
        y = self.y + self.env.xy_anchor_to_y(self.xy_anchor, screen_coordinates=True)

        self.button = tkinter.Button(
            self.env.root, text=self.lasttext, command=self.action, anchor=tkinter.CENTER)
        self.button.configure(
            width=int(2.2 * self.width / self.fontsize),
            foreground=self.env.colorspec_to_hex(self.color, False),
            background=self.env.colorspec_to_hex(self.fillcolor, False),
            relief=tkinter.FLAT)
        self.button_window = g.canvas.create_window(
            x + self.width, self.env._height - y - self.height,
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
        if self.installed:
            if not Pythonista:
                self.button.destroy()
            self.installed = False


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

    linecolor : colorspec
        color of contour (default foreground_color)

    labelcolor : colorspec
        color of the label (default foreground_color)

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
    '''

    def __init__(self, layer=0, x=0, y=0, width=100, height=20,
                 vmin=0, vmax=10, v=None, resolution=1,
                 linecolor='fg', labelcolor='fg', label='',
                 font='', fontsize=12, action=None, xy_anchor='sw', env=None):

        self.env = g.default_env if env is None else env
        n = round((vmax - vmin) / resolution) + 1
        self.vmin = vmin
        self.vmax = vmin + (n - 1) * resolution
        self._v = vmin if v is None else v
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
        self.linecolor = self.env.colorspec_to_tuple(linecolor)
        self.labelcolor = self.env.colorspec_to_tuple(labelcolor)
        self.font = font
        self.fontsize = fontsize
        self.label = label
        self.action = action
        self.installed = False
        self.xy_anchor = xy_anchor

        if Pythonista:
            self.y = self.y - height * 1.5

        self.env.ui_objects.append(self)

    def v(self, value=None):
        '''
        value

        Parameters
        ----------
        value: float
            new value |n|
            if omitted, no change

        Returns
        -------
        Current value of the slider : float
        '''
        if value is not None:
            if Pythonista:
                self._v = value
            else:
                if self.env._animate:
                    self.slider.set(value)
                else:
                    self._v = value

        if Pythonista:
            return self._v
        else:
            if self.env._animate:
                return self.slider.get()
            else:
                return self._v

    def install(self):
        x = self.x + self.env.xy_anchor_to_x(self.xy_anchor, screen_coordinates=True)
        y = self.y + self.env.xy_anchor_to_y(self.xy_anchor, screen_coordinates=True)
        self.slider = tkinter.Scale(
            self.env.root,
            from_=self.vmin, to=self.vmax,
            orient=tkinter.HORIZONTAL,
            label=self.label,
            resolution=self.resolution,
            command=self.action)
        self.slider.window = g.canvas.create_window(
            x, self.env._height - y,
            anchor=tkinter.NW, window=self.slider)
        self.slider.config(
            font=(self.font, int(self.fontsize * 0.8)),
            foreground=self.env.colorspec_to_hex('fg', False),
            background=self.env.colorspec_to_hex('bg', False),
            highlightbackground=self.env.colorspec_to_hex('bg', False))
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
        if self.installed:
            if not Pythonista:
                self.slider.quit()
            self.installed = False


class AnimateQueue(object):
    '''
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
        if 'w', waiting line runs westwards (i.e. from right to left) |n|
        if 'n', waiting line runs northeards (i.e. from bottom to top) |n|
        if 'e', waiting line runs eastwards (i.e. from left to right) (default) |n|
        if 's', waiting line runs southwards (i.e. from top to bottom)

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
        font of the title (default '')

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

    layer : int
        layer (default 0)

    id : any
        the animation works by calling the animation_objects method of each component, optionally
        with id. By default, this is self, but can be overriden, particularly with the queue

    arg : any
        this is used when a parameter is a function with two parameters, as the first argument or
        if a parameter is a method as the instance |n|
        default: self (instance itself)

    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation object will be removed
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue, id, arg and parent can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    '''

    def __init__(self, queue, x=50, y=50, direction='w', max_length=None,
        xy_anchor='sw', reverse=False,
        title=None, titlecolor='fg', titlefontsize=15, titlefont='', titleoffsetx=None, titleoffsety=None,
        layer=0,
        id=None, arg=None, parent=None):
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
        self.parent = parent
        self.env = queue.env
        self.vx = 0
        self.vy = 0
        self.vangle = 0
        self.vlayer = 0
        self.vanchor = 'e'
        self.titleoffsetx = titleoffsetx
        self.titleoffsety = titleoffsety
        self.titlefont = titlefont
        self.titlefontsize = titlefontsize
        self.titlecolor = titlecolor
        self.title = title
        self.layer = layer
        self.aotitle = AnimateText(text=lambda: self.vtitle, textcolor=lambda: self.vtitlecolor,
            x=lambda: self.vx, y=lambda: self.vy, text_anchor=lambda: self.vanchor, angle=lambda: self.vangle,
            screen_coordinates=True, fontsize=lambda: self.vtitlefontsize, font=lambda: self.vtitlefont,
            layer=lambda: self.vlayer)
        self.env.sys_objects.append(self)

    def update(self, t):
        prev_aos = self.current_aos
        self.current_aos = {}
        xy_anchor = _call(self.xy_anchor, t, self.arg)
        max_length = _call(self.max_length, t, self.arg)
        x = _call(self.x, t, self.arg)
        y = _call(self.y, t, self.arg)
        direction = _call(self.direction, t, self.arg)
        reverse = _call(self.reverse, t, self.arg)
        titleoffsetx = _call(self.titleoffsetx, t, self.arg)
        titleoffsety = _call(self.titleoffsety, t, self.arg)
        title = _call(self.title, t, self.arg)
        self.vtitle = self._queue.name() if title is None else title
        self.vtitlefont = _call(self.titlefont, t, self.arg)
        self.vtitlefontsize = _call(self.titlefontsize, t, self.arg)
        self.vtitlecolor = _call(self.titlecolor, t, self.arg)
        self.vlayer = _call(self.layer, t, self.arg)
        x += self._queue.env.xy_anchor_to_x(xy_anchor, screen_coordinates=True)
        y += self._queue.env.xy_anchor_to_y(xy_anchor, screen_coordinates=True)
        if direction == 'e':
            self.vx = x + (-25 if titleoffsetx is None else titleoffsetx)
            self.vy = y + (25 if self.titleoffsety is None else titleoffsety)
            self.vanchor = 'sw'
            self.vangle = 0
        elif direction == 'w':
            self.vx = x + (25 if titleoffsetx is None else titleoffsetx)
            self.vy = y + (25 if self.titleoffsety is None else titleoffsety)
            self.vanchor = 'se'
            self.vangle = 0
        elif direction == 'n':
            self.vx = x + (-25 if titleoffsetx is None else titleoffsetx)
            self.vy = y + (-25 - self.vtitlefontsize if self.titleoffsety is None else titleoffsety)
            self.vanchor = 'sw'
            self.vangle = 0
        elif direction == 's':
            self.vx = x + (-25 if titleoffsetx is None else titleoffsetx)
            self.vy = y + (25if self.titleoffsety is None else titleoffsety)
            self.vanchor = 'sw'
            self.vangle = 0

        factor_x, factor_y = \
            {'w': (-1, 0), 'n': (0, 1), 'e': (1, 0), 's': (0, -1)}[direction.lower()]
        n = 0
        for c in reversed(self._queue) if reverse else self._queue:
            if (max_length is not None) and n >= max_length:
                break
            if c not in prev_aos:
                nargs = c.animation_objects.__code__.co_argcount
                if nargs == 1:
                    animation_objects = self.current_aos[c] = c.animation_objects()
                else:
                    animation_objects = self.current_aos[c] = c.animation_objects(self.id)
            else:
                animation_objects = self.current_aos[c] = prev_aos[c]
                del prev_aos[c]
            dimx = _call(animation_objects[0], t, c)
            dimy = _call(animation_objects[1], t, c)
            for ao in animation_objects[2:]:
                if isinstance(ao, _Vis):
                    ao.x = x
                    ao.y = y
                else:
                    ao.x0 = x
                    ao.y0 = y
            x += factor_x * dimx
            y += factor_y * dimy
            n += 1

        for animation_objects in prev_aos.values():
            for ao in animation_objects[2:]:
                ao.remove()

    def remove(self):
        for animation_objects in self.current_aos.values():
            for ao in animation_objects[2:]:
                ao.remove()
        self.aotitle.remove()
        self.env.sys_objects.remove(self)


class _Vis(object):
    pass


class AnimateText(_Vis):
    '''
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
        If '', the given coordimates are used untranslated

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
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue and arg can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called

    '''
    def __init__(self, text='', x=0, y=0, fontsize=15, textcolor='fg', font='', text_anchor='sw', angle=0,
        visible=True, xy_anchor='', layer=0, env=None, screen_coordinates=False, arg=None, parent=None,
        offsetx=0, offsety=0, max_lines=0):
        self.env = g.default_env if env is None else env

        # the checks hasattr are req'd to not override methods of inherited classes
        if not hasattr(self, 'x'):
            self.x = x
        if not hasattr(self, 'y'):
            self.y = y
        if not hasattr(self, 'offsetx'):
            self.offsetx = offsetx
        if not hasattr(self, 'offsety'):
            self.offsety = offsety
        if not hasattr(self, 'text'):
            self.text = text
        if not hasattr(self, 'max_lines'):
            self.max_lines = max_lines
        if not hasattr(self, 'textcolor'):
            self.textcolor = textcolor
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'text_anchor'):
            self.text_anchor = text_anchor
        if not hasattr(self, 'font'):
            self.font = font
        if not hasattr(self, 'fontsize'):
            self.fontsize = fontsize
        if not hasattr(self, 'visible'):
            self.visible = visible
        if not hasattr(self, 'xy_anchor'):
            self.xy_anchor = xy_anchor
        if not hasattr(self, 'layer'):
            self.layer = layer
        self.arg = self if arg is None else arg
        ao0 = _AnimateVis(text='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        self.aos = (ao0,)

    def remove(self):
        for ao in self.aos:
            ao.remove()


class AnimateRectangle(_Vis):
    '''
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
        If '', the given coordimates are used untranslated

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

    textoffsetx : float
        extra x offset to the text_anchor point

    textoffsety : float
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
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue and arg can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    '''
    def __init__(self, spec=(), x=0, y=0, fillcolor='fg', linecolor='', linewidth=1,
        text='', fontsize=15, textcolor='bg', font='', angle=0, xy_anchor='', layer=0, max_lines=0,
        offsetx=0, offsety=0, as_points=False, text_anchor='c', text_offsetx=0, text_offsety=0, arg=None,
        parent=None,
        visible=True, env=None, screen_coordinates=False):

        self.env = g.default_env if env is None else env

        # the checks hasattr are req'd to not override methods of inherited classes
        if not hasattr(self, 'spec'):
            self.spec = spec
        if not hasattr(self, 'fillcolor'):
            self.fillcolor = fillcolor
        if not hasattr(self, 'linecolor'):
            self.linecolor = linecolor
        if not hasattr(self, 'linewidth'):
            self.linewidth = linewidth
        if not hasattr(self, 'as_points'):
            self.aspoint = as_points
        if not hasattr(self, 'x'):
            self.x = x
        if not hasattr(self, 'y'):
            self.y = y
        if not hasattr(self, 'offsetx'):
            self.offsetx = offsetx
        if not hasattr(self, 'offsety'):
            self.offsety = offsety
        if not hasattr(self, 'text_offsetx'):
            self.text_offsetx = text_offsetx
        if not hasattr(self, 'text_offsety'):
            self.text_offsety = text_offsety
        if not hasattr(self, 'text'):
            self.text = text
        if not hasattr(self, 'max_lines'):
            self.max_lines = max_lines
        if not hasattr(self, 'textcolor'):
            self.textcolor = textcolor
        if not hasattr(self, 'text_anchor'):
            self.text_anchor = text_anchor
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'font'):
            self.font = font
        if not hasattr(self, 'fontsize'):
            self.fontsize = fontsize
        if not hasattr(self, 'visible'):
            self.visible = visible
        if not hasattr(self, 'xy_anchor'):
            self.xy_anchor = xy_anchor
        if not hasattr(self, 'layer'):
            self.layer = layer
        self.arg = self if arg is None else arg
        ao0 = _AnimateVis(rectangle0=(), vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1 = _AnimateVis(text='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1.dependent = True
        self.aos = (ao0, ao1)

    def remove(self):
        for ao in self.aos:
            ao.remove()


class AnimatePolygon(_Vis):
    '''
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
        If '', the given coordimates are used untranslated

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

    textoffsetx : float
        extra x offset to the text_anchor point

    textoffsety : float
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
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue and arg can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    '''
    def __init__(self, spec=(), x=0, y=0, fillcolor='fg', linecolor='', linewidth=1,
        text='', fontsize=15, textcolor='bg', font='', angle=0, xy_anchor='', layer=0, max_lines=0,
        offsetx=0, offsety=0, as_points=False, text_anchor='c', text_offsetx=0, text_offsety=0, arg=None, parent=None,
        visible=True, env=None, screen_coordinates=False):
        self.env = g.default_env if env is None else env

        # the checks hasattr are req'd to not override methods of inherited classes
        if not hasattr(self, 'spec'):
            self.spec = spec
        if not hasattr(self, 'fillcolor'):
            self.fillcolor = fillcolor
        if not hasattr(self, 'linecolor'):
            self.linecolor = linecolor
        if not hasattr(self, 'linewidth'):
            self.linewidth = linewidth
        if not hasattr(self, 'as_points'):
            self.aspoint = as_points
        if not hasattr(self, 'x'):
            self.x = x
        if not hasattr(self, 'y'):
            self.y = y
        if not hasattr(self, 'offsetx'):
            self.offsetx = offsetx
        if not hasattr(self, 'offsety'):
            self.offsety = offsety
        if not hasattr(self, 'text_offsetx'):
            self.text_offsetx = text_offsetx
        if not hasattr(self, 'text_offsety'):
            self.text_offsety = text_offsety
        if not hasattr(self, 'text'):
            self.text = text
        if not hasattr(self, 'max_lines'):
            self.max_lines = max_lines
        if not hasattr(self, 'textcolor'):
            self.textcolor = textcolor
        if not hasattr(self, 'text_anchor'):
            self.text_anchor = text_anchor
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'font'):
            self.font = font
        if not hasattr(self, 'fontsize'):
            self.fontsize = fontsize
        if not hasattr(self, 'visible'):
            self.visible = visible
        if not hasattr(self, 'xy_anchor'):
            self.xy_anchor = xy_anchor
        if not hasattr(self, 'layer'):
            self.layer = layer
        self.arg = self if arg is None else arg
        ao0 = _AnimateVis(polygon0=(), vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1 = _AnimateVis(text='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1.dependent = True
        self.aos = (ao0, ao1)

    def remove(self):
        for ao in self.aos:
            ao.remove()


class AnimateLine(_Vis):
    '''
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
        If '', the given coordimates are used untranslated

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

    textoffsetx : float
        extra x offset to the text_anchor point

    textoffsety : float
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
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue and arg can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    '''
    def __init__(self, spec=(), x=0, y=0, linecolor='fg', linewidth=1,
        text='', fontsize=15, textcolor='fg', font='', angle=0, xy_anchor='', layer=0, max_lines=0,
        offsetx=0, offsety=0, as_points=False, text_anchor='c', text_offsetx=0, text_offsety=0, arg=None,
        parent=None,
        visible=True, env=None, screen_coordinates=False):
        self.env = g.default_env if env is None else env

        # the checks hasattr are req'd to not override methods of inherited classes
        if not hasattr(self, 'spec'):
            self.spec = spec
        if not hasattr(self, 'linecolor'):
            self.linecolor = linecolor
        if not hasattr(self, 'linewidth'):
            self.linewidth = linewidth
        if not hasattr(self, 'as_points'):
            self.aspoint = as_points
        if not hasattr(self, 'x'):
            self.x = x
        if not hasattr(self, 'y'):
            self.y = y
        if not hasattr(self, 'offsetx'):
            self.offsetx = offsetx
        if not hasattr(self, 'offsety'):
            self.offsety = offsety
        if not hasattr(self, 'text_offsetx'):
            self.text_offsetx = text_offsetx
        if not hasattr(self, 'text_offsety'):
            self.text_offsety = text_offsety
        if not hasattr(self, 'text'):
            self.text = text
        if not hasattr(self, 'max_lines'):
            self.max_lines = max_lines
        if not hasattr(self, 'textcolor'):
            self.textcolor = textcolor
        if not hasattr(self, 'text_anchor'):
            self.text_anchor = text_anchor
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'font'):
            self.font = font
        if not hasattr(self, 'fontsize'):
            self.fontsize = fontsize
        if not hasattr(self, 'visible'):
            self.visible = visible
        if not hasattr(self, 'xy_anchor'):
            self.xy_anchor = xy_anchor
        if not hasattr(self, 'layer'):
            self.layer = layer
        self.fillcolor = ''
        self.arg = self if arg is None else arg
        ao0 = _AnimateVis(line0=(), vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1 = _AnimateVis(text='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1.dependent = True
        self.aos = (ao0, ao1)

    def remove(self):
        for ao in self.aos:
            ao.remove()


class AnimatePoints(_Vis):
    '''
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
        If '', the given coordimates are used untranslated

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

    textoffsetx : float
        extra x offset to the text_anchor point

    textoffsety : float
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
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue and arg can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    '''
    def __init__(self, spec=(), x=0, y=0, linecolor='fg', linewidth=4,
        text='', fontsize=15, textcolor='fg', font='', angle=0, xy_anchor='', layer=0, max_lines=0,
        offsetx=0, offsety=0, text_anchor='c', text_offsetx=0, text_offsety=0, arg=None, parent=None,
        visible=True, env=None, screen_coordinates=False):
        self.env = g.default_env if env is None else env

        # the checks hasattr are req'd to not override methods of inherited classes
        if not hasattr(self, 'spec'):
            self.spec = spec
        if not hasattr(self, 'linecolor'):
            self.linecolor = linecolor
        if not hasattr(self, 'linewidth'):
            self.linewidth = linewidth
        if not hasattr(self, 'x'):
            self.x = x
        if not hasattr(self, 'y'):
            self.y = y
        if not hasattr(self, 'offsetx'):
            self.offsetx = offsetx
        if not hasattr(self, 'offsety'):
            self.offsety = offsety
        if not hasattr(self, 'text_offsetx'):
            self.text_offsetx = text_offsetx
        if not hasattr(self, 'text_offsety'):
            self.text_offsety = text_offsety
        if not hasattr(self, 'text'):
            self.text = text
        if not hasattr(self, 'max_lines'):
            self.max_lines = max_lines
        if not hasattr(self, 'textcolor'):
            self.textcolor = textcolor
        if not hasattr(self, 'text_anchor'):
            self.text_anchor = text_anchor
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'font'):
            self.font = font
        if not hasattr(self, 'fontsize'):
            self.fontsize = fontsize
        if not hasattr(self, 'visible'):
            self.visible = visible
        if not hasattr(self, 'xy_anchor'):
            self.xy_anchor = xy_anchor
        if not hasattr(self, 'layer'):
            self.layer = layer
        self.fillcolor = ''
        self.arg = self if arg is None else arg
        ao0 = _AnimateVis(line0=(), as_points=True, vis=self,
            screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1 = _AnimateVis(text='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1.dependent = True
        self.aos = (ao0, ao1)

    def remove(self):
        for ao in self.aos:
            ao.remove()


class AnimateCircle(_Vis):
    '''
    Displays a (partial) circle or (partial) ellipse , optionally with a text

    Parameters
    ----------
    radius : float
        radius of the circle

    radius1 : float
        the 'height of the ellipse. If None (default), a circle will be drawn

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
        If '', the given coordimates are used untranslated |n|
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

    textoffsetx : float
        extra x offset to the text_anchor point

    textoffsety : float
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
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue and arg can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    '''
    def __init__(self, radius=100, radius1=None, arc_angle0=0, arc_angle1=360,
        draw_arc=False, x=0, y=0, fillcolor='fg', linecolor='', linewidth=1,
        text='', fontsize=15, textcolor='bg', font='', angle=0, xy_anchor='', layer=0, max_lines=0,
        offsetx=0, offsety=0, text_anchor='c', text_offsetx=0, text_offsety=0, arg=None, parent=None,
        visible=True, env=None, screen_coordinates=False):
        self.env = g.default_env if env is None else env

        # the checks hasattr are req'd to not override methods of inherited classes
        if not hasattr(self, 'radius'):
            self.radius = radius
        if not hasattr(self, 'radius1'):
            self.radius1 = radius1
        if not hasattr(self, 'arc_angle0'):
            self.arc_angle0 = arc_angle0
        if not hasattr(self, 'arc_angle1'):
            self.arc_angle1 = arc_angle1
        if not hasattr(self, 'draw_arc'):
            self.draw_arc = draw_arc
        if not hasattr(self, 'fillcolor'):
            self.fillcolor = fillcolor
        if not hasattr(self, 'linecolor'):
            self.linecolor = linecolor
        if not hasattr(self, 'linewidth'):
            self.linewidth = linewidth
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'x'):
            self.x = x
        if not hasattr(self, 'y'):
            self.y = y
        if not hasattr(self, 'offsetx'):
            self.offsetx = offsetx
        if not hasattr(self, 'offsety'):
            self.offsety = offsety
        if not hasattr(self, 'text_offsetx'):
            self.text_offsetx = text_offsetx
        if not hasattr(self, 'text_offsety'):
            self.text_offsety = text_offsety
        if not hasattr(self, 'text'):
            self.text = text
        if not hasattr(self, 'max_lines'):
            self.max_lines = max_lines
        if not hasattr(self, 'textcolor'):
            self.textcolor = textcolor
        if not hasattr(self, 'text_anchor'):
            self.text_anchor = text_anchor
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'font'):
            self.font = font
        if not hasattr(self, 'fontsize'):
            self.fontsize = fontsize
        if not hasattr(self, 'visible'):
            self.visible = visible
        if not hasattr(self, 'xy_anchor'):
            self.xy_anchor = xy_anchor
        if not hasattr(self, 'layer'):
            self.layer = layer
        self.arg = self if arg is None else arg
        ao0 = _AnimateVis(circle0=(), vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1 = _AnimateVis(text='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1.dependent = True
        self. aos = (ao0, ao1)

    def remove(self):
        for ao in self.aos:
            ao.remove()


class AnimateImage(_Vis):
    '''
    Displays an image, optionally with a text

    Parameters
    ----------
    image : str
        image to be displayed |n|
        if used as function or method or in direct assigmnent,
        the image should be a PIL image (most likely via spec_to_image)

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
        If '', the given coordimates are used untranslated

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
        angle of the text (in degrees) |n|
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

    textoffsetx : float
        extra x offset to the text_anchor point

    textoffsety : float
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
        automatically upon termination of the parent

    Note
    ----
    All measures are in screen coordinates |n|

    All parameters, apart from queue and arg can be specified as: |n|
    - a scalar, like 10 |n|
    - a function with zero arguments, like lambda: title |n|
    - a function with one argument, being the time t, like lambda t: t + 10 |n|
    - a function with two parameters, being arg (as given) and the time, like lambda comp, t: comp.state |n|
    - a method instance arg for time t, like self.state, actually leading to arg.state(t) to be called
    '''

    def __init__(self, spec='', x=0, y=0, width=None,
        text='', fontsize=15, textcolor='bg', font='', angle=0, xy_anchor='', layer=0, max_lines=0,
        offsetx=0, offsety=0, text_anchor='c', text_offsetx=0, text_offsety=0, arg=None, parent=None,
        anchor='sw', visible=True, env=None, screen_coordinates=False):
        self.env = g.default_env if env is None else env

        # the checks hasattr are req'd to not override methods of inherited classes
        if not hasattr(self, 'spec'):
            self.spec = spec_to_image(spec)
        if not hasattr(self, 'width'):
            self.width = width
        if not hasattr(self, 'x'):
            self.x = x
        if not hasattr(self, 'y'):
            self.y = y
        if not hasattr(self, 'offsetx'):
            self.offsetx = offsetx
        if not hasattr(self, 'offsety'):
            self.offsety = offsety
        if not hasattr(self, 'text_offsetx'):
            self.text_offsetx = text_offsetx
        if not hasattr(self, 'text_offsety'):
            self.text_offsety = text_offsety
        if not hasattr(self, 'text'):
            self.text = text
        if not hasattr(self, 'max_lines'):
            self.max_lines = max_lines
        if not hasattr(self, 'textcolor'):
            self.textcolor = textcolor
        if not hasattr(self, 'text_anchor'):
            self.text_anchor = text_anchor
        if not hasattr(self, 'angle'):
            self.angle = angle
        if not hasattr(self, 'anchor'):
            self.anchor = anchor
        if not hasattr(self, 'font'):
            self.font = font
        if not hasattr(self, 'fontsize'):
            self.fontsize = fontsize
        if not hasattr(self, 'visible'):
            self.visible = visible
        if not hasattr(self, 'xy_anchor'):
            self.xy_anchor = xy_anchor
        if not hasattr(self, 'layer'):
            self.layer = layer

        self.arg = self if arg is None else arg
        ao0 = _AnimateVis(image='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1 = _AnimateVis(text='', vis=self, screen_coordinates=screen_coordinates, env=env, parent=parent)
        ao1.dependent = True
        self. aos = (ao0, ao1)

    def remove(self):
        for ao in self.aos:
            ao.remove()


class _AnimateVis(Animate):
    def __init__(self, vis, *args, **kwargs):
        Animate.__init__(self, *args, **kwargs)
        self.vis = vis

    def x(self, t):
        return _call(self.vis.x, t, self.vis.arg)

    def y(self, t):
        return _call(self.vis.y, t, self.vis.arg)

    def offsetx(self, t):
        return _call(self.vis.offsetx, t, self.vis.arg)

    def offsety(self, t):
        return _call(self.vis.offsety, t, self.vis.arg)

    def text_offsetx(self, t):
        return _call(self.vis.text_offsetx, t, self.vis.arg)

    def text_offsety(self, t):
        return _call(self.vis.text_offsety, t, self.vis.arg)

    def rectangle(self, t):
        return _call(self.vis.spec, t, self.vis.arg)

    def line(self, t):
        return _call(self.vis.spec, t, self.vis.arg)

    def polygon(self, t):
        return _call(self.vis.spec, t, self.vis.arg)

    def circle(self, t):
        return (
            _call(self.vis.radius, t, self.vis.arg),
            _call(self.vis.radius1, t, self.vis.arg),
            _call(self.vis.arc_angle0, t, self.vis.arg),
            _call(self.vis.arc_angle1, t, self.vis.arg),
            _call(self.vis.draw_arc, t, self.vis.arg))

    def image(self, t):
        return _call(self.vis.spec, t, self.vis.arg)

    def fillcolor(self, t):
        return _call(self.vis.fillcolor, t, self.vis.arg)

    def linecolor(self, t):
        return _call(self.vis.linecolor, t, self.vis.arg)

    def linewidth(self, t):
        return _call(self.vis.linewidth, t, self.vis.arg)

    def text(self, t):
        return _call(self.vis.text, t, self.vis.arg)

    def max_lines(self, t):
        return _call(self.vis.max_lines, t, self.vis.arg)

    def textcolor(self, t):
        return _call(self.vis.textcolor, t, self.vis.arg)

    def text_anchor(self, t):
        return _call(self.vis.text_anchor, t, self.vis.arg)

    def angle(self, t):
        return _call(self.vis.angle, t, self.vis.arg)

    def width(self, t):
        return _call(self.vis.width, t, self.vis.arg)

    def anchor(self, t):
        return _call(self.vis.anchor, t, self.vis.arg)

    def font(self, t):
        return _call(self.vis.font, t, self.vis.arg)

    def fontsize(self, t):
        return _call(self.vis.fontsize, t, self.vis.arg)

    def visible(self, t):
        return _call(self.vis.visible, t, self.vis.arg)

    def xy_anchor(self, t):
        return _call(self.vis.xy_anchor, t, self.vis.arg)

    def layer(self, t):
        return _call(self.vis.layer, t, self.vis.arg)


class _AosObject(object):  # for Monitor.animate and MonitorTimestamp.animate
    def __init__(self):
        self.aos = []

    def remove(self):
        for ao in self.aos:
            ao.remove()
        self.aos = []


class _Animate_index_x_Line(Animate):
    def __init__(self, monitor, xll, yll, width, height, value_offsety, value_scale, index_scale,
        linewidth, *args, **kwargs):
        self.monitor = monitor
        self.xll = xll
        self.yll = yll
        self.width = width
        self.height = height
        self.value_offsety = value_offsety
        self.value_scale = value_scale
        self.index_scale = index_scale
        self._linewidth = linewidth
        self.index_width = int(self.width / self.index_scale)
        Animate.__init__(self, *args, **kwargs)

    def index_to_x(self, index):
        if len(self.monitor._x) > self.index_width:
            index = index + self.index_width - len(self.monitor._x)
            if index < 0:
                self.done = True
        x = (index + 0.5) * self.index_scale
        return self.xll + max(self._linewidth / 2, min(self.width - self._linewidth / 2, x))

    def value_to_y(self, value):
        try:
            value = float(value)
        except ValueError:
            value = 0
        return self.yll + max(
            self._linewidth / 2, min(self.height - self._linewidth / 2, value * self.value_scale + self.value_offsety))

    def line(self, t):
        p = []
        self.done = False

        for index, value in zip(reversed(range(len(self.monitor._x))), reversed(self.monitor._x)):
            x = self.index_to_x(index)
            if self.done:
                break
            y = self.value_to_y(value)

            p.append(x)
            p.append(y)
        return p


class _Animate_t_x_Line(Animate):
    def __init__(self, monitor, width, height, value_offsety, value_scale, t_scale, linewidth,
        as_level, *args, **kwargs):
        self.monitor = monitor
        self.width = width
        self.height = height
        self.value_offsety = value_offsety
        self.value_scale = value_scale
        self.t_scale = t_scale
        self._linewidth = linewidth
        self.as_level = as_level
        self.t_width = self.width / self.t_scale
        Animate.__init__(self, *args, **kwargs)

    def t_to_x(self, t):
        t = t - self.t0
        if self.tnow - self.t0 > self.t_width:
            t = t + self.t_width - (self.tnow - self.t0)
            if t < 0:
                t = 0
                self.done = True
        x = t * self.t_scale
        return max(self._linewidth / 2, min(self.width - self._linewidth / 2, x))

    def value_to_y(self, value):
        if value == self.monitor.off:
            value = 0
        else:
            try:
                value = float(value)
            except ValueError:
                value = 0
        return max(
          self._linewidth / 2, min(self.height - self._linewidth / 2, value * self.value_scale + self.value_offsety))

    def line(self, t):
        self.tnow = t
        self.t0 = self.monitor._t[0]
        l = []
        value = self.monitor._xw[-1]
        lastt = t
        if self.as_level:
            l.append(self.t_to_x(lastt))
            l.append(self.value_to_y(value))
        self.done = False
        for value, t in zip(reversed(self.monitor._xw), reversed(self.monitor._t)):
            if self.as_level:
                l.append(self.t_to_x(lastt))
                l.append(self.value_to_y(value))
            l.append(self.t_to_x(t))
            l.append(self.value_to_y(value))
            if self.done:
                break
            lastt = t
        return l


class _Animate_t_Line(Animate):
    def __init__(self, monitor, width, height, t_scale, *args, **kwargs):
        self.monitor = monitor
        self.t_scale = t_scale
        self.width = width
        self.height = height
        self.t_width = self.width / self.t_scale
        Animate.__init__(self, *args, **kwargs)

    def line(self, t):
        t = t - self.monitor._t[0]
        if t > self.t_width:
            t = self.t_width
        x = t * self.t_scale
        return x, 0, x, self.height


class Component(object):
    '''Component object

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
        if None (default), it will try to start self.process() |n|
        if '', no process will be started even if self.process() exists,
        i.e. become a data component. |n|
        note that the function *must* be a generator,
        i.e. contains at least one yield.

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
        if omitted, the mode will be None. |n|
        also mode_time will be set to now.

    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used
    '''

    def __init__(self, name=None, at=None, delay=None, urgent=None,
      process=None, suppress_trace=False, suppress_pause_at_step=False, skip_standby=False, mode=None,
      env=None, **kwargs):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        _set_name(name, self.env._nameserializeComponent, self)
        self._qmembers = {}
        self._process = None
        self._status = data
        self._requests = collections.defaultdict(int)
        self._claims = collections.defaultdict(int)
        self._waits = []
        self._on_event_list = False
        self._scheduled_time = inf
        self._failed = False
        self._skip_standby = skip_standby
        self._creation_time = self.env._now
        self._suppress_trace = suppress_trace
        self._suppress_pause_at_step = suppress_pause_at_step
        self._mode = mode
        self._mode_time = self.env._now
        self._aos = {}

        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now

        if process is None:
            if hasattr(self, 'process'):
                p = self.process
                process_name = 'process'
            else:
                p = None
        else:
            if process is '':
                p = None
            else:
                try:
                    p = getattr(self, process)
                    process_name = process
                except AttributeError:
                    raise SalabimError('self.' + process + ' does not exist')
        if p is None:
            if at is not None:
                raise SalabimError('at is not allowed for a data component')
            if delay is not None:
                raise SalabimError('delay is not allowed for a data component')
            if urgent is not None:
                raise SalabimError('urgent is not allowed for a data component')
            if self.env._trace:
                if self._name == 'main':
                    self.env.print_trace('', '', self.name() +
                        ' create', _modetxt(self._mode))
                else:
                    self.env.print_trace('', '', self.name() +
                       ' create data component', _modetxt(self._mode))
        else:
            self.env.print_trace('', '', self.name() +
                ' create', _modetxt(self._mode))

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

            extra = 'process=' + process_name

            if urgent is None:
                urgent = False
            if delay is None:
                delay = 0
            if at is None:
                scheduled_time = self.env._now + delay
            else:
                scheduled_time = at + self.env._offset + delay

            self._reschedule(scheduled_time, urgent, 'activate', extra=extra)
        self.setup(**kwargs)

    def animation_objects(self, id):
        '''
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
        '''
        size_x = 50
        size_y = 50
        ao0 = AnimateRectangle(text=str(self.sequence_number()), textcolor='bg', spec=(-20, -20, 20, 20),
            linewidth=0, fillcolor='fg')
        return (size_x, size_y, ao0)

    def _remove_from_aos(self, q):
        if q in self._aos:
            for ao in self._aos[q][2:]:
                ao.remove()
            del self._aos[q]

    def setup(self):
        '''
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

            redcar=Car(color='red') |n|
            bluecar=Car(color='blue')
        '''
        pass

    def __repr__(self):
        return objectclass_to_str(self) + ' (' + self.name() + ')'

    def register(self, registry):
        '''
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
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self in registry:
            raise SalabimError(self.name() + ' already in registry')
        registry.append(self)
        return self

    def deregister(self, registry):
        '''
        deregisters the component in the registry

        Parameters
        ----------
        registry : list
            list of registered components

        Returns
        -------
        component (self) : Component
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self not in registry:
            raise SalabimError(self.name() + ' not in registry')
        registry.remove(self)
        return self

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append(objectclass_to_str(self) + ' ' + hex(id(self)))
        result.append('  name=' + self.name())
        result.append('  class=' + str(type(self)).split('.')[-1].split("'")[0])
        result.append('  suppress_trace=' + str(self._suppress_trace))
        result.append('  suppress_pause_at_step=' + str(self._suppress_pause_at_step))
        result.append('  status=' + self._status())
        result.append('  mode=' + _modetxt(self._mode).strip())
        result.append('  mode_time=' + time_to_string(self._mode_time))
        result.append('  creation_time=' + time_to_string(self._creation_time))
        result.append('  scheduled_time=' +
            time_to_string(self._scheduled_time))
        if len(self._qmembers) > 0:
            result.append('  member of queue(s):')
            for q in sorted(self._qmembers, key=lambda obj: obj.name().lower()):
                result.append('    ' + pad(q.name(), 20) + ' enter_time=' +
                    time_to_string(self._qmembers[q].enter_time - self.env._offset) +
                    ' priority=' + str(self._qmembers[q].priority))
        if len(self._requests) > 0:
            result.append('  requesting resource(s):')

            for r in sorted(list(self._requests),
              key=lambda obj: obj.name().lower()):
                result.append('    ' + pad(r.name(), 20) + ' quantity=' +
                    str(self._requests[r]))
        if len(self._claims) > 0:
            result.append('  claiming resource(s):')

            for r in sorted(list(self._claims), key=lambda obj: obj.name().lower()):
                result.append('    ' + pad(r.name(), 20) +
                    ' quantity=' + str(self._claims[r]))
        if len(self._waits) > 0:
            if self._wait_all:
                result.append('  waiting for all of state(s):')
            else:
                result.append('  waiting for any of state(s):')
            for s, value, _ in self._waits:
                result.append('    ' + pad(s.name(), 20) +
                    ' value=' + str(value))
        return return_or_print(result, as_str, file)

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
            if self.env._trace:
                self.env.print_trace('', '', self.name(), 'request failed')
            for r in list(self._requests):
                self.leave(r._requesters)
                if r._requesters._length == 0:
                    r._minq = inf
            self._requests = collections.defaultdict(int)
            self._failed = True

        if self._waits:
            if self.env._trace:
                self.env.print_trace('', '', self.name(), 'wait failed')
            for state, _, _ in self._waits:
                if self in state._waiters:  # there might be more values for this state
                    self.leave(state._waiters)
            self._waits = []
            self._failed = True

    def _reschedule(self, scheduled_time, urgent, caller, extra='', s0=None):
        if scheduled_time < self.env._now:
            raise SalabimError(
                'scheduled time ({:0.3f}) before now ({:0.3f})'.
                format(scheduled_time, self.env._now))
        self._scheduled_time = scheduled_time
        if scheduled_time != inf:
            self._push(scheduled_time, urgent)
        self._status = scheduled
        if self.env._trace:
            if extra == '*':
                scheduled_time_str = 'ends on no events left  '
                extra = ' '
            else:
                scheduled_time_str = 'scheduled for {:10.3f}'.format(scheduled_time - self.env._offset)
            self.env.print_trace(
                '', '', self.name() + ' ' + caller,
                merge_blanks(
                    scheduled_time_str +
                    _urgenttxt(urgent) + '@' + self.lineno_txt(),
                    _modetxt(self._mode),
                    extra),
                s0=s0)

    def activate(self, at=None, delay=0, urgent=False, process=None,
      keep_request=False, keep_wait=False, mode=None, **kwargs):
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
        '''
        p = None
        if process is None:
            if self._status == data:
                if hasattr(self, 'process'):
                    p = self.process
                    process_name = 'process'
                else:
                    raise SalabimError('no process for data component')
        else:
            try:
                p = getattr(self, process)
                process_name = process
            except AttributeError:
                raise SalabimError('self.' + process + ' does not exist')

        if p is None:
            extra = ''
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

            extra = 'process=' + process_name

        if self._status != current:
            self._remove()
            if p is None:
                if not (keep_request or keep_wait):
                    self._check_fail()
            else:
                self._check_fail()

        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now

        if at is None:
            scheduled_time = self.env._now + delay
        else:
            scheduled_time = at + self.env._offset + delay

        self._reschedule(scheduled_time, urgent, 'activate', extra=extra)

    def hold(self, duration=None, till=None, urgent=False, mode=None):
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
        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now

        if till is None:
            if duration is None:
                scheduled_time = self.env._now
            else:
                scheduled_time = self.env._now + duration
        else:
            if duration is None:
                scheduled_time = till + self.env._offset
            else:
                raise SalabimError('both duration and till specified')
        self._reschedule(scheduled_time, urgent, 'hold')

    def passivate(self, mode=None):
        '''
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
        '''
        if self._status == current:
            self._remaining_duration = 0
        else:
            self._checkisnotdata()
            self._remove()
            self._check_fail()
            self._remaining_duration = self._scheduled_time - self.env._now
        self._scheduled_time = inf
        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now
        if self.env._trace:
            self.env.print_trace('', '', self.name() + ' passivate', merge_blanks(_modetxt(self._mode)))
        self._status = passive

    def interrupt(self, mode=None):
        '''
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
        '''
        if self._status == current:
            raise SalabimError(self.name() + ' current component cannot be interrupted')
        else:
            if mode is not None:
                self._mode = mode
                self._mode_time = self.env._now
            if self._status == interrupted:
                self._interrupt_level += 1
                extra = '.' + str(self._interrupt_level)
            else:
                self._checkisnotdata()
                self._remove()
                self._remaining_duration = self._scheduled_time - self.env._now
                self._interrupted_status = self._status
                self._interrupt_level = 1
                self._status = interrupted
                extra = ''
            self.env.print_trace('', '', self.name() + ' interrupt' + extra, merge_blanks(_modetxt(self._mode)))

    def resume(self, all=False, mode=None, urgent=False):
        '''
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

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time

        Note
        ----
        Can be only applied to interrupted components. |n|
        '''
        if self._status == interrupted:
            if mode is not None:
                self._mode = mode
                self._mode_time = self.env._now
            self._interrupt_level -= 1
            if self._interrupt_level and (not all):
                self.env.print_trace(
                    '', '', self.name() + ' resume (interrupted.' + str(self._interrupt_level) + ')',
                    merge_blanks(_modetxt(self._mode)))
            else:
                self._status = self._interrupted_status
                self.env.print_trace(
                    '', '', self.name() + ' resume (' + self.status()() + ')', merge_blanks(_modetxt(self._mode)))
                if self._status == passive:
                    self.env.print_trace('', '', self.name() + ' passivate', merge_blanks(_modetxt(self._mode)))
                elif self._status == standby:
                    self._scheduled_time = self.env._now
                    self.env._standbylist.append(self)
                    self.env.print_trace('', '', self.name() + ' standby', merge_blanks(_modetxt(self._mode)))
                elif self._status == scheduled:
                    if self._waits:
                        if self._trywait():
                            return
                        reason = 'wait'
                    elif self._requests:
                        if self._tryrequest():
                            return
                        reason = 'request'
                    else:
                        reason = 'hold'
                    self._reschedule(self.env._now + self._remaining_duration, urgent, reason)
                else:
                    raise SalabimError(self.name() + ' unexpected interrupted_status', self._status())
        else:
            raise SalabimError(self.name() + ' not interrupted')

    def cancel(self, mode=None):
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
        if to be used for the current component, use ``yield self.cancel()``.
        '''
        if self._status != current:
            self._checkisnotdata()
            self._remove()
            self._check_fail()
        self._process = None
        self._scheduled_time = inf
        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now
        if self.env._trace:
            self.env.print_trace('', '', 'cancel ' +
                self.name() + ' ' + _modetxt(self._mode))
        self._status = data
        for ao in self.env.an_objects[:]:
            if ao.parent == self:
                self.env.an_objects.remove(ao)
        for so in self.env.sys_objects[:]:
            if so.parent == self:
                so.remove()

    def standby(self, mode=None):
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
        use ``yield self.standby()``.
        '''
        if self._status != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()
        self._scheduled_time = self.env._now
        self.env._standbylist.append(self)
        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now
        if self.env._trace:
            if self.env._buffered_trace:
                self.env._buffered_trace = False
            else:
                self.env.print_trace('', '', 'standby', _modetxt(self._mode))
        self._status = standby

    def request(self, *args, **kwargs):
        '''
        request from a resource or resources

        Parameters
        ----------
        args : sequence of items where each item can be:
            - resource, where quantity=1, priority=tail of requesters queue
            - tuples/list containing a resource, a quantity and optionally a priority.
                if the priority is not specified, the request
                for the resource be added to the tail of
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
        ``yield self.request(r1)`` |n|
        --> requests 1 from r1 |n|
        ``yield self.request(r1,r2)`` |n|
        --> requests 1 from r1 and 1 from r2 |n|
        ``yield self.request(r1,(r2,2),(r3,3,100))`` |n|
        --> requests 1 from r1, 2 from r2 and 3 from r3 with priority 100 |n|
        ``yield self.request((r1,1),(r2,2))`` |n|
        --> requests 1 from r1, 2 from r2 |n|
        '''
        fail_at = kwargs.pop('fail_at', None)
        fail_delay = kwargs.pop('fail_delay', None)
        mode = kwargs.pop('mode', None)
        if kwargs:
            raise TypeError("request() got an expected keyword argument '" + tuple(kwargs)[0] + "'")

        if self._status != current:
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
                    scheduled_time = self.env._now + fail_delay
        else:
            if fail_delay is None:
                scheduled_time = fail_at + self.env._offset
            else:
                raise SalabimError('both fail_at and fail_delay specified')

        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now

        self._failed = False

        for arg in args:
            q = 1
            priority = None
            if isinstance(arg, Resource):
                r = arg
            elif isinstance(arg, (tuple, list)):
                r = arg[0]
                if len(arg) >= 2:
                    q = arg[1]
                if len(arg) >= 3:
                    priority = arg[2]
            else:
                raise SalabimError('incorrect specifier', arg)

            if q <= 0:
                raise SalabimError('quantity ' + str(q) + ' <=0')
            self._requests[r] += q  # is same resource is specified several times, just add them up
            addstring = ''
            if priority is None:
                self.enter(r._requesters)
            else:
                addstring = addstring + ' priority=' + str(priority)
                self.enter_sorted(r._requesters, priority)
            if self.env._trace:
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
        if self._status == interrupted:
            return False
        honored = True
        for r in self._requests:
            if self._requests[r] > (r._capacity - r._claimed_quantity + 1e-8):
                honored = False
                break
        if honored:
            for r in list(self._requests):
                r._claimed_quantity += self._requests[r]

                self.leave(r._requesters)
                if not r._anonymous:
                    self._claims[r] += self._requests[r]
                    mx = self._member(r._claimers)
                    if mx is None:
                        self.enter(r._claimers)
                if r._requesters._length == 0:
                    r._minq = inf
                r.claimed_quantity.tally(r._claimed_quantity)
                r.occupancy.tally(0 if r._capacity <= 0 else r._claimed_quantity / r._capacity)
                r.available_quantity.tally(r._capacity - r._claimed_quantity)
            self._requests = collections.defaultdict(int)
            self._remove()
            self._reschedule(self.env._now, False, 'request honor', s0=self.env.last_s0)
        return honored

    def _release(self, r, q=None, s0=None):
        if r not in self._claims:
            raise SalabimError(self.name() +
                ' not claiming from resource ' + r.name())
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
        if self.env._trace:
            self.env.print_trace('', '', self.name(),
                'release ' + str(q) + ' from ' + r.name(), s0=s0)
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
            for arg in args:
                q = None
                if isinstance(arg, Resource):
                    r = arg
                elif isinstance(arg, (tuple, list)):
                    r = arg[0]
                    if len(arg) >= 2:
                        q = arg[1]
                else:
                    raise SalabimError('incorrect specifier' + arg)
                if r._anonymous:
                    raise SalabimError(
                        'not possible to release anonymous resources ' + r.name())
                self._release(r, q)
        else:
            for r in list(self._claims):
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
        ``yield self.wait(s1)`` |n|
        --> waits for s1.value()==True |n|
        ``yield self.wait(s1,s2)`` |n|
        --> waits for s1.value()==True or s2.value==True |n|
        ``yield self.wait((s1,False,100),(s2,'on'),s3)`` |n|
        --> waits for s1.value()==False or s2.value=='on' or s3.value()==True |n|
        s1 is at the tail of waiters, because of the set priority |n|
        ``yield self.wait(s1,s2,all=True)`` |n|
        --> waits for s1.value()==True and s2.value==True |n|
        '''
        fail_at = kwargs.pop('fail_at', None)
        fail_delay = kwargs.pop('fail_delay', None)
        all = kwargs.pop('all', False)
        mode = kwargs.pop('mode', None)
        if kwargs:
            raise TypeError("wait() got an expected keyword argument '" + tuple(kwargs)[0] + "'")

        if self._status != current:
            self._checkisnotdata()
            self._checkisnotmain()
            self._remove()
            self._check_fail()

        self._wait_all = all
        self._fail = False

        if fail_at is None:
            if fail_delay is None:
                scheduled_time = inf
            else:
                if fail_delay == inf:
                    scheduled_time = inf
                else:
                    scheduled_time = self.env._now + fail_delay
        else:
            if fail_delay is None:
                scheduled_time = fail_at + self.env._offset
            else:
                raise SalabimError('both fail_at and fail_delay specified')

        if mode is not None:
            self._mode = mode
            self._mode_time = self.env._now

        for arg in args:
            value = True
            priority = None
            if isinstance(arg, State):
                state = arg
            elif isinstance(arg, (tuple, list)):
                state = arg[0]
                if len(arg) >= 2:
                    value = arg[1]
                if len(arg) >= 3:
                    priority = arg[2]
            else:
                raise SalabimError('incorrect specifier', args)

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
        if self._status == interrupted:
            return False
        if self._wait_all:
            honored = True
            for state, value, valuetype in self._waits:
                if valuetype == 0:
                    if value != state._value:
                        honored = False
                        break
                elif valuetype == 1:
                    if eval(value.replace('$', 'state._value')):
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
                    self.leave(s._waiters)
            self._waits = []
            self._remove()
            self._reschedule(self.env._now, False, 'wait honor', s0=self.env.last_s0)

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
        return list(self._claims)

    def requested_resources(self):
        '''
        Returns
        -------
        list of requested resources : list
        '''
        return list(self._requests)

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

    def name(self, value=None):
        '''
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
        '''
        if value is not None:
            self._name = value
        return self._name

    def base_name(self):
        '''
        Returns
        -------
        base name of the component (the name used at initialization): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the component : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dotcomma at the end)
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

    def suppress_trace(self, value=None):
        '''
        Parameters
        ----------
        value: bool
            new suppress_trace value |n|
            if omitted, no change

        Returns
        -------
        suppress_trace : bool
            components with the suppress_status of True, will be ignored in the trace
        '''
        if value is not None:
            self._suppress_trace = value
        return self._suppress_trace

    def suppress_pause_at_step(self, value=None):
        '''
        Parameters
        ----------
        value: bool
            new suppress_trace value |n|
            if omitted, no change

        Returns
        -------
        suppress_pause_at_step : bool
            components with the suppress_pause_at_step of True, will be ignored in a step
        '''
        if value is not None:
            self._suppress_pause_at_step = value
        return self._suppress_pause_at_step

    def skip_standby(self, value=None):
        '''
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
        '''
        if value is not None:
            self._skip_standby = value
        return self._skip_standby

    def mode(self, value=None):
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
        if value is not None:
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

    def isinterrupted(self):
        '''
        Returns
        -------
        True if status is interrupted, False otherwise : bool

        Note
        ----
        Be sure to always include the parentheses, otherwise the result will be always True
        '''
        return self._status == interrupted

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

    def queues(self):
        '''
        Returns
        -------
        set of queues where the component belongs to : set
        '''
        return set(self._qmembers)

    def count(self, q=None):
        '''
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
        '''
        if q is None:
            return len(self._qmembers)
        else:
            return 1 if self in q else 0

    def index(self, q):
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
        return self

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
        return self

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
        return self

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
        return self

    def enter_sorted(self, q, priority):
        '''
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
        '''

        self._checknotinqueue(q)
        m2 = q._head.successor
        while (m2 != q._tail) and (m2.priority <= priority):
            m2 = m2.successor
        Qmember().insert_in_front_of(m2, self, q, priority)
        return self

    def leave(self, q=None):
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
                self.env.print_trace('', '', self.name(), 'leave ' + q.name())
        length_of_stay = self.env._now - mx.enter_time
        q.length_of_stay.tally(length_of_stay)
        q.length.tally(q._length)
        return self

    def priority(self, q, priority=None):
        '''
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
        '''

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
        return mx.enter_time - self.env._offset

    def creation_time(self):
        '''
        Returns
        -------
        time the component was created : float
        '''
        return self._creation_time - self.env._offset

    def scheduled_time(self):
        '''
        Returns
        -------
        time the component scheduled for, if it is scheduled : float
            returns inf otherwise
        '''
        return self._scheduled_time - self.env._offset

    def remaining_duration(self, value=None, urgent=False):
        '''
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

        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled
            in front of all components scheduled
            for the same time

        Returns
        -------
        remaining duration : float
            if passive, remaining time at time of passivate |n|
            if scheduled, remaing time till scheduled time |n|
            if requesting or waiting, time till fail_at time |n|
            else: 0

        Note
        ----
        This method is usefu for interrupting a process and then resuming it,
        after some (breakdown) time
        '''
        if value is not None:
            if self._status in (passive, interrupted):
                self._remaining_duration = value
            elif self._status == current:
                raise SalabimError(
                    'setting remaining_duration not allowed for current component (' + self.name() + ')')
            elif self._status == standby:
                raise SalabimError(
                    'setting remaining_duration not allowed for standby component (' + self.name() + ')')
            else:
                self._remove()
                self._reschedule(value + self.env._now, urgent, 'set remaining_duration', extra='')

        if self._status in (passive, interrupted):
            return self._remaining_duration
        elif self._status == scheduled:
            return self._scheduled_time - self.env._now
        else:
            return 0

    def mode_time(self):
        '''
        Returns
        -------
        time the component got it's latest mode : float
            For a new component this is
            the time the component was created. |n|
            this function is particularly useful for animations.
        '''
        return self._mode_time - self.env._offset

    def status(self):
        '''
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
        '''
        if len(self._requests) > 0:
            return requesting
        if len(self._waits) > 0:
            return waiting
        return self._status

    def interrupted_status(self):
        '''
        returns the original status of an interrupted component

        possible values are
            - passive
            - scheduled
            - requesting
            - waiting
            - standby
        '''
        if self._status != interrupted:
            raise SalabimError(self.name() + 'not interrupted')
        if len(self._requests) > 0:
            return requesting
        if len(self._waits) > 0:
            return waiting
        return self._interrupted_status

    def interrupt_level(self):
        '''
        returns interrupt level of an interrupted component |n|
        non interrupted components return 0
        '''
        if self._status == interrupted:
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

    def lineno_txt(self):
        plus = '+'
        if self == self.env._main:
            frame = self.frame
        else:
            if self._process_isgenerator:
                frame = self._process.gi_frame
                if frame.f_lasti == -1:  # checks whether generator is created
                    plus = ' '
            else:
                gs = inspect.getsourcelines(self._process)
                s0 = self.env.filename_lineno_to_str(self._process.__code__.co_filename, gs[1]) + ' '
                return s0
        return self.env._frame_to_lineno(frame) + plus


class Random(random.Random):
    '''
    defines a randomstream, equivalent to random.Random()

    Parameters
    ----------
    seed : any hashable
        default: None
    '''
    def __init__(self, seed=None):
        random.Random.__init__(self, seed)


class _Distribution():

    def bounded_sample(self, lowerbound=-inf, upperbound=inf, fail_value=None, number_of_retries=100):
        '''
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

        Returns
        -------
        Bounded sample of a distribution : depending on distribution type (usually float)

        Note
        ----
        If, after number_of_tries retries, the sampled value is still not within the given bounds,
        fail_value  will be returned |n|
        Samples that cannot be converted (only possible with Pdf and CumPdf) to float
        are assumed to be within the bounds.
        '''
        if (lowerbound == -inf) and (upperbound == inf):
            return self.sample()

        if lowerbound is None:
            lowerbound = -inf
        if upperbound is None:
            upperbound = inf

        if lowerbound > upperbound:
            raise SalabimError('lowerbound > upperbound')

        if number_of_retries <= 0:
            raise SalabimError('number_of_tries <= 0')

        if fail_value is None:
            if lowerbound == -inf:
                fail_value = upperbound
            else:
                fail_value = lowerbound

        for _ in range(number_of_retries):
            sample = self.sample()
            try:
                samplefloat = float(sample)
            except ValueError:
                return sample  # a value that cannot be converted to a float is sampled is assumed to be correct

            if (samplefloat >= lowerbound) and (samplefloat <= upperbound):
                return sample

        return fail_value

    def __call__(self, *args):
        return self.sample(*args)


class Exponential(_Distribution):
    '''
    exponential distribution

    Parameters
    ----------
    mean : float
        mean of the distribtion (beta)|n|
        if omitted, the rate is used |n|
        must be >0

    rate : float
        rate of the distribution (lambda)|n|
        if omitted, the mean is used |n|
        must be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    Note
    ----
    Either mean or rate has to be specified, not both
    '''

    def __init__(self, mean=None, rate=None, randomstream=None):
        if mean is None:
            if rate is None:
                raise SalabimError('neither mean nor rate are specified')
            else:
                if rate <= 0:
                    raise SalabimError('rate<=0')
                self._mean = 1 / rate
        else:
            if rate is None:
                if mean <= 0:
                    raise SalabimError('mean<=0')
                self._mean = mean
            else:
                raise SalabimError('both mean and rate are specified')

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

    def __repr__(self):
        return('Exponential')

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Exponential distribution ' + hex(id(self)))
        result.append('  mean=' + str(self._mean))
        result.append('  rate (lambda)=' + str(1 / self._mean))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : float
        '''
        return self.randomstream.expovariate(1 / (self._mean))

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Normal(_Distribution):
    '''
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

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''

    def __init__(self, mean, standard_deviation=None, coefficient_of_variation=None,
      use_gauss=False, randomstream=None):
        self._use_gauss = use_gauss
        self._mean = mean
        if standard_deviation is None:
            if coefficient_of_variation is None:
                self._standard_deviation = 0
            else:
                if mean == 0:
                    raise SalabimError('coefficient_of_variation not allowed with mean = 0')
                self._standard_deviation = coefficient_of_variation * mean
        else:
            if coefficient_of_variation is None:
                self._standard_deviation = standard_deviation
            else:
                raise SalabimError('both standard_deviation and coefficient_of_variation specified')
        if self._standard_deviation < 0:
            raise SalabimError('standard_deviation < 0')
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

    def __repr__(self):
        return 'Normal'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Normal distribution ' + hex(id(self)))
        result.append('  mean=' + str(self._mean))
        result.append('  standard_deviation=' + str(self._standard_deviation))
        if self._mean == 0:
            result.append('  coefficient of variation= N/A')
        else:
            result.append('  coefficient_of_variation=' + str(self._standard_deviation / self._mean))
        if self._use_gauss:
            result.append('  use_gauss=True')
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : float
        '''
        if self._use_gauss:
            return self.randomstream.gauss(self._mean, self._standard_deviation)
        else:
            return self.randomstream.normalvariate(self._mean, self._standard_deviation)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class IntUniform(_Distribution):
    '''
    integer uniform distribution, i.e. sample integer values between lowerbound and upperbound (inclusive)

    Parameters
    ----------
    lowerbound : int
        lowerbound of the distribution

    upperbound : int
        upperbound of the distribution |n|
        if omitted, lowerbound will be used |n|
        must be >= lowerbound

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    Note
    ----
    In contrast to range, the upperbound is included.

    Example
    -------
    die = sim.IntUniform(1,6)
    for _ in range(10):
        print (die())

    This will print 10 throws of a die.
    '''

    def __init__(self, lowerbound, upperbound=None, randomstream=None):
        self._lowerbound = lowerbound
        if upperbound is None:
            self._upperbound = lowerbound
        else:
            self._upperbound = upperbound
        if self._lowerbound > self._upperbound:
            raise SalabimError('lowerbound>upperbound')
        if self._lowerbound != int(self._lowerbound):
            raise SalabimError('lowerbound not integer')
        if self._upperbound != int(self._upperbound):
            raise SalabimError('upperbound not integer')

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = (self._lowerbound + self._upperbound) / 2

    def __repr__(self):
        return 'IntUniform'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('IntUniform distribution ' + hex(id(self)))
        result.append('  lowerbound=' + str(self._lowerbound))
        result.append('  upperbound=' + str(self._upperbound))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution: int
        '''
        return self.randomstream.randint(self._lowerbound, self._upperbound)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Uniform(_Distribution):
    '''
    uniform distribution

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

    def __init__(self, lowerbound, upperbound=None, randomstream=None):
        self._lowerbound = lowerbound
        if upperbound is None:
            self._upperbound = lowerbound
        else:
            self._upperbound = upperbound
        if self._lowerbound > self._upperbound:
            raise SalabimError('lowerbound>upperbound')
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = (self._lowerbound + self._upperbound) / 2

    def __repr__(self):
        return 'Uniform'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Uniform distribution ' + hex(id(self)))
        result.append('  lowerbound=' + str(self._lowerbound))
        result.append('  upperbound=' + str(self._upperbound))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution: float
        '''
        return self.randomstream.uniform(self._lowerbound, self._upperbound)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Triangular(_Distribution):
    '''
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

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''

    def __init__(self, low, high=None, mode=None, randomstream=None):
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
            raise SalabimError('low>high')
        if self._low > self._mode:
            raise SalabimError('low>mode')
        if self._high < self._mode:
            raise SalabimError('high<mode')
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = (self._low + self._mode + self._high) / 3

    def __repr__(self):
        return 'Triangular'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Triangular distribution ' + hex(id(self)))
        result.append('  low=' + str(self._low))
        result.append('  high=' + str(self._high))
        result.append('  mode=' + str(self._mode))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribtion : float
        '''
        return self.randomstream.triangular(self._low, self._high, self._mode)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Constant(_Distribution):
    '''
    constant distribution

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

    def __init__(self, value, randomstream=None):
        self._value = value
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._mean = value

    def __repr__(self):
        return 'Constant'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Constant distribution ' + hex(id(self)))
        result.append('  value=' + str(self._value))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        sample of the distribution (= the specified constant) : float
        '''
        return(self._value)

    def mean(self):
        '''
        Returns
        -------
        mean of the distribution (= the specified constant) : float
        '''
        return self._mean


class Poisson(_Distribution):
    '''
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
    '''

    def __init__(self, mean, randomstream=None):
        if mean <= 0:
            raise SalabimError('mean (lambda) <=0')

        self._mean = mean

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

    def __repr__(self):
        return 'Poisson'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Poissonl distribution ' + hex(id(self)))
        result.append('  mean (lambda)' + str(self._lambda_))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : int
        '''
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
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Weibull(_Distribution):
    '''
    weibull distribution

    Parameters
    ----------
    scale: float
        scale of the distribution (alpha or k)

    shape: float
        shape of the distribution (beta or lambda)|n|
        should be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''

    def __init__(self, scale, shape, randomstream=None):
        self._scale = scale
        if shape <= 0:
            raise SalabimError('shape<=0')

        self._shape = shape
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        self._mean = self._scale * math.gamma((1 / self._shape) + 1)

    def __repr__(self):
        return 'Weibull'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Weibull distribution ' + hex(id(self)))
        result.append('  scale (alpha or k)=' + str(self._scale))
        result.append('  shape (beta or lambda)=' + str(self._shape))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : float
        '''
        return self.randomstream.weibullvariate(self._scale, self._shape)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Gamma(_Distribution):
    '''
    gamma distribution

    Parameters
    ----------
    shape: float
        shape of the distribution (k) |n|
        should be >0

    scale: float
        scale of the distribution (teta) |n|
        should be >0

    rate : float
        rate of the distribution (beta) |n|
        should be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    Note
    ----
    Either scale or rate has to be specified, not both.
    '''

    def __init__(self, shape, scale=None, rate=None, randomstream=None):
        if shape <= 0:
            raise SalabimError('shape<=0')
        self._shape = shape
        if rate is None:
            if scale is None:
                raise SalabimError('neither scale nor rate specified')
            else:
                if scale <= 0:
                    raise SalabimError('scale<=0')
                self._scale = scale
        else:
            if scale is None:
                if rate <= 0:
                    raise SalabimError('rate<=0')
                self._scale = 1 / rate
            else:
                raise SalabimError('both scale and rate specified')

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        self._mean = self._shape * self._scale

    def __repr__(self):
        return 'Gamma'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Gamma distribution ' + hex(id(self)))
        result.append('  shape (k)=' + str(self._shape))
        result.append('  scale (teta)=' + str(self._scale))
        result.append('  rate (beta)=' + str(1 / self._scale))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : float
        '''
        return self.randomstream.gammavariate(self._shape, self._scale)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Beta(_Distribution):
    '''
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
    '''

    def __init__(self, alpha, beta, randomstream=None):
        if alpha <= 0:
            raise SalabimError('alpha<=0')
        self._alpha = alpha
        if beta <= 0:
            raise SalabimError('beta<>=0')
        self._beta = beta

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        self._mean = self._alpha / (self._alpha + self._beta)

    def __repr__(self):
        return 'Beta'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Beta distribution ' + hex(id(self)))
        result.append('  alpha=' + str(self._alpha))
        result.append('  beta=' + str(self._beta))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : float
        '''
        return self.randomstream.betavariate(self._alpha, self._beta)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Erlang(_Distribution):
    '''
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

    scale: float
        scale of the distribution (mu) |n|
        if omitted, the rate is used |n|
        should be >0

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    Note
    ----
    Either rate or scale has to be specified, not both.
    '''

    def __init__(self, shape, rate=None, scale=None, randomstream=None):
        if int(shape) != shape:
            raise SalabimError('shape not integer')
        if shape <= 0:
            raise SalabimError('shape <=0')
        self._shape = shape
        if rate is None:
            if scale is None:
                raise SalabimError('neither rate nor scale specified')
            else:
                if scale <= 0:
                    raise SalabimError('scale<=0')
                self._rate = 1 / scale
        else:
            if scale is None:
                if rate <= 0:
                    raise SalabimError('rate<=0')
                self._rate = rate
            else:
                raise SalabimError('both rate and scale specified')

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        self._mean = self._shape / self._rate

    def __repr__(self):
        return 'Erlang'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Erlang distribution ' + hex(id(self)))
        result.append('  shape (k)=' + str(self._shape))
        result.append('  rate (lambda)=' + str(self._rate))
        result.append('  scale (mu)=' + str(1 / self._rate))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : float
        '''
        return self.randomstream.gammavariate(self._shape, 1 / self._rate)

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
        '''
        return self._mean


class Cdf(_Distribution):
    '''
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

    randomstream: randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it defines a new stream with the specified seed

    '''

    def __init__(self, spec, randomstream=None):
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
            raise SalabimError('last cumulative value should be > 0')
        self._cum = [x / lastcum for x in self._cum]
        self._mean = 0
        for i in range(len(self._cum) - 1):
            self._mean +=\
                ((self._x[i] + self._x[i + 1]) / 2) * \
                (self._cum[i + 1] - self._cum[i])

    def __repr__(self):
        return 'Cdf'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Cdf distribution ' + hex(id(self)))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : float
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
        Mean of the distribution : float
        '''
        return self._mean


class Pdf(_Distribution):
    '''
    Probability distribution function

    Parameters
    ----------
    spec : list or tuple
        either

        -   if no probabilities specified: |n|
            list with x-values and corresponding probability
            (x0, p0, x1, p1, ...xn,pn) |n|
        -   if probabilities is specified: |n|
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
    The x-values can be any type. |n|
    If it is a salabim distribution, not the distribution,
    but a sample will be returned when calling sample.
    '''

    def __init__(self, spec, probabilities=None, randomstream=None):
        self._x = [0]  # just a place holder
        self._cum = [0]
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        sump = 0
        sumxp = 0
        hasmean = True
        if probabilities is None:
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

        self._cum = [x / sump for x in self._cum]
        if hasmean:
            self._mean = sumxp / sump
        else:
            self._mean = nan

    def __repr__(self):
        return 'Pdf'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Pdf distribution ' + hex(id(self)))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : any (usually float)
        '''
        r = self.randomstream.random()
        for cum, x in zip(self._cum, self._x):
            if r <= cum:
                if isinstance(x, _Distribution):
                    return x.sample()
                return x

    def mean(self):
        '''
        Returns
        -------
        mean of the distribution : float
            if the mean can't be calculated (if not all x-values are scalars or distributions),
            nan will be returned.
        '''
        return self._mean


class CumPdf(_Distribution):
    '''
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

    randomstream : randomstream
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed

    Note
    ----
    p0<=p1<=..pn>0 |n|
    all densities are auto scaled according to pn,
    so no need to have pn be 1 or 100. |n|
    The x-values can be any type. |n|
    If it is a salabim distribution, not the distribution,
    but a sample will be returned when calling sample.
    '''

    def __init__(self, spec, cumprobabilities=None, cum=False, randomstream=None):
        self._x = [0]  # just a place holder
        self._cum = [0]
        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream

        sump = 0
        sumxp = 0
        hasmean = True
        if cumprobabilities is None:
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
                p = p - sump
                if p < 0:
                    raise SalabimError('non increasing cumulative probabilities')
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
            if isinstance(cumprobabilities, (list, tuple)):
                cumprobabilities = list(cumprobabilities)
            else:
                raise SalabimError('wrong type for cumulative probabilities')
            if len(spec) != len(cumprobabilities):
                raise SalabimError(
                    'length of x-values does not match length of cumulative probabilities')

            while len(spec) > 0:
                x = spec.pop(0)
                self._x.append(x)
                p = cumprobabilities.pop(0)
                p = p - sump
                if p < 0:
                    raise SalabimError('non increasing cumulative probabilities')
                sump += p
                self._cum.append(sump)
                if isinstance(x, _Distribution):
                    x = x._mean
                try:
                    sumxp += float(x) * p
                except:
                    hasmean = False

        if sump == 0:
            raise SalabimError('last cumulative probability should be >0')

        self._cum = [x / sump for x in self._cum]
        if hasmean:
            self._mean = sumxp / sump
        else:
            self._mean = nan

    def __repr__(self):
        return 'CumPdf'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('CumPdf distribution ' + hex(id(self)))
        result.append('  randomstream=' + hex(id(self.randomstream)))
        return return_or_print(result, as_str, file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the distribution : any (usually float)
        '''
        r = self.randomstream.random()
        for cum, x in zip(self._cum, self._x):
            if r <= cum:
                if isinstance(x, _Distribution):
                    return x.sample()
                return x

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
    '''

    def __init__(self, spec, randomstream=None):

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
            for distype in ('Uniform', 'Constant', 'Triangular', 'Exponential', 'Normal',
              'Cdf', 'Pdf', 'CumPdf', 'Weibull', 'Gamma', 'Erlang', 'Beta', 'IntUniform', 'Poisson'):
                if pre == distype.upper()[:len(pre)]:
                    sp[0] = distype
                    spec = '('.join(sp)
                    break

        d = eval(spec)

        if randomstream is None:
            self.randomstream = random
        else:
            _checkrandomstream(randomstream)
            self.randomstream = randomstream
        self._distribution = d
        self._mean = d._mean

    def __repr__(self):
        return self._distribution.__repr__()

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        return self._distribution.print_info(as_str=as_str, file=file)

    def sample(self):
        '''
        Returns
        -------
        Sample of the  distribution : any (usually float)
        '''
        self._distribution.randomstream = self.randomstream
        return self._distribution.sample()

    def mean(self):
        '''
        Returns
        -------
        Mean of the distribution : float
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
        overrides the default animation_object method |n|
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
        if omitted, default_env is used
    '''
    def __init__(self, name=None, value=False, type='any',
      monitor=True, animation_objects=None, env=None, *args, **kwargs):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        _set_name(name, self.env._nameserializeState, self)
        self._value = value
        self._aos = []
        savetrace = self.env._trace
        self.env._trace = False
        self._waiters = Queue(
            name='waiters of ' + self.name(),
            monitor=monitor, env=self.env)
        self._waiters._isinternal = True
        self.env._trace = savetrace
        self.value = MonitorTimestamp(
            name='Value of ' + self.name(),
            initial_tally=value, monitor=monitor, type=type, env=self.env)
        if animation_objects is not None:
            self.animation_objects = animation_objects.__get__(self, State)
        if self.env._trace:
            self.env.print_trace(
                '', '', self.name() + ' create',
                'value= ' + str(self._value))
        self.setup(*args, **kwargs)

    def setup(self):
        '''
        called immediately after initialization of a state.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments will be passed
        '''
        pass

    def register(self, registry):
        '''
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
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self in registry:
            raise SalabimError(self.name() + ' already in registry')
        registry.append(self)
        return self

    def deregister(self, registry):
        '''
        deregisters the state in the registry

        Parameters
        ----------
        registry : list
            list of registered states

        Returns
        -------
        state (self) : State
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self not in registry:
            raise SalabimError(self.name() + ' not in registry')
        registry.remove(self)
        return self

    def __repr__(self):
        return objectclass_to_str(self) + ' (' + self.name() + ')'

    def print_histograms(self, exclude=(), as_str=False, file=None):
        '''
        print histograms of the waiters queue and the value timestamped monitor

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
        '''
        result = []
        if self.waiters() not in exclude:
            result.append(self.waiters().print_histograms(exclude=exclude, as_str=True))
        if self.value not in exclude:
            result.append(self.value.print_histogram(as_str=True))
        return return_or_print(result, as_str, file)

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append(objectclass_to_str(self) + ' ' + hex(id(self)))
        result.append('  name=' + self.name())
        result.append('  value=' + str(self._value))
        if self._waiters:
            result.append('  waiting component(s):')
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

                result.append('    ' + pad(c.name(), 20), ' value(s): ' + values)
        else:
            result.append('  no waiting components')
        return return_or_print(result, as_str, file)

    def __call__(self):
        return self._value

    def get(self):
        '''
        get value of the state

        Returns
        -------
        value of the state : any
            Instead of this method, the state can also be called directly, like |n|

            level = sim.State('level') |n|
            ... |n|
            print(level()) |n|
            print(level.get())  # identical |n|
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
        if self.env._trace:
            self.env.print_trace('', '', self.name() + ' set', 'value = ' + str(value))
        if self._value != value:
            self._value = value
            self.value.tally(value)
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
        if self.env._trace:
            self.env.print_trace('', '', self.name() + ' reset', 'value = ' + str(value))
        if self._value != value:
            self._value = value
            self.value.tally(value)
            self._trywait()

    def trigger(self, value=True, value_after=None, max=inf):
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
        if value_after is None:
            value_after = self._value
        if self.env._trace:
            self.env.print_trace('', '', self.name() + ' trigger',
                ' value = ' + str(value) + ' --> ' + str(value_after) +
                ' allow ' + str(max) + ' components')
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
        self.waiters().monitor(value)
        self.value.monitor(value)

    def reset_monitors(self, monitor=None):
        '''
        resets the timestamped monitor for the state's value and the monitors of the waiters queue

        Parameters
        ----------
        monitor : bool
            if True, monitoring will be on. |n|
            if False, monitoring is disabled |n|
            if omitted, no change of monitoring state

        '''
        self._waiters.reset_monitors(monitor)
        self.value.reset()

    def _get_value(self):
        return self._value

    def name(self, value=None):
        '''
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
        '''
        if value is not None:
            self._name = value
            self._waiters.name('waiters of ' + value)
            self.value.name('Value of ' + value)

        return self._name

    def base_name(self):
        '''
        Returns
        -------
        base name of the state (the name used at initialization): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the state : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        '''
        return self._sequence_number

    def print_statistics(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Statistics of {} at {}'.format(self.name(), fn(self.env._now - self.env._offset, 13, 3)))
        result.append(
            self.waiters().length.print_statistics(show_header=False, show_legend=True, do_indent=True, as_str=True))
        result.append('')
        result.append(
            self.waiters().length_of_stay.print_statistics(show_header=False, show_legend=False, do_indent=True,
            as_str=True))
        result.append('')
        result.append(self.value.print_statistics(show_header=False, show_legend=False, do_indent=True, as_str=True))
        return return_or_print(result, as_str, file)

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
        if the name end with a comma,
        auto serializing starting at 1 will be applied |n|
        if omitted, the name will be derived from the class
        it is defined in (lowercased)

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
        if omitted, default_env is used
    '''

    def __init__(self, name=None, capacity=1,
                 anonymous=False, monitor=True, env=None, *args, **kwargs):
        if env is None:
            self.env = g.default_env
        else:
            self.env = env
        self._capacity = capacity
        _set_name(name, self.env._nameserializeResource, self)
        savetrace = self.env._trace
        self.env._trace = False
        self._requesters = Queue(
            name='requesters of ' + self.name(),
            monitor=monitor, env=self.env)
        self._requesters._isinternal = True
        self._claimers = Queue(
            name='claimers of ' + self.name(),
            monitor=monitor, env=self.env)
        self._claimers._isinternal = True
        self.env._trace = savetrace
        self._claimed_quantity = 0
        self._anonymous = anonymous
        self._minq = inf
        self.capacity = MonitorTimestamp(
            'Capacity of ' + self.name(),
            initial_tally=capacity, monitor=monitor, type='float', env=self.env)
        self.claimed_quantity = MonitorTimestamp(
            'Claimed quantity of ' + self.name(),
            initial_tally=0, monitor=monitor, type='float', env=self.env)
        self.available_quantity = MonitorTimestamp(
            'Available quantity of ' + self.name(),
            initial_tally=capacity, monitor=monitor, type='float', env=self.env)
        self.occupancy = MonitorTimestamp(
            'Occupancy of ' + self.name(),
            initial_tally=0, monitor=monitor, type='float', env=self.env)
        if self.env._trace:
            self.env.print_trace(
                '', '', self.name() + ' create',
                'capacity=' + str(self._capacity) + (' anonymous' if self._anonymous else ''))
        self.setup(*args, **kwargs)

    def setup(self):
        '''
        called immediately after initialization of a resource.

        by default this is a dummy method, but it can be overridden.

        only keyword arguments are passed
        '''
        pass

    def reset_monitors(self, monitor=None):
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
            claimed_quantity.reset() or
            occupancy.reset()
        '''

        self.requesters().reset_monitors(monitor)
        self.claimers().reset_monitors(monitor)
        for m in (self.capacity, self.available_quantity, self.claimed_quantity, self.occupancy):
            m.reset(monitor)

    def print_statistics(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append('Statistics of {} at {:13.3f}'.format(self.name(), self.env._now - self.env._offset))
        show_legend = True
        for q in [self.requesters(), self.claimers()]:
            result.append(
                q.length.print_statistics(show_header=False, show_legend=show_legend, do_indent=True, as_str=True))
            show_legend = False
            result.append('')
            result.append(
                q.length_of_stay.print_statistics(
                    show_header=False, show_legend=show_legend, do_indent=True, as_str=True))
            result.append('')

        for m in (self.capacity, self.available_quantity, self.claimed_quantity, self.occupancy):
            result.append(m.print_statistics(show_header=False, show_legend=show_legend, do_indent=True, as_str=True))
            result.append('')
        return return_or_print(result, as_str, file)

    def print_histograms(self, exclude=(), as_str=False, file=None):
        '''
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
        '''
        result = []
        for q in (self.requesters(), self.claimers()):
            if q not in exclude:
                result.append(q.print_histograms(exclude=exclude, as_str=True))
        for m in (self.capacity, self.available_quantity, self.claimed_quantity):
            if m not in exclude:
                result.append(m.print_histogram(as_str=True))
        return return_or_print(result, as_str, file)

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
        and requesters().monitor(), capacity.monitor(), available_quantity.monitor),
        claimed_quantity.monitor() or occupancy.monitor()
        '''
        self.requesters().monitor(value)
        self.claimers().monitor(value)
        for m in (self.capacity, self.available_quantity, self.claimed_quantity, self.occupancy):
            m.monitor(value)

    def register(self, registry):
        '''
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
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self in registry:
            raise SalabimError(self.name() + ' already in registry')
        registry.append(self)
        return self

    def deregister(self, registry):
        '''
        deregisters the resource in the registry

        Parameters
        ----------
        registry : list
            list of registered components

        Returns
        -------
        resource (self) : Resource
        '''
        if not isinstance(registry, list):
            raise SalabimError('registry not list')
        if self not in registry:
            raise SalabimError(self.name() + ' not in registry')
        registry.remove(self)
        return self

    def __repr__(self):
        return objectclass_to_str(self) + ' (' + self.name() + ')'

    def print_info(self, as_str=False, file=None):
        '''
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
        '''
        result = []
        result.append(objectclass_to_str(self) + ' ' + hex(id(self)))
        result.append('  name=' + self.name())
        result.append('  capacity=' + str(self._capacity))
        if self._requesters:
            result.append('  requesting component(s):')
            mx = self._requesters._head.successor
            while mx != self._requesters._tail:
                c = mx.component
                mx = mx.successor
                result.append('    ' + pad(c.name(), 20) +
                    ' quantity=' + str(c._requests[self]))
        else:
            result.append('  no requesting components')

        result.append('  claimed_quantity=' + str(self._claimed_quantity))
        if self._claimed_quantity >= 0:
            if self._anonymous:
                result.append('  not claimed by any components,' +
                    ' because the resource is anonymous')
            else:
                result.append('  claimed by:')
                mx = self._claimers._head.successor
                while mx != self._claimers._tail:
                    c = mx.component
                    mx = mx.successor
                    result.append('    ' + pad(c.name(), 20) +
                        ' quantity=' + str(c._claims[self]))
        return return_or_print(result, as_str, file)

    def _tryrequest(self):
        mx = self._requesters._head.successor
        while mx != self._requesters._tail:
            if self._minq > (self._capacity - self._claimed_quantity + 1e-8):
                break  # inpossible to honor any more requests
            c = mx.component
            mx = mx.successor
            c._tryrequest()

    def release(self, quantity=None):
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
        self.capacity.tally(self._capacity)
        self.available_quantity.tally(self._capacity - self._claimed_quantity)
        self.occupancy.tally(0 if self._capacity <= 0 else self._claimed_quantity / self._capacity)
        self._tryrequest()

    def name(self, value=None):
        '''
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
        '''
        if value is not None:
            self._name = value
            self._requesters.name('requesters of ' + value)
            self._claimers.name('claimers of ' + value)
            self.capacity.name('Capacity of ' + value)
            self.claimed_quantity.name('Clamed quantity of ' + value)
            self.available_quantity.name('Available quantity of ' + value)
            self.occupancy.name('Occupancy of ' + value)

        return self._name

    def base_name(self):
        '''
        Returns
        -------
        base name of the resource (the name used at initialization): str
        '''
        return self._base_name

    def sequence_number(self):
        '''
        Returns
        -------
        sequence_number of the resource : int
            (the sequence number at initialization) |n|
            normally this will be the integer value of a serialized name,
            but also non serialized names (without a dot or a comma at the end)
            will be numbered)
        '''
        return self._sequence_number


class _PeriodComponent(Component):
    def setup(self, pm):
        self.pm = pm

    def process(self):
        for iperiod, duration in itertools.cycle(enumerate(self.pm.periods)):
            self.pm.perperiod[self.pm.iperiod].monitor(False)
            self.pm.iperiod = iperiod
            if self.pm.m._timestamp:
                self.pm.perperiod[self.pm.iperiod].tally(self.pm.m())
            self.pm.perperiod[self.pm.iperiod].monitor(True)
            yield self.hold(duration)


class PeriodMonitor(object):
    '''
    defines a number of (timestamped) period monitors for a given monitor.

    Parameters
    ----------
    patent_monitor : Monitor.monitor or MonitorTimestamp.monitor 
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
    '''

    @staticmethod
    def new_tally(self, x):
        for m in self.period_monitors:
            m.perperiod[m.iperiod].tally(x)
        self.org_tally(x)

    @staticmethod
    def new_reset(self, monitor=None):
        for m in self.period_monitors:
            for iperiod in range(len(m.periods)):
                m.perperiod[iperiod].reset()
        self.org_reset(monitor=monitor)

    def __getitem__(self, i):
        return self.perperiod[i]
        
    def remove(self):
        '''
        removes the period monitor
        '''
        self.pc.cancel()
        del(self.periods)
        self.m.period_monitors.remove(self)

    def __init__(self, parent_monitor, periods=None, period_monitor_names=None):
        self.pc = _PeriodComponent(pm=self, skip_standby=True, suppress_trace=True)
        if periods is None:
            periods = 24 * [1]
        self.periods = periods
        cum = 0
        if period_monitor_names is None:
            period_monitor_names = []
            for duration in periods:
                period_monitor_names.append(
                    parent_monitor.name() + '.period [' + str(cum) + ' - ' + str(cum + duration) + ']')
                cum += duration

        self.m = parent_monitor
        if not hasattr(self, 'period_monitors'):
            self.m.period_monitors = []
            self.m.org_tally = self.m.tally
            self.m.tally = types.MethodType(self.new_tally, self.m)
            self.m.org_reset = self.m.reset
            self.m.reset = types.MethodType(self.new_reset, self.m)
            self.m.period_monitors.append(self)

        self.iperiod = 0
        if self.m._timestamp:
            self.perperiod = [MonitorTimestamp(
                name=period_monitor_name, monitor=False) for period_monitor_name in period_monitor_names]
        else:
            self.perperiod = [Monitor(
                name=period_monitor_name, monitor=False) for period_monitor_name in period_monitor_names]


def colornames():
    '''
    available colornames

    Returns
    -------
    dict with name of color as key, #rrggbb or #rrggbbaa as value : dict
    '''
    if not hasattr(colornames, 'cached'):
        colornames.cached = pickle.loads(b'(dp0\nVfuchsia\np1\nV#FF00FF\np2\nsV\np3\nV#00000000\np4\nsVtransparent\np5\ng4\nsVpalevioletred\np6\nV#DB7093\np7\nsVskyblue\np8\nV#87CEEB\np9\nsVpaleturquoise\np10\nV#AFEEEE\np11\nsVcadetblue\np12\nV#5F9EA0\np13\nsVorangered\np14\nV#FF4500\np15\nsVsteelblue\np16\nV#4682B4\np17\nsVdimgray\np18\nV#696969\np19\nsVdarkseagreen\np20\nV#8FBC8F\np21\nsV60%gray\np22\nV#999999\np23\nsVroyalblue\np24\nV#4169E1\np25\nsVmediumblue\np26\nV#0000CD\np27\nsVgoldenrod\np28\nV#DAA520\np29\nsVmediumvioletred\np30\nV#C71585\np31\nsVblueviolet\np32\nV#8A2BE2\np33\nsVgainsboro\np34\nV#DCDCDC\np35\nsVdarkred\np36\nV#8B0000\np37\nsVrosybrown\np38\nV#BC8F8F\np39\nsVgold\np40\nV#FFD700\np41\nsVcoral\np42\nV#FF7F50\np43\nsVwhite\np44\nV#FFFFFF\np45\nsVdarkcyan\np46\nV#008B8B\np47\nsVblack\np48\nV#000000\np49\nsVorchid\np50\nV#DA70D6\np51\nsVmediumturquoise\np52\nV#48D1CC\np53\nsVlightgreen\np54\nV#90EE90\np55\nsVlime\np56\nV#00FF00\np57\nsVpapayawhip\np58\nV#FFEFD5\np59\nsVchocolate\np60\nV#D2691E\np61\nsV40%gray\np62\nV#666666\np63\nsVoldlace\np64\nV#FDF5E6\np65\nsVdarkblue\np66\nV#00008B\np67\nsVsilver\np68\nV#C0C0C0\np69\nsVaquamarine\np70\nV#7FFFD4\np71\nsVlightcoral\np72\nV#F08080\np73\nsVcyan\np74\nV#00FFFF\np75\nsVdodgerblue\np76\nV#1E90FF\np77\nsV10%gray\np78\nV#191919\np79\nsVmidnightblue\np80\nV#191970\np81\nsVgreen\np82\nV#008000\np83\nsVlightsalmon\np84\nV#FFA07A\np85\nsVazure\np86\nV#F0FFFF\np87\nsVred\np88\nV#FF0000\np89\nsVlightpink\np90\nV#FFB6C1\np91\nsVwhitesmoke\np92\nV#F5F5F5\np93\nsVyellow\np94\nV#FFFF00\np95\nsVlawngreen\np96\nV#7CFC00\np97\nsVmagenta\np98\ng2\nsVlightsteelblue\np99\nV#B0C4DE\np100\nsVolivedrab\np101\nV#6B8E23\np102\nsVlightslategray\np103\nV#778899\np104\nsVslategray\np105\nV#708090\np106\nsVlightblue\np107\nV#ADD8E6\np108\nsVmoccasin\np109\nV#FFE4B5\np110\nsVmediumspringgreen\np111\nV#00FA9A\np112\nsVlightgray\np113\nV#D3D3D3\np114\nsVseashell\np115\nV#FFF5EE\np116\nsVdarkkhaki\np117\nV#BDB76B\np118\nsVslateblue\np119\nV#6A5ACD\np120\nsVaqua\np121\ng75\nsVpalegoldenrod\np122\nV#EEE8AA\np123\nsVdeeppink\np124\nV#FF1493\np125\nsVdarkgreen\np126\nV#006400\np127\nsVblanchedalmond\np128\nV#FFEBCD\np129\nsVturquoise\np130\nV#40E0D0\np131\nsVnavy\np132\nV#000080\np133\nsVtomato\np134\nV#FF6347\np135\nsVyellowgreen\np136\nV#9ACD32\np137\nsVpeachpuff\np138\nV#FFDAB9\np139\nsV30%gray\np140\nV#464646\np141\nsVpink\np142\nV#FFC0CB\np143\nsVpalegreen\np144\nV#98FB98\np145\nsVlightskyblue\np146\nV#87CEFA\np147\nsVchartreuse\np148\nV#7FFF00\np149\nsVmediumorchid\np150\nV#BA55D3\np151\nsVolive\np152\nV#808000\np153\nsVdarkorange\np154\nV#FF8C00\np155\nsVbeige\np156\nV#F5F5DC\np157\nsVforestgreen\np158\nV#228B22\np159\nsVmediumpurple\np160\nV#9370DB\np161\nsVmintcream\np162\nV#F5FFFA\np163\nsVhotpink\np164\nV#FF69B4\np165\nsVdarkgoldenrod\np166\nV#B8860B\np167\nsVpowderblue\np168\nV#B0E0E6\np169\nsVhoneydew\np170\nV#F0FFF0\np171\nsVsalmon\np172\nV#FA8072\np173\nsVsnow\np174\nV#FFFAFA\np175\nsVmistyrose\np176\nV#FFE4E1\np177\nsVkhaki\np178\nV#F0E68C\np179\nsVmediumaquamarine\np180\nV#66CDAA\np181\nsVdarksalmon\np182\nV#E9967A\np183\nsValiceblue\np184\nV#F0F8FF\np185\nsVdarkturquoise\np186\nV#00CED1\np187\nsVlightyellow\np188\nV#FFFFE0\np189\nsVwheat\np190\nV#F5DEB3\np191\nsVlightseagreen\np192\nV#20B2AA\np193\nsVlightcyan\np194\nV#E0FFFF\np195\nsVantiquewhite\np196\nV#FAEBD7\np197\nsVsaddlebrown\np198\nV#8B4513\np199\nsVmediumseagreen\np200\nV#3CB371\np201\nsV70%gray\np202\nV#B2B2B2\np203\nsVsienna\np204\nV#A0522D\np205\nsVcornflowerblue\np206\nV#6495ED\np207\nsVseagreen\np208\nV#2E8B57\np209\nsVfloralwhite\np210\nV#FFFAF0\np211\nsVivory\np212\nV#FFFFF0\np213\nsVcornsilk\np214\nV#FFF8DC\np215\nsVindianred\np216\nV#CD5C5C\np217\nsVplum\np218\nV#DDA0DD\np219\nsV90%gray\np220\nV#E6E6E6\np221\nsVgreenyellow\np222\nV#ADFF2F\np223\nsVteal\np224\nV#008080\np225\nsVbrown\np226\nV#A52A2A\np227\nsVdarkslategray\np228\nV#2F4F4F\np229\nsVpurple\np230\nV#800080\np231\nsVviolet\np232\nV#EE82EE\np233\nsVdeepskyblue\np234\nV#00BFFF\np235\nsVghostwhite\np236\nV#F8F8FF\np237\nsVburlywood\np238\nV#DEB887\np239\nsVblue\np240\nV#0000FF\np241\nsVcrimson\np242\nV#DC143C\np243\nsVindigo\np244\nV#4B0082\np245\nsV20%gray\np246\nV#333333\np247\nsVdarkmagenta\np248\nV#8B008B\np249\nsV80%gray\np250\nV#CCCCCC\np251\nsVlightgoldenrodyellow\np252\nV#FAFAD2\np253\nsVtan\np254\nV#D2B48C\np255\nsVlimegreen\np256\nV#32CD32\np257\nsVlemonchiffon\np258\nV#FFFACD\np259\nsVbisque\np260\nV#FFE4C4\np261\nsVfirebrick\np262\nV#B22222\np263\nsVnavajowhite\np264\nV#FFDEAD\np265\nsVnone\np266\ng4\nsVmaroon\np267\nV#800000\np268\nsV50%gray\np269\nV#7F7F7F\np270\nsVdarkgray\np271\nV#A9A9A9\np272\nsVorange\np273\nV#FFA500\np274\nsVlavenderblush\np275\nV#FFF0F5\np276\nsVdarkorchid\np277\nV#9932CC\np278\nsVlavender\np279\nV#E6E6FA\np280\nsVspringgreen\np281\nV#00FF7F\np282\nsVthistle\np283\nV#D8BFD8\np284\nsVlinen\np285\nV#FAF0E6\np286\nsVdarkolivegreen\np287\nV#556B2F\np288\nsVdarkslateblue\np289\nV#483D8B\np290\nsVgray\np291\nV#808080\np292\nsVdarkviolet\np293\nV#9400D3\np294\nsVperu\np295\nV#CD853F\np296\nsVsandybrown\np297\nV#FAA460\np298\nsVmediumslateblue\np299\nV#7B68EE\np300\ns.')  # NOQA
    return colornames.cached


def salabim_logo_red_white_200():
    #  picture created from salabim logo red white 200.png
    from PIL import Image
    import io
    import base64
    if not hasattr(salabim_logo_red_white_200, 'cached'):
        salabim_logo_red_white_200.cached = Image.open(io.BytesIO(base64.b64decode(''
           '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'  # NOQA
           ''.encode('ascii')))).convert('RGBA')
    return salabim_logo_red_white_200.cached


def salabim_logo_red_black_200():
    #  picture created from salabim logo red black 200.png
    from PIL import Image
    import io
    import base64
    if not hasattr(salabim_logo_red_black_200, 'cached'):
        salabim_logo_red_black_200.cached = Image.open(io.BytesIO(base64.b64decode(''
           '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'  # NOQA
           ''.encode('ascii')))).convert('RGBA')
    return salabim_logo_red_black_200.cached


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


def spec_to_image(spec):
    '''
    convert an image specification to an image

    Parameters
    ----------
    image : str or PIL.Image.Image
        if str: filename of file to be loaded |n|
        if '': dummy image will be returned |n|
        if PIL.Image.Image: return this image untranslated

    Returns
    -------
    image : PIL.Image.Image
    '''
    if isinstance(spec, str):
        if can_animate(try_only=True):
            if spec == '':
                im = Image.new('RGBA', (0, 0), (0, 0, 0, 0))
            else:
                im = Image.open(spec)
                im = im.convert('RGBA')
            return im
        else:
            return None  # will never be used!
    else:
        return spec


def _i(p, v0, v1):
    if v0 == v1:
        return v0  # avoid rounding problems
    if (v0 is None) or (v1 is None):
        return None
    return (1 - p) * v0 + p * v1


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
    linear interpolation between v0 and v1 based on t between t0 and t1 : float or tuple

    Note
    ----
    Note that no extrapolation is done, so if t<t0 ==> v0  and t>t1 ==> v1 |n|
    This function is heavily used during animation.
    '''
    if v0 == v1:
        return v0

    if t1 == inf:
        return v0
    if t0 == t1:
        return v1
    if t0 > t1:
        (t0, t1) = (t1, t0)
        (v0, v1) = (v1, v0)
    if t <= t0:
        return v0
    if t >= t1:
        return v1
    p = (0.0 + t - t0) / (t1 - t0)
    if isinstance(v0, (list, tuple)):
        return tuple((_i(p, x0, x1) for x0, x1 in zip(v0, v1)))
    else:
        return _i(p, v0, v1)


def _set_name(name, _nameserialize, object):
    if name is None:
        name = objectclass_to_str(object).lower() + '.'
    elif len(name) <= 1:
        if name == '':
            name = objectclass_to_str(object).lower()
        elif name == '.':
            name = objectclass_to_str(object).lower() + '.'
        elif name == ',':
            name = objectclass_to_str(object).lower() + ','

    object._base_name = name

    if name in _nameserialize:
        sequence_number = _nameserialize[name] + 1
        _nameserialize[name] = sequence_number

    else:
        if name.endswith(','):
            _nameserialize[name] = 1
            sequence_number = 1
        else:
            _nameserialize[name] = 0
            sequence_number = 0

    if name.endswith('.'):
        object._name = name + str(sequence_number)
    elif name.endswith(','):
        object._name = name[:-1] + '.' + str(sequence_number)
    else:
        object._name = name
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


def _checkrandomstream(randomstream):
    if not isinstance(randomstream, random.Random):
        raise SalabimError('Type randomstream or random.Random expected, got ' + str(type(randomstream)))


def _checkismonitor(monitor):
    if not isinstance(monitor, Monitor):
        raise SalabimError('Type Monitor or MonitorTimestamp expected, got ' + str(type(monitor)))


def _checkisqueue(queue):
    if not isinstance(queue, Queue):
        raise SalabimError('Type Queue expected, got ' + str(type(queue)))


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
    for v in l:
        try:
            vfloat = float(v)
        except:
            vfloat = 0
        float_result.append(vfloat)

    return float_result


def deep_flatten(l):

    if hasattr(l, '__iter__') and not isinstance(l, str):
        for x in l:
            #  the two following lines are equivalent to 'yield from deep_flatten(x)' (not supported in Python 2.7)
            for xx in deep_flatten(x):
                yield xx
    else:
        yield l


def merge_blanks(*l):
    '''
    merges all non blank elements of l, separated by a blank

    Parameters
    ----------
    *l : elements to be merged : str

    Returns
    -------
    string with merged elements of l : str
    '''
    return ' '.join(x for x in l if x)


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
        return '!'
    else:
        return ' '


def _modetxt(mode):
    if mode is None:
        return ''
    else:
        return 'mode=' + str(mode)


def objectclass_to_str(object):
    return str(type(object)).split('.')[-1].split("'")[0]


def _get_caller_frame():
    stack = inspect.stack()
    filename0 = inspect.getframeinfo(stack[0][0]).filename
    for i in range(len(inspect.stack())):
        frame = stack[i][0]
        if filename0 != inspect.getframeinfo(frame).filename:
            break
    return frame


def return_or_print(result, as_str, file):
    result = '\n'.join(result)
    if as_str:
        return result
    else:
        if file is None:
            print(result)
        else:
            print(result, file=file)


def _call(c, t, self):
    '''
    special function to support scalars, methods (with one parameter) and function with zero, one or two parameters
    '''
    if inspect.isfunction(c):
        nargs = c.__code__.co_argcount
        if nargs == 0:
            return c()
        elif nargs == 1:
            return c(t)
        else:
            return c(self, t)
    if inspect.ismethod(c):
        return c(t)
    return c


def de_none(l):
    if l is None:
        return None
    result = []
    for index, item in enumerate(l):
        if item is None:
            result.append(l[index - 2])
        else:
            result.append(item)
    return result


def data():
    return 'data'


def current():
    return 'current'


def standby():
    return 'standby'


def passive():
    return 'passive'


def interrupted():
    return 'interrupted'


def scheduled():
    return 'scheduled'


def requesting():
    return 'requesting'


def waiting():
    return 'waiting'


def random_seed(seed, randomstream=None):
    '''
    Reseeds a randomstream

    Parameters
    ----------
    seed : hashable object, usually int
        the seed for random, equivalent to random.seed() |n|
        if None or '*', a purely random value (based on the current time) will be used
        (not reproducable) |n|

    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
    '''
    if randomstream is None:
        randomstream = random
    if seed == '*':
        seed = None
    randomstream.seed(seed)


def _std_fonts():
    # the names of the standard fonts are generated by ttf fontdict.py on the standard development machine
    if not hasattr(_std_fonts, 'cached'):
        _std_fonts.cached = pickle.loads(b'(dp0\nVHuxley_Titling\np1\nVHuxley Titling\np2\nsVGlock___\np3\nVGlockenspiel\np4\nsVPENLIIT_\np5\nVPenultimateLightItal\np6\nsVERASMD\np7\nVEras Medium ITC\np8\nsVNirmala\np9\nVNirmala UI\np10\nsVebrimabd\np11\nVEbrima Bold\np12\nsVostrich-dashed\np13\nVOstrich Sans Dashed Medium\np14\nsVLato-Hairline\np15\nVLato Hairline\np16\nsVLTYPEO\np17\nVLucida Sans Typewriter Oblique\np18\nsVbnmachine\np19\nVBN Machine\np20\nsVLTYPEB\np21\nVLucida Sans Typewriter Bold\np22\nsVBOOKOSI\np23\nVBookman Old Style Italic\np24\nsVEmmett__\np25\nVEmmett\np26\nsVCURLZ___\np27\nVCurlz MT\np28\nsVhandmeds\np29\nVHand Me Down S (BRK)\np30\nsVsegoesc\np31\nVSegoe Script\np32\nsVTCM_____\np33\nVTw Cen MT\np34\nsVJosefinSlab-ThinItalic\np35\nVJosefin Slab Thin Italic\np36\nsVSTENCIL\np37\nVStencil\np38\nsVsanss___\np39\nVSansSerif\np40\nsVBOD_CI\np41\nVBodoni MT Condensed Italic\np42\nsVGreek_i\np43\nVGreek Diner Inline TT\np44\nsVHTOWERT\np45\nVHigh Tower Text\np46\nsVTCCB____\np47\nVTw Cen MT Condensed Bold\np48\nsVCools___\np49\nVCoolsville\np50\nsVbnjinx\np51\nVBN Jinx\np52\nsVFREESCPT\np53\nVFreestyle Script\np54\nsVGARA\np55\nVGaramond\np56\nsVDejaVuSansMono\np57\nVDejaVu Sans Mono Book\np58\nsVCALVIN__\np59\nVCalvin\np60\nsVGIL_____\np61\nVGill Sans MT\np62\nsVCandaraz\np63\nVCandara Bold Italic\np64\nsVVollkorn-Bold\np65\nVVollkorn Bold\np66\nsVariblk\np67\nVArial Black\np68\nsVGOTHIC\np69\nVCentury Gothic\np70\nsVMAIAN\np71\nVMaiandra GD\np72\nsVBSSYM7\np73\nVBookshelf Symbol 7\np74\nsVAcme____\np75\nVAcmeFont\np76\nsVDetente_\np77\nVDetente\np78\nsVCandarai\np79\nVCandara Italic\np80\nsVFTLTLT\np81\nVFootlight MT Light\np82\nsVGILC____\np83\nVGill Sans MT Condensed\np84\nsVLFAXD\np85\nVLucida Fax Demibold\np86\nsVNIAGSOL\np87\nVNiagara Solid\np88\nsVLFAXI\np89\nVLucida Fax Italic\np90\nsVCandarab\np91\nVCandara Bold\np92\nsVFRSCRIPT\np93\nVFrench Script MT\np94\nsVLBRITE\np95\nVLucida Bright\np96\nsVFRABK\np97\nVFranklin Gothic Book\np98\nsVostrich-bold\np99\nVOstrich Sans Bold\np100\nsVTCCM____\np101\nVTw Cen MT Condensed\np102\nsVcorbelz\np103\nVCorbel Bold Italic\np104\nsVTCMI____\np105\nVTw Cen MT Italic\np106\nsVethnocen\np107\nVEthnocentric\np108\nsVVINERITC\np109\nVViner Hand ITC\np110\nsVROCKB\np111\nVRockwell Bold\np112\nsVconsola\np113\nVConsolas\np114\nsVcorbeli\np115\nVCorbel Italic\np116\nsVPENUL___\np117\nVPenultimate\np118\nsVMAGNETOB\np119\nVMagneto Bold\np120\nsVisocp___\np121\nVISOCP\np122\nsVQUIVEIT_\np123\nVQuiverItal\np124\nsVARLRDBD\np125\nVArial Rounded MT Bold\np126\nsVJosefinSlab-SemiBold\np127\nVJosefin Slab SemiBold\np128\nsVntailub\np129\nVMicrosoft New Tai Lue Bold\np130\nsVflubber\np131\nVFlubber\np132\nsVBASKVILL\np133\nVBaskerville Old Face\np134\nsVGILB____\np135\nVGill Sans MT Bold\np136\nsVPERTILI\np137\nVPerpetua Titling MT Light\np138\nsVLato-HairlineItalic\np139\nVLato Hairline Italic\np140\nsVComfortaa-Light\np141\nVComfortaa Light\np142\nsVtrebucit\np143\nVTrebuchet MS Italic\np144\nsVmalgunbd\np145\nVMalgun Gothic Bold\np146\nsVITCBLKAD\np147\nVBlackadder ITC\np148\nsVsansso__\np149\nVSansSerif Oblique\np150\nsVCALISTBI\np151\nVCalisto MT Bold Italic\np152\nsVsyastro_\np153\nVSyastro\np154\nsVSamsungIF_Md\np155\nVSamsung InterFace Medium\np156\nsVHombre__\np157\nVHombre\np158\nsVseguiemj\np159\nVSegoe UI Emoji\np160\nsVFRAHVIT\np161\nVFranklin Gothic Heavy Italic\np162\nsVJUICE___\np163\nVJuice ITC\np164\nsVFRAMDCN\np165\nVFranklin Gothic Medium Cond\np166\nsVseguisb\np167\nVSegoe UI Semibold\np168\nsVconsolai\np169\nVConsolas Italic\np170\nsVGLECB\np171\nVGloucester MT Extra Condensed\np172\nsVframd\np173\nVFranklin Gothic Medium\np174\nsVSCHLBKI\np175\nVCentury Schoolbook Italic\np176\nsVCENTAUR\np177\nVCentaur\np178\nsVromantic\np179\nVRomantic\np180\nsVBOD_CB\np181\nVBodoni MT Condensed Bold\np182\nsVverdana\np183\nVVerdana\np184\nsVTangerine_Regular\np185\nVTangerine\np186\nsVseguili\np187\nVSegoe UI Light Italic\np188\nsVNunito-Regular\np189\nVNunito\np190\nsVSCHLBKB\np191\nVCentury Schoolbook Bold\np192\nsVGOTHICB\np193\nVCentury Gothic Bold\np194\nsVpalai\np195\nVPalatino Linotype Italic\np196\nsVBKANT\np197\nVBook Antiqua\np198\nsVLato-Italic\np199\nVLato Italic\np200\nsVPERBI___\np201\nVPerpetua Bold Italic\np202\nsVGOTHICI\np203\nVCentury Gothic Italic\np204\nsVROCKBI\np205\nVRockwell Bold Italic\np206\nsVLTYPEBO\np207\nVLucida Sans Typewriter Bold Oblique\np208\nsVAmeth___\np209\nVAmethyst\np210\nsVyearsupplyoffairycakes\np211\nVYear supply of fairy cakes\np212\nsVGILBI___\np213\nVGill Sans MT Bold Italic\np214\nsVBOOKOS\np215\nVBookman Old Style\np216\nsVVollkorn-Italic\np217\nVVollkorn Italic\np218\nsVswiss\np219\nVSwis721 BT Roman\np220\nsVcomsc\np221\nVCommercialScript BT\np222\nsVchinyen\np223\nVChinyen Normal\np224\nsVeurr____\np225\nVEuroRoman\np226\nsVROCK\np227\nVRockwell\np228\nsVPERTIBD\np229\nVPerpetua Titling MT Bold\np230\nsVCHILLER\np231\nVChiller\np232\nsVtechb___\np233\nVTechnicBold\np234\nsVLato-Light\np235\nVLato Light\np236\nsVOUTLOOK\np237\nVMS Outlook\np238\nsVmtproxy6\np239\nVProxy 6\np240\nsVdutcheb\np241\nVDutch801 XBd BT Extra Bold\np242\nsVgadugib\np243\nVGadugi Bold\np244\nsVBOD_CR\np245\nVBodoni MT Condensed\np246\nsVmtproxy7\np247\nVProxy 7\np248\nsVnobile_bold\np249\nVNobile Bold\np250\nsVELEPHNT\np251\nVElephant\np252\nsVCOPRGTL\np253\nVCopperplate Gothic Light\np254\nsVMTCORSVA\np255\nVMonotype Corsiva\np256\nsVconsolaz\np257\nVConsolas Bold Italic\np258\nsVBOOKOSBI\np259\nVBookman Old Style Bold Italic\np260\nsVtrebuc\np261\nVTrebuchet MS\np262\nsVcomici\np263\nVComic Sans MS Italic\np264\nsVJosefinSlab-BoldItalic\np265\nVJosefin Slab Bold Italic\np266\nsVMycalc__\np267\nVMycalc\np268\nsVmarlett\np269\nVMarlett\np270\nsVsymeteo_\np271\nVSymeteo\np272\nsVcandles_\np273\nVCandles\np274\nsVbobcat\np275\nVBobcat Normal\np276\nsVLSANSDI\np277\nVLucida Sans Demibold Italic\np278\nsVINFROMAN\np279\nVInformal Roman\np280\nsVsf movie poster2\np281\nVSF Movie Poster\np282\nsVcomicz\np283\nVComic Sans MS Bold Italic\np284\nsVcracj___\np285\nVCracked Johnnie\np286\nsVcourbd\np287\nVCourier New Bold\np288\nsVItali___\np289\nVItalianate\np290\nsVITCEDSCR\np291\nVEdwardian Script ITC\np292\nsVcourbi\np293\nVCourier New Bold Italic\np294\nsVcalibrili\np295\nVCalibri Light Italic\np296\nsVgazzarelli\np297\nVGazzarelli\np298\nsVGabriola\np299\nVGabriola\np300\nsVVollkorn-BoldItalic\np301\nVVollkorn Bold Italic\np302\nsVromant__\np303\nVRomanT\np304\nsVisoct3__\np305\nVISOCT3\np306\nsVsegoeuib\np307\nVSegoe UI Bold\np308\nsVtimesbd\np309\nVTimes New Roman Bold\np310\nsVgoodtime\np311\nVGood Times\np312\nsVsegoeuii\np313\nVSegoe UI Italic\np314\nsVBOD_BLAR\np315\nVBodoni MT Black\np316\nsVhimalaya\np317\nVMicrosoft Himalaya\np318\nsVsegoeuil\np319\nVSegoe UI Light\np320\nsVPermanentMarker\np321\nVPermanent Marker\np322\nsVBOD_BLAI\np323\nVBodoni MT Black Italic\np324\nsVTCBI____\np325\nVTw Cen MT Bold Italic\np326\nsVarial\np327\nVArial\np328\nsVBrand___\np329\nVBrandish\np330\nsVsegoeuiz\np331\nVSegoe UI Bold Italic\np332\nsVswisscb\np333\nVSwis721 Cn BT Bold\np334\nsVPAPYRUS\np335\nVPapyrus\np336\nsVANTIC___\np337\nVAnticFont\np338\nsVGIGI\np339\nVGigi\np340\nsVENGR\np341\nVEngravers MT\np342\nsVsegmdl2\np343\nVSegoe MDL2 Assets\np344\nsVBRLNSDB\np345\nVBerlin Sans FB Demi Bold\np346\nsVLato-BoldItalic\np347\nVLato Bold Italic\np348\nsVholomdl2\np349\nVHoloLens MDL2 Assets\np350\nsVBRITANIC\np351\nVBritannic Bold\np352\nsVNirmalaB\np353\nVNirmala UI Bold\np354\nsVVollkorn-Regular\np355\nVVollkorn\np356\nsVStephen_\np357\nVStephen\np358\nsVbabyk___\np359\nVBaby Kruffy\np360\nsVHARVEST_\np361\nVHarvest\np362\nsVKUNSTLER\np363\nVKunstler Script\np364\nsVstylu\np365\nVStylus BT Roman\np366\nsVWINGDNG3\np367\nVWingdings 3\np368\nsVWINGDNG2\np369\nVWingdings 2\np370\nsVlucon\np371\nVLucida Console\np372\nsVCandara\np373\nVCandara\np374\nsVBERNHC\np375\nVBernard MT Condensed\np376\nsVtechnic_\np377\nVTechnic\np378\nsVLimou___\np379\nVLimousine\np380\nsVTCB_____\np381\nVTw Cen MT Bold\np382\nsVPirate__\np383\nVPirate\np384\nsVFrnkvent\np385\nVFrankfurter Venetian TT\np386\nsVromand__\np387\nVRomanD\np388\nsVLTYPE\np389\nVLucida Sans Typewriter\np390\nsVSHOWG\np391\nVShowcard Gothic\np392\nsVMOD20\np393\nVModern No. 20\np394\nsVostrich-rounded\np395\nVOstrich Sans Rounded Medium\np396\nsVJosefinSlab-Italic\np397\nVJosefin Slab Italic\np398\nsVneon2\np399\nVNeon Lights\np400\nsVpalabi\np401\nVPalatino Linotype Bold Italic\np402\nsVwoodcut\np403\nVWoodcut\np404\nsVToledo__\np405\nVToledo\np406\nsVverdanai\np407\nVVerdana Italic\np408\nsVSamsungIF_Rg\np409\nVSamsung InterFace\np410\nsVtrebucbd\np411\nVTrebuchet MS Bold\np412\nsVPALSCRI\np413\nVPalace Script MT\np414\nsVComfortaa-Regular\np415\nVComfortaa\np416\nsVmicross\np417\nVMicrosoft Sans Serif\np418\nsVseguisli\np419\nVSegoe UI Semilight Italic\np420\nsVtaile\np421\nVMicrosoft Tai Le\np422\nsVcour\np423\nVCourier New\np424\nsVparryhotter\np425\nVParry Hotter\np426\nsVgreekc__\np427\nVGreekC\np428\nsVRAGE\np429\nVRage Italic\np430\nsVMATURASC\np431\nVMatura MT Script Capitals\np432\nsVBASTION_\np433\nVBastion\np434\nsVREFSAN\np435\nVMS Reference Sans Serif\np436\nsVterminat\np437\nVTerminator Two\np438\nsVmmrtextb\np439\nVMyanmar Text Bold\np440\nsVgothici_\np441\nVGothicI\np442\nsVmonotxt_\np443\nVMonotxt\np444\nsVcorbelb\np445\nVCorbel Bold\np446\nsVVALKEN__\np447\nVValken\np448\nsVRowdyhe_\np449\nVRowdyHeavy\np450\nsVLato-Black\np451\nVLato Black\np452\nsVswisski\np453\nVSwis721 Blk BT Black Italic\np454\nsVcouri\np455\nVCourier New Italic\np456\nsVMTEXTRA\np457\nVMT Extra\np458\nsVsanssbo_\np459\nVSansSerif BoldOblique\np460\nsVl_10646\np461\nVLucida Sans Unicode\np462\nsVLato-BlackItalic\np463\nVLato Black Italic\np464\nsVseguibli\np465\nVSegoe UI Black Italic\np466\nsVGeotype\np467\nVGeotype TT\np468\nsVxfiles\np469\nVX-Files\np470\nsVjavatext\np471\nVJavanese Text\np472\nsVseguisym\np473\nVSegoe UI Symbol\np474\nsVverdanaz\np475\nVVerdana Bold Italic\np476\nsVGILI____\np477\nVGill Sans MT Italic\np478\nsVALGER\np479\nVAlgerian\np480\nsVAGENCYR\np481\nVAgency FB\np482\nsVnobile\np483\nVNobile\np484\nsVHaxton\np485\nVHaxton Logos TT\np486\nsVswissbo\np487\nVSwis721 BdOul BT Bold\np488\nsVBELLI\np489\nVBell MT Italic\np490\nsVBROADW\np491\nVBroadway\np492\nsVsegoepr\np493\nVSegoe Print\np494\nsVGILLUBCD\np495\nVGill Sans Ultra Bold Condensed\np496\nsVverdanab\np497\nVVerdana Bold\np498\nsVSalina__\np499\nVSalina\np500\nsVAGENCYB\np501\nVAgency FB Bold\np502\nsVAutumn__\np503\nVAutumn\np504\nsVGOUDOS\np505\nVGoudy Old Style\np506\nsVconstanz\np507\nVConstantia Bold Italic\np508\nsVPOORICH\np509\nVPoor Richard\np510\nsVPRISTINA\np511\nVPristina\np512\nsVLATINWD\np513\nVWide Latin\np514\nsVromanc__\np515\nVRomanC\np516\nsVLeelawUI\np517\nVLeelawadee UI\np518\nsVitalict_\np519\nVItalicT\np520\nsVostrich-regular\np521\nVOstrich Sans Medium\np522\nsVmonosbi\np523\nVMonospac821 BT Bold Italic\np524\nsVcambriai\np525\nVCambria Italic\np526\nsVisocp2__\np527\nVISOCP2\np528\nsVltromatic\np529\nVLetterOMatic!\np530\nsVbgothm\np531\nVBankGothic Md BT Medium\np532\nsVbgothl\np533\nVBankGothic Lt BT Light\np534\nsVSwkeys1\np535\nVSWGamekeys MT\np536\nsVCENSCBK\np537\nVCentury Schoolbook\np538\nsVgothicg_\np539\nVGothicG\np540\nsValmosnow\np541\nVAlmonte Snow\np542\nsVTangerine_Bold\np543\nVTangerine Bold\np544\nsVswisseb\np545\nVSwis721 Ex BT Bold\np546\nsVCOLONNA\np547\nVColonna MT\np548\nsVsupef___\np549\nVSuperFrench\np550\nsVTCCEB\np551\nVTw Cen MT Condensed Extra Bold\np552\nsVsylfaen\np553\nVSylfaen\np554\nsVcomicbd\np555\nVComic Sans MS Bold\np556\nsVRoland__\np557\nVRoland\np558\nsVELEPHNTI\np559\nVElephant Italic\np560\nsVmmrtext\np561\nVMyanmar Text\np562\nsVsymap___\np563\nVSymap\np564\nsVswissko\np565\nVSwis721 BlkOul BT Black\np566\nsVswissck\np567\nVSwis721 BlkCn BT Black\np568\nsVWhimsy\np569\nVWhimsy TT\np570\nsVsanssb__\np571\nVSansSerif Bold\np572\nsVtaileb\np573\nVMicrosoft Tai Le Bold\np574\nsVcomic\np575\nVComic Sans MS\np576\nsVGLSNECB\np577\nVGill Sans MT Ext Condensed Bold\np578\nsVColbert_\np579\nVColbert\np580\nsVJOKERMAN\np581\nVJokerman\np582\nsVARIALNB\np583\nVArial Narrow Bold\np584\nsVDOMIN___\np585\nVDominican\np586\nsVBRUSHSCI\np587\nVBrush Script MT Italic\np588\nsVCALLI___\np589\nVCalligraphic\np590\nsVFRADM\np591\nVFranklin Gothic Demi\np592\nsVJosefinSlab-LightItalic\np593\nVJosefin Slab Light Italic\np594\nsVsimplex_\np595\nVSimplex\np596\nsVphagspab\np597\nVMicrosoft PhagsPa Bold\np598\nsVswissek\np599\nVSwis721 BlkEx BT Black\np600\nsVscripts_\np601\nVScriptS\np602\nsVswisscl\np603\nVSwis721 LtCn BT Light\np604\nsVCASTELAR\np605\nVCastellar\np606\nsVdutchi\np607\nVDutch801 Rm BT Italic\np608\nsVnasaliza\np609\nVNasalization Medium\np610\nsVariali\np611\nVArial Italic\np612\nsVOpinehe_\np613\nVOpineHeavy\np614\nsVPLAYBILL\np615\nVPlaybill\np616\nsVROCCB___\np617\nVRockwell Condensed Bold\np618\nsVCALIST\np619\nVCalisto MT\np620\nsVCALISTB\np621\nVCalisto MT Bold\np622\nsVHATTEN\np623\nVHaettenschweiler\np624\nsVntailu\np625\nVMicrosoft New Tai Lue\np626\nsVCALISTI\np627\nVCalisto MT Italic\np628\nsVsegoeprb\np629\nVSegoe Print Bold\np630\nsVDAYTON__\np631\nVDayton\np632\nsVswissel\np633\nVSwis721 LtEx BT Light\np634\nsVmael____\np635\nVMael\np636\nsVisoct2__\np637\nVISOCT2\np638\nsVBorea___\np639\nVBorealis\np640\nsVwingding\np641\nVWingdings\np642\nsVONYX\np643\nVOnyx\np644\nsVmonosi\np645\nVMonospac821 BT Italic\np646\nsVtimesi\np647\nVTimes New Roman Italic\np648\nsVostrich-light\np649\nVOstrich Sans Condensed Light\np650\nsVseguihis\np651\nVSegoe UI Historic\np652\nsVNovem___\np653\nVNovember\np654\nsVOCRAEXT\np655\nVOCR A Extended\np656\nsVostrich-black\np657\nVOstrich Sans Black\np658\nsVnarrow\np659\nVPR Celtic Narrow Normal\np660\nsVitalic__\np661\nVItalic\np662\nsVmonosb\np663\nVMonospac821 BT Bold\np664\nsVPERB____\np665\nVPerpetua Bold\np666\nsVCreteRound-Regular\np667\nVCrete Round\np668\nsVcalibri\np669\nVCalibri\np670\nsVSCRIPTBL\np671\nVScript MT Bold\np672\nsVComfortaa-Bold\np673\nVComfortaa Bold\np674\nsVARIALN\np675\nVArial Narrow\np676\nsVHARNGTON\np677\nVHarrington\np678\nsVJosefinSlab-Bold\np679\nVJosefin Slab Bold\np680\nsVVIVALDII\np681\nVVivaldi Italic\np682\nsVhollh___\np683\nVHollywood Hills\np684\nsVBOD_R\np685\nVBodoni MT\np686\nsVSkinny__\np687\nVSkinny\np688\nsVLBRITED\np689\nVLucida Bright Demibold\np690\nsVframdit\np691\nVFranklin Gothic Medium Italic\np692\nsVsymusic_\np693\nVSymusic\np694\nsVgadugi\np695\nVGadugi\np696\nsVswissbi\np697\nVSwis721 BT Bold Italic\np698\nsVBOD_B\np699\nVBodoni MT Bold\np700\nsVERASDEMI\np701\nVEras Demi ITC\np702\nsVWaverly_\np703\nVWaverly\np704\nsVcompi\np705\nVCommercialPi BT\np706\nsVBOD_I\np707\nVBodoni MT Italic\np708\nsVconstan\np709\nVConstantia\np710\nsVARIALNBI\np711\nVArial Narrow Bold Italic\np712\nsVarialbi\np713\nVArial Bold Italic\np714\nsVJosefinSlab-Light\np715\nVJosefin Slab Light\np716\nsVBOD_CBI\np717\nVBodoni MT Condensed Bold Italic\np718\nsVwebdings\np719\nVWebdings\np720\nsVRAVIE\np721\nVRavie\np722\nsVROCC____\np723\nVRockwell Condensed\np724\nsVFELIXTI\np725\nVFelix Titling\np726\nsVRussrite\np727\nVRussel Write TT\np728\nsVisocteur\np729\nVISOCTEUR\np730\nsVLSANSD\np731\nVLucida Sans Demibold Roman\np732\nsVmalgun\np733\nVMalgun Gothic\np734\nsVheavyhea2\np735\nVHeavy Heap\np736\nsVGOUDYSTO\np737\nVGoudy Stout\np738\nsVVLADIMIR\np739\nVVladimir Script\np740\nsVARIALUNI\np741\nVArial Unicode MS\np742\nsVJosefinSlab-Thin\np743\nVJosefin Slab Thin\np744\nsVFRADMCN\np745\nVFranklin Gothic Demi Cond\np746\nsVBlackout-2am\np747\nVBlackout 2 AM\np748\nsVpalab\np749\nVPalatino Linotype Bold\np750\nsVDejaVuSansMono-Oblique\np751\nVDejaVu Sans Mono Oblique\np752\nsVANTQUABI\np753\nVBook Antiqua Bold Italic\np754\nsVswissc\np755\nVSwis721 Cn BT Roman\np756\nsVSPLASH__\np757\nVSplash\np758\nsVNIAGENG\np759\nVNiagara Engraved\np760\nsVCOPRGTB\np761\nVCopperplate Gothic Bold\np762\nsVBruss___\np763\nVBrussels\np764\nsVconsolab\np765\nVConsolas Bold\np766\nsVGOTHICBI\np767\nVCentury Gothic Bold Italic\np768\nsVmtproxy4\np769\nVProxy 4\np770\nsVmtproxy5\np771\nVProxy 5\np772\nsVromai___\np773\nVRomantic Italic\np774\nsVFRABKIT\np775\nVFranklin Gothic Book Italic\np776\nsVBELL\np777\nVBell MT\np778\nsVmtproxy1\np779\nVProxy 1\np780\nsVmtproxy2\np781\nVProxy 2\np782\nsVmtproxy3\np783\nVProxy 3\np784\nsVLCALLIG\np785\nVLucida Calligraphy Italic\np786\nsVphagspa\np787\nVMicrosoft PhagsPa\np788\nsVANTQUAI\np789\nVBook Antiqua Italic\np790\nsVmtproxy8\np791\nVProxy 8\np792\nsVmtproxy9\np793\nVProxy 9\np794\nsVLato-Bold\np795\nVLato Bold\np796\nsVtxt_____\np797\nVTxt\np798\nsVconstanb\np799\nVConstantia Bold\np800\nsVERASBD\np801\nVEras Bold ITC\np802\nsVLato-LightItalic\np803\nVLato Light Italic\np804\nsVRONDALO_\np805\nVRondalo\np806\nsVconstani\np807\nVConstantia Italic\np808\nsVBRLNSB\np809\nVBerlin Sans FB Bold\np810\nsVgeorgiaz\np811\nVGeorgia Bold Italic\np812\nsVgothice_\np813\nVGothicE\np814\nsVcalibriz\np815\nVCalibri Bold Italic\np816\nsVgeorgiab\np817\nVGeorgia Bold\np818\nsVLeelaUIb\np819\nVLeelawadee UI Bold\np820\nsVtimesbi\np821\nVTimes New Roman Bold Italic\np822\nsVPERI____\np823\nVPerpetua Italic\np824\nsVromab___\np825\nVRomantic Bold\np826\nsVBRLNSR\np827\nVBerlin Sans FB\np828\nsVBELLB\np829\nVBell MT Bold\np830\nsVgeorgiai\np831\nVGeorgia Italic\np832\nsVNirmalaS\np833\nVNirmala UI Semilight\np834\nsVdutchb\np835\nVDutch801 Rm BT Bold\np836\nsVdigifit\np837\nVDigifit Normal\np838\nsVROCKEB\np839\nVRockwell Extra Bold\np840\nsVgdt_____\np841\nVGDT\np842\nsVmonbaiti\np843\nVMongolian Baiti\np844\nsVsegoescb\np845\nVSegoe Script Bold\np846\nsVsymath__\np847\nVSymath\np848\nsVisoct___\np849\nVISOCT\np850\nsVTarzan__\np851\nVTarzan\np852\nsVsnowdrft\np853\nVSnowdrift\np854\nsVHTOWERTI\np855\nVHigh Tower Text Italic\np856\nsVCENTURY\np857\nVCentury\np858\nsVmalgunsl\np859\nVMalgun Gothic Semilight\np860\nsVseguibl\np861\nVSegoe UI Black\np862\nsVCreteRound-Italic\np863\nVCrete Round Italic\np864\nsVAlfredo_\np865\nVAlfredo\np866\nsVCOMMONS_\np867\nVCommons\np868\nsVLFAX\np869\nVLucida Fax\np870\nsVLBRITEI\np871\nVLucida Bright Italic\np872\nsVFRAHV\np873\nVFranklin Gothic Heavy\np874\nsVisocteui\np875\nVISOCTEUR Italic\np876\nsVManorly_\np877\nVManorly\np878\nsVBolstbo_\np879\nVBolsterBold Bold\np880\nsVsegoeui\np881\nVSegoe UI\np882\nsVNunito-Light\np883\nVNunito Light\np884\nsVIMPRISHA\np885\nVImprint MT Shadow\np886\nsVgeorgia\np887\nVGeorgia\np888\nsV18cents\np889\nV18thCentury\np890\nsVMOONB___\np891\nVMoonbeam\np892\nsVPER_____\np893\nVPerpetua\np894\nsVHansen__\np895\nVHansen\np896\nsVLato-Regular\np897\nVLato\np898\nsVBOUTON_International_symbols\np899\nVBOUTON International Symbols\np900\nsVCOOPBL\np901\nVCooper Black\np902\nsVmonos\np903\nVMonospac821 BT Roman\np904\nsVtahoma\np905\nVTahoma\np906\nsVcityb___\np907\nVCityBlueprint\np908\nsVswisscbi\np909\nVSwis721 Cn BT Bold Italic\np910\nsVEnliven_\np911\nVEnliven\np912\nsVLeelUIsl\np913\nVLeelawadee UI Semilight\np914\nsVCALIFR\np915\nVCalifornian FB\np916\nsVumath\np917\nVUniversalMath1 BT\np918\nsVswisscbo\np919\nVSwis721 BdCnOul BT Bold Outline\np920\nsVcomplex_\np921\nVComplex\np922\nsVBOOKOSB\np923\nVBookman Old Style Bold\np924\nsVMartina_\np925\nVMartina\np926\nsVromans__\np927\nVRomanS\np928\nsVmvboli\np929\nVMV Boli\np930\nsVCALIFI\np931\nVCalifornian FB Italic\np932\nsVGARABD\np933\nVGaramond Bold\np934\nsVebrima\np935\nVEbrima\np936\nsVTEMPSITC\np937\nVTempus Sans ITC\np938\nsVCALIFB\np939\nVCalifornian FB Bold\np940\nsVitalicc_\np941\nVItalicC\np942\nsVisocp3__\np943\nVISOCP3\np944\nsVscriptc_\np945\nVScriptC\np946\nsValiee13\np947\nVAlien Encounters\np948\nsVnobile_italic\np949\nVNobile Italic\np950\nsVGARAIT\np951\nVGaramond Italic\np952\nsVswissli\np953\nVSwis721 Lt BT Light Italic\np954\nsVCabinSketch-Bold\np955\nVCabinSketch Bold\np956\nsVcorbel\np957\nVCorbel\np958\nsVseguisbi\np959\nVSegoe UI Semibold Italic\np960\nsVSCHLBKBI\np961\nVCentury Schoolbook Bold Italic\np962\nsVasimov\np963\nVAsimov\np964\nsVLFAXDI\np965\nVLucida Fax Demibold Italic\np966\nsVBRADHITC\np967\nVBradley Hand ITC\np968\nsVswisscki\np969\nVSwis721 BlkCn BT Black Italic\np970\nsVGILSANUB\np971\nVGill Sans Ultra Bold\np972\nsVHARLOWSI\np973\nVHarlow Solid Italic Italic\np974\nsVHARVEIT_\np975\nVHarvestItal\np976\nsVcambriab\np977\nVCambria Bold\np978\nsVswissci\np979\nVSwis721 Cn BT Italic\np980\nsVcounb___\np981\nVCountryBlueprint\np982\nsVNotram__\np983\nVNotram\np984\nsVPENULLI_\np985\nVPenultimateLight\np986\nsVtahomabd\np987\nVTahoma Bold\np988\nsVMISTRAL\np989\nVMistral\np990\nsVpala\np991\nVPalatino Linotype\np992\nsVOLDENGL\np993\nVOld English Text MT\np994\nsVinductio\np995\nVInduction Normal\np996\nsVJosefinSlab-SemiBoldItalic\np997\nVJosefin Slab SemiBold Italic\np998\nsVMinerva_\np999\nVMinerva\np1000\nsVsymbol\np1001\nVSymbol\np1002\nsVcambriaz\np1003\nVCambria Bold Italic\np1004\nsVtrebucbi\np1005\nVTrebuchet MS Bold Italic\np1006\nsVtimes\np1007\nVTimes New Roman\np1008\nsVERASLGHT\np1009\nVEras Light ITC\np1010\nsVSteppes\np1011\nVSteppes TT\np1012\nsVREFSPCL\np1013\nVMS Reference Specialty\np1014\nsVPARCHM\np1015\nVParchment\np1016\nsVDejaVuSansMono-Bold\np1017\nVDejaVu Sans Mono Bold\np1018\nsVswisscli\np1019\nVSwis721 LtCn BT Light Italic\np1020\nsVLSANS\np1021\nVLucida Sans\np1022\nsVPhrasme_\np1023\nVPhrasticMedium\np1024\nsVDejaVuSansMono-BoldOblique\np1025\nVDejaVu Sans Mono Bold Oblique\np1026\nsVarialbd\np1027\nVArial Bold\np1028\nsVSNAP____\np1029\nVSnap ITC\np1030\nsVArchitectsDaughter\np1031\nVArchitects Daughter\np1032\nsVCorpo___\np1033\nVCorporate\np1034\nsVeurro___\np1035\nVEuroRoman Oblique\np1036\nsVimpact\np1037\nVImpact\np1038\nsVlittlelo\np1039\nVLittleLordFontleroy\np1040\nsVsimsunb\np1041\nVSimSun-ExtB\np1042\nsVARIALNI\np1043\nVArial Narrow Italic\np1044\nsVdutchbi\np1045\nVDutch801 Rm BT Bold Italic\np1046\nsVcalibrii\np1047\nVCalibri Italic\np1048\nsVDeneane_\np1049\nVDeneane\np1050\nsVFRADMIT\np1051\nVFranklin Gothic Demi Italic\np1052\nsVANTQUAB\np1053\nVBook Antiqua Bold\np1054\nsVcalibril\np1055\nVCalibri Light\np1056\nsVisocpeui\np1057\nVISOCPEUR Italic\np1058\nsVpanroman\np1059\nVPanRoman\np1060\nsVMelodbo_\np1061\nVMelodBold Bold\np1062\nsVcalibrib\np1063\nVCalibri Bold\np1064\nsVdistant galaxy 2\np1065\nVDistant Galaxy\np1066\nsVPacifico\np1067\nVPacifico\np1068\nsVnobile_bold_italic\np1069\nVNobile Bold Italic\np1070\nsVmsyi\np1071\nVMicrosoft Yi Baiti\np1072\nsVBOD_PSTC\np1073\nVBodoni MT Poster Compressed\np1074\nsVLSANSI\np1075\nVLucida Sans Italic\np1076\nsVcreerg__\np1077\nVCreepygirl\np1078\nsVsegoeuisl\np1079\nVSegoe UI Semilight\np1080\nsVvinet\np1081\nVVineta BT\np1082\nsVisocpeur\np1083\nVISOCPEUR\np1084\nsVtechl___\np1085\nVTechnicLite\np1086\nsVswissb\np1087\nVSwis721 BT Bold\np1088\nsVCLARE___\np1089\nVClarendon\np1090\nsVdutch\np1091\nVDutch801 Rm BT Roman\np1092\nsVLBRITEDI\np1093\nVLucida Bright Demibold Italic\np1094\nsVswisse\np1095\nVSwis721 Ex BT Roman\np1096\nsVswissk\np1097\nVSwis721 Blk BT Black\np1098\nsVswissi\np1099\nVSwis721 BT Italic\np1100\nsVfingerpop2\np1101\nVFingerpop\np1102\nsVswissl\np1103\nVSwis721 Lt BT Light\np1104\nsVBAUHS93\np1105\nVBauhaus 93\np1106\nsVVivian__\np1107\nVVivian\np1108\nsVgreeks__\np1109\nVGreekS\np1110\nsVGOUDOSI\np1111\nVGoudy Old Style Italic\np1112\nsVBOD_BI\np1113\nVBodoni MT Bold Italic\np1114\nsVLHANDW\np1115\nVLucida Handwriting Italic\np1116\nsVITCKRIST\np1117\nVKristen ITC\np1118\nsVBALTH___\np1119\nVBalthazar\np1120\nsVFORTE\np1121\nVForte\np1122\nsVJosefinSlab-Regular\np1123\nVJosefin Slab\np1124\nsVROCKI\np1125\nVRockwell Italic\np1126\nsVGOUDOSB\np1127\nVGoudy Old Style Bold\np1128\nsVLEELAWAD\np1129\nVLeelawadee\np1130\nsVLEELAWDB\np1131\nVLeelawadee Bold\np1132\nsVmarlett_0\np1133\nVMarlett\np1134\nsVmplus-1m-bold\np1135\nVM+ 1m bold\np1136\nsVmplus-1m-light\np1137\nVM+ 1m light\np1138\nsVmplus-1m-medium\np1139\nVM+ 1m medium\np1140\nsVmplus-1m-regular\np1141\nVM+ 1m\np1142\nsVmplus-1m-thin\np1143\nVM+ 1m thin\np1144\nsVMSUIGHUB\np1145\nVMicrosoft Uighur Bold\np1146\nsVMSUIGHUR\np1147\nVMicrosoft Uighur\np1148\nsVSamsungIF_Md_0\np1149\nVSamsung InterFace Medium\np1150\nsVSamsungIF_Rg_0\np1151\nVSamsung InterFace\np1152\nsVbahnschrift\np1153\nVBahnschrift\np1154\nsVBowlbyOneSC-Regular\np1155\nVBowlby One SC\np1156\nsVCabinSketch-Regular\np1157\nVCabin Sketch\np1158\nsVCookie-Regular\np1159\nVCookie\np1160\nsVCourgette-Regular\np1161\nVCourgette\np1162\nsVdead\np1163\nVDead Kansas\np1164\nsVDoppioOne-Regular\np1165\nVDoppio One\np1166\nsVeuphorig\np1167\nVEuphorigenic\np1168\nsVGreatVibes-Regular\np1169\nVGreat Vibes\np1170\nsVKalam-Bold\np1171\nVKalam Bold\np1172\nsVKalam-Light\np1173\nVKalam Light\np1174\nsVKalam-Regular\np1175\nVKalam\np1176\nsVLemon-Regular\np1177\nVLemon\np1178\nsVLimelight-Regular\np1179\nVLimelight\np1180\nsVMegrim\np1181\nVMegrim Medium\np1182\nsVMontserratSubrayada-Bold\np1183\nVMontserrat Subrayada Bold\np1184\nsVNotoSans-Regular\np1185\nVNoto Sans\np1186\nsVRussoOne-Regular\np1187\nVRusso One\np1188\nsVSigmarOne-Regular\np1189\nVSigmar One\np1190\nsVYellowtail-Regular\np1191\nVYellowtail\np1192\ns.')  # NOQA
    return _std_fonts.cached


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
        fontlist1 = [fontname]
    else:
        fontlist1 = list(fontname)

    fontlist1.extend(['calibri', 'arial'])

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

    heightA = result.getsize('A')[1]
    getfont.lookup[(fontname, fontsize)] = result, heightA
    return result, heightA


def show_fonts():
    '''
    show (print) all available fonts on this machine
    '''
    fontnames = []
    for fns, ifilename in fonts():
        for fn in fns:
            fontnames.append(fn)
    fontnames.extend(list(standardfonts()))
    last = ''
    for font in sorted(fontnames, key=normalize):
        if font != last:  # remove duplicates
            print(font)
            last = font


def show_colornames():
    '''
    show (print) all available color names and their value.
    '''
    names = sorted(colornames())
    for name in names:
        print('{:22s}{}'.format(name, colornames()[name]))


def arrow_polygon(size):
    '''
    creates a polygon tuple with a centerd arrow for use with sim.Animate

    Parameters
    ----------
    size : float
        length of the arrow
    '''
    size /= 4
    return (-2 * size, -size, 0, -size, 0, -2 * size, 2 * size, 0, 0, 2 * size, 0, size, -2 * size, size)


def centered_rectangle(width, height):
    '''
    creates a rectangle tuple with a centered rectangle for use with sim.Animate

    Parameters
    ----------
    width : float
        width of the rectangle

    height : float
        height of the rectangle
    '''
    return -width / 2, -height / 2, width / 2, height / 2


def regular_polygon(radius=1, number_of_sides=3, initial_angle=0):
    '''
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
    '''
    number_of_sides = int(number_of_sides)
    if number_of_sides < 3:
        raise SalabimError('number of sides < 3')
    tangle = 2 * math.pi / number_of_sides
    sint = math.sin(tangle)
    cost = math.cos(tangle)
    p = []
    x = radius * math.cos(initial_angle * math.pi / 180)
    y = radius * math.sin(initial_angle * math.pi / 180)

    for i in range(number_of_sides):
        x, y = (x * cost - y * sint, x * sint + y * cost)
        p.append(x + radius)
        p.append(y + radius)

    return p


def can_animate(try_only=True):
    '''
    Tests whether animation is supported.

    Parameters
    ----------
    try_only : bool
        if True (default), the function does not raise an error when the required modules cannot be imported |n|
        if False, the function will only return if the required modules could be imported.

    Returns
    -------
    True, if required modules could be imported, False otherwise : bool
    '''
    global Image
    global ImageDraw
    global ImageFont
    global GifImagePlugin
    global ImageTk
    global tkinter
    try:
        import PIL  # NOQA
        from PIL import Image
        from PIL import ImageDraw
        from PIL import ImageFont
        from PIL import GifImagePlugin
        if not Pythonista:
            from PIL import ImageTk
    except ImportError:
        if try_only:
            return False
        raise SalabimError('PIL is required for animation. Install with pip install Pillow or see salabim manual')

    if not Pythonista:
        try:
            import tkinter
        except ImportError:
            try:
                import Tkinter as tkinter
            except ImportError:
                if try_only:
                    return False
                raise SalabimError('tkinter is required for animation')
    return True


def can_video(try_only=True):
    '''
    Tests whether video is supported.

    Parameters
    ----------
    try_only : bool
        if True (default), the function does not raise an error when the required modules cannot be imported |n|
        if False, the function will only return if the required modules could be imported.

    Returns
    -------
    True, if required modules could be imported, False otherwise : bool
    '''
    global cv2
    global np
    if Pythonista:
        if try_only:
            return False
        raise SalabimError('video production not supported on Pythonista')
    else:
        try:
            import cv2
            import numpy as np
        except ImportError:
            if try_only:
                return False
            if platform.python_implementation == 'PyPy':
                raise SalabimError('video production is not supported under PyPy.')
            else:
                raise SalabimError('cv2 required for video production. Install with pip install opencv-python')
    return True


def default_env():
    '''
    Returns
    -------
    default environment : Environment
    '''
    return g.default_env


def reset():
    '''
    resets global variables

    used internally at import of salabim

    might be useful for REPLs or for Pythonista
    '''
    try:
        g.default_env.video_close()
    except:
        pass

    g.default_env = None
    g.animation_env = None
    g.animation_scene = None
    g.in_draw = False


reset()

if __name__ == '__main__':
    try:
        import salabim_test
    except ModuleNotFoundError:
        print('salabim_test.py not found')
        quit()

    try:
        salabim_test.__dict__['test']
    except KeyError:
        print('salabim_test.test() not found')
        quit()

    salabim_test.test()
