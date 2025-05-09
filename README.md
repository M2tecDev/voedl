# VOE.sx Bulk Video Downloader — **voedl**

[![MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![aria2c](https://img.shields.io/badge/aria2c-supported-brightgreen)](https://aria2.github.io)
[![Latest release](https://img.shields.io/github/v/release/M2tecDev/voedl)](https://github.com/M2tecDev/voedl/releases)

> **voedl** (*VOE Downloader*) turns stream pages from **VOE.sx** and its mirrors (jonathansociallike / diananatureforeign) into direct MP4 files—fast & in parallel.


## ✨ Features
* **Resolver chain** — VOE JSON → `/e/` embed → `/download` stub → orbitcache MP4 (w/ Referer fix).
* **Multi‑connection** download via `aria2c` (16 × 2 MiB by default).
* **Parallel files** with a worker pool (`-w/--workers`).
* **tqdm** multi‑line progress bars (`--progress`).
* **Debug mode** (`-d`) writes a timestamped log.

## 🚀 Quick start
```bash
git clone https://github.com/M2tecDev/voedl.git
cd voedl
python -m pip install -U yt-dlp requests beautifulsoup4
sudo apt install aria2     # speed boost   (brew install aria2 on macOS)
python -m pip install tqdm # pretty bars   (optional)

python bulkdl.py -l "https://voe.sx/v/abc123 | Test Video" --progress
```

## ⚙️ CLI
```text
python bulkdl.py [options]

-h, --help            print help
-f, --file FILE       links list (default: links.txt)
-w, --workers N       parallel download slots
-c, --chunks  N       aria2c connections per file
-l, --url ENTRY       download one  "url | Name" entry
-d, --debug           write debug logfile
    --progress        show tqdm bars (requires pkg 'tqdm')
```

### links.txt example
```
https://jonathansociallike.com/9brhleia0cov | The Boss Baby (2017)
https://voe.sx/v/XYZabc123                    | Movie 2
```

## 🖥️ Examples
| Command | Purpose |
|---------|---------|
| `python bulkdl.py -f links.txt -w 4 --progress` | Download whole list with 4 workers + bars |
| `python bulkdl.py -l "https://voe.sx/v/XYZ | Clip"` | Grab single link |
| `python bulkdl.py -d` | Run default list & save debug log |

## 🤝 Contributing
Pull requests welcome – please run `black bulkdl.py` before committing.

## 📜 License
MIT – see [LICENSE](LICENSE).

<sub>SEO keywords: voe downloader, voe.sx video download script, orbitcache mp4, jonathansociallike download button.</sub>
