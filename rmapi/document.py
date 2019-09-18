from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
from uuid import uuid4
import json
from typing import NoReturn
from requests import Response


class Document(object):
    """ Document represents a real object expected in most
    calls by the remarkable API"""

    ID = ""
    Version = 0
    Message = ""
    Succes = True
    BlobURLGet = ""
    BlobURLGetExpires = ""
    BlobURLPut = ""
    BlobURLPutExpires = ""
    ModifiedClient = ""
    Type = "DocumentType"
    VissibleName = ""
    CurrentPage = 1
    Bookmarked = False
    Parent = ""

    def __init__(self, **kwargs):
        kkeys = self.to_dict().keys()
        for k in kkeys:
            setattr(self, k, kwargs.get(k, getattr(self, k)))

    def to_dict(self):
        return {
            "ID": self.ID,
            "Version": self.Version,
            "Message": self.Message,
            "Succes": self.Succes,
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

    def __str__(self):
        return f"<rmapi.document.Document {self.ID}>"

    def __repr__(self):
        return self.__str__()


class ZipDocument(object):
    """
    Here is the content of an archive retried on the tablet as example:
    384327f5-133e-49c8-82ff-30aa19f3cfa40.content
    384327f5-133e-49c8-82ff-30aa19f3cfa40-metadata.json
    384327f5-133e-49c8-82ff-30aa19f3cfa40.rm
    384327f5-133e-49c8-82ff-30aa19f3cfa40.pagedata
    384327f5-133e-49c8-82ff-30aa19f3cfa40.thumbnails/0.jpg

    As the .zip file from remarkable is simply a normal .zip file
    containing specific file formats, this package is a helper to
    read and write zip files with the correct format expected by
    the tablet.

    In order to correctly use this package, you will have to understand
    the format of a Remarkable zip file, and the format of the files
    that it contains.

    You can find some help about the format at the following URL:
    https://remarkablewiki.com/tech/filesystem
    """
    content = {
        "ExtraMetadata": {
            "LastBrushColor": "Black",
            "LastBrushThicknessScale": "2",
            "LastColor": "Black",
            "LastEraserThicknessScale": "2",
            "LastEraserTool": "Eraser",
            "LastPen": "Ballpoint",
            "LastPenColor": "Black",
            "LastPenThicknessScale": "2",
            "LastPencil": "SharpPencil",
            "LastPencilColor": "Black",
            "LastPencilThicknessScale": "2",
            "LastTool": "SharpPencil",
            "ThicknessScale": "2"
        },
        "FileType": "",
        "FontName": "",
        "LastOpenedPage": 0,
        "LineHeight": -1,
        "Margins": 100,
        "Orientation": "portrait",
        "PageCount": 0,
        "Pages": [],
        "TextScale": 1,
        "Transform": {
            "M11": 1,
            "M12": 0,
            "M13": 0,
            "M21": 0,
            "M22": 1,
            "M23": 0,
            "M31": 0,
            "M32": 0,
            "M33": 1,
        }
    }
    metadata = {
        "deleted": False,
        "lastModified": "1568368808000",
        "metadatamodified": False,
        "modified": False,
        "parent": "",
        "pinned": False,
        "synced": True,
        "type": "DocumentType",
        "version": 1,
        "visibleName": "New Document"
    }

    pagedata = ""

    zipfile = BytesIO()
    pdf = None
    epub = None
    rm = []
    ID = None

    def __init__(self, ID=None, doc=None, file=None):
        if not ID:
            ID = str(uuid4())
        self.ID = ID
        if doc:
            ext = doc[-4:]
            if ext.endswith("pdf"):
                self.content["FileType"] = "pdf"
                self.pdf = BytesIO()
                with open(doc, 'rb') as fb:
                    self.pdf.write(fb.read())
            if ext.endswith("epub"):
                self.content["FileType"] = "epub"
                self.epub = BytesIO()
                with open(doc, 'rb') as fb:
                    self.epub.write(fb.read())
            elif ext.endswith("rm"):
                self.content["FileType"] = "notebook"
                self.pdf = BytesIO()
                with open(doc, 'rb') as fb:
                    self.rm.append(RmPage(page=BytesIO(doc.read())))

        if file:
            self.load(file)

    def __str__(self):
        return f"<rmapi.document.ZipDocument {self.ID}>"

    def __repr__(self):
        return self.__str__()

    def dump(self, file):
        """
        Dump the contents of ZipDocument back to a zip file
        """

        with ZipFile(f"{file}.zip", "w", ZIP_DEFLATED) as zf:
            if self.content:
                zf.writestr(f"{self.ID}.content",
                            json.dumps(self.content))
            if self.pagedata:
                zf.writestr(f"{self.ID}.pagedata",
                            self.pagedata.read())

            if self.pdf:
                zf.writestr(f"{self.ID}.pdf",
                            self.pdf.read())

            if self.epub:
                zf.writestr(f"{self.ID}.epub",
                            self.epub.read())

            for page in self.rm:

                zf.writestr(f"{self.ID}/{page.order}.rm",
                            page.page.read())

                zf.writestr(f"{self.ID}/{page.order}-metadata.json",
                            json.dumps(page.metadata))
                page.page.seek(0)
                zf.writestr(f"{self.ID}.thumbnails/{page.order}.jpg",
                            page.thumbnail.read())

    def load(self, file) -> NoReturn:
        """
        Fill in the defaults from the given ZIP
        """
        self.zipfile = BytesIO()
        self.zipfile.seek(0)
        if isinstance(file, str):
            with open(file, 'rb') as f:
                shutil.copyfileobj(f, self.zipfile)
        elif isinstance(file, BytesIO):
            self.zipfile = file
            self.zipfile.seek(0)
        else:
            raise Exception("Unsupported file type.")
        with ZipFile(self.zipfile, 'r') as zf:
            with zf.open(f"{self.ID}.content", 'r') as content:
                self.content = json.load(content)
            try:
                with zf.open(f"{self.ID}.metadata", 'r') as metadata:
                    self.metadata = json.load(metadata)
            except KeyError:
                pass
            try:
                with zf.open(f"{self.ID}.pagedata", 'r') as pagedata:
                    self.pagedata = BytesIO(pagedata.read())
            except KeyError:
                pass

            try:
                with zf.open(f"{self.ID}.pdf", 'r') as pdf:
                    self.pdf = BytesIO(pdf.read())
            except KeyError:
                pass

            try:
                with zf.open(f"{self.ID}.epub", 'r') as epub:
                    self.epub = BytesIO(epub.read())
            except KeyError:
                pass

            # Get the RM pages

            content = [x for x in zf.namelist()
                       if x.startswith(f"{self.ID}/") and x.endswith('.rm')]
            for p in content:
                pagenumber = p.replace(f"{self.ID}/", "").replace(".rm", "")
                pagenumber = int(pagenumber)
                page = BytesIO()
                thumbnail = BytesIO()
                with zf.open(p, 'r') as rm:
                    page = BytesIO(rm.read())
                    page.seek(0)
                with zf.open(p.replace(".rm", "-metadata.json"), 'r') as md:
                    metadata = json.load(md)
                thumbnail_name = p.replace(".rm", ".jpg")
                thumbnail_name = thumbnail_name.replace("/", ".thumbnails/")
                with zf.open(thumbnail_name, 'r') as tn:
                    thumbnail = BytesIO(tn.read())
                    thumbnail.seek(0)

                self.rm.append(RmPage(page, metadata, pagenumber, thumbnail,
                                      self.ID))

        self.zipfile.seek(0)


class RmPage(object):
    """A Remarkable Page"""
    def __init__(self, page, metadata=None, order=0, thumbnail=None, ID=None):
        self.page = page
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = {"layers": [{"name": "Layer 1"}]}

        self.order = order
        if thumbnail:
            self.thumbnail = thumbnail
        if ID:
            self.ID = ID
        else:
            self.ID = str(uuid4())

    def __str__(self):
        return f"<rmapi.document.RmPage {self.order} for {self.ID}>"

    def __repr__(self):
        return self.__str__()


def from_zip(ID: str, file: str) -> ZipDocument:
    """
    Return A ZipDocument from a zipfile.
    """
    return ZipDocument(ID, file=file)


def from_request_stream(ID: str, stream:  Response) -> ZipDocument:
    """
    Return a ZipDocument from a request stream containing a zipfile.
    """
    tmp = BytesIO()
    for chunk in stream.iter_content(chunk_size=8192):
        tmp.write(chunk)
    zd = ZipDocument(ID=ID)
    zd.load(tmp)
    return zd
