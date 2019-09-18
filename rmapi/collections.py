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

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, position: int) -> DocOrFolder:
        return self.items[position]
