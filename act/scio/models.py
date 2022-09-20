from typing import Optional

from pydantic import BaseModel, StrictInt, StrictStr

from act.scio.tlp import TLP


class BaseDocument(BaseModel):
    """Document model"""

    filename: StrictStr
    uri: Optional[StrictStr]
    tlp: Optional[TLP]
    owner: Optional[StrictStr]
    store: bool = True


class Document(BaseDocument):
    """Document model"""

    content: StrictStr


class LookupResponse(BaseModel):
    """Response model for document search"""

    filename: StrictStr
    content_type: StrictStr


class SubmitResponse(BaseDocument):
    """Response model for document submit"""

    hexdigest: StrictStr
    count: StrictInt
    error: Optional[StrictStr]