### changelog | salabim | discrete event simulation

#### version 25.0.15  2025-07-20

- Bug with Component.activate() in yielded  mode fixed.

#### version 25.0.14  2025-07-11

- Upon calling `Environment.snapshot()`, the snapshot was taken at the animation time t() instead of at now(). From this version on, the snapshot is taken at t=now(), as documented.
- Bug when a font size of (nearly) 0 was specified. In that case, a ValueError was raised. Fixed.
  (thanks to a bug report by Heinz Ranja) 

#### version 25.0.13  2025-07-07

- Bug in `Component.activate()` prevented using extra keyword arguments in yieldless mode. Fixed.
  (thanks to a bug report by Ben Moverley Smith)
- Instead of testing for `xlwings`, salabim now tests for `pyodide` to conclude that a model runs under *pyodide*. Related to that are several messages that now refer to pyodide rather than xlwings. This makes it possible to use salabim under PyScript (and other pyodide based platforms) as well.

#### version 25.0.12  2025-07-05

- Bug prevented any animation under Pythonista. Fixed.

####  version 25.0.11  2025-07-02

* With this version, it is possible to use `screen_coordinates=False` (again) for `AnimateQueue` and `AnimateMonitor`. The animation will correctly follow the zooming and panning if screen_coordinates is False.
  Related to this change is that the `Component.animation_objects` *may* now have a parameter `screen_coordinates`, which will be set to the `screen_coordinates` parameter of the  AnimateQueue call (default True) if called. Please note that defining this parameter is optional.

  The default `Component.animation_objects()` method now reads:

  ```
      def animation_objects(self, id: Any, screen_coordinates: bool = True) -> Tuple:
          size_x = 50
          size_y = 50
          ao0 = AnimateRectangle(
              text=str(self.sequence_number()), textcolor="bg", spec=(-20, -20, 20, 20), linewidth=0, fillcolor="fg", screen_coordinates=screen_coordinates
          )
          return (size_x, size_y, ao0)
  ```

####  version 25.0.10  2025-07-01

* With this version it is possible to zoom in and out 2D animations. This can be done with the scroll wheel of the mouse. 
  It is now also possible to pan the 2D animation by pressing the left mouse button and moving the mouse in any direction.
  Note that animation objects that are specified with `screen_coordinates=True` will not be zoomed or panned.
* `AnimateQueue` and `AnimateMonitor` are now always executed with `screen_coordinates=True` (and the parameter `screen_coordinates` is even not defined anymore) .
  It is highly recommended to always define all animation objects in `Component.animation_objects()` with `screen_coordinates=True` as otherwise zooming and panning might not work as expected.

####  version 25.0.9  2025-05-08

* Salabim can now also be run from within Excel with `xlwings lite`. That means that it is now possible to distribute models and have the user run a model without even installing Python or any module!
  If run within Excel, models have to be yielded (yieldless=False), which is the default if run under xlwings, anyway.
  Also, only blind animation is supported (and is True by default if run under xlwings lite). Animated video files can only be written to the pyodide file system. In order to make these pyodide files available to the local file system, you can use the xlwings_utils module (see www.salabim.org/xlwing_utlls) to copy these to a Dropbox file.
  
* The nice thing about running a salabim model in Excel is that you can build input sheets specifying a scenario easily and run the model with that scenario straight from that sheet. Then, place the output on either the same sheet or another sheet (including matplotlib/seaborn graphs, etc.).
  
  I intend to add a section on this in the documentation. Stay tuned.
  
* Special features for Microsoft's PythonInExcel, Anaconda's Anaconda Code and PyDroid3 are now deprecated. 

####  version 25.0.8  2025-03-29

* The yieldless mode memory leak solution as introduced in version 25.0.5 did not work properly. Therefore, the method `Environment.cancel_all()`
  has been removed.
  (thanks to a bug reported by Michiel Luyken)

####  version 25.0.7  2025-03-19

* Bug in the internal Monitor._xweight() method for non level monitors, made that sometime ex0=True in several monitor methods was ignored. Fixed.
  (thanks to a bug report by Lukas Hollenstein)

####  version 25.0.6  2025-03-17

* Bug in the overlapping parameter check of the `process` method, as introduced in version 25.0.5 fixed.

####  version 25.0.5  2025-03-15

* If a `setup` method of any salabim object (Component, Queue, Resource, ...) had any parameter that was also used in the `__init__` method, that parameter was already 'consumed' and caused an error that might be confusing.
  From this version, salabim checks if this is the case and, if so, raises a much more clear `TypeError`.

* If a `process` method of a Component had any parameter that was also used in the `__init__` or `setup` method,
  that parameter was already 'consumed' and caused an error that might be confusing. 
  From this version, salabim checks if this is the case and, if so, raises a much more clear `TypeError`.

####  version 25.0.3  2025-01-24

* Bug in Component.from_store with a filter fixed.
  (thanks to a bug report by  董江成 and Lukas Hollenstein)

####  version 25.0.2  2025-01-18

* Bug in Component.wait() fixed.
  (thanks to a bug report by Thomas Müller)

#### version 25.0.1  2025-01-17

* A bug prevented salabim to run under Python <3.13. Fixed.

#### version 25.0.0  2025-01-15

* Component.enter() now has an optional priority parameter. If the priority parameter is omitted, the component will enter at the tail of the queue, 
  while setting the sorting parameter to the value of the value of the priority of the tail component
  
* Queue.add() and Queue.append() now have an optional priority parameter (like Component.enter())

* Component.to_store() now has an optional request_priority parameter specifying in which order component will enter the requesters queue.

* Component.from_store() now has an optional request_priority parameter specifying in which order component will enter the requesters queue.

* Component.request() now has an optional request_priority parameter specifying in which order component will enter the requesters queue.
  If a priority is specified with the resource spec, this parameter is ignored.
  
* Component.wait() now has an optional request_priority parameter specifying in which order component will enter the waiters queue.
  If a priority is specified with the state spec, this parameter is ignored.
  
* The docstrings and the documentation now explicitly indicate that a priority should be float (although other types might work as well)  

* Internal change: Component.request() and Component.wait() now explicitly specify keyword arguments rather than popping from kwarg

* AnimateText (and text in other Animatexxx classes), now support ANSI color escape sequences. This makes it possible to change color in the same call to AnimateText (et al). Note that salabim only support foreground colors.
  In order to facilitate the build up of ANSI escape sequences, salabim has a class ANSI that can be used as sim.ANSI.red, sim.ANSI.dark_blue, etc. Supported colors are sim.ANSI.black, sim.ANSI.white, sim.ANSI.red, sim.ANSI.green, sim.ANSI.blue, sim.ANSI.cyan, sim.ANSI.magenta, sim.ANSI.yellow, sim.ANSI.dark_black, sim.ANSI.dark_white, sim.ANSI.dark_red, sim.ANSI.dark_green, sim.ANSI.dark_blue, sim.ANSI.dark_cyan, sim.ANSI.dark_magenta  and sim.ANSI.dark_yellow. To reset to the textcolor, use sim.ANSI.reset.
  E.g. 
  
  ```
  sim.AnimateRectangle(
      (0, 0, 260, 40),
      x=100,
      y=100,
      text=f"{sim.ANSI.blue}blue{sim.ANSI.white}blanc{sim.ANSI.red}rouge",
      fillcolor="black",
      text_anchor="sw",
      fontsize=40,
  )
  ```
  
  will put this image on the animation canvas:
  
  <img src="https://www.salabim.org/bleublancrouge.png"> 


- salabim used to apply a correction algorithm for fixing a Pillow bug that made characters (sometimes) look 'shadowed'. Apparently Pillow has fixed that bug now, so the special code has been removed from the salabim code base. This results in faster rendering of texts.
- Bug in Component.wait() with a specified priority fixed.

#### version 24.0.18  2024-12-22

* Component now has a method `reset_monitors()`, which can be useful to prevent keeping statistics of the status and mode monitors. Apart from disabling monitoring completely, it is also possible to use stats_only.
  Note that this functionality was already available for Queue, Store, Resource and State.

  So by issuing  `reset_monitors(False)` in the setup of all components, queues, stores, resources and states, memory consumption may be considerably less.

  (inspired by a remark by 董江成 and a comment by Lukas Hollenstein)

#### version 24.0.17  2024-11-19
- Bug in wait evaluation testing with all=True fixed.
  (Inspired by a bug report by Marko Djogatovic)

#### version 24.0.16  2024-11-14
- Bug in `Component.interrupt()` prevented interrupted components to be interrupted (and thus increasing the interrupt level). Fixed. The docstring has been changed to reflect this fix.
  (Inspired by a comment by Michiel Luyken)
  
- Transparent videos (.gif and .webp) were actually saved as non transparent. Fixed.
- A bug in Pillow under Python 3.13 made it impossible to save animated gif/webp videos. Salabim now detects the problem and, if found, saves file non transparent. Hopefully, this will be fixed in an upcoming version of Pillow for Python 3.13.

#### version 24.0.15  2024-10-30
- Introduced `Environment.minimized` method, which can be useful for real-time simulation without showing an animation window:
```
  minimized

  Parameters
  ----------
  value : bool
      if True, minimize the curent animation window
      if False, (re)show the current animation window
      if None (default): no action

  Returns
  -------
  current state of the animation window : bool
      True if current animation windows is minimized
      False otherwise
```

- Realtime simulation is now covered in section Miscellaneous/Realtime simulation of the documentation.

- The changelog for version 24.0.14 mentioned a new way of installing 3D support for Python 3.13. The instructions
  have been changed (again) and the result is a more stable and better documented installation. Refer to the Overview
  section of the documentation for details.


#### version 24.0.14  2024-10-22
- `sim.AnimateImage` has a new parameter: height. So, the image can be scaled according to the
  height, rather than the width. If both width and height are specified, the aspect ratio might not be the same as the original image.

- `sim.Animate` now has two new parameters: height0 and height1. See above.

- The method `Pdf` is now available also under the name `Pmf` (probability mass function), which is technically more correct. 
  Also, `CumPdf` is now available under the name `CumPmf` (cumulative probability mass function). The manual is updated accordingly.
  (Inspired by a comment by Cahyadi Nugraha)

- If either `Environment.width` or `Environment.height` was a float, some animation methods did not work properly. Fixed.

- When rendering an animation to video, pasting frames could make the program crash sometimes. Fixed.

- Explicit test whether OpenGL supports glut introduced. Explicit test for availabity of pyglet (required for pywavefront) introduced.

- Not so much a change in salabim itself: 
  A version of OpenGL (PyOpenGL) which supports glut (required for 3D salabim animations)
  can now be pip installed: `pip install OpenGL-glut` (Windows Intel/AMD 64 bit only!).
  This makes running 3D animations under Python 3.13 possible and 
  installation for other Python versions much easier. The documentation is updated with this information.
  Also, from now on the documentation recommends installing an even older version of pyglet: `pip install pyglet==1.4.0`  

#### version 24.0.13  2024-09-23
- sim.ComponentGenerator can now also be used with a number of moments:

```
  sim.ComponentGenerator(Ship, moments=(10, 20, 50))
```
  This will generate Ships at t=10, t=20 and t=50. The times should be specified in the current time unit.
  The moments do not have to be sorted.

  Note that moment cannot be used together with at, delay, till,duration, number, iat,force_at, force_till, disturbance or  equidistant

- This version introduces a new class: Event. This is a specialized Component, that is most useful as a timer, which performs
  some action after a certain time. E.g.:
  ```
  class Client(sim.Component):
      def process(self):
          timer = sim.Event(action= lambda: self.activate(), name='timer', delay=10)
          self.hold(sim.Uniform(0,20))
          timer.cancel()  # this can be done even is the action was taken and timer is a data component
          if timer.action_taken():
              print("balked, because I had to wait for 10 minutes")      
              return
          print("do stuff ...")
  ```
   For more information, see the section on events and the reference in the latest documentation.
  
- Canceling a data component does not result in an exception anymore. This can be useful to cancel a wake up event even if it
  it already ended.
  
- When reading a font file, the fontfile was not closed, thus causing a warning message if run under Viktor.ai. Fixed.
  (Inspired by a comment by Michiel Luyken)

#### version 24.0.12  2024-08-27

- Using the `fill` parameter of `sim.Store` resulted in an error. Fixed.
- Alternative way of testing for running under *AnacondaCode*
- captured_stdout` is now cleared with a `sim.reset()` call, which is particularly useful for running under *AnacondaCode* and Pythonista
- Under *PythonInExcel* and *AnacondaCode*, `yieldless` is now False by default (as under *Pythonista*).

#### version 24.0.11  2024-08-18

- salabim can now also run (including .gif video creation) under *AnacondaCode* (Excel extension). The functionality is essentially 
the same as running under *PythonInExcel*.

#### version 24.0.10  2024-08-06

- When PySimpleGUI was installed with
  ```pip install PySimpleGUI-4-Foss```

  sometimes an error occurred. Fixed.  
  
- In version 24.0.9 the dynamic argument could be already object, but was not documented.
  If the value of the parameter is `object` , this refers to the animation object itself. So, we can say

  ```
  sim.AnimateText(text="Hello", x=lambda t: t * 10, y=lambda t, me=object: me.x(t))
  ```

  It is also possible now to specify arg=object  for completeness:

  ```
  sim.AnimateText(text="Hello", x=lambda t: t*10, y=lambda arg, t: arg.x(t), arg=object)
  ```
  
- If a user had forgotten to initialize the environment  (with `env = sim.Environment()`), a rather cryptic AttributeError was raised, From now on a meaningful ValueError will be raised instead:

  `ValueError: no default environment. Did yout forget to call sim.Environment()?` 

- When slicing a monitor in animate mode, the slice ended at `env.now()` rather than `env.t()`, thus making *running averages* in an animation difficult (or incorrect). 
  
- When slicing a non level monitor in animate mode, an error was raised if there were no entries (yet). Fixed.

#### version 24.0.9  2024-06-30

- The image parameter of `AnimateImage` can now can also be an image in a zip archive. In order to specify that, use the name of the zipfile, followed by a bar (|) and the name of the file in the zip archive. So, for instance
  `AnimateImage("cars.zip|bmw.png")`

- Dynamic attributes for anaimation objects can now b expressed differently.
  The advanced section of the Animation chapter in the manual mentions says:

  > The various classes have a lot of parameters, like color, line width, font, etc.
  >
  > These parameters can be given just as a scalar, like:
  >
  > ```
  > sim.AnimateText(text='Hello world', x=200, y=300, textcolor='red')
  > ```
  >
  > But each of these parameters may also be a:
  >
  > - function with zero arguments
  > - function with one argument being the time t
  > - function with two arguments being ‘arg’ and the time t
  > - a method with instance ‘arg’ and the time t
  >   
  
  Although not properly documented, It was always possible to add keyword arguments provided `arg` and `t` were specified:
  
  ```
  for n in range(4):
      AnimateText(text=lambda arg, t, n=n: self.message[n], y=n * 30)
  ```
  
  From this version on, it also possible to leave out `arg` and `t` in this case:
  
  ```
  for n in range(4):
      AnimateText(text=lambda n=n: self.message[n], y=n * 30)
  ```
  
  If the time parameter is required in this case, `env.t()` can be used.
  
  The `arg` parameter is not used at al in this specification. 
  
  > [!TIP]
  >
  > It is strongly recommended to try and use this new specification as it is more intuitive.

#### version 24.0.8  2024-06-26

- Bug in `Component.wait()` in *yieldless* mode caused a process to come to a standstill if the wait condition was met immediately. Fixed.

#### version 24.0.7  2024-06-25

- In initializing Environment, it is now possible to directly present parameters for `Environment.animation_parameters`, e.g.

  ```
  env = sim.Environment(trace=True, animate=True, speed=5)
  ```

  is equivalent to

  ```
  env = sim.Enviroment(trace=True)
  env.animation_parameters(animate=True, speed=5)
  ```

  or

  ```
  env = sim.Enviroment(trace=True)
  env.animate(True)
  env.speed(5)
  ```

  This can make code a bit smaller and more readable.

- Using a Path object as the spec parameter for `Environment.AnimateImage()`raised an error. Fixed.

#### 24.0.6  2024-06-20

From this version on,  the monitor associated with a state (`State.value`) has a `value` property. In previous version only `_value` was supported.

So now, we can say

  ```
mystate.value.value += 1
  ```

as an alternative to

```
my_state.set(my_state() + 1)
```

#### version 24.0.5  2024-05-16

- When merging monitors, all monitors had to be of the same type. 
  From this version on, that's not required anymore.
  (Inspired by a comment by Yin Chi Chang)

- The *Monitor.as_dataframe()* now has additional parameters (in line with methods *Monitor.xt()* and *Monitor.tx()*):
  
```
  ex0 : bool
          if False (default), include zeroes. if True, exclude zeroes

  exoff : bool
      if False (default), include self.off. if True, exclude self.off's
      non level monitors will return all values, regardless of exoff

  force_numeric : bool
      if True (default), convert non numeric tallied values numeric if possible, otherwise assume 0
      if False, do not interpret x-values, return as list if type is list

  add_now : bool
      if True (default), the last tallied x-value and the current time is added to the result
      if False, the result ends with the last tallied value and the time that was tallied
      non level monitors will never add now
      if now is <= last tallied value, nothing will be added, even if add_now is True
```

  Note that `add_now` is True by default, whereas in salabim <= 24.0.4 now was not added.
  (Inspired by a comment by Yin Chi Chang)

- Bug in `Environment.getfontsize_to_fit` fixed.

- Bug when in `Resource.release()` with an anonymous resource fixed.

- From this version the changelog is not anymore a .txt file, but a markdown (.md) file. This allows for more clear explanations. You can find the file changelog.md in the GitHub repo. Alternatively, the rendered changelog is available on www.salabim.org/changelog.html

#### Older versions

  ```
version 24.0.4  2024-05-03
==========================

Although there's no functional change, this is a major upgrade,
that could result in bugs or unexpected behaviour.
Please report any bug or problem.

Internal organization completely changed. Now uses git for version
control. That means that it is much easier for the developer
to push new versions.

And for publishing on PyPI salabim now uses a pyproject.toml file.
This also makes publishing easier for the developer.

Changed the styling of the salabim logo, which will be visible on the
website, readme, manual, etc.
Also the Environment.modelname() method now shows the new styling.

version 24.0.2  2024-03-15
==========================

Added functionality (0)
-----------------------

Salabim now also supports rounded rectangles, which can result in more pleasing animations.

Therefore, the spec argument (tuple) of sim.AnimateRectangle now has an optional fifth item, 
which is the radius of the corners of the rounded rectangle.

The same holds for the rectangle0 and rectangle1 (tuple) parameters of sim.Animate.

Note that if the radius is too big, the radius will be adjusted.

Changed functionality (0)
-------------------------

Under Pythonista, yieldless is False by default, now.
This can be useful for models which have no active components (and just env.run() statements).

Bug fix (0)
-----------

In version 23.3.12 the naming of components, queues, etc. was changed.
Unfortunately, the role of , and . at the end of the name were swapped.
From this version, the naming/sequence number system works again as intended and documented. So
    for i in range(3):
        car = Car('Audi.')
        print(car.name(), car.sequence_number())
    for i in range(3):
        car = Car('BMW,')
        print(car.name(), car.sequence_number())

will now (again) result in:
    Audi.0 0
    Audi.1 1
    Audi.2 2
    BMW.1 1
    BMW.2 2
    BMW.3 3

Bug fix (1)
-----------

Under PyPy yieldless did not work properly. Fixed.

Clarification (0)
-----------------

The salabim documentation states that models could run much faster under PyPy.
("We have found 6 to 7 times faster execution compared to CPython.")

In practice, the performance gain is much smaller. It is not uncommon that
models run even slower under PyPy!
Therefore, the paragraph about PyPy has been removed from the documentation.

(Inspired by a comment by Luc van den Brink)

Clarification (1)
-----------------

For the alternative UI the package PySimpleGUI is required.
Just recently, PySimpleGUI has changed its license to a more restrictive one.
And for commercial applications, charges apply.
If you want to use the real open-source version (which I recommend), please install
PySimpleGUI with
    pip install PySimpleGUI==4.60.5
of course, this version is not maintained any more, but the package is rather stable.

I have also cloned the old PySimpleGUIfile repository to salabim, so you can just 
copy pysimplegui.py (the only required file) from that repo to your model folder.

This information is also added to the documentation.

version 24.0.1  2024-01-11
==========================

New functionality (0)
---------------------

The method Environment.ui_granularity has been introduced.
With this, it is possible to set the number of simulation steps that have to be
called before _handle_ui_event is called (again).
This can significantly improve performance during simulation with animation off
and the UI shown.
The ui_granularity is 1 at start-up.
It might require some experimentation to find a suitable value:

- too low might result in slow execution
- too high might result in bad responsiveness


Enhancement (0)
---------------

Component.request() needed to have at least one resource specified.
From now on, the request method also works without any resource (tuple) specified. So
    self.request()
is allowed, although it is just a dummy action, like self.hold(0).


Bug fix (0)
-----------

