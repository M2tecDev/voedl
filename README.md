# VOE.sx Bulk Video Downloader — **voedl**

[![MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![aria2c](https://img.shields.io/badge/aria2c-supported-brightgreen)](https://aria2.github.io)
[![PyPI version](https://img.shields.io/pypi/v/voedl)](https://pypi.org/project/voedl)

> **voedl** is a high‑speed, command‑line utility that turns stream pages from **VOE.sx**, **jonathansociallike.com**, and **diananatureforeign.com** into direct MP4 downloads—parallelized and using multi‑connection transfers for maximum throughput.

---

## ✨ Features
- **Resolver chain**: VOE JSON API → `/e/` embed → `/download` stub → orbitcache MP4 (with correct Referer header to bypass 403).
- **Multi‑connection download** via [aria2c](https://aria2.github.io/) (default: 16 × 2 MiB per file).
- **Parallel downloads** with configurable worker pool (`-w` / `--workers`).
- **Progress bars**: Per‑file live bars via [`tqdm`](https://github.com/tqdm/tqdm) (`--progress`).
- **Debug mode** (`-d`): Logs detailed resolver and download steps to a timestamped logfile.
- **Single‑entry mode** (`-l`): Download one URL|Name directly without a list file.

---

## 🚀 Installation

### 1) From PyPI

```bash
pip install voedl
```

Visit the latest release on PyPI: https://pypi.org/project/voedl/

### 2) From source (no pip install required except dependencies)

```bash
# Clone the repository
git clone https://github.com/M2tecDev/voedl.git
cd voedl

# Install Python dependencies only
pip install -r requirements.txt

# Run directly from source
python voedl.py [options]
```

---

## ⚙️ Usage

Once installed via pip:

```bash
voedl [options]
```

If running from a local clone:

```bash
python voedl.py [options]
```

```text
Options:
  -h, --help            Show this help message and exit
  -f, --file FILE       Path to links list file (default: links.txt)
  -w, --workers N       Number of parallel download slots (default: 2)
  -c, --chunks N        Number of aria2c connections per file (default: 16)
  -l, --url ENTRY       Download a single "URL | Name" entry
  -d, --debug           Enable debug log (writes voedl_YYYYMMDD-HHMMSS.log)
      --progress        Show tqdm progress bars
```

---

## 🖥️ Examples

- **Download whole list** with 4 parallel workers and live bars:

  ```bash
  voedl -f links.txt -w 4 --progress
  ```

- **Single video** with 32 aria2c segments:

  ```bash
  voedl -l "https://voe.sx/v/XYZ123 | My Clip" -c 32 --progress
  ```

- **Default list** with debug log:

  ```bash
  voedl -d
  ```

---

## 📜 License

Released under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

<sub>SEO keywords: voe downloader, voe.sx downloader, jonathansociallike, orbitcache mp4, bulk video CLI.</sub>
