from __future__ import annotations
from typing import Literal, TypedDict



class ServerExistence(TypedDict):
    exist: bool
    openTime: int
    closeTime: int

class Existence(TypedDict):
    CN: ServerExistence
    JP: ServerExistence
    KR: ServerExistence
    US: ServerExistence

class Item(TypedDict):
    alias: list[str]
    existence: Existence
    groupID: str
    itemId: str
    itemType: str
    name: str
    name_i18n: dict[str, str]
    pron: list[str]
    rarity: int
    sortId: int
    spriteCoord: list[int]


class Bounds(TypedDict):
    lower: int
    upper: int
    exceptions: list[int]

class DropInfo(TypedDict):
    bounds: Bounds
    dropType: str
    itemId: str

class Stage(TypedDict):
    apCost: int
    code: str
    code_i18n: dict[str, str]
    dropInfos: list[DropInfo]
    existence: Existence
    minClearTime: int
    recognitionOnly: list[str]
    stageId: str
    stageType: Literal['MAIN', 'SUB', 'ACTIVITY', 'DAILY']
    zoneId: str

class ArkDrop(TypedDict):
    dropType: Literal['REGULAR_DROP', 'NORMAL_DROP', 'SPECIAL_DROP', 'EXTRA_DROP', 'FURNITURE']
    itemId: str
    quantity: int

class SingleReportRequest(TypedDict):
    drops: list[ArkDrop]
    server: str
    source: str
    stageId: str
    version: str