When passing (non-consumed) parameters to the Component.process method, an error was raised in
yieldless mode, so
    class X(sim.Component):
        def process(self, extra):
            print(f"{extra=})
            self.hold(1)
    x = X(extra="extra")
didn't work properly in yieldless mode.
Fixed.


Bug fix (1)
-----------

In yieldless mode, the line number where a component becomes current,
sometimes incorrectly referred to a line in salabim, instead of the user program. Fixed.


Bug fix (2)
-----------

If ComponentGenerator was used with a spread (i.e. no iat) at a time not being 0,
an error was raised. Fixed.


Bug fix (3)
-----------

With blind_animation mode True, video production didn't work in yieldless mode. Fixed.
(Bug reported by max l)

version 24.0.0  2024-01-02
==========================

Added functionality (0)
-----------------------

The parameter 'interrupted' for Component.hold() has been introduced.
With this it is possible to hold a component, and let it go immediately in interrupted state.
This is very useful to simulate breakdowns, where a component should immediately observe
the breakdown state:
     yield self.hold(10, interrupted=machine.mode() == "down")
This functionality would be rather difficult to implement, otherwise.

Note that the parameter 'interrupted' may be also an integer >=1 to denote the interrupt level.


Changed functionality (0)
-------------------------

For stability reasons, Component.interrupt() is from now on only allowed for scheduled components.

Added test (0)
--------------

A common mistake is to test the value of a monitor, like Component.mode or Component.status with
a string or integer.
E.g.
    if comp.status == "passive":
        ...
In this case the test will always fail. Of course it should read:
    if comp.status() == "passive":
        ...

From this version on, testing a monitor against anything else than a monitor will raise
a TypeError.
So, now
    if comp.status == "passive":
        ...
will show:
    TypeError: Not allowed to compare Monitor with str . Add parentheses?


version 23.3.13  2023-12-20
===========================

Bug fix (0)
-----------

When calling Component.from_store, the return value was incorrectly None when the request
could be honoured immediately.
Fixed.
(bug reported by Bart van Corven)

Bug fix (1)
-----------

Calling Environment.width() with adjust_x0_x1_y0=True didn't work properly. Fixed.

Bug fix (2)
-----------

Animating an animated gif or webp with AnimateImage(animation_repeat=True) caused a bug. Fixed.

Bug fix (3)
-----------

Calling Resource.release with a non anonymous resource caused an error. Fixed.
(bug reported by Floris Padt) 

version 23.3.12 2023-11-28
===========================

Changed functionality (0)
-------------------------

In order to avoid excessive cache size, the sequence number is not cached anymore
for non-serialized names (those that do not end in "." or ",").
To the user that has the effect that calling sequence_number method on non-serialized
components, queues, monitors, resources, environment and states will always return 1.
In practice that means that:
    man0 = Man(name="man")
    man1 = Man(name="man")
    print(man0.sequence_number(), man1.sequence_number())
will now print
    1 1
,whereas that used to be
    1 2
For 
    man0 = Man()
    man1 = Man()
    print(man0.sequence_number(), man1.sequence_number())
the output is still
    1 2
Internally, neither the base_name nor the sequence_number are stored anymore
for non-serialized names, which reduces the memory footprint (marginally).

The documentation has been updated reflecting this change.

(inspired by an observation by Floris Padt)

Changed functionality (1)
-------------------------

In AnimateImage, a width of 0, resulted in a ValueError, caused by Pillow.
From now on, a width of 0, is accepted, which can be useful for
dynamic sizing of an image. So,
    sim.AnimateImage("my_image.png", width=lambda t: sim.interpolate(t, 0, 10, 1024, 0))
will now result "nothing" after env.t() > 10.

Bug fix (0)
-----------

A bug caused a ValueError when tracing with suppress_trace_linenumbers(True) in yieldless mode. Fixed.
(bug reported by Ben Moverley Smith)

Bug fix (1)
-----------

For some reason, adding audio to a video file didn't work anymore (new version of ffmpeg?).
Fixed by adding the -safe 0 command to the final ffmpeg command.


version 23.3.11 2023-11-14
===========================

Changed functionality (0)
-------------------------

From now on, Monitor.print_statistics and Monitor.print_histogram does not show "no data"
anymore when the number of entries / total weight is zero. This change is made to be
have a more consistent output, which is important when post processing the output string.

In relation to this, histogram_autoscale now also returns 'sensible' values when
there are no entries or the total weight is zero.

Changed functionality (1)
-------------------------

When a component is cancelled, any claimed resources are now automatically released.
This is in line with the termination of a component.
(inspired by Luca Di Gaspero)

Extended functionality (0)
--------------------------

Under Windows, fonts are now also searched in the user/AppData/Local/Microsoft/Windows/Fonts
folder, as fonts are sometimes installed there as well. 

Python in Excel functionality (0)
---------------------------------

In Python in Excel, line numbers are now completely suppressed in the trace.

The test for PythonInExcel has been changed (by testing whether __file__ is in globals())
to be compatible with the new runner functionality.

The file salabim.py now contains the line
    # module = salabim
, to make it compatible with Python in Excel, out of the box.

Bug fix (0)
-----------

A problem with activating a process in yieldless mode fixed.
(Bug reported by bonusguy)

Bug fix (1)
-----------

A bug in Component.cancel() prevented a process to stop correctly in yieldless mode. Fixed.
(Bug reported by Devin Kain)

Bug fix (2)
-----------

A bug in Component.passivate(), Component.standby(), Component.from_store() and Component.to_store()
in yieldless mode.
When called one of these methods were applied on a component that's not current (so not self), the
process of that component stopped incorrectly. E.g.
   other_car.passivate()
Fixed.

Documententation updates (0)
----------------------------

The documentation (both html and pdf) have been updated considerably, mainly as a result of
the preparation of the printed user and reference manual.

Availability of printed user and reference manual (0)
-----------------------------------------------------

Now a printed manual is available from your local Amazon site in two formats:

* full colour premium paper hardcover (ISBN 9798867009403)
* full colour standard paper paperback (ISBN 9798865131472)

Please search for "salabim user and reference manual" on your local Amazon site and you can buy it directly there.


version 23.3.10 2023-10-09 
===========================

Added functionality (0)
-----------------------

Saving
    an animated gif, png or webp file
    a snapshot 
under Python In Excel, now saves an encoded file to sim.pie_result().
The stored result contains the name of the file, so later decoding to a real file is possible.

Also, a file handler b64_file_handler is provided to allow writing to a file
in binary or text mode as an encoded file. This is used internally, but it can be used
by an application as well.

It is also possible to add text to the sim.pie_result() list without
affecting the stored file(s) information.

Note that for the decoding a VBA macro is required.

Changed functionality (0)
-------------------------

Under Python in Excel, blind_animation is enabled by default for a call to Environment().

Changed functionality (1)
-------------------------

If the trace had to show a line in the source of salabim (particularly in ComponentGenerator),
the line numbers were not always displayed correctly and were not very useful
for the trace anyway.
From now on, in that case, no line number will be shown. 

Bug fix (0)
-----------

Label lines in AnimateMonitor / Monitor.animate() were obscured by the fillcolor.
From now on, the line around the frame will be shown over the label lines,
whereas the label lines will be shown over the filled rectangle.

Bug fix (1)
-----------

On Pythonista, the fallback font did not work properly as Pythonista does not support
file handles as the font parameter for PIL.ImageFont. Therefore, on this platform
salabim falls back on the standard Arial font.

Bug fix (2)
-----------

Pause/Resume an animation with <space> didn't work properly. Fixed.
(bug reported by Harald Mutzke)

Type annotation fix (0)
-----------------------

Fixed a wrong type annotation in AnimateSlider.
(flagged by Harald Mutzke)

PyPI/GitHub distribution change (0)
------------------=-----------------

On PyPI salabim now has a meaningful description.
GitHub also has an updated readme.

version 23.3.9  2023-09-18
==========================

New functionality (0)
---------------------

A new context manager sim.capture_stdout(), makes it possible to capture all stdout output.
Unless include_print=False is given, the output *also* goes to the console (as usual).

For example, with
     with sim.capture_stdout():
         env = sim.Environment(trace=True)
all trace output will be printed AND be captured.

With
     with sim.capture_stdout(include_print=False):
         env = sim.Environment(trace=True)
, trace output will not be printed, but still be captured.

The captured output can be retrieved with 
    sim.captured_stdout_as_list() to retrieve it as a list of strings
    sim.captured_stdout_as_str() to retrieve it as a string
    sim.captured_stdout_as_file() to retrieve it in a file (given as a str, Path or file handle)

The first function is particularly useful for Python in Excel.

It is possible to clear the captured_stdout information with
    sim.clear_captured_stdout()

Of course, we can also use env.capture_stdout(), env.captured_stdout_to_list(), etc. instead.

New functionality (1)
---------------------

Salabim can now run under Python in Excel.

This required a change in the line number assessment.
When the line cannot be determined, a question mark will now be used instead.

Note that only blind animation is supported as tkinter is not available under
Python in Excel. 
Although technically salabim supports making an animated Gif under Python in Excel (with
some specialized VBA code), this is not very practical (as of now).

Changed functionality (0)
-------------------------

The salabim code now contains encoded versions of the fonts
    "calibri" / "std" / ""
    "dejavusansmono" / "mono"
    "mplus_1m_regular" / "narrow"
This means that it is not longer required to have the files
    calibri.ttf
    DejaVuSansMono.ttf
    mplus-1m-regular.ttf
installed or available anywhere anymore.
Also, when a font is not found, salabim will fall back to the calibri font.

This makes distributing models without installing salabim simpler.

And it also makes font handling available to models run under PythonInExcel.

Changed functionality (1)
-------------------------

AnimateQueue() / Queue.animate() now has a screen_coordinates parameter that is True by default.
If the animation objects of the components to be shown are in user coordinates, specify screen_coordinates=False.
Actually, this change was already introduced in salabim 23.3.5, but was left out of the changelog of that version.

Bug fix (0)
-----------

The patch in salabim 23.3.5 to support Pillow 10.0.0, did not work under all circumstances.
Fixed.

Bug fix (1)
-----------

Blind animation still required tkinter under some circumstances. Fixed.

Bug fix (2)
-----------

Blind animation video making did not finish when env.run() was specified. Fixed.

Bug fix (3)
-----------

AnimateMonitor() / Monitor.animate() label lines did not observe the xy_offset parameter. Fixed.
AnimateMonotor() / Monitor.animate() label lines could 'override' the surrounding rectangle. Fixed.

Bug fix (4)
-----------

AnimateText did not observe the offsetx and offsety parameter correctly. Fixed.

version 23.3.8  2023-09-05
==========================

Enhanced UI functionality (0)
-----------------------------

The UI window layout has been changed to be more useful with
narrower windows.
Some more updates to the appearance.

When the UI is started, the time in the animation window is no longer disabled.
The user can always switch that off with Environment.show_time(False).

Environment.start_ui() now has useful defaults for window_size and window_position.

Environment.start_ui() now has a parameter default_actions, which is True by default.
If False, there are no actions like, pause/go, speed, etc. defined, so the user has to
specify the required actions with the actions parameter.
This is useful to use a different layout or leave out certain elements. Be sure to
use the same keys to be able to use the programmed interactions. However, you
can leave out elements.

It is recommended to use the standard actions as a template:

    [sg.Text("", key="-TIME-", metadata=[1, 2], size=200)],
    [sg.Button("Pause", key="-PAUSE-GO-", metadata=[1, 2]), sg.Button("Stop", key="-STOP-", button_color=("white", "firebrick3"), metadata=[1, 2])],
    [sg.Checkbox("Pause at each step", False, key="-PAUSE-AT-EACH-STEP-", enable_events=True, metadata=[1, 2])],
    [sg.Text(f"Pause at{env.get_time_unit(template='(t)')}", key="-PAUSE-AT-TEXT-", size=17), sg.Input("", key="-PAUSE-AT-", size=(10, 20))],
    [sg.Text(f"Pause each{env.get_time_unit(template='(d)')}", key="-PAUSE-EACH-TEXT-", size=17), sg.Input("", key="-PAUSE-EACH-", size=(10, 20))],
    [
        sg.Text("Speed", key="-SPEED-TEXT-", metadata=[1]),
        sg.Button("/2", key="-SPEED/2-", metadata=[1]),
        sg.Button("*2", key="-SPEED*2-", metadata=[1]),
        sg.Input("", key="-SPEED-", size=(7, 10)),
    ],
    [sg.Checkbox("Trace", env.trace(), key="-TRACE-", metadata=[1, 2], enable_events=True)],
    [sg.Checkbox("Synced", env.synced(), key="-SYNCED-", metadata=[1], enable_events=True)],
    [sg.Checkbox("Animate", True, key="-ANIMATE-", metadata=[1, 2], enable_events=True)],


The simulation did not stop exactly at the time given in 'Pause at'. Fixed.

Added demos (0)
---------------

The program demo_ui.py shows a pretty standard UI with some extra elements.

The program demo_horizontal_ui.py demonstrates the same functionality, but now
with a horizontal UI window. Note that this requires quite a bit more
code than the standard one.
But it demonstrates what is possible.

Bug fix (0)
-----------

Component.to_store_store did not always return the right store. Fixed.
Thanks to Florian Förster for reporting this bug and the fix.

Bug fix (1)
-----------

Store.to_store_requesters() returned the wrong queue. Fixed. 

version 23.3.7  2023-08-22
==========================

Bug fix (0)
-----------

Environment.paused(True) did not call set_start_animation(), which is required. Fixed.

Bug fix (1)
-----------

Removing and showing an animated monitor did not restore the labels and label lines. Fixed. 

version 23.3.6  2023-08-18
==========================

New functionality (0)
---------------------

The parameter datetime0 in Environment(), may now be also a string, which is relatively 
free format as it uses dateutil.parser.parse.
Note that (unless Environment.dateutil_parse is overridden), it is advised to use
Y-M-D format, e.g.
    env = sim.Environment(datetime0="2023-08-17")
Note that for this functionality, dateutil has to be installed, most likely with
    pip install python-dateutil

New functionality (1)
---------------------

The parameter datetime0 in Environment.datetime0(), may now be also a string, which is relatively 
free format as it uses dateutil.parser.parse.
Note that (unless Environment.dateutil_parse is overridden), it is advised to use
Y-M-D format, e.g.
    env.datetime0("2023-08-17")
Note that for this functionality, dateutil has to be installed, most likely with
    pip install python-dateutil
    

New functionality (2)
---------------------

The above functionality uses a method Environment.dateutil_parse, which more or less defaults to 
    def dateutil_parse(self, spec):
        import dateutil.parser
        return dateutil.parser.parse(spec, dayfirst=False, yearfirst=True)

If other values for dayfirst or yearfirst are desired, formulate a custom method, like
    sim.Environment.dateutil_parse = lambda self, spec: dateutil.parser.parse(spec, dayfirst=True, yearfirst=False)

Refer to the Python dateutil.parse documentation for details.

Note that for this functionality, dateutil has to be installed, most likely with
    pip install python-dateutil

Changed functionality (3)
-------------------------

If datetime0 is not False, all process interaction methods that require a time, like Component.hold,
Component creation, fail_at parameters, can now be a datetime.datetime, e.g.
    comp.hold(till=datetime.datetime(year=2023, month=8, day=17))
Or it can be string containing a relatively free format date, like
    comp.hold(till="2023-08_07")
And now it is even possible to use a string:
    comp.hold(till="1000")
    
If datetime0 is not False, all process interaction methods that require a duration, like Component.hold,
Component creation, fail_delay parameters, can now be a datetime.timedelta, e.g.
    comp.hold(datetime.timedelta(hours=1)
    Vehicle(delay=datetime.timedelta(days=2))
Or it can be string containing a relatively free format duration, like
    comp.hold("12:00:00"))
And now it is even possible to use a string:
    comp.hold("1000")
    
Of course, these parameters can also be a callable, like
    comp.hold(env.Pdf(("12:00", "13:45", "20:30"), 1))
    
Note that this functionality is a by-product of the implementation of the not yet documented, but already
available, UI (using PySimpleGUI) functionality.

New functionality (4)
---------------------

The value of State.value can now be assigned and queried directly. E.g.
    my_state.value.value = 3
    print(my_state.value.value)
is equivalent to
    my_state.set(3)
    print(my_state.get())
This can be useful to increment or decrement a state. E.g.
    my_state.value.value += 5
is equivalent to
    my.state.set(my_state.get() + 5)

The value of Component.mode can now be assigned also like:
    my_component.mode.value = "working"
, instead of
    my_component.set_mode("working")
This can also be useful to increment or decrement a mode. E.g.
    my_component.mode.value += 5
is equivalent to
    my_component.set_mode(my_component.mode() + 5)

Changed functionality (0)
-------------------------

The class Environmnent does not contain a subclass Environment anymore,
so you can't say
    env1 = env.Environment()
anymore. This was never intended to be supported.
Use 
    env1 = sim.Environment()
now.

Compatibility fix (0)
---------------------

When saving a video as .gif, Pythonista required the images2gif module, which has a bug in
the latest version of Pythonista.
As Pythonista has now an updated version of Pillow, saving can and will be done in the same way as
in non Pythonista versions.

version 23.3.5  2023-07-29
==========================

Compatibility update (0)
------------------------

Due to a change in Pillow 10.0.0, salabim did not work properly with that version:

- font.getsize was deprecated. Salabim now uses font.getbbox.
- Image.ANTIALIAS was deprecated. Salabim now uses Image.LANCZOS
  From now on, Pillow >=10.0.0 is also supported.

version 23.3.4  2023-07-26
==========================

Bug fix (0)
-----------

A bug in Component.to_stock() fixed.

version 23.3.3  2023-07-23
==========================

Changed functionality (0)
-------------------------

In order to check whether a model that runs with sim.yieldless(False)
is not a yieldless model, salabim may under rare circumstances report:
    ValueError: process must be a generator (contain yield statements.)
    Maybe this a yieldless model. In that case:
    - remove sim.yieldless(False)
    If it is indeed a yield model, make this process method (and maybe others) into a generator, e.g.
    by adding at the end:
        return
        yield  # just to make this a generator

So when it is indeed a yieldless model, remove the sim.yieldless(False) statement.
If this is a model with yields, change the process method into a generator, e.g. by adding
    yield self.hold(0)  # added to make this process a generator
or
    if False:
        yield  # added to make this process a generator
or (at the end)
    return
    yield  # added to make this process a generator
    

Added functionality (0)
-----------------------

The method Store.to_store_requesters() returns a reference to the to requesters, like
Store.from_requesters() that was already in salabim.
These methods can be very useful for animating a store.
    

Bug fix (0)
-----------

AnimateGrid used 0 and env.width() for the x-range. And 0 and env.height() for the y-range.
This worked fine as long as screen coordinates were the same as user coordinates.
In order to properly work with user coordinates, the x-range should be env.x0() and env.x1()
and the y-range should be env.y0() and env.y1(). Fixed.


version 23.3.2  2023-07-10 
==========================

Bug fix (0)
-----------

Please note that
    When another component than self was used in activate, passivate, hold (or any process interaction)
    it was not possible to use yield. So
        yield other.activate()
    was not executed properly, although it did not raise an (immediate) error.
    From now on, this is accepted, which makes it also easier to translate yieldless models to not yieldless models,
    as the user can just add yield for any process interaction call.
is not valid anymore as the implementation contained a serious bug. Fixed.

To summarize (only relevant for yield versions):
    other.activate(), other.hold(), etc should NEVER be called with as yield other.activate(), yield other.hold(), etc.
    when other is not self!
(bug reported by Michiel Luyken)

version 23.3.1  2023-07-10 
==========================

Bug fix (0)
-----------

As mentioned in the 23.3.0 changelog, yieldless should be True by default.
But yieldless was False. Fixed.
To avoid any confusion: salabim runs now in yieldless mode by default!

Bug fix (1)
-----------

A bug in Component.from_store caused that the component reported failed. Fixed.
(bug reported by Michiel Luyken)

version 23.3.0  2023-07-09 
==========================

Changed default mode (0)
------------------------

From now on, yieldless is the default mode.

For non yieldless (yield) models to run you can

- add sim.yieldless(False), just after import salabim as sim or
- add the yieldless parameter to env = sim.Environment, like
  env = sim.Environment(trace=True, yieldless=False) or
- remove all yield statements or
- run salabim_unyield.py over the required model(s)

The documentation now also defaults to the yieldless version.

Improved functionality in yield mode (0)
----------------------------------------

When another component than self was used in activate, passivate, hold (or any process interaction)
it was not possible to use yield. So
    yield other.activate()
was not executed properly, although it did not raise an (immediate) error.
From now on, this is accepted, which makes it also easier to translate yieldless models to not yieldless models,
as the user can just add yield for any process interaction call.

Related to this is a much more useful error message when a yield model is run in yieldless mode.

Improved documentation (0)
--------------------------

Salabim now has two complete sets of documentation: for yieldless (default) and yield version.
There are also two versions of the pdf documentation.

sample models and sample 3d models (0)
--------------------------------------

The GitHub repository now features the yieldless versions. The non yieldless (yield) versions
end with _yield.

Bug fix (0)
-----------

When a queue element was selected by subscripting, like my_queue[index], None was returned
when the index was out of range. Example my_queue[0] result is None, when my_queue is empty.
This should raise an IndexError. Fixed.
(inspired by a problem reported by Michiel Luyken)


version 23.2.0  2023-07-02
==========================

Completely new way of building processes (0)
--------------------------------------------

With this version comes a completely new way to build processes.
Up to now, a Component's process was essentially a generator with yields to allow
switching to other Components. Those yields are far from natural and often caused
beginners (and sometimes experts) to make mistakes.
And last but not least, if you wanted a specific task to be called as a method,
you had to use 'yield from', which is a confusing concept to say the least.

Therefore, from now on the process interaction may be done with so-called greenlets.
If you specify
    sim.yieldless(True)
prior to any sim.Environment call, salabim works differently, as you can and should
refrain from the yield part.

So,
    def double_hold(self, duration):
        yield self.hold(2 * duration)
    

    def process(self):
        yield self.hold(5)
        while not len(q):
            yield self.passivate()
        other.activate()
        yield from self.double_hold(4)
        item = yield self.from_store(store)

, now reads:
    def double_hold(self, duration):
        self.hold(2 * duration)

    def process(self):
        self.hold(5)
        while not len(q):
            self.passivate()
        other.activate()
        self.double_hold(4)
        item = self.from_store(store)

Wow! So much cleaner.

There's just one caveat: the code might run slower, although in practice not that much.
But that's just a small price for a much cleaner API.

For now, salabim offers both ways of defining processes, where coroutines (with yields) are
still the default. However, that might change in the future. The same holds for the documentation
and sample scripts.

In order to run without yields, you can just do
    sim.yieldless(True)
before calling env = sim.Environment(), or do
    env =  sim.Environment(yieldless=True)
    
Anyway, in that case the greenlet module has to be installed, most likely with:
    pip install greenlet

Note that this yieldless=True functionality is still experimental. Please report any bugs or
strange behaviour.

In order to facilitate the conversion to yieldless=True, there's a script to do just that:
    salabim_unyield.py
, which is a bit more intelligent than just removing the text 'yield' and 'yield from'.       


New functionality (0)
---------------------

The method Component.from_store has a new parameter: key.
If present, it should be function accepting a component and returning a value that can be compared
to others, most likely a number or string.
When applied, the component with the lowest key (and meeting the filter) will be returned, if any.
(inspired by a request of Zhong Zhyu)

New functionality (1)
---------------------

Introduced sim.AnimateGrid/env.AnimateGrid, which can be useful to align animation objects.
The function will draw a grid with a given spacing and add text labels, like:
    env.AnimateGrid(spacing=100, linecolor="blue")
or 
    env.AnimateGrid(spacing=100, linecolor="black", textcolor="black", visible=preview_mode)

(inspired by a request of Michiel Luyken and a reference implementation by Richard)

New functionality (2)
---------------------

From this version, an alternative user interface (UI) via PySimpleGUI is available.
This makes it easier to control animations and simulations via a separate window.

In the new control window the aplication can add widgets, including input, buttons,
radio buttons, sliders, ...

It is now also possible to turn of animation up to a certain time (including
at regular intervals) and regain control.

This feature is not yet documented and still experimental.
However, you can experiment with it. See sample models/demo_ui.py in the github
repository.

Functionality change (0)
------------------------

The attribute Environment.paused is now a method that can be used to set and get the value
of the internal paused status.
This can affect previous models that explicitely wrote or read the attribute env.paused.
This for instance means that
    self.paused = True
has to be changed into
    self.paused(True)
Likewise
    if self.paused:
has to be changed into
    if self.paused():
USERS WHO HAVE PREVIOUSLY USED env.paused SHOULD CHECK AND CHANGE THEIR CODE !

Enhancement (0)
---------------

sim.linspace / env.linspace did not have a default for the num parameter.
From this version on the default is 50 (as in numpy.linspace).

Documentation / docstring update (0)
------------------------------------

The layer parameter for Animatexxx classes was missing in the docstring. Fixed.
Also, a section on Using layers is added to the Animation chapter of the documentation.

Bug fix (0)
-----------

When using sim.Animate(image=) / env.Animate(image=), the animation crashed
because the various new image parameters
    flip_horizontal, flip_vertical, animation_start, animation_speed,
    animation_repeat, animation_pingpong, animation_from and animation_to
were not implemented at all. Fixed.

Bug fix (1)
-----------

When an unexpected keyword was given in any 'step' method (hold, activate, ...),
the process was incorrectly terminated without any warning.
Fixed.

Bug fix (2)
-----------

In AnimateImage, filename that contained // was incorrectly always opened as a URL.
Thus not correctly handling files like C://test//abc.jpg, although these are
valid file names. Fixed.
(Inspired by a problem reported by Harald Mutzke)

Bug fix (3)
-----------

If simulation events happened after the current animation time (env.t()), salabim did
'rewind' the animation time, thus causing unwanted behaviour.
Fixed.
(bug reported by Richard)

version 23.1.4  2023-05-14
==========================

New functionality (0)
---------------------

Introduced sim.full_screen() / env.full_screen() , which
creates a true full screen window, without a title, where
x0=0, y0=0, x1=width of screen
(Inspired by a remark from Lukas Hollenstein)

New parameter (0)
-----------------

The method sim.width() / env.width() now have a second parameter
adjust_x0_x1_y0, which is False by default.
If adjust_x0_x1_y0 is True, apart from setting the width,
x0 will be set to 0, y0 will be set to 0 and x1 will be set to the given width.
E.g.
    env.width(1000, True)

Note that existing programs won't be affected, as the parameter
adjust_x0_x1_y0 is False by default.

New functionality (1)
---------------------

sim.AnimateImage / env.AnimateImage now supports animated GIFs and
animated .webp files.

Therefore, AnimateImage has six new parameters:

- animation_start (simulation) time that the animation should start
- animation_repeat if False (default) no repeat, if True, repeat
- animation_pingpong if False (default) no pingpong, if True, first goes forward then backward
- animation_speed specifies how fast the animation should be (relative to env.speed)
- animation_from specifies the time in the video from which to animate
- animation_to specifies the time in the video to which to animate

Note that these parameters may be specified for non animated images as well,
but will have no meaning, then.
All these parameters are dynamic.

The AnimateImage now has a method duration that returns the duration of the image
(0 if not animated).

Note that animated GIFs and .webp files can have a transparent background,
which makes it ideal for showing moving objects, like vehicles, cranes, animals, etc.

New functionality (2)
---------------------

It is now possible to produce .webp format videos.
E.g.
    with env.video("my_video.webp"):
        env.run(10)

New functionality (3)
---------------------

The class sim.AnimateImage / env.AnimateImage can now be used with
.webp files (still or animated).
E.g.
    env.AnimateImage(image="my_picture.webp")

New functionality (4)
---------------------

The class sim.AnimateImage / env.AnimateImage can now be used also to
animate an image given by a URL. 
Any image parameter that contains // will be opened as a URL.
E.g.
    env.AnimateImage("https://salabim.org/manual/_images/2d1.gif")

New functionality (5)
---------------------

The class sim.AnimateImage / env.AnimateImage now have two new (dynamic)
boolean parameters:

- flip_horizontal
- flip_vertical
  Both parameters are False by default.
  When True, the image is flipped either horizontal or vertical.
  Note that this functionality is also available for animated
  images.
  E.g.
    env.AnimateImage("mypicture.webp", flip_vertical=lambda t: t > 10)

New functionality (6)
---------------------

The new function sim.video_duration() / method env.video_duration() 
will return the length or a given animated GIF/Webp file or URL.
This can be useful in animating a GIF/Webp file or URL.
E.g.
    duration =  env.video_duration("my_video.gif")
    

New functionality (7)
---------------------

ComponentGenerator has a new parameter: at_end. If not specified, no action when the component generator ends.
If a parameterless function is specified, this function will be called when the component generator ends.
The most obvious usage of this is to reactivate main when all components are generated.

    ComponentGenerator(number=10, iat=env.Uniform(1,2), at_end=lambda: env.main().activate())

Performance improvement (0)
---------------------------

When using AnimateImage, all images are now properly cached, which improves
performance under certain conditions.

Support for Pythonista 3.4 (0)
------------------------------

Fixed a problem in the set_aliases routine.

A bug in Pythonista 3.4 makes that the using the Calibri font with fontsize between 12 and 17 crashes the
system. Therefore, on Pythonista, Calibri font is replaced by the Arial font, until the Pythonista bug
is fixed.

Bug fix (0)
-----------

AnimateCombined did not handle a non list animation_objects parameter correctly. Fixed.
(bug reported by Michiel Luyken)

Bug fix (1)
-----------

Animated GIFs could not handle a transparent background color properly. Fixed.

Bug fix (2)
-----------

Under Python 3.10 (Pythonista only?) classes that have no __init__ method, don't seem to have a signature, 
which lead to some problems in the aliasing of globals into Environment. Fixed.

Bug fix (3)
-----------

When using applying a filter for Store.from_store() the wrong component was returned. Fixed.
(bug reported by Martin Kunkel, fix slightly different)

Bug fix (4)
-----------

A bug in _AnimateIntro and _AnimateExtro made that Environment(isdefault_env=False) didn't work properly.
Fixed.
(bug reported by Michiel Luyken)

Bug fix (5)
-----------

Under Pythonista, the simulation time was not animated correctly in unsynced mode. Fixed.

HTML documentation readability enhancement (0)
----------------------------------------------

In the sidebar of the HTML documentation, level 4 items are now shown in a larger font,
which makes it easier to read.
(Inspired by a remark from Michiel Luyken)

version 23.1.3  2023-04-01
==========================

New functionality (0)
---------------------

Introduced two new functions to get the width and height of the screen:
    sim.screen_width() / env.screen_width()
    sim.screen_height() / env.screen_height()
So now it is easy to have a full-screen animation:
    env.width(env.screen_width())
    env.height(env.screen_height())
    env.x1(env.width())
(Inspired by a question by Michiel Luyken)

Improved type hinting (0)
-------------------------

The type hints and docstrings in sim.Environment cover now all 
classes and methods.

Improved type hinting (1)
-------------------------

Component.from_store now also has a type hint ("Component"), so
    c = self.from_store(store)
will show the typing info.
(inspired by a discussion with Lukas Hollenstein)

Docstrings improvement (0)
--------------------------

Docstrings used to contain many |n| characters, which were there
to render the reference section of the documentation.
But, these characters were annoying and did not work out well in
tooltips.
From now on, the docstrings don't contain |n| characters anymore,
and can still be used in the automatic documentation-building process.
(inspired by a discussion with Lukas Hollenstein)

Bug fix (0)
-----------

A minor error in tracing from_store honor / to_store honor fixed.

Bug fix (1)
-----------

Error when honouring a to_store request for multiple stores fixed.

version 23.1.2  2023-03-19
==========================

Added functionality(0)
----------------------

When animating a queue, with a trajectory, it is now possible to specify the
x and y coordinates, which may even be dynamic.
And the trajectory may be dynamic now as well.

It is now documented that for usage in Queue.animate() or AnimateQueue,
t0 should be set to 0 for at least the first segment of a trajectory.

Changed functionality (0)
-------------------------

It is more logical to use urgent=True in calls to Component.from_store and
Component.to_store. Therefore the default value for urgent in these methods
is now True.

Improved type hint handling (0)
-------------------------------

The recently introduced functionality to use env. prefix where sim. prefix
was required (like env.Component instead of sim.Component) did not show the
type hints in IDEs. 
From this version type hints and the docstring will show these correctly.

The consequence of this change is an increase in the size of the source code,
but that shouldn't cause any problems.

Alternative way to initialize a simulation (0)
----------------------------------------------

It is quite common to start an app(lication) with ::

    app = App()

This is now also possible with salabim as sim.App is now just an alias of
sim.Environment. So ::

    app = sim.App(trace=True)
    app.ComponentGenerator(X, iat=app.Exponential(10))
    app.run(app.Uniform(10,20))

is now valid code.

Note that the env parameter in several class definitions has not been changed, though. 
This might not cause too many problems as env= is hardly ever used in practice
(as far as I know).

Bug fix (0)
-----------

If Trajectory.length() was called without a time (t), an exception was raised. Fixed.

Bug fix (1)
-----------

When using sim.ComponentGenerator the default environment was not propagated correctly. Fixed.

Documentation updates (0)
-------------------------

The documentation now makes clear that t0 should be 0 in case a trajectory is
to be used as a trajectory for queue animation.

Documentation updates (1)
-------------------------

The HTML documentation now uses the better legible rtd (Read The Docs) theme.
Also, many additions and changes have been done.

version 23.1.1  2023-03-14
==========================

New functionality (0)
---------------------

The t- and x-values of a monitor (level or non level) can now be saved as
a pandas dataframe, which can be useful for further data analysis.

All you have to do is:
    df = mon.as_dataframe()

When dealing with level monitors, this might not be very useful as 
most analyses assume a uniform (equidistant) t-scale.
Therefore, salabim also offers the possibility to resample the
monitor into a dataframe, like
    df = mon.as_resampled_dataframe(delta_t=1)
Like this, the monitor will be resampled with a frequency of 1 time unit.
The lower delta_t, the more accurately the dataframe follows the real values,
albeit at the cost of a larger dataframe.

It is possible to resample multiple monitors into one pandas dataframe.

See the documentation (Monitor and Reference chapter) for details.

Changed functionality (0)
-------------------------

Considerable change in the implementation and API of stores.

From now a store doesn't *have* a contents queue: It *is* a queue!
This has a lot of advantages. For instance, all normal queue operations
are now also available for stores.

And you can now enter components or take them out, possibly honouring
any pending from_store or to_store.

Note that if the capacity of the store is not inf, the store becomes a
limited capacity queue. That implies that when a component tries to enter
the queue when it is already at its capacity, a ``sim.QueueFullError`` will be raised.

Changing the filter function will now automatically rescan for from_store
honors.
Changing the capacity of a store (with set_capacity will now automatically
rescan for to_store honors), if required.

It is still possible to rescan a store with Store.rescan().

The manual has been updated to reflect the changes.

Changed functionality (1)
-------------------------

The Component.from_store method now supports a very handy way to get the
item (component).
Instead of
    yield self.from_store(store)
    item = self.from_store_item()
you can now say
    item = yield self.from_store(store)

Note that you have to do an assignment! So, something like
    yield self.from_store(store).activate()
or
    print(yield self.from_store(store).name())
is not possible (it is actually a syntax error)

Even with the item = yield self.from_store(store) syntax, you can
query the item with self.from_store_item()

And it is still allowed to use just
    yield self.from_store(store)

The manual has been updated accordingly.

New functionality (0)
---------------------

ComponentGenerator has a new parameter: equidistant.
If equidistant is True, the components will not be randomly distributed over the
given duration, but evenly spread. For instance:
    env.ComponentGenerator(X, at=100, till=200, number=3, equidistant=True)
, will generate instances of X at t=100, t=150 and t=200.

If equidistant is True, iat may not be specified.

Optimization (0)
----------------

The method Component.enter_sorted and Queue.add_sorted now search backwards instead of forward,
which is more efficient in case all components have the same priority, which is not uncommon.

Note (0)
--------

Version 23.1.0 introduced the possibility to use env. instead of sim. in almost all cases.
As mentioned you can't use this construction when defining an inherited class, like
    class Car(env.Component)
This is simply not accepted.

But there is one case, which is not detected and does not work as expected:

    class Car(sim.Component)
        def __init__(self, *args, **kwargs):
            ...
            env.Component.__init__(self,*args, **kwargs) # instead of sim.Component.__init__(self, *args, **kwargs)

The recommended way is:

    class Car(sim.Component)
        def __init__(self, *args, **kwargs):
            ...
            super().__init__(*args, **kwargs) # instead of sim.Component.__init__(self, *args, **kwargs)

version 23.1.0  2023-03-06
==========================

New functionality (0)
---------------------

This version contains a completely new concept that can make modelling
simpler, particularly for job shops, flow, etc.: stores 

A store is essentially a queue (sometimes with limited capacity) that can
hold components.

And we can then request components from the store. If there's a component
in the store, it is returned. But if it is not the requesting component
goes into the requesting state, until something is available in the store.

The same holds for processes putting components in the store: if it
is full, the component that wants to add something to the store goes into
the requesting state. Here we have an unlimited waiting room, though.

Here's the well-known 3 clerk bank sample model with a store:

    # Bank, 3 clerks (store).py
    import salabim as sim


    class CustomerGenerator(sim.Component):
        def process(self):
            while True:
                yield self.to_store(waiting_room, Customer())
                yield self.hold(sim.Uniform(5, 15).sample())


    class Clerk(sim.Component):
        def process(self):
            while True:
                yield self.from_store(waiting_room)
                customer = self.from_store_item()
                yield self.hold(30)


    class Customer(sim.Component):
        ...


    env = sim.Environment(trace=False)
    CustomerGenerator()
    for _ in range(3):
        Clerk()
    waiting_room = sim.Store("waiting_room")


    env.run(till=50000)
    
    waiting_room.contents().print_statistics()
    waiting_room.contents().print_info()

It is possible to specify several stores to get an item from. And likewise,
several stores to put an item.
It is also possible to filter components so to make the requester only get
a certain type of item.

The manual contains a new section on stores, with several examples. See also the
chapter on Modelling.

New functionality (1)
---------------------

From now on every class or function that used to be prefixed with sim.
can also be prefixed with env.

So, for instance:
    q = env.Queue("q")
or
    store = env.Store("store")
or
    env.run(env.inf)

The only place where that is not allowed is for subclassing,
particularly sim.Component. So you still need to say
    class Car(sim.Component):
        ...

Note that explicit setting of env is still possible:
    env.Queue("q", env=env0)
is equivalent to
    sim.Queue("q", env=env0)

Implicit setting of env is handled like
    env0.Queue("q")
is equivalent to
    sim.Queue("q", env=env0)

Support functions, like arange can now also be prefixed with env.
So env.arange(0, 10, 0.5) and sim.arange(0, 10, 0.5) are equivalent. 

Also prefixable with env are env.inf and env.nan and the exceptions.

New functionality (2)
---------------------

Introduced a context manager Environment.suppress_trace that can
be used to temporarily disable trace. After the context manager block,
the trace status returns to the value before. Usage:
    with env.suppress_trace():
        car = sim.Component()
This will never print the trace output for component creation.

Changed functionality (0)
-------------------------

In TrajectoryPolygon, the spline may now also be "" (the null string),
denoting no splining.

Added functionality (0)
-----------------------

In the various print_histogram() print_histograms() a new parameter is
introduced: graph_scale, which represents the number of characters to
show 100% in the graphical representation of % and cum%.
This is particularly useful for (this) documentation.

So, ``m.print_histogram()`` might print:

...
           <=      duration     %  cum%
        0            22.216  22.2  22.2 *****************|
        1            32.485  32.5  54.7 *************************                  |
        2            26.441  26.4  81.1 *********************                                           |
        3            18.858  18.9 100   ***************                                                                 |
          inf         0       0   100                                                                                   |

, whereas ``m.print_histogram(graph_scale=30)`` will result in:

...
           <=      duration     %  cum%
        0            22.216  22.2  22.2 ******|
        1            32.485  32.5  54.7 *********       |
        2            26.441  26.4  81.1 *******                 |
        3            18.858  18.9 100   *****                         |
          inf         0       0   100                                 |
          

Bug fix (0)
-----------

Trajectories did not always work correctly. Fixed.

Bug fix (1)
-----------

If a queue is animated the title should be the name of the queue by default.
In a recent update, the default was set to the null string, though.
Fixed.

Bug fix (2)
-----------

When saving an animated gif, the duration of the video was not always correct.
Particularly at 30 fps (the default), the duration was actually 90% shorter,
because frame durations are always a multiple of 10 ms.
That means that a 30 fps animated gif will be now actually recorded at 33.33 fps
and have the proper duration.
Fixed.

Documentation (0)
-----------------

The changelog is now part of both the online and pdf documentation.
The pdf version is now kept up-to-date (synced with the online docs).

version 23.0.1  2023-02-06
==========================

Annotation (0)
--------------

Salabim has now type hints on all API classes, methods and functions. 
This might help users when using IDEs and other tooling.

Warning (0)
-----------

As this change involved quite a lot of modifications (and some bug fixes),
it is possible that errors were introduced.
Please report any bugs as soon as possible. 

Changed functionality / bug fix (0)
-----------------------------------

Due to an error in the sampling of a Poisson distribution, large means
(around 750 and up), always returned 2.
Now, if this happens, salabim falls back to another algorithm,
that works for any mean. But, this is slower than the 'base'
algorithm.

Salabim now offers the possibility to use the numpy Poisson sampling 
functionality, which is indeed much faster. For reproducibility 
reasons, this feature is disabled by default.
In order to enable numpy Poisson distribution sampling, specify
prefer_numpy = True when defining the Poisson distribution, like
    d = sim.Poisson(mean=1000, prefer_numpy=True)
If numpy is not installed, salabim uses the 'normal' algorithm.

Bug fix (0)
-----------

AnimateSlider could not be removed properly. Fixed.

Bug fix (1)
-----------

A bug in AnimateSlider sometimes caused an error in getting the current value (v). Fixed.

Bug fix (2)
-----------

The way caching xweight was built, sometimes resulted in -although statistically correct-
unexpected results for monitor. The fix applied is also more performant.

version 23.0.0  2023-01-06
==========================

Added functionality (0)
-----------------------

The labels parameter of AnimateMonitor may now be also a dict, where
the keys indicate where to put the label (via vertical_map), and the
values are the texts to be shown there.
It is still possible to use an iterable, in which case the text to
be shown the string representation of the label itself.

Added functionality (1) [thanks to a suggestion by @tcdejong]
-----------------------

A new monitor has been added to Queue: available_quantity, which can be
used to get the remaining capacity, e.g.
    q = sim.Queue("q", capacity=10)
    c.enter(q)
    print(q.available_quantity()
This monitor can't be tallied by the user.

Also introduced is a new method of Queue: set_capacity:
    q = sim.Queue("q", capacity=10)
    q.set_capacity(20)
    print(q.capacity(), q.available_quantity()

Added test (0)
--------------

If blind_animation == True, the test for the existence of PIL was not done, so
a less obvious error message was issued if PIL was not present. Fixed.

Bug fix (0)
-----------

Bug in AnimateQueue where direction="e" and textoffsetx is specified
and textoffsety is not specified fixed.

Bug fix (1) [thanks to @citrusvanilla]
-----------

AnimatePolygon did not properly close the polygon.
Fixed.

Bug fix (2)
-----------

Bug in 3D blind animation. Fixed.

Documentation fix (0)
---------------------

TrajectoryMerged was not documented. Fixed.

Usage recommendation (0)
------------------------

Hugo Hughes reports that it is possible to run 3D animated model on a headless server.
This can be done with a module that creates a virtual screen "pyvirtualdisplay", like
    from pyvirtualdisplay import Display
    virtual_display = Display(visible=0, size=(1920, 1080))
    virtual_display.start()

(Both the tkinter and OpenGL windows are properly emulated).
Is blind_animation still required?

version 22.0.8  2022-10-13
==========================

New functionality (0)
-----------------------

Salabim has a new feature: trajectories.
These can be used as:

- a trajectory an animated object should follow in time,
  including getting the required duration
- placing components of a queue along a trajectory

A trajectory can consist of a number of subtrajectories,
where each can be a polygon (optionally splined) or a circle (segment)

The position on the trajectory in relation to the time is
optionally described a uniform acceleration/deceleration
with a given initial speed, final speed as well a maximum speed.

The various classes and their methods are in the reference section
of the documentation.
A manual update covering this subject is in the works.

See also sample models "Demo trajectory.py".

New functionality (1)
-----------------------

AnimateQueue and Queue.animate can now place the animation objects on a given
trajectory, by specifying
    direction="t", trajectory=...
The trajectory x, y and angle method are called with the cumulated 'length' of the
animation objects dimx parameter (dimy is ignored).

See also sample models "Demo trajectory animate queue.py"

New functionality (2)
---------------------

AnimateImage now supports .heic (Apple's propriety High Efficiency Image File Format) files.
In order to read these files, pillow-heif has to be installed, e.g. with
    pip install pillow-heif
This functionality is not available under Pythonista.

Changed functionality (0)
-------------------------

The AnimateSlider parameters are changed considerably as the previous version
was not consistent and missed useful functionality.

New parameters are:
    foreground_color : colorspec
        color of the foreground (default "fg")

    background_color : colorspec
        color of the backgroundground (default "bg")
    
    trough_color : colorspec
        color of the trough (default "lightgrey")
    
    show_value : boolean
        if True (default), show values; if False don't show values (thus only showing the label)

The following parameters were available, but actually not used at all:
    linecolor
    labelcolor
    layer
They will remain accepted for compatibility reasons.

Added the method AnimateSlider.label:
    Parameters
    ----------
    text : str
        new label
        if omitted, no change

    Returns
    -------
    Current label : str

With the new label method, it's easy to make dynamic labels, like:

    import salabim as sim
    import datetime
    
    def action(v):
        v_as_datetime = datetime.datetime(2022, 1, 1) + datetime.timedelta(days=int(v))
        an0.label(f"{v_as_datetime:%Y-%m-%d}")
    
    env = sim.Environment()
    an0 = sim.AnimateSlider(x=100, y=100, action=action, width=500, height=30, v=30, vmin=0, vmax=365, resolution=1, fontsize=12, show_value=False)
    env.animate(True)
    env.run(sim.inf)

See also sample model "Demo slider.py"

Note that the Pythonista implementation does not use all given parameters.

Changed functionality (1)
-------------------------

In order to let AnimateCombined dynamic attributes work the same way as ordinary
Animatexxx objects, getting an attribute for an AnimateCombined object now returns
that attribute of the first animation object that has such an attribute, rather
than the 'shared' value.
If an attribute can't be found at all, now an AttributeError is raised, rather than
a ValueError.

As the animation_objects in AnimateCombined are now a list, rather than a set,
AnimateCombined.add is replaced by AnimateCombined.append.
    

Bugfix (0)
----------

Fixed a bug in resource requesting (thanks to Cameron Powell)

Bugfix (1)
----------

Bug in Monitor.xt() re adding now (introduced in version 22.0.6) fixed. 

Documentation bugfix (0)
------------------------

A minor mistake in the docstring of animation_paramters re show_menu_buttons corrected

version 22.0.7  2022-08-14
==========================

New functionality
-----------------

The method Environment.background3d_color can be used to set or query the
background color of a 3D window. Note that this can be changed at any time
and will be immediately in effect.
Related to this is a new parameter background3d_color of Envuironment.animation_parameters,
which has the same functionality.

Renamed methods (0)
-------------------

For consistency reasons, the following methods are renamed

salabim <= 22.0.6                            salabim >= 22.0.7

------------------------------------------   -------------------------------------------

Environment.user_to_screencoordinates_x      Environment.user_to_screen_coordinates_x
Environment.user_to_screencoordinates_y      Environment.user_to_screen_coordinates_y
Environment.user_to_screencoordinates_size   Environment.user_to_screen_coordinates_size
Environment.screen_to_usercoordinates_x      Environment.screen_to_user_coordinates_x
Environment.screen_to_usercoordinates_y      Environment.screen_to_user_coordinates_y
Environment.screen_to_usercoordinates_size   Environment.screen_to_user_coordinates_size

------------------------------------------   -------------------------------------------

Bugfix (0)
----------

When a 3D animation was closed, the 3D window did not disappear.
Fixed.

Bugfix (1)
----------

When initializing Resource with a non zero inititial_claimed_quantity,
the Resource.available_quantity monitor got the wrong initial tally.
Fixed.

version 22.0.6  2022-07-28
==========================

Bugfix (0)
----------

In the just released version 22.0.5, a serious bug made that animations did
not run correctly.
Fixed.

Bugfix (1)
----------

In AnimateMonitor / Monitor.animate(), the fillcolor rectangle was not correctly
positioned behind the label lines, which were in turn not positioned behind
the plot line/points.
Fixed.

version 22.0.5  2022-07-24  
==========================

Improved functionality (0)
--------------------------

Now a call to sim.reset() will destroy a previous tkinter canvas window (if any).
That makes it much easier to use salabim in an interactive environment like iPython or Jupyter.

Added functionality (0)
-----------------------

The new function searchsorted offers (nearly) the same functionality as
numpy.searchsorted.
If numpy is installed the function delegates to numpy.searchsorted.

Added functionality (1)
-----------------------

The new function arange offers (nearly) the same functionality as
numpy.arange.
If numpy is installed the function delegates to numpy.arange.

Added functionality (3)
-----------------------

The new function linspace offers similar functionality as numpy.linspace.
The function returns a list, rather than an array, which
is usually more practical in a salabim model.

Added functionality (4)
-----------------------

The function interp now also supports lists and tuples.
This can be useful to interpolate lines and polygons directly.
The function now uses internally a binary search (bisect).
Furthermore, the function does not delegate to numpy anymore as this is just slower.

Added functionality (5)
-----------------------

The new method Environment.color_interp() can be used to
interpolate colors, interp() style. E.g.
    sim.color_interp(t, (0, 10, 20), ('red', 'blue', 'green'))
This allows for more than two times/colors to be specified as opposed to Environment.colorinterpolate
which supports only two times/colors (with a different API).

Added functionality (6)
-----------------------

The new method Monitor.start_time() will return the creation time or the last time of a reset
of this monitor.

Added functionality (7)
-----------------------

AnimateMonitor() and Monitor.animate() now have a parameter as_points, which allows the user
to override the default for tallied points, which is False for level monitors and
True for non level monitors. 

New functionality (0)
---------------------

It is now possible to get the actual animation time with
Environment.t()
Note that in a simulation step, env.t() is always equal to env.now(), even if animation is off.

Changed functionality (0)
-------------------------

When animating and requesting any of the level monitor statistics, these ended at env.now(),
but in practice, it is better to end these with env.t.
Changed behaviour, so it is now possible to have a dynamic mean, std, percentile, etc.
up to the current animation time.

Internal changes / change in functionality (0)
----------------------------------------------

In version 20.0.3 the internals of the parent parameter in all Animatexxx was changed.
Unfortunately, this change is not guaranteed to work.
Therefore, from this version on, the animation object(s) of which a component is parent
will be removed at the very moment that component becomes a data component (i.e.
terminates).
The new method Component.remove_animation_children() can be used also to remove all the
animation objects of which the component is parent.

Perfomance improvement (0)
--------------------------

When calling make_pil_image with self.type == "text" and no text to display,
the attributes x, y, angle, ... were evaluated always.
Now, the method returns immediately by placing the check code at the top
of the method.

Bugfix (0)
----------

When Environment.reset_now() was called, animations could be wrong, because the time communicated
to dynamic attributes was not set correctly.
Fixed.

Bugfix (1)
----------

A bug in Monitor.reset() made that the start attribute of a monitor was not set properly when
a reset_now() had been issued. Fixed.

Documentation of 3D camera control keys
---------------------------------------

<Left>          rotate camera -1 degree
<Right>         rotate camera +1 degree


<Up>            zoom in 0.9 * 
<Down>          zoom out 1.1 *

<z>             lower the camera 0.9 *
<Z>             raise the camera 1.1 *

<Shift-Up>      move camera in z-plane 0.9 *
<Shift-Down>    move camera in z-plane 1.1 *

<Alt-Left>      move camera x - 10
<Alt-Right>     move camera x + 10
<Alt-Down>      move camera y - 10
<Alt><Up>       move camera y + 10 

<Control-Left>  center x - 10
<Control-Right> center x + 10
<Control-Down>  center y - 10
<Control-Down>  center y + 10

<o>             field of view * 0.9
<O>             field of view * 1.1

<t>             tilt camera +1 degree
<T>             tilt camera -1 degree

<r>             rotate camera axis +1 degree
<R>             rotate camera axis -1 degree

<p>             print current camera control settings



version 22.0.4  2022-06-02
==========================

Changed functionality (0)
-------------------------

When an animation window was closed with the X button in the upper right-hand corner.
the application used to crash. 
From this version on, the simulation will turn off the animation and raise a
SimulationStopped exception.

Animation functionality (0)
---------------------------

All animation primitives *) now have a show() method that can be used
to show an animation objects that had been removed. 
It is possible to use show for animation objects that are already shown.

All animation primitives *) now have a remove() method that can be used
take an animation object off the animation objects set.
This is different from setting visible to False, as it is not checked
anymore.
It is possible to use remove for animation objects that are already removed.

All animation primitives *) now have a isremoved() method, that returns
True if the animation object is on the animation objects set. False,
otherwise.

All animation primitives *) now have a (dynamic) keep parameter method that can be used
to remove an animation object once the values becomes False.
Note that even if you set keep=True, later, the animation object will not be
reshown as the animation object is not checked anymore.
If you want an animation object which was removed by keep=False, use the
show() method (at the same time making sure that keep=True).

