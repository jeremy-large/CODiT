#  Covid Opensource Digital Twin project (CODiT)

#### Creating provisional code to model a community's response to the Covid-19 epidemic

## Introduction

This codebase uses agent-based methods to simulate the spread of an epidemic such as Covid-19 through a population.
It was motivated by concern that many geographies could benefit from a _focused-systems_ approach to suppressing C19. 
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

1.	A model [population](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/networks/city.py#L13), 
potentially stratified by age, gender and C19 risk, who
a.	experience [relevant symptoms](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/covid.py#L37) 
due both to C19 and to non-C19, and 
b.	[pass-on C19 to contacts](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/person.py#L38) on a realistic timescale.

2.	A network of physical contacts in the region at a point in time
a.	[Household structure](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/networks/city_config/typical_households.py#L8)
b.	[Study- / work-place structure](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/networks/city.py#L123)
c.  [School classroom structure](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/networks/city.py#L73))
d.  [Care home structure](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/networks/city.py#L44)
e.	[Ephemeral contact](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/population/networks/city.py#L22)
f.  ...

3.	Estimates of compliance by the public with health measures such as the current Test/Trace/Isolate system, 
built around a [scaffold of interpretable parameters](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/config.py)

4.	[Modelled tests](https://github.com/jeremy-large/CODiT/blob/master/lib/codit/society/test.py) (PCR, lateral flow…) with finite capacity where backlogs can develop.
We generate estimates of (1 & 2) using publicly available data. 

So the model can be thought of as an approximate Digital Twin for a community such as a city, 
randomizing where necessary after accessing publicly available data. 

## Installation instructions

The github repo can be cloned on to your local machine:
```
$ git clone git@github.com:jeremy-large/CODiT.git
```
or
```
$ git clone https://github.com/jeremy-large/CODiT.git
```
Once cloned, you can either build and install the repo as a **conda** package, or you can simply add the repo lib dir to 
your **PYTHONPATH** environment variable so that you can import the modules locally.

### 1) Local development

If you are a developer looking to adapt CODiT to local needs, it is more likely that you will engage in some
local development. 

For this, you would add the `.../CODiT/lib` directory appearing in your local repo, 
to your **PYTHONPATH** environment variable.  

You can do this manually, or there is a handy batch script for Windows in the repo called 
[add_pypath.bat](https://github.com/jeremy-large/CODiT/blob/master/add_pypath.bat) that will do this for you.
Similarly there is a bash script called 
[add_pypath.sh](https://github.com/jeremy-large/CODiT/blob/master/add_pypath.sh) to do this under linux and osx.

You will also need to create a conda environment that is suitable for this project. 
This can be achieved with the commands:

```
$ conda create -n tti -c anaconda python=3.8 scikit-learn=0.22.1 xlrd=1.1.0 pandas matplotlib jupyterlab nbconvert pydot networkx pytest
$ conda activate tti
```

(thereby naming the environment `tti`)

#### Local development with pycharm

When using **pycharm** to edit and run this code, it will also be necessary to create a suitable project interpreter. 
This can be achieved through the pycharm gui by

1. setting the pycharm interpreter to use conda, and within conda selecting the environment, `tti`;
 
1. setting testing infrastructure to `pytest`, rather than its common default;

1. adjusting this pycharm interpreter by extending its python path to point at your local version of the CODiT libraries.
Select the interpreter from a list (it may be called `tti`), click on the 'tree' icon, 
and add to the displayed list a directory, which you specify to be the absolute path 
of `.../CODiT/lib`.

### 2) Installation as a conda package

(Assuming you are using conda) you can enter the repo directory, 
build the CODiT conda package and then install it into your current conda environment:
```
$ cd CODiT
$ conda build --no-test .
$ conda install --use-local codit
```
## Running instructions

Begin with `share/notebooks/overview.ipynb`. Copy this and run the copy in `jupyter lab`.
This applies the Simulator to several Models in turn, in order to generate various epidemic curves.

The other two notebooks in `share/notebooks` offer more detailed functionality, 
including an implementation of a Looper.
