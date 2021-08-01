import dataclasses
import datetime
import json
import typing as T
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List

from rmapy import utils


class FileType(Enum):
    CONTENT = ".content"
    METADATA = ".metadata"
    PAGEDATA = ".pagedata"
    PDF = ".pdf"
    LINK_FILE = ".metadata"

    @classmethod
    def get_type_from_file_name(cls, filename: str) -> T.Optional[FileType]:
        for file_type in list(FileType):
            if filename.endswith(file_type.value):
                return file_type

        return None


class DocumentType(Enum):
    Document = "DocumentType"
    Folder = "CollectionType"


@dataclass
class Locator():
    id: str

    @classmethod
    def generate_locator(cls) -> Locator:
        return cls(
            id=utils.generate_path()
        )


@dataclass  # type: ignore
class CloudFile(metaclass=ABCMeta):
    locator: Locator = dataclasses.field(
        default_factory=Locator.generate_locator, init=False)  # type: ignore

    @abstractmethod
    def to_data(self) -> bytes:
        pass

    @abstractmethod
    def size(self) -> int:
        pass

    @property
    @abstractmethod
    def file_ending(self) -> str:
        pass


CloudFileType = T.TypeVar("CloudFileType", bound=CloudFile)


def parse_from_file_type(type: T.Type[CloudFile], data: bytes) -> CloudFile:
    if type == Metadata:
        return Metadata.from_data(data)
    else:
        raise Exception(f"Parsing {type} has not yet been implemented")


def get_type_from_file_name(filename: str) -> T.Type[CloudFile]:
    if filename.endswith(Metadata.file_ending):
        return Metadata
    elif filename.endswith(PDF.file_ending):
        return PDF
    elif filename.endswith(Content.file_ending):
        return Content
    else:
        raise Exception(f"Could not determine file type for {filename}")


@dataclass
class PDF(CloudFile):

    file_ending = ".pdf"

    data: bytes

    def size(self) -> int:
        return len(self.data)

    def to_data(self) -> bytes:
        return self.data

    @classmethod
    def generate(cls, file_path: str) -> PDF:
        with open(file_path, "rb") as data:
            return PDF(
                data=data.read()
            )


@dataclass
class Metadata(CloudFile):
    file_ending = ".metadata"

    deleted: bool
    lastModified: int
    lastOpenedPage: int
    metadatamodified: bool
    modified: bool
    parent: str
    pinned: bool
    synced: bool
    type: DocumentType
    version: int
    visibleName: str

    def to_data(self) -> bytes:
        data = {
            "deleted": self.deleted,
            "lastModified": self.lastModified,
            "metadatamodified": self.metadatamodified,
            "modified": self.modified,
            "parent": self.parent,
            "pinned": self.pinned,
            "synced": self.synced,
            "type": self.type.value,
            "version": self.version,
            "visibleName": self.visibleName
        }

        if self.type == DocumentType.Document:
            data["lastOpenedPage"] = self.lastOpenedPage

        return json.dumps(data).encode()

    def size(self) -> int:
        return len(self.to_data())

    @classmethod
    def generate(cls, name: str, doc_type: DocumentType, parent: T.Optional[str] = None) -> Metadata:
        return cls(
            deleted=False,
            lastModified=int(datetime.datetime.now().timestamp()),
            lastOpenedPage=0,
            metadatamodified=False,
            modified=False,
            parent=parent or "",
            pinned=False,
            synced=False,
            type=doc_type,
            version=0,
            visibleName=name
        )

    @classmethod
    def from_data(cls, data: bytes) -> Metadata:
        result = json.loads(data.decode())
        return Metadata(
            **result
        )


@dataclass
class Content(CloudFile):
    file_ending = ".content"

    def size(self) -> int:
        return len(self.to_data())

    @classmethod
    def generate(cls) -> Content:
        return cls()

    def to_data(self) -> bytes:
        return json.dumps({}).encode()


@dataclass
class LinkEntry:

    # Link entry line parts
    cloud_hash: str
    first_int: int  # seems to be 0 most of the time?
    file_name: str
    second_int: int  # seems to be 0 most of the time?
    size: int  # Size in bytes

    entry_type: T.Type[CloudFile]

    def to_line(self) -> str:
        return f"{self.cloud_hash}:{self.first_int}:{self.file_name}:{self.second_int}:{self.size}"

    @classmethod
    def from_line(cls, line: str) -> 'LinkEntry':
        entries = line.split(":")
        file_name = entries[2]
        entry_type = get_type_from_file_name(file_name)

        if entry_type is None:
            raise Exception(f"Could not classify link entry {line}")

        return cls(
            cloud_hash=entries[0],
            first_int=int(entries[1]),
            file_name=file_name,
            second_int=int(entries[3]),
            size=int(entries[4]),
            entry_type=entry_type
        )


@dataclass  # type: ignore
class LinkFile(CloudFile):
    version: int
    entries: List[LinkEntry]

    file_ending = ""

    def size(self) -> int:
        return len(self.to_data())

    def to_data(self) -> bytes:
        """ Produces a link doc for uploading to cloud """
        data = f"{self.version}\n"
        for entry in self.entries:
            data += f"{entry.to_line()}\n"
        return data.encode()

    @classmethod
    def from_data(cls, data: bytes) -> 'LinkFile':
        lines = data.decode().split('\n')

        version = int(lines[0])

        link_entries: List[LinkEntry] = []
        for line in lines[1:]:
            if line != "":
                link_entries.append(LinkEntry.from_line(line))

        return cls(
            version=version,
            entries=link_entries
        )


@dataclass
class RootEntry:
    link_file_hash: str
    first_int: int  # This is always 80000000
    file_uuid: str
    number_of_files_in_link: int
    second_int: int  # This seems to be 0

    def to_line(self) -> str:
        return f"{self.link_file_hash}:{self.first_int}:{self.file_uuid}:{self.number_of_files_in_link}:{self.second_int}"

    @classmethod
    def from_line(cls, line: str) -> 'RootEntry':
        entries = line.split(":")
        return cls(
            link_file_hash=entries[0],
            first_int=int(entries[1]),
            file_uuid=entries[2],
            number_of_files_in_link=int(entries[3]),
            second_int=int(entries[4])
        )


@dataclass  # type: ignore
class RootData(CloudFile):
    version: int
    entries: List[RootEntry]

    file_ending = ""

    def size(self) -> int:
        return len(self.to_data())

    def get_root_entry_for_file_uuid(self, file_uuid: str) -> T.Optional[RootEntry]:
        for entry in self.entries:
            if entry.file_uuid == file_uuid:
                return entry
        return None

    def to_data(self) -> bytes:
        data = f"{self.version}\n"
        for entry in self.entries:
            data += f"{entry.to_line()}\n"
        return data.encode()

    @classmethod
    def from_data(cls, data: bytes) -> RootData:
        lines = data.decode().split("\n")
        version = int(lines[0])
        entries = [RootEntry.from_line(line) for line in lines[1:]]
        return cls(
            version=version,
            entries=entries
        )