*) AnimateCircle, AnimateImage, AnimateLine, AnimatePolygon, AnimatePoints, AnimateRectangle, AnimateText,
   Animate3dBar, Animate3dBase, Animate3dBox, Animate3dGrid, Animate3dLine, Animate3dObj,
   Animate3dRectangle, Animate3dSphere,
   AnimateQueue, Animate3dQueue and AnimateMonitor

Animation functionality (1)
---------------------------

AnimateCombined now acts like a set instead of a list.

Animation internals (0)
-----------------------

The animation engine is internally changed rather dramatically.
Previously AnimateLine, AnimateRectangle, etc. delegated to Animate.
Now Animate delegates to AnimateLine, AnimateRectangle, ...
Animate itself is not used internally anymore.
This change made it possible to use the more versatile dynamic attribute method and is
potentially safer.
This change should have no impact on existing models. But, you never know ...

Bugfix (0)
----------

A bug introduced in version 22.0.3 made it impossible to use vertical_map properly in AnimateMonitor.
Fixed.

Bugfix (1)
----------

A bug in over3d animation fixed.

Bugfix (2)
----------

In version 22.0.3 the add_attr method in animation primitives *) was removed by mistake. Fixed.


version 22.0.3  2022-05-15
==========================

Added functionality (0)
-----------------------

AnimateMonitor is completely rebuilt to allow dynamic attributes.
From now on, *ALL* attributes can be specified as a constant, a function of t or a method witn t as
argument. 
This is particularly useful for dynamic ranges, both horizontally and vertically.

Now AnimateMonitor also supports visible and over3d (both dynamic) and screen_coordinates.

it is possible to get the monitor associated with AnimateMonitor via the monitor() method. 
This can be handy in writing dynamic lambda function, e.g. to get the maximum of a monitor.
(see example below)

