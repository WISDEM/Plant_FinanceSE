# DEPRECATED
------------

**THIS REPOSITORY IS DEPRECATED AND WILL BE ARCHIVED (READ-ONLY) IN NOVEMBER 2019.**

WISDEM has moved to a single, integrated repository at https://github.com/wisdem/wisdem

---------------
# Plant_FinanceSE

Plant_FinanceSE is a set of models for assessing overall wind plant cost of energy (coe).  The models use wind turbine and plant cost and energy production information as well as several financial parameters in simple equations to estimate coe.

Author: [NREL WISDEM Team](mailto:systems.engineering@nrel.gov) 

## Documentation

See local documentation in the `docs`-directory or access the online version at <http://wisdem.github.io/Plant_FinanceSE/>

## Installation

For detailed installation instructions of WISDEM modules see <https://github.com/WISDEM/WISDEM> or to install Plant_FinanceSE by itself do:

    $ python setup.py install

## Run Unit Tests

To check if installation was successful try to import the package:

	$ python
	> import plant_financese.basic_finance.coe_fin
	> import plant_financese.nrel_csm_fin.nrel_csm_fin

You may also run the unit tests which include functional and gradient tests.  Analytic gradients are provided for variables only so warnings will appear for missing gradients on model input parameters; these can be ignored.

	$ python src/test/test_Plant_FinanceSE.py

For software issues please use <https://github.com/WISDEM/Plant_FinanceSE/issues>.  For functionality and theory related questions and comments please use the NWTC forum for [Systems Engineering Software Questions](https://wind.nrel.gov/forum/wind/viewtopic.php?f=34&t=1002).
