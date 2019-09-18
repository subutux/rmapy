from .document import Document
from .folder import Folder
from typing import NoReturn, TypeVar

DocOrFolder = TypeVar('DocumentOrFolder', Document, Folder)


class Collection(object):
    """
    A collection of meta items
    """
    items = []

    def __init__(self, *items):
        for i in items:
            self.items.append(i)

    def add(self, docdict: dict) -> NoReturn:
        if docdict.get("Type", None) == "DocumentType":
            return self.addDocument(docdict)
        elif docdict.get("Type", None) == "CollectionType":
            return self.addFolder(docdict)
        else:
            raise TypeError("Unsupported type: {_type}"
                            .format(_type=docdict.get("Type", None)))

    def addDocument(self, docdict: dict) -> NoReturn:
        self.items.append(Document(**docdict))

    def addFolder(self, dirdict: dict) -> NoReturn:
        self.items.append(Folder(**dirdict))

    def parent(self, docorfolder: DocOrFolder) -> Folder:
        """Returns the paren of a Document or Folder

        Args:
            docorfolder: A document or folder to get the parent from

        Returns:
            The parent folder.
        """

        results = [i for i in self.items if i.ID == docorfolder.ID]
        if len(results) > 0:
            return results[0]
        else:
            raise FolderNotFound("Could not found the parent of the document.")

    def children(self, folder: Folder = None) -> List[DocOrFolder]:
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

    def __getitem__(self, position: int) -> DocOrFolder:
        return self.items[position]
