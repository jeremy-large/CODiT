#  Covid Opensource Digital Twin project (CODiT)

#### Creating provisional code to model a ccommunity's response to the Covid-19 epidemic

## Introduction

This codebase uses agent-based methods to simulate the spread of an epidemic such as Covid-19 through a population.
It was motivated by concern that many geographies could benefit from a _focused-systems_ approach to supressing C19. 
For example, it could be used to explore the hypothesis that a stream of testing focused on the people who are most likely 
to spread the disease could reduce R significantly. 

This is suitable to simulate the impact of various strategies on a population of up to 1M+ with a network of contacts.  

It consists of three parts:

1. A Model which provides a network of contacts between people that is meant to be an approximate twin of the city/area in question.

1. A Simulator which simulates the progress of C19 through the network as impeded by various policies (eg on testing, tracing, isolation)

1. A Looper which allows many runs to be taken to assess the stochasticity of the results and the impact of varying parameters of interest.


Although our model inevitably vastly oversimplifies some complex and poorly understood issues, 
we believe that it does give insight; however there are doubtless assumptions in need of pushback or recoding. 

We now provide a little more detail on the Model.

### Model
This is the first of the three components provided in this codebase. It consists of:

1.	A model population, potentially stratified by age, gender and C19 risk, who
a.	experience relevant symptoms due both to C19 and to non-C19, and 
b.	pass-on C19 to contacts on a realistic timescale.

2.	A network of physical contacts in Leeds at this time
a.	Household structure
b.	Study- / work-place structure
c.  School classroom structure
d.  Care home structure
e.	Ephemeral contact
f.  ...

3.	Estimates of compliance by the public with health measures such as the current Test/Trace/Isolate system, built around a scaffold of interpretable parameters

4.	Modelled tests (PCR, lateral flow…) with finite capacity where backlogs can develop.
We generate estimates of (1 & 2) using publicly available data. 

So the model can be thought of as an approximate Digital Twin for a community such as a city, 
randomizing where necessary after accessing publicly available data. 

## Installation instructions

Having cloned this repo, conda should be used to create the required environment to run the code.

TODO: Paul please elaborate 

With this environment, code can be run provided that the environment variable, `PYTHONPATH`, has been set
to `.../CODiT/lib`. To achieve this, the scripts `add_pythonpath.bat` and `add_pythonpath.sh` are provided, 
for the cases, respectively, of Windows and Linux.

When using pycharm to edit this code, show all project interpreters, select the one suitable for this project, 
then, clicking on the 'tree' icon, add an environment variable called `PYTHONPATH`, 
whose value is the absolute path of `.../CODiT/lib`. The testing infrastructure should be set to `pytest`, 
rather than its common default.

## Running instructions

Begin with `share/notebooks/overview.ipynb`. Copy this and run the copy in `jupyter lab`.
This applies the Simulator to several Models in turn, in order to generate various epidemic curves.

The other two notebooks in `share/notebooks` offer more detailed functionality, 
including an implementation of a Looper.
