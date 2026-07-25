#!/usr/bin/env python3
"""
MusicMorph TG Bot v4.0 — PREMIUM EDITION
Author: HackerAI Pentest Suite
License: Authorized security assessment use only

═══ PREMIUM FEATURES ═══
• 𝕱𝖆𝖓𝖈𝖞 𝕲𝖊𝖓𝖊𝖗𝖆𝖙𝖊𝖉 𝕿𝖊𝖝𝖙 — classy Unicode typography
• 🎬 Pinterest intro video — loops on start message
• 👥 Group mode — /emina <song> sends directly, no selection
• 💬 DM mode — full search + selection as before
• 📈 Trending, mood picks, smart defaults

═══ METHODS (UNCHANGED) ═══
M0-M9 — all extraction engines preserved in original order
"""
import threading
import os, re, io, json, time, random, shutil, asyncio, tempfile
import logging, subprocess, traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Callable, Any
from collections import defaultdict, deque

import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK
from mutagen.mp4 import MP4, MP4Cover

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputFile, constants, ChatMember, Chat
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ChatMemberHandler
)
from telegram.helpers import escape_markdown

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────

BOT_TOKEN = "8785887150:AAF8Y9r4NG0HXRsfI3xql18lwmS9wr-56Qg"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
COOLDOWN_SECONDS = 10
MAX_DURATION_MINUTES = 120
MAX_FILE_SIZE_MB = 9999
TEMP_DIR = Path("./temp_downloads")
TEMP_DIR.mkdir(exist_ok=True)
COOKIES_FILE = Path("./cookies.txt")
PROXY_LIST = os.getenv("PROXY_LIST", "").split(",") if os.getenv("PROXY_LIST") else []
USE_TOR = os.getenv("USE_TOR", "false").lower() == "true"
TOR_PORT = os.getenv("TOR_PORT", "9050")

# Pinterest video for start message (change this URL to any Pinterest pin with a classy video)
PINTEREST_START_VIDEO_URL = os.getenv(
    "PINTEREST_START_VIDEO",
    "https://pin.it/7HigM52kt"  # <-- CHANGE THIS to your desired pin
)

_user_cooldowns: Dict[int, datetime] = {}
_user_queues: Dict[int, deque] = defaultdict(deque)

stats = {
    "total_downloads": 0, "total_searches": 0,
    "method_m0": 0, "method_m1": 0, "method_m2": 0, "method_m3": 0,
    "method_m4": 0, "method_m5": 0, "method_m6": 0, "method_m7": 0,
    "method_m8": 0, "method_m9": 0,
    "method_failures": 0, "method_recovery": 0,
    "group_downloads": 0, "premium_users": 0,
}

# ─── FANCY TEXT ENGINES ────────────────────────────────────────────────────

class Fancy:
    """Premium text stylizer — turns plain text into 𝖈𝖑𝖆𝖘𝖘𝖞 𝖀𝖓𝖎𝖈𝖔𝖉𝖊"""
    
    @staticmethod
    def script(text: str) -> str:
        """𝒮𝒸𝓇𝒾𝓅𝓉 𝒮𝓉𝓎𝓁𝑒"""
        mapping = {
            'A':'𝒜','B':'𝐵','C':'𝒞','D':'𝒟','E':'𝐸','F':'𝐹','G':'𝒢','H':'𝐻',
            'I':'𝐼','J':'𝒥','K':'𝒦','L':'𝐿','M':'𝑀','N':'𝒩','O':'𝒪','P':'𝒫',
            'Q':'𝒬','R':'𝑅','S':'𝒮','T':'𝒯','U':'𝒰','V':'𝒱','W':'𝒲','X':'𝒳',
            'Y':'𝒴','Z':'𝒵','a':'𝒶','b':'𝒷','c':'𝒸','d':'𝒹','e':'𝑒','f':'𝒻',
            'g':'ℊ','h':'𝒽','i':'𝒾','j':'𝒿','k':'𝓀','l':'𝓁','m':'𝓂','n':'𝓃',
            'o':'𝑜','p':'𝓅','q':'𝓆','r':'𝓇','s':'𝓈','t':'𝓉','u':'𝓊','v':'𝓋',
            'w':'𝓌','x':'𝓍','y':'𝓎','z':'𝓏',
        }
        return ''.join(mapping.get(c, c) for c in text)
    
    @staticmethod
    def fraktur(text: str) -> str:
        """𝕱𝖗𝖆𝖐𝖙𝖚𝖗 𝕾𝖙𝖞𝖑𝖊"""
        mapping = {
            'A':'𝔄','B':'𝔅','C':'ℭ','D':'𝔇','E':'𝔈','F':'𝔉','G':'𝔊','H':'ℌ',
            'I':'ℑ','J':'𝔍','K':'𝔎','L':'𝔏','M':'𝔐','N':'𝔑','O':'𝔒','P':'𝔓',
            'Q':'𝔔','R':'ℜ','S':'𝔖','T':'𝔗','U':'𝔘','V':'𝔙','W':'𝔚','X':'𝔛',
            'Y':'𝔜','Z':'ℨ','a':'𝔞','b':'𝔟','c':'𝔠','d':'𝔡','e':'𝔢','f':'𝔣',
            'g':'𝔤','h':'𝔥','i':'𝔦','j':'𝔧','k':'𝔨','l':'𝔩','m':'𝔪','n':'𝔫',
            'o':'𝔬','p':'𝔭','q':'𝔮','r':'𝔯','s':'𝔰','t':'𝔱','u':'𝔲','v':'𝔳',
            'w':'𝔴','x':'𝔵','y':'𝔶','z':'𝔷',
        }
        return ''.join(mapping.get(c, c) for c in text)
    
    @staticmethod
    def double_struck(text: str) -> str:
        """𝔻𝕠𝕦𝕓𝕝𝕖-𝕊𝕥𝕣𝕦𝕔𝕜"""
        mapping = {
            'A':'𝔸','B':'𝔹','C':'ℂ','D':'𝔻','E':'𝔼','F':'𝔽','G':'𝔾','H':'ℍ',
            'I':'𝕀','J':'𝕁','K':'𝕂','L':'𝕃','M':'𝕄','N':'ℕ','O':'𝕆','P':'ℙ',
            'Q':'ℚ','R':'ℝ','S':'𝕊','T':'𝕋','U':'𝕌','V':'𝕍','W':'𝕎','X':'𝕏',
            'Y':'𝕐','Z':'ℤ','a':'𝕒','b':'𝕓','c':'𝕔','d':'𝕕','e':'𝕖','f':'𝕗',
            'g':'𝕘','h':'𝕙','i':'𝕚','j':'𝕛','k':'𝕜','l':'𝕝','m':'𝕞','n':'𝕟',
            'o':'𝕠','p':'𝕡','q':'𝕢','r':'𝕣','s':'𝕤','t':'𝕥','u':'𝕦','v':'𝕧',
            'w':'𝕨','x':'𝕩','y':'𝕪','z':'𝕫',
        }
        return ''.join(mapping.get(c, c) for c in text)
    
    @staticmethod
    def bold_sans(text: str) -> str:
        """𝗕𝗼𝗹𝗱 𝗦𝗮𝗻𝘀 𝗦𝗲𝗿𝗶𝗳"""
        mapping = {
            'A':'𝗔','B':'𝗕','C':'𝗖','D':'𝗗','E':'𝗘','F':'𝗙','G':'𝗚','H':'𝗛',
            'I':'𝗜','J':'𝗝','K':'𝗞','L':'𝗟','M':'𝗠','N':'𝗡','O':'𝗢','P':'𝗣',
            'Q':'𝗤','R':'𝗥','S':'𝗦','T':'𝗧','U':'𝗨','V':'𝗩','W':'𝗪','X':'𝗫',
            'Y':'𝗬','Z':'𝗭','a':'𝗮','b':'𝗯','c':'𝗰','d':'𝗱','e':'𝗲','f':'𝗳',
            'g':'𝗴','h':'𝗵','i':'𝗶','j':'𝗷','k':'𝗸','l':'𝗹','m':'𝗺','n':'𝗻',
            'o':'𝗼','p':'𝗽','q':'𝗾','r':'𝗿','s':'𝘀','t':'𝘁','u':'𝘂','v':'𝘃',
            'w':'𝘄','x':'𝘅','y':'𝘆','z':'𝘇',
        }
        return ''.join(mapping.get(c, c) for c in text)
    
    @staticmethod
    def circled(text: str) -> str:
        """🅃🄴🅇🅃 🄸🄽 🄲🄸🅁🄲🄻🄴🅂"""
        mapping = {
            'A':'🄰','B':'🄱','C':'🄲','D':'🄳','E':'🄴','F':'🄵','G':'🄶','H':'🄷',
            'I':'🄸','J':'🄹','K':'🄺','L':'🄻','M':'🄼','N':'🄽','O':'🄾','P':'🄿',
            'Q':'🅀','R':'🅁','S':'🅂','T':'🅃','U':'🅄','V':'🅅','W':'🅆','X':'🅇',
            'Y':'🅈','Z':'🅉','a':'🄰','b':'🄱','c':'🄲','d':'🄳','e':'🄴','f':'🄵',
            'g':'🄶','h':'🄷','i':'🄸','j':'🄹','k':'🄺','l':'🄻','m':'🄼','n':'🄽',
            'o':'🄾','p':'🄿','q':'🅀','r':'🅁','s':'🅂','t':'🅃','u':'🅄','v':'🅅',
            'w':'🅆','x':'🅇','y':'🅈','z':'🅉',
        }
        return ''.join(mapping.get(c, c) for c in text)

    @staticmethod
    def glow(text: str) -> str:
        """Adds a 'glowing' effect with shadow Unicode chars"""
        return ' '.join(list(text.upper()))

    @staticmethod
    def header(title: str, char: str = "═", width: int = 40) -> str:
        """Create a classy boxed header"""
        side = (width - len(title) - 2) // 2
        return f"{char * side} {title} {char * side}"
    
    @staticmethod
    def premium_badge() -> str:
        """Premium floating badge"""
        return (
            "👑 ═══ ✦ 𝐄𝐌𝐈𝐍𝐀𝐌𝐔𝐒𝐈𝐂✦ ═══ 👑"
        )

