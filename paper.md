---
title: 'salabim: discrete event simulation and animation in Python'
tags:
  - Python
  - simulation
  - DES
  - process
  - animation
authors:
 - name: Ruud van der Ham
   orcid: 0000-0001-7696-8059
   affiliation: "1, 2"
affiliations:
 - name: salabim.org
   index: 1
 - name: Upward Systems
   index: 2
date: 27 May 2018
bibliography: paper.bib
---

# Summary

Salabim is a discrete event simulation package in Python.

A discrete-event simulation (DES) models the operation of a system as a discrete sequence of events in time. Each event occurs at a particular instant in time and marks a change of state in the system. Between consecutive events, no change in the system is assumed to occur; thus the simulation can directly jump in time from one event to the next.

This contrasts with continuous simulation in which the simulation continuously tracks the system dynamics over time. Instead of being event-based, this is called an activity-based simulation; time is broken up into small time slices and the system state is updated according to the set of activities happening in the time slice.[2] Because discrete-event simulations do not have to simulate every time slice, they can typically run much faster than the corresponding continuous simulation.

Applications of DES can be found in transportion research, manufacturing, mining, hospital logistics, (air)ports, network analysis, etc.

There is a wide range of packages and languages available, many of them proprietary and very expensive.
In the open source world, there are open source projects based on Java (dSOL), Julia (SimJulia), R (Simmer),
Pascal/Delphi(Tomas) and in Python SimPy and salabim.
Several of these packages use the Simula activate/passivate/hold paradigm, which leads to very clear
and easy to maintain models.
SimPy, the other DES under Python, does not follow that process description method and is therefore more difficult
to use for modellers. Also, salabim provides animation, queues, 'states', monitors for data
collection and presentation, tracing and statistical distributions, none of which are present in SimPy.

The integrated 2D-animation makes validation and demonstration simple and powerful.

Simulations and animations run under CPython or PyPy on Windows, Linux, OSX and iOS.
The ability to simulate and animate models on a iPad is unique.

Salabim has applications in transportion research, manufacturing, mining, hospital logistics, network analysis, etc.

# References
Several wikipedia articles on DES and simulation languages.


