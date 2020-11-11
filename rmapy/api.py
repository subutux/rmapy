import requests
from logging import getLogger
from datetime import datetime
from typing import Union, Optional
from uuid import uuid4
from .collections import Collection
from .config import load, dump
from .document import Document, ZipDocument, from_request_stream
from .folder import Folder
from .exceptions import (
    AuthError,
    DocumentNotFound,
    ApiError,
    UnsupportedTypeError,)
from .const import (RFC3339Nano,
                    USER_AGENT,
                    BASE_URL,
                    DEVICE_TOKEN_URL,
                    USER_TOKEN_URL,
                    DEVICE,)

log = getLogger("rmapy")
DocumentOrFolder = Union[Document, Folder]


class Client(object):
    """API Client for Remarkable Cloud

    This allows you to authenticate & communicate with the Remarkable Cloud
    and does all the heavy lifting for you.
    """

    token_set = {
        "devicetoken": "",
        "usertoken": ""
    }

    def __init__(self):
        config = load()
        if "devicetoken" in config:
            self.token_set["devicetoken"] = config["devicetoken"]
        if "usertoken" in config:
            self.token_set["usertoken"] = config["usertoken"]

    def request(self, method: str, path: str,
                data=None,
                body=None, headers=None,
                params=None, stream=False) -> requests.Response:
        """Creates a request against the Remarkable Cloud API

        This function automatically fills in the blanks of base
        url & authentication.

        Args:
            method: The request method.
            path: complete url or path to request.
            data: raw data to put/post/...
            body: the body to request with. This will be converted to json.
            headers: a dict of additional headers to add to the request.
            params: Query params to append to the request.
            stream: Should the response be a stream?
        Returns:
            A Response instance containing most likely the response from
            the server.
        """

        if headers is None:
            headers = {}
        if not path.startswith("http"):
            if not path.startswith('/'):
                path = '/' + path
            url = f"{BASE_URL}{path}"
        else:
            url = path

        _headers = {
            "user-agent": USER_AGENT,
        }

        if self.token_set["usertoken"]:
            token = self.token_set["usertoken"]
            _headers["Authorization"] = f"Bearer {token}"
        for k in headers.keys():
            _headers[k] = headers[k]
        log.debug(url, _headers)
        r = requests.request(method, url,
                             json=body,
                             data=data,
                             headers=_headers,
                             params=params,
                             stream=stream)
        return r

    def register_device(self, code: str):
        """Registers a device on the Remarkable Cloud.

        This uses a unique code the user gets from
        https://my.remarkable.com/connect/remarkable to register a new device
        or client to be able to execute api calls.

        Args:
            code: A unique One time code the user can get
                at https://my.remarkable.com/connect/remarkable .
        Returns:
            True
        Raises:
            AuthError: We didn't recieved an devicetoken from the Remarkable
                Cloud.
        """

        uuid = str(uuid4())
        body = {
            "code": code,
            "deviceDesc": DEVICE,
            "deviceID": uuid,

        }
        response = self.request("POST", DEVICE_TOKEN_URL, body=body)
        if response.ok:
            self.token_set["devicetoken"] = response.text
            dump(self.token_set)
            return True
        else:
            raise AuthError("Can't register device")

    def renew_token(self):
        """Fetches a new user_token.

        This is the second step of the authentication of the Remarkable Cloud.
        Before each new session, you should fetch a new user token.
        User tokens have an unknown expiration date.

        Returns:
            True

        Raises:
            AuthError: An error occurred while renewing the user token.
        """

        if not self.token_set["devicetoken"]:
            raise AuthError("Please register a device first")
        token = self.token_set["devicetoken"]
        response = self.request("POST", USER_TOKEN_URL, None, headers={
                "Authorization": f"Bearer {token}"
            })
        if response.ok:
            self.token_set["usertoken"] = response.text
            dump(self.token_set)
            return True
        else:
            raise AuthError("Can't renew token: {e}".format(
                e=response.status_code))

    def is_auth(self) -> bool:
        """Is the client authenticated

        Returns:
            bool: True if the client is authenticated
        """

        if self.token_set["devicetoken"] and self.token_set["usertoken"]:
            return True
        else:
            return False

    def get_meta_items(self) -> Collection:
        """Returns a new collection from meta items.

        It fetches all meta items from the Remarkable Cloud and stores them
        in a collection, wrapping them in the correct class.

        Returns:
            Collection: a collection of Documents & Folders from the Remarkable
                Cloud
        """

        response = self.request("GET", "/document-storage/json/2/docs")
        collection = Collection()
        log.debug(response.text)
        for item in response.json():
            collection.add(item)

        return collection

    def get_doc(self, _id: str) -> Optional[DocumentOrFolder]:
        """Get a meta item by ID

        Fetch a meta item from the Remarkable Cloud by ID.

        Args:
            _id: The id of the meta item.

        Returns:
            A Document or Folder instance of the requested ID.
        Raises:
            DocumentNotFound: When a document cannot be found.
        """

        log.debug(f"GETTING DOC {_id}")
        response = self.request("GET", "/document-storage/json/2/docs",
                                params={
                                    "doc": _id,
                                    "withBlob": True
                                })
        log.debug(response.url)
        data_response = response.json()
        log.debug(data_response)

        if len(data_response) > 0:
            if data_response[0]["Type"] == "CollectionType":
                return Folder(**data_response[0])
            elif data_response[0]["Type"] == "DocumentType":
                return Document(**data_response[0])
        else:
            raise DocumentNotFound(f"Could not find document {_id}")
        return None

    def download(self, document: Document) -> ZipDocument:
        """Download a ZipDocument

        This will download a raw document from the Remarkable Cloud containing
        the real document. See the documentation for ZipDocument for more
        information.

        Args:
            document: A Document instance we should download

        Returns:
            A ZipDocument instance, containing the raw data files from a
            document.
        """

        if not document.BlobURLGet:
            doc = self.get_doc(document.ID)
            if isinstance(doc, Document):
                document = doc
            else:
                raise UnsupportedTypeError(
                    "We expected a document, got {type}"
                    .format(type=type(doc)))
        log.debug("BLOB", document.BlobURLGet)
        r = self.request("GET", document.BlobURLGet, stream=True)
        return from_request_stream(document.ID, r)

    def delete(self, doc: DocumentOrFolder):
        """Delete a document from the cloud.

        Args:
            doc: A Document or folder to delete.
        Raises:
            ApiError: an error occurred while uploading the document.
        """

        response = self.request("PUT", "/document-storage/json/2/delete",
                                body=[{
                                    "ID": doc.ID,
                                    "Version": doc.Version
                                }])

        return self.check_response(response)

    def upload(self, zip_doc: ZipDocument, to: Folder = Folder(ID="")):
        """Upload a document to the cloud.

        Add a new document to the Remarkable Cloud.

        Args:
            zip_doc: A ZipDocument instance containing the data of a Document.
            to: the parent of the document. (Default root)
        Raises:
            ApiError: an error occurred while uploading the document.

        """

        blob_url_put = self._upload_request(zip_doc)
        zip_doc.dump(zip_doc.zipfile)
        response = self.request("PUT", blob_url_put, data=zip_doc.zipfile.read())
        # Reset seek
        zip_doc.zipfile.seek(0)
        if response.ok:
            doc = Document(**zip_doc.metadata)
            doc.ID = zip_doc.ID
            doc.Parent = to.ID
            return self.update_metadata(doc)
        else:
            raise ApiError("an error occured while uploading the document.",
                           response=response)

    def update_metadata(self, docorfolder: DocumentOrFolder):
        """Send an update of the current metadata of a meta object

        Update the meta item.

        Args:
            docorfolder: A document or folder to update the meta information
                from.
        """

        req = docorfolder.to_dict()
        req["Version"] = self.get_current_version(docorfolder) + 1
        req["ModifiedClient"] = datetime.utcnow().strftime(RFC3339Nano)
        res = self.request("PUT",
                           "/document-storage/json/2/upload/update-status",
                           body=[req])

        return self.check_response(res)

    def get_current_version(self, docorfolder: DocumentOrFolder) -> int:
        """Get the latest version info from a Document or Folder

        This fetches the latest meta information from the Remarkable Cloud
        and returns the version information.

        Args:
            docorfolder: A Document or Folder instance.
        Returns:
            the version information.
        Raises:
            DocumentNotFound: cannot find the requested Document or Folder.
            ApiError: An error occurred while processing the request.
        """

        try:
            d = self.get_doc(docorfolder.ID)
        except DocumentNotFound:
            return 0
        if not d:
            return 0
        return int(d.Version)

    def _upload_request(self, zip_doc: ZipDocument) -> str:
        zip_file, req = zip_doc.create_request()
        res = self.request("PUT", "/document-storage/json/2/upload/request",
                           body=[req])
        if not res.ok:
            raise ApiError(
                     f"upload request failed with status {res.status_code}",
                     response=res)
        response = res.json()
        if len(response) > 0:
            dest = response[0].get("BlobURLPut", None)
            if dest:
                return dest
            else:
                raise ApiError(
                    "Cannot create a folder. because BlobURLPut is not set",
                    response=res)

    def create_folder(self, folder: Folder):
        """Create a new folder meta object.

        This needs to be done in 3 steps:

        #. Create an upload request for a new CollectionType meta object.
        #. Upload a zipfile with a *.content file containing an empty object.
        #. Update the meta object with the new name.

        Args:
            folder: A folder instance.
        Returns:
            True if the folder is created.
        """

        zip_folder, req = folder.create_request()
        res = self.request("PUT", "/document-storage/json/2/upload/request",
                           body=[req])
        if not res.ok:
            raise ApiError(
                     f"upload request failed with status {res.status_code}",
                     response=res)
        response = res.json()
        if len(response) > 0:
            dest = response[0].get("BlobURLPut", None)
            if dest:
                res = self.request("PUT", dest, data=zip_folder.read())
            else:
                raise ApiError(
                    "Cannot create a folder. because BlobURLPut is not set",
                    response=res)
        if res.ok:
            self.update_metadata(folder)
        return True

    @staticmethod
    def check_response(response: requests.Response):
        """Check the response from an API Call

        Does some sanity checking on the Response

        Args:
            response: A API Response

        Returns:
            True if the response looks ok

        Raises:
            ApiError: When the response contains an error
        """

        if response.ok:
            if len(response.json()) > 0:
                if response.json()[0]["Success"]:
                    return True
                else:
                    log.error("Got A non success response")
                    msg = response.json()[0]["Message"]
                    log.error(msg)
                    raise ApiError(f"{msg}",
                                   response=response)
            else:
                log.error("Got An empty response")
                raise ApiError("Got An empty response",
                               response=response)
        else:
            log.error(f"Got An invalid HTTP Response: {response.status_code}")
            raise ApiError(
                f"Got An invalid HTTP Response: {response.status_code}",
                response=response)
