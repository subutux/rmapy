class Meta(object):
    """ Meta represents a real object expected in most
    calls by the remarkable API

    This class is used to be subclassed by for new types.

    Attributes:
        ID: Id of the meta object.
        Version: The version of this object.
        Success: If the last API Call was a success.
        BlobURLGet: The url to get the data blob from. Can be empty.
        BlobURLGetExpires: The expiration date of the Get url.
        BlobURLPut: The url to upload the data blob to. Can be empty.
        BlobURLPutExpires: The expiration date of the Put url.
        ModifiedClient: When the last change was by the client.
        Type: Currently there are only 2 known types: DocumentType &
            CollectionType.
        visibleName: The human name of the object.
        CurrentPage: The current selected page of the object.
        Bookmarked: If the object is bookmarked.
        parent: If empty, this object is is the root folder. This can be an ID
            of a CollectionType.

    """
    deleted = False
    lastModified = ''
    lastOpenedPage = 0
    metadatamodified = False
    modified = False
    parent = ''
    pinned = False
    synced = False
    type = 'DocumentType'
    version = 0,
    visibleName = ''
    ID = ''
    cloud_id = ''
    meta_cloud_id = ''

    def __init__(self, **kwargs):
        k_keys = self.to_dict().keys()
        for k in k_keys:
            setattr(self, k, kwargs.get(k, getattr(self, k)))

    def to_dict(self) -> dict:
        """Return a dict representation of this object.

        Used for API Calls.

        Returns
            a dict of the current object.
        """

        return dict(deleted=self.deleted,
                    lastModified=self.lastModified,
                    lastOpenedPage=self.lastOpenedPage,
                    metadatamodified=self.metadatamodified,
                    modified=self.modified,
                    parent=self.parent,
                    pinned=self.pinned,
                    synced=self.synced,
                    type=self.type,
                    version=self.version,
                    visibleName=self.visibleName,
                    ID=self.ID,
                    cloud_id=self.cloud_id,
                    meta_cloud_id = self.meta_cloud_id)
