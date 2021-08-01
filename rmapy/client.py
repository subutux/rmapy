import dataclasses
import datetime
import typing as T
from typing import List

from rmapy import api_v2, models, utils
from rmapy.config import dump, load


class ClientV2:

    def __init__(self, token: T.Optional[api_v2.Token] = None) -> None:
        config = load()
        if "devicetoken" in config or "usertoken" in config:
            token = api_v2.Token(
                device_token=config['devicetoken'],
                user_token=config['usertoken']
            )

        self.__api = api_v2.API(token)
        self.__root = Root.get_current_root(self.__api)

    def register_device(self, code: str) -> None:
        token = self.__api.register_device(code)
        dump(token.to_storage_dict())

    def renew_token(self) -> None:
        token = self.__api.renew_token()
        dump(token.to_storage_dict())

    def is_auth(self) -> bool:
        return self.__api.is_auth()

    def get_meta_items(self) -> T.List[models.RootEntry]:
        # This should return a list of metadata items...
        return self.__root.get_entries()

    def create_folder(self, folder_name: str, parent: T.Optional[str]) -> None:
        self.__root = Root.get_current_root(self.__api)
        doc_id = utils.generate_doc_id()

        metadata = models.Metadata.generate(
            folder_name, models.DocumentType.Folder, parent)
        content = models.Content.generate()

        content_link_entry = self.__root.__upload_link_entry(doc_id, content)
        metadata_link_entry = self.__root.__upload_link_entry(doc_id, metadata)
        link_file = self.__root.__upload_link_file(
            [content_link_entry, metadata_link_entry])

        self.__root.add_entry(link_file, doc_id)
        self.__root.commit_root()
        self.__root.complete_sync()

    def create_document(self, name: str, file_path: str, parent: T.Optional[str] = None) -> None:
        self.__root = Root.get_current_root(self.__api)

        doc_id = utils.generate_doc_id()

        metadata = models.Metadata.generate(
            name, models.DocumentType.Document, parent)
        content = models.Content.generate()
        pdf = models.PDF.generate(file_path)

        content_link_entry = self.__root.__upload_link_entry(doc_id, content)
        metadata_link_entry = self.__root.__upload_link_entry(doc_id, metadata)
        pdf_link_entry = self.__root.__upload_link_entry(doc_id, pdf)

        link_file = self.__root.__upload_link_file(
            [content_link_entry, metadata_link_entry, pdf_link_entry])

        self.__root.add_entry(link_file, doc_id)
        self.__root.commit_root()
        self.__root.complete_sync()

    def get_document(self, doc_id: str) -> T.Optional[models.Metadata]:
        return self.__root.get_metadata_for_file_uuid(doc_id)

    def move_file_to_trash(self, doc_id: str) -> None:
        # lookup doc_id hash in the root
        self.move_file(doc_id, "trash")

    def move_file(self, src_doc_id: str, destination_folder: str) -> None:
        # lookup doc_id hash in the root
        self.__root = Root.get_current_root(self.__api)

        link_file = self.__root.get_link_file_for_file_uuid(src_doc_id)
        if link_file is None:
            raise Exception(f"Could not link file for {src_doc_id}")

        metadata = self.__root.get_metadata_for_file_uuid(src_doc_id)
        if metadata is None:
            raise Exception(
                f"Could not find metadata for {src_doc_id} in {link_file}")

        metadata.parent = destination_folder
        metadata.lastModified = int(datetime.datetime.now().timestamp())
        metadata.metadatamodified = True
        # Create a new locator for this copied metadata
        metadata.locator = models.Locator.generate_locator()

        metadata_link_entry = self.__root.__upload_link_entry(
            src_doc_id, metadata, parent_locator=link_file.locator)

        new_link_file = self.__root.__upload_link_file([metadata_link_entry] + [
            entry for entry in link_file.entries if entry.entry_type != models.Metadata
        ])

        self.__root.remove_entry(src_doc_id)
        self.__root.add_entry(new_link_file, src_doc_id)
        self.__root.commit_root()
        self.__root.complete_sync()