Exam
  ```

ple:

    import salabim as sim


    class X(sim.Component):
        def process(self):
            v0 = v1 = 10
            while True:
                v0 = max(0, min(500, v0 + sim.Uniform(-1, 1)() * 10))
                level_monitor.tally(v0)
                v1 = max(0, min(500, v1 + sim.Uniform(-1, 1)() * 10))
                non_level_monitor.tally(v1)
                yield self.hold(1)


    env = sim.Environment()
    env.speed(10)
    
    sim.AnimateText("Demonstration dynamic AnimateMonitor", fontsize=20, y=700, x=100)
    
    level_monitor = sim.Monitor("level_monitor", level=True)
    non_level_monitor = sim.Monitor("non_level_monitor")
    X()
    sim.AnimateMonitor(
        level_monitor,
        linewidth=3,
        x=100,
        y=100,
        width=900,
        height=250,
        vertical_scale=lambda arg, t: min(50, 250 / arg.monitor().maximum()),
        labels=lambda arg, t: [i for i in range(0, int(arg.monitor().maximum()), 10)],
        horizontal_scale=lambda t: min(10, 900 / t),
    )
    sim.AnimateMonitor(
        non_level_monitor,
        linewidth=5,
        x=100,
        y=400,
        width=900,
        height=250,
        vertical_scale=lambda arg, t: min(50, 250 / arg.monitor().maximum()),
        labels=lambda arg, t: [i for i in range(0, int(arg.monitor().maximum()), 10)],
        horizontal_scale=lambda t: min((10, 900 / t)),
    )
    
    env.animate(True)
    env.run(120)

Enjoy this new feature!

Changed functionality (0)
-------------------------
The behaviour of setting/getting attributes in AnimateCombined is changed.

If you query an attribute of a combined animation object, it will now return the 
value of the attribute, only if all combining animation objects (that have this attribute)
are the equal.
If they are not equal or no attribute is found at all, a ValueError will be raised.

If you set an attribute, it will set that attribute only for combining animation
objects that have indeed that attribute present. It is not an error if no
attribute is found at all.

Examples:
    an0 = sim.AnimateRectangle(spec=(-10,-10,10,10))
    an1 = sim.AnimateCircle(radius=5, fillcolor="white")
    an2 = sim.AnimateCircle(radius=10, fillcolor="red")

    an = sim.AnimateCombined([an0, an1, an2])
    
    an.x = 5  # will set x=0 for an0, an1 and an2
    an.radius = 7  # will set radius=7 for an1 and an2, but not an0
    
    print(an.x)  # will print 5 as x==5 for an0, an1 and an2
    print(an.radius)
      # will print 7 as radius==7 for an1 and an2 (an0 does not have a radius and is ignored)
    
    print(an.fillcolor)
      # will raise a ValueError because an0, an1 and an2 do not have the same fillcolor
    
    print(an.image)
      # will raise a ValueError because neither an0, an1 nor an2 have an image attribute

Changed functionality (1)
-------------------------
sim.Resource now has an initial_claimed_quantity parameter, that can be used only
for anonymous resources. If not zero, the resource starts with a quantity in it.

Example:
    r = sim.Resource("r", capacity=100, initial_claimed_quantity=50, anonymous=True)

Changed functionality (2)
-------------------------
The over3d parameter of
   sim.AnimateText, sim.AnimateLine, sim.AnimatePoints, sim.AnimatePolygon,
   sim.AnimateImage, sim.AnimateRectangle
is now dynamic.

Bugfix (0)
-----------
There was a bug in AnimateLine, AnimateRectangle and AnimatePolygon that prevented from using as_points properly.
Fixed.


version 22.0.2  2022-04-30
==========================
Added functionality (0)
-----------------------
All methods that set a scheduled time now have a parameter cap_now:
- Environment.run
- Component.hold
- Componentactivate
- Component.request
- Component.wait
- creation of a new component

Normally, a scheduled time in the past raises a exception.
If cap_now is True, a scheduled time in the past will change that time into now. E.g.
    yield self.hold(sim.Normal(2,1))
would normally raise an exception after a couple of samples. But
    yield self.hold(sim.Normal(2,1), cap_now=True) 
would cap the negative samples to 0, thus avoiding an exception.
Be careful using this feature as you might miss a serious problem.

It is even possible to set cap_now globaly with sim.default_cap_now(True).

And there's a context manager sim.cap_now to temporarily override the global default_cap_now:
    with sim.cap_now():
        yield self.hold(-1)
This will hold for a duration of 0!

The documentation has a section on this functionality, now.

Added functionality (1)
-----------------------
The ComponentGenerator() class now suppports a disturbance for iat type generators.
This can be very useful to define a recurring event (e.g. a regular arrival of a bus),
which deviates from the 'timetable'. Like
    sim.ComponentGenerator(Bus, iat=60, disturbance=sim.Uniform(-1, 5))

Added functionality (2)
-----------------------
ComponentGenerator now supports any callable as the component_class.
If disturbance is specified (see above), component_class has to be a subclass of
ComponentClass, however.

Added functionality (3)
-----------------------
The function interp offers the same basic functionality as numpy.interp. In fact it uses numpy if available.
This can be very useful for animations where the location changes at certain point in time, like
    AnimationRectangle((-10,-10,10,10), x=100, y=lambda t: sim.interp(t, (0,10,20,30),(100,200,500,1000)))

Added functionality (4)
-----------------------
Salabim can now optionally show times and durations as dates/timedeltas. 
Therefore, sim.Environment() has a new parameter datetime0.
If datetime0 is set to True, the base date will be 1 January 1970. Alternatively, a
datetime.datatime date can be given.
Note that if no time unit is specified, and datetime0 is given, the time unit will
be set to seconds automatically.
If datetime0 is set, the methods Environment.time_to_str and Environment.duration_to_str
will return a nicely formatted date/time or duration,
like Fri 2022-04-29 20:55:06 for a date/time or 00:04:45 for a duration.
Note that these are used in the trace and in animations (to show the time).
Of course, it is still possible to override these two methods.

Furthermore, the following methods are added to salabim
- Environment.datetime_to_t
- Environment.timedelta_to_duration
- Environment.t_to_datetime
- Environment.duration_to_timedelta
- Environment.datetime0

Particulary datetime_to_t can be very useful to read information from an
external source (file, API, ...) and translated into simulation time.
In order to output these times, just use t_to_datetime with an
appropriate format.

Also, the method Environment.reset_now is now also datetime0 aware.

The documentation has a section on this functionality, now.

Added functionality (5)
-----------------------
Under Pythonista, salabim can now also run correctly in retina mode (native resolution)
on iPhones and other screens with a scale factor that is not 2.
Note that the buttons are still not shown.

Bug fix (0)
-----------
When stopping an animation from the menu (with the Stop button), the SimulationStopped exception
was incorrectly not raised in case synced is False. Fixed. 
    
version 22.0.1  2022-02-12
==========================

Added functionality (0)
-----------------------
Monitors now have an x_map method, which makes it possible to create a new monitor:
- for non level monitors: apply a function to each x-value
- for level monitors: apply a function to several x-values
  Examples:
    q = sim.Queue()
    ...
    stay_in_hours = q.length_of_stay.x_map(lambda x: x * 3600)
  
    containers20 = sim.Monitor(level=True)
    containers40 = sim.Monitor(level=True)
    ...
    teu = containers20.x_map(lambda n20, n40: (n20 + 2 * n40) / (n1 + n2), monitors=[containers40], name="teu")
  

Also new for this version is t_multiply for level monitors.
With this method, all t values will be multiplied with a given, positive factor.
Example:
    m = sim.Monitor('m', level=True)
    m.tally(1)
    env.run(1)
    m.tally(2)
    env.run(1)
    m.tally(3)
    env.run(8)
    print(m.bin_duration(2, 3))
    m10 = m.t_multiply(10)
    print(m10.bin_duration(2, 3))
will print
    8.0
    80.0    
        
Added functionality (1)
-----------------------
The method Component.line_number() will return the line_number in the process where the
component will become current next.
This can be extremely useful when debugging a complex model by observing the animation.
For data components, the string "N/A" will be returned.

Added functionality (2)
------------------------
The method Environment.camera_auto_print() can be used to enable/disable printing
of the changed camera parameters on a given key.
If this parameter is True, the method camera_print will be called upon each and every camera
control key, like Up, z, Ctrl-Down, etc.
This is useful to make the specification for Environment.camera_move() method (see below).

The output of camera_print, now also includes a timestamp (as a comment), like 
    view(x_eye=-102.5950, y_eye=-97.3592, z_eye=100, x_center=50, y_center=50, z_center=0, field_of_view_y=50)  # t=0
    view(x_eye=-200,y_eye=-200)  # t=2
    view(x_eye=-100,y_eye=-100)  # t=5
    
Added functionality (3)
-----------------------
The new method Environment.camera_move() can be used to automatically follow a number of recorded
camera positions. These are usualy recorded with Environment.camera_camera_auto_print(True).
The captured output can be used as a specification to this method.
The movement will be lagged by the (simulation) time specified with lag, so a nice smooth movement
is the result, which is particularly useful for presentation quality videos.

Normally, the spec parameter will be a triple quoted string, like:
    env.camera_move("""\
view(x_eye=-102.5950, y_eye=-97.3592, z_eye=100, x_center=50, y_center=50, z_center=0, field_of_view_y=50)  # t=0
view(x_eye=-200,y_eye=-200)  # t=2
view(x_eye=-100,y_eye=-100)  # t=5
""", lag=1.5)

Added functionality (4)
-----------------------
It is now possible to make the tkinter animation window invisible with the visible parameter of
Environment.animation():
    env.animation_parameters(visible=False)
The same can be realized with Environment.visible:
    env.visible(False)
With the latter method, you can also query the current status.

This functionality can be useful when doing realtime simulations with a custom GUI or similar.

Added functionality (5)
-----------------------
It is now possible to exclude certain animation objects from a video by setting 
visible to "not in video". Those animation objects are still shown in the normal animation window. 
E.g.
    sim.AnimateText(text="this will be visible in the animation window, but not in the video", x=10, y=10, visible="not in video")

Similarly, it also possible to exclude certain animation objects from the animation
window, but leave it in the video.
E.g.
    sim.AnimateText(text="this will be visible in the video, but not in the animation window", x=10, y=10, visible="only in video")

Note that this functionality does not apply to 3D animation objects (including over3d animation objects).

Added functionality (6)
-----------------------
The method Environment.is_videoing() can be used to check whether a video is being recorded.
This can be useful when running dependent on whether a video is recorded. E.g.
    filename = ... # if filename == "", run infinitely, otherwise, run for 5 time units.
    with video(filename):
        if env.is_videoing():
            env.run(5)
        else:
            env.run(sim.inf)
    
Improved functionality (0)
--------------------------
The trace facility now also shows the (next) line number for passivate and standby calls.
The same holds for components that are being interrupted or resumed.

Improved functionality (1)
--------------------------
The value of a state in the trace is now printed with repr() instead of str(), so it's easier to
see the value (particularly for the null string of strings with only blanks), e.g.
   32                                  s2 create                            value = ''
instead of
   32                                  s2 create                            value = 

Bugfix (0)
----------
A bug in Monitor.sysweight() made that Monitor.x() didn't work properly. Fixed.

Bugfix (1)
----------
The line number of an activated process that was not a generator object (i.e. without a yield) was misaligned. Fixed.

Documentation fix (0)
---------------------
In several Animation classes the text_offsetx and text_offsety parameters were incorrectly documented as
textoffsetx and textoffsety. Fixed.

version 22.0.0  2022-01-09
==========================
Added functionality (0)
-----------------------
It is now possible to add a 2D overlay to a 3d animation. This overlay can be extremely useful
for showing status information, like the time. And logos and ...
Particularly videos can be much more professional and instructive.

All normal 2d animation objects are available for overlaying:
Animate, AnimateCircle, AnimateImage, AnimateLine, AnimatePolygon,
AnimatePoints, AnimateRectangle and AnimateText
Also, the AnimateMonitor and AnimateQueue support overlaying.
All these classes have an optional parameter over3d.

Note that the optional parameter defaults to False, but can be overridden with the
sim.default_override() function. On top of that, it is possible to use the
sim.over3d() context manager to temporarily override the default like,
    with sim.over3d():
        AnimateCircle(radius=50, x=100, y=100)
        AnimateRectangle((-20, -20, 20, 20), x=100, y=100)
These two animation objects will now be shown as an overlay on the 3d animation.

For AnimateQueue, the Component.animation_objects_over3d method should specify the objects
, just like Component.animation_objects for ordinary 2d animations.
By default, this is a defined as a square (same as in ordinary 2d).

Changed functionality (0)
-------------------------
From now on, there are several ways that resource requests are honoured (specifified in Resource parameters):
    honor_only_first: if True, only the first of the requesters queue will be honoured
    honor_only_highest_priority: if True, only components with the priority of the first in requesters will be honoured
As both parameters are False by default, existing models will still work as before.

Changed functionality (1)
-------------------------
The way AnimateImage and Animate(image=...) handles the given image spec has been changed,
and is much more robust now.
That means that an image will not be read util really required. So, if animation is not activated,
the image file will not be opened (and could be even absent).
Also, read images from a file will be cached automatically, so it is very easy to cycle through
several images without a performance problems.
It is now possible to say
    an = sim.AnimateImage(spec="a.png")
    ...
    an.spec = "b.png"
, so no more need to use sim.spec_to_image(), although that function still exists.

Related to this is that in case no width is given, the width of the image will be
assessed as late as possible.
The method .width() of an image animation object will return None if no width is specified.
If it is required to get the actual (physical) width of a spec, there's now the function
    sim.spec_to_image_width()

Changed fuctionality (2)
------------------------
To avoid confusion, it is not allowed anymore to change
  fps
  video_width
  video_height
  video_mode
  video_repeat
  video_pingpong
when a video is being recorded.

Changed functionality (3)
------------------------
When a simulation raised a SimulationStopped exception, a video being recorded will be closed automatically.

Added functionality (0)
-----------------------
An animation can now be stopped with Ctrl-C.

Bugfix (0)
----------
Under Pythonista, changing fonts didn't work properly in version 21.1.7. Fixed.

Bugfix (1)
----------
If Map was used in a specification of a Distribution, an attribute error was raised. Fixed.

Internal change (0)
-------------------
Salabim now uses f-strings extensively (mainly automatically converted by flynt).
This makes reading and maintaining the source easier (and arguably faster).

version 21.1.7  2021-12-13
==========================
Added functionality (1)
-----------------------
During an animation, it is now possible to:
- press <space> to toggle between run and pause (with menu button shown)
  ,so it is not necessary to press the Menu/Go mouse button
- press - to halve the animation speed
- press + to double the animation speed
- press s to single step
  this can very useful, particularly when trace is on
  You will love this!

Added functionality (0)
-----------------------
Queues can now have limited capacity, by setting the capacity parameter of Queue(), e.g.
    q = sim.Queue('q', capacity=5)
If a queue exceeds that capacity, a QueueFullError exception will be raised.
So, it is possible to do
    try:
        c.enter(q)
    except sim.QueueFullError:
        experienced_full += 1
     
Queue.capacity is a level monitor that can be changed like
    q.capacity.value = 10
, so it is also possible to make a normal unrestricted queue into a queue with a 
limited capacity.
    q = sim.Queue('q')
    ...
    q.capacity.value = 5
Important: if the queue contains more components than the new capacity, all
components will stay in the queue.

The methods union, intersection, difference, symmetric_diffence, and the operator +, -, ^, |, &
will not use the capacity in any way.

The methods copy and move do not copy the capacity by default, but may do so if
copy_capacity=True is given with the call.

Changed functionality (0)
-------------------------
When an animation is stopped, either by the user or an error, now a SimulationStopped exception is raised.
This makes that a simulation will not continue in that case, as it did before.

If you just want to be able to stop a run from the animation menu in a clean way, use something like
try:
    env.run()
    queue.print_histograms()
except sim.SimulationStopped:
    pass
    
Changed functionality (1)
-------------------------
The s1 parameter in print_trace was always padded to a length of 10.

From now on this length is dynamically defined, although it is highly recommended that the method
always returns the same length string.

In relation to this, the Environment.time_to_str_format() method has been phased out.

The same functionality as env.time_to_str_format("{:10.4f}") can be obtained with:
    sim.Enviroment.time_to_str = lambda self, t: f"{t:10.4f}"
or
    class MyEnvironment(sim.Component):
        def time_to_str(self, t):
            return f"{t:10.4f}"
    ...
    env = MyEnvironment()

With this change in functionality, it is possible to show the time even as a proper date/time, like
    sim.Enviroment.time_to_str = lambda self, t: datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")

Note that the Environment.time_to_str() method is also used to show the current time in animations.

Related to this change is a new method Environment.duration_to_str, that is used whenever a duration has
to be printed in a trace.
This method defaults to a 0.3f formatted string, but may be overridden.

Removed functionality (2)
-------------------------
The height, linecolor and linewidth parameters of AnimateButton were completely ignored 
(apart from in the Pythonista implementation).
Therefore, these have been removed completely.
The documentation/docstring will be updated accordingly.

Pythonista specific improvements / bugfixes (0)
----------------------------------------------
Using one of the standard fonts now do not have to call fonts(), thus avoiding a significant delay.

AnimateSlider() now calls the action function (if any) at start up, as with the tkinter version.

The action function in AnimateSlider gets a string as parameter now instead of a float, as with the tkinter version.

Bugfix (0)
----------
A serious bug prevented animations to run properly under Pythonista. Fixed.

Bugfix (1)
----------
Bug in the interpretation of multiple states in Component.wait() fixed.

Bugfix (2)
----------
When producing an animated gif or png video, pingpong was always applied, regardless of the pingpong parameter. Fixed.

Bug fix (3)
-----------
When video_repeat was 1 (for animated GIF videos), the video was played twice on certain platforms.
Fixed.

Bug fix (4)
-----------
The maximum number of fonts that could be use in one animation was approximately 500.
From this version on, the number of fonts that can be handled is only limited by the available memory.

Speed improvement(0)
--------------------
If a font can't be located directly, the salabim and current directory are not searched recursively anymore.

Documentation update (0)
------------------------
The docstring for Environment.video() now makes clear that the
  video_width
  video_height
  video_mode
  video_repeat
  video_pingpong
parameters at the time Environment.video is called are used. Any change after will be ignored and only applied to
another Environment.video call.

Documentation update (0)
------------------------
The docstring for Component.request() and Component.wait() now makes clear that the
priority parameter refers to the fail event.


version 21.1.6  2021-11-07
==========================
Changed functionality (0)
-------------------------
Labels in AnimateMonitor() / Monintor.animate() are now suppressed if the
corresponding y-value is outside the 'y range'.

Changed functionality (1)
-------------------------
The default for priority in Environment.run() is now inf (was 0).
This makes that, by default, all components scheduled for the end moment will become active before
the run ends

Changed functionality (2)
-------------------------
When an_menu() was issued from a program, the simulation wasn't paused until the next tkinter tick.
From this version, the simulation will pause exactly at the current time (just prior to the next event).
This functionality is also available under Pythonista.

Added checks (0)
----------------
A call to Component.wait is now more strictly checked for errors.

Bugfix (0)
----------
In version 21.1.4 a bug was introduced that made it impossible to add audio to a video.
Fixed.

Bugfix (1)
-----------
Although State.animate was phased out already in version 2.3.0, the State.__init__ method still contained
an animation_objects parameter, that is not used anymore.
So, both the docstring, documentation and the parameter heading have been updated accordingly.

Bugfix (2)
----------
Bug in Monitor.median caused an error when interpolation was not specified. Fixed.

Bugfix (3)
----------
AnimateSlide did not observe the width and height parameters at all (apart from under Pythonista).
Fixed.

Documentation and docstring enhancement (0)
-------------------------------------------
All animation objects now have the remove() method documented.

Documentation bugfix (0)
------------------------
The default value label_anchor parameter of AnimateMonitor / Monitor.animate was
documented to be 'sw', where it should have been 'e'. Fixed.

Internal change (0)
-------------------
Check for correct interpolation in Monitor.percentile() / Monitor.median() now done at start of the method, thus being more robust.

version 21.1.5  2021-09-01
==========================
Changed functionality / bug fix (0)
-----------------------------------
The Monitor.percentile method has been completely rewritten, to fix bugs and
introduce the interpolation parameter.

For non weighted monitors, the method is now exactly equivalent to the numpy percentile
function. So it is now possible to use the interpolation parameters as follows:
    This optional parameter specifies the interpolation method to use when the
      desired percentile lies between two data points i < j:
    ‘linear’: i + (j - i) * fraction, where fraction is the fractional part of the index surrounded by i and j
    ‘lower’: i.
    ‘higher’: j.
    ‘nearest’: i or j, whichever is nearest.
    ‘midpoint’: (i + j) / 2.
For weighted and level monitors the behaviour is quite different (there's no equivalent in numpy),
as only tallied values will be returned,  apart from when the value is undetermined,
i.e. on change of value. In that case, the interpolation parameter will be applied as follows:
    ‘linear’, 'midpoint': mean of the two tallied values
    ‘lower’: lower tallied value
    ‘higher’: highed tallie value

In all cases, interpolation defaults to 'linear'.

The test_monitor.py file has been updated to test the new functionality.

Added functionality (0)
-----------------------
The Monitor.median method now also supports the interpolation parameter
  (see above description of percentile)


Added functionality (1)
-----------------------
The classes
  AnimateCircle, AnimateImage, AnimateLine, AnimatePolygon, AnimateRectangle, AnimateText,
  Animate3dBar, Animate3dBox, Animate3dGrid, Animate3dLine, Animate3dObj, Animate3dRectangle, Animate3dSphere and
  AnimateQueue
now have additional method: add_attr .

This is useful to add attribute(s) to an animation object, without having to assign the object a name and 
assign the attribute(s) in seperate line(s).
So, instead of
    for xx in range(10):
        an = sim.AnimateRectangle(spec=lambda arg,t: (arg.xx,0,arg.xx+10,arg.xx+t*10))
        an.xx = xx
we can now say
    for xx in range(10):
        sim.AnimateRectangle(spec=lambda arg,t: (arg.xx, 0, arg.xx + 10, arg.xx + t * 10)).add_attr(xx=xx * 20)

It is possible to assign several attributes at once, like:
    sim.AnimateRectangle(spec=lambda arg,t: (arg.xx, arg.yy,arg.xx + 10,arg.xx + t * 10)).add_attr(xx=xx * 20, yy=xx * 5)
, but also like
    sim.AnimateRectangle(spec=lambda arg,t: (arg.xx, arg.yy,arg.xx + 10, arg.xx + t * 10)).add_attr(xx=xx * 20).add_attr(yy=xx * 5)

The method add_attr just returns the "calling" object, thus allowing "daisy chanining".

Note that it is not allowed to add any attributes that are already defined. So
    sim.AnimateRectangle(spec=(0, 0, 10, 10).add_attr(x=5)
is not allowed as x is already defined by salabim.


Added functionality (2)
-----------------------
The method env.animate() now can use '?', to enable animation, if possible.
If not possible, animation is ignored.

The method env.animate3d() now can use '?', to enable 3D-animation, if possible.
If not possible, 3D-animation is ignored.

Both functionalities are also available via env.animation_parameters().

Bug fix (0)
-----------
The offsetx and offsety parameters of all animation objects were always in screen_coordinates, even
if screen_coordinates == False. Fixed.

Documentation bug fix (0)
-------------------------
Docstring of AnimateMonitor and Monitor.animate() updated.

Bug fix (1)
-----------
Under Pythonista, 3D animation was just ignored, instead of issueing an error message
(as Pythonista does not support OpenGL). Fixed.

version 21.1.4  2021-07-18
==========================
New functionality (0)
---------------------
Introduced Environment.insert_frame() that can insert a PIL image or file (specified as str or pathlib.Path)
into the video stream.
This is particularly useful to add an introduction and explanatory frames.
Note that each frame is 1/30 seconds and you can specify the number of frames.
The image is automatically scaled to fit the current video resolution.

New functionality (1)
---------------------
The method Environment.snapshot() now has an extra parameter 'video_mode' that can be "2d" (the default),
"3d" or "screen".
Note that "3d" is only available if animate3d is True.
The resulting image is never scaled.

Changed functionality (0)
-------------------------
The method Environment.Animate3dObj now postpones the actual loading of the file till the moment it is
required. That makes it possible to call Animate3dObj even if no 3d animation is activated and
even possible.
Also, the filename and show_warnings may now be changed dynamically.

Internal changes (0)
--------------------
Changed the internals of _save_frame (now via insert_frame) and _capture_image.

Internal changes (1)
--------------------
If ImageGrab is not available on a platform, video_mode 'screen' is not supported
for video and snapshot and properly detected.


version 21.1.3  2021-07-07
==========================
New functionality (0)
---------------------
From this version on, it is possible to select the "video_mode" of a video.
You can choose from
- "2d" to film the normal tkinter window
- "3d" to film the OpenGL 3d animation window (only if animate3d is True)
- "screen" to film the full screen (screen capture). This is particularly handy to make a video of both
  the 2d and 3d windows.
  The method Environment.video_mode can be used to specify the video_mode. The default is "2d".
  Alternatively, the video_mode parameter of Environment.animation_parameters may be used as well.
  It is possible to change the video_mode during a recording.

New functionality (1)
---------------------
It is now possible to specify the resolution of the to be recorded video.
This can be done with Environment.video_width() and Environment.video_height().
Alternatively, the video_width and video_height parameters of Environment.animation_parameters may be used as well.
If the video_width/video_height is "auto" (the default), the resolution is taken from the video_mode at the time
video recording was started.
The captured images are always scaled to the given resolution, which might lead to horizontal or vertical
black bars to pad the image.

Added functionality (0)
-----------------------
The camera control keys in 3d animation now work also when the OpenGL window has the focus.


version 21.1.2  2021-07-03
==========================
Bugfix (0)
----------
Version 21.1.1 tried erroneously to import ycecream. This dependency has been removed.

BTW, my ycecream package is a very useful tool for debugging and benchmarking any Python program,
including salabim models.
See www.github.com/salabim/ycecream , if you are interested.


version 21.1.1  2021-07-02
==========================
New functionality (0)
---------------------
Introduced Animate3dSphere to animate a sphere.

Enhanced functionality (0)
--------------------------
Blind animation now also supports 3D animations. Note that OpenGL needs to be installed, though.

Functional change (0)
---------------------
The way the mode monitor was implemented made that the garbage collector could never remove a component,
thus causing a memory leak.
In order to change the behaviour, it won't be possible to set the mode of a component with 
    Component.mode.value = ...
anymore (as was mentioned in the 20.0.4 release notes).
You have to set the mode via one of the process control functions or with set_mode().

Bugfix (0)
----------
A bug in version 21.1.0 required to have OpenGL installed, even when no 3D animation was used. Fixed.
This bugfix also makes startup of non 3D animation models faster.

Bugfix (1)
----------
Under certain conditions, the file/linenumber in the trace was not shown correctly in the trace. Fixed.

Sample models update (0)
------------------------
Updated several models in the sample models folder.

Documentation update (0)
------------------------
A section on how to install OpenGL under Windows has been added to the documentation.
Here's the same text (slightly differently formatted):
    If, after  
       pip install PyOpenGL
    you get a runtime error that glutInit is not defined, try to install from the
    Unofficial Windows Binaries for Python Extension Packages site at
    https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopengl
    Find the right 3.1.5 or later version for you
    (e.g. for Python 3.7, 64 bits you use PyOpenGL-3.1.5-cp37-cp37m-win_amd64.whl) and download that.
    Then issue
        pip install wheelfile
    ,like (for the above package)
        pip install PyOpenGL-3.1.5-cp37-cp37m-win_amd64.whl
    and it should work.
    It is reecommended to install pyopengl_accelerate in the same way, like
        pip install PyOpenGL_accelerate-3.1.5-cp37-cp37m-win_amd64.whl
    
version 21.1.0  2021-06-17
==========================
Added functionality (0)
-----------------------
This version introduces 3D animation. That's a very powerful feature that
requires users at least to know how to do 2D animation.

Note that the API is still work in progress and might change.

Note that the documetation is not properly updated. Only the reference section
contains is now up-to-date.
I intend to update the documentation soon. Volunteers to help with that are welcome!

The sample 3d models folder on GitHub contains a couple of demo models, that
could be used as a start.

Changed functionality (0)
-------------------------
When Stop is pressed from the menu, the program now correctly exits, instead of returning to main.

Changed functionality (1)
-------------------------
Color name 'lightgrey' added, as this is present in the X11 color name standard, but was absent in salabim.
Color name 'sandybrown' updated, to be in line with the X11 color name standard

Bugfix (0)
----------
If video specified an extension with a coded, like .mp4+h264, the output file extension incorrectly
contained the codec information.
From this version on, the codec information is skipped in the resulting filename.


version 21.0.4  2021-05-01
==========================
Bugfix (0)
-----------
When a non-level monitor was sliced, the stop value was included in the slice,
so causing an overlap with a slice that started at that value.
Fixed.

Bugfix (1)
-----------
When run on a Chromebook (at least on a Lenovo Duet), the menu buttons were far too big. Fixed.

Bugfix (2)
-----------
On Linux platforms fonts not having the .ttf extension (particularly .TTF) were not found. Fixed.

Bugfix (3)
-----------
PeriodMonitors now get the stats_only flag from the parent monitor.
PeriodMonitors now correctly tally the weight.

version 21.0.3  2021-03-20
==========================
Added functionality (0)
-----------------------
Environment.snapshot() now also supports the .ico image file format.
This may be useful when (mis)using salabim as an icon generator.

Bug fix (0)
----------
Bug in initializing system monitors at init of a component (not setting env to self.env). Fixed.

Bug fix (1)
-----------
When producing videos with blind_animation=True (to allow running without tkinter installed),
the Environment.animation_pre_tick_sys() method was not called prior to saving a frame,
causing problems with animating queues. Fixed.

version 21.0.2  2021-01-25
==========================
Improved functionality (0)
--------------------------
The probabilities parameter of sim.Pdf can now be any iterable, so not just list or tuple.
This can be useful when using the keys or values of a dict as probabilities.

Improved functionality (1)
--------------------------
The spec parameter of sim.Pdf can now be a dict, where the keys are the x-values and the values
are the probabilities. In that case, the probabilities parameter can't be used.
E.g.
    d = sim.Pdf({1:10, 2:70, 3:20})
    d = sim.Pdf(dict(red=45, yellow=10, green=45))

Change in distribution (0)
--------------------------
The test scripts are now also available on GitHub (in the /test folder).

Bug fix (0)
-----------
Slicing of a merged level monitor didn't work properly, because the attribute start of the merged
monitor was not set correctly. Fixed.



version 21.0.1  2021-01-14
==========================
Bug fix (0)
-----------
Bug in Component._remove() fixed.

version 21.0.0  2021-01-14
==========================
New functionality (0)
---------------------
Added Environment.title()
With this, the title of the canvas window can be set. The title is set to "", the title will be completely suppressed.

Added Environment.show_menu_buttons()
With this, the menu buttons can be hidden

Added parameter title and show_menu_buttons to Environment.animation_parameters

The title of the canvas window now defaults to salabim, instead of tk. This can be overruled with Environment.title()


version 20.0.6  2020-12-18
==========================
New functionality (0)
---------------------
Monitors can now optionally collect statistics only.
This minimizes memory usage as individual tallies will not be stored in that case.
But beware that some important functionality is not available in stats_only monitors (see below).

You can define the stats_only status at creation time of the monitor, like:
    m = sim.Monitor('m', stats_only=True)

But, it is also possible to reset a monitor with a different stats_only value.
This can be useful if you want a system monitor, like Component.mode or Component.status to not keep individual
tallied values:
    class Car(sim.Component):
        def setup(self):
            self.mode.reset(stats_only=True)
When stats_only is active, values are always forced to numeric, with a fallback value of 0.

Monitor with stats_only=True support
    __call__/get (without arguments), base_name, deregister, duration, duration_zero, maximum, mean,
    minimum, monitor, name, number_of_entries, number_of_entries_zero, print_histogram,
    print_histograms, print_statistics, register, rename, reset, reset_monitors, sequence_number,
    setup, stats_only, std, t, tally, weight, weight_zero

Monitors with stats_only=True do NOT support (these will raise a NotImplementedError):
    __call__/get (with an argument), arithmeric operations (+, *, /), animate, bin_duration,
    bin_number_of_entries, bin_weight, freeze, histogram_autoscale, median, merge, multiply,
    percentile, slice, slicing, to_days, to_hours, to_microseconds, to_milliseconds, to_minutes,
    to_seconds, to_time_unit, to_weeks, to_years, tx, value_duration, value_number_of_entries,
    value_weight, values, x, xduration, xt, xweight

In line with the above, Queue.reset_monitors, Resource.reset_monitors, State.reset_monitors now
have a stats_only parameter, with which all monitors can set/reset the stats_only status.
So, if you want all eight monitors belonging to a resource, but the requesters' to be stats_only, you can write
    r.reset_monitors(stats_only=True)
    r.requesters.monitors(stats_only=False)
    
The current stats_only mode can be queried with Monitor.stats_only() .
    
New functionality (1)
---------------------
Queue.all_monitors() returns all (2) monitors associated with the queue
Resource.all_monitors() returns all (8) monitors associated with the resource
State.all_monitors() returns all (3) monitors associated with the state

Change of functionality (0)
---------------------------
Monitor.t is no longer a property, but a method. That means that to get the last tally time and value
of monitor m, you can write
    last_tally_t = m.t()
    last_tally = m()  # or last_tally = m.get()

Bug fix (0)
-----------
Non-level monitors did not always calculate the ex0=True mean and ex0=True std correctly when weights
other than one were in the monitor. Fixed.

version 20.0.5  2020-11-24
==========================
Added functionality (0)
-----------------------
The methods Component.request() and Component.wait() now also support the urgent and priority parameters, which
make it possible to fine-tune race conditions.

Added functionality (1)
-----------------------
ComponentGenerator can now 'propagate' keyword parameters to the components generated.
In line with this, the name parameter is changed to generator_name, in order to make it possible to
define the name of the generated components.
Example:

    import salabim as sim
    
    class Worker(sim.Component):
        def process(self, collar):
            print(f"I am {self.name()} and I have a {collar} collar")
         
    env = sim.Environment(trace=True)
    sim.ComponentGenerator(Worker, "technician generator", iat=sim.Uniform(2,4), name="technician.", collar="blue")
    sim.ComponentGenerator(Worker, "manager generator", iat=sim.Uniform(3,6), name="manager.", collar="white")
    env.run(10)

Added functionality (2)
-----------------------
sim.Environment() has now an extra parameter, blind_animation that can be used to create videos
without showing the animation during production.
This is particularly useful when running a simulation on a platform where tkinter is not supported,
such a server.
This functionality can also be used to slightly increase the performance of video production.
    
Example usage:
    try:
        import tkinter
        blind_animation = False
    except ImportError:
        blind_animation = True
    env = sim.Environment(blind_animation = blind_animation)
        
Improved functionality (0)
--------------------------
Monitor.print_histogram() can now show a user specified collection of values. This can be done by giving
an iterable to the values parameter. If not all values present in the monitor are given, a <rest> value
will be shown at the bottom. Like:
    x0.status.print_histogram(values=["scheduled", "current", "passive"])
may result in
    Histogram of x.0.status
    duration            50

    value                     duration     %
    scheduled                   10.100  20.2 ****************
    current                      0       0
    passive                     31.600  63.2 **************************************************
    <rest>                       8.300  16.6 *************

By default, the values are shown in the given order, but can also be sorted on value by specifying
sort_on_value=True.

Improved functionality (1)
--------------------------
Monitor.print_histogram() with values now supports sorting on weight (=number of entries if
all weights are 1) (for non-level monitors) and sorting on duration (for level monitors).
Therefore, two parameters have been added to print_histogram(): sort_on_weight and sort_on_duration.

So,
    x0.status.print_histogram(values=["scheduled", "current", "passive"], sort_on_duration=True)
may result in
    Histogram of x.0.status
    duration            50

    value                     duration     %
    passive                     31.600  63.2 **************************************************
    scheduled                   10.100  20.2 ****************
    current                      0       0
    <rest>                       8.300  16.6 *************

Improved functionality (2)
--------------------------
Monitor.values() now supports sorting on weight (=number of entries if all weights are 1) (for non-level monitors) and sorting on duration (for level monitors).
Therefore, two parameters have been added to values(): sort_on_weight and sort_on_duration.
So, in the above example,
    print(x0.status.values())
may result in
    ['data', 'interrupted', 'passive', 'scheduled']
, whereas
    print(x0.status.values(sort_on_duration))
may result in
    ['passive', 'scheduled', data', 'interrupted']
    
Internal change (0)
-------------------
The Component.__del__ now explicitly checks for the existence of an _animation_children attribute to prevent
an error when deleting a component which is not completely initialized yet.

version 20.0.4  2020-10-26
==========================
New functionality (0)
---------------------
A component now supports a level monitor 'status' that keeps track of all the statuses a component has been in.
For instance, component.status.print_histogram(values=True) will print something like
    Histogram of x.1.status
    duration            40

    value                     duration     %
    data                         4.300  10.8 ********
    interrupted                  4      10   ********
    passive                     11.500  28.7 ***********************
    requesting                  10.100  25.2 ********************
    scheduled                   10.100  25.3 ********************

And of course, it is possible to get the duration a component was in a certain status, like
    passive_time = component.status.value_duration(sim.passive).
You can even get the status of the component at a moment in the past, with e.g.
    status_4_units_ago = c1.status(env.now() - 4)

In line with this change, the various statutes (passive, scheduled, ...) are no longer functions,
but just strings. So now, therefore it is also possible to say
     passive_time = component.status.value_duration("passive")
This will be quite transparent from the user. Only if the text representation of a status was required,
status() had to be called, like
    print(f"car status={car.status()()}")
From this version on, this should read
    print(f"car status={car.status()}")
, which is also more intuitive.
Alternatively, you can now also write
    print(f"car status={car.status.value}")

This makes the methods Component.ispassive(), Component.isscheduled, etc. less required as
    component.status() == "passive" and
    component.status() == "scheduled"
are arguably easier to understand.

The package salabim now has a function statuses() that returns a tuple with all statuses a component can be in.
So
    print(sim.statuses())
will print
    ('current', 'data', 'interrupted', 'passive', 'requesting', 'scheduled', 'standby', 'waiting')

New functionality (1)
---------------------
Component.mode is now a monitor. That makes it possible to get an overview of all modes a component
has been in, either as a histogram or an animated monitor.
And it is possible to get the duration a component was in a certain mode, with e.g.
    red_time = c1.mode.value_duration("red")
It is even possible to get the mode a component was in at a given moment, like
    mode_4_units_ago = c1.mode(env.now() - 4)
Because of this you can't use mode(x) anymore to set the mode directly. In order to do that, you
have to use the new method set_mode:
    c1.set_mode("green")
or
    c1.mode.value = "green"
Both options do store the modetime correctly.
Please observe that the initial value for mode is now the null string and not None.

New_functionality (3)
---------------------
New method: Monitor.values() to assess all values in a monitor.
The values returned will be alphabetically sorted (not case sensitive), just as in Monitor.print_histogram().
The method supports both ex0 and force_numeric parameter flags.
Example (with same monitor as above):
    print(x1.status.values())
will print
    ['data', 'interrupted', 'passive', 'requesting', 'scheduled']

New functionality (4)
---------------------
The values parameter of print_histogram() can now also be an iterable (i.e. tuple, list or set).
In that case, the statistics of only these values will be shown.
Example (with same monitor as above):
    x1.status.print_histogram(values = sim.statuses())
will print
    Histogram of x.1.status
    duration            40

    value                     duration     %
    current                      0       0
    data                         4.300  10.8 ********
    interrupted                  4      10   ********
    passive                     11.500  28.7 ***********************
    requesting                  10.100  25.2 ********************
    scheduled                   10.100  25.3 ********************
    standby                      0       0
    waiting                      0       0

Any not shown values will be shown at the bottom as '<rest>'.
So, again with the same monitor as above:
    x1.status.print_histogram(values = ("passive", "requesting", "error"))
will print
    Histogram of x.1.status
    duration            40

    value                     duration     %
    passive                     11.500  28.7 ***********************
    requesting                  10.100  25.2 ********************
    error                        0       0
    <rest>                    18.400  46.0 ************************************

New functionality (5)
---------------------
AnimateMonitor and Monitor.animate has got a new parameter: vertical_map.
This parameter should be a function that accepts one argument (the value to be plotted). By default
vertical_map is float.
The function vertical_map should result in a float or raise a TypeError or ValueError.
E.g. to map "red" to the value 1, "blue" to 2, etc., you could provide a mapping function like:
    vertical_map = "unknown red blue green yellow".split().index
Note that in this example any value other than red, blue, green or yellow would map to 0
(via a ValueError exception).
This vertical_map function can also be used to map to a logarithmic scale:
    vertical_map = lambda value_y: math.log(value_y) * 10

New functionality (6)
---------------------
AnimateMonitor and Monitor.animate can now show labels and corresponding lines.
There is full control of the colours, linewidth, fonts, placement, etc. See the docstring or
documentation for details.
There is a sample model (demo animation of labeled monitors.py) in the sample model folder
to illustrate the usage of this new functionality with the new Component.status and
Component.mode monitors.

Changed functionality (0)
-------------------------
The tests for which value(s) to include in
    Montitor.value_number_of_entries()
    Monitor.value_duration()
    Monitor.value_weight()
are now direct and do not involve string conversion anymore. Normally, this won't cause any compatibility issues.

Distribution change (0)
-----------------------
The setup information (used in PyPI) now includes a set of classifiers as well as requires_python information.

Compatibility change (0)
------------------------
Salabim requires Python 3.6 from now on.

Internal change (0)
-------------------
The statuses requesting and waiting were internally stored as scheduled and 'translated' in the status()
method. Now, these statuses are natively stored as such (in the status monitor).

Version 20.0.3  2020-08-06
==========================
New functionality (0)
-----------------------
The specification of sim.Distribution now also accepts a time_unit parameter.
Note that if the specification string contains a time_unit parameter as well, the time_unit parameter
of Distribution is ignored.
Examples
    d = sim.Distribution('uniform(1, 2)', time_unit='minutes'))  # 1-2 minutes
    d = sim.Distribution('uniform(1, 2, time_unit='hours')'))  # 1-2 hours, same as before
    d = sim.Distribution('uniform(1, 2, time_unit='hours')', time_unit='minutes'))  # 1-2 hours, ignore minutes

New functionality (1)
-----------------------
Monitor.freeze() returns a 'frozen' monitor that can be used to store the results not
depending on the current environment.
This is particularly useful for pickling a monitor.
E.g. use
    with open("mon.pickle", "wb") as f:
        pickle.dump(f, mon.freeze())
to save the monitor mon, and
    with open("mon.pickle", "rb") as f:
        mon_retrieved = pickle.load(f)
to retrieve the monitor, later.

Both level and non-level monitors are supported.
Frozen monitors get the name of the original monitor padded with '.frozen' unless specified differently.

New functionality (2)
---------------------
All Component methods that support urgent to schedule a component now also support a priority parameter.
With this it is possible to sort a component before or after other components, scheduled for the same time.
Note that urgent only applies to components scheduled with the same time and same priority.
The priority is 0 by default.
This is particularly useful for race conditions. It is possible to change the priority of a component
by cancelling it prior to activating it with another priority.

The priority can be accessed with the new Component.scheduled_priority() method.

Improved functionality (0)
--------------------------
Video production can now be done with a context manager, thus making an explicit final call to video_close
obsolete:
with env.video('myvideo.mp4'):
    ...
    env.run(10)
    
This will automatically close the file myvideo.mp4 upon leaving the with block.

Change in functionality (0)
---------------------------
In sim.reset(), which is always called at startup, random_seed() will be called without any parameters, causing
the random_seed to be set to 1234567.
That makes reproducibility even possible when calling
   env = sim.Environment(random_seed="")  # no change in seed

If 'real' random behaviour (dependent on clock ticks) is required, just do:
    env = sim.Environment(random_seed="*")
    
Changes in functionality (1)
----------------------------
Queue.extend() does return None now instead of a copy of self, for consistency reasons.

Now queues support all comparisons, i.e. ==, !=, <, <=, >, >=
These comparsons are on membership only, i.e they ignore, the order, priorities and name.
It is possible to compare a quueu with any object supporting the iter protocol, most notably
sets, lists and tuples.

Internal changes /change in functionality (0)
---------------------------------------------
Upon termination of a process, salabim did check a list to see whether there were any animation objects
that had this component as it parent. Particularly with many animation objects defined that could take a long
time, as reported by Hugo Huges.
From this version on, a component itself has a set of its 'animation children'.
Also changed is the moment the animation child is removed automatically. When a parent (component)
is no longer accessible, it will remove all of its animation children if any.
That means we now rely on the automatic garbage collection, which can be slightly delayed.
This change means that an animation object with a parent that terminates its process is not
necessarily removed, as it can be still in a queue, or even just referenced by a variable.
If you use the parent parameter in an Animate, AnimateQueue or AnimateMonitor this might change the
behaviour.

Added support files (0)
-----------------------
For the development there's is now a set of pytest files that will result in a more stable product. Indeed
several bugs (see below) were detected during this test development.
Future versions will include more test scripts.

Bug fix (0)
-----------
Minor bug in 'install salabim from github.py' and 'install salabim.py' fixed.

Bug fix (1)
-----------
Bug in Component.wait() fixed. Thank you, Alexander Kaiblinger, for detecting the bug and proposing the solution.

Bug fix (2)
-----------
Upon honouring an anonymous resource, the statistics of the available_quantity, claimed_quantity and occupancy
were not updated. Bug fixed. Thank you, Lukas Hollenstein, for detecting the bug and proposing the solution.

Bug fix (3)
-----------
The algorithm used to calculate weighted percentiles in Monitor.percentile() from a stackoverflow.com article
was found to be incorrect, thus sometimes resulting in wrong percentiles.
Bug fixed.

Bug fix (4)
-----------
Minor changes in Queue.__iter__ and Queue.__reversed__ to make iterating when components are added or removed
during the iteration more consistent.


version 20.0.2  2020-05-18
==========================
New functionality (0)
---------------------
Component.request() has a new parameter 'oneof'.
If oneof=True, the request has to be honoured by just one of the given resources.
So, this essentially an or condition.
Note that the order of the mentioned resources is the order in which the request will be honoured.
It is possible to check which resource has claimed with Component.claimers()

Example:
    c.request(r1, r2, r3, oneof=True)
The request will be honoured if either r1, r2 OR r3 has at least a quantity of one available.
This contrast to
    c.request(r1, r2, r3)
, which will be honoured if r1, r2 AND r3 have at least a quantity of one available.

The trace of request and honouring request has been updated accordingly.


Changes in video production (0)
-------------------------------
With this version, animated PNGs are supported as well. In contrast to animated GIFs, the background
can be transparent (i.e. have an alpha <255).

For the production of individual video frames in jpg, png, bmp, tiff or gif format, the filename
now has to contain one asterisk (*), which will be replaced by a 6 digit zero-padded serial number
at run time, for each frame.
E.g.
    video('.\videos\car*.jpg)
Filenames without an asteriks are only allowed for real videos or animated gif/png files:
    videos('.videos\car.png')
Note that the directory is now automatically created.
Because of the changes, the Environment.delete_video() is now deprecated.

Internally, the video production is now more consistent and easier to maintain.

Improved functionality (0)
--------------------------
Under Linux and Android many more fonts will be available because salabim now searches (recursively)
in /usr/share/fonts and /system/fonts for .ttf files as well.
As a reminder: it is possible to show all available fonts with
    sim.show_fonts()


Utility files (0)
-----------------
The utility 'install.py' is now called 'install salabim.py' and is now fully compatible with
pip uninstall and pip update, because a salabim-<version>.dist-info directory is written correctly
to the site-packages folder.

New is 'install salabim from github.py' which installs salabim directly from github instead of PyPI.


Support for iPadOS/iOS PyTo (0)
-------------------------------
When running under PyTo, a NotImplementedError was raised. Now, salabim can be run on this platform, albeit
animation is not supported.


Compatibility (0)
-----------------
From now on, only Python >=3.4 is supported, particularly because salabim now uses pathlib internally.


Bugfix (0)
-----------
In a number of methods, e.g. Queue.__init__(), the environment of an implied Monitor was set to the
default environment instead of the overruled environment.


Bugfix (1)
-----------
PeriodMonitor lacked an env parameter. Fixed.


Bugfix (2)
-----------
Under certain conditions, an animated GIF was not written correctly as a result of a bug in the optimization
of PIL save. From now on, salabim disables the optimization, possibly resulting in slightly larger
.GIF files. This change does not apply to Pythonista, which uses another technique to save animated GIFs.

Bugfix (3)
-----------
Under Pythonista, video production (animated gif only) did not start at the right time.
Fixed.

Internal changes (0)
--------------------
In order to support the new oneof parameter of request, the data structure of _requests and _claims is now
collections.OrderedDict instead of collections.defaultdict.

version 20.0.1  2020-02-27
==========================
New functionality (0)
---------------------
A new class ComponentGenerator is introduced.
With this, component can be generated according to a given inter arrival time (distribution) or a random spread
over a given interval.
Examples:
    sim.ComponentGenerator(Car, iat=sim.Exponential(2))
    # generates Cars according to a Poisson arrival
    
    sim.ComponentGenerator(Car, iat=sim.Exponential(2), at=10, till=30, number=10)
    # generates maximum 10 Cars according to a Poisson arrival from t=10 to t=30
    
    sim.ComponentGenerator(Car, iat=sim.Exponential(2), at=10, till=30, number=10, force_at=True)
    # generates maximum 10 Cars according to a Poisson arrival from t=10 to t=30, first arrival at t=10
    
    sim.ComponentGenerator(sim.Pdf((Car, 0.7, Bus, 0.3)), iat=sim.Uniform(20,40), number=20)
    # generates maximum 20 vehicles (70% Car, 30% Bus) according to a uniform inter arrival time
        
    sim.ComponentGenerator(Car, duration=100, n=20)
    # generates exactly 20 Cars, random spread over t=now and t=now+100

ComponentGenerator is a subclass of Component and therefore has all the normal properties and methods of an
ordinary component, altough it is not recommended to use any the process methods, apart from cancel.

Added functionality (0)
-----------------------
It is now possible to suppress line numbers in the trace.
Particularly when the trace output is written to a file, this can result in dramatic (up to 50 times!)
performance increase, because the calculation of line numbers is very demanding.
Now, therefore a method Environment.suppress_trace_linenumbers() has been introduced.
Like:
    env = sim.Environment(trace=True)
    env.suppress_trace_linenumbers(True)
By default, line numbers are not suppressed in the trace.
The current status can be queried with
    print(env.suppress_trace_linenumbers())


version 20.0.0  2020-02-10
==========================
Announcement (0)
----------------
Salabim now runs fully also on Android platforms under the excellent Pydroid3 app
    <https://play.google.com/store/apps/details?id=ru.iiec.pydroid3&hl=en>.
In order to use animation on that platform, it is required to import tkinter in the main program
, otherwise you will get a salabim error message if you try and start an animation.

With the PyDroid3 Premium version, your can also produce animation videos, albeit only .avi files.

AnimateButton does not properly yet and therefore the animation navigation buttons are not
placed correctly and in fact not usable. We plan a fix for this in a future version of salabim.
    

New functionality (0)
---------------------
An AnimateQueue object now has a queue() method that returns the queue it refers to.
This is useful in animation_objects() that want to check the queue (in the id parameter).


Improved functionality (0)
--------------------------
Normal video production (i.e. not .gif, .jpg, .bmp, .tiff, .png) is now done via a temporary file.
That has the effect that if the video production is not closed properly, the video is not written at all,
thus making the production process more stable.
It is necessary to always close the video production with
    env.video("")
    

Changed functionality (0)
-------------------------
If a video name with extension .avi is to be produced (with env.video()), the default codec is now MJPG.
For all other extensions, the default codec remains MP4V.


Utility update (0)
------------------
The install.py utility is changed internally. Also, it shows now the location where salabim was installed.


Documentation (0)
-----------------
The width parameter of AnimateImage was not documented. Fixed.


Documentation (1)
-----------------
Closing a video is now documented (see also above).


Bug fix (0)
-----------
Minor bug in video production, when animation was turned off and on during the simulation. Fixed.

version 19.0.10  2019-12-18
===========================
New functionality (0)
---------------------
Map distribution allows sampled values from a distribution to be mapped to
a given function. E.g.
    round_normal = sim.Map(sim.Normal(10, 4), lambda x: round(x))
or, equivalently:
    round_normal = sim.Map(sim.Normal(10, 4), round)
The sampled values from the normal distribution will be rounded.
Another example:
    positive_normal = sim.Map(sim.Normal(10, 4), lambda x: x if x > 0 else 0)
Negative sampled values will be set to zero, positive values are not affected.
Note that this is different from
    sim.Bounded(sim.Normal(10, 4), lowerbound=0)
as in the latter case resampling will be done when a negative value is sampled,
in other words, virtually no zero samples.

New functionality (1)
---------------------
Introduced an AnimateCombined class with which it is possible to combine several instances of
AnimateText, AnimateCircle, AnimateRectangle, AnimatePolygon, AnimateLine, AnimatePoints,
AnimateImage or another AnimateCombined.
AnimateCombined works as a list, so can be filled by initializing with a list of Animatexxx instances, like
    a = sim.AnimateCombined((a0, a1, a2))
, but can also be build up with
    a.append(a3)
    a.extend((a4, a5))
    a += a6
etc.
It is then possible to set an attribute of the combined animation objects, like
    a.x = 100
This will set the x for all animation objects to 100.
It is required that each of animation objects in an AnimatCombined instance supports the attribute
to be set! That means that you cannot set the radius for an AnimateCombined instance with an` AnimateCircle
and an AnimateRectangle, as the latter does not support radius.
If an attribute of an AnimateCombined instance is queried, the value for the first animation object will be returned.
It is possible to put AnimateCombined instances in another AnimateCombined object.

