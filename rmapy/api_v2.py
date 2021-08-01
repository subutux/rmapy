import base64
import dataclasses
import hashlib
import json
import typing as T
import uuid
from dataclasses import dataclass
from typing import Dict

import requests

from rmapy.const import (DEVICE, DEVICE_TOKEN_URL, SERVICE_MGR_URL, USER_AGENT,
                         USER_TOKEN_URL)
from rmapy.execptions import AuthError

DeviceToken = str
UserToken = str


@dataclass
class Token:
    device_token: str
    user_token: T.Optional[str]

    def to_storage_dict(self) -> T.Dict[str, T.Optional[str]]:
        return {
            'devicetoken': self.device_token,
            'usertoken': self.user_token
        }


class API:

    def __init__(self, token: T.Optional[Token] = None) -> None:
        self.__token: T.Optional[Token] = None
        if token is not None:
            self.__token = token
            self.__configure_urls()

    def __configure_urls(self):
        self.__api_url = self.__get_base_url()
        self.__download_url = self.__api_url + "/signed-urls/downloads"
        self.__upload_url = self.__api_url + "/signed-urls/uploads"
        self.__sync_complete = self.__api_url + "/sync-complete"

    def __assert_auth(self) -> None:
        if self.__token is None or self.__token.device_token is None:
            raise AuthError(
                "Could not find device token. Did you call register_token with a one-time use code?")
        if self.__token.user_token is None:
            raise AuthError(
                "Could not find user token. Did you call renew_token?")

    def __get_base_url(self) -> str:
        """ Query the service url to get the latest document storage url """
        response = self.request(
            "GET",
            SERVICE_MGR_URL + "/service/json/1/blob-storage?environment=production&apiVer=1"
        )
        response.raise_for_status()
        base_url = response.json()["Host"]
        return base_url.rstrip("/") + "/"

    def is_auth(self) -> bool:
        if self.__token is None or self.__token.device_token is None or self.__token.user_token is None:
            return False
        return True

    def send_complete_sync(self) -> requests.Response:
        self.__assert_auth()
        res = self.request(
            "POST",
            self.__sync_complete,
        )
        res.raise_for_status()
        return res

    def register_device(self, code: str) -> Token:
        uuid = str(uuid.uuid4())
        body = {
            "code": code,
            "deviceDesc": DEVICE,
            "deviceID": uuid,
        }
        response = self.request(
            "POST", DEVICE_TOKEN_URL, data=json.dumps(body))
        if response.ok:
            self.__token = Token(device_token=response.text, user_token=None)
            return Token(**dataclasses.asdict(self.__token))
        else:
            raise AuthError("Can't register device")

    def renew_token(self) -> Token:
        if self.__token is None or self.__token.device_token is None:
            raise AuthError(
                "Please register a device using a one time token first.")

        response = self.request("POST", USER_TOKEN_URL, headers={
            "Authorization": f"Bearer {self.__token.device_token}"
        })
        if response.ok:
            self.__token.user_token = response.text
            self.__configure_urls()
            return Token(**dataclasses.asdict(self.__token))
        else:
            raise AuthError(f"Can't renew token: {response.status_code}")

    def request(self,
                method: str,
                url: str,
                data=None,
                headers=None) -> requests.Response:

        if headers is None:
            headers = {}

        _headers = {
            "User-Agent": USER_AGENT,
        }
        _headers.update(headers)

        if self.__token is not None and self.__token.user_token is not None:
            _headers["Authorization"] = f"Bearer {self.__token.user_token}"

        return requests.request(method, url, data=data, headers=_headers)

    def query_api(self, request: Dict[str, str]) -> requests.Response:
        self.__assert_auth()
        if "http_method" not in request:
            raise Exception(f"Malformed request for {request}")

        response = None
        if request['http_method'] == "PUT":
            response = requests.request(
                "POST", self.__upload_url, data=json.dumps(request))
        elif request['http_method'] == "GET":
            response = requests.request(
                "POST", self.__download_url, data=json.dumps(request))
        else:
            raise Exception(f"Could not identify http method for {request}")

        response.raise_for_status()
        return response

    def push_to_storage(self, url: str, data: bytes, generation: T.Optional[int]) -> None:
        self.__assert_auth()
        headers = {
            'Content-MD5': base64.b64encode(hashlib.md5(data).digest()).decode()
        }
        if generation:
            headers['x-goog-if-generation-match'] = str(generation)

        requests.put(url, data=data, headers=headers).raise_for_status()

    def get_from_storage(self, url: str) -> requests.Response:
        self.__assert_auth()
        response = requests.get(url)
        return response

    def put(self,
            relative_path: str,
            data: bytes,
            generation: T.Optional[int] = None,
            parent_hash: T.Optional[str] = None) -> None:
        """ Put request """
        self.__assert_auth()
        request: Dict[str, str] = {
            'http_method': "PUT",
            'relative_path': relative_path
        }
        if parent_hash is not None and parent_hash != "":
            request['parent_hash'] = parent_hash

        if generation is not None:
            request['generation'] = str(generation)

        resp = self.query_api(request).json()
        data_url = resp['url']
        self.push_to_storage(data_url, data, generation)

    def get(self, relative_path: str) -> T.Tuple[bytes, T.Optional[int]]:
        """ Get request """
        self.__assert_auth()
        request = {
            'http_method': "GET",
            'relative_path': relative_path
        }
        response = self.query_api(request)
        data_response = self.get_from_storage(response.json()['url'])
        data = data_response.content
        generation_str = data_response.headers.get('generation')
        generation = None
        if generation_str is not None:
            generation = int(generation_str)
        return data, generation
