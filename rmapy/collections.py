from .document import Document
from .folder import Folder
from typing import NoReturn, List, Union
from .exceptions import FolderNotFound
from .config import config_meta_path
from pathlib import Path

from yaml import BaseLoader
from yaml import load as yml_load
from yaml import dump as yml_dump

DocumentOrFolder = Union[Document, Folder]


class Collection(object):
    """A collection of meta items

    This is basically the content of the Remarkable Cloud.

    Attributes:
        items: A list containing the items.
    """

    def __init__(self, *items: List[DocumentOrFolder]):
        self.items: List[DocumentOrFolder] = []

        for i in items:
            self.items.append(i)

    def to_list(self) -> list:
        """ Return a list of the collection. """
        return [item.to_dict() for item in self.items]

    def load(self) -> None:
        """ Load Collection from storage """
        storage = []
        if Path.exists(config_meta_path):
            with open(config_meta_path, 'r') as config_file:
                storage = list(yml_load(config_file.read(), Loader=BaseLoader))

        for item in storage:
            self.add(item)

    def dump(self) -> None:
        """ Dump collection to storage"""
        with open(config_meta_path, 'w') as config_file:
            config_file.write(yml_dump(self.to_list()))

    def add(self, doc_dict: dict) -> None:
        """Add an item to the collection.
        It wraps it in the correct class based on the Type parameter of the
        dict.

        Args:
            doc_dict: A dict representing a document or folder.
        """

        if doc_dict.get("type", None) == "DocumentType":
            self.add_document(doc_dict)
        elif doc_dict.get("type", None) == "CollectionType":
            self.add_folder(doc_dict)
        else:
            raise TypeError("Unsupported type: {_type}"
                            .format(_type=doc_dict.get("type", None)))

    def add_document(self, doc_dict: dict) -> None:
        """Add a document to the collection

        Args:
            doc_dict: A dict representing a document.
        """

        self.items.append(Document(**doc_dict))

    def add_folder(self, dir_dict: dict) -> None:
        """Add a document to the collection

        Args:
            dir_dict: A dict representing a folder.
        """

        self.items.append(Folder(**dir_dict))

    def parent(self, doc_or_folder: DocumentOrFolder) -> Folder:
        """Returns the paren of a Document or Folder

        Args:
            doc_or_folder: A document or folder to get the parent from

        Returns:
            The parent folder.
        """

        results = [i for i in self.items if i.ID == doc_or_folder.ID]
        if len(results) > 0 and isinstance(results[0], Folder):
            return results[0]
        else:
            raise FolderNotFound("Could not found the parent of the document.")

    def children(self, folder: Folder = None) -> List[DocumentOrFolder]:
        """Get all the children from a folder

        Args:
            folder: A folder where to get the children from. If None, this will
                get the children in the root.
        Returns:
            a list of documents an folders.
        """

        if folder:
            return [i for i in self.items if i.parent == folder.ID]
        else:
            return [i for i in self.items if i.parent == ""]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, position: int) -> DocumentOrFolder:
        return self.items[position]
