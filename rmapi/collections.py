from .document import Document
from .folder import Folder
from typing import NoReturn, List, Union
from .exceptions import FolderNotFound

DocumentOrFolder = Union[Document, Folder]


class Collection(object):
    """A collection of meta items

    This is basicly the content of the Remarkable Cloud.

    Attributes:
        items: A list containing the items.
    """

    items: List[DocumentOrFolder] = []

    def __init__(self, *items):
        for i in items:
            self.items.append(i)

    def add(self, docdict: dict) -> None:
        """Add an item to the collection.
        It wraps it in the correct class based on the Type parameter of the
        dict.

        Args:
            docdict: A dict representing a document or folder.
        """

        if docdict.get("Type", None) == "DocumentType":
            self.add_document(docdict)
        elif docdict.get("Type", None) == "CollectionType":
            self.add_folder(docdict)
        else:
            raise TypeError("Unsupported type: {_type}"
                            .format(_type=docdict.get("Type", None)))

    def add_document(self, docdict: dict) -> None:
        """Add a document to the collection

        Args:
            docdict: A dict respresenting a document.
        """

        self.items.append(Document(**docdict))

    def add_folder(self, dirdict: dict) -> None:
        """Add a document to the collection

        Args:
            dirdict: A dict respresenting a folder.
        """

        self.items.append(Folder(**dirdict))

    def parent(self, docorfolder: DocumentOrFolder) -> Folder:
        """Returns the paren of a Document or Folder

        Args:
            docorfolder: A document or folder to get the parent from

        Returns:
            The parent folder.
        """

        results = [i for i in self.items if i.ID == docorfolder.ID]
        if len(results) > 0 and isinstance(results[0], Folder):
            return results[0]
        else:
            raise FolderNotFound("Could not found the parent of the document.")

    def children(self, folder: Folder = None) -> List[DocumentOrFolder]:
        """Get all the childern from a folder

        Args:
            folder: A folder where to get the children from. If None, this will
                get the children in the root.
        Returns:
            a list of documents an folders.
        """

        if folder:
            return [i for i in self.items if i.Parent == folder.ID]
        else:
            return [i for i in self.items if i.Parent == ""]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, position: int) -> DocumentOrFolder:
        return self.items[position]
