############
Installation
############

Up to now now pymrio doesn't have a installation routine. Just download the package and add the folder to your python path. 

>>> import sys
>>> _pymrio_path = 'c:/downloads/pymrio'  
>>> if not _pymrio_path in sys.path:
>>>    sys.path.append(_pymrio_path)
>>> del _pymrio_path

***************
Python versions
***************

- Python version 3.3+

************
Dependencies
************

- pandas
- numpy
- matplotlib

************************
Recommended Dependencies
************************

- docutils: For generating reports in tex and html format
- seaborn: Improves the figure appearance tremendously. http://stanford.edu/~mwaskom/software/seaborn/index.html

