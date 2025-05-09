# Bulk Video Downloader

Bulk Video Downloader is a high‑speed command‑line utility that turns “stream
page” links (VOE, jonathansociallike, diananatureforeign) into real MP4 files
on disk.  It resolves the full redirect chain, injects required *Referer*
headers to bypass 403 errors and uses **aria2c** for multi‑connection
downloads.  
Multiple files can be fetched in parallel and each transfer can display its own
`tqdm` progress bar.

---

## Features

* **Resolver chain** – VOE JSON API → `/e/` embed → `/download` stub  
  → orbitcache direct MP4.
* **Automatic HTML‑entity decoding** (`&amp;` → `&`).
* **403 workaround** – correct *Referer* header for orbitcache.com.
* **Multi‑connection** download (default 16 × 2 MiB) via aria2c
  *(falls back to yt‑dlp’s internal downloader if aria2c is missing)*.
* **Parallel downloads** with configurable worker pool.
* **tqdm multi‑line progress bars** (`--progress`).
* **Debug mode** writes an easy‑to‑share log for troubleshooting.

---

## Installation

```bash
# 1. Clone or download this repo
git clone https://github.com/M2tecDev/voedl.git
cd voedl

# 2. Python deps
python -m pip install -U yt-dlp requests beautifulsoup4

# 3. (optional) Speed boost
sudo apt install aria2      # Debian/Ubuntu
# or
brew install aria2          # macOS

# 4. (optional) Pretty progress bars
python -m pip install tqdm
```

Test the script:

```bash
python voedl.py -l "https://jonathansociallike.com/abc123 | Test Video" --progress
```

---

## Usage

```text
python voedl.py [options]

Options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  links list (default: links.txt)
  -w N,   --workers N   parallel download slots (default: 2)
  -c N,   --chunks N    aria2c connections per file (default: 16)
  -l ENTRY, --url ENTRY download a single "url | Name" entry
  -d, --debug           enable debug log (voedl_YYYYMMDD-HHMMSS.log)
      --progress        show tqdm progress bars
```

### Link list format (`links.txt`)

```
https://jonathansociallike.com/9brhleia0cov | The Boss Baby (2017)
https://voe.sx/v/XYZabc123                | Movie 2
```

Blank lines and lines starting with `#` are ignored.

---

## Examples

*Download an entire list with 4 parallel workers and fancy progress bars:*

```bash
python voedl.py -f links.txt -w 4 --progress
```

*Download one video quickly with 32 aria2c segments:*

```bash
python voedl.py -l "https://voe.sx/v/XYZ123 | Single Test" -c 32 --progress
```

*Generate a debug log while running the default list:*

```bash
python voedl.py -d
```

The log is saved next to the script, e.g. `voedl_20250508-221530.log`.

---

## License

MIT License – see [`LICENSE`](LICENSE) for the full text.

---

## Contributing

Pull requests are welcome! Feel free to submit issues or suggestions.

1. Fork → Branch → PR.
2. Run `black voedl.py` before committing.
3. Ensure the link resolver chain still passes quick tests (`links_test.txt`).

---

## Acknowledgements

* **yt‑dlp** – the best general‑purpose video downloader.  
* **aria2**  – ultra‑fast, multi‑source CLI downloader.  
* **tqdm**   – simple, elegant progress bars.
