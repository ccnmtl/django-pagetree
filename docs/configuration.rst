Configuration
=============

.. configuration::

`PAGETREE_CUSTOM_CACHE_CLEAR`
    Use this as a hook to clear any custom caches you've set up. It will
    get called whenever Pagetree's internal cache is called. The function
    should take one argument: the `Section` whose cache is getting cleared.