The remove method applied to AnimateCombined objects will remove all the included animation objects.

Changed functionality (0
--------------------------
In version 19.0.6 the following functionality was introduced:
    If an error occurred in the make_pil_image method during an animation, it was sometimes difficult to
    find out the reason for that error. From this version on, the line number (and the filename)
    where the animation object was created will be added to the error message, which makes debugging
    hopefully easier.
However, this feature sometimes appears to significantly slow down animations.
Therefore, this feature is now disabled by default.
If required (particularly when finding a complicated error), it is possible to enable the source location
tracking. The method Environment.animation_parameters() has therefore now a new parameter: animate_debug,
which is False by default.
Alternatively, the method Environment.animate_debug() can be used.

Changed functionality (1)
-------------------------
sim.Environment() now automatically resets the simulation environment when run under Pythonista.
A parameter 'do_reset' to sim.Environment() allows the user to force a reset as well, or to indicate
that no reset should be executed under Pythonista.

Internal change (0)
-------------------
The install.py file has been internally changed to support other single source
packages. No functional changes.

version 19.0.9  2019-10-08
==========================
New functionality (0)
---------------------
Introduced preemptive resources

It is now possible to specify that a resource is to be preemptive, by adding preemptive=True when the resource
is created.
If a component requests from a preemptive resource, it may bump component(s) that are claiming from
the resource, provided these have a lower priority = higher value).
If component is bumped, it releases the resource and is the activated, thus essentially stopping the current
action (usually hold or passivate).
Therefore, it is necessary that a component claiming from a preemptive resource should check
whether the component is bumped or still claiming at any point where they can be bumped.
This can be done with the method Component.isclaiming which is True if the component is claiming from the resource,
or the opposite (Component.isbumped) which is True is the component is not claiming from te resource.

