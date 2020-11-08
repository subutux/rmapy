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
        VissibleName: The human name of the object.
        CurrentPage: The current selected page of the object.
        Bookmarked: If the object is bookmarked.
        Parent: If empty, this object is is the root folder. This can be an ID
            of a CollectionType.

    """

    ID = ""
    Version = 0
    Message = ""
    Success = True
    BlobURLGet = ""
    BlobURLGetExpires = ""
    BlobURLPut = ""
    BlobURLPutExpires = ""
    ModifiedClient = ""
    Type = ""
    VissibleName = ""
    CurrentPage = 1
    Bookmarked = False
    Parent = ""

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

        return {
            "ID": self.ID,
            "Version": self.Version,
            "Message": self.Message,
            "Success": self.Success,
            "BlobURLGet": self.BlobURLGet,
            "BlobURLGetExpires": self.BlobURLGetExpires,
            "BlobURLPut": self.BlobURLPut,
            "BlobURLPutExpires": self.BlobURLPutExpires,
            "ModifiedClient": self.ModifiedClient,
            "Type": self.Type,
            "VissibleName": self.VissibleName,
            "CurrentPage": self.CurrentPage,
            "Bookmarked": self.Bookmarked,
            "Parent": self.Parent
        }

