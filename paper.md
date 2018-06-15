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
It uses the process description method as shown in Simula, must, Tomas and SimPy2.
That means processes can be (re)activated, passivated, held, etc.

SimPy3, the most used DES under Python, does not follow the same process description method and is more difficult
to use for modellers. Also, salabim provides animation, queues, 'states', monitors for data
collection and presentation, tracing and statistical distributions, none of which are present in SimPy3.

The integrated 2D-animation makes validation and demonstration simple and powerful.

Simulations and animations run under CPython or PyPy on Windows, Linux, OSX and iOS.
The ability to simulate and animate models on a iPad is unique.

Salabim has applications in transportion research, manufacturing, mining, hospital logistics, network analysis, etc.