E.g. if the component has to start all over again (hold(1)) if it is bumped:
    def process(self):
        prio = sim.Pdf((1,2,3), 1)
        while True:
            yield self.request((preemptive_resource, 1, prio)
            yield self.hold(1)
            if self.isclaiming(preemptive_resource):
                break
        self.release(preemptive_resource)
                
E.g. if the component just has to 'complete' the hold time:
    def process(self):
        prio = sim.Pdf((1,2,3), 1)
        remaining = 1
        while True:
            yield self.request((preemptive_resource, 1, prio)
            yield self.hold(remaining, mode='')
            if self.isclaiming(preemptive_resource):
                break
            remaining -= (env.now() - self.mode_time())
        self.release(preemptive_resource)

Note that a component that hasn't requested at all from a resource, it is considered as bumped, therefore the above
example can be rewritten as:
    def process(self):
        prio = sim.Pdf((1,2,3), 1)
        remaining = 1
        while isbumped(preemptive_resource):
            yield self.request((preemptive_resource, 1, prio)
            yield self.hold(remaining, mode='')
            remaining -= (env.now() - self.modetime())
        self.release(preemptive_resource)
        
Finally, if the component is dealing with just one preemptive resource (which is very likely), the isbumped()
and isclaiming() methods can be used without an argument:
        prio = sim.Pdf((1,2,3), 1)
        remaining = 1
        while isbumped():
            yield self.request((preemptive_resource, 1, prio)
            yield self.hold(remaining, mode='')
            remaining -= (env.now() - self.modetime())
        self.release(preemptive_resource)
                
If a request for a preemptive resource is made, it is not possible to combine that request with any other
resource.

The method Resource.ispreemptive() can be used to check the whether a resource is preemptive.

There is an animated demo showing nicely the difference between preemptive and non preemptive resources
See salabim./sample models/Demo preemptive resources animated.py.

New functionality (1)
---------------------
In the trace, the time of rescheduling of Component initialization, activate, hold, request, wait and run
the time was always shown in the information field of the trace as 'scheduled for xxx'.
From this version, also the delta time (if not 0 of inf) is shown as +xxx behind the action, e.g.

   75+      1.000 main                 current
   76                                  client.0 create
   76                                  client.0 activate                    scheduled for      1.000 @   59  process=process
   77                                  client.1 create
   77                                  client.1 activate +1.000             scheduled for      2.000 @   59  process=process
   78                                  client.2 create
   78                                  client.2 activate +3.000             scheduled for      4.000 @   59  process=process

New functionality (2)
---------------------
The trace parameter in Environment() and Environment.trace() can now be a file handle.
If so, the trace output will be directed to the file given, provided it is opened for output.
When the trace parameter is not an 'open for write' file handle, but is 'Truthy' (usually True),
the trace output is sent to stdout, as before.
When the parameter is 'Falsy', no trace output will be generated, as before.

Example:
    import salabim as sim
    
    class X(sim.Component):
        pass
    
    out = open('output.txt', 'w') as out:
    env = sim.Environment(trace=out)
    
    env.trace(True)
    X()
    env.trace(False)
    X()
    env.trace(out)
    X()
    env.trace(False)
    out.close()

After execution, the file output.txt contains:
    line#        time current component    action                               information
    ------ ---------- -------------------- -----------------------------------  -------------------------------
                                           line numbers refers to               test.py
        8                                  default environment initialize
        8                                  main create
        8       0.000 main                 current
        9                                  x.0 create data component

And the following output is generated:
       12                                  x.1 create data component
       
Note that by issueing env.trace(False), the file is not closed, so that has to be done explicitely or with
a context manager.
       

Changed functionality (0)
-------------------------
The default priority of a requested resource is now inf, which means the lowest possible priority.
In practice, this will hardly ever make a difference with the former behaviour that if no priority was given, it was
added to the tail of the requesters

When a request is honoured, the component now enters the claimers queue with priority as it had in the requesters
queue. Again, in practice this will hardly make any difference.

Bugfix (0)
-----------
A bug with autonumbering components, queues, etc. by ending the name with a comma, like
    for _ in range(3):
        Car(name='car,')
fixed.
Now, the cars are correctly named car.1, car.2 and car.3 .

Bugfix (1)
-----------
On some platforms PIL does not accept a new image with a width or height of 0. Therefore, salabim now
sets the dimensions for a dummy image to (1, 1).

Bugfix (2)
-----------
As a leftover from a test, the seed was printed when an Environment was created. Removed.


version 19.0.8  2019-09-17
==========================
New functionality (0)
---------------------
The time related parameters of the methods methods mentioned below can now be called with a
distribution instead of a float value ('auto sampling ').

Method                    parameters that can be auto sampled
------------------------  -----------------------------------
sim.Component             at, delay
Component.activate        at, delay
Component.hold            duration, till
Component.request         fail_at, fail_delay
Component.wait            fail_at, fail_delay
Environment.run           duration, till
Environment.reset_now     new_now
Environment.years, ...    t
Environment.to_time_unit  t
Environment.to_years, ... t

If a distribution is given, the distribution will be sampled.
So,
    car = Car(delay=sim.Normal(100,10))
is equivalent to
    car = Car(delay=sim.Normal(100,10).sample())
and
    car = Car(delay=sim.Normal(100,10)())
    
This makes it possible to intermix floats/ints and distributions, without having to worry about sampling, e.g.
    set_up_time = 6
    processing_time = Normal(10, 1)
    reaction_time = sim.Constant(10)
    ...
    yield self.hold(set_up_time)
    yield self.hold(processing_time)
    yield self.hold(env.hours(reaction_time))
    
Note that salabim also supports basic expressions for distributions, so it is even possible to do something like
    yield self.hold(2 * setup_time + processing_time)
    
New functionality (1)
---------------------
Introduced a new distribution, External, that makes it possible to specify an 'external' statistical
distribution from the modules
* random
* numpy.random
* scipy.stats
as were it a salabim distribution.
The class takes at least one parameter (dis) that specifies the distribution to use, like
* random.uniform
* numpy.random.uniform
* scipy.stats.uniform
Next, all postional and keyword parameters are used for sampling. In case of random and numpy.random by calling
the method itself, in case of a scipy.stats distribution by calling rvs().

Examples:
    d = sim.External(random.lognormvariate, mu=5, sigma=1)
    d = sim.External(numpy.random.laplace, loc=5, scale=1)
    d = sim.SciPyDis(SciPy.beta, a=1, loc=4, scale=1)
Then sampling with
    d.sample()
or
    d()
    
If the size is given (only for numpy.random and scipy.stats distributions), salabim will return the sampled values successively. This can be useful to increase performance.

The mean() method returns the proper mean for scipy.stats distributions, nan otherwise.

If a time_unit parameter is given, the sampled values will be multiplied by the applicable factor, e.g.
    env = sim.Environment(time_unit='seconds')
    d = sim.ScyPyDis(SciPy.norm, loc=2, time_unit='minutes')
    print(d.mean())
will print out
    120

New functionality (2)
---------------------
Bounded distribution now has a time_unit parameter to specify the lowerbound or upperbound.

New functionality (3)
---------------------
IntUniform distribution now also supports a time_unit. If used, the returned value will be scaled accordingly.
E.g.
    env = sim.Environment('seconds')
    d = sim.IntUniform(1, 2, time_unit='minutes')
    print(d.sample())
will print either 60 or 120.

Improvement (0)
---------------
When trying to animate text for a None object, salabim issued an error, about absence of .strip().
Now, None will be handled as the null string ("")

Improvement (1)
---------------
When a distribution with a time unit was specified without an Environment was instantiated, a rather obscure error
message was shown. Now, a clear error message will be shown, in that case.

Implementation note (0)
-----------------------
Provided numpy is installed, now numpy.random is seeded at init of Environment() and when calling random_seed,
unless the set_numpy_random_seed parameter is False.
This is particularly useful when using External distributions with
numpy.random or scypi.stats distributions. Therefore, unless explicitely overriden, also those
distribution sampling will be reproducable.
Related to this is an internal change in the way Environment seeds random.

Implementation note (1)
-----------------------
Change in the way time_units are handled internally.

version 19.0.7  2019-08-12
==========================
Bug fix (0)
-----------
Rare error in multiplication of monitors (and thus Monitor.to_hours, etc) fixed.

version 19.0.6  2019-07-09
==========================
Improved functionality (0)
--------------------------
AnimateMonitor and Monitor.animate() now allow rotation of an animated monitor.
This is particularly useful for animating a monitor from top to bottom (angle = 270),
instead of from left to right (angle=0)
The rotation angle is specified with the angle parameter, which defaults to 0.
Also, offsetx and offsety are now supported for AnimateMonitor and Monitor.animate().

Improved functionality (1)
--------------------------
The spec parameter of AnimateLine, AnimatePoints, AnimateRectangle and AnimatePolygon can now use None to repeat
a previous x or y-coordinate.
The same holds for the line0/line1, rectangle0/rectangle1, polygon0/polygon1 parameters of Animate and
Animate.update().
From now on it is therefore possible to say for instance:
    sim.AnimateLine(spec=(100, 0, 900, None, None, 600))
which is equivalent to
    sim.AnimateLine(spec=(100, 0, 900, 0, 900, 600))
And it even possible to say:
    sim.AnimatePoints(spec=100, 400, 150, None, 200, None, 300, None)
which is equivalent to
    sim.AnimatePoints(spec=100, 400, 150, 400, 200, 400, 300, 400)
    
Improved functionality (2)
--------------------------
Applications can now retrieve the salabim version consistenty with sim.__version__.
Previously, this had to be done with
- sim.__version__ if salabim.py is in the current directory
- sim.salabim.__version__ if salabim.py is not in the current directory
Techinal note: This change is actually in the __init__.py file rather than in salabim.py.
For comparisons of versions, distutils.version.StrictVersion() is recommended.

Improved functionality (3)
--------------------------
If an error occured in the make_pil_image method during an animation, it was sometimes difficult to
find out the reason for that error. From this version on, the line number (and the filename)
where the animation object was created will be added to the error message, which makes debugging
hopefully easier.

Bug fix (0)
-----------
Creating a video with audio did crash sometimes. Fixed.

Bug fix (1)
-----------
Under Pythonista (iOS), animation objects were not properly sorted, thus causing layer values sometimes to be
ignored. Fixed.

Bug fix (2)
-----------
When querying a tallied value from a level monitor, either with mon.get(t) or mon(t), the values were not correct
when a Environment.reset_time() was applied. Fixed.


version 19.0.5  2019-06-20
==========================
New functionality (0)
---------------------
Level monitors have two new properties:
- value, which can be used to get the current value of a monitor, i.e
    a = m.value is equivalent to a = m.get() and a = m()
  value can also be used to tally a value, i.e.
    m.value = 10 is equivalent to m.tally(10)
  Combining the getter and the setter is useful in constructs like
    m.value += 100, which is equivalent to m.tally(m.get() + 100)
- t, which can be used to get the time the last value was tallied.

Combining these two is for instance useful to calculate the cost of storage over a period, such as
  costs += (env.now() - inventory.t) * inventory.value * cost_per_day
  inventory.value -= consume
Both value and t are available can be used even if the monitor is turned off.

Note that these two properties are only available for level monitors.

Note that this functionality is also available for the capacity of a resource, which means that increasing
the capacity of a resource by 1 can now be done with
    res.set_capacity(res.capacity() + 1)
or
    res.capacity.value += 1
    
The following standard salabim level monitors do support only *getting* the value and (for obvious reasons)
not *setting* the value:
- Queue.length()
- Resource.available_quantity()
- Resource.claimed_quantity()
- Resource.occupancy()
- State.value()


New functionality (1)
---------------------
Anonymous resources can now request for a negative quantity. In that case, the request gets honoured if
the claimed quantity is greater than or equal to minus the requested quantity.
In case of these anonymous resources, it might be easier to think in terms of get and put, like in
SimPy.Container. Therefore, salabim introduces to new methods:
- Component.get(), which is equivalent to Component.request
- Component.put(), which is equivalent to Component.request, but where the quantity of anonymous resources
  is negated.
  Thus yield self.request((r, -5)) is the same as yield self.put((r, 5)) if r is defined as
  r = sim.Resource(name='r', anonymous=True)
  Note that in the trace, the text 'request honor' will be shown even for get or request calls.
  Also, isrequesting() will be True if a component is waiting for a get or put honor.
  The Gas station model in sample models illustrates the get/put functionality.

Note that you can still 'refill' an anonymous resource without checking for exceeding the capacity, with a call to Resource.release(). In many cases that will be sufficient.


New functionality (2)
---------------------
On Windows and Pythonista platforms, an audio track (usually an mp3 file) may be played during animation.
This particularly during the development of lip synchronized videos.
Therefore, a new method Environment.audio() has been introduced.
Alternatively, the new parameter audio of Environment.animation_parameters() can be used to specify which
mp3 to be played.
It is recommended not to use variable bit rate (vbr) mp3 files, as the length can't be detected correctly.
Note that audio is only played when the animation speed is equal to audio_speed, which is 1 by default.
The audio_speed may be changed with Environment.audio_speed() or the new parameter audio_speed of
Environment.animation_parameters().
On other platforms than Windows or Pythonista, the audio functions are ignored.

The duration of an audio file (usually an mp3 file) can be retrieved with sim.audio_duration(filename).
On other platforms than Windows or Pythonista, a length of zero will be returned when sim.audio_duration() is called.

New functionality (3)
---------------------
On Windows platforms, an audio track can now be added to a video animation.
The audio is controlled by Environment.audio() commands (see above).
In order to add audio to a video, ffmpeg must be installed and included in the environment path.
See www.ffmpeg.org for download and installation instructions.


New functionality (4)
---------------------
When animating images, the alpha (transparency channel) can now be specified.
Therefore, Animation() and Animation.update() have two extra arguments: alpha0 and alpha1.
AnimateImage() has an extra parameter alpha.
The alpha value should be between 0 (fully transparent) and 255 (not transparent).
Note that if an image has alpha values other than 255, these are scaled accordingly.
Images with an alpha values of less than 255 are rendered quicker when numpy is installed.


Improved performance (0)
------------------------
Animation objects that are completely out of the frame are suppressed now. This results in better
performance when many animation objects are not visible anyway.


Improved performance (1)
------------------------
Rendering speed of animated text improved, particularly when numpy is installed.


Experimental functionality (0)
------------------------------
Experimental support for retina screens on supported iOS devices (Pythonista only).
By adding retina=True to the Environment() call, iOS devices will double the number of pixels, both
in height and width. As of now, buttons and sliders are not shown in retina mode.


Bug fixes (0)
-------------
In some Ubuntu environments, install.py could not install salabim correctly.
This has been fixed with this release.


version 19.0.4  2019-05-03
==========================
New functionality (0)
---------------------
Queue.extend() has an extra parameter, clear_source. If clear_source = True, the given source will be cleared
after copying the elements to self.
This means that
    q0.extend(q1, clear_source=True)
effectively transfers all elements of q1 into q0, prior to emptying q1.
Note that clear_source cannot be applied if source is a list or a tuple.

New functionality (1)
---------------------
non-level monitors can now be filled from a list or tuple, like
    m = Monitor("my monitor", level=False, fill=(1,2,5,7,2,3))
which is functionally equivalent to
    m = Monitor("my monitor", level=False)
    for el in (1,2,5,7,2,3):
        m.tally(el)

Bug fix (0)
-----------
Autoscaling of histograms was incorrectly always enabled.
Now histograms are autoscaled only if neither number_of_bins, nor lowerbound nor bin_width is specified.

Bug fix (1)
-----------
Due to a problem with the Black formatter, version 19.0.3 did not run under Python versions prior to 3.6.
This is fixed with this release.


version 19.0.3  2019-04-21
==========================
New method (0)
--------------
Monitor.rename() can be used to rename a monitor in a chained way.
This is particularly useful when merging with the + operator, merging with sum or slicing with [],
multiplication and division as well as the unit conversion methods (to_years, ...),
because the resulting monitors get automatically a name, that might not be appropriate.
The Monitor.rename() method is essentially the same as Monitor.name(), but will return the monitor itself.
Examples:
    (mon0 + mon1 + mon2 + mon3).rename('mon0 - mon3').print_histogram()
    sum(mon for mon in (mon0, mon1, mon2, mon3)).rename('mon0 - mon3').print_histogram()
    mon0[1000:2000].rename('mon0 between t=1000 and t=2000').print_statistics()
    mon0.to_years().rename('mon0 in hours').print_statistics()


New method (1)
--------------
Queue.rename() can be used to rename a queue in a chained way.
This particularly useful when the queues are combined with +, -, |, & and ^ operator or the sum function,
because the resulting queue get automatically a name, that might not be appropriate.
The Queue.rename() method is essentially the same as Queue.name(), but will return the queue itself.
Examples:
    (q0 + q1 + q2 + q3).rename('q0 - q3').print_statistics()
    (q1 - q0).rename('difference of q1 and q0)').print_histograms()
    

New functionality
-----------------
It is now possible to get the union of several queues by means of the sum function.
Example:
    rows = [Queue('row.') for _ in range(10)]
    ...
    sum(rows).print_info()


Improved functionality (0)
--------------------------
When animating a large number of objects, it was possible that tkinter crashed because there were too many tkinter
bitmaps aka canvas objects, sometimes by issuing a 'Fail to allocate bitmap', sometimes without any message.
From this version on, salabim limits the number of bitmap automatically by combining animation objects
in one aggregated bitmap if the number of bitmaps exceeds a given maximum.
Unfortunately it is not possible to detect this 'Fail to allocate bitmap', so it may take some experimentation to
find a workable maximum (maybe going as low as 1000).
By default, salabim sets the maximum number of bitmaps to 4000, but may be changed with the
Environment.maximum_number_of_bitmaps() method, or the maximum_number_of_bitmaps parameter of
Environment.animation_parameters().
Choosing a too low maximum (particularly 0), may result in a performance degradation.
The bitmap aggregation process is transparent to the user, but improves the usability of salabim.
Note that does this not apply to the Pythonista implementation, where bitmaps are always aggregated.


Improved functionality (1)
--------------------------
When using the new style Animate classes (AnimateLine, AnimateRectangle, ...), texts are optional. Up to
this version, even a blank text (which is the default), resulted in a small 'empty' bitmap to be 'displayed'.
From this version, these blank texts are ignored automatically , which is transparent to the user but can result
in better performance and reduces the probability of a tkinter crash.


Changed functionality (0)
-------------------------
The method Environment.animation_parameters() does no longer automatically enable animate, but
instead leaves the animate status unchanged. So, if the user now wants to start the animation as
well when specifying other parameters, it is necessary to add animate=True.
Or, better yet, specify the various parameters with their corresponding method and use
env.animate(True).
E.g. instead of
    env.animation_parameters(x0=100, modelname="My model")
use now
   env.animation_parameters(x0=100, modelname="My model", animate=True)
or
   env.x0(100)
   env.modelname("My model")
   env.animate(True)


Changed functionality (1)
-------------------------
When creating an animated video, the default codec is now mp4v instead of MP4V.
If this causes a problem in an appication, just add +MP4V to the filename, like
    env.video("my_video.mp4+MP4V")


Changed functionality (2)
-------------------------
The function random_seed is defined in a slightly different way and is now in line with
the random_seed parameter of Environment().
The docstring and the documentation have been updated accordingly.

Bug fixes
---------
Minor error in AnimateMonitor and Monitor.animate() for non-level monitors fixed.

version 19.0.2  2019-03-25
==========================

New functionality
-----------------
It is now possible to scale the output of non-level monitor, which is most useful for the automatically
registered length_of_stay monitor of queues. For instance, if the time unit of the simulation is days,
the duration in the queue (q) is registered in days. Buf if a histogram in minutes is more appropriate,
it is possible to say
    q.length_of_stay.to_hours().print_histogram()
Equivalent methods are available for year, weeks, days, minutes, seconds, milliseconds and microseconds.
Alternatively the method Monitor.to_time_unit() might be used as in
    q.length_of_stay.to_time_unit('minutes').print_histogram()
Finally, a monitor may be scaled with a given factor, e.g.
    q.length_of_stay.multiply(24 * 60).print_histogram()
or even
    (q.length_of_stay * 24 * 60).print_histogram()

Here is a list of all the new Monitor methods:

Monitor.multiply()
Monitor.to_years()
Monitor.to_weeks()
Monitor.to_days()
Monitor.to_hours()
Monitor.to_minutes()
Monitor.to_seconds()
Monitor.to_milliseconds()
Monitor.to_microseconds()
Monitor.to_time_unit()

On top of Environment.to_years, Environment.to_weeks, etc., there is now a generic method
    Environment.to_time_unit()
For instance,
    env.to_minutes(env.now)
is equivalent to
    env._to_time_unit('minutes', env.now)
    

Bug fixes
---------
Minor error in run without a duration or till parameter fixed (was not correctly fixed in version 19.0.1)
Bug in Queue.extend() fixed.
Bug in Queue.clear() fixed.

version 19.0.1 2019-03-02
=========================
Added functionality
-----------------
The methods Queue.add, Queue.append, Queue.add_at_head, Queue.add_sorted, Queue.add_in_front_of,
Queue.add_behind, Queue.insert, Queue.remove now return the the queue itself (self), in order
to allow chaining,like
    waitingline.add(car1).add(car2)


Documentation update
--------------------
The documentation has been enhanced.
A section on using monitors in other packages, like matplotlib has been added.
This includes a hint to use
    plt.plot(*waitingline.length.tx(), drawstyle="steps-post")
to generate a plot from a level monitor.


Bug fixes
---------
Minor error in run without a duration or till parameter fixed.

version 19.0.0 2019-01-01
=========================
New functionality
-----------------
Queues now register the arrival rate and the departure rate, defined as
   number of arrivals since last reset / duration since last reset
   number of departures since last reset / duration since last reset
The following methods are available:
    Queue.arrival_rate()
    Queue.departure_rate()
The registration can be reset with
    Queue.arrival_rate(reset=True)
    Queue.departure_rate(reset=True)
Note that this functionality is completely independent of the monitoring.


Added functionality
-------------------
Video production now supports also the creation of a series of individual frames, in
.jpg, .png, .tiff or .bmp format.
By specifying video with one of these extension, the filename will be padded with 6 increasing digits, e.g.
    env.video('test.jpg')
will write individual autonumbered frames named
    test000000.jpg
    test000001.jpg
    test000002.jpg
    ...
Prior to creating the frames, all files matching the specification will be removed, in order to get only
the required frames, most likely for post processing with ffmpeg or similar.

Note that individual frame video production is available on all platforms, including Pythonista.


The method Environment.delete_video() can be used to delete all autonumbered files, like
    env.delete_video('test.jpg')
will delete
    test000000.jpg
    test000001.jpg
    test000002.jpg
    ...
If this method is used with any other file type, like .mp4, the file does not need to exist (i.e. no action is taken then).


Announcements
-------------
From this version, salabim uses the CalVer (see www.calver.org) standard for version numbering.
This means that versions are numbered YY.major.minor, where
  YY is the year of the release minus 2000
  major is the major version number (0 based)
  minor is the minor version number (0 based)

From this version, legacy Python (<= 2.7) is not longer officially supported.

version 2.4.2  2018-11-01
=========================
Added functionality
-------------------
Sampling from a Pdf distribution now also supports getting a number of samples without replacement.
In order to be able to use that, all probabilities have to be the same, like
    colors_dis = sim.Pdf(("red", "green", "blue", "yellow"), 1)
Then we can get a random list of all colors with
    colors_dis.sample(4)  # e.g. ["yellow", "green", "blue", "red"]
or two randomly choosen colors, without replacement with
    colors_dis.sample(2)  # e.g. ["green", "blue"]
Note that if  n=1, a list of one value will be returned
    colors_dis,sample(1)  # e.g. ["blue"]


Bug fixes
---------
Under some conditions, Monitor.merge() did not work properly. Fixed.
Under rare conditions Pdf did not handle timeunits properly. Fixed.

Internal changes
----------------
The code is now 'blackened', causing neater and more consistent formatting.
This has not any effect on the functionality.

Sampling from a Pdf distribution has been optimized.


version 2.4.0  2018-10-23
=========================

Added functionality
-------------------
Apart from Monitor.merge(), monitors can now be merged also with the + operator, e.g.
    print((m0 + m1 + m2).mean())
is equivalent to
    print(m0.merge(m1, m2).mean())
It is also possible to use the sum function to merge a number of monitors. So,
    print(sum((m0, m1, m2)).mean())
is equivalent to the constructs above.
And if ms = (m0, m1, m2), it is also possible to use:
    print(sum(ms).mean())
A practical example of this, is the case where the list waitinglines contains a number of queues.
Then to get the aggregated statistics of the length of all these queues, use:
    sum(waitingline.length for waitingline in waitinglines).print_statistics()
    

Distributions can now be used in expressions. This creates an _Expression distribution which can be sampled from.
Examples:
    d0 = 5 - sim.Uniform(1, 2)  # equivalent to Uniform (3, 4)
    d1 = sim.Normal(4, 1) // 1  # integer samples of a normal distribution
    d2 = sim.IntUniform(1,5) * 10)  # to return 10, 20, 30, 40 or 50.
    d3 = (1 / sim.Uniform(1, 2))()  # to return values between 0.5 and 1 (not uniform!)
    d4 = sim.Pdf((0, 1, 2, 3, 4, 5, 6), (18, 18, 18, 18, 18, 8,2), 'days') +
        sim.Cdf((0,0, 8,10, 17, 90, 24, 100), 'hours')
        # this generates an arrival moment during a week, with emphasis on day 0-4.
        # The distribution over the day concentrates between hour 8 and 17.
    d5 = sim.Uniform(1,2) * (10 + sim.Triangular(1,3,2) + sim.Normal(2,1)) ** 3  # over the top or what?

An instance of the class _Expresssion can be used as any other distribution.
For example, each expression below returns 10, 20, 30, 40 or 50.
    d2.sample()
    sim.IntUniform(1,5) * 10).sample()
    sim.IntUniform(1,5) * 10)()
    
Like all distributions, the _Expression class supports the
mean(), sample(), bounded_sample() and print_info() methods.
If the mean can't be calculated, mean() will return nan.
    (sim.Uniform(1, 2) / 10).mean()  # 0.15
    (10 / sim.Uniform(1, 2)).mean()  # nan
    (sim.Uniform(1, 2) / sim.Uniform(1, 2)).mean()  # nan


Added a special distribution class: Bounded.
This class can be used as a replacement of a distribution's bounded_sample method(), with
the advantage that the boundaries can now be specified at time of definition.
Examples:
    dis = sim.Bounded(sim.Normal(3, 1), lowerbound=0)
    sample = dis.sample()  # normal distribution, non negative
    sim.Bounded(sim.Exponential(6, upperbound=20).sample()  # exponential distribution <= 20
    sim.Bounded(sim.Exponential(6, upperbound=20)()  # exponential distribution <= 20
The bounded_sample() method of distributions is still available, but not preferred.
Like all distributions, the Bounded class supports the mean(), sample() and print_info() methods.


Modified exception handling
---------------------------
Salabim does not generate SalabimError exceptions anymore. Instead, the appropriate standard exceptions
(primarily ValueError and TypeError) are raised, if required.
Also several error messages contain more (useful) information.


Added validation checks
-----------------------
Check for tallying 'off' in a level monitor added. If so, a SalabimError exception is raised.
Check for enabling merged and sliced monitors added. If so, a SalabimError exception is raised.


Bug fixes
---------
Bug in Monitor.merge() fixed.


Documentation
-------------
The documentation is updated considerably, particularly with respect to recent features.
Also, a section on interpretation and controlling trace output has been added (cf. Miscellaneous).


Compatibility
-------------
Salabim has been tested against Python 3.7, with success.
Legacy Python (aka version 2.7) is still supported (till at least 31 December 2018).


version 2.4.0  2018-10-07
=========================
New Functionality
-----------------
Complete overhaul of Monitor/MonitorTimestamp internals, resulting in more consistent operation.
The documentation has been updated accordingly.
MonitorTimestamp is phased out and replaced by level monitors, which are instances of Monitor.
Timestamped monitors are now called level monitors, whereas non timestamped monitors are now called
non-level monitors.
non-level monitors now always timestamp the entry, which makes slicing and more useful animation possible.
It is no longer required (and possible) to indicate that a non-level monitor is weighted. If a weight is
required, just tally with a weight != 1.

Animation of non-level monitors is now also shown on a timescale, thus making it easier to see
the relation with a level monitor, e.g. length and length_of_stay of a queue.

This has a number of consequences for the API:

MonitorTimestamp ==> Monitor(level=True)
Merging of monitors not anymore part of the init, but is a separate method:
  m = Monitor(merge=(m1, m2, m3)) ==> m = m1.merge(m2, m3)

It is no longer necessary (and possible) to specify weighted=True in init of Monitor.
All non-level monitors now support weighted, if required.
  m = Monitor(weighted=True) ==> m = Monitor()
    
The (level monitor only) method .get() or direct call can now also be used to get the value of the level at a
specified time within the monitored period, e.g.
  print('queue length at time 100 was', q.length.get(100))
or alternatively:
  print('queue length at time 100 was', q.length(100))

It is now possible to slice a monitor with Monitor.slice(), which has two applications:
- to get statistics on a monitor with respect to a given time period, most likely a subrun
- to get statistics on a monitor with respect to a recurring time period, like hour 0-1, hour 0-2, etc.
  Examples:
   for i in range(10):
       start = i * 1000
       stop = (i+1) * 1000
       print(f'mean length of q in [{start},{stop})={q.length.slice(start,stop).mean()}'
       print(f'mean length of stay in [{start},{stop})={q.length_of_stay.slice(start,stop).mean()}'
       
   for i in range(24):
       print(f'mean length of q in hour {i}={q.length.slice(i, i+1, 24).mean()}'
       print(f'mean length of stay of q in hour {i}={q.length_of_stay.slice(i, i+1, 24).mean()}'

Instead of slice(), a monitor can be sliced as well with the standard slice operator [], like:
   q.length[1000:2000].print_histogram()
   q.length[2:3:24].print_histogram()


It is now possible to change the format of times in trace, animation, etc. with the method
  Environment.time_to_str_format()
For instance, if 5 decimals in the trace are to be shown instead of the default 3, issue:
  env.time_to_str_format('{:10.5f}')
Make sure that the format represents 10 characters.
See the docstring / documentation for more information.


From now on it is possible, but definitely not required, to set the dimension of the time unit when defining an environment, like
   env = sim.Environment(time_unit='hours')
Salabim supports 'years', 'weeks', 'days', 'hours', 'minutes', 'seconds', 'milliseconds' and 'n/a' as dimension.

If the time unit is set, times can be specified in any dimension, like
   yield self.hold(env.seconds(20))
The following methods for conversion to the current time unit are available:
  Environment.years()
  Environment.weeks()
  Environment.days()
  Environment.hours()
  Environment.minutes()
  Environment.seconds()
  Environment.milliseconds()
  Environment.microseconds()
Example:
  env = sim.Environment(time_unit='hours')
  env.run(env.days(10))
This effectively let the simulation run for 240 (hours).
                     
The following methods for conversion from time current time unit are available:
  Environment.to_years()
  Environment.to_weeks()
  Environment.to_days()
  Environment.to_hours()
  Environment.to_minutes()
  Environment.to_seconds()
  Environment.to_milliseconds()
  Environment.to_microseconds()
Example:
  env = sim.Environment(time_unit='hours')
  env.run(env.days(14))
  print('it is now', env.to_days(env.now()), 'weeks')
  #  output: it is now 2 weeks

Finally, the current time unit dimension can be queried with Environment.get_time_unit().
Example:
  env = sim.Environment(time_unit='hours')
  env.run(env.days(10))
  print('it is now', env.now()), env.get_time_unit())
  #  output: it is now 240 hours

All distributions, apart from IntUniform, Poisson and Beta now have an additional parameter, time_unit.
If the time_unit is specified at initialization of Environment(), the time_unit of the distribution
can now be specified.
As an example, suppose env has been initialized with env = sim.Environment(time_unit='hours').
If we then define a duration distribution as:
   duration_dis = sim.Uniform(10, 20, 'days')
, the distribution is effectively uniform between 240 and 480 (hours).
This facility makes specification of duration distribution easier and more intuitive.
Refer to the docstrings or documentation for details.
    
By default the time unit dimension is 'n/a', which means that conversions are not possible.

The documentation has a new chapter Miscellaneous/Time units covering this topic.


Announcement
------------
The class PeriodMonitor that was added in version 2.3.4 will be phased out in a future release.
Slicing monitors (see above) is much more reliable and versatile.


Reminder
--------
Python 2.7 will no longer be supported as from 31 December 2018.
Please upgrade to Python 3.x as soon as possible.


version 2.3.4.2  2018-09-29
===========================
Bug fixes
---------
Serious bug in MonitorTimestamp caching mechanism resulted in sometimes not updating the statistics, when
animation is off. Fixed.


version 2.3.4.1  2018-09-22
===========================
Bug fixes
---------
Joren van Lindert showed that the percentile calculation for (timestamped) monitors was incorrect.
A new algorithm is implemented.

Bug in merging (timestamped)monitors fixed.

version 2.3.4  2018-09-20
=========================
New functionality
-----------------
From this version, salabim supports so called period monitors with the class PeriodMonitor.
These period monitors can be used to get statistics about (timestamped) monitors per specific period.
For instance if the time unit is hours a period monitor with 24 periods of 1, will give 24 monitors
containing data about hour 0-1, 1-2, ... 23-24 (modulo 24).
It is not necessary that the durations are all the same.
The most obvious use case of this new functionality is to get period information about the builtin
queue monitors length and length_of_stay.
  qlength_per_hours= sim.PeriodMonitor(q.length, periods=24 * [1])
  q_length_of_stay_per_hour = sim.PeriodMonitor(q.length_of_stay, periods=24 * [1])
Then after a run, the histogram of the length of stay for hour 0-1 (modulo 24) can be printed with
  q_length_of_stay_per_hour[0].print_histogram()
And the mean length for hour 2-3 (modulo 24) can be retrieved with
  q_length_per_hour[2].mean()
Have a look at the sample program 'Demo periodmonitor.py' for an example, and the docstring or the
latest documentation for the exact API specification.
Please note that this class is still experimental functionality that might change in a future version.


It is now possible to indicate that after a specific component returns control to the event scheduler,
standby component should not be activated. This is particularly useful when a data collection component
becomes current every so often. In that case, activating standby component is not useful and will just
consume processing power.
There are two ways to indicate that a component should skip standby activation:
- Component.skip_standby()
- at initialization of a component, with the skip_standby parameter.
Component.skip_standby() can also be used to query the current value.


New methods
-----------
Added the methods
- Environment.user_to_screen_coordinates_x()
- Environment.user_to_screen_coordinates_y()
- Environment.user_to_screen_coordinates_size()
- Environment.screen_to_usercoordinates_x()
- Environment.screen_to_usercoordinates_y()
- Environment.screen_to_usercoordinates_size()
to convert between user and screen coordinates and vice versa.
These methods are particularly useful for position and sizing AnimateButtons, AnimateSliders or AnimateEntries.


Improved functionality
----------------------
It is no longer required that a process of a component contains a yield statement.
So now ordinary methods (non generators) can now be activated.
This is particularly useful for decision processes that do not consume any time.
Note that these non generator methods can also be called with (keyword) parameters.


Implementation notes
--------------------
Check for hasprocess() changed.
Substantial refactoring to allow for non generator processes to be supported, particularly
with respect to proper tracing.

Process as defined in Component inititalization and Component.activate are no longer assessed
by eval(), but by getattr(), resulting in more stable code.


Bug fixes
---------
Bug in MonitorTimestamp.xduration() fixed.


Announcement
------------
Python 2.7 will no longer be supported as from 31 December 2018.
Please upgrade to Python 3.x as soon as possible.


version 2.3.3.2  2018-08-25
===========================
Changed functionality
---------------------
If Environment.run() is given a till or a duration, main will become active at the specified time.
If not, main will become active when there are no more events on the event list. This will be shown
in the trace with 'ends on no events left'.
So, if you don't want a simulation to stop at the moment the event list becomes empty, issue
    env.run(sim.inf)
This can particularly be useful if you don't want to stop an animation when there are no events left.


The placement of the title of AnimateQueue() and Queue.animate() when the direction is 'n' or 's' has
been changed. Now the title is always displayed horizontally.


Implementation note
-------------------
Error reporting for AnimateEntry on Pythonista now only when actually animating.


Big fix
-------
On Pythonista, setting env.video parameter without animating, caused a crash. Fixed.


version 2.3.3.1  2018-08-23
===========================

Implementation note
-------------------
Not documented tkinter_init and tkinit_exit code removed.

Bug fix
-------
From version 2.3.3 main will be reactivated once there are no more events. This functionality was not
supported when running animated. Fixed.

Sometimes an animation object was not removed correctly (under tkinter). Fixed.


version 2.3.3  2018-08-22
=========================
New functionality
-----------------
The class AnimateEntry adds a new UI element to salabim. With this, it is possible to ask for the user to
enter a text. The Enter key will call an action function, which can be used to get the entered text.
In most cases, the entry animation will have to be removed then. See the manual or docstring for details.
AnimateEntry is not supported under Pythonista.
Note that the API of this class is still experimental and might change in future releases.

Improved functionality
----------------------
AnimateQueue() and Queue.animate() can now display a title near the start of the queue animation.
This makes it very easy to show the contents of a queue, with just one line of code
By default, the name of the queue will be displayed next to the queue. There are several parameters
to control the text placement and appearance. See the manual or docstring for details.

Changed functionality
---------------------
When there are no more events on the event chain, main was activated at time=inf, which made it
difficult to get useful time stamped statistics.
Therefore, from this version on main will become active at the time of the last event, when there are no more events. This condition is also properly traced now.

Bug fixes
---------
When a timestamped monitor was run till inf, the print_histogram method did not work properly. Fixed.

The linenumber in trace for 'request honor' or 'wait honor' was not correct. Fixed.


version 2.3.2.6  2018-08-09
===========================

Bug fix
-------
Under Python 2.7 autoscaling histogram sometimes did result into a TypeError. Fixed.

The wrong line number was displayed when tracing request honor and request wait. Fixed.


version 2.3.2.5  2018-08-08
===========================

New functionality
-----------------
The functionality to print to another file rather than stdout in all methods
  print_histogram()
  print_histograms()
  print_statistics()
  print_info()
as introduced in version 2.3.2.4 has been changed into a more logical way.

Now each of these methods has an additional parameter 'file'  which can be used
to direct the output to that file. If file is omitted, the output goes to stdout.
If as_str is True, the methods always return as a string rather than writing to a file.

Example:
    q=sim.Queue(name='queue')
    with open('test.txt', 'w') as f:
        q.print_statistics(file=f)
        
    print(q.print_info(as_str=True))

Bug fixes
---------
A bug when Pillow (PIL) was not installed (correctly) and running without animation fixed.
    

version 2.3.2.4  2018-08-07
===========================
New functionality
-----------------
The as_str parameter in the methods
  print_histogram()
  print_histograms()
  print_statistics()
  print_info()
can now also be used to direct the output to the file as mentioned in as_str, like in
    q=sim.Queue(name='queue')
    with open('test.txt', 'w') as f:
        q.print_statistics(as_str=f)
If as_str is True, the output will be returned as a string.
If as_str is False  (the default for all methods), the output will go to stdout.

Bug fixes
---------
Problem when printing 'values' histograms fixed.

Bug with drawing a circle with old style Animate() fixed.

A syntax error when run under Python 2.7 with 'yield from' fixed. Be advised that salabim will
drop Python 2.7 support in the future.


version 2.3.2.3  2018-07-31
===========================
Bug fixes
---------
ItemFile.read_item(), ItemFile.read_item_int(), ItemFile.read_item_float() and ItemFile.read_bool()
did ignore tabs completely.
From this version on, tabs are treated as whitespace, just like blanks.

Error in scaling of lines, rectangles, polygons and points fixed.
Line widths are now always rounded, which has the consequence that lines with a line width < 0.5 are not
displayed.


version 2.3.2.2  2018-07-24
===========================
Bug fixes
---------
Circles were scaled twice. Fixed.


version 2.3.2.1  2018-07-22
===========================
Bug fixes
---------
Fatal error in Component.cancel() when tracing standby components fixed.


version 2.3.2  2018-07-21
=========================
New functionality
-----------------
The methods
  AnimateText
  AnimateRectangle
  AnimateLine
  AnimatePolygon
  AnimatePoints
  AnimateCircle
  AnimateImage
  AnimateQueue
  AnimateMonitor
  AnimateMonitorTimestamp
now have an additional parameter, parent.
When a process finishes, either by reaching the end or by a cancel, all animation objects with that
component as its parent will be automatically removed.


Bug fixes
---------
Fatal error when tracing standby components fixed.

After a reset of a timestamped monitor, the animation of that monitor did not start at the left hand side of
the graph. Fixed.

Some minor error handling problems with checking for types fixed.


Demonstration of animation features
-----------------------------------
In order to demonstrate the new style animation classes, the following files (with comments) are included
in the GitHub distribution:
Demo animation classes.py (requires the file Pas un pipe.py)
Demo queue animation.py
Demo animation dynamic.py
Demo animation dynamic lambda.py


version 2.3.1  2018-07-09
=========================
New functionality
-----------------
Monitors can now be weighted. Initializing a Monitor instance has therefore a new parameter, weighted.
If weighted is set to True, the tally method can be used to specify the weight.
Monitor.weight() returns the sum of all weights.
Monitor.value_weight() returns the sum of all weights equal to or in value
Monitor.bin_weight() returns the sum of all weights > lowerbound and <= upperbound.
The name of the weight (used in Print_histogram and print_statistics) can be specified by the user (default is weight).


sim.Animate(circle0=) now supports also ellipses and circle arcs. Please consult the documentation for the correct
parameter usage.
It is highly recommended to use the new style AnimateCircle, which has some more parameters now:
  radius1 is the height of the ellipse (if omitted, a circle will be drawn)
  arc_angle0 is the start angle of the arc (default 0)
  arc_angle1 is the end angle of the arc (default 360, thus a full circle)
  draw_arc indicates whether the arcs should be drawn (default False)
Note that all the parameters may be a scalar, a function with 0, 1 or 2 arguments or a method with one argument (t).
Note also that the text is always positioned relative to the full circle/ellipse, regardless of the arc_angles.
Example:
  sim.AnimateCircle(radius=100, radius1=50, arc_angle1=lambda t: t*10)


Bug fixes
---------
Bug in closing an animation under Spyder or Idle fixed.
Bug in Environment.snaphot() under Pythonista fixed.


Internal
--------
Major overhaul of monitor off values and handling of duration for MonitorTimestamped.
Timestamped monitors now share most of their functionality with weighted monitors.


version 2.3.0  2018-06-28
=========================
New functionality
-----------------
As from this version, animation is more powerful and easier to use. Although the old style
Animate class is still available, it is recommended to use the new style classes.

The documentation is not yet completely up-to-date. Please read these release notes carefully to get more information.

All the docstrings (and therefore the reference section of the manual) are however up-to-date.
It is planned to publish a number of tutorial videos or guides, both for basic and advanced animation.

To visualize rectangles, lines, points, polygon, texts, circles and images salabim offers the new classes
- AnimateCircle
- AnimateImage
- AnimateLine
- AnimatePoints
- AnimatePolygon
- AnimateRectangle
- AnimateText

The main difference with the Animate class is that no automatic linear interpolation over time is supported.
But, each of the characteristics may be still changed over time easily!
All visualizations (apart from AnimateText) have an attached text field that will be displayed relative to
the shape.
Thus, for instance, it possible to say:
    vis = sim.AnimateRectangle(spec=(100, 100, 300, 50), text='some text')
and then a rectangle with the text 'some text' in the middle will be displayed.
In contrast to Animate, updating any of the specifying fields does not require the update method, but can be
done directly.
In the above example you can just say
    vis.text='yet another text' or vis.x=100

One of the key features of this new visualization is that all the specifying fields can now be functions or methods.
This make is possible to automatically update fields, e.g.
   vis = sim.AnimateText(lambda:'mean of histogram = ' + str(hist1.mean()), x=100, y=100)
   which will show and update the current mean of the histogram
or
   vis = sim.AnimateRectangle(spec=(0, 0, 60, 20), x=100, y=lambda t:t+10)
   which results in a rectangle, moving from bottom to top.
The animation_objects method of Component now accepts any of the new visualization class instances as well as
Animate instances.

Animation of queues is now specified with the class AnimateQueue, although Queue.animate() is still supported.
One queue can now be animated in several ways, whereas previously one queue could be animated only once. See
Demo queue animation.py for an example.
It possible to restrict the number of components shown (max_length).
Is possible to change all the parameters of the queue animation and the shown components dynamically.
See for instance Elevator animated.py where the queue position moves up and down.
Or see Machine shop animated.py where the shape of the components changes dynamically.
Internally, the animation of queues uses a new, more efficient, algorithm.

Most examples have been updated to use this new visualization functionality.

Texts can now spawn multiple lines (lines separated by linefeeds). Also, a list or tuple of strings may
be used instead, in which case each element of the list/tuple will be treated as another line.
This is particularly useful to present (dynamic) monitor values.
With AnimateText, it is possible to restrict the number of lines (parameter max_lines) shown.


Class Animate has a new animation parameter, as_points that applies to lines, rectangles and polygons.
If as_points is False (the default), all lines will be drawn.
If as_points is True, only the end point will be drawn as a square with a width equal to the linewidth.
Technical remark: the advantage of using as_points this instead of a series of individual squares
is that there is only one bitmap to be placed on the canvas, which may lead to better performance in many cases.
Also this is used internally for AnimateMonitor() (see below).
Points are also available in the new AnimatePoints class.


Class AnimateMonitor() can be used to visualize the value of a timestamped monitor over time. It is
particularly useful for visualizing the length of a queue, the various monitors of a resource or
the value of a state.
It is possible to connect the lines (very useful for 'duration' monitors, like queue length) or just show
the individual points.
This class can also visualize the relationship between the index and the value of a non time stamped monitor.
The points can be just shown or connected with a line.
It is possible to use
    Monitor.animate() and
    MonitorTimestamp.animate()
as an alternative, although not recommended.

The MMc animated.py model demonstrates the use of the (timestamped) monitor animation.


Monitor and MonitorTimestamp can now be used to create a merged (timestamped) monitor.
This is done by providing a list of (timestamped) monitors (all have to have the same type), like
    mc = MonitorTimestamp(name='m1 and m2', merge=(m1, m2))
For monitors, just all of the tallied x-values are copied from the to be merged monitors.
For timestamped monitors, the x-values are summed, for all the periods where all the monitors were on.
Periods where one or more monitors were off, are excluded.
Note that the merge only takes place at creation of the (timestamped) monitor and not dynamically later.

Sample usage:
Suppose we have three types of products, that each have a queue for processing, so
a.processing, b.processing, c.processing.
If we want to print the histogram of the combined (=summed) length of these queues:
    MonitorTimestamp(name='combined processing length',
        merge=(a.processing.length, b.processing.length, c.processing.length)).print_histogram()
and to print the histogram of the length_of_stay for all entries:
    Monitor(name='combined processing length of stay',
        merge=(a.processing.length_of_stay, b.processing.length_of_stay, c.processing.length_of_stay)).print_histogram()
        

CumPdf is a new distribution type that is similar to Pdf, but where cumulative probability values are used.
This is particularly useful for dichotomies, like failing probabilities:
    failrate = 0.1
    if CumPdf(True, failrate, False,1)
        print('failed!')


All methods
  print_histogram()
  print_histograms()
  print_statistics()
  print_info()
now have an additional parameter as_str, that allows the output to be returned
as a string, rather than print the information (the default is False, so just print):
This is particularly useful for animation of that information (see demo queue animation.py) or to
write directly to a file.
                        

sim.Random() is a new class that makes a randomstream. It is essentially the same as sim.random.Random().


Queue.name(value), Resource.name(value) and State.name(value) now also update the derived names.

API changes
-----------
The API of Component has changed slightly. The parameter process now defaults to None, which means that
it tries to run the process generator method, if any.
If you don't want to start the process generator method, even if it exists, now set process='' (this was None).

The API of Environment had changed slightly. The parameter random_seed now defaults to None, which means that
1234567 will be used as the random seed value. If random_seed is '*', a system generated, non reproducable,
random seed will be used.

The API of Environment.random_seed has changed slightly. If the argument seed is '*', a system generated, non
reproducable random seed will be used.

State.animate() is phased out. Use the standard visualization classes, like AnimateRectangle,
    AnimateCircle and AnimateTex instead.


Future changes
--------------
Python 2.7 will not be supported in a future version. Please upgrade to Python 3.x as soon as possible .


Internal changes
----------------
Most default parameters are now None, instead of omitted, which is completely phased out.
This makes it easier to specify default arguments, like:
    myname = None
    sim.Component(name=myname)
This internal change required a couple of changes to the API (see above).
Apart from that, the user shouldn't notice this rather dramatic internal change (>500 replacements in the code!).

Animating lines and polygons without any points is now supported.


version 2.2.23  2018-05-28
==========================
New functionality
-----------------
Component.leave() can now be called without a queue, in which case, the component will leave all queues
it is in, apart from internal queues (Resource.claimers(), Resource.requesters and State.waiters()).
It is not necessary that the component is in any queue.
The best use case is to leave the one and only queue it is in without having to specify the
queue, like
    self.enter(q1)
    ...
    self.leave()

Also, Component.leave() now returns the component (self). This is useful for daisy chaining, like:
def process(self):
    while True:
        self.leave().enter(q1)
        yield self.hold(p1())
        self.leave().enter(q2)
        yield self.hold(p2())
        self.leave().enter(q3)
        yield self.hold(p3())
With this code, the component 'hops' from queue to queue, with minimal effort.


In line with this daisy chaining of leave, the methods
    Component.enter(),
    Component.enter_at_head()
    Component.enter_sorted()
    Component.enter_in_front_of()
    Component.enter_behind()
now return the component (self).

With this new functionality, it is possible to do things like
    self.enter(q1).enter(q2).enter(q3)
for a component to enter three queues on just one line.


Monitor.print_histograms() introduced as an alias for Monitor.print_histogram()
MonitorTimestamped.print_histograms() introduced as an alias for MonitorTimestamped.print_histogram()
Monitor.reset_monitors() introduced as an alias for Monitor.reset()
MonitorTimestamped.reset_monitors() introduced as an alias for MonitorTimestamped.reset()

These four new methods make it possible to intermix resources, states, queues, (timestamped) monitors when
printing histograms or resetting the monitors, like:
for obj in [my_queue, my_resource, my_monitor, my_timestamped_monitor]:
     obj.print_histograms()
     obj.reset_monitors()
     
     
Introduced methods register and deregister for classes:
    Component
    Monitor
    MonitorTimestamped
    Queue
    Resource
    State
This makes it easier to do collective actions on a number of component, queues, (timestamped)monitors, queues,
resources and/or states.
A registry is just a list of objects, which can for instance be used as:
    monitors = []
    m1 = sim.Monitor(name='m1').register(monitors)
    m2 = sim.Monitor(name='m2').register(monitors)
    queues = []
    q1 = sim.Queue(name='q1').register(queues)
    q2 = sim.Queue(name='q2').register(queues)
    ...
    for obj in monitors + queues:
        obj.print_histograms()
        obj.reset_histograms()
    
Another example:
    components = []
    while(...):
        MyComp().register(components)
    ...
    print('all components in system:')
    for component in components:
        print(component.name())

Make sure to deregister any objects that are not used anymore, otherwise these will not be garbage collected!

Note that it is possible to mix several types of class in a registry (list).


Documentation update
--------------------
In contrast to documentation so far, the priority parameter in Component.enter_sorted, Component.priority()
and Queue.add_sorted() does not have to be float.
It can be any type as long as it can be compared with the other priorities in the queue.
Example 1:
    q=sim.Queue('q')
    X().enter_sorted(q, (1,1))
    X().enter_sorted(q, (0,2))
    X().enter_sorted(q, (1,0))
    X().enter_sorted(q, (1,3))
    q.print_info()
will print
    Queue 0x11a0136d8
      name=q
      component(s):
        x.1                  enter_time     0.000 priority=(0, 2)
        x.2                  enter_time     0.000 priority=(1, 0)
        x.0                  enter_time     0.000 priority=(1, 1)
        x.3                  enter_time     0.000 priority=(1, 3)
        
Example 2:
    q=sim.Queue('q')
    X().enter_sorted(q, 'one')
    X().enter_sorted(q, 'two')
    X().enter_sorted(q, 'three')
    X().enter_sorted(q, 'four')
    q.print_info()
will print
    Queue 0x1279a82b0
      name=q
      component(s):
        x.3                  enter_time     0.000 priority=four
        x.0                  enter_time     0.000 priority=one
        x.2                  enter_time     0.000 priority=three
        x.1                  enter_time     0.000 priority=two
        
Note: Avoid mixing enter_sorted or add_sorted with enter, enter_at_head, add, append or add_at_head when using
non float priorities.


Bug fixes
---------
Bug in State introduced in version 2.2.22 fixed.


version 2.2.22  2018-05-21
==========================
New functionality
-----------------
Monitor.print_histogram() and MonitorTimestamp.print_histogram() now support auto scaling of
the bin_width, lowerbound and number_of_bins, when none of these parameters are specified.
The autoscaling algorithm method can be overridden if required (see Histogram.histogram_autoscale).
For example, the following code
    m = sim.Monitor('normal distribution')
    for i in range(100000):
        m.tally(sim.Normal(10,2)())
    m.print_histogram()

will print:

    Histogram of normal distribution
                            all    excl.zero         zero
    -------------- ------------ ------------ ------------
    entries           10000        10000            0
    mean                  9.989        9.989
    std.deviation         1.989        1.989
    
    minimum               1.881        1.881
    median                9.978        9.978
    90% percentile       12.550       12.550
    95% percentile       13.245       13.245
    maximum              17.597       17.597
    
               <=       entries     %  cum%
            1             0       0     0   |
            2             1       0.0   0.0 |
            3             3       0.0   0.0 |
            4            14       0.1   0.2 |
            5            43       0.4   0.6 |
            6           153       1.5   2.1 *|
            7           439       4.4   6.5 ***  |
            8           925       9.2  15.8 *******     |
            9          1532      15.3  31.1 ************            |
           10          1938      19.4  50.5 ***************                         |
           11          1895      18.9  69.4 ***************                                        |
           12          1475      14.8  84.2 ***********                                                        |
           13           940       9.4  93.6 *******                                                                   |
           14           424       4.2  97.8 ***                                                                           |
           15           165       1.7  99.5 *                                                                              |
           16            34       0.3  99.8                                                                                |
           17            15       0.1 100.0                                                                                |
           18             4       0.0 100.0                                                                                |
              inf         0       0   100.0                                                                                |

Monitor.print_histogram() and MonitorTimestamp.print_histogram() now supports the presentation of
individual values, by specifying values=True.
This is especially useful when collecting the status of a component over time, like:

    Histogram of Status
    duration            300
    entries              57
    
    value                     duration        entries
    idle                        88.558( 29.5%)      9( 15.8%) ***********************
    produce A                   37.459( 12.5%)      9( 15.8%) *********
    produce B                    8.425(  2.8%)      2(  3.5%) **
    produce C                   44.352( 14.8%)     10( 17.5%) ***********
    produce D                   54.775( 18.3%)     12( 21.1%) **************
    store                       38.591( 12.9%)      8( 14.0%) **********
    transport                   27.841(  9.3%)      7( 12.3%) *******

Monitor.value_number_of_entries() introduced. The method can be used to check how many entries have an x
equal to value or an x that is in value.

MonitorTimestamp.value_duration() introduced. The method can be used to check the duration of an x
equal to value or an x that is in value.

MonitorTimestamp.value_number_of_entries() introduced. The method can be used to check how many entries have an x
equal to value or an x that is in value.

Introduced Queue.print_histograms(). This method prints autoscaled histograms of the
- length timstamped monitor
- length_of_stay monitor

Introduced Resource.print_histograms(). This method prints autoscaled histograms of the
- requesters().length timstamped monitor
- requesters().length_of_stay monitor
- claimers().length timstamped monitor
- claimers().length_of_stay monitor
- capacity timestamped monitor
- available_quantity timestamped monitor
- claimed_quantity timestamped monitor

Introduced State.print_histograms(). This method prints autoscaled histograms of the
- waiters().length timestamped monitor
- waiters().length_of_stay monitor
- value timestamped monitor

MonitorTimestamp.number_of_entries() introduced, to be used to retrieve the number of entries.

Component.name(), Environment.name(), Monitor.name(), MonitorTimestamp.name(), Queue.name()
Resource.name() and State.name() now can be used to change the name of the object.
Note that the base_name and the sequence_number will not change upon a name change.

Function regular_polygon introduced.


Renamed
-------
MonitorTimestamp.bin_count() is now called MonitorTimestamp.bin_duration()
Monitor.bin_count() is now called Monitor.bin_number_entries()


Bug fix
-------
Problem when PIL was not installed (correctly).


version 2.2.21  2018-05-01
==========================
New functionality
-----------------
Component.interrupt() can now be called also when a component is interrupted. In that case, the 'interrupt_level'
will be incremented. This allows interrupts to be 'stacked'.
When resuming with Component.resume(), the interrupt_level will be decremented. If it reaches zero,
the component will return to the status at the moment of the first interrupt.
If c.resume(all=True) is issued, the component c will return to its original status, regardless of the
interrupt_level.
The trace shows the level in interrupt and resume for interrupt_levels >= 2.
The file 'demo interrupt resume.py' demonstrates the application of stacked interrupts for breakdowns of
several parts of a machine.

The new method Component.interrupt_level() can be used to query the current interrupt_level. It is zero
for non interrupted components.

Function Component.isinterrupted() can be used to check whether a component is interrupted. This is equivalent
to c.status() == sim.interrupted


The new method Environment.snapshot() can be used to write an animated frame (at time=now()) to a file.
The method accepts .png, .jpg, .bmp, .gif and .tiff files. For all extensions but .jpg, the image can
have a semi transparent background (i.e. an alpha < 255).
The animation does not have to be started to use snapshot().

Bug fixes
---------
Component.resume() did not handle mode correctly. Fixed.
It was not possible to use sim.spec_to_image() if the animation was not started. Fixed.

version 2.2.20  2018-04-28
==========================
New functionality
-----------------
New process interaction methods Component.interrupt() and Component.resume() introduced to interrupt a component.
This is particularly useful for simulating breakdowns.

When a component is interrupted, the component is removed from the event chain (if applicable) and
the status becomes interrupted. For scheduled, waiting and requesting component, the remaining
duration will be calculated.
Upon resume, the action depends on the original status:
- passive: the component gets passive
- standby: the component gets standby
- requesting: if the request can be honored, it will.
  If not, the fail_at time will be updated according to the remaining duration
- waiting: if the wait can be honored, it will.
  If not, the fail_at time will be updated according to the remaining duration
- scheduled: the scheduled time will be updated according to the remaining duration
  Note that an interrupted component cannot be interrupted.
  Also, only interrupted components can be resumed.
  Interrupted components can leave the interrupted state with the all process activation methods:
  activate, hold, passivate, wait, request, standby or cancel.
  

The functionality of method Component.remaining_duration() has been extended.
Now the method has a value parameter which allows setting the remaining_duration.
The action depends on the status where the component is in:
- passive: the remaining duration is update according to the given value
- standby and current: not allowed
- scheduled: the component is rescheduled according to the given value
- waiting or requesting: the fail_at is set according to the given value
- interrupted: the remaining_duration is updated according to the given value
The method returns:
- passive: the remaining time (if applicable) at the moment passivate() was given, unless overridden
- scheduled, waiting or requesting: the scheduled time minus now
- interrupted: the remaining time (if applicable) at the the moment interrupt was given unless overridden
- otherwise: 0


Environment.run() now allows main to be scheduled urgent, by specifying urgent=True.

Improvement
-----------
When a process ends the trace now shows the line number of the last line in the process,
postpended with a plus symbol. Previously no line number was shown.
Also, any auto resource releases at the end of a process will show the same information now.

version 2.2.19  2018-04-13
==========================
New functionality
-----------------
Support for animated GIF production. If Environment.animation.parameters(video=...) of Environment.video()
gets a filename with .gif as extension, an animated GIF is created.
Note that GIF production does not require numpy nor opencv, and therefore Environment.can_video() does not
have to be True to produce an animated GIF.
This feature is particularly useful on Pythonista platforms, where opencv is not supported.

For animated GIFs, Environment.animation_parameters() has two extra parameters:
  video_repeat   ==> how many times the animated GIF will be repeated (default 1)
  video_pingpong ==> whether all frames should be appended in reverse order at the end of the animated GIF
                   resulting in a smooth repeating video (default: False)

Two methods have been added to Environment to support GIF file production:
  Environment.video_repeat()
  Environment,video_pingpong()
               
                   
For ordinary video files (non GIF), it is now possible to specify a codec, by adding a plus sign and
the name of the codec after the extension of the file, like
  video='myvideo.avi+DIVX'


Introduced Resource.occupancy timestamped monitor. The occupancy is defined as the claimed quantity
divided by the capacity. Note that when the capacity of r changes over time, r.occupancy.mean() may differ
from r.claimed_quantity.mean() / r.capacity.mean(). Also, in that case, the occupancy may be even greater than 1.
If the capacity is <=0, the occupancy is assumed to be 0.


Improvements
------------
The time in the upper right-hand corner is now displayed with the mono font, which is better legible and
not as 'nervous' as the narrow font that was used previously. Also, on Pythonista, the text is moved a bit
to the left in order not to coincide with the closing symbol X.


Clarification
-------------
When a process ends, all claimed resources will be automatically released.
If that functionality is not desired, the process should be prematurely cancelled, with
    yield self.cancel()
    
Compare these two components:
    class X(sim.Component):
        def process(self):
            yield self.request(r)
            yield self.hold(1)
            # automatically releases r at the end of the process

    class Y(sim.Component):
        def process(self):
            yield self.request(r)
            yield self.hold(1)
            yield self.cancel()  # process ends here and r is NOT released!

Also, all animation objects that have set the parent field to a component will be removed automatically
when the process of that component ends. Again, this can be prevented by yield self.cancel().

This information will be included in the documentation.
    

Bug fixes
---------
Bugs in AnimateSlider fixed (thanks to John Hutchinson).

Bug when honoring a resource request of a component that was already claiming that resource fixed.

Bug in the line number of the trace when auto releasing claimed resources at end of a process fixed.

Bug in wait with a fail_at parameter fixed.


version 2.2.18  2018-03-31
==========================
New functionality
-----------------
Function reset() resets all global variables and closes a video recording, if any
It can be useful to start a script with sim.reset() when used in REPLs and under Pythonista (iPad).

Release notes 2.2.17 corrections
--------------------------------
Method Environment.scale() introduced, returning the scale of the animation, i.e. width / (x1 - x0)
  (not (x1 - x0) / width).

Function arrow_polygon added (not polygon_arrow).
Function centered_rectangle() added (not rectangle_centered).

Bug fixes
---------
Bug in AnimateSlider corrected.

version 2.2.17  2018-03-31
==========================
New functionality
-----------------
Normal distribution now supports specification of coefficient_of_variation as an alternative
  to standard_deviation.
Note that it is not allowed to specify both standard_deviation and cooeficient_of_variation.
The coefficient_of_variation is now also shown in Normal.print_info().
The coefficient_of_variation is defined as the standard deviation divided by the mean.

Method Environment.scale() introduced, returning the scale of the animation, i.e. (x1 - x0) / width

sim.Animate and sim.update now allows and prefers circle0 or circle1 to be specified as a scalar.
The functionality to the specify the radius as a one element tuple/list is still supported.
E.g. sim.Animate(circle0=(30,)) is equivalent to sim.Animate(circle0=30) now.
Note that Animate.circle may also return a one item tuple/list or a scalar.

sim.Animate() and sim.update() now allows the specification of
  line0, line1, rectangle0, rectangle1, poloygon0 and polygon1 to include None values
The None values will repeat the previous x or y value. E.g.
sim.Animate(line0=(10, 20, None, 30, 40, None)) is equivalent to sim.Animate(line0=(10, 20, 10, 30, 40, 30))

Function polygon_arrow() added.
Function rectangle_centered() added.

Video production now supports .MP4 and .AVI extensions. Other extensions are not accepted.

Environment.is_dark(colorspec) now returns the is_dark value of the background color
  if the alpha value of the colorspec is 0.

Changed API
-----------
The parameter lambda_ for the Poisson distribution is renamed to mean, in order to avoid problems
with the online documentation.

Bug fixes
---------
Bug in handling width/height of images when using a redefined coordinate system fixed.
Bug in method Queue.add_at_head() fixed.
Bug with default font handling on Pythonista fixed.
Bug in Environment.animation_parameters() and Environment.video() fixed.
Work around a PIL bug where rendering the first letter of some italic font texts chopped the lefthand serif.

Sample files
------------
Show colornames.py shows all available colors.
Demo using process interaction in method.py gives an example of how to use hold in a separate method.
Dining philsophers animated.py updated to use the new circle specification.

Documentation
-------------
Documentation updated and improved. Although still work in progress ...



version 2.2.16  2018--03-01
===========================
From this version, neither animation modules (PIL, tkinter) nor video modules (cv2, numpy) will
be imported unless these are required at runtime (with animation_parameters).

A user program can now check whether animation is supported with a call to sim.can_animate().
A user program can now check whether video is supported with a call to sim.can_video().

Bug fix
-------
Minor bug when ImageTk could not be imported corrected.

version 2.2.15  2018-02-28
==========================
Animation updates
-----------------
Overhaul of the way animation is organized. Now, the animation can be started and stopped during a run.
When animation is off, the simulation model runs full speed without any overhead.
It is possible to use different environmnent for the animation although not at the same time.

The API for animation has changed slightly:
center is now refered to as 'c'  (although 'center' is still accepted)
xy_anchor allows x0, x1, y0 and y1 in Animate and x and y in AnimateButton or AnimateSlider object, to be
relative to each of the wind directions 'n', 'nw', 'w', 'sw', 's', 'se', 'e' or 'ne' or 'c' (for center).
This makes it, for instance, possible to define a button relative to the top right hand corner of the
animation frame:
b = sim.AnimateButton(text='My button', x=-100, y=-20, xy_anchor='ne')

All arguments of Environment.animation_parameters have now a corresponding function that
can be used to set or query one of the animation parameters:
  Environment.x0() to set/query x-coordinate of lower left corner of animation frame
  Environment.x1() to set/query x-coordinate of upper right corner of animation frame
  Environment.y0() to set/query y-coordinate of lower left corner of animation frame
  Environment.y1() to query y-coordinate of upper right corner of animation frame
  Environment.width() to set/query width of animation frame
  Environment.height() to set/query height of animation frame
  Environment.fps() to set/query the number of frames per second
  Environment.show_time() to set/query whether time should be shown
  Environment.show_fps() to set/query whether fps should be shown
  Environment.modelname() to set/query the model name ('' to show nothing)
  Environment.animate() to start/stop the animation and to query the current status
  Environment.speed() to set/query the speed of the animation
  Environment.video() to set/query the name of the video ('' for no video)

New functionality
-----------------
The Poisson distribution is now supported.

Enhancements
------------
Text alignment in text Animate is significantly improved. Now the text is always aligned according to the
(estimated) 'cap line', which is derived from a capital A.
So, when aligning south, the descender of the g is below the baseline.
When aligning north, top of the capline is the given y-position.
Finally, aligning w, c or e means given y-position is the middle of the cap line.

Functionality updates
---------------------
- linewidth0 defaults to 1 for lines, 0 for rectangles, polygons and circles.
- When a modelname is given, that is presented in a different way along with a salabim logo.

Updated animated sample files
-----------------------------
Please not that the animated sample models have been updated to use the new xy_anchor functionality.

Bug fix
-------
Collected tallies for monitors were not cached properly, resulting in non optimal performance of Monitor.x() and
querying the monitor, e.g. print_histogram.

version 2.2.14  2018-02-02
==========================
New functionality
-----------------
Standby components just getting current and go into standby again can now be excluded from the trace.
This can be controlled with the method Environment.suppress_trace_standby().
By default, standby is excluded from the trace.


Added functionality to read item based input files (inspired by TomasRead).
Therefore, the class ItemFile is added to salabim.

Example usage:
    with sim.ItemFile(filename) as f:
        run_length = f.read_item_float()
        run_name = f.read_item()
        
Or (not recommended):
    f = sim.InputFile(filename)
    run_length = f.read_item_float()
    run_name = f.read_item()
    f.close()

The input file is read per item, where blanks, linefeeds, tabs are treated as separators.
Any text on a line after a # character is ignored.
Any text within curly brackets ( {} ) is ignored (and treated as an item separator).
Note that this strictly on a per line basis.
If a blank is to be included in a string, use single or double quotes.
The recommended way to end a list of values is //

So, a typical input file is:

    # Typical experiment file for a salabim model
    1000              # run length
    'Experiment 2.0'  # run name
    
     #Model          speed color
     #-------------- ----- ------
    
     'Peugeot 208'       150 red
     'Peugeot 3008'      175 orange
     'Citroen C5'        160 blue
     'Renault "Twingo"'  165 green
     //
     
     France {country} Europe {continent}
     
     #end of file

Instead of the filename as a parameter to ItemFile, also a string with the content can be given. In that
case, at least one linefeed has to be in the content string. Usually, the content string will be triple
quoted. This can be very useful during testing as the input is part of the source file and not external, e.g.

    test_input = '''
    one two
    three four
    five
    '''
    with sim.ItemFile(test_input) as f:
        while True:
            try:
                print(f.read_item())
            except EOFError:
                break


​    
​     
version 2.2.13A  2018-01-25
===========================
Bug fix
-------
The just introduced functionality to use parameters for processes did not work under Python prior to version 3.4, so
also not under Python 2.7|.

This intermediate version fixes that.

version 2.2.13  2018-01-25
==========================
New functionality
-----------------
It is now possible to use arguments for the process generator of a component. Only keyword arguments are supported.
Parameters can either be set at initialization of a component or the call to activate. E.g.:

    import salabim as sim
    class Car(sim.Component):
        def setup(self, color):
            self.color=color
            
        def process(self, duration):
            print(self.color, duration)
            yield self.hold(duration)
            yield self.activate(process='process', duration=50)  # this restarts the process
            
    env=sim.Environment(trace=True)
    Car(color='red', duration=12)
    env.run(100)

Note that the keywords used by the process generator are not passed to setup(), at initialization of a component.
That means that setup() can't have the same parameters as the process called at initialization (usually process()).
Furthermore, neither the process generator nor setup() can use
  at, delay, urgent, process, keep_request, keep_wait when called from activate()
  name, suppress_trace, suppress_pause_at_step, mode, env, at, delay, urgent, process at initialization of a component
as parameters.

Bug fix
-------
Corrected bug when tracing a standby component.

Optimization
------------
Optimized animation perfomance by improving the interpolate function.

version 2.2.12  2018-01-18
==========================
In the trace the line numbers are now prefixed by a letter to indicate
in which file the line is in.
The file from which the environment is created is not prefixed.
The trace will issue a line when a not yet used source file is referenced.

New method Environment.print_trace_header() will print a header.
If an Environment is initialized, the trace_header is also printed provided trace=True.

Now MonitorTimestamped.xt() and MonitorTimestampled.tx() add the last tallied value along with
the current time as the last x- and t-value. This can be turned off by specifying add_now=False.

Defining MonitorTimestamp is now much simpler as it is no longer required to use a getter function.
Instead, the caller has now to provide the value to be tallied directly to the tally() method.
When initializing a timestamped monitor, an initial_tally can be provided (by default 0).

Added IntUniform distribution to sample integer values in a given range, for example:
  die = sim.IntUniform(1,6)

Added method bounded_sample to all distributions, to force sampling of a distribution within given bounds.
This is, for instance, useful when sampling from a normal distribution, where the sample has be positive:
  s = Normal(8,5).bounded_sample(lowerbound=0)

Added Component.queues() which returns a set of all queues where the component is in.
Added Component.count() which returns the number of queues the component is in or 1 if the component is in the queue, 0 otherwise

Added a method Environment.beep() which can be useful to attract attention, etc. Note that this works only under Windows or iOS (Pythonista).
For all other platforms, this is just a dummy function.

Component.index_in_queue() renamed to Component.index() to be consistent with Queue.index()

Significant updates to the documentation (structure).

Optimizations by checking _trace flag before calling print_trace.

version 2.2.11  2018-01-14
==========================
Enhanced trace output
---------------------
The trace output now also shows the line number in the source code. This can be extremely
useful when debugging or learning.

E.g. the following code

    1|import salabim as sim
    2|
    3|class X(sim.Component):
    4|    def process(self):
    5|        yield self.hold(10,mode='one')
    6|        if self == x1:
    7|            yield self.passivate()
    8|        yield self.hold(10,urgent=True, mode='two')
    9|
   10|class Y(sim.Component):
   11|    def process(self):
   12|        yield self.request((res, 4), fail_at=15)
   13|        x1.activate()
   14|
   15|env=sim.Environment(trace=True)
   16|res = sim.Resource()
   17|
   18|x0=X()
   19|x1=X()
   20|Y()
   21|
   22|env.run(50)

prints:

line#         time current component    action                               information
-----   ---------- -------------------- -----------------------------------  ------------------------------------------------
   15                                   main create
   15        0.000 main                 current
   16                                   resource.0 create                    capacity=1
   18                                   x.0 create
   18                                   x.0 activate                         scheduled for      0.000 @    4  process=process
   19                                   x.1 create
   19                                   x.1 activate                         scheduled for      0.000 @    4  process=process
   20                                   y.0 create
   20                                   y.0 activate                         scheduled for      0.000 @   11  process=process
   22                                   main run                             scheduled for     50.000 @   22+
    4        0.000 x.0                  current
    5                                   x.0 hold                             scheduled for     10.000 @    5+ mode=one
    4        0.000 x.1                  current
    5                                   x.1 hold                             scheduled for     10.000 @    5+ mode=one
   11        0.000 y.0                  current
   12                                   y.0                                  request for 4 from resource.0
   12                                   y.0 request                          scheduled for     15.000 @   12+
    5+      10.000 x.0                  current
    8                                   x.0 hold                             scheduled for     20.000!@    8+ mode=two
    5+      10.000 x.1                  current
    7                                   x.1 passivate                        mode=one
   12+      15.000 y.0                  current
   22                                   y.0                                  request failed
   13                                   x.1 activate                         scheduled for     15.000 @    7+ mode=one
                                        y.0 ended
    7+      15.000 x.1                  current
    8                                   x.1 hold                             scheduled for     25.000!@    8+ mode=two
    8+      20.000 x.0                  current
                                        x.0 ended
    8+      25.000 x.1                  current
                                        x.1 ended
   22+      50.000 main                 current

Note that output line now starts with the line number in the source.
If a + is behind the line number, that means the statement following that line.
Also, for components to be scheduled the line number where the component will start execution
is shown following the @ sign.
Urgent scheduling is now indicated with an ! sign behind the time.

Distributions
-------------
New distributions:
    Beta
    Erlang
    Gamma
    Weibull
    
Exponential distributions can now be specified with a mean (beta) or a rate (lambda).

Normal distributions can now be specified to use the alternative random.gauss method.


New parameter for class Component
---------------------------------
suppress_pause_at_trace


New methods
-----------
Component.suppress_pause_at_trace

Sampling from a distribution is now also possible by just calling the distribution, like:
    yield self.hold(inter_arrival_time())
, which is equivalent to
    yield self.hold(inter_arrival_time.sample())

Documentation update
--------------------
The online documentation is now better structured and more accessible.
Also, a lot of content added, although still not complete. As always, volunteers are welcome
to help in improving the manual!

The documentation makes clear now that the time stamps as used in timestamped monitors are
not adjusted for reset_now().

version 2.2.10  2018-01-03
==========================
New methods:
  Component.remaining_duration()
    This method returns the duration left of a hold, request or wait at the time a passivate
    was given.
    For components that are scheduled, the remaining time to the scheduled time is returned.
    This is very handy to interrupt a component's hold for a, like in
        class Machine(sim.Component):
            def process(self):
                while True:
                    yield self.hold(produce_one_part)
                    number_of_parts += 1
                
        class Disturber(sim.Component):
            def process(self):
                while True:
                    yield self.hold(time_to_failure)
                    machine.passivate()  # interrupt the production
                    yield self.hold(time_to_repair)
                    machine.hold(machine.remaining_duration())  # resume production

  Environment.reset_now()
    This method can be used to reset now, by default to 0.
    All times communicated to/from the application will be according to the new time.
    Be sure to adjust any user defined times as these will not be updated automatically!
    
    Internally, the reset is realized by keeping track of the offset of the time.

Naming of object changed:
    In previous versions when initializing an object (Environment, Component, Queue, Resource, State,
    Monitor or MonitorTimestamped) where the name ended with a period , the sequence number (0) was
    suppressed for the first object.
    When a second object with the same name was initialized, that first object was renamed and got
    a 0 as sequence number. Now, an object with a name ending with a period is always serialized.
    If the name ends with a comma, the sequence starts at 1 (and the , is replaced by a .).
    E.g.
       for i in range(2):
           a = Airplane(name='airplane')
           b = Boat()
           c = Car(name='car,')
           print(a.name())
           print(b.name())
           print(c.name())
     
       Result:
       airplane
       boat.0
       car.1
       airplane
       boat.1
       car.2
       
    The name() method no longer supports renaming an object, i.e. can only be used to get the name.

Change of name:
    Queue.intersect has been renamed to Queue.intersection.

New queue functionality:
    The intersection of two queues can now be assessed also with the & operator, e.g. q1 & q2.
    The union of two queues can now be assessed also with | operator, e.g. q1 | q2.
    The difference of two queues can now be assessed also with the - operator, e.g. q1 - q2.
    The symmetric_difference of two queues (new method) can be assessed also with the ^ operator, e.g. q1 ^ q2.

    Queues have a couple of new methods, to be more in line with list and set functionality:
    append() is equivalent to add
    pop now also supports an index
    del q[] can now be used to delete one component, e.g. q[4] or a component by slice, e.g. q[3:5]
    remove without an argument now clears a queue completely
    extend can be used to add component at the tail of a queue from a queue or list
    initialization of queues with a queue, list and tuple
    
    as_set() can be used to get all components in a queue as a set.
    as_list() can be used to get all components in a queue as a list.
    q[:] can be used to get all components in a queue a list.
    
    The Queue methods union, difference, intersection, copy and move now support default (meaningful) names.

New color functionality:
    The method Environment.animation_parameters now has an additional parameter, foregroundcolor.
    If not specified, salabim automatically chooses the most contrasting color (white or black).
    This foreground color is used to show the system button, the time, modelname.
    Besides, several colors in Animate, AmimateButton and AnimateSliders now defaults to
    this foreground_color.

    Also, it is now possible to specify 'fg' for the foreground color and 'bg' for the background color when
    a color is required.

Internal:
    Several optimizations.
    Better checks for validity of colors.


version 2.2.9  2017-12-20
=========================
From this version the following classes:
  Environment
  Monitor
  MonitorTimestamp
  Queue
  Resource
  State
support automatic naming according to the class where it is defined, like Component.
Also, all these classes now call a setup method as the last statement in __init__ .
By default, this setup method is dummy.

Classes Monitor and MonitorTimestamp now contain base_name() and sequence_number() methods.

The image method of the class Animate now just returns an image and not anymore a tuple of
an image and a serial number.

The function spec_to_image now supports the null string, in which case a dummy picture will be
returned.

Animation of images is now correctly handled if width0 is omitted. When overriding Animate.width,
None can be used to disable scaling.

Improved error handling (no more asserts).

Bug in Resource.release fixed.


version 2.2.8  2017-12-06
=========================
New features / major changes:
Animation can now run synced (i.e. in real time, with a speed factor) or not synced. In the latter
case, the animation will step from event to event. In that case also single stepping is now supported.
Synced on/off can be set with animation_parameters and/or with the menu system.

The menu system is completely redesigned. It now shows only a 'Menu' button at start up. When this button
is pressed, several buttons are shown. Here, the user can select Synced on/off, Trace on/off and Stop. When Synced
is on, the user can increase or decrease the animation speed. When Synced is off, the user can single
step through the simulation (with Step). Finally, with Go the simulation will run again.
The animation speed is no longer shown in the right hand upper corner. And frames per second (fps) is disabled
by default now, in order to get a less cluttered top line and more space for user information.

Minor changes and bug fixes:
A major bug caused Pythonista to crash frequently and rapidly. This is now fixed.

The function show_speed of Environment.animation_parameters is no longer available.

The functions clocktext is are now a method of Environment, thus making it overridable.

Sample models are updated.

version 2.2.7  2017-11-28
=========================
New features:
Animation of queues is now a standard feature, which makes visualisation of queue contents much simpler.
In order to realize that, a component now has an animation_objects method,
which defines how a component is to be visualized.
The default method shows a black square of 40x40 with the sequence_number in white in this square.
But, it is possible and quite likely necessary to override the animation_objects method.
The method should return a list or tuple containing the x-size, y-size and one or more animation objects.
In order to animate a queue, the method Queue.animate should be called with the position of
the first component and the direction for subsequent components.
Please have a look at the MMc model for a demonstration.

Animation of states is now a standard feature, which facilitates in visualization of a changing state.
In order to realize that, a state now has an animation_object method, which defines
how a state is displayed for each possible value.
The default method shows a black square of 40x40 with the value dispayed in white in this square. If
the value is a valid colour, an emmpty square with that colour is displayed.
But, it is possible and quite likely necessary to override the animation_objects method.
The method should return a list or tuple containing one or more animation objects.
In order to animate a state, the method State.animate should be called once with the position of
the animation object.

The animation now calls a method Environment.animation_pre_tick(t) just before starting
the animation objects display loop.
And Environment.animation_post_tick(t) just after the loop. Both methods are by default dummy
(they just return).
Overriding/monkey patching these methods (particularly animation_pre_tick) can be useful for advanced animations,
e.g. for a queue where the y position changes over time (cf. the Elevator animated model).

Reintroduced functionality to remove animation objects belonging to a component that becomes a data component.
The 'belonging to' has to be indicated with parent in the call to Animate.

Minor changes and bug fixes:
Default arguments are now handled with an omitted value rather than None (or '*' in some cases).

All error handling is now via SalabimError.

Internal handling of Monitor.x, MonitorTimestamped.xduration, MonitorTimestamped.xt and
MonitorTimestamped.tx improved.

Code optimized with several list comprehensions.

Bug fixes.

version 2.2.6  2017-10-07
=========================
Salabim now supports Python 2.7. The biggest advantage of this is, that models can
now be run under PyPy.

The module numpy is no longer required (although still required for video production).
This makes it easier to run under PyPy, where installing numpy can be complicated.
When PIL is installed, even animation is now supported under PyPy.

All animated examples were updated to support Python 2.7, particularly by changing
super().proc(...) into sim.Component.proc(self,...) and sim.Animate.proc(self, ...)

Internal: font searching and build up of font tables improved.
Now salabim also searches the current directory for any .ttf files.

Several bug fixes.

version 2.2.5  2017-09-27
=========================
Queue.reset() has been renamed to Queue.reset_monitors()
Resource.reset() has been renamed to Resource.reset_monitors()
New method: State.reset_monitors()

In Component.wait(), if the test value contains a $, the $
sign is now replaced by state.value() instead of str(state.value())
This means that you can now say
    self.wait('light','$ in ("green","yellow")')
    
Monitor can now store the tallied values in an array instead of a list.
this results in less memory usage and faster execution speed.
The array may be either integer, unsigned integer or float.
Integer and unsigned integer is available in 1, 2, 4 or 8 byte versions.
When type='any' is given (default), the tallied values will be stored in a list.
Note that the monitor for Queue.length_of_stay is a float array now.
For list monitors the x-value in x() returns a numpy array
where the values are converted to a numeric (value 0 if not possible)
unless overridden with force_numeric=False.

MonitorTimestamp will now store the timestamps in a float array.
The tallied values can be stored in an array instead of a list. This results in less memory usage and
faster execution speed.
The array may be either integer, unsigned integer or float.
Integer and unsigned integer is available in 1, 2, 4 or 8 byte versions.
When type='any' is given, the tallied values will be stored in a list.
Monitor off is now tallied now with the attribute off of the timestamped monitor,
which is dependent on the type.
Note that the tallied values for Queue.length are in an uint32 array.
The tallied values for Resource.capacity, Resource.claimed_quantity and
Resource.available_quantity are in a float array,
The tallied values for State.value are in a list, unless a type is specified at init time.
The MonitorTimestamp.x() method returns a numpy array for integer and float monitors.
For 'any' timestamped monitors the x-value in xduration() is a numpy array
where the values are converted to a numeric (value 0 if not possible)
unless overridden with force_numeric=False.

The Monitor.x() and MonitorTimestamped.xduration() methods now uses caching to impove performance.

The function type in Component.wait now uses three arguments instead of a tuple of value,
component and state.

Redesigned font searching in order to support animation on Linux and to guarantee a consistent
appearance over different platforms.
Therefore, a small set of ttf fonts is included in the distribution. These should reside in
the same directory where salabim.py is located (PyPI automatically takes care of that).
These fonts will be first searched. As of this moment, salabim is shipped with:
- calibri.ttf           The preferred proportional font. Also accessible with font='std' or font=''
- arial.ttf
- cour.ttf
- DejaVuSansMono.ttf    The preferred monospaced font. Also accessible with font='mono'
- mplus-1m-regular.ttf  The preferred narrow monospaced font. Also accessible with font='narrow'
If salabim is not able to find any matching font, the PIL.ImageFont.load_default() will be called, now.

Internal optimizations by using defaultdict instead of dict where useful.

Outphased:
  salabim.run()
  salabim.main()
  salabim.trace()
  salabim.now()
  salabim.animation_parameters()
  salabim.current_component()
Use the equivalent default environment method instead, like
  env.run()

version 2.2.4  2017-09-12
=========================
Automatic naming of components, queues, etc. results in shorter names now.
E.g., instead of 'client............11' the name is now 'client.11'.
Also the name is not shortened anymore (was: 20 characters).

The methods Monitor.print_statistics(), MonitorTimestamp.print_statistics(),
Queue.print_statistics, State.print_statistics and Resource.print_statistics()
have an improved layout.

The method Monitor.print_histogram() and MonitorTimestamp.print_histogram()
have an improved layout.

Monitor and MonitorTimestamp names are now serialized.

Please have a look at the much improved manual.

version 2.2.3  2017-09-05
=========================
PIL 4.2.1 (shipped with the latest WinPython distribution), has a bug when
trying to animate text with the null string.
Therefore, salabim now has special code to handle null strings correctly.

Minor bug with importing PIL under Pythonista fixed.

version 2.2.2  2017-09-02
=========================
Component.wait() now allows to check for":
- a value
  yield self.wait((light,'red'))
- an expresssion to be evaluated. the value has to be $ which is replaced by
  str(state.value()), each time the condition is checked
  yield self.wait((light,'$in ("red","yellow")'))
  yield self.wait((level,'<30'))
  it is possible to use state for the state under test and self for the
  component under test
- a function to be called each time the condition is checked.
  the function is called with one argument, being
  a tuple of state.value(), component, state
  yield self.wait((light,lambda x: x[0] in ('red,ýellow'))
  yield self.wait((level,lambda x: x[0]<30))
  

Component.activate() has an additional parameter keep_wait, which controls whether
waits are to be kept upon an activate, thus allowing an update of a timeout.

When salabim detects that PIL or tkinter is not installed when trying to animate,
the error message now provided instructions on how to install the relevant package.

When salabim detects that cv2 is not installed when trying to produce a video,
the error message now provided instructions on how to install the relevant package.

version 2.2.1  2017-08-31
=========================
Bug in Component.request() corrected.
This prevented Machine shop animated to work properly.


version 2.2.0  2017-08-30
=========================
Introduced a new process control method: wait.
This functionality is similar but not equal to the waitevent and queueevent
methods in SimPy2.
The method allows a process to wait for a any if all of (number of) certain
value(s) of a so called state.
A state has a value and each time this value change, all components waiting for
this state are checked.
The class State has a number of methods, which allow to control the state:
  set(value) sets the value. Normally used without argument, in which
          case True will be used.
  reset() resets the value to False=
  trigger(value) sets the value (default True), triggers any components waiting,
    and then immediately resets to a given value (default False).
    optionally, the number of components to be honored with the trigger
    value may be limited (if used, most like 1).
The current value of a state can be retrieved with
  get() or by directly calling the state.
  So, e.g. dooropen.get() or dooropen()
On top of that, the queue of waiters may be accessed with
  State.waiters()
And there is a monitor to register the the value over time, called State.value .
.
The waiters queue and value will be monitored by default.

Components can wait for a certain value of a state (or states) by
  yield self.wait(dooropen)
or
  yield self.wait((dooropen,False))
And for several states at one time:
  yield self.wait(frontdooropen,backdooropen) to test for fontdooropen OR backdooropen
or
  yield self.wait(dooropen,lighton,all=True) to test for dooropen AND lighton
It is also possible to check for several values of one state:
  yield self.wait((light,'green'),(light,'yellow')) tests for lighth is green of yellow

The method wait can have an optional timeout parameter.
If they are timed out, Component.fail() is True.

If a component is in a wait state, the status waiting will be returned.
In order to test for this state, use either
  c.state() == waiting
or
  c.iswaiting()
See the example script demo wait.py for a demonstration of the trigger and time out functionality.

Deprecated functionality:
In method Component.request(), it is no longer allowed to specify
greedy behaviour. Also strict_order is not anymore supported.
The reason for this is its limited use and stability.

Technical note: The process of honouring requests is now optimized by keeping track of
the minimal requested quantity for each resource.

Method request_failed() changed to failed().
This method now also refers to fails of wait.

For Monitor and MonitorTimestamp, the tallied values are now converted to a numeric
equivalent, if not yet int/float. Values of type bool are converted to 0 for False and
1 for True (as usual).
For all other types a conversion to int/float is tried. If that's not possible,
0 is used.
So after
  m=sim.Monitor(name='m')
  m.tally(2)
  m.tally(True)
  m.tally('12')
  m.tally('red')
m.x() is array([2,1,12,0])
This automatic conversion is used in all monitor methods, apart from getting the
current value.
So, after the above code,
  m() will return 'red'
The unprocessed values are available in the lists
  Monitor._x
end
  MonitorTimestamp._x (along with the coresponding MonitorTimestamp._t)
So, after the above code m._x is (2,True,'12','red') .

The __repr__ methods of Environment, Queue, Component, Monitor, Resource and the
distributions, now return
    Environment(name), Queue(name), ...
E.g. now
    q=sim.Queue('visitors')
    print(q)
returns
    Queue(visitors)
Getting information about one of the above class instances is now provided by
the method print_info (formerly available via __repr__).
E.g.
    q=sim.Queue('visitors')
    print(q)
prints something like
    Queue 0x26e8e78ada0
    name=visitors
    no components

The default random stream when initializing Environment is now 1234567. If a
purely, not reproducable, stream by by specifying Environment(random_seed=None)
or sim.random_seed(None).
If you don't want any action when calling Environment (thats usually for
subsequent run) (cf. Elevator animated.py specify the null string, so
Environment(random_seed='')
All sample models have been updated to reflect this change, i.e. no more
random_seed=1234567 in the call to Environment, there.

Convention change:
Instead of naming the default environment de, from now env is prefered.
All sample models have been updated accordingly.

Documentation change only:
Package numpy is required.
The order of components in Queue.union() and Queue.intersect() is now specified.

Packaging remarks:
Release notes.txt is now called changelog.txt, to be more in line with PyPI standards.

salabim is now on PyPI. So now you can install salabim also with pip install salabim!

version 2.1.3  2017-08-24
=========================
Upto now it was a requirement to build an __init__ method with a call
to super().__init__ if the component had to be initialized in some way.
This is a rather awkward construction and difficult to grasp for beginners.
Although this construction is still accepted, there is now a more elegant
method: setup.
If this method is present in the definition of a component, it will be called
after salabim has done all its initialization and even after the activate
statement, if applicable.
The method may have arguments. If so, whencreating the component, it is
required to use keyword arguments.

salabim any version                    salabim>=2.1.3
--------------------------------------------------------------------
class Car(sim.Component):              class Car(sim.Component):
    def __init__(self,name,color):         def setup(self,color):
        super().__init__(name=name)            self.color=color
        self.color=color               Car(name='BMW',color='red')
Car(name='BMW',color=red)
                              
Note that the __init__ construction is still available.

All examples that used the __init__ construction have been updated
accordingly.

Both salabim and all examples now conform to PEP8 (with the exception
of requirements on line length and visual indent).
    
Bug in print_statistics when monitoring was False fixed.


version 2.1.0
=========================
Not released


version 2.1.2  2017-08-21
=========================
New functionality:
When a Component, Queue or Reseource is created, and the name ends with a period to
signify auto serializing, the first created object with that name does not get serialized.
So after
  wait0=sim.Queue('wait.')
, the name of wait0 is 'wait' .
When a second object with that name is created, the first object is serialized as yet.
So after
  wait0=sim.Queue('wait.')
  wait1=sim.Queue('wait.')
, the name of wait0 is 'wait..............0'
This also holds for Components that are named after their class, like after
  class TrafficLight(sim.Component):
      pass
  t=TrafficLight()
, the name of t is 'trafficlight'
When more traffic lights are created, the name of t will become
'trafficlight.......0'


Name changes for a Component, Queue and Resource are now traced.

Creation of a Component, Queue and Resource is now traced.

Bug in Component.hold() fixed.

version 2.1.1  2017-08-19
=========================
Method Queue.print_statistics() now shows more information.
New: Resource.print_statistics()

If a component now terminates (no more events), all claimed resources are now
automatically released.
Note, that this does not hold for cancellation of a component.

version 2.1.0  2017-08-18
=========================
At creation of a component, it is now possible to specify a process other than self.process to start.
The new process parameter for the init of a component is a string containing the name of the
(generation)function.
Now, there also a check to see if process is a generator (i.e. contains at least one yield statement).

If there is a process attribute in a component, but you do not want that to be activated,
specify process=None. The parameter auto_start is phased out, as there is now process=None.

The process parameter of Component.activate() has been changed. It is now a string containing the
name of the process to be started. If None, no change.

With the function running_process, the name of the currently running process can be retrieved.
For data components, None will be returned.


New to salabim are monitors, which are very useful for collecting (statistical) data.
It is possible to tally values based on occurence, like the length of a ship, each time one is
created. Or the length of stay for components leaving a queue.
Another feature is a timestamped value. This is useful when collecting data on a time axis,
like the length of a queue. Each time the queue length changes, the new length, together
with time is then collected. This is a much more accurate and usually more efficient way of
collecting data than just sampling on a regular basis.

Queue now supports monitoring of key statistics:
  length *
  length_of_stay

Resource now supports monitoring of key statistics:
  requesters.length *
  claimers.length *
  requesters.length_of_stay
  claimers.length_of_stay
  claimed_quantity *
  available_quantity *
  capacity *

The timestamped monitors (marked with a *) can be also used to query the current value, like
  c=myresource.claimed_quantity() or
  l=myqueue.length() although len(myqueue) is preferred

Monitors can be disabled/enabled with monitor (on the level of a Resource, a Queue or an individual Monitor or
MonitorTimeStamp).

salabim <2.1.0                     salabim >= 2.1.0
-------------------------------------------------------------------------------
Queue.reset_statistics()           Queue.reset() / Queue.monitor()
Queue.minimum_length()             Queue.length.minimum()
Queue.maximum_length()             Queue.length.maximum()
Queue.number_passed()              Queue.length_of_stay.number_entries()
Queue.number_direct_passed()       Queue.length_of_stay.number_entries_zero()
Queue.mean_length()                Queue.length.mean()
Queue.mean_length_of_stay()        Queue.length_of_stay.mean()
Queue.minimum_length_of_stay()     Queue.length_of_stay.minimum()
Queue.maximum_length_of_stay()     Queue.length_of_stay.maximum()
Queue.length()                     Queue.length() / len()
Queue.print_statistics()           Queue.print_histogram()
                                   Queue.length.std()
                                   Queue.length.median()
                                   Queue.length.percentile()
                                   Queue.length.bin_count()
                                   Queue.length_of_stay.std()
                                   Queue.length_of_stay.median()
                                   Queue.length_of_stay.percentile()
                                   Queue.length_of_stay.bin_count()
                                   Resource.availabe_quantity ==> MonitorTimeStamp
                                   Resource.claimed_quantity ==> MonitorTimeStamp
                                   Resource.capacity ==> MonitorTimeStamp
Resource.capacity(cap)             Resource.set_capacity(cap)
                                   Component.requested_resources()
                                   Component.requested_quantity(resource)

All monitors can be used with MatPlotLib. For Monitor, there is Monitor.x() to get an array of all
tallied values. For MonitorTimestamp, MonitorTimestamp.xduration() and MonitorTimestamp.xt() are available.
Note that for the time a MonitorTimestamp is disabled, x will be nan.

Defining a non timestamped monitor (class Monitor) is fairly straightforward.
Defining a timestamped monitor is a bit more complicated. The Lock with monitor script shows an example.
Furthermore, refer to the manual for details.

As a consequence of this, Resource.capacity() can no longer be used to change the capacity.
A new method Resource.set_capacity() is provided, instead.

All examples have been updated to support or show the new functionality.

Thanks to Frans Sopers: Bug in Component.release() fixed.
Thanks to Jan Knoop: arialmt font is now included in getfont, which is required for iPad without additional fonts.

version 2.0.2  2017-08-08
=========================
Internal event handling changed, in order to be able to use all event methods (i.e.
activate, hold, request, standby, cancel and passivate regardless whether
the component is current or not). For the current component, always use yield ...
Also, now it is possible to activate, hold or passivate main.

Component.reschedule() and Component.reactivate had been phased out. Both are replaced
by the more versatile Component.activate() method.

Component.activate() has an additional parameter keep_request, which controls whether
pending requests are to be kept upon an activate.

Environment.stop_run() and stop_run() has been phased out.
Use the much more logical Environment.main().activate() or env.main().activate() instead.
This allows the user to specify the time (including inf) of the main reactivation.
The models 'Dining philosophers animated.py' and 'Elevator animated.py' have been
updated accordingly.

Component.request() has now an additional parameter fail_delay.

When a request is pending, the status of the component used to be scheduled, but is now requesting.
Also, a new method Component.isrequesting() is provided to test for this new status

The methods Component.get_priority and Component.set_priority are replaced by one method: Component.priority.

'salabim release notes.txt' is now called 'Release notes.txt'.

The github distribution now also contains the example scripts as used in the manual.

version 2.0.1
=========================
In the specification of Distribution, it is now also possible to use:
c1       ==> Constant(c1)
c1,c2,   ==> Uniform(c1,c2)
c1,c2,c3 ==> Triangular (c1,c2,c3)

It is not required to use the exact name of the distribution anymore.
If you specify only the first letters of the distribution name, the correct distribution will be selected,
regardless of casing.

Examples of these new features
Uniform(13)  ==> Uniform(13)
Uni(12,15)   ==> Uniform(12,15)
UNIF(12,15)  ==> Uniform(12,15)
N(12,3)      ==> Normal(12,3)
Tri(10,20).  ==> Triangular(10,20,15)
10           ==> Constant(10)
12,15        ==> Uniform(12,15)
(12,15)      ==> Uniform(12,15)

Normal distribution now has a default value for standard_deviation : 0, so effectively constant
Uniform distribution now has a default value for upperbound : lowerbound, so effectively constant
Trianguar distribution now has a default value for high : low, so effectively constant
Trianguar distribution now has a default value for mode : (low+high)/2, so a symmetric distribution

version 2.0.0  2017-07-24
=========================
Major reorganization of the interface.

All properties has been phased out and made place for a method. This is
done in order to be more Pythonic and consistent. Also, overriding is now easier.

Version 2.0.0                       Version 2.0.0
---------------------------------------------------------------------------------------
Environment.peek                    Environment.peek()
Environment.main                    Environment.main()
Environment.now                     Environment.now()
Environment.trace                   Environment.trace(value)
Environment.current_component       Environment.current_component()
Environment.name                    Environment.name(txt)
Environment.base_name               Environment.base_name()
Environment.sequence_number         Environment.sequence_number()

Component.claimed_resources         Component.claimed_resources()
Component.request_failed            Component.request_failed()
Component.name                      Component.name(txt)
Component.base_name                 Component.base_name()
Component.sequence_number           Componnt.sequence_number()
Component.suppress_trace            Component.suppress_trace(value)
Component.mode                      Component.mode(value)
Component.ispassive                 Component.ispassive()
Component.iscurrent                 Component.iscurrent()
Component.isscheduled               Component.isscheduled()
Component.isstandby                 Component.isstandby()
Component.isdata                    Component.isdate()
Component.creation_time             Component.creation_time()
Component.scheduled_time            Component.scheduled_time()
Component.mode_time                 Component.mode_time()
Component.status                    Component.status()
Component.now                       phased out, use Component.env.now()
Component.main                      phased out, use Component.env.main()
Component.trace                     phased out, use Component.env.trace(value)
Component.current_component         phased out, use Component.env.current_component()

Resource.requesters                 Resource.requesters()
Resource.claimers                   Resource.claimers()
Resource.capacity                   Resource.capacity(cap)
Resource.claimed_quantity           Resource.claimed_quantity()
Resource.strict_order               Resource.strict_order(value)

Queue.name                          Queue.name(txt)
Queue.base_name                     Queue.base_name()
Queue.sequence_number               Queue.sequence_number()
Queue.head                          Queue.head()
Queue.tail                          Queue.tail()
Queue.pop                           Queue.pop()
Queue.length                        Queue.length(), len() recommended
Queue.minimum_length                Queue.minimum_length()
Queue.maximum_length                Queue.maximum_length()
Queue.minimum_length_of_stay        Queue.minimum_length_of_stay()
Queue.maximum_length_of_stay        Queue.maximum_length_of_stay()
Queue.number_passed                 Queue.number_passed()
Queue.mean_length_of_stay           Queue.mean_length_of_stay()
Queue.mean_length                   Queue.mean_length()

Uniform.mean                        Uniform.mean()
Triangular.mean                     Triangular.mean()
Constant.mean                       Constant.mean()
Exponential.mean                    Exponential.mean()
Normal.mean                         Normal.mean()
Cdf.mean                            Cdf.mean()
Pdf.mean                            Pdf.mean()
Distribution.mean                   Distribution.mean()

Uniform.sample                      Uniform.sample()
Triangular.sample                   Triangular.sample()
Constant.sample                     Constant.sample()
Exponential.sample                  Exponential.sample()
Normal.sample                       Normal.sample()
Cdf.sample                          Cdf.sample()
Pdf.sample                          Pdf.sample()
Distribution.sample                 Distribution.sample()

AnimateSlider.v                     AnimateSlider.v(value)
---------------------------------------------------------------------------------------
***ATTENTION***
Be very careful with adding the parentheses, particularly when using in
logical tests, like:
    if c.ispassive: #always True !
    if c.status==passive #always False !
    if trace: #always True
and never assign to one of these methods,like
    env.trace=True #overrides the trace method of env
    c.name='Machine' # overrides the name method of the component c
    
Nearly all existing models will need be updated. All sample files are now version 2 compatible.

Nearly only internal change: the possible values of the status of a component were up to version 2.0.0
global variables, containing the name of the status. From this version the values of status are actually
references to methods that return the name of the status. This affects passive, data, current, standby,
scheduled and suspended. From an application point of view this does not change anything.
Testing of the status is still done with (e.g.)
    if c.status()=sim.passive:
or, better yet,
    if c.ispassive():
Only when the status has to be printed, be sure to *call* the status() method, thus
print('current status of c=', c.status()())

If the distribution Pdf gets now a distribution as an x-value, not the
distribution, but a sample of that this distribution will be returned.
Example:
  d=sim.Pdf((Uniform(10,20),10,Uniform(20,30),80,Uniform(30,40),10))
  d.sample() # 10% between 10 and 20, 80% between 20 and 30 and 10% between 30 and 40.
  d.mean() # is 25.

The argument list if Component.request() is redefined. See the manual or docstring
for details.
The argument list if Component.release() is redefined. See the manual or docstring
for details.

The method Queue.index_of() has been renamed Queue.index() to be more in line
with Python standards.

The script to install salalabim in site-packages is now called install.py

There are two new sample models, 'Lock with resources' and 'Lock with resources animated',
showing a different approach of the Lock model, involving resources.

Major improvements of the docstrings and manual (at www.salabim.org/manual).
Just a reminder: you can get help on all methods
of salabim (pages and pages of information) with
    import salabim as sim
    help(sim)
or just one method or class by (e.g.)
    import salabim as sim
    help(Animate)
    help(Component.enter)
    help(env.now)
    
Bug fixes.
        
version 1.1.3  2017-07-22
=========================
Pythonista could not handle the long one line statement defining the std_fonts.
Therefore the definition of the dictionary is now in several lines of maximal 80
characters. The table is now also sorted (only for cosmetic reasons).
The colornames dictionary is now sorted (only for cosmetic reasons).

version 1.1.2  2017-07-20
=========================
Under the hood restructuring of classes, thus enabling overriding.

In order to support packaging (i.e make salabim a site_package), the simulation
environment is no longer automatically defined.
It is now necessary to make an environment in the application, by:
    Environment()
The Environment class has now an extra argument, is_default_env, which is True by
default.
Also, the global variable random has been phased out. Instead, salabim uses now
the random class directly in all statistical sampling functions.
It is possible to set the seed of the random stream by means of
- random_seed()
- random.seed(), provided random is imported
- Environment(random_seed=...)
The standard random stream is now used in all distribution definitions, unless
a randomstream is explicitly specified.

Other than in previous versions, reproducibility is only available if
a random seed value is specified, usually when defining an Environment.

All sample programs are defined in such a way that they give reproducible results.

main is no longer a global variable. You can use either the main
property in Component or Environment classes or just main() from the
salabim module, e.g. with env.main()

The default environment can be queried with the function default_env(),
e.g. de=sim.default_env().

All sample filea are updated according to the new interface.

Font handling has been improved. It is now allowed to specify a font by the
file name or the descriptor, e.g.
'timesi' or 'Times New Roman Italic'.
The case is not important any more.
The function show_fonts() can be used to retrieve all currently available
font names (on this machine).

The salabim_install script now installs salabim in a more Pythonic way
in the site-packages folder.

Bug in slider function under Pythonista fixed.

version 1.1.1  2017-07-08
=========================
Bug in video production fixed.
Minor changes in the sample programs.

version 1.1.0  2017-07-08
=========================
The animation of all sample models is completely restructured in order to separate the simulation model
code from the animation code. This leads to much easier to read and debug models. Also the same code can now
be used for animation and production (non animated) applications.

Introduced an attribute 'mode' for components, which can be set either with an assignment or as a parameter of:
    initialization of a component
    passivate
    activate
    reactivate
    hold
    activate
    standby
    request
    cancel
This attribute can be very useful for animations which run more or less separate from the simulation code.
The mode parameter may be any type, although str is possibly the most useful.
Also, the mode is now shown in a trace.

The attribute passive_reason has been phased out, as mode offers similar functionality for passive components. Be aware that mode is not reset automatically!

When the mode is set, either by an assignment or one of the above methods, the property mode_time is
set to now. This is particularly useful for hold, in order to assess when the component started the
hold, like in
  fraction=sim.interpolate(env.now,comp.mode_time,comp.scheduled_time,0,1)
This technique is used in the sample models 'Lock animated' and 'Elevator animated'.

A bug in PIL caused non black texts to have a kind of outline around the characters in Animate(text=...).
This was especially visible with white texts on a dark background.
Code has been added to correct this behaviour.

Introduced a parameter visible for Animate and Animate.update. The method visible of animation
objects can be overridden. This is especially useful in dashboard like animations.

AnimateButton and AnimateSlider no longer have a layer parameter, as these UI elements are now always
on top of the Animate objects.

The animation parameters of run() are all removed. Now, a new animation_parameters method (in class Environment)
is used to set all parameters.
The function animation_speed has been phased out. It is now in animation_parameters.

Pythonista animation performance is increased by building up the image completely with PIL,
before putting it into a scene. This also results in higher quality images
(essentially the same as under tkinter).

On Pythonista, the animation size is now automatically set to the dimension of the screen.
This can be overridden with a call to animation_parameters.

In the animation, the Quit button has been renamed to Stop.

The color of the text in Animate(text=) is now set with textcolor0 and textcolor1 instead of fillcolor0 and
fillcolor1.

If a specified font in Animate cannot be found, the system now searches for calibri and next for arial fonts.

Bug fix: after a yield self.request call, the status of the component was still current, instead of scheduled.

version 1.0.6  2017-06-16
=========================
Animation on CPython platform is now slightly smoother, because there was a bug in the timing routine, which
caused that the animation was doomed to be slower than 30 fps.

The upper right hand corner now shows, optionally, the number of frames per second fps).
The run command has three new parameters, which control what is shown in the upper right hand corner, in case of animation:
        show_fps : bool
            if True, show the number of frames per second (default)|n|
            if False, do not show the number of frames per second

        show_animation_speed: bool
            if True, show the animation speed (default)|n|
            if False, do not show the animation speed
    
        show_time: bool
            if True, show the time (default)|n|
            if False, do not show the time

The text of an AnimateButton is now set via function text(), which can be overridden.

The function str_or_function had been phased out, as this can be achieved now by overriding methods.

version 1.0.5  2017-06-14
=========================
Complete overhaul of the tkinter way objects are shown. Instead of deleting all canvas objects
for each animation tick, salabim now tries to minimize the number of create_image calls,
by using itemconfig and coords and reusing canvas elements, if possible and necessary.
The result is a much smoother animation, particularly at higher animation speeds.
The above doesn't, unfortunately, apply to Pythonista.

Now all of the following methods of the class Animate may be overridden:
    def x(self,t=None)
    def y(self,t=None)
    def offsetx(self,t=None)
    def offsety(self,t=None)
    def angle(self,t=None)
    def linewidth(self,t=None)
    def linecolor(self,t=None)
    def fillcolor(self,t=None)
    def circle(self,t=None)
    def line(self,t=None)
    def polygon(self,t=None)
    def rectangle(self,t=None)
    def width(self,t=None)
    def fontsize(self,t=None)
    def text(self,t=None)
    def anchor(self,t=None)
    def image(self,t=None)
    def layer(self,t=None)
, thus giving the possibility to use non linear movement, special effects, etc.

The distribution now also contains a script called salabim_install, which will install salabim
in the appropriate site-packages folder. Once installed, salabim can be used from whatever location!

version 1.0.4
=========================
Animation interpolation can now be overridden (monkey patched) to allow for
non linear interpolation or advanced animation techniques.
For this make a new class based on Animation and redefine the necessary functions,
like x,y, angle.

As illustration of the possibilities, have a look at demo_override.py

Duck typing implemented for more Pythonic behaviour.


version 1.0.3  2017-05-26
=========================
Minor bug with stop_run in animation mode fixed.


version 1.0.2  2017-05-07
=========================
The animation part of salabim has been redesigned, to make it more
reliable and easier to access.
Animation is not initialized with Animation() any more. Instead, the animation
(and creation of a tkinter canvas in case of CPython) is now started by the
run function.
Therefore, the run function has now a number of additional parameters to set
the size of the canvas, define scaling and transformation, etc.

An animation object is now a class. One of the attributes is the environment
where it belongs to. There are three classes defined:
  Animate()
  Animate_button()
  Animate_slider()
If you don't need animation, PIL does not need to be imported any more.

Also, the run function now supports the creation of an .mp4 video.
For video production, numpy and cv2 (opencv) are required.
This feature is not supported on Pythonista.

The animation_speed can now be get/set by calling animation_speed().

A number of function have been renamed to be more in line with Python naming
(like isinstance):
  is_passive    -> ispassive
  is_current    -> iscurrent
  is_scheduled  -> isscheduled
  is_standby    -> isstandby
  is_data       -> isdata

Bug when in a call to Animate() t0 was specified fixed.

version 1.0.1  2017-03-13
=========================
Iteration of components in a queue is completely reimplemented.
Instead of the function components, iteration is now done the Pythonic way, like
  for comp in myqueue:
Also, the algorithm now allows for very fast iteration even if components are leaving the queue
during the iteration. If there is a change (enter or leave or change of order) during the iteration, the iteration is guaranteed to deliver all components in the queue after the change correctly.
Therefore, there is no need for specification of static and/or removals_possible as in the out phased
components function.

It is also possible to traverse a queue from tail to head, by using reversed as in:
    for comp in reversed(myqueue):
This is also a generator where updates are possible during the iteration.

If you want to get a specific element in a queue, this can be now achieved with
    comp=myqueue[1] to access the second element in the queue.
So, therefore
    myqueue[0] is equivalent to q.head
    myqueue[-1] is equivalent to q.tail
Nevertheless head and tail are still supported, to be more in line with Tomas/Must terminology.
The function Queue.component_with_index has been phased-out.

Slicing of queues is now supported. So
  for c in myqueue[1:3]:
      print(c.name)
will print the names of the second and third element of the queue (provided they are available).
Also,
  for c in myqueue[::-1]:
      print(c.name)
will list the contents of myqueue, in reverse order. In contrast with the above mentioned reversed() this
is just a static snapshot.
 	  
If a static snapshot of the queue contents is required, use
  myqueue[:]
now. In contrast to previous versions of salabim, this is not faster than the standard iteration.

The functions Queue.contains(c) and Component.is_in_queue(q) have been phased out. Instead salabim
now support the much more legible and Pythonic in construction, for example
  if comp in myqueue:
or
  if comp not in queue:

The length of a queue can be found with len(q). The old style Queue.length is still available.

Automatic numbering of components, queues, resources and environments now starts with 0 (in contrast to 1 in previous versions). This is done to be more in line with Python.

All sample models are updated to accommodate the above changes.

Bug fixed: Changing a priority with set_priority, did affect the queue statistics. Now works as intended.

Bug fixed: The parameter use_toplevel in Animation() works as intended.

version 1.0.0  2017-03-01
=========================
The following names have been changed:
SalabimComponent          Component
SalabimQueue              Queue
SalabimEnvironment        Environment
SalabimResource           Resource
salabim_random            random
reset_env (method)        reset
Distribution_from_string  Distribution

The global function reset_env() (not the method of Environment) has been
phased out. Use default_env.reset() instead.

The default process to be executed when creating a component is now called
process, instead of action.
The proc argument of activate has been changed to process.
The proc argument of reschedule has been changed to process.

It is highly recommended to use the pythonistic
  import salabim
or
  import salabim as sim
instead of
  from salabim import *
In all examples, we now use
  import salabim as sim
If you use the latter form, all salabim items have to be preceeded by sim. ,
like sim.Component, sim.Resource, env.main, sim.passive, env.now(), sim.inf.
If you want to use a salabim item without prefixing, use something like
  from salabim import inf,main
along with
  import salabim as sim

In order to avoid having to specifiy sim.passive, sim.scheduled, etc.
when importing as recommended, a number of new properties are introduced:
  is_passive (equivalent to status=sim.passive)
  is_current (eqivalent to status==sim.current)
  is_scheduled (equivalent to status==sim.scheduled)
  is_standby (equivalent to status==sim.standby)
  is_data (equivalent to status==sim.data)

Technical note: The test routines, which were present in the salabim source,
are now in a separate module, called salabim_test.py.

Style note: the name salabim is now all lowercase, to be more Pythonistic.

The utility program salabim0to1.py translates existing version 0 models into
the new version 1 style.
The program translates *ALL* version 0 programs in the current directory,
adding a 1 to the name, e.g. Lock.py will be translated to Lock1.py
Please note, that the translation is not guaranteed to be 100% accurate,
and some fine tuning might be necessary.

All sample models are updated accordingly.

version 0.9.17 (not released)
=============================
Salabim animations can now work in parallel with other modules using tkinter,
like graphics.py. If so, set the parameter use_toplevel to True.
If a user would like to start its own tkinter window(s) next to salabim's
window (initialized with tkiniter.Tk(), just use root=tkinter.Toplevel()
instead of root=tkinter.Tk()

version 0.9.16 2017-02-15
=========================
Bug when using Salabim without animation fixed.

version 0.9.15 2017-01-14
=========================
Improved way of animating circles. Also, now support for offset (most useful in combination with angle).
Better support for transparency(alpha blending) for fill and line colors.

Bugs fixed.

version 0.9.14 2017-02-02
=========================
The classes AnimateCircle, AnimateLine, AnimatePolygon, AnimateRectangle, AnimateImage and AnimateText are now all combined in one class: Animate.
All animations, including images now support scaling and rotation. Also, under Pythonista, convave polygons are now available.
All animation objects support semi-transparency (also called alpha blending or opacity).
Salabim now requires PIL (Pillow) for animations.

Bugs fixed.

version 0.9.13 2017-01-14
=========================
Animation on iPad / Pythonista now supported.
Button and slider animation objects now available without the need to use tkinter functions.
Button and slider animation objects are now also available under Pythonista.
All functions are now documented as docstrings.


version 0.9.12 2016-12-16
=========================
SalabimQueue, SalabimComponent, SalabimResource and SalabimEnvironment as well as distribution now feature __repr__, in order to print the contents of the object.
Thus,e.g., print(q1) now print information of the contents of q1

Now any environment may be reset to initial condition, with reset_env().
The function salabim_reset is renamed into reset_env, which is equivalent to default_env.reset_env()
Environments now have a (optionally serialized) name.

In order to make the usage of the default environment, a number of functions have been changed into global variables:
  default_env
  main

Please observe that these variables should *NEVER* be set by the user.
Tracing of the default environment is still controlled via the trace function or the setter/getter default_env.trace.
Also, now() and current_component() are still to be used to access now and current_component for the default_env.
Alternatively, now, current_component and trace can be accessed directly via the setter/getter of any SalabimComponent.

The function show() of a SalabimQueue has been renamed to print_statistics() and will no longer show the contents of a queue. In order to print the contents of a queue just use print(q).

Introduced a parameter 'reason' for passivate(). A program can now check why a component is passive by means of the property passive_reason. If a component is not passive, passive_reason is None.

Extensive support for animation with tkinter.

Bugs fixed.


version 0.9.11 2016-11-29
=========================
Bug in standby fixed.

When the name of a component is derived from the class name, the name is now serialized, e.g.
  s=Ship()
  print(s.name)
will print
  Ship...............1


version 0.9.10 2016-11-28
=========================
Overhaul of the way randomstreams are used with the Salabim distributions.
Now, instead of a seed, all distibutions can be given a randomstream. If this parameter is omitted, the default randomstream called salabim_random will be used.
This salabim_randomstream will be automatically started with a reproducable seed, i.e. -1.
The user may reseed this distribution with salabim_random.seed(seed) or salabim_random.seed() for a system time dependent (not reproducable) stream.
If the user does not want to use the salabim_random stream, all distributions may be called with something like randomstream=random.Random(11000) or randomstream=mystream.
Please note that the randomstream salabim_random may be (and is recommended to be) used by the native Random sampling routines, like random, shuffle, gauss and sample.


This version contains an extensive animation engine, that is not yet fully tested nor documented. This functionality will be soon available, along with several examples. The animation engine will be fully  available on CPython and Pythonista platforms with tkinter and PIL (Pillow) installed and and with limited functionality when PIL (Pillow) is not available like in PyPy.


version 0.9.8  2016-11-13
=========================
Introduced property base_name and sequence_number for components, queues and resources

sorting_parameter renamed priority to be compatible with resource terminology.

SalabimComponents, SalabimQueue and SalabimResource now have a seqence_number and a base_name attribute (property). The base_name is the string given at initialization time. Even for components, queues and resources whose base name does not end with a period, the sequence_number is available.
When assigning a new name to a component, queue or resource, base_name and sequence_number will be set according to the new name.

Bug fix for method release.

version 0.9.7  2016-11-10
=========================
The queue requests has been renamed to requesters.

Properties that do not return a value, are now functions (again):
  yield passivate  ==> yield passivate()
  yield cancel     ==> yield cancel()
  yield standby    ==> yield standby()
  step             ==> step()
  clear            ==> clear()
  reset_statistics ==> reset_statistics()
  run_stop         ==> run_stop()

Please be sure to update older applications, particularly with respect to
passivate and stop_run, as the old syntax is still valid Python code, but the
functions calls without parenthesis will have no action!

Added comments to resource functionality.


version 0.9.6  2016-11-06
=========================
Specification of a pdf now allows the x value to be a pair in the form of a list or tuple.
If so, uniform sampling between these will be used if 'selected'.
Example
d=Pdf((10,(5,10),80,(10,50),10,(50,100))
In this case 10% will be 5-10, 80% between 10 and 50 and 10% from 50 to 100.
There is not any restriction on the value pairs, so they may be overlapping or be completely separate. Also, scalars may be
used in the same pdf specification. So the following is allowed, although not very likely to be useful:
d=Pdf((10,0, 20,(-5,50), 30,(100,500), 1,2000)

The method mean() is now available for all distributions.

If no name is specified when initializing a SalabimComponent, the name is now derived from the
class name (lowercased), e.g.
  mycar=Car()
makes car the name of mycar.

Queue methods union, intersect and difference optimized for performance.

Introduced support for resources requesting/releasing resources. The functionality is similar to resources and levels in SimPy and semaphores in Tomas.
This is a concept, with which a component can claim a quantity from a resource. A component is able to request from more than one resource at a time ('and' clause).
Once all the requested quantities are available, the program continues with the next statement.
The requested quantities are then claimed.
Anyone (but most of the time it will be the requesting component) can then release (part of) the claimed quantities.
The resource can be also anonymous, which means that the claimed quantities are not connected to a component, but just treated as one heap. This is similar to levels in SimPy.
*to be described in more detail*

The following methods are now properties and are to be used without ():
SalabimQueue
  name *)
  head
  tail
  pop
  length
  minimum_length
  maximum_length
  minimum length_of_stay
  maximum_length_of_stay
  number_passed
  number_passed_direct
  mean_length_of_stay
  mean_length
  clear
  reset_statistics

SalabimEnvironment
  step
  peek
  main
  now
  trace *)
  current_component

SalabimComponent
  passivate
  cancel
  standby
  stop_run
  granted_resources
  request_failed
  name *)
  main
  now
  trace *)
  creation_time
  scheduled_time
  current_component
  status

Distributions_from_string
  mean
  sample

SalabimResource
  requests
  claimers
  claimed_quantity
  strict_order *)
  name *)

*) means that these are also setters, so for instance c.name='box'.

Finally, the following functions, which are not part of a class still require ():
  main()
  now()
  trace() or trace(val)
  step()
  peek()

version 0.9.5  2016-10-27
=========================
It is now possible to use a default environment.
In most cases there will be no need to use the concept of environments at all, which results in an
easier to understand and read program.
Therefore, upon startup, Salabim automatically creates an environment, which is available via
default_env() if required.
The default environment is an excellent placeholder for pseudo global variables.
A new default environment (e.g. for a new run or experiment), can be set via salabim_reset(). Note that
also the pseudo globals will be 'lost' then.

For the (few) methods/properties that required an environment as parameter, the following alternatives
are available:
  env.run()                                run()
  env.peek()                               peek()
  env.step()                               step()
  env.now()                                now()
  env.main()                               main()
Furthermore tracing control is implemented differently and may be set/retrieved now via
  env.trace()                              trace()
Both with SalabimEnvironent.__init__ as well as salabim_reset the trace parameter can be set (it is False
by default).

It is now possible to schedule a component from the initialization by including an action() method in
the class for this component. If so, it will be auto started, optionally at a later moment, specified by the at, delay and urgent parameters as in activate.

All properties have been removed to be more consistent (reversing the changes of one of the previous
versions). Therefore, now all values to be retrieved, like q.length() and c.name() need a pair of parentheses.

Retrieving and setting of the sorting_parameter of a component in a queue is now done with *one* function: sorting_parameter.

The trace now also shows the name of the action generator, in case it's not action()?

Distributions are now documented. Please observe that Table is renamed to Cdf and Discrete if renamed to Pdf.

version 0.9.4  2016-10-25
=========================
The method components to iterate over all components in a queue now has an additional parameter
  'removals_possible'.
  If it is guaranteed that no components will leave the queue during the iteration, this parameter
  may be set to False.
  Also in that case, components that do not enter the queue *at the tail*, might be excluded
  from the iteration. The result is a speed increase (particularly with large queues).

Internal:
Optimalisations for several queue methods, by using the result of the check for membership of a queue in
subsequent actions.

version 0.9.3  2016-10-24
=========================
The method stop_run has been added.

version 0.9.2  2016-10-23
=========================
Major bug in the activate, hold, reactivate and reschedule fixed

Now supports also older versions of Python, where NumPy does not feature nan and inf.

Now Python 2.7 compatible (not fully tested yet).

Optimized the method components, which is particularly useful if the queues is large. The method was O(n^2) and is now O(n).

Beautified the trace output.


version 0.9.0  2016-10-23
=========================
This version has a number of changes compared to previous versions.

Salabim does not rely on SimPy anymore.

The statuses now comply more with Must and Prosim than with Tomas, in order to achieve a more consistent interface.

State transition diagram


from\to  |        data|   current|       scheduled|        passive|      standby|
---------+------------+----------+----------------+---------------+-------------+
data     |      -     |  activate|        activate|              -|            -|
         |            |        1)|                |               |             |
---------+------------+----------+----------------+---------------+-------------+
current  |  action end|         -|      yield hold|yield passivate|yield standby|
         |yield cancel|          |yield reschedule|               |             |
---------+------------+----------+----------------+---------------+-------------+
scheduled|      cancel|next event|      reschedule|      passivate|            -|
         |            |          |                |               |             |
---------+------------+----------+----------------+---------------+-------------+
passive  |      cancel|reactivate|      reactivate|              -|            -|
         |            |        1)|      reschedule|               |             |