# ─── PINTEREST VIDEO FETCHER ─────────────────────────────────────────────

async def fetch_pinterest_video(pin_url: str) -> Optional[Path]:
    """
    Download a video from a Pinterest pin URL.
    Used for the premium start message intro video.
    """
    import aiohttp
    import re
    
    cached = TEMP_DIR / "start_intro.mp4"
    if cached.exists():
        log.info("Using cached Pinterest intro video")
        return cached
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    patterns = [
        r'"contentUrl"\s*:\s*"([^"]+)"',
        r'"url"\s*:\s*"([^"]*\.mp4[^"]*)"',
        r'<video[^>]+src="([^"]+)"',
        r'"video_list"[^}]*"url"\s*:\s*"([^"]+)"',
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            # Fetch page
            async with session.get(pin_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    log.warning(f"Pinterest page returned {resp.status}")
                    return None
                html = await resp.text()
            
            # Try JSON-LD first (most reliable)
            import json as json_lib
            ld_matches = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
            for ld in ld_matches:
                try:
                    data = json_lib.loads(ld)
                    if isinstance(data, dict):
                        for key in ['contentUrl', 'url']:
                            if key in data and 'mp4' in str(data[key]):
                                video_url = data[key]
                                if not video_url.startswith('http'):
                                    continue
                                # Download
                                async with session.get(video_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as vresp:
                                    if vresp.status == 200:
                                        with open(cached, "wb") as f:
                                            async for chunk in vresp.content.iter_chunked(8192):
                                                f.write(chunk)
                                        if cached.stat().st_size > 1024:
                                            log.info(f"✅ Downloaded Pinterest video ({cached.stat().st_size/1024:.0f}KB)")
                                            return cached
                except: pass
            
            # Regex fallback
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    video_url = match.group(1).replace('\\/', '/').replace('&amp;', '&')
                    if not video_url.startswith('http'):
                        continue
                    async with session.get(video_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as vresp:
                        if vresp.status == 200:
                            with open(cached, "wb") as f:
                                async for chunk in vresp.content.iter_chunked(8192):
                                    f.write(chunk)
                            if cached.stat().st_size > 1024:
                                log.info(f"✅ Downloaded Pinterest video ({cached.stat().st_size/1024:.0f}KB)")
                                return cached
            
            log.warning("No video URL found in Pinterest page")
            return None
            
    except Exception as e:
        log.warning(f"Pinterest fetch failed: {e}")
        return None

# ─── OTHER HELPERS ─────────────────────────────────────────────────────────

def safe_filename(s: str, max_len: int = 60) -> str:
    s = re.sub(r'[<>:"/\\|?*]', "", s)
    s = s.strip().replace("\n", " ").replace("\r", "")
    if len(s) > max_len: s = s[:max_len].rsplit(" ", 1)[0] + "…"
    return s or "audio"

def fmt_duration(seconds: int) -> str:
    if not seconds: return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"

def fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024: return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"

def get_random_proxy() -> Optional[str]:
    if USE_TOR: return f"socks5://127.0.0.1:{TOR_PORT}"
    if PROXY_LIST: return random.choice(PROXY_LIST)
    return None

def extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return None

def ensure_ytdlp_config():
    config_content = """# MusicMorph PRO v4.0 config
--remote-components ejs:github
--js-runtimes deno
--geo-bypass
--geo-bypass-country US
--no-playlist
--no-warnings
"""
    config_dirs = [Path.home() / ".yt-dlp", Path.home() / ".config" / "yt-dlp", Path(".")]
    for cfg_dir in config_dirs:
        cfg_dir = Path(cfg_dir)
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config"
        if not cfg_file.exists():
            try:
                cfg_file.write_text(config_content)
                log.info(f"Config created at {cfg_file}")
                break
            except: pass
        elif "--remote-components" not in cfg_file.read_text():
            with open(cfg_file, "a") as f:
                f.write("\n# MusicMorph PRO v4.0\n--remote-components ejs:github\n--js-runtimes deno\n")
            break

# ─── TAG ENGINES ────────────────────────────────────────────────────────────

async def run_ffmpeg(*args, timeout: int = 180) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await asyncio.wait_for(proc.wait(), timeout=timeout)
        return proc.returncode == 0
    except: return False

async def tag_audio_file(filepath: Path, info: dict, cover_data: Optional[bytes] = None) -> None:
    ext = filepath.suffix.lower()
    if ext == ".mp3": await _tag_mp3(filepath, info, cover_data)
    elif ext in (".m4a", ".mp4"): await _tag_m4a(filepath, info, cover_data)

async def _tag_mp3(filepath: Path, info: dict, cover_data: Optional[bytes] = None) -> None:
    try:
        audio = MP3(filepath, ID3=ID3)
        if audio.tags is None: audio.tags = ID3()
        t = info.get("title", "Unknown"); u = info.get("uploader") or info.get("channel", "Unknown")
        a = info.get("album") or info.get("playlist_title", "YouTube Music")
        y = info.get("upload_date", "")[:4] if info.get("upload_date") else ""
        r = info.get("playlist_index", "")
        audio.tags.add(TIT2(encoding=3, text=t)); audio.tags.add(TPE1(encoding=3, text=u))
        audio.tags.add(TALB(encoding=3, text=a))
        if y: audio.tags.add(TDRC(encoding=3, text=y))
        if r: audio.tags.add(TRCK(encoding=3, text=str(r)))
        if cover_data: audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover_data))
        audio.save()
    except Exception as e: log.warning(f"Tagging failed: {e}")

async def _tag_m4a(filepath: Path, info: dict, cover_data: Optional[bytes] = None) -> None:
    try:
        audio = MP4(filepath)
        audio["\xa9nam"] = info.get("title", "Unknown"); audio["\xa9ART"] = info.get("uploader") or info.get("channel", "Unknown")
        audio["\xa9alb"] = info.get("album") or info.get("playlist_title", "YouTube Music")
        y = info.get("upload_date", "")[:4]; 
        if y: audio["\xa9day"] = y
        if cover_data: audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
        audio.save()
    except Exception as e: log.warning(f"M4A tagging failed: {e}")

async def fetch_cover(thumb_url: str) -> Optional[bytes]:
    if not thumb_url: return None
    try:
        import aiohttp
        async with aiohttp.ClientSession() as sess:
            async with sess.get(thumb_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200: return await resp.read()
    except: pass
    return None

# ═══════════════════════════════════════════════════════════════════════════
# PRE-FLIGHT
# ═══════════════════════════════════════════════════════════════════════════

async def run_preflight_check() -> Dict[str, Any]:
    results = {"deno": False, "ytdlp_ejs": False, "ytdlp_version": "", "cookies": False, "ffmpeg": False}
    for cmd in ["deno", "node"]:
        try:
            proc = await asyncio.create_subprocess_exec(cmd, "--version", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0: results["deno"] = True; break
        except: pass
    try:
        proc = await asyncio.create_subprocess_exec("yt-dlp", "--version", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode == 0: results["ytdlp_version"] = o.decode().strip()
    except: pass
    try:
        import yt_dlp.ejs; results["ytdlp_ejs"] = True
    except: pass
    if COOKIES_FILE.exists(): results["cookies"] = True
    try:
        proc = await asyncio.create_subprocess_exec("ffmpeg", "-version", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode == 0: results["ffmpeg"] = True
    except: pass
    return results

# ═══════════════════════════════════════════════════════════════════════════
# METHODS — M0 through M9 (COMPLETELY UNCHANGED)
# ═══════════════════════════════════════════════════════════════════════════
# ▸ These methods are IDENTICAL to v3.1
# ▸ Order preserved: M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9
# ▸ No modifications to any extraction logic
# ═══════════════════════════════════════════════════════════════════════════

QUALITY_PRESETS = {
    "ultra": {"format": "bestaudio[abr>192]/bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}], "label": "🎧 Ultra 320kbps"},
    "high": {"format": "bestaudio[abr<=192]/bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}], "label": "🎵 High 192kbps"},
    "medium": {"format": "bestaudio[abr<=128]/bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}], "label": "🔉 Medium 128kbps"},
    "opus_raw": {"format": "bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "opus"}], "label": "🎤 Opus Raw"},
}
DEFAULT_QUALITY = "high"

# ─── M0: SUBPROCESS CLI ────────────────────────────────────────────────────

async def method0_subprocess(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] yt-dlp via subprocess with --remote-components ejs:github"""
    video_id = extract_video_id(url) or "unknown"
    out_template = str(TEMP_DIR / "%(id)s_m0.%(ext)s")
    quality_map = {"ultra": "bestaudio[abr>192]/bestaudio/best", "high": "bestaudio[abr<=192]/bestaudio/best", "medium": "bestaudio[abr<=128]/bestaudio/best", "opus_raw": "bestaudio[ext=opus]/bestaudio/best"}
    fmt = quality_map.get(quality_key, "bestaudio/best")
    cmd = ["yt-dlp", "--no-playlist", "--quiet", "--no-warnings", "--no-color", "--geo-bypass", "--geo-bypass-country", "US", "--restrict-filenames", "--print", "after_move:filepath", "-o", out_template, "-f", fmt, "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0", "--embed-thumbnail", "--add-metadata", "--remote-components", "ejs:github", "--js-runtimes", "deno"]
    if COOKIES_FILE.exists(): cmd.extend(["--cookies", str(COOKIES_FILE)])
    try:
        proc = await asyncio.create_subprocess_exec("yt-dlp", "--cookies-from-browser", "chrome", "--version", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await asyncio.wait_for(proc.communicate(), timeout=5)
        cmd.extend(["--cookies-from-browser", "chrome"])
    except:
        try:
            proc = await asyncio.create_subprocess_exec("yt-dlp", "--cookies-from-browser", "firefox", "--version", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            await asyncio.wait_for(proc.communicate(), timeout=5)
            cmd.extend(["--cookies-from-browser", "firefox"])
        except: pass
    proxy = get_random_proxy()
    if proxy: cmd.extend(["--proxy", proxy])
    po_token = os.getenv("PO_TOKEN")
    if po_token: cmd.extend(["--extractor-args", f"youtube:po_token=web.gvs+{po_token}"])
    cmd.extend(["--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"])
    cmd.append(url)
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode != 0: return None
        output = stdout.decode().strip() if stdout else ""
        fp_str = output.split("\n")[-1].strip() if output else ""
        found = None
        if fp_str and Path(fp_str).exists(): found = Path(fp_str)
        else:
            cands = list(TEMP_DIR.glob("*_m0.mp3")) + list(TEMP_DIR.glob("*_m0.*"))
            if cands: found = max(cands, key=os.path.getmtime)
        if not found or not found.exists(): return None
        info_cmd = ["yt-dlp", "--no-playlist", "--quiet", "--no-warnings", "--dump-json", "--no-download", "--remote-components", "ejs:github", "--js-runtimes", "deno", url]
        proc2 = await asyncio.create_subprocess_exec(*info_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        s2, _ = await asyncio.wait_for(proc2.communicate(), timeout=30)
        info = {}
        if s2:
            try: info = json.loads(s2.decode().split("\n")[0])
            except: pass
        if not info.get("id"): info["id"] = video_id; info["title"] = info.get("title", video_id); info["uploader"] = info.get("uploader", "YouTube")
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(found, info, cd)
        return found, info, cd
    except Exception as e: log.warning(f"M0 failed: {e}"); return None

# ─── M1: yt-dlp FULL ───────────────────────────────────────────────────────

async def method1_ytdlp_full(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] yt-dlp Python API with combined format + extractor args"""
    preset = QUALITY_PRESETS.get(quality_key, QUALITY_PRESETS[DEFAULT_QUALITY])
    ydl_opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "no_color": True, "noprogress": True, "outtmpl": str(TEMP_DIR / "%(id)s_m1.%(ext)s"), "restrictfilenames": True, "format": "bv*+ba/b", "geo_bypass": True, "geo_bypass_country": "US", "extractor_args": {"youtube": {"player_client": ["android", "ios", "web_safari"], "skip": ["dash", "hls"]}}, "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}, "extractor_retries": 3, "fragment_retries": 3, "retry_sleep": lambda n: 2 ** min(n, 4)}
    if COOKIES_FILE.exists(): ydl_opts["cookiefile"] = str(COOKIES_FILE)
    proxy = get_random_proxy()
    if proxy: ydl_opts["proxy"] = proxy
    if quality_key != "opus_raw": ydl_opts["postprocessors"] = preset.get("postprocessors", [])
    po_token = os.getenv("PO_TOKEN")
    if po_token: ydl_opts["extractor_args"]["youtube"]["po_token"] = f"web.gvs+{po_token}"
    try:
        loop = asyncio.get_event_loop()
        def sync_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: return ydl.extract_info(url, download=True)
        info = await loop.run_in_executor(None, sync_dl)
        if info is None: return None
        video_id = info.get("id", "unknown")
        expected = TEMP_DIR / f"{video_id}_m1.mp3"
        if not expected.exists():
            for ext in ["mp3", "m4a", "opus", "webm", "mka"]:
                cand = TEMP_DIR / f"{video_id}_m1.{ext}"
                if cand.exists(): expected = cand; break
            else:
                files = sorted(TEMP_DIR.glob(f"{video_id}_m1*"), key=os.path.getmtime, reverse=True)
                if files: expected = files[0]
                else: return None
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(expected, info, cd)
        return expected, info, cd
    except Exception as e: log.warning(f"M1 failed: {e}"); return None

# ─── M2: yt-dlp LEGACY ─────────────────────────────────────────────────────

async def method2_ytdlp_legacy(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] Android/iOS client extraction path"""
    preset = QUALITY_PRESETS.get(quality_key, QUALITY_PRESETS[DEFAULT_QUALITY])
    ydl_opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "no_color": True, "noprogress": True, "outtmpl": str(TEMP_DIR / "%(id)s_m2.%(ext)s"), "restrictfilenames": True, "extractor_retries": 3, "format": "bv*+ba/b", "geo_bypass": True, "geo_bypass_country": "US", "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv"], "skip": ["dash", "hls", "webpage", "configs"]}}, "http_headers": {"User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36"}}
    if COOKIES_FILE.exists(): ydl_opts["cookiefile"] = str(COOKIES_FILE)
    proxy = get_random_proxy()
    if proxy: ydl_opts["proxy"] = proxy
    if quality_key != "opus_raw": ydl_opts["postprocessors"] = preset.get("postprocessors", [])
    po_token = os.getenv("PO_TOKEN")
    if po_token: ydl_opts["extractor_args"]["youtube"]["po_token"] = f"ios.gvs+{po_token}"
    try:
        loop = asyncio.get_event_loop()
        def sync_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: return ydl.extract_info(url, download=True)
        info = await loop.run_in_executor(None, sync_dl)
        if info is None: return None
        video_id = info.get("id", "unknown")
        expected = TEMP_DIR / f"{video_id}_m2.mp3"
        if not expected.exists():
            for ext in ["mp3", "m4a", "opus", "webm"]:
                cand = TEMP_DIR / f"{video_id}_m2.{ext}"
                if cand.exists(): expected = cand; break
            else:
                files = sorted(TEMP_DIR.glob(f"{video_id}_m2*"), key=os.path.getmtime, reverse=True)
                if files: expected = files[0]
                else: return None
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(expected, info, cd)
        return expected, info, cd
    except Exception as e: log.warning(f"M2 failed: {e}"); return None

# ─── M3: DASH Direct ───────────────────────────────────────────────────────

async def method3_dash_direct(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] Direct DASH manifest extraction"""
    preset = QUALITY_PRESETS.get(quality_key, QUALITY_PRESETS[DEFAULT_QUALITY])
    ydl_opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "no_color": True, "noprogress": True, "outtmpl": str(TEMP_DIR / "%(id)s_m3.%(ext)s"), "restrictfilenames": True, "format": "bestaudio[protocol=https,dash]/bestaudio[protocol=m3u8]/bestaudio/best", "geo_bypass": True, "geo_bypass_country": "US", "extractor_args": {"youtube": {"player_client": ["android", "ios"], "include_dash_manifest": True, "skip": ["webpage", "configs"]}}}
    if COOKIES_FILE.exists(): ydl_opts["cookiefile"] = str(COOKIES_FILE)
    try:
        loop = asyncio.get_event_loop()
        def sync_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: return ydl.extract_info(url, download=True)
        info = await loop.run_in_executor(None, sync_dl)
        if info is None: return None
        video_id = info.get("id", "unknown")
        candidates = list(TEMP_DIR.glob(f"{video_id}_m3.*"))
        if not candidates: return None
        source_file = candidates[0]
        mp3_path = TEMP_DIR / f"{video_id}_m3.mp3"
        success = await run_ffmpeg("-i", str(source_file), "-codec:a", "libmp3lame", "-q:a", "0", "-map", "a", str(mp3_path), timeout=180)
        if not success or not mp3_path.exists(): return None
        source_file.unlink(missing_ok=True)
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(mp3_path, info, cd)
        return mp3_path, info, cd
    except Exception as e: log.warning(f"M3 failed: {e}"); return None

# ─── M4: COMBINED ──────────────────────────────────────────────────────────

async def method4_combined(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] Combined format (bv+ba/b) — 403 bypass"""
    ydl_opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "no_color": True, "noprogress": True, "outtmpl": str(TEMP_DIR / "%(id)s_m4.%(ext)s"), "restrictfilenames": True, "format": "bv*+ba/b", "merge_output_format": "mp4", "geo_bypass": True, "geo_bypass_country": "US", "extractor_args": {"youtube": {"player_client": ["android", "ios", "web_safari"], "skip": ["dash", "hls"]}}, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
    if COOKIES_FILE.exists(): ydl_opts["cookiefile"] = str(COOKIES_FILE)
    proxy = get_random_proxy()
    if proxy: ydl_opts["proxy"] = proxy
    po_token = os.getenv("PO_TOKEN")
    if po_token: ydl_opts["extractor_args"]["youtube"]["po_token"] = f"web.gvs+{po_token}"
    try:
        loop = asyncio.get_event_loop()
        def sync_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: return ydl.extract_info(url, download=True)
        info = await loop.run_in_executor(None, sync_dl)
        if info is None: return None
        video_id = info.get("id", "unknown")
        expected = TEMP_DIR / f"{video_id}_m4.mp3"
        if not expected.exists():
            for ext in ["mp3", "m4a", "opus"]:
                cand = TEMP_DIR / f"{video_id}_m4.{ext}"
                if cand.exists(): expected = cand; break
            else: return None
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(expected, info, cd)
        return expected, info, cd
    except Exception as e: log.warning(f"M4 failed: {e}"); return None

# ─── M5: PYTUBEFIX ─────────────────────────────────────────────────────────

async def method5_pytubefix(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] pytubefix OAuth — actively maintained fork"""
    try:
        from pytubefix import YouTube as PytubeFix
    except ImportError: log.warning("M5: pytubefix not installed"); return None
    try:
        loop = asyncio.get_event_loop()
        def sync_pt():
            yt = PytubeFix(url, use_oauth=True, allow_oauth_cache=True)
            stream = yt.streams.get_audio_only()
            if not stream: stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            if not stream: return None
            info = {"id": yt.video_id, "title": yt.title, "uploader": yt.author, "thumbnail": yt.thumbnail_url, "duration": yt.length}
            out_path = stream.download(output_path=str(TEMP_DIR), filename=f"{yt.video_id}_m5", mp3=False)
            out_file = Path(out_path)
            mp3_path = TEMP_DIR / f"{yt.video_id}_m5.mp3"
            result = subprocess.run(["ffmpeg", "-i", str(out_file), "-codec:a", "libmp3lame", "-q:a", "0", "-map", "a", str(mp3_path)], capture_output=True, timeout=180)
            if mp3_path.exists(): out_file.unlink(missing_ok=True); return mp3_path, info
            return None
        result = await loop.run_in_executor(None, sync_pt)
        if result is None: return None
        filepath, info = result
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(filepath, info, cd)
        return filepath, info, cd
    except Exception as e: log.warning(f"M5 failed: {e}"); return None

# ─── M6: INVIDIOUS ─────────────────────────────────────────────────────────

INVIDIOUS_INSTANCES = ["https://inv.nadeko.net", "https://yewtu.be", "https://invidious.snopyta.org", "https://invidious.privacydev.net", "https://invidious.projectsegfau.lt", "https://invidious.nerdvpn.de", "https://invidious.osi.kr", "https://vid.puffyan.us", "https://inv.vern.cc", "https://invidious.baczek.me"]

async def method6_invidious(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] Use Invidious instance as proxy"""
    video_id = extract_video_id(url)
    if not video_id: return None
    instances = INVIDIOUS_INSTANCES.copy(); random.shuffle(instances)
    for instance in instances:
        invidious_url = f"{instance}/watch?v={video_id}"
        ydl_opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "no_color": True, "noprogress": True, "outtmpl": str(TEMP_DIR / f"{video_id}_m6.%(ext)s"), "restrictfilenames": True, "format": "bestaudio/best", "extractor_args": {"youtube": {"skip": ["dash", "hls"]}}, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
        try:
            loop = asyncio.get_event_loop()
            def sync_dl():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl: return ydl.extract_info(invidious_url, download=True)
            info = await loop.run_in_executor(None, sync_dl)
            if info is None: continue
            expected = TEMP_DIR / f"{video_id}_m6.mp3"
            if not expected.exists():
                for ext in ["mp3", "m4a", "opus"]:
                    cand = TEMP_DIR / f"{video_id}_m6.{ext}"
                    if cand.exists(): expected = cand; break
                else: continue
            cd = await fetch_cover(info.get("thumbnail"))
            await tag_audio_file(expected, info, cd)
            return expected, info, cd
        except Exception as e: log.warning(f"M6 failed on {instance}: {e}"); continue
    return None

# ─── M7: YT MUSIC API ─────────────────────────────────────────────────────

async def method7_ytmusicapi(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] YouTube Music internal API"""
    try: from ytmusicapi import YTMusic
    except ImportError: log.warning("M7: ytmusicapi not installed"); return None
    video_id = extract_video_id(url)
    if not video_id: return None
    try:
        loop = asyncio.get_event_loop()
        def sync_ytm():
            ytm = YTMusic(); song = ytm.get_song(video_id)
            if not song: return None
            stream_url = None
            if song.get("adaptiveFormats") and "url" in song["adaptiveFormats"][0]:
                stream_url = song["adaptiveFormats"][0].get("url") or song["adaptiveFormats"][0].get("streamUrl")
            if not stream_url and "playbackUrl" in song: stream_url = song["playbackUrl"]
            if not stream_url:
                try:
                    si = ytm.get_stream(video_id)
                    if si: stream_url = si.get("url") or si.get("streamUrl")
                except: pass
            if not stream_url: return None
            return song, stream_url
        result = await loop.run_in_executor(None, sync_ytm)
        if result is None: return None
        song, stream_url = result
        import aiohttp
        filepath = TEMP_DIR / f"{video_id}_m7.m4a"
        async with aiohttp.ClientSession() as session:
            async with session.get(stream_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://music.youtube.com/"}) as resp:
                if resp.status != 200: return None
                with open(filepath, "wb") as f:
                    while True:
                        chunk = await resp.content.read(8192)
                        if not chunk: break
                        f.write(chunk)
        if not filepath.exists() or filepath.stat().st_size < 1024: return None
        mp3_path = TEMP_DIR / f"{video_id}_m7.mp3"
        success = await run_ffmpeg("-i", str(filepath), "-codec:a", "libmp3lame", "-q:a", "0", "-map", "a", str(mp3_path), timeout=180)
        if not success or not mp3_path.exists(): return None
        filepath.unlink(missing_ok=True)
        artists = song.get("artists", [{}]) if song.get("artists") else [{}]
        artist_name = artists[0].get("name", "Unknown") if artists else "Unknown"
        info = {"id": video_id, "title": song.get("title", "Unknown"), "uploader": artist_name, "thumbnail": "", "duration": song.get("lengthSeconds", 0)}
        thumbnails = song.get("thumbnail", {}).get("thumbnails", [])
        if thumbnails: info["thumbnail"] = thumbnails[-1].get("url", "")
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(mp3_path, info, cd)
        return mp3_path, info, cd
    except Exception as e: log.warning(f"M7 failed: {e}"); return None

# ─── M8: TV CLIENT ─────────────────────────────────────────────────────────

async def method8_tv_client(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] YouTube TV client — least restricted"""
    preset = QUALITY_PRESETS.get(quality_key, QUALITY_PRESETS[DEFAULT_QUALITY])
    ydl_opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "no_color": True, "noprogress": True, "outtmpl": str(TEMP_DIR / "%(id)s_m8.%(ext)s"), "restrictfilenames": True, "format": "bv*+ba/b", "geo_bypass": True, "geo_bypass_country": "US", "extractor_args": {"youtube": {"player_client": ["tv", "tv_embedded", "android_vr"], "skip": ["dash", "hls", "webpage", "configs"]}}, "http_headers": {"User-Agent": "Mozilla/5.0 (SMART-TV; Linux; Tizen 8.0) AppleWebKit/537.36 (KHTML, like Gecko) SamsungTV/2024 Chrome/120.0.6099.144 Safari/537.36"}}
    if COOKIES_FILE.exists(): ydl_opts["cookiefile"] = str(COOKIES_FILE)
    if quality_key != "opus_raw": ydl_opts["postprocessors"] = preset.get("postprocessors", [])
    try:
        loop = asyncio.get_event_loop()
        def sync_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: return ydl.extract_info(url, download=True)
        info = await loop.run_in_executor(None, sync_dl)
        if info is None: return None
        video_id = info.get("id", "unknown")
        expected = TEMP_DIR / f"{video_id}_m8.mp3"
        if not expected.exists():
            for ext in ["mp3", "m4a", "opus", "webm"]:
                cand = TEMP_DIR / f"{video_id}_m8.{ext}"
                if cand.exists(): expected = cand; break
            else:
                files = sorted(TEMP_DIR.glob(f"{video_id}_m8*"), key=os.path.getmtime, reverse=True)
                if files: expected = files[0]
                else: return None
        cd = await fetch_cover(info.get("thumbnail"))
        await tag_audio_file(expected, info, cd)
        return expected, info, cd
    except Exception as e: log.warning(f"M8 failed: {e}"); return None

# ─── M9: PLAYWRIGHT ────────────────────────────────────────────────────────

async def method9_playwright(url: str, quality_key: str = DEFAULT_QUALITY) -> Optional[Tuple[Path, dict, bytes]]:
    """[UNCHANGED] Headless browser extraction — nuclear option"""
    try: from playwright.async_api import async_playwright
    except ImportError: log.warning("M9: playwright not installed"); return None
    video_id = extract_video_id(url)
    if not video_id: return None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-web-security", "--disable-features=IsolateOrigins,site-per-process", "--mute-audio"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", viewport={"width": 1920, "height": 1080}, locale="en-US")
            page = await context.new_page()
            audio_urls = []; audio_urls_set = set()
            async def intercept_response(response):
                if response.status != 200: return
                u = response.url
                if "googlevideo.com" in u and "audio" in u and u not in audio_urls_set:
                    audio_urls_set.add(u); audio_urls.append(u)
            page.on("response", intercept_response)
            await page.goto(f"https://www.youtube.com/watch?v={video_id}", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            try:
                pb = await page.wait_for_selector("button.ytp-play-button", timeout=5000)
                if pb: await pb.click(); await page.wait_for_timeout(3000); await pb.click()
            except: pass
            await page.wait_for_timeout(2000)
            audio_url = None
            try:
                audio_url = await page.evaluate("""
                    () => {
                        const v = document.querySelector('video');
                        if (v) {
                            if (v.src) return v.src;
                            for (const s of v.querySelectorAll('source'))
                                if (s.src) return s.src;
                        }
                        return null;
                    }
                """)
            except: pass
            if not audio_url and audio_urls:
                for u in audio_urls:
                    if any(e in u for e in [".m4a", ".webm", "audio", "itag=140", "itag=251", "itag=250"]):
                        audio_url = u; break
                if not audio_url: audio_url = audio_urls[-1]
            await browser.close()
            if not audio_url: return None
            import aiohttp
            filepath = TEMP_DIR / f"{video_id}_m9.m4a"
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, headers={"User-Agent": "Mozilla/5.0", "Referer": f"https://www.youtube.com/watch?v={video_id}"}) as resp:
                    if resp.status != 200: return None
                    with open(filepath, "wb") as f:
                        while True:
                            chunk = await resp.content.read(8192)
                            if not chunk: break
                            f.write(chunk)
            if not filepath.exists() or filepath.stat().st_size < 1024: return None
            mp3_path = TEMP_DIR / f"{video_id}_m9.mp3"
            success = await run_ffmpeg("-i", str(filepath), "-codec:a", "libmp3lame", "-q:a", "0", "-map", "a", str(mp3_path), timeout=180)
            if not success or not mp3_path.exists(): return None
            filepath.unlink(missing_ok=True)
            info = {"id": video_id, "title": video_id, "uploader": "YouTube", "duration": 0}
            try:
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                    idata = ydl.extract_info(url, download=False)
                    if idata:
                        info["title"] = idata.get("title", video_id)
                        info["uploader"] = idata.get("uploader", idata.get("channel", "YouTube"))
                        info["duration"] = idata.get("duration", 0)
                        info["thumbnail"] = idata.get("thumbnail", "")
            except: pass
            cd = await fetch_cover(info.get("thumbnail"))
            await tag_audio_file(mp3_path, info, cd)
            return mp3_path, info, cd
    except Exception as e: log.warning(f"M9 failed: {e}"); return None

# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR — Method Chain (UNCHANGED ORDER)
# ═══════════════════════════════════════════════════════════════════════════

METHOD_CHAIN = [
    ("M0", "⚡ yt-dlp CLI", method0_subprocess),
    ("M1", "🚀 yt-dlp Full", method1_ytdlp_full),
    ("M2", "⚡ yt-dlp Legacy", method2_ytdlp_legacy),
    ("M3", "📡 DASH Direct", method3_dash_direct),
    ("M4", "🔀 Combined Fmt", method4_combined),
    ("M5", "🐍 PytubeFix", method5_pytubefix),
    ("M6", "🔗 Invidious", method6_invidious),
    ("M7", "🎼 YT Music API", method7_ytmusicapi),
    ("M8", "📺 TV Client", method8_tv_client),
    ("M9", "🕵️ Playwright", method9_playwright),
]

METHOD_EMOJIS = {"M0": "⚡", "M1": "🚀", "M2": "⚡", "M3": "📡", "M4": "🔀", "M5": "🐍", "M6": "🔗", "M7": "🎼", "M8": "📺", "M9": "🕵️"}

async def download_with_fallback(url, quality_key=DEFAULT_QUALITY, progress_callback=None):
    """[UNCHANGED] Try each method in sequence until one succeeds"""
    failures = []
    for method_id, method_name, method_func in METHOD_CHAIN:
        try:
            log.info(f"Trying {method_id} ({method_name})...")
            if progress_callback: await progress_callback(f"🔄 Trying {METHOD_EMOJIS.get(method_id, '🔧')} {method_name}...")
            result = await method_func(url, quality_key)
            if result is not None:
                filepath, info, cover_data = result
                log.info(f"✅ {method_id} succeeded: {filepath.name}")
                stats[f"method_{method_id.lower()}"] += 1
                stats["total_downloads"] += 1
                return filepath, info, cover_data, method_id
            else: failures.append(method_id)
        except Exception as e:
            log.warning(f"❌ {method_id} threw: {e}")
            failures.append(method_id)
    stats["method_failures"] += 1
    return None

# ═══════════════════════════════════════════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════════════════════════════════════════

async def search_youtube(query: str, max_results: int = 8) -> List[dict]:
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "default_search": "ytsearch", "playlistend": max_results, "ignoreerrors": True}
    try:
        loop = asyncio.get_event_loop()
        def sync_search():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: return ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        result = await loop.run_in_executor(None, sync_search)
        entries = result.get("entries", [])
        if entries: return [e for e in entries if e and e.get("id")]
    except Exception as e: log.warning(f"Search failed: {e}")
    random.shuffle(INVIDIOUS_INSTANCES)
    for instance in INVIDIOUS_INSTANCES[:5]:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{instance}/api/v1/search?q={query}&type=video", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [{"id": v.get("videoId"), "title": v.get("title"), "duration": v.get("lengthSeconds", 0), "uploader": v.get("author"), "thumbnail": v.get("videoThumbnails", [{}])[0].get("url", "")} for v in data[:max_results]]
        except: continue
    return []

# ═══════════════════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════

def search_results_keyboard(results: List[dict], page: int = 0) -> InlineKeyboardMarkup:
    keyboard = []
    start, end = page * 5, min(page * 5 + 5, len(results))
    for idx in range(start, end):
        v = results[idx]
        title = (v.get("title") or "Unknown")[:35]
        dur = fmt_duration(v.get("duration", 0))
        uploader = (v.get("uploader") or v.get("channel") or "?")[:18]
        keyboard.append([InlineKeyboardButton(f"{idx+1}. {title} [{dur}] — {uploader}", callback_data=f"select_{v['id']}_{idx}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"page_{page-1}"))
    total = (len(results) + 4) // 5
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total}", callback_data="noop"))
    if end < len(results): nav.append(InlineKeyboardButton("Next ▶", callback_data=f"page_{page+1}"))
    if nav: keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("🎛 Quality", callback_data="quality_menu_global"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def quality_keyboard(url: str = "", msg_id: int = 0) -> InlineKeyboardMarkup:
    keyboard = []
    for key, preset in QUALITY_PRESETS.items():
        keyboard.append([InlineKeyboardButton(preset["label"], callback_data=f"dl_{key}_{msg_id}")])
    keyboard.append([InlineKeyboardButton("↩ Back", callback_data="back_to_results"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def music_player_keyboard(video_id: str, method: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇ Re-Download", callback_data=f"redl_{video_id}"), InlineKeyboardButton("🔎 New Search", callback_data="new_search")],
        [InlineKeyboardButton("🗑 Delete", callback_data=f"delmsg_{video_id}"), InlineKeyboardButton("ℹ️ Info", callback_data=f"info_{video_id}")],
        [InlineKeyboardButton("👑 Owner", url="https://t.me/Ankneewayz")
        ]
    ])

def premium_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 𝕾𝖊𝖆𝖗𝖈𝖍 𝕸𝖚𝖘𝖎𝖈", callback_data="new_search")],
        [InlineKeyboardButton("📈 𝕿𝖗𝖊𝖓𝖉𝖎𝖓𝖌 𝕹𝖔𝖜", callback_data="trending")],
        [InlineKeyboardButton("📊 𝕾𝖙𝖆𝖙𝖘", callback_data="show_stats"), InlineKeyboardButton("❓ 𝕳𝖊𝖑𝖕", callback_data="show_help")],
        [InlineKeyboardButton("👥 𝕲𝖗𝖔𝖚𝖕 𝕸𝖔𝖉𝖊", callback_data="group_info")],
    ])

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS — PREMIUM EDITION
# ═══════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🎬 PREMIUM start message with Pinterest intro video + classy typography"""
    user = update.effective_user
    chat = update.effective_chat
    is_group = chat.type in (Chat.GROUP, Chat.SUPERGROUP)
    
    stats["premium_users"] += 1
    
    # ── 𝕻𝖗𝖊𝖒𝖎𝖚𝖒 𝖂𝖊𝖑𝖈𝖔𝖒𝖊 𝕿𝖊𝖝𝖙 ──
    welcome_text = (
        f"🎬 {Fancy.premium_badge()}\n\n"
        f"✦ {Fancy.bold_sans('WELCOME')} ✦\n\n"
        f"👑 {Fancy.script(f'{user.first_name}')}, you've unlocked\n"
        f"{Fancy.double_struck('MusicMorph PRO v4.0')}\n\n"
        f"{Fancy.header('10 ENGINES')}\n"
        f"⚡ M0: {Fancy.fraktur('yt-dlp CLI Subprocess')}\n"
        f"🚀 M1: {Fancy.fraktur('yt-dlp Full')}\n"
        f"⚡ M2–M9: {Fancy.fraktur('Legacy · DASH · Combined · PytubeFix')}\n"
        f"         {Fancy.fraktur('Invidious · YT API · TV · Playwright')}\n\n"
        f"{Fancy.header('COMMANDS')}\n"
        f"🎵 `{escape_markdown('/search')}`  {Fancy.script('Search any song or artist')}\n"
        f"📥 `{escape_markdown('/dl')}`  {Fancy.script('Direct download from URL')}\n"
        f"👥 `{escape_markdown('/emina')}`  {Fancy.script('Group mode — instant send')}\n"
        f"📈 `{escape_markdown('/trending')}`  {Fancy.script('What is hot right now')}\n"
        f"✅ `{escape_markdown('/check')}`  {Fancy.script('System diagnostics')}\n\n"
        f"{Fancy.header('', '✦', 30)}\n"
    )
    
    if is_group:
        welcome_text += f"\n👥 *Group Mode Active*\nUse `/emina <song name>` to get music instantly!\n"
    
    # ── Try to fetch & send Pinterest intro video ──
    video_path = await fetch_pinterest_video(PINTEREST_START_VIDEO_URL)
    
    if video_path and video_path.exists():
        try:
            # Send video first (looping, no sound classy intro)
            with open(video_path, "rb") as vf:
                await update.message.reply_video(
                    video=InputFile(vf, filename="intro.mp4"),
                    caption=welcome_text,
                    parse_mode=constants.ParseMode.MARKDOWN,
                    reply_markup=premium_menu_keyboard(),
                    supports_streaming=True,
                    width=720, height=720,
                    duration=5,
                )
            return
        except Exception as e:
            log.warning(f"Video send failed, falling back to photo: {e}")
    
    # ── Fallback: try sending a thumbnail if video failed ──
    # Try to at least get a thumbnail from Pinterest
    try:
        import aiohttp
        import re
        async with aiohttp.ClientSession() as session:
            async with session.get(PINTEREST_START_VIDEO_URL, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    img_match = re.search(r'"image"\s*:\s*"([^"]+)"', html)
                    if not img_match:
                        img_match = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
                    if img_match:
                        img_url = img_match.group(1).replace('\\/', '/')
                        async with session.get(img_url) as img_resp:
                            if img_resp.status == 200:
                                img_data = await img_resp.read()
                                await update.message.reply_photo(
                                    photo=InputFile(io.BytesIO(img_data), filename="premium.jpg"),
                                    caption=welcome_text,
                                    parse_mode=constants.ParseMode.MARKDOWN,
                                    reply_markup=premium_menu_keyboard(),
                                )
                                return
    except: pass
    
    # ── Ultimate fallback: text only ──
    await update.message.reply_text(
        welcome_text,
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=premium_menu_keyboard(),
    )

async def emina_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    👥 GROUP MODE — /emina <song name and artist>
    In groups: searches and downloads the BEST match instantly, no selection.
    In DMs: works like /search with selection.
    """
    chat = update.effective_chat
    is_group = chat.type in (Chat.GROUP, Chat.SUPERGROUP)
    
    query = " ".join(context.args) if context.args else None
    if not query:
        if is_group:
            await update.message.reply_text(
                f"👥 *Group Mode Usage:*\n`/emina <song name> — artist`\n\n"
                f"Example: `/emina Changes — 2Pac`\n\n"
                f"🔊 I'll find & send the best match instantly!",
                parse_mode=constants.ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(
                f"🎵 `/emina <song name>` works great in both DMs and groups!\n\n"
                f"In *groups*, I send the music instantly.\n"
                f"In *DMs*, I show search results for you to pick.",
                parse_mode=constants.ParseMode.MARKDOWN,
            )
        return
    
    user_id = update.effective_user.id
    last = _user_cooldowns.get(user_id)
    if last and datetime.now() - last < timedelta(seconds=COOLDOWN_SECONDS):
        remain = COOLDOWN_SECONDS - (datetime.now() - last).seconds
        await update.message.reply_text(f"⏳ Cooldown: {remain}s")
        return
    _user_cooldowns[user_id] = datetime.now()
    
    if is_group:
        # ── GROUP MODE: Direct download ──
        status_msg = await update.message.reply_text(
            f"👥 *Emina Mode* — Searching: *{escape_markdown(query[:50])}*...",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        
        # Search for the best match
        results = await search_youtube(query, max_results=3)
        if not results:
            await status_msg.edit_text(
                "❌ *No results found.* Try being more specific!\n"
                "Example: `/emina Changes — 2Pac`",
                parse_mode=constants.ParseMode.MARKDOWN,
            )
            return
        
        # Auto-download the first (best) result
        best = results[0]
        video_id = best.get("id")
        if not video_id:
            await status_msg.edit_text("❌ Couldn't extract video ID.")
            return
        
        url = f"https://youtube.com/watch?v={video_id}"
        title = best.get("title", "Unknown")[:40]
        
        await status_msg.edit_text(
            f"👥 *Emina* → 🎵 *{escape_markdown(title)}*\n"
            f"⚡ Starting 10-method extraction...",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        
        await process_download(update, context, url, status_msg, "high")
        stats["group_downloads"] += 1
        
    else:
        # ── DM MODE: Show search results (same as /search) ──
        await update.message.chat.send_action(constants.ChatAction.TYPING)
        await update.message.reply_text(
            f"🔎 Searching: *{escape_markdown(query)}*...",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        
        results = await search_youtube(query)
        stats["total_searches"] += 1
        
        if not results:
            await update.message.reply_text("❌ No results found.")
            return
        
        context.user_data["search_results"] = results
        context.user_data["search_page"] = 0
        
        await update.message.reply_text(
            f"🎵 *{len(results)} tracks found* — Select one:",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=search_results_keyboard(results, 0),
        )

# ─── OTHER COMMAND HANDLERS ─────────────────────────────────────────────────

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pre-flight diagnostics"""
    chat = update.effective_chat
    if chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        await update.message.reply_text("🔍 Use /check in private chat for diagnostics.")
        return
    
    msg = await update.message.reply_text("🔍 Running pre-flight check...")
    results = await run_preflight_check()
    
    lines = [f"{Fancy.double_struck('PRE-FLIGHT CHECK')}\n"]
    
    checks = [
        ("JS Runtime (Deno/Node)", results["deno"], True),
        ("yt-dlp-ejs package", results["ytdlp_ejs"], True),
        ("yt-dlp version", bool(results["ytdlp_version"]), results["ytdlp_version"]),
        ("Cookies file", results["cookies"], False),
        ("FFmpeg", results["ffmpeg"], True),
    ]
    
    all_pass = True
    for name, passed, detail in checks:
        status = "✅" if passed else "❌"
        if isinstance(detail, str) and detail:
            lines.append(f"{status} {name}: `{detail}`")
        else:
            lines.append(f"{status} {name}")
        if not passed: all_pass = False
    
    lines.append("")
    if all_pass:
        lines.append(f"✅ {Fancy.bold_sans('ALL SYSTEMS NOMINAL')}")
    else:
        lines.append("⚠️ *Fixes needed:*")
        if not results["deno"]: lines.append("  ❌ Install: `winget install DenoLand.Deno`")
        if not results["ytdlp_ejs"]: lines.append("  ❌ Run: `pip install -U \"yt-dlp[default]\"`")
        if not results["ffmpeg"]: lines.append("  ❌ Install FFmpeg")
    
    await msg.edit_text("\n".join(lines), parse_mode=constants.ParseMode.MARKDOWN)

async def trending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """📈 Show trending YouTube Music"""
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    msg = await update.message.reply_text(
        f"{Fancy.premium_badge()}\n\n📈 Fetching *Trending Music*...",
        parse_mode=constants.ParseMode.MARKDOWN,
    )
    
    results = await search_youtube("trending music 2026 youtube", max_results=8)
    
    if not results:
        await msg.edit_text("❌ Couldn't fetch trending. Try /search pop music 2026")
        return
    
    context.user_data["search_results"] = results
    context.user_data["search_page"] = 0
    
    await msg.edit_text(
        f"📈 *Trending Now* — {len(results)} hot tracks",
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=search_results_keyboard(results, 0),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    is_group = chat.type in (Chat.GROUP, Chat.SUPERGROUP)
    
    text = (
        f"{Fancy.premium_badge()}\n\n"
        f"{Fancy.double_struck('PREMIUM HELP')}\n\n"
        f"**Commands:**\n"
        f"🔎 `/search <query>`  — Search & select from results\n"
        f"📥 `/dl <url>`  — Download from any YouTube URL\n"
        f"👥 `/emina <song>`  — **Group mode** → instant send\n"
        f"📈 `/trending`  — What's hot right now\n"
        f"✅ `/check`  — Run diagnostics\n"
        f"📊 `/stats`  — Bot statistics\n\n"
        f"{Fancy.header('10 ENGINES')}\n"
        f"⚡ M0: yt-dlp CLI  | 🚀 M1: yt-dlp Full\n"
        f"⚡ M2: Legacy  | 📡 M3: DASH\n"
        f"🔀 M4: Combined  | 🐍 M5: PytubeFix\n"
        f"🔗 M6: Invidious  | 🎼 M7: YT API\n"
        f"📺 M8: TV Client  | 🕵️ M9: Playwright\n\n"
        f"{Fancy.header('', '✦', 30)}\n"
    )
    
    if is_group:
        text += (
            f"\n👥 *Group Mode — /emina*\n"
            f"• Send `/emina <song name> — artist`\n"
            f"• I automatically download the best match\n"
            f"• No selection needed — instant delivery!\n"
            f"• For selectable results, use in DM.\n"
        )
    
    await update.message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    method_stats = "\n".join(
        f"{METHOD_EMOJIS.get(f'M{k}', '🔧')} M{k}: `{stats.get(f'method_m{k}', 0)}`" 
        for k in range(0, 10)
    )
    total_method = sum(stats.get(f"method_m{k}", 0) for k in range(0, 10))
    await update.message.reply_text(
        f"{Fancy.premium_badge()}\n\n"
        f"📊 *MusicMorph PRO Stats*\n\n"
        f"• Total Downloads: `{stats['total_downloads']}`\n"
        f"• Total Searches: `{stats['total_searches']}`\n"
        f"• Group Downloads: `{stats['group_downloads']}`\n"
        f"• Premium Users: `{stats['premium_users']}`\n"
        f"• Failures: `{stats['method_failures']}`\n\n"
        f"**Method Breakdown:**\n{method_stats}\n\n"
        f"Total via methods: `{total_method}`",
        parse_mode=constants.ParseMode.MARKDOWN,
    )

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        # In groups, redirect to /emina for instant downloads
        await update.message.reply_text(
            "👥 In groups, use `/emina <song name>` for instant music!\n"
            "`/search` is available in private chat for song selection.",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return
    
    query = " ".join(context.args) if context.args else None
    if not query and update.message and update.message.text:
        text = update.message.text.strip()
        if text.lower().startswith("/search"):
            query = text[7:].strip()
        else:
            query = text
    
    if not query:
        await update.message.reply_text(
            f"🔎 *Usage:* `/search <song name>`\n"
            f"Example: `/search tupac changes`\n\n"
            f"👥 In groups, use `/emina`",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return
    
    await update.message.chat.send_action(constants.ChatAction.TYPING)
    await update.message.reply_text(f"🔎 Searching: *{escape_markdown(query)}*...", parse_mode=constants.ParseMode.MARKDOWN)
    
    results = await search_youtube(query)
    stats["total_searches"] += 1
    
    if not results:
        await update.message.reply_text("❌ No results found.")
        return
    
    context.user_data["search_results"] = results
    context.user_data["search_page"] = 0
    await update.message.reply_text(
        f"🎵 *{len(results)} tracks found* — Select one:",
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=search_results_keyboard(results, 0),
    )

async def dl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = " ".join(context.args)
    if not url:
        await update.message.reply_text("📥 *Usage:* `/dl <YouTube URL>`", parse_mode=constants.ParseMode.MARKDOWN)
        return
    
    user_id = update.effective_user.id
    last = _user_cooldowns.get(user_id)
    if last and datetime.now() - last < timedelta(seconds=COOLDOWN_SECONDS):
        remain = COOLDOWN_SECONDS - (datetime.now() - last).seconds
        await update.message.reply_text(f"⏳ Cooldown: {remain}s")
        return
    
    msg = await update.message.reply_text(
        f"🚀 *Download* — Starting 10-method chain...",
        parse_mode=constants.ParseMode.MARKDOWN,
    )
    await process_download(update, context, url, msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-command messages"""
    chat = update.effective_chat
    is_group = chat.type in (Chat.GROUP, Chat.SUPERGROUP)
    text = update.message.text.strip()
    
    # YouTube URL → download
    yt_regex = r'(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/'
    if re.match(yt_regex, text):
        if is_group:
            await update.message.reply_text("👥 Send `/dl <url>` in DMs for downloads. Use `/emina <song>` for quick search!")
            return
        user_id = update.effective_user.id
        last = _user_cooldowns.get(user_id)
        if last and datetime.now() - last < timedelta(seconds=COOLDOWN_SECONDS):
            remain = COOLDOWN_SECONDS - (datetime.now() - last).seconds
            await update.message.reply_text(f"⏳ Cooldown: {remain}s")
            return
        msg = await update.message.reply_text("🚀 Processing URL...", parse_mode=constants.ParseMode.MARKDOWN)
        await process_download(update, context, text, msg)
        return
    
    # In groups: ignore random text (no accidental searches)
    if is_group:
        return
    
    # In DMs: treat as search
    context.args = [text]
    await search_cmd(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "cancel":
        await query.edit_message_text("❌ Cancelled."); return
    if data == "noop": return
    
    if data == "show_help":
        await query.edit_message_text(
            f"{Fancy.premium_badge()}\n\n"
            f"**Commands:**\n🔎 /search\n📥 /dl\n👥 /emina (group mode)\n📈 /trending\n✅ /check\n📊 /stats\n\n"
            f"**10 Engines:**\n⚡M0 CLI 🚀M1 Full ⚡M2 Legacy 📡M3 DASH 🔀M4 Combined\n🐍M5 PytubeFix 🔗M6 Inv 🎼M7 YT API 📺M8 TV 🕵️M9 Browser",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=premium_menu_keyboard(),
        ); return
    
    if data == "show_stats":
        total = sum(stats.get(f"method_m{k}", 0) for k in range(0, 10))
        await query.edit_message_text(
            f"📊 *Stats*\nDownloads: `{stats['total_downloads']}`\nSearches: `{stats['total_searches']}`\nGroup: `{stats['group_downloads']}`\nUsers: `{stats['premium_users']}`\nFailures: `{stats['method_failures']}`",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=premium_menu_keyboard(),
        ); return
    
    if data == "group_info":
        await query.edit_message_text(
            f"👥 *Group Mode — /emina*\n\n"
            f"Add me to a group and use:\n`/emina <song name> — artist`\n\n"
            f"✅ Finds best match automatically\n✅ Sends audio instantly\n✅ No selection needed\n\n"
            f"Example: `/emina Lose Yourself — Eminem`\n\n"
            f"*Selection mode* is only in DMs.",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=premium_menu_keyboard(),
        ); return
    
    if data == "trending":
        await trending_cmd(update, context); return
    
    if data == "new_search":
        await query.edit_message_text("🔎 Send me a song name or YouTube link!"); return
    
    if data == "back_to_results":
        results = context.user_data.get("search_results", [])
        page = context.user_data.get("search_page", 0)
        if not results: await query.edit_message_text("❌ No cached results."); return
        await query.edit_message_text(
            f"🎵 *Search Results* — Page {page+1}",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=search_results_keyboard(results, page),
        ); return
    
    # Pagination
    if data.startswith("page_"):
        page = int(data.split("_")[1])
        results = context.user_data.get("search_results", [])
        if not results: await query.edit_message_text("❌ No cached results."); return
        context.user_data["search_page"] = page
        await query.edit_message_text(
            f"🎵 *Search Results* — Page {page+1}",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=search_results_keyboard(results, page),
        ); return
    
    # Select song
    if data.startswith("select_"):
        parts = data.split("_", 2)
        video_id = parts[1]
        msg_id = query.message.message_id
        url = f"https://youtube.com/watch?v={video_id}"
        context.user_data.setdefault("pending_urls", {})[str(msg_id)] = url
        context.user_data["pending_dl_url"] = url
        await query.edit_message_text(
            "🎛 *Select Quality:*",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=quality_keyboard(url, msg_id=msg_id),
        ); return
    
    # Download quality
    if data.startswith("dl_"):
        parts = data.split("_", 2)
        quality_key = parts[1]
        msg_id_str = parts[2] if len(parts) > 2 else "0"
        pending = context.user_data.get("pending_urls", {})
        url = pending.get(msg_id_str) or context.user_data.get("pending_dl_url", "")
        if not url: await query.edit_message_text("❌ URL reference lost. Search again."); return
        user_id = update.effective_user.id
        last = _user_cooldowns.get(user_id)
        if last and datetime.now() - last < timedelta(seconds=COOLDOWN_SECONDS):
            remain = COOLDOWN_SECONDS - (datetime.now() - last).seconds
            await query.edit_message_text(f"⏳ Cooldown: {remain}s"); return
        await query.edit_message_text(
            f"🚀 Downloading at *{quality_key.upper()}*\n⚡ M0: yt-dlp CLI first...",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        await process_download(update, context, url, query.message, quality_key); return
    
    # Re-download
    if data.startswith("redl_"):
        video_id = data.split("_", 1)[1]
        url = f"https://youtube.com/watch?v={video_id}"
        msg_id = query.message.message_id
        context.user_data.setdefault("pending_urls", {})[str(msg_id)] = url
        context.user_data["pending_dl_url"] = url
        await query.edit_message_text(
            "🎛 *Select quality for re-download:*",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=quality_keyboard(url, msg_id=msg_id),
        ); return
    
    if data.startswith("delmsg_"):
        await query.edit_message_text("🗑 Deleted.")
        try: await query.message.delete()
        except: pass; return
    
    if data.startswith("info_"):
        video_id = data.split("_", 1)[1]
        await query.edit_message_text(
            f"ℹ️ *Video ID:* `{video_id}`\n📥 `/dl https://youtube.com/watch?v={video_id}`",
            parse_mode=constants.ParseMode.MARKDOWN,
        ); return

# ─── CORE DOWNLOAD PROCESSOR ───────────────────────────────────────────────

async def process_download(update, context, url, status_msg, quality_key=DEFAULT_QUALITY):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    _user_cooldowns[user_id] = datetime.now()
    progress_msg = status_msg
    
    async def update_progress(text):
        nonlocal progress_msg
        try: await progress_msg.edit_text(text, parse_mode=constants.ParseMode.MARKDOWN)
        except: pass
    
    try:
        result = await download_with_fallback(url, quality_key, progress_callback=update_progress)
        
        if result is None:
            await update_progress(
                "❌ *All 10 methods failed!*\n\n"
                "*Run `/check` to diagnose.*\n\n"
                "**Common fixes:**\n"
                "1️⃣ `winget install DenoLand.Deno`\n"
                "2️⃣ `pip install -U \"yt-dlp[default]\"`\n"
                "3️⃣ Export cookies.txt from browser\n"
                "4️⃣ Set `PO_TOKEN` environment variable"
            )
            return
        
        filepath, info, cover_data, method_id = result
        file_size = filepath.stat().st_size
        
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            await update_progress(f"⚠ File too large: {fmt_size(file_size)}. Limit: {MAX_FILE_SIZE_MB}MB")
            return
        
        title = info.get("title", "Unknown Track")
        uploader = info.get("uploader") or info.get("channel") or "Unknown"
        duration = info.get("duration", 0)
        emoji = METHOD_EMOJIS.get(method_id, "🔧")
        
        caption = (
            f"🎵 *{escape_markdown(title[:60])}*\n"
            f"👤 {escape_markdown(uploader[:30])}\n"
            f"⏱ {fmt_duration(duration)} | 📀 *{quality_key.upper()}* | 📦 {fmt_size(file_size)}\n"
            f"🔧 `{emoji} {method_id}` | ⚡ MusicMorph PRO"
        )
        
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.UPLOAD_DOCUMENT)
        
        with open(filepath, "rb") as f:
            await progress_msg.delete()
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=InputFile(f, filename=f"{safe_filename(title)}.mp3"),
                title=title[:60], performer=uploader[:60], duration=duration,
                caption=caption, parse_mode=constants.ParseMode.MARKDOWN,
                thumbnail=InputFile(io.BytesIO(cover_data), filename="cover.jpg") if cover_data else None,
                reply_markup=music_player_keyboard(info.get("id", "unknown"), method_id),
            )
        
        try: filepath.unlink(missing_ok=True)
        except: pass
        
    except Exception as e:
        log.error(f"process_download error: {traceback.format_exc()}")
        try: await update_progress(f"❌ *Fatal Error:* `{str(e)[:200]}`")
        except: pass

# ─── PERIODIC TASKS ─────────────────────────────────────────────────────────

async def cleanup_temp(interval=6):
    while True:
        await asyncio.sleep(interval * 3600)
        cutoff = datetime.now() - timedelta(hours=24)
        cleaned = 0
        for f in TEMP_DIR.glob("*"):
            try:
                if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                    f.unlink(missing_ok=True); cleaned += 1
            except: pass
        if cleaned: log.info(f"Cleaned {cleaned} temp files")

async def update_ytdlp(interval=12):
    while True:
        await asyncio.sleep(interval * 3600)
        try:
            proc = await asyncio.create_subprocess_exec("pip", "install", "-U", "yt-dlp", capture_output=True)
            await proc.wait()
            log.info("yt-dlp updated")
        except: pass

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print(f"""
╔════════════════════════════════════════════════════╗
║  {Fancy.bold_sans('MusicMorph PRO v4.0')}                ║
║  {Fancy.fraktur('10-Method Fallback Audio Extractor')}       ║
║  {Fancy.script('YouTube 2026 — Fully Compatible')}          ║
║  {Fancy.double_struck('PREMIUM EDITION')}                    ║
╚════════════════════════════════════════════════════╝
    """)
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Set BOT_TOKEN env var: export BOT_TOKEN='your_token'")
        return
    
    ensure_ytdlp_config()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(run_preflight_check())
    
    if not results["deno"]:
        print("❌ No JS runtime! Install: winget install DenoLand.Deno")
    if not results["ytdlp_ejs"]:
        print("❌ yt-dlp-ejs missing! Run: pip install -U \"yt-dlp[default]\"")
    if not results["ffmpeg"]:
        print("❌ FFmpeg not found! Install: winget install ffmpeg")
    
    for mod, name in [("pytubefix", "pytubefix"), ("ytmusicapi", "ytmusicapi"), ("playwright", "playwright")]:
        try: __import__(mod); print(f"✅ {mod} installed")
        except ImportError: print(f"ℹ️  {mod} optional: pip install {mod}")
    
    print(f"\n✅ Building MusicMorph PRO v4.0...")
    print(f"📹 Pinterest video URL: {PINTEREST_START_VIDEO_URL}")
    
    from telegram.ext import Application as TGApp
    
    app = TGApp.builder().token(BOT_TOKEN).concurrent_updates(True).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("dl", dl_cmd))
    app.add_handler(CommandHandler("emina", emina_cmd))
    app.add_handler(CommandHandler("trending", trending_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    loop.create_task(cleanup_temp())
    loop.create_task(update_ytdlp())
    
    print(f"✅ {Fancy.bold_sans('MusicMorph PRO v4.0')} running with {len(METHOD_CHAIN)} methods")
    print(f"👥 Group mode: /emina <song> for instant downloads")
    print(f"🎬 Premium intro video from Pinterest")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()