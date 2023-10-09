![Logo](./images/ycecream_logo.png)

# Introduction

Do you ever use `print()` or `log()` to debug your code? If so,  ycecream, or `y` for short, will make printing debug information a lot sweeter.
And on top of that, you get some basic benchmarking functionality.

# Table of contents

* [Installation](#installation)

* [Inspect variables and expressions](#inspect-variables-and-expressions)

* [Inspect execution](#inspect-execution)

* [Return value](#return-value)

* [Debug entry and exit of function calls](#debug-entry-and-exit-of-function-calls)

* [Benchmarking with ycecream](#benchmarking-with-ycecream)

* [Configuration](#configuration)

* [Return a string instead of sending to output](#return-a-string-instead-of-sending-to-output)

* [Disabling ycecream's output](#disabling-ycecreams-output)

* [Speeding up disabled ycecream](#speeding-up-disabled-ycecream)

* [Using ycecream as a substitute for `assert`](#using-ycecream-as-a-substitute-for-assert)

* [Interpreting the line number information](#interpreting-the-line-number-information)

* [Configuring at import time](#configuring-at-import-time)

* [Working with multiple instances of y](#working-with-multiple-instances-of-y)

* [Test script](#test-script)

* [Using ycecream in a REPL](#using-ycecream-in-a-repl)

* [Alternative to `y`](#alternative-to-y)

* [Alternative installation](#alternative-installation)

* [Limitations](#limitations)

* [Implementation details](implementation-details)

* [Acknowledgement](#acknowledgement)

* [Differences with IceCream](./differences_with_icecream.md)


# Installation

Installing ycecream with pip is easy.
```
$ pip install ycecream
```
or when you want to upgrade,
```
$ pip install ycecream --upgrade
```

Alternatively, ycecream.py can be juist copied into you current work directory from GitHub (https://github.com/salabim/ycecream).

No dependencies!


# Inspect variables and expressions

Have you ever printed variables or expressions to debug your program? If you've
ever typed something like

```
print(add2(1000))
```

or the more thorough

```
print("add2(1000)", add2(1000)))
```
or (for Python >= 3.8 only):
```
print(f"{add2(1000) =}")
```

then `y()` is here to help. With arguments, `y()` inspects itself and prints
both its own arguments and the values of those arguments.

```
from ycecream import y

def add2(i):
    return i + 2

y(add2(1000))
```

prints
```
y| add2(1000): 1002
```

Similarly,

```
from ycecream import y
class X:
    a = 3
world = {"EN": "world", "NL": "wereld", "FR": "monde", "DE": "Welt"}

y(world, X.a)
```

prints
```
y| world: {"EN": "world", "NL": "wereld", "FR": "monde", "DE": "Welt"}, X.a: 3
```
Just give `y()` a variable or expression and you're done. Sweet, isn't it?


# Inspect execution

Have you ever used `print()` to determine which parts of your program are
executed, and in which order they're executed? For example, if you've ever added
print statements to debug code like

```
def add2(i):
    print("enter")
    result = i + 2
    print("exit")
    return result
```
then `y()` helps here, too. Without arguments, `y()` inspects itself and
prints the calling line number and -if applicable- the file name and parent function.

```
from ycecream import y
def add2(i):
    y()
    result = i + 2
    y()
    return result
y(add2(1000))
```

prints something like
```
y| #3 in add2()
y| #5 in add2()
y| add2(1000): 1002
```
Just call `y()` and you're done. Isn't that sweet?


# Return Value

`y()` returns its argument(s), so `y()` can easily be inserted into
pre-existing code.

```
from ycecream import y
def add2(i):
    return i + 2
b = y(add2(1000))
y(b)
```
prints
```
y| add2(1000): 1002
y| b: 1002
```
# Debug entry and exit of function calls

When you apply `y()` as a decorator to a function or method, both the entry and exit can be tracked.
The (keyword) arguments passed will be shown and upon return, the return value.

```
from ycecream import y
@y()
def mul(x, y):
    return x * y
    
print(mul(5, 7))
```
prints
```
y| called mul(5, 7)
y| returned 35 from mul(5, 7) in 0.000006 seconds
35
```
It is possible to suppress the print-out of either the enter or the exit information with
the show_enter and show_exit parameters, like:

```
from ycecream import y
@y(show_exit=False)
def mul(x, y):
    return x * y
    
print(mul(5, 7))
```
prints
```
y| called mul(5, 7)
35
```
Note that it is possible to use `y` as a decorator without the parentheses, like
```
@y
def diode(x):
    return 0 if x<0 else x
```
, but this might not work correctly when the def/class definition spawns more than one line. So, always use `y()` or
`y(<parameters>)` when used as a decorator.  

# Benchmarking with ycecream

If you decorate a function or method with y, you will be offered the duration between entry and exit (in seconds) as a bonus.

That opens the door to simple benchmarking, like:
```
from ycecream import y
import time

@y(show_enter=False,show_line_number=True)
def do_sort(i):
    n = 10 ** i
    x = sorted(list(range(n)))
    return f"{n:9d}"  
    
for i in range(8):
    do_sort(i)
```
the ouput will show the effects of the population size on the sort speed:
```
y| #5 ==> returned '        1' from do_sort(0) in 0.000027 seconds
y| #5 ==> returned '       10' from do_sort(1) in 0.000060 seconds
y| #5 ==> returned '      100' from do_sort(2) in 0.000748 seconds
y| #5 ==> returned '     1000' from do_sort(3) in 0.001897 seconds
y| #5 ==> returned '    10000' from do_sort(4) in 0.002231 seconds
y| #5 ==> returned '   100000' from do_sort(5) in 0.024014 seconds
y| #5 ==> returned '  1000000' from do_sort(6) in 0.257504 seconds
y| #5 ==> returned ' 10000000' from do_sort(7) in 1.553495 seconds
```

It is also possible to time any code by using y as a context manager, e.g.
```
with y():
    time.sleep(1)
```
wil print something like
```
y| enter
y| exit in 1.000900 seconds
```
You can include parameters here as well:
```
with y(show_context=True, show_time=True):
    time.sleep(1)
```
will print somethink like:
```
y| #8 @ 13:20:32.605903 ==> enter
y| #8 @ 13:20:33.609519 ==> exit in 1.003358 seconds
```

Finally, to help with timing code, you can request the current delta with
```
y().delta
```
or (re)set it  with
```
y().delta = 0
```
So, e.g. to time a section of code:
```
y.delta = 0
time.sleep(1)
duration = y.delta
y(duration)
```
might print:
```
y| duration: 1.0001721999999997
```

# Configuration

For the configuration, it is important to realize that `y` is an instance of the `ycecream._Y` class, which has
a number of configuration attributes:
```
------------------------------------------------------
attribute               alternative     default
------------------------------------------------------
prefix                  p               "y| "
output                  o               "stderr"
serialize                               pprint.pformat
show_line_number        sln             False
show_time               st              False
show_delta              sd              False
show_enter              se              True
show_exit               sx              True
show_traceback          stb             False
sort_dicts *)           sdi             False
enabled                 e               True
line_length             ll              80
compact *)              c               False
indent                  i               1
depth                   de              1000000
wrap_indent             wi              "     "   
separator               sep             ", "
context_separator       cs              " ==> "
equals_separator        es              ": "
values_only             vo              False
value_only_for_fstrings voff            False 
return_none             rn              False
enforce_line_length     ell             False
decorator               d               False
context_manager         cm              False
delta                   dl              0
------------------------------------------------------
*) ignored under Python 2.7
```
It is perfectly ok to set/get any of these attributes directly, like
```
y.prefix = "==> "
print(y.prefix)
```

But, it is also possible to apply configuration directly in the call to `y`:
So, it is possible to say
```
from ycecream import y
y(12, prefix="==> ")
```
, which will print
```
==> 12
```
It is also possible to configure y permanently with the configure method. 
```
y.configure(prefix="==> ")
y(12)
```
will print
```
==> 12
```
It is arguably easier to say:
```
y.prefix = "==> "
y(12)
```
or even
```
y.p = "==> "
y(12)
```
to print
```
==> 12
```
Yet another way to configure y is to get a new instance of y with y.new() and the required configuration:
```
z = y.new(prefix="==> ")
z(12)
```
will print
```
==> 12
```

Or, yet another possibility is to clone y (optionally with modified attributes):
```
yd1 = y.clone(show_date=True)
yd2 = y.clone()
yd2.configure(show_date=True)
```
After this `yd1` and `yd2` will behave similarly (but they are not the same!)

## prefix / p
```
from ycecream import y
y('world', prefix='hello -> ')
```
prints
```
hello -> 'world'
```

`prefix` can be a function, too.

```
import time
from ycecream import y
def unix_timestamp():
    return f"{int(time.time())} "
hello = "world"
y.configure(prefix=unix_timestamp)
y(hello) 
```
prints
```
1613635601 hello: 'world'
```

## output / o
This will allow the output to be handled by something else than the default (output being written to stderr).

The `output` attribute can be

* a callable that accepts at least one parameter (the text to be printed)
* a string or Path object that will be used as the filename
* a text file that is open for writing/appending

In the example below, 
```
from ycecream import y
import sys
y(1, output=print)
y(2, output=sys.stdout
with open("test", "a+") as f:
    y(3, output=f)
y(4, output="")
```
* `y| 1` will be printed to stdout
* `y| 2` will be printed to stdout
* `y| 3` will be appended to the file test
* `y| 4` will *disappear*

As `output` may be any callable, you can even use this to automatically log any `y` output:
```
from ycecream import y
import logging
logging.basicConfig(level="INFO")
log = logging.getLogger("demo")
y.configure(output=log.info)
a = {1, 2, 3, 4, 5}
y(a)
a.remove(4)
y(a)
```
will print to stderr:
```
INFO:demo:y| a: {1, 2, 3, 4, 5}
INFO:demo:y| a: {1, 2, 3, 5}
```
Finally, you can specify the following strings:
```
"stderr"           to print to stderr
"stdout"           to print to stdout
"null" or ""       to completely ignore (dummy) output 
"logging.debug"    to use logging.debug
"logging.info"     to use logging.info
"logging.warning"  to use logging.warning
"logging.error"    to use logging.error
"logging.critical" to use logging.critical
```
E.g.
```
from ycecream import y
import sys
y.configure(output="stdout")
```
to print to stdout.

## serialize
This will allow to specify how argument values are to be
serialized to displayable strings. The default is pformat (from pprint), but this can be changed to,
for example, to handle non-standard datatypes in a custom fashion.
The serialize function should accept at least one parameter.
The function can optionally accept the keyword arguments `width` and `sort_dicts`, `compact`, `indent` and `depth`.
```
from ycecream import y
def add_len(obj):
    if hasattr(obj, "__len__"):
        add = f" [len={len(obj)}]"
    else:
        add = ""
    return f"{repr(obj)}{add}"

l = list(range(7))
hello = "world"
y(7, hello, l, serialize=add_len)
```   
prints
```
y| 7, hello: 'world' [len=5], l: [0, 1, 2, 3, 4, 5, 6] [len=7]
```

## show_line_number / sln
If True, adds the `y()` call's line number and possible the filename and parent function to `y()`'s output.

```
from ycecream import y
y.configure(show_line_number=True)
def shout():
    hello="world"
    y(hello)
shout()
```
prints something like
```
y| #5 in shout() ==> hello: 'world'
```

If "no parent" or "n", the parent function will not be shown.
```
from ycecream import y
y.configure(show_line_number="n")
def shout():
    hello="world"
    y(hello)
shout()
```
prints something like
```
y| #5 ==> hello: 'world'
```
Note that if you call `y` without any arguments, the line number is always shown, regardless of the status `show_line_number`.

See below for an explanation of the information provided.

## show_time / st
If True, adds the current time to `y()`'s output.

```
from ycecream import y
y.configure(show_time=True)
hello="world"
y(hello)
```
prints something like
```
y| @ 13:01:47.588125 ==> hello: 'world'
```

## show_delta / sd
If True, adds the number of seconds since the start of the program to `y()`'s output.
```
from ycecream import y
import time
y.configure(show_delta=True)
french = "bonjour le monde"
english = "hallo world"
y(english)
time.sleep(1)
y(french)
```
prints something like
```
y| delta=0.088 ==> english: 'hallo world'
y| delta=1.091 ==> french: 'bonjour le monde'
```

## show_enter / se
When used as a decorator or context manager, by default, ycecream ouputs a line when the decorated the
function is called  or the context manager is entered.

With `show_enter=False` this line can be suppressed.

## show_exit / sx
When used as a decorator or context manager, by default, ycecream ouputs a line when the decorated the
function returned or the context manager is exited.

With `show_exit=False` this line can be suppressed.


## show_traceback / stb
When show_traceback is True, the ordinary output of y() will be followed by a printout of the
traceback, similar to an error traceback.
```
from ycecream import y
y.show_traceback=True
def x():
    y()

x()
x()
```
prints
```
y| #4 in x()
    Traceback (most recent call last)
      File "c:\Users\Ruud\Dropbox (Personal)\Apps\Python Ruud\ycecream\x.py", line 6, in <module>
        x()
      File "c:\Users\Ruud\Dropbox (Personal)\Apps\Python Ruud\ycecream\x.py", line 4, in x
        y()
y| #4 in x()
    Traceback (most recent call last)
      File "c:\Users\Ruud\Dropbox (Personal)\Apps\Python Ruud\ycecream\x.py", line 7, in <module>
        x()
      File "c:\Users\Ruud\Dropbox (Personal)\Apps\Python Ruud\ycecream\x.py", line 4, in x
        y()
```
The `show_traceback` functionality is also available when y is used as a decorator or context manager. 

## line_length / ll
This attribute is used to specify the line length (for wrapping). The default is 80.
Ycecream always tries to keep all output on one line, but if it can't it will wrap:
```
d = dict(a1=1,a2=dict(a=1,b=1,c=3),a3=list(range(10)))
y(d)
y(d, line_length=120)
```
prints
```
y|
    d:
        {'a1': 1,
         'a2': {'a': 1, 'b': 1, 'c': 3},
         'a3': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
y| d: {'a1': 1, 'a2': {'a': 1, 'b': 1, 'c': 3}, 'a3': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
```

## compact / c
This attribute is used to specify the compact parameter for `pformat` (see the pprint documentation
for details). `compact` is False by default.
```
a = 9 * ["0123456789"]
y(a)
y(a, compact=True)
```
prints
```
y|
    a:
        ['0123456789',
         '0123456789',
         '0123456789',
         '0123456789',
         '0123456789',
         '0123456789',
         '0123456789',
         '0123456789',
         '0123456789']
y|
    a:
        ['0123456789', '0123456789', '0123456789', '0123456789', '0123456789',
         '0123456789', '0123456789', '0123456789', '0123456789']
```
Note that `compact` is ignored under Python 2.7.

## indent / i
This attribute is used to specify the indent parameter for `pformat` (see the pprint documentation
for details). `indent` is 1 by default.
```
s = "01234567890012345678900123456789001234567890"
y( [s, [s]])
y( [s, [s]], indent=4)
```
prints
```
y|
    [s, [s]]:
        ['01234567890012345678900123456789001234567890',
         ['01234567890012345678900123456789001234567890']]
y|
    [s, [s]]:
        [   '01234567890012345678900123456789001234567890',
            ['01234567890012345678900123456789001234567890']]
```

## depth / de
This attribute is used to specify the depth parameter for `pformat` (see the pprint documentation
for details). `depth` is `1000000` by default. 
```
s = "01234567890012345678900123456789001234567890"
y([s,[s,[s,[s,s]]]])
y([s,[s,[s,[s,s]]]], depth=3)
```
prints
```
y|
    [s,[s,[s,[s,s]]]]:
        ['01234567890012345678900123456789001234567890',
         ['01234567890012345678900123456789001234567890',
          ['01234567890012345678900123456789001234567890',
           ['01234567890012345678900123456789001234567890',
            '01234567890012345678900123456789001234567890']]]]
y|
    [s,[s,[s,[s,s]]]]:
        ['01234567890012345678900123456789001234567890',
         ['01234567890012345678900123456789001234567890',
          ['01234567890012345678900123456789001234567890', [...]]]]
```

## wrap_indent / wi
This specifies the indent string if the output does not fit in the line_length (has to be wrapped).
Rather than a string, wrap_indent can be also be an integer, in which case the wrap_indent will be that amount of blanks.
The default is 4 blanks.

E.g.
```
d = dict(a1=1,a2=dict(a=1,b=1,c=3),a3=list(range(10)))
y(d, wrap_indent="  ")
y(d, wrap_indent="....")
y(d, wrap_indent=2)
```
prints
```
y|
  d:
    {'a1': 1,
     'a2': {'a': 1, 'b': 1, 'c': 3},
     'a3': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
y|
....d:
........{'a1': 1,
........ 'a2': {'a': 1, 'b': 1, 'c': 3},
........ 'a3': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
y|
  d:
    {'a1': 1,
     'a2': {'a': 1, 'b': 1, 'c': 3},
     'a3': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
```

## enabled / e
Can be used to disable the output:
```
from ycecream import y

y.configure(enabled=False)
s = 'the world is '
y(s + 'perfect.')
y.configure(enabled=True)
y(s + 'on fire.')
```
prints
```
y| s + 'on fire.': 'the world is on fire.'
```
and nothing about a perfect world.

## sort_dicts / sdi
By default, ycecream does not sort dicts (printed by pprint). However, it is possible to get the
default pprint behaviour (i.e. sorting dicts) with the sorted_dicts attribute:

```
world = {"EN": "world", "NL": "wereld", "FR": "monde", "DE": "Welt"}
y(world))
s1 = y(world, sort_dicts=False)
s2 = y(world, sort_dicts=True)
```
prints
```
y| world: {'EN': 'world', 'NL': 'wereld', 'FR': 'monde', 'DE': 'Welt'}
y| world: {'EN': 'world', 'NL': 'wereld', 'FR': 'monde', 'DE': 'Welt'}
y| world: {'DE': 'Welt', 'EN': 'world', 'FR': 'monde', 'NL': 'wereld'}
```
Note that `sort_dicts` is ignored under Python 2.7, i.e. dicts are always sorted.

## separator / sep
By default, pairs (on one line) are separated by `, `.
It is possible to change this with the attribute ` separator`:
```
a="abcd"
b=1
c=1000
d=list("ycecream")
y(a,(b,c),d)
y(a,(b,c),d, separator=" | ")
```
prints
```
y| a: 'abcd', (b,c): (1, 1000), d: ['y', 'c', 'e', 'c', 'r', 'e', 'a', 'm']
y| a: 'abcd' | (b,c): (1, 1000) | d: ['y', 'c', 'e', 'c', 'r', 'e', 'a', 'm']
```
## context_separator / cs
By default the line_number, time and/or delta are followed by ` ==> `.
It is possible to change this with the attribute `context_separator`:
```
a="abcd"
y(a)
y(a, show_time=True, context_separator = ' \u279c ')
```
prints:
```
y| @ 12:56:11.341650 ==> a: 'abcd'
y| @ 12:56:11.485567 ➜ a: 'abcd'
```
## equals_separator / es
By default name of a variable and its value are separated by `: `.
It is possible to change this with the attribute `equals_separator`:
```
a="abcd"
y(a)
y(a, equals_separator = ' == ")
```
prints:
```
y| a: 'abcd'
y| a == 'abcd'
```

## values_only / vo
If False (the default), both the left-hand side (if possible) and the
value will be printed. If True, the left_hand side will be suppressed:
```
hello = "world"
y(hello, 2 * hello)
y(hello, 2 * hello, values_only=True)
```
prints
```
y| hello: 'world', 2 * hello = 'worldworld'
y| 'world', 'worldworld'
```
The values=True version of y can be seen as a supercharged print/pprint.


## values_only_for_fstrings / voff
If False (the default), both the original f-string and the
value will be printed for f-strings.
If True, the left_hand side will be suppressed in case of an f-string:
```
x = 12.3
y(f"{x:0.3e}")
y.values_only_for_fstrings = True
y(f"{x:0.3e}")
```
prints
```
y| f"{x:0.3e}": '1.230e+01'
y| '1.230e+01'
```
Note that if `values_only` is True, f-string will be suppressed, regardless of `values_only_for_fstrings`.

## return_none / rn
Normally, `y()`returns the values passed directly, which is usually fine. However, when used in a notebook
or REPL, that value will be shown, and that can be annoying. Therefore, if `return_none`is True, `y()`will
return None and thus not show anything.
```
a = 3
print(y(a, a + 1))
y.configure(return_none=True)
print(y(a, a + 1))
```
prints
```
y| (3, 4)
(3, 4)
y| (3, 4)
None
```

## enforce_line_length / ell
If enforce_line_length is True, all output lines are explicitely truncated to the given
line_length, even those that are not truncated by pformat.

## delta / dl
The delta attribute can be used to (re)set the current delta, e.g.
```
y.configure(dl=0)
print(y.delta)
```
prints a value that slightly more than 0.


## decorator / d
Normally, an ycecream instance can be used as to show values, as a decorator and as a
context manager.

However, when used from a REPL the usage as a decorator can't be detected properly and in that case,
specify `decorator=True`. E.g. 
```
>>>@y(decorator=True)
>>>def add2(x):
>>>    return x + 2
>>>print(add2(10))
y| called add2(10)
y| returned 12 from add2(10) in 0.000548 seconds
12
```

The `decorator` attribute is also required when using `y()` as a decorator
witb *fast disabling* (see below).
```
y.enabled([])
@y()
def add2(x):
    return x + 2
```
would fail with`TypeError: 'NoneType' object is not callable`, but
```
y.enabled([])
@y(decorator=True)
def add2(x):
    return x + 2
```
will run correctly.


## context_manager / cm
Normally, an ycecream instance can be used as to show values, as a decorator and as a
context manager.

However, when used from a REPL the usage as a context manager can't be detected properly and in that case,
specify `context_manager=True`. E.g. 
```
>>>with y(context_manager=True)
>>>    pass
y| enter
y| exit in 0.008644 seconds
```

The `context_manager` attribute is also required when using `y():` as a context manager
with *fast disabling* (see below).
```
y.enabled([])
with y:
    pass
```
would fail with `AttributeError: __enter__`, but
```
y.enabled([])
with y(context_manager=True):
    pass
```
will run correctly.

## provided / pr
If provided is False, all output for this call will be suppressed.
If provided is True, output will be generated as usual (obeying the enabled attribute).

```
x = 1
y("should print", provided=x > 0)
y("should not print", provided=x < 0)
```
This will print
```
should print
```

# Return a string instead of sending to output

`y(*args, as_str=True)` is like `y(*args)` but the output is returned as a string instead
of written to output.

```
from ycecream import y
hello = "world"
s = y(hello, as_str=True)
print(s, end="")
```
prints
```
y| hello: 'world'
```

Note that if enabled=False, the call will return the null string (`""`).

# Disabling ycecream's output

```
from ycecream import y
yd = y.fork(show_delta=True)
y(1)
yd(2)
y.enabled = False
y(3)
yd(4)
y.enabled = True
y(5)
yd(6)
print(y.enabled)
```
prints
```
y| 1
y| delta=0.011826 ==> 2
y| 5
y| delta=0.044893 ==> 6
True
```
Of course `y()` continues to return its arguments when disabled, of course.

It is also possible to suppress output with the provided attribute (see above).

## Speeding up disabled ycecream
When output is disabled, either via `y.configure(enbabled=False)` or `ycecream.enable = False`,
ycecream still has to check for usage as a decorator or context manager, which can be rather time
consuming.

In order to speed up a program with disabled ycecream calls, it is possible to specify
`y.configure(enabled=[])`, in which case `y` will always just return
the given arguments. If ycecream is disabled this way, usage as a `@y()` decorator  or as a `with y():`
context manager will raise a runtime error, though. The `@y` decorator without parentheses will
not raise any exception, though.

To use `y` as a decorator and still have *fast disabling*:
```
y.configure(enabled=[])
@y(decorator=True):
def add2(x):
     return x + 2
x34 = add2(30)
```
And, similarly, to use `y` as a context manager  combined with *fast disabling*:
```
y.configure(enabled=[])
with @y(context_manager=True):
    pass
```

The table below shows it all.
```  
-------------------------------------------------------------------------------
                         enabled=True   enabled=False                enabled=[]
-------------------------------------------------------------------------------
execution speed                normal          normal                      fast     
y()                            normal       no output                 no output
@y                             normal       no output                 no output
y(decorator=True)              normal       no output                 no output
y(context_manager=True)        normal       no output                 no output
@y()                           normal       no output                 TypeError
with y():                      normal       no output  AttributeError/TypeError
y(as_str=True)                 normal             ""                         ""
-------------------------------------------------------------------------------
```

# Using ycecream as a substitute for `assert`

Ycecream has a method `assert_` that works like `assert`, but can be enabled or disabled with the enabled flag.

```
temperature = -1
y.assert_(temperature > 0)
```
This will raise an AttributeError.

But
```
y.enabled = False
temperature = -1
y.assert_(temperature > 0)
```
will not.

Note that with the attribute propagation method, you can in effect have a layered assert system.

# Interpreting the line number information

When `show_line_number` is True or y() is used without any parameters, the output will contain the line number like:
```
y| #3 ==> a: 'abcd'
```
If the line resides in another file than the main file, the filename (without the path) will be shown as well:
```
y| #30[foo.py] ==> foo: 'Foo'
```
And finally when used in a function or method, that function/method will be shown as well:
```
y| #456[foo.py] in square_root ==> x: 123
```
The parent function can be suppressed by setting `show_line_number` or `sln` to `"n"` or `"no parent"`.

# Configuring at import time

It can be useful to configure ycecream at import time. This can be done by providing a `ycecream.json` file which
can contain any attribute configuration overriding the standard settings.
E.g. if there is an `ycecream.json` file with the following contents
```
{
    "o": "stdout",
    "show_time": true,
    "line_length": 120`
    'compact' : true
}
```
in the same folder as the application, this program:
```
from ycecream import y
hello = "world"
y(hello)
```
will print to stdout (rather than stderr):
```
y| @ 14:53:41.392190 ==> hello: 'world'
```
At import time the sys.path will be searched for, in that order, to find an `ycecream.json` file and use that. This mean that 
you can place an `ycecream.json` file in the site-packages folder where `ycecream` is installed to always use
these modified settings.

Please observe that json values are slightly different from their Python equivalents:
```
-------------------------------
Python     json
-------------------------------
True       true
False      false
None       none
strings    always double quoted
-------------------------------
```
Note that not-specified attributes will remain the default settings.

For obvious reasons, it is not possible to specify `serialize` in an ycecream.json file.

# Working with multiple instances of y

Normally, only the `y()` object is used.

It can be useful to have multiple instances, e.g. when some of the debugging has to be done with context information
and others requires an alternative prefix.

THere are several ways to obtain a new instance of ycecream:

*    by using `y.new()`
     
     With this a new ycecream object is created with the default attributes
     and possibly ycecream.json overrides.
*    by using `y.new(ignore_json=True)`

     With this a new ycecreamobject is created with the default attibutes. Any ycecream.json files asre ignored.
*    by using `y.fork()`
     
     With this a new ycecream object is created with the same attributes as the object it is created ('the parent') from. Note that any non set attributes are copied (propagated) from the parent.
*    by using `y.clone()`, which copies all attributes from y()

     With this a new ycecream object is created with the same attributes as the object it is created ('the parent') from. Note that the attributes are not propagated from the parent, in this case.

*    with `y()` used as a context manager
    
In either case, attributes can be added to override the default ones.

### Example
```
from ycecream import y
y_with_line_number = y.fork(show_line_number=True)
y_with_new_prefix = y.new(prefix="==> ")
y_with_new_prefix_and_time = y_with_new_prefix.clone(show_time=True)
hello="world"
y_with_line_number(hello)
y_with_new_prefix(hello)
y_with_new_prefix_and_time(hello)
y.equals_separator = " == "  # this affects only the forked objects
y_with_line_number(hello)
y_with_new_prefix(hello)
y_with_new_prefix_and_time(hello)
with y(prefix="ycm ") as ycm:
    ycm(hello)
    y(hello)
```
prints
```
y| #6 ==> hello: 'world'
==> hello: 'world'
==> @ 09:55:10.883732 ==> hello: 'world'
y| #10 ==> hello == 'world'
==> hello: 'world'
==> @ 09:55:10.910717 ==> hello: 'world'
ycm enter
ycm hello == 'world'
y| hello == 'world'
ycm exit in 0.017686 seconds
```

## ignore_json
With `y.new(ignore_json=True)` an instance of y without having applied any json configuration file will be returned. That can be useful when guaranteeing the same output in several setups.

### Example
Suppose we have an `ycecream.json` file in the current directory with the contents
```
{prefix="==>"}
```
Then
```
y_post_json = y.new()
y_ignore_json = y.new(ignore_json=True)
hello = "world"
y(hello)
y_post_json(hello)
y_ignore_json(hello)
```
prints
```
==>hello: 'world'
==>hello: 'world'
y| hello: 'world'
```

# Test script

On GitHub is a file `test_ycecream.py` that tests (and thus also demonstrates) most of the functionality
of ycecream.

It is very useful to have a look at the tests to see the features (some may be not covered (yet) in this readme).

# Using ycecream in a REPL

Ycecream may be used in a REPL, but with limited functionality:
* all arguments are just presented as such, i.e. no left-hand side, e.g.
  ```
  >> hello = "world"
  >>> y(hello, hello * 2)
  y| 'hello', 'hellohello'
  ('hello', 'hellohello')
  ```
* line numbers are never shown  
* use as a decorator is only supported when you used as `y(decorator=True)` or `y(d=1)`
* use as a context manager is only supported when used as `y(context_manager=True)`or `y(cm=1)`

# Alternative to `y`

Sometimes, it is not suitable to use the name y in a program, e.g. when
dealing with coordinates x, y and z.

In that case, it is possible to use yc instead
```
from ycecream import yc
```
The `yc` object is a *fork* of y with the prefix `"yc| "`. That means that attributes of `y` are propagated to `yc`, unless overridden.

Of course, it is also possible to use
```
from ycecream import y as yy
```
or
```
yy = y.new()
```
or
```
yy = y.new(prefix="yy| ")
```

# Alternative installation

With `install ycecream from github.py`, you can install the ycecream.py directly from GitHub to the site packages (as if it was a pip install).

With `install ycecream.py`, you can install the ycecream.py in your current directory to the site packages (as if it was a pip install).

Both files can be found in the GitHub repository (https://github.com/salabim/ycecream).


# Limitations

It is not possible to use ycecream:
* from a frozen application (e.g. packaged with PyInstaller)
* when the underlying source code has changed during execution

# Implementation details

Although not important for using the package, here are some implementation details:
* ycecream.py contains the complete source of the asttokens and executing packages, in
   order to offer the required source lookups, without any dependencies
* ycecream.py contains the complete source of pprint as of Python 3.8 in order to support the sort_dicts parameter, Under Python 2.7 this is ignored and the pprint module
from the standard library is used.
* in order to support using y() as a decorator and a context manager, ycecream caches the complete source of
any source file that uses y()


# Acknowledgement

The **ycecream** pacakage is inspired by the **IceCream** package, but is a 
nearly complete rewrite. See https://github.com/gruns/icecream

Many thanks to the author Ansgar Grunseid / grunseid.com / grunseid@gmail.com .

# Differences with IceCream

The ycecream module was originally a fork of IceCream, but has many differences:

```
----------------------------------------------------------------------------------------
characteristic                    ycecream                 IceCream
----------------------------------------------------------------------------------------
platform                          Python 2.7, >=3.6, PyPy  Python 2.7, >=3.5, PyPy
default name                      y (or yc)                ic
dependencies                      none                     many
number of files                   1                        several
usable without installation       yes                      no
can be used as a decorator        yes                      no
can be used as a context manager  yes                      no
can show traceback                yes                      no
PEP8 (Pythonic) API               yes                      no
sorts dicts                       no by default, optional  yes
supports compact, indent and
depth parameters of pprint        yes                      no
use from a REPL                   limited functionality    no
external configuration            via json file            no
observes line_length correctly    yes                      no
benchmarking functionality        yes                      no
suppress f-strings at left hand   optional                 no
indentation                       4 blanks (overridable)   dependent on length of prefix
forking and cloning               yes                      no
test script                       pytest                   unittest
colourize                         no                       yes (can be disabled)
----------------------------------------------------------------------------------------
*) sort_dicts and compact are ignored under Python 2.7

![PyPI](https://img.shields.io/pypi/v/ycecream) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ycecream) ![PyPI - Implementation](https://img.shields.io/pypi/implementation/ycecream)

![PyPI - License](https://img.shields.io/pypi/l/ycecream) ![Black](https://img.shields.io/badge/code%20style-black-000000.svg) 
 ![GitHub last commit](https://img.shields.io/github/last-commit/salabim/ycecream)

If you like ycecream <a href="https://www.buymeacoffee.com/ruudvanderham" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-red.png" alt="Buy Me A Coffee" height="25" width="120"></a>