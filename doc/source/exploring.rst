#######################
Exploring the IO System
#######################

The string representation of IO system as well as the extensions provides some
information about available attributes.

.. code python::

    import pymrio
    mrio = pymrio.load_test()
    
    print(mrio)
    print(mrio.emissions)

The output of the description changes depending on the calculated accounts:    

.. code python::
    
    mrio.calc_all()
    print(mrio)

Further information can be found in the API Reference.
