from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from typing import Optional
from pathlib import Path

from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings
from starlette.datastructures import Secret

from app.constants.gamemodes import GameMode

config = Config(".env")

SERVER_ADDR: str = config("SERVER_ADDR")
SERVER_PORT: Optional[int] = (
    int(v) if (v := config("SERVER_PORT", default=None)) else None
)

DB_DSN: DatabaseURL = config("DB_DSN", cast=DatabaseURL)
REDIS_DSN: str = config("REDIS_DSN")

OSU_API_KEY: Secret = config("OSU_API_KEY", cast=Secret)
DISCORD_SECRET: Secret = config("DISCORD_SECRET", cast=Secret)
GULAG_WEB_PATH: Path = config("GULAG_WEB_PATH", cast=Path)

DOMAIN: str = config("DOMAIN", default="cmyui.xyz")

MIRROR_SEARCH_ENDPOINT = os.environ["MIRROR_SEARCH_ENDPOINT"]
MIRROR_DOWNLOAD_ENDPOINT = os.environ["MIRROR_DOWNLOAD_ENDPOINT"]

COMMAND_PREFIX: str = config("COMMAND_PREFIX", default="!")

SEASONAL_BGS: CommaSeparatedStrings = config(
    "SEASONAL_BGS",
    cast=CommaSeparatedStrings,
    default=CommaSeparatedStrings(
        [
            "https://akatsuki.pw/static/flower.png",
            "https://i.cmyui.xyz/nrMT4V2RR3PR.jpeg",
        ],
    ),
)

MENU_ICON_URL: str = config(
    "MENU_ICON_URL",
    default="https://akatsuki.pw/static/logos/logo_ingame.png",
)
MENU_ONCLICK_URL: str = config("MENU_ONCLICK_URL", default="https://akatsuki.pw")

DATADOG_API_KEY: Secret = config("DATADOG_API_KEY", cast=Secret)
DATADOG_APP_KEY: Secret = config("DATADOG_APP_KEY", cast=Secret)

DEBUG: bool = config("DEBUG", cast=bool, default=False)
REDIRECT_OSU_URLS: bool = config("REDIRECT_OSU_URLS", cast=bool, default=True)

PP_CACHED_ACCURACIES: list[int] = [
    int(acc)
    for acc in config(
        "PP_CACHED_ACCS",
        cast=CommaSeparatedStrings,
    )
]
PP_CACHED_SCORES: list[int] = [
    int(score)
    for score in config(
        "PP_CACHED_SCORES",
        cast=CommaSeparatedStrings,
    )
]

DISALLOWED_NAMES: CommaSeparatedStrings = config(
    "DISALLOWED_NAMES",
    cast=CommaSeparatedStrings,
)
DISALLOWED_PASSWORDS: CommaSeparatedStrings = config(
    "DISALLOWED_PASSWORDS",
    cast=CommaSeparatedStrings,
)

DISCORD_AUDIT_LOG_WEBHOOK: str = config("DISCORD_AUDIT_LOG_WEBHOOK")
DISCORD_AUDIT_SCORE_WEBHOOK: str = config("DISCORD_AUDIT_SCORE_WEBHOOK")
DISCORD_AUDIT_NEW_RANKED_WEBHOOK: str = config("DISCORD_AUDIT_NEW_RANKED_WEBHOOK")
DISCORD_AUDIT_NEW_REQUEST_WEBHOOK: str = config("DISCORD_AUDIT_NEW_REQUEST_WEBHOOK")
DISCORD_AUDIT_HALLOFSHAME: str = config("DISCORD_AUDIT_HALLOFSHAME")
DISCORD_AUDIT_ANTICHEAT_LOG_WEBHOOK: str = config("DISCORD_AUDIT_ANTICHEAT_LOG_WEBHOOK")

STD_PP_CAP = int(os.environ["STD_PP_CAP"])
RX_PP_CAP = int(os.environ["RX_PP_CAP"])
AP_PP_CAP = int(os.environ["AP_PP_CAP"])

HITOBJ_LOW_PRESSTIMES_VALUE: int = config("HITOBJ_LOW_PRESSTIMES_VALUE", cast=int)
HITOBJ_LOW_PRESSTIMES_PRESSES: int = config("HITOBJ_LOW_PRESSTIMES_PRESSES", cast=int)

UNSTABLE_RATE_CAP: int = config("UNSTABLE_RATE_CAP", cast=int)

FRAME_TIME_CAP: int = config("FRAME_TIME_CAP", cast=int)
RX_FRAME_TIME_MP: float = config("RX_FRAME_TIME_MP", cast=float)

SNAPS_CAP: int = config("SNAPS_CAP", cast=int)

AUTOMATICALLY_REPORT_PROBLEMS: bool = config(
    "AUTOMATICALLY_REPORT_PROBLEMS",
    cast=bool,
    default=True,
)

# advanced dev settings

## WARNING: only touch this once you've
##          read through what it enables.
##          you could put your server at risk.

DEVELOPER_MODE: bool = config("DEVELOPER_MODE", cast=bool, default=False)


DS_TOKEN: str = config("DS_TOKEN", default="none")
SERVERID: int = config("SERVERID", default=0)

RANK_SSH: str = config("RANK_SSH", default="none")
RANK_SS: str = config("RANK_SS", default="none")
RANK_SH: str = config("RANK_SH", default="none")
RANK_S: str = config("RANK_S", default="none")
RANK_A: str = config("RANK_A", default="none")
RANK_B: str = config("RANK_B", default="none")
RANK_C: str = config("RANK_C", default="none")
RANK_D: str = config("RANK_D", default="none")
RANK_F: str = config("RANK_F", default="none")

## WARNING: only touch this if you know how
##          the migrations system works.
##          you'll regret it.
VERSION = "4.3.2"
