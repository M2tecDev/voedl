#!/usr/bin/env python3
"""
voedl.py – VOE.sx Bulk Video Downloader  (v2.5.1)

Features
--------
* Parallel file list (-w/--workers)
* Multi-connection per file via aria2c (-c/--chunks)
* Resolver chain: VOE → jonathansociallike → diananatureforeign → orbitcache
* Referer fix, HTML-entity decode, 403 workaround
* tqdm multi-line progress bars (--progress) — stdout stays *clean*
* Debug mode (-d) writes bulkdl_YYYYMMDD-HHMMSS.log
"""

from __future__ import annotations

import argparse, datetime as dt, html, logging, re, shutil, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup           # type: ignore
from yt_dlp import YoutubeDL            # type: ignore

try:
    from tqdm import tqdm               # type: ignore
    _TQDM = True
except ImportError:
    _TQDM = False

# ─────────────────────────── settings ────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept": "text/html,application/json",
}
TIMEOUT         = 15
ARIA_CHUNK_SIZE = "2M"

PAT_ORBIT  = re.compile(r"https?://[^\"']+orbitcache\.com/[^\"']+\.mp4[^\"']*")
_VOE_ID_RE = re.compile(r"https?://voe\.sx/(?:[evd]/)?([A-Za-z0-9]+)")

# ───────────────────── general helpers ───────────────────────────
def sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip()


def _req(method: str, url: str, *, referer: str | None = None, **kw):
    hdr = dict(HEADERS)
    if referer:
        hdr["Referer"] = referer
    kw.setdefault("headers", hdr)
    kw.setdefault("timeout", TIMEOUT)
    return requests.request(method, url, **kw)


def _follow_redirect(url: str) -> Optional[str]:
    try:
        r = _req("HEAD", url, allow_redirects=True)
        if r.status_code >= 400:
            r = _req("GET", url, allow_redirects=True, stream=True)
        if re.search(r"\.(mp4|mkv|webm|mov)(\?|$)", r.url):
            return r.url
    except Exception as exc:
        logging.debug("redirect fail %s → %s", url, exc)
    return None

# ───────────────────────── resolver ──────────────────────────────
def _extract_orbit(html_text: str) -> Optional[str]:
    m = PAT_ORBIT.search(html_text)
    return html.unescape(m.group(0)) if m else None


def _resolve_download_page(url: str) -> Optional[str]:
    vid = urlparse(url).path.strip("/").split("/")[0]
    ref = f"https://jonathansociallike.com/{vid}/download"
    try:
        page = _req("GET", url, referer=ref).text
    except Exception as exc:
        logging.debug("download-page fetch fail %s", exc)
        return None
    return _extract_orbit(page) or _follow_redirect(url)


def _voe_id(url: str) -> Optional[str]:
    m = _VOE_ID_RE.match(url)
    return m.group(1) if m else None


def _voe_api_mp4(vid: str) -> Optional[str]:
    for api in (f"https://voe.sx/api/video/{vid}",
                f"https://voe.sx/api/serve/file/{vid}"):
        try:
            data = _req("GET", api).json()
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for q in ("1080p", "720p", "480p", "360p"):
            cand = data.get("files", {}).get(q)
            if isinstance(cand, dict):
                cand = cand.get("url") or cand.get("src")
            if isinstance(cand, str):
                return cand
        for k in ("url", "src", "link"):
            cand = data.get(k)
            if isinstance(cand, str):
                return cand
    return None


def _voe_embed_mp4(vid: str) -> Optional[str]:
    try:
        html_text = _req("GET", f"https://voe.sx/e/{vid}").text
    except Exception:
        return None
    m = re.search(r"https?://[^\"']+\.(?:mp4|m3u8)[^\"']*", html_text)
    return m.group(0) if m else None


def _resolve_voe(url: str) -> str:
    vid = _voe_id(url)
    if not vid:
        return url
    for fn in (
        _voe_api_mp4,
        _voe_embed_mp4,
        lambda v: _resolve_download_page(
            f"https://diananatureforeign.com/{v}/download")
    ):
        mp4 = fn(vid)
        if mp4:
            return mp4
    return url


def resolve_url(url: str) -> str:
    url = url.strip()
    if re.search(r"\.(mp4|mkv|webm|mov)(\?|$)", url):
        return url
    if redir := _follow_redirect(url):
        return redir
    if "voe.sx" in url:
        return _resolve_voe(url)

    # direct jonathansociallike stub
    m = re.match(r"https?://jonathansociallike\.com/([A-Za-z0-9]+)", url)
    if m:
        vid = m.group(1)
        direct = _resolve_download_page(
            f"https://diananatureforeign.com/{vid}/download")
        if direct:
            return direct

    try:
        html_text = _req("GET", url).text
    except Exception as exc:
        logging.debug("fetch fail %s: %s", url, exc)
        return url

    soup = BeautifulSoup(html_text, "html.parser")
    btn = soup.find("a", href=re.compile(r"/download"))
    if btn and btn.has_attr("href"):
        stub = btn["href"]
        if not stub.startswith("http"):
            stub = urljoin(url, stub)
        if mp4 := _resolve_download_page(stub):
            return mp4

    iframe = soup.find("iframe", src=re.compile(r"voe\\.sx/(?:[evd]/)?"))
    if iframe and iframe.has_attr("src"):
        return _resolve_voe(iframe["src"])

    return _extract_orbit(html_text) or url

