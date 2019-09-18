quickstart
==========

If you previously used the go package `rmapi`_ ,the keys for authorization
are re-used because we use the same storage location & format.

If not, you'll need to register the client as a new device on `my remarkable`_.


.. _my remarkable: https://my.remarkable.com/connect/remarkable

.. _rmapi: https://github.com/juruen/rmapi


Registering the API CLient
~~~~~~~~~~~~~~~~~~~~~~~~~~

Registering the device is easy. Go to `my remarkable`_ to register a new device
and use the code you see on the webpage

.. code-block:: python
   :linenos:


    from rmapi.api import Client

    rmapi = Client()
    # Shoud return False
    rmapi.is_authenticated()
    # This registers the client as a new device. The received device token is
    # stored in the users directory in the file ~/.rmapi, the same as with the
    # go rmapi client.
    rmapi.register_device("fkgzzklrs")
    # It's always a good idea to refresh the user token everytime you start
    # a new session.
    rmapi.refresh_token()
    # Shoud return True
    rmapi.is_authenticated()

Working with items
~~~~~~~~~~~~~~~~~~

The remarkable fs structure is flat containing metadata objects.

