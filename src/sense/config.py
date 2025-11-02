"""Application configuration."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    environment: str = os.getenv("SENSE_ENV", "dev")

    # Database
    @property
    def knowledgec_db_path(self) -> Path:
        """Get database path based on environment."""
        if self.environment == "prod":
            # Production: use real macOS KnowledgeC database
            return Path.home() / "Library" / "Application Support" / "Knowledge" / "knowledgeC.db"
        else:
            # Development: use synced copy in data/ directory
            return Path(__file__).parent.parent.parent / "data" / "knowledgeC.db"

    # Cache
    cache_ttl_seconds: int = 60

    # Pagination
    default_page_size: int = 100
    max_page_size: int = 1000

    # Date range limits
    max_date_range_days: int = 7

    # Focus sessions
    focus_session_gap_minutes: float = 5.0

    # Interruptions
    max_interruption_seconds: int = 300  # 5 minutes

    # Filters
    global_blocked_domains: list[str] = [
        "500px",
        "aa.com.tr",
        "abercrombie",
        "akamaihd",
        "amazon",
        "archive.is",
        "archive.li",
        "artstation",
        "audio-ice1.ibiblio.org",
        "awwni",
        "bandcamp",
        "bandcamp.com",
        "bellinghamherald.com",
        "bestbuy.com",
        "bnd.com",
        "charlotteobserver.com",
        "costco",
        "dailymotion",
        "deviantart",
        "diffchecker.com",
        "discord",
        "discordapp",
        "dropbox",
        "e621",
        "eastbay.com",
        "elnuevoherald.com",
        "erome",
        "eroshare",
        "eroshare.com",
        "fbcdn",
        "flickr",
        "flkeysnews.com",
        "footlocker",
        "fresnobee.com",
        "furaffinity",
        "futhead",
        "gamestop.com",
        "gfycat",
        "gifsound",
        "gifsoup",
        "giphy",
        "gospelherald.com",
        "groupon",
        "gunprime.com",
        "gyazo",
        "gyazo.com",
        "herald.com",
        "heraldonline.com",
        "heraldsun.com",
        "idahostatesman.com",
        "imagefap",
        "imageshack",
        "imgflip.com",
        "imgur.com",
        "instagram",
        "islandpacket.com",
        "itunes.apple.com",
        "kansas.com",
        "kansascity.com",
        "karmadecay",
        "kentucky.com",
        "kym-cdn",
        "ledger-enquirer.com",
        "lethbridgeherald.com",
        "linksynergy.com",
        "listen.noagendastream.com",
        "liveleak",
        "livememe",
        "lmgtfy",
        "m.gamestop.com",
        "macon.com",
        "magaimg",
        "magaimg.net",
        "mcclatchydc.com",
        "mega.nz",
        "memegenerator",
        "miamiherald.com",
        "minus",
        "modbee.com",
        "morejpegmyrtlebeachonline.com",
        "newsobserver.com",
        "nhk.or.jp",
        "nocookie",
        "pcpartpicker",
        "pcrichard.com",
        "photobucket",
        "pinimg",
        "pixiv",
        "pornhub",
        "pornhub.com",
        "prntscr",
        "puu",
        "qkme",
        "quickmeme",
        "quotev.com",
        "radd",
        "redd",
        "reddit",
        "reddit-stream",
        "redditlog",
        "redditmedia",
        "reddituploads",
        "redtube",
        "roanoke.com",
        "sacbee.com",
        "sanluisobispo.com",
        "sli.mg",
        "soundcloud.com",
        "soundgasm",
        "spankbang",
        "spotify",
        "spotify.com",
        "spotrac.com",
        "star-telegram.com",
        "staticflickr",
        "steamcommunity",
        "store.hp.com",
        "store.playstation.com",
        "strawpoll",
        "strawpoll.me",
        "streamable",
        "streamable.com",
        "sunherald.com",
        "taobao.com",
        "themalaymailonline.com",
        "thenewstribune.com",
        "theolympian.com",
        "thestate.com",
        "ticketmaster",
        "timeanddate.com",
        "tinypic",
        "tri-cityherald.com",
        "tumblr",
        "twimg",
        "twimg.com",
        "twitch",
        "twitch.tv",
        "twitter",
        "vimeo",
        "vimeo.com",
        "vine",
        "vocaroo",
        "voyagefusion.com",
        "walmart.com",
        "wikimedia",
        "xhamster",
        "xkcd.com",
        "xvideos",
        "xvideos.com",
        "xnxx.com",
        "yg-life.com",
        "youtu.be",
        "youtube",
        "youtubedoubler.com",
        "ytimg",
    ]

    system_apps: list[str] = [
        "com.apple.quicklook.QuickLookUIService",
        "com.apple.archiveutility",
        "com.apple.systempreferences",
        "com.apple.Mouse-Settings.extension",
    ]


settings = Settings()
