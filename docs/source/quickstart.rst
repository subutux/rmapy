quick start
==========

If you previously used the go package `rmapi`_ ,the keys for authorization
are re-used because we use the same storage location & format.

If not, you'll need to register the client as a new device on `my remarkable`_.


.. _my remarkable: https://my.remarkable.com/connect/remarkable

.. _rmapi: https://github.com/juruen/rmapi


Registering the API Client
~~~~~~~~~~~~~~~~~~~~~~~~~~

Registering the device is easy. Go to `my remarkable`_ to register a new device
and use the code you see on the webpage

.. code-block:: python
   :linenos:


    from rmapy.api import Client

    rmapy = Client()
    # Should return False
    rmapy.is_auth()
    # This registers the client as a new device. The received device token is
    # stored in the users directory in the file ~/.rmapi, the same as with the
    # go rmapi client.
    rmapy.register_device("fkgzzklrs")
    # It's always a good idea to refresh the user token every time you start
    # a new session.
    rmapy.refresh_token()
    # Should return True
    rmapy.is_auth()

Working with items
~~~~~~~~~~~~~~~~~~

The remarkable fs structure is flat containing metadata objects of two types:

* DocumentType
* CollectionType

We can list the items in the Cloud

.. code-block:: python
   :linenos:

    >>> from rmapy.api import Client
    >>> rmapy = Client()
    >>> rmapy.renew_token()
    True
    >>> collection = rmapy.get_meta_items()
    >>> collection
    <rmapy.collections.Collection object at 0x7fa1982d7e90>
    >>> len(collection)
    181
    >>> # Count the amount of documents
    ... from rmapy.document import Document
    >>> len([f for f in collection if isinstance(f, Document)])
    139
    >>> # Count the amount of folders
    ... from rmapy.folder import Folder
    >>> len([f for f in collection if isinstance(f, Folder)])
    42



DocumentType
````````````

A DocumentType is a document. This can be a pdf, epub or notebook.
These types are represented by the object :class:`rmapy.document.Document`


Changing the metadata is easy

.. code-block:: python
   :linenos:


    >>> from rmapy.api import Client
    >>> rmapy = Client()
    >>> rmapy.renew_token()
    True
    >>> collection = rmapy.get_meta_items()
    >>> doc = [ d for d in collection if d.VissibleName == 'ModernC'][0]
    >>> doc
    <rmapy.document.Document a969fcd6-64b0-4f71-b1ce-d9533ec4a2a3>
    >>> doc.to_dict()
    {'ID': 'a969fcd6-64b0-4f71-b1ce-d9533ec4a2a3', 'Version': 1, 'Message': '', 'Succes': True, 'BlobURLGet': '', 'BlobURLGetExpires': '0001-01-01T00:00:00Z', 'BlobURLPut': '', 'BlobURLPutExpires': '', 'ModifiedClient': '2019-09-18T20:12:07.206206Z', 'Type': 'DocumentType', 'VissibleName': 'ModernC', 'CurrentPage': 0, 'Bookmarked': False, 'Parent': ''}
    >>> doc.VissibleName = "Modern C: The book of wisdom"
    >>> # push the changes back to the Remarkable Cloud
    ... rmapy.update_metadata(doc)
    True
    >>> collection = rmapy.get_meta_items()
    >>> doc = [ d for d in docs if d.VissibleName == 'ModernC'][0]
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    IndexError: list index out of range
    >>> doc = [ d for d in docs if d.VissibleName == 'Modern C: The book of wisdom'][0]
    >>> doc
    <rmapy.document.Document a969fcd6-64b0-4f71-b1ce-d9533ec4a2a3>
    >>> doc.to_dict()
    {'ID': 'a969fcd6-64b0-4f71-b1ce-d9533ec4a2a3', 'Version': 1, 'Message': '', 'Succes': True, 'BlobURLGet': '', 'BlobURLGetExpires': '0001-01-01T00:00:00Z', 'BlobURLPut': '', 'BlobURLPutExpires': '', 'ModifiedClient': '2019-09-18T20:12:07.206206Z', 'Type': 'DocumentType', 'VissibleName': 'Modern C: The book of wisdom', 'CurrentPage': 0, 'Bookmarked': False, 'Parent': ''}


CollectionType
``````````````

A CollectionType is a Folder.