---------+------------+----------+----------------+---------------+-------------+
standby  |      cancel|next event|      reschedule|              -|            -|
         |            |          |                |               |             |
---------+------------+----------+----------------+---------------+-------------+
1) via scheduled

The method activate now has an optional parameter for the action. If omitted, action will be assumed. So if the action of the component
description is just called action, then the component can be started with component.activate(), which is functionally the
equivalent to component.activate(component.action()).

The method hold now supports 'duration' as well as 'till' parameters (even both are permitted)
activate, reactivate and reschedule now support 'at' as well 'delay' (even both are permitted)
All transitions to current are via scheduled now.

It is now possible to issue a new action in activate, reactivate and reschedule, even for the current component via reschedule.

The methods reactivate, activate, reschedule and hold now have an 'urgent' parameter, which, if True, will schedule
this component before each component with the same scheduled time. When urgent=False (default), component are scheduled after all
components with the same scheduled time.

The method run now supports 'duration' as well as 'till' parameters (even both are permitted).

The scheduled time is now accessible for all component via scheduled_time. If the component is data or passive, inf will be returned.
The creation time is now available via creation_time.


Many functions without parameters are now a property.

New naming:
    q.components (was q.iterate)
    q.mean_length (was q.average_length)
    q.mean_length_of_stay (was q.average_length_of_stay)
    q.add_in_front_of (was q.add_before)
    q.add_behind (was q.add_after)
    c.enter_in_front_of (was c.enter_before)
    c.enter_behind (was c.enter_after)

Names for queues and components are serialized separately now, if the name end with a period.

Introduced statistical distribution sampling.
    Exponential
    Normal
    Uniform
    Triangular
    Constant
    Table
    Discrete
    Distribution_from_string

Note that these distributions are not yet fully documented.

Improved trace functionality.


All functions and classes are now fully documented in the source code. Use help(...) to obtain information.