# ───────────────────── download helpers ─────────────────────────
def _headers_for(mp4_url: str) -> dict[str, str]:
    if "orbitcache.com" in mp4_url:
        vid = urlparse(mp4_url).path.split("/")[4].split("_")[0]
        return {"Referer": f"https://diananatureforeign.com/{vid}/download"}
    return {}


def _aria2_available() -> bool:
    return shutil.which("aria2c") is not None


def _bar(title: str):
    if _TQDM:
        return tqdm(desc=title[:50], unit="B", unit_scale=True, leave=True)
    return None


def _hook_for(bar):
    def hook(d):
        if bar is None:
            return
        if d.get("status") == "downloading":
            bar.total = d.get("total_bytes") or bar.total
            bar.update(d.get("downloaded_bytes") - bar.n)
        elif d.get("status") == "finished":
            bar.close()
    return hook


def _download(task: Tuple[str, str], args, dest: Path):
    url, title = task
    try:
        final = resolve_url(url)
    except Exception:
        logging.exception("resolver failed for %s", url)
        return

    bar = _bar(title) if args.progress else None

    class _Silent:                       # suppress yt-dlp chatter
        def debug(self, *_): ...
        info = warning = error = debug

    opts = {
        "outtmpl": str(dest / f"{sanitize(title)}.%(ext)s"),
        "quiet": True,
        "logger": _Silent() if args.progress and not args.debug else None,
        "no_warnings": True,
        "retries": 3,
        "progress_hooks": [_hook_for(bar)],
        "http_headers": _headers_for(final),
    }

    # use aria2c only when *no* progress bars requested
    if _aria2_available() and not args.progress:
        opts.update({
            "external_downloader": "aria2c",
            "external_downloader_args": [
                "-x", str(args.chunks),
                "-s", str(args.chunks),
                "-k", ARIA_CHUNK_SIZE,
                "--file-allocation=none",
                "--summary-interval=0",
            ],
        })

    if not args.progress or args.debug:
        logging.info("Final URL → %s", final)
    with YoutubeDL(opts) as ydl:
        ydl.download([final])
    if bar:
        bar.close()

# ───────────────────────── cli helpers ──────────────────────────
def _parse_line(line: str) -> Optional[Tuple[str, str]]:
    if "|" not in line:
        return None
    u, n = (x.strip() for x in line.split("|", 1))
    return (u, n) if u and n else None


def _load_list(path: Path) -> List[Tuple[str, str]]:
    tasks: List[Tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        if parsed := _parse_line(raw):
            tasks.append(parsed)
        else:
            logging.warning("Skip malformed line: %s", raw)
    return tasks

# ──────────────────────────── main ──────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(
        prog="voedl",
        description="High-speed bulk video downloader for VOE.sx",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("-f", "--file", default="links.txt",
                    help="links list file (url | name)")
    ap.add_argument("-w", "--workers", type=int, default=2,
                    help="parallel download slots")
    ap.add_argument("-c", "--chunks", type=int, default=16,
                    help="aria2c connections per file")
    ap.add_argument("-l", "--url", metavar="URL|NAME",
                    help="single entry \"url | Name\"")
    ap.add_argument("-d", "--debug", action="store_true",
                    help="write debug logfile")
    ap.add_argument("--progress", action="store_true",
                    help="show tqdm progress bars")
	ap.add_argument("-o", "--output", default=".",
                    help="download directory (default: current working dir)")

    if len(sys.argv) == 1:
        ap.print_help(sys.stderr)
        sys.exit(0)

    args = ap.parse_args()
    lvl = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=lvl,
                        format="%(asctime)s | %(levelname)5s | %(message)s",
                        datefmt="%H:%M:%S")
    if args.debug:
        lf = Path(__file__).with_name(
            f"bulkdl_{dt.datetime.now():%Y%m%d-%H%M%S}.log")
        logging.getLogger().addHandler(logging.FileHandler(lf, encoding="utf-8"))
        logging.info("Debug log → %s", lf)

    dest = Path(args.output).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)        # legt Ordner an, falls nötig
    logging.info("Saving downloads to %s", dest)

    tasks: List[Tuple[str, str]]
    if args.url:
        single = _parse_line(args.url)
        if not single:
            ap.error("-l entry must be  URL | Name")
        tasks = [single]
    else:
        src = Path(args.file)
        if not src.exists():
            ap.error(f"links file '{src}' not found")
        tasks = _load_list(src)
        if not tasks:
            logging.warning("List empty – nothing to do.")
            return

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_download, t, args, dest) for t in tasks]
        for f in as_completed(futures):
            f.result()

    print("\nAll tasks completed.")


if __name__ == "__main__":
    main()