These types are represented by the object :class:`rmapy.folder.Folder`

Working with folders is easy!

.. code-block:: python
   :linenos:


    >>> from rmapy.api import Client
    >>> rmapy = Client()
    >>> rmapy.renew_token()
    True
    >>> collection = rmapy.get_meta_items()
    >>> collection
    <rmapy.collections.Collection object at 0x7fc4718e1ed0>
    >>> from rmapy.folder import Folder
    >>> # Get all the folders. Note that the fs of Remarkable is flat in the cloud
    ... folders = [ f for f in collection if isinstance(f, Folder) ]
    >>> folders
    [<rmapy.folder.Folder 028400f5-b258-4563-bf5d-9a47c314668c>, <rmapy.folder.Folder 06a36729-f91e-47da-b334-dc088c1e73d2>, ...]
    >>> # Get the root folders
    ... root = [ f for f in folders if f.Parent == "" ]
    >>> root
    [<rmapy.folder.Folder 028400f5-b258-4563-bf5d-9a47c314668c>, <rmapy.folder.Folder 5005a085-d7ee-4867-8859-4cd90dee0d62>, ...]
    >>> # Create a new folder
    ... new_folder = Folder("New Folder")
    >>> new_folder
    <rmapy.folder.Folder 579df08d-7ee4-4f30-9994-887e6341cae3>
    >>> rmapy.create_folder(new_folder)
    True
    >>> # verify
    ... [ f for f in rmapy.get_meta_items() if f.VissibleName == "New Folder" ]
    [<rmapy.folder.Folder 579df08d-7ee4-4f30-9994-887e6341cae3>]
    >>> [ f for f in rmapy.get_meta_items() if f.VissibleName == "New Folder" ][0].ID == new_folder.ID
    True
    >>> # Move a document in a folder
    ... doc = rmapy.get_doc("a969fcd6-64b0-4f71-b1ce-d9533ec4a2a3")
    >>> doc
    <rmapy.document.Document a969fcd6-64b0-4f71-b1ce-d9533ec4a2a3>
    >>> doc.Parent = new_folder.ID
    >>> # Submit the changes
    ... rmapy.update_metadata(doc)
    True
    >>> doc = rmapy.get_doc("a969fcd6-64b0-4f71-b1ce-d9533ec4a2a3")
    >>> doc.Parent == new_folder.ID
    True


Uploading & downloading
~~~~~~~~~~~~~~~~~~~~~~~~

reMarkable has a "special" file format for the raw documents.
This is basically a zip file with files describing the document.

Here is the content of an archive retried on the tablet as example:

    * 384327f5-133e-49c8-82ff-30aa19f3cfa40.content
    * 384327f5-133e-49c8-82ff-30aa19f3cfa40-metadata.json
    * 384326f5-133e-49c8-82ff-30aa19f3cfa40.pdf
    * 384327f5-133e-49c8-82ff-30aa19f3cfa40.pagedata
    * 384327f5-133e-49c8-82ff-30aa19f3cfa40.thumbnails/0.jpg

As the .zip file from remarkable is simply a normal .zip file
containing specific file formats.

You can find some help about the format at the following URL:
https://remarkablewiki.com/tech/filesystem

Uploading
`````````

To upload a pdf or epub file, we'll first need to convert it into
the remarkable file format:


.. code-block:: python
   :linenos:


    >>> from rmapy.document import ZipDocument
    >>> from rmapy.api import Client
    >>> rm = Client()
    >>> rm.renew_token()
    True
    >>> rawDocument = ZipDocument(doc="/home/svancampenhout/27-11-2019.pdf")
    >>> rawDocument
    <rmapy.document.ZipDocument b926ffc2-3600-460e-abfa-0fcf20b0bf99>
    >>> rawDocument.metadata["VissibleName"]
    '27-11-2019'

Now we can upload this to a specific folder:

.. code-block:: python
   :linenos:


    >>> books = [ i for i in rm.get_meta_items() if i.VissibleName == "Boeken" ][0]
    >>> rm.upload(rawDocument, books)
    True

And verify its existance:

.. code-block:: python
   :linenos:

    >>> [ i.VissibleName for i in collection.children(books) if i.Type == "DocumentType" ]
    ['Origin - Dan Brown', 'Flatland', 'Game Of Thrones', '27-11-2019']