class Root:

    def __init__(self, api: api_v2.API, root_data: models.RootData, generation: int):
        self.__root_data = root_data
        self.__api = api
        self.__generation = generation

    @classmethod
    def get_root(cls, api: api_v2.API) -> T.Tuple[models.RootData, int]:
        root_hash_bytes, _ = api.get("root")
        root_hash = root_hash_bytes.decode()
        root_data, generation = api.get(root_hash)
        if generation is None:
            raise Exception("Could not determine generation of root")
        return models.RootData.from_data(root_data), generation

    @classmethod
    def get_current_root(cls, api: api_v2.API) -> Root:
        """ Return the current root """
        root_data, generation = Root.get_root(api)
        return Root(api, root_data, generation)

    def get_entries(self) -> T.List[models.RootEntry]:
        return [
            models.RootEntry(**dataclasses.asdict(entry))
            for entry in self.__root_data.entries
        ]

    def add_entry(self, link_file: models.LinkFile, file_uuid: str) -> None:
        """ Add an entry to this root object."""
        if not self.__root_data.get_root_entry_for_file_uuid(file_uuid) is None:
            self.__root_data.entries.append(models.RootEntry(
                link_file_hash=link_file.locator.id,
                first_int=80000000,
                file_uuid=file_uuid,
                number_of_files_in_link=len(link_file.entries),
                second_int=0
            ))
        else:
            raise Exception(f"RootEntry for {file_uuid} already exists")

    def remove_entry(self, file_uuid: str) -> None:
        if self.__root_data.get_root_entry_for_file_uuid(file_uuid) is None:
            self.__root_data.entries = [
                models.RootEntry(**dataclasses.asdict(entry)) for entry in self.__root_data.entries
                if entry.file_uuid != file_uuid
            ]
        else:
            raise Exception(f"RootEntry for {file_uuid} already exists")

    def __upload_link_entry(self,
                            file_uuid: str,
                            data: models.CloudFile,
                            parent_locator: T.Optional[models.Locator] = None) -> models.LinkEntry:
        """ Take a file as bytes, and return the cloud id that is identified by it """
        self.__api.put(data.locator.id,
                       data.to_data(),
                       generation=None,
                       parent_hash=parent_locator.id if parent_locator is not None else None)

        link_entry = models.LinkEntry(
            cloud_hash=data.locator.id,
            first_int=0,
            file_name=f"{file_uuid}{data.file_ending}",
            second_int=0,
            size=data.size(),
            entry_type=data.__class__
        )
        return link_entry

    def __upload_link_file(self, entries: List[models.LinkEntry]) -> models.LinkFile:
        link_file = models.LinkFile(
            version=3,
            entries=[models.LinkEntry(**dataclasses.asdict(entry))
                     for entry in entries]
        )
        data = link_file.to_data()
        self.__api.put(link_file.locator.id, data)
        return link_file

    def get_metadata_for_file_uuid(self, file_uuid: str) -> T.Optional[models.Metadata]:
        link_file = self.get_link_file_for_file_uuid(file_uuid)
        if link_file is None:
            return None

        metadata = None
        for entry in link_file.entries:
            if entry.entry_type == models.FileType.METADATA:
                metadata = self.get_link_entry_file_data(entry)
                break

        if metadata is not None:
            assert isinstance(metadata, models.Metadata)

        return metadata

    def get_link_file_for_file_uuid(self, file_uuid: str) -> T.Optional[models.LinkFile]:
        root_entry = self.__root_data.get_root_entry_for_file_uuid(file_uuid)
        if not root_entry:
            return None
        link_data, _ = self.__api.get(root_entry.link_file_hash)
        return models.LinkFile.from_data(link_data)

    def get_link_entry_file_data(self, link_entry: models.LinkEntry) -> T.Optional[models.CloudFile]:
        data, _ = self.__api.get(link_entry.cloud_hash)
        return models.parse_from_file_type(link_entry.entry_type, data)

    def commit_root(self) -> str:
        """ Commit root to the remarkable """
        generated_hash = utils.generate_path()
        data = self.__root_data.to_data()
        self.__api.put(generated_hash, data, generation=None)
        self.__api.put("root", generated_hash.encode(),
                       generation=self.__generation)
        return generated_hash

    def complete_sync(self) -> str:
        """ Send the complete sync message. Return the id response. """
        res = self.__api.send_complete_sync()
        res_json = res.json()
        if 'id' in res_json:
            return res_json['id']
        return ""


# upload_pdf_to_root: Done upload_document
# upload_pdf_to_folder: Done upload_document
# create_folder: Done create_folder
# remove document: Done remove_document
# remove folder: Done, same as remove_document
# empty trash:
# open client without changes
# open client with remove
# generally change metadata
