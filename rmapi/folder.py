from .meta import Meta
from datetime import datetime
from uuid import uuid4
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from .const import RFC3339Nano
from typing import Tuple, Optional

class ZipFolder(object):
    """A dummy zipfile to create a folder

    This is needed to create a folder on the Remarkable Cloud
    """

    def __init__(self, ID: str):
        """Creates a zipfile in memory

        Args:
            ID: the ID to create a zipFolder for
        """
        super(ZipFolder, self).__init__()
        self.ID = ID
        self.file = BytesIO()
        self.Version = 1
        with ZipFile(self.file, 'w', ZIP_DEFLATED) as zf:
            zf.writestr(f"{self.ID}.content", "{}")
        self.file.seek(0)


class Folder(Meta):
    """
    A Meta type of object used to represent a folder.
    """

    def __init__(self, name: Optional[str] = None, **kwargs) -> None:
        """Create a Folder instance

        Args:
            name: An optional name for this folder. In the end, a name is
                really needed, but can be ommitted to set a later time.
        """

        super(Folder, self).__init__(**kwargs)
        self.Type = "CollectionType"
        if name:
            self.VissibleName = name
        if not self.ID:
            self.ID = str(uuid4())

    def create_request(self) -> Tuple[BytesIO, dict]:
        """Prepares the nessesary parameters to create this folder.

        This creates a ZipFolder & the nessesary json body to
        create an upload request.
        """

        return ZipFolder(self.ID).file, {
            "ID": self.ID,
            "Type": "CollectionType",
            "Version": 1
        }

    def update_request(self) -> dict:
        """Perpares the nessesary parameters to update a folder.

        This sets some parameters in the datastructure to submit to the API.
        """

        data = self.to_dict()
        data["Version"] = data.get("Version", 0) + 1
        data["ModifiedClient"] = datetime.utcnow().strftime(RFC3339Nano)
        return data

    def __str__(self):
        return f"<rmapi.folder.Folder {self.ID}>"

    def __repr__(self):
        return self.__str__()



