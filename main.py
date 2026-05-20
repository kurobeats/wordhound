from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit

import requests
import tldextract
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

VERSION = "0.1.0"
EMAIL_REGEX = re.compile(r"\b[-A-Z0-9._%+]+@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\b", re.I)
JS_REDIRECT_REGEX = re.compile(r"location\.href\s*=\s*[\"\']([^\"\']+)[\"\']", re.I)
META_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "xls",
    "xlsx",
    "odt",
    "ods",
    "odp",
}
SKIP_EXTENSIONS = {
    "zip",
    "gz",
    "bz2",
    "png",
    "gif",
    "jpg",
    "jpeg",
    "webp",
    "svg",
    "ico",
    "woff",
    "woff2",
    "ttf",
    "eot",
}


@dataclass
class CrawlConfig:
    url: str
    depth: int = 2
    min_word_length: int = 3
    max_word_length: int | None = None
    offsite: bool = False
    exclude_paths: set[str] = field(default_factory=set)
    allowed_regex: re.Pattern[str] | None = None
    output_file: str | None = None
    email_file: str | None = None
    meta_file: str | None = None
    user_agent: str | None = None
    no_words: bool = False
    groups: int = 0
    lowercase: bool = False
    with_numbers: bool = False
    convert_umlauts: bool = False
    include_meta: bool = False
    include_email: bool = False
    show_count: bool = False
    verbose: bool = False
    debug: bool = False
    keep: bool = False
    keep_js: bool = False
    keep_css: bool = False
    meta_temp_dir: str = tempfile.gettempdir()
    capture_paths: bool = False
    capture_subdomains: bool = False
    capture_domain: bool = False
    auth_type: str | None = None
    auth_user: str | None = None
    auth_pass: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    proxy_host: str | None = None
    proxy_port: int = 8080
    proxy_username: str | None = None
    proxy_password: str | None = None
    timeout: int = 20


class WordhoundCrawler:
    def __init__(self, cfg: CrawlConfig):
        self.cfg = cfg
        self.words: Counter[str] = Counter()
        self.group_words: Counter[str] = Counter()
        self.emails: set[str] = set()
        self.meta_values: set[str] = set()
        self.session = requests.Session()
        self.seen: set[str] = set()
        self.seed = self._normalize_url(cfg.url)
        self.seed_parts = urlparse(self.seed)

        if cfg.user_agent:
            self.session.headers["User-Agent"] = cfg.user_agent
        self.session.headers.update(cfg.headers)

        if cfg.auth_type:
            if cfg.auth_type == "basic":
                self.session.auth = HTTPBasicAuth(cfg.auth_user or "", cfg.auth_pass or "")
            elif cfg.auth_type == "digest":
                self.session.auth = HTTPDigestAuth(cfg.auth_user or "", cfg.auth_pass or "")

        if cfg.proxy_host:
            auth = ""
            if cfg.proxy_username and cfg.proxy_password:
                auth = f"{cfg.proxy_username}:{cfg.proxy_password}@"
            proxy_url = f"http://{auth}{cfg.proxy_host}:{cfg.proxy_port}"
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }

    def crawl(self) -> None:
        queue: deque[tuple[str, int, str | None]] = deque([(self.seed, 0, None)])

        while queue:
            current, depth, prior = queue.popleft()
            normalized = self._normalize_url(current)
            if normalized in self.seen:
                continue
            self.seen.add(normalized)

            if self.cfg.verbose:
                if prior:
                    print(f"Visiting: {normalized} referred from {prior}", file=sys.stderr)
                else:
                    print(f"Visiting: {normalized}", file=sys.stderr)

            response = self._fetch(normalized)
            if response is None:
                continue

            content_type = response.headers.get("Content-Type", "")
            self._process_page(normalized, response, content_type)

            if depth >= self.cfg.depth:
                continue

            links = self._extract_links(normalized, response, content_type)
            for link in links:
                if self._should_follow(link):
                    queue.append((link, depth + 1, normalized))

    def _fetch(self, url: str) -> requests.Response | None:
        try:
            response = self.session.get(url, timeout=self.cfg.timeout, allow_redirects=True)
            return response
        except requests.RequestException as exc:
            if self.cfg.verbose:
                print(f"Failed to fetch {url}: {exc}", file=sys.stderr)
            return None

    def _process_page(self, url: str, response: requests.Response, content_type: str) -> None:
        ext = self._url_extension(url)

        if self.cfg.keep:
            self._keep_download(url, response.content)

        if self.cfg.include_email:
            self._extract_emails(response.text)

        if self.cfg.capture_paths:
            self._capture_path_components(url)
        if self.cfg.capture_subdomains:
            self._capture_subdomain_components(url)
        if self.cfg.capture_domain:
            self._capture_domain(url)

        if "html" not in content_type.lower() and "xml" not in content_type.lower():
            if self.cfg.include_meta and ext in META_EXTENSIONS:
                self._extract_document_meta(ext, response.content)
            return

        soup = BeautifulSoup(response.text, "html.parser")

        if not self.cfg.keep_js:
            for tag in soup.find_all("script"):
                tag.decompose()
        if not self.cfg.keep_css:
            for tag in soup.find_all("style"):
                tag.decompose()

        if self.cfg.include_email:
            self._extract_mailto(soup)

        if self.cfg.include_meta:
            self._extract_html_meta(soup)

        text_parts: list[str] = [soup.get_text(" ", strip=True)]
        text_parts.extend(self._extract_attributes(soup, ["alt", "title"]))
        page_text = " ".join(part for part in text_parts if part)

        if self.cfg.include_email:
            self._extract_emails(page_text)

        js_redirects = JS_REDIRECT_REGEX.findall(response.text)
        for rel in js_redirects:
            target = urljoin(url, rel)
            if self._should_follow(target):
                if self.cfg.debug:
                    print(f"JavaScript redirect found: {target}", file=sys.stderr)

        if not self.cfg.no_words:
            tokens = self._tokenize(page_text)
            self._add_words(tokens)
            self._add_groups(tokens)

    def _extract_links(self, base_url: str, response: requests.Response, content_type: str) -> set[str]:
        links: set[str] = set()
        if "html" not in content_type.lower() and "xml" not in content_type.lower():
            return links

        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("#"):
                continue
            full = urljoin(base_url, href)
            links.add(self._normalize_url(full))

        for rel in JS_REDIRECT_REGEX.findall(response.text):
            links.add(self._normalize_url(urljoin(base_url, rel)))

        return links

    def _should_follow(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return False

        ext = self._url_extension(url)
        if ext in SKIP_EXTENSIONS:
            return False

        if not self.cfg.offsite:
            if (
                parsed.scheme != self.seed_parts.scheme
                or parsed.hostname != self.seed_parts.hostname
                or (parsed.port or self._default_port(parsed.scheme))
                != (self.seed_parts.port or self._default_port(self.seed_parts.scheme))
            ):
                return False

        req_uri = parsed.path or "/"
        if parsed.query:
            req_uri = f"{req_uri}?{parsed.query}"

        if req_uri in self.cfg.exclude_paths:
            return False

        if self.cfg.allowed_regex and not self.cfg.allowed_regex.search(parsed.path or "/"):
            return False

        normalized = self._normalize_url(url)
        if normalized in self.seen:
            return False

        return True

    def _add_words(self, tokens: list[str]) -> None:
        for token in tokens:
            if len(token) < self.cfg.min_word_length:
                continue
            if self.cfg.max_word_length is not None and len(token) > self.cfg.max_word_length:
                continue
            self.words[token] += 1

    def _add_groups(self, tokens: list[str]) -> None:
        n = self.cfg.groups
        if n <= 0:
            return

        window: deque[str] = deque(maxlen=n)
        for token in tokens:
            if len(token) < self.cfg.min_word_length:
                continue
            if self.cfg.max_word_length is not None and len(token) > self.cfg.max_word_length:
                continue
            window.append(token)
            if len(window) == n:
                self.group_words[" ".join(window)] += 1

    def _tokenize(self, text: str) -> list[str]:
        work = text
        if self.cfg.convert_umlauts:
            work = work.translate(
                str.maketrans(
                    {
                        "ä": "ae",
                        "ö": "oe",
                        "ü": "ue",
                        "ß": "ss",
                        "Ä": "Ae",
                        "Ö": "Oe",
                        "Ü": "Ue",
                    }
                )
            )

        if self.cfg.lowercase:
            work = work.lower()

        if self.cfg.with_numbers:
            work = re.sub(r"[^0-9A-Za-z]+", " ", work)
        else:
            work = re.sub(r"[^A-Za-z]+", " ", work)

        return [tok for tok in work.split() if tok]

    def _extract_mailto(self, soup: BeautifulSoup) -> None:
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                value = href[7:].split("?")[0].strip()
                if value:
                    self.emails.add(value)

    def _extract_emails(self, text: str) -> None:
        for match in EMAIL_REGEX.findall(text or ""):
            self.emails.add(match)

    def _extract_html_meta(self, soup: BeautifulSoup) -> None:
        for name in ("description", "keywords", "author", "creator"):
            for tag in soup.find_all("meta"):
                n = (tag.get("name") or "").strip().lower()
                if n == name:
                    content = (tag.get("content") or "").strip()
                    if content:
                        for value in re.split(r"[,;]", content):
                            v = value.strip()
                            if v:
                                self.meta_values.add(v)

    def _extract_document_meta(self, ext: str, raw: bytes) -> None:
        if ext != "pdf":
            return
        try:
            from pypdf import PdfReader
        except Exception:
            return

        tmp = Path(tempfile.gettempdir()) / "wordhound_meta.pdf"
        try:
            tmp.write_bytes(raw)
            reader = PdfReader(str(tmp))
            info = reader.metadata or {}
            for key in ("/Author", "/Creator", "/Producer"):
                value = info.get(key)
                if value and isinstance(value, str):
                    self.meta_values.add(value.strip())
        except Exception:
            if self.cfg.debug:
                print("Failed to read PDF metadata", file=sys.stderr)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

    def _capture_path_components(self, url: str) -> None:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        for part in parts:
            clean = re.sub(r"\?.*$", "", part)
            clean = re.sub(r"\.[^.]*$", "", clean)
            clean = re.sub(r"[^A-Za-z0-9_-]", "", clean)
            self._add_capture_token(clean)

    def _capture_subdomain_components(self, url: str) -> None:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if not host:
            return

        extracted = tldextract.extract(host)
        suffix = ".".join(p for p in [extracted.domain, extracted.suffix] if p)
        if not suffix:
            return

        full_parts = host.split(".")
        suffix_parts = suffix.split(".")
        count = max(len(full_parts) - len(suffix_parts), 0)
        for i in range(count):
            self._add_capture_token(full_parts[i])

    def _capture_domain(self, url: str) -> None:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if not host:
            return

        extracted = tldextract.extract(host)
        domain = ".".join(p for p in [extracted.domain, extracted.suffix] if p)
        self._add_capture_token(domain)

    def _add_capture_token(self, token: str) -> None:
        if not token:
            return
        if len(token) < self.cfg.min_word_length:
            return
        if self.cfg.max_word_length is not None and len(token) > self.cfg.max_word_length:
            return

        if self.cfg.lowercase:
            token = token.lower()
        self.words[token] += 1

    def _extract_attributes(self, soup: BeautifulSoup, attrs: Iterable[str]) -> list[str]:
        results: list[str] = []
        for attr in attrs:
            for tag in soup.find_all(attrs={attr: True}):
                value = (tag.get(attr) or "").strip()
                if value:
                    results.append(value)
        return results

    def _keep_download(self, url: str, data: bytes) -> None:
        out_dir = Path(self.cfg.meta_temp_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        parsed = urlsplit(url)
        name = Path(parsed.path).name or "index.html"
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
        target = out_dir / safe
        try:
            target.write_bytes(data)
        except OSError:
            if self.cfg.verbose:
                print(f"Unable to save {target}", file=sys.stderr)

    @staticmethod
    def _url_extension(url: str) -> str:
        path = urlparse(url).path
        if "." not in path:
            return ""
        return path.rsplit(".", 1)[1].lower()

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        host = parsed.hostname.lower() if parsed.hostname else ""
        port = parsed.port

        if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
            netloc = f"{host}:{port}"
        else:
            netloc = host

        path = parsed.path or "/"
        return urlunsplit((scheme, netloc, path, parsed.query, ""))

    @staticmethod
    def _default_port(scheme: str) -> int:
        return 443 if scheme == "https" else 80


def _open_output(path: str | None):
    if not path:
        return sys.stdout, False
    fh = open(path, "w", encoding="utf-8")
    return fh, True


def _parse_headers(values: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for value in values:
        if ":" not in value:
            raise ValueError(f"Invalid header: {value}. Expected name:value")
        name, content = value.split(":", 1)
        headers[name.strip()] = content.strip()
    return headers


def _load_excludes(path: str | None) -> set[str]:
    excludes: set[str] = set()
    if not path:
        return excludes
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped:
                excludes.add(stripped)
    return excludes


def _sorted_items(counter: Counter[str]) -> list[tuple[str, int]]:
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def _print_counter(items: list[tuple[str, int]], out, show_count: bool) -> None:
    for word, count in items:
        if show_count:
            out.write(f"{word}, {count}\n")
        else:
            out.write(f"{word}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wordhound", description="Custom Word List generator (Python)")

    parser.add_argument("url", help="The site to spider")
    parser.add_argument("-k", "--keep", action="store_true", help="Keep downloaded files")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Depth to spider (default: 2)")
    parser.add_argument("-m", "--min_word_length", type=int, default=3, help="Minimum word length")
    parser.add_argument("-x", "--max_word_length", type=int, help="Maximum word length")
    parser.add_argument("-o", "--offsite", action="store_true", help="Follow offsite links")
    parser.add_argument("--exclude", help="File containing paths to exclude")
    parser.add_argument("--allowed", help="Regex pattern paths must match")
    parser.add_argument("-w", "--write", dest="output_file", help="Write output to file")
    parser.add_argument("-u", "--ua", dest="user_agent", help="User-Agent string")
    parser.add_argument("-n", "--no-words", action="store_true", help="Do not output wordlist")
    parser.add_argument("-g", "--groups", type=int, default=0, help="Output word groups of size N")
    parser.add_argument("--lowercase", action="store_true", help="Lowercase parsed words")
    parser.add_argument("--with-numbers", action="store_true", help="Include words with digits")
    parser.add_argument("--convert-umlauts", action="store_true", help="Convert common umlauts")

    parser.add_argument("-a", "--meta", dest="include_meta", action="store_true", help="Include metadata")
    parser.add_argument("--meta_file", help="Output metadata to file")
    parser.add_argument("-e", "--email", dest="include_email", action="store_true", help="Include email addresses")
    parser.add_argument("--email_file", help="Output emails to file")
    parser.add_argument("--meta-temp-dir", default=tempfile.gettempdir(), help="Temp directory for saved files")

    parser.add_argument("-c", "--count", action="store_true", help="Show count for each word")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--keep-js", action="store_true", help="Keep JavaScript text")
    parser.add_argument("--keep-css", action="store_true", help="Keep CSS text")

    parser.add_argument("--auth_type", choices=["basic", "digest"], help="Authentication type")
    parser.add_argument("--auth_user", help="Authentication username")
    parser.add_argument("--auth_pass", help="Authentication password")

    parser.add_argument("--proxy_host", help="Proxy host")
    parser.add_argument("--proxy_port", type=int, default=8080, help="Proxy port")
    parser.add_argument("--proxy_username", help="Proxy username")
    parser.add_argument("--proxy_password", help="Proxy password")

    parser.add_argument("-H", "--header", action="append", default=[], help="Header in name:value format")

    parser.add_argument("--capture-paths", action="store_true", help="Capture URL path components")
    parser.add_argument("--capture-subdomains", action="store_true", help="Capture subdomain components")
    parser.add_argument("--capture-domain", action="store_true", help="Capture main domain")
    parser.add_argument("--capture-url-structure", action="store_true", help="Capture domain, paths, and subdomains")
    parser.add_argument("--version", action="version", version=f"wordhound {VERSION}")

    return parser


def _normalize_input_url(url: str) -> str:
    if re.match(r"^https?://", url, re.I):
        return url
    return f"http://{url}"


def parse_args(argv: list[str]) -> CrawlConfig:
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.depth < 0:
        parser.error("--depth must be >= 0")
    if ns.min_word_length < 1:
        parser.error("--min_word_length must be >= 1")
    if ns.max_word_length is not None and ns.max_word_length < 1:
        parser.error("--max_word_length must be >= 1")
    if ns.groups < 0:
        parser.error("--groups must be >= 0")

    if ns.auth_type and (not ns.auth_user or not ns.auth_pass):
        parser.error("--auth_type requires --auth_user and --auth_pass")
    if not ns.auth_type and (ns.auth_user or ns.auth_pass):
        parser.error("--auth_user/--auth_pass require --auth_type")

    if not os.path.isdir(ns.meta_temp_dir):
        parser.error("--meta-temp-dir must point to an existing directory")
    if not os.access(ns.meta_temp_dir, os.W_OK):
        parser.error("--meta-temp-dir must be writable")

    try:
        headers = _parse_headers(ns.header)
    except ValueError as exc:
        parser.error(str(exc))

    allowed_regex = re.compile(ns.allowed) if ns.allowed else None
    exclude_paths = _load_excludes(ns.exclude)

    capture_paths = ns.capture_paths
    capture_subdomains = ns.capture_subdomains
    capture_domain = ns.capture_domain
    if ns.capture_url_structure:
        capture_paths = True
        capture_subdomains = True
        capture_domain = True

    return CrawlConfig(
        url=_normalize_input_url(ns.url),
        depth=ns.depth,
        min_word_length=ns.min_word_length,
        max_word_length=ns.max_word_length,
        offsite=ns.offsite,
        exclude_paths=exclude_paths,
        allowed_regex=allowed_regex,
        output_file=ns.output_file,
        email_file=ns.email_file,
        meta_file=ns.meta_file,
        user_agent=ns.user_agent,
        no_words=ns.no_words,
        groups=ns.groups,
        lowercase=ns.lowercase,
        with_numbers=ns.with_numbers,
        convert_umlauts=ns.convert_umlauts,
        include_meta=ns.include_meta,
        include_email=ns.include_email,
        show_count=ns.count,
        verbose=ns.verbose,
        debug=ns.debug,
        keep=ns.keep,
        keep_js=ns.keep_js,
        keep_css=ns.keep_css,
        meta_temp_dir=ns.meta_temp_dir,
        capture_paths=capture_paths,
        capture_subdomains=capture_subdomains,
        capture_domain=capture_domain,
        auth_type=ns.auth_type,
        auth_user=ns.auth_user,
        auth_pass=ns.auth_pass,
        headers=headers,
        proxy_host=ns.proxy_host,
        proxy_port=ns.proxy_port,
        proxy_username=ns.proxy_username,
        proxy_password=ns.proxy_password,
    )


def _build_text_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wordhound text", description="Build a wordlist from a local text file")
    parser.add_argument("input", help="Path to input text file")
    parser.add_argument("-w", "--write", dest="output_file", help="Write output to file")
    parser.add_argument("-m", "--min_word_length", type=int, default=3, help="Minimum word length")
    parser.add_argument("-x", "--max_word_length", type=int, help="Maximum word length")
    parser.add_argument("--lowercase", action="store_true", help="Lowercase parsed words")
    parser.add_argument("--with-numbers", action="store_true", help="Include words with digits")
    parser.add_argument("--convert-umlauts", action="store_true", help="Convert common umlauts")
    parser.add_argument("-c", "--count", action="store_true", help="Show count for each word")
    return parser


def _build_pdf_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wordhound pdf", description="Build a wordlist from a local PDF file")
    parser.add_argument("input", help="Path to input PDF file")
    parser.add_argument("-w", "--write", dest="output_file", help="Write output to file")
    parser.add_argument("-m", "--min_word_length", type=int, default=3, help="Minimum word length")
    parser.add_argument("-x", "--max_word_length", type=int, help="Maximum word length")
    parser.add_argument("--lowercase", action="store_true", help="Lowercase parsed words")
    parser.add_argument("--with-numbers", action="store_true", help="Include words with digits")
    parser.add_argument("--convert-umlauts", action="store_true", help="Convert common umlauts")
    parser.add_argument("-c", "--count", action="store_true", help="Show count for each word")
    return parser


def _build_reddit_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wordhound reddit", description="Build a wordlist from Reddit threads")
    parser.add_argument("subreddits", nargs="+", help="One or more subreddit names")
    parser.add_argument("-w", "--write", dest="output_file", help="Write output to file")
    parser.add_argument("-m", "--min_word_length", type=int, default=3, help="Minimum word length")
    parser.add_argument("-x", "--max_word_length", type=int, help="Maximum word length")
    parser.add_argument("--lowercase", action="store_true", help="Lowercase parsed words")
    parser.add_argument("--with-numbers", action="store_true", help="Include words with digits")
    parser.add_argument("--convert-umlauts", action="store_true", help="Convert common umlauts")
    parser.add_argument("-c", "--count", action="store_true", help="Show count for each word")
    parser.add_argument("--posts", type=int, default=25, help="Max posts to fetch per subreddit")
    parser.add_argument("--comments", type=int, default=50, help="Max comments to fetch per thread")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument("--user-agent", default="wordhound/0.1 (+https://github.com/kurobeats/wordhound)")
    return parser


def _build_aggregate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wordhound aggregate", description="Aggregate words from one or more files")
    parser.add_argument("inputs", nargs="+", help="Input files to aggregate")
    parser.add_argument("-w", "--write", dest="output_file", help="Write output to file")
    parser.add_argument("-c", "--count", action="store_true", help="Show count for each word")
    parser.add_argument("--lowercase", action="store_true", help="Lowercase words before aggregation")
    return parser


def _tokenize_text(text: str, *, lowercase: bool, with_numbers: bool, convert_umlauts: bool) -> list[str]:
    work = text
    if convert_umlauts:
        work = work.translate(
            str.maketrans(
                {
                    "ä": "ae",
                    "ö": "oe",
                    "ü": "ue",
                    "ß": "ss",
                    "Ä": "Ae",
                    "Ö": "Oe",
                    "Ü": "Ue",
                }
            )
        )

    if lowercase:
        work = work.lower()

    if with_numbers:
        work = re.sub(r"[^0-9A-Za-z]+", " ", work)
    else:
        work = re.sub(r"[^A-Za-z]+", " ", work)

    return [tok for tok in work.split() if tok]


def _count_tokens(tokens: list[str], min_len: int, max_len: int | None) -> Counter[str]:
    words: Counter[str] = Counter()
    for token in tokens:
        if len(token) < min_len:
            continue
        if max_len is not None and len(token) > max_len:
            continue
        words[token] += 1
    return words


def _write_words(counter: Counter[str], output_file: str | None, show_count: bool) -> None:
    out, should_close = _open_output(output_file)
    try:
        _print_counter(_sorted_items(counter), out, show_count)
    finally:
        if should_close:
            out.close()


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError("PDF mode requires pypdf. Install dependencies from requirements.txt") from exc

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text:
            parts.append(text)
    return "\n".join(parts)


def _extract_comment_bodies(node) -> Iterable[str]:
    if not isinstance(node, dict):
        return []

    data = node.get("data")
    if not isinstance(data, dict):
        return []

    body = data.get("body")
    items: list[str] = []
    if isinstance(body, str) and body:
        items.append(body)

    replies = data.get("replies")
    if isinstance(replies, dict):
        reply_data = replies.get("data", {})
        children = reply_data.get("children", []) if isinstance(reply_data, dict) else []
        for child in children:
            items.extend(_extract_comment_bodies(child))

    return items


def _fetch_reddit_text(subreddits: list[str], posts: int, comments: int, timeout: int, user_agent: str) -> str:
    headers = {"User-Agent": user_agent}
    chunks: list[str] = []

    for subreddit in subreddits:
        listing_url = f"https://www.reddit.com/r/{subreddit}/new.json"
        response = requests.get(listing_url, headers=headers, params={"limit": posts}, timeout=timeout)
        response.raise_for_status()
        listing = response.json()

        children = listing.get("data", {}).get("children", [])
        for child in children:
            data = child.get("data", {}) if isinstance(child, dict) else {}
            title = data.get("title")
            selftext = data.get("selftext")
            permalink = data.get("permalink")

            if isinstance(title, str) and title:
                chunks.append(title)
            if isinstance(selftext, str) and selftext:
                chunks.append(selftext)

            if not isinstance(permalink, str) or not permalink:
                continue

            comments_url = f"https://www.reddit.com{permalink}.json"
            c_resp = requests.get(comments_url, headers=headers, params={"limit": comments}, timeout=timeout)
            c_resp.raise_for_status()
            c_payload = c_resp.json()

            if not isinstance(c_payload, list) or len(c_payload) < 2:
                continue

            comment_listing = c_payload[1]
            comment_children = comment_listing.get("data", {}).get("children", []) if isinstance(comment_listing, dict) else []
            for comment in comment_children:
                chunks.extend(_extract_comment_bodies(comment))

    return "\n".join(chunks)


def _run_text_mode(argv: list[str]) -> int:
    parser = _build_text_parser()
    ns = parser.parse_args(argv)

    path = Path(ns.input)
    if not path.exists() or not path.is_file():
        parser.error(f"input file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    tokens = _tokenize_text(
        text,
        lowercase=ns.lowercase,
        with_numbers=ns.with_numbers,
        convert_umlauts=ns.convert_umlauts,
    )
    words = _count_tokens(tokens, ns.min_word_length, ns.max_word_length)
    _write_words(words, ns.output_file, ns.count)
    return 0


def _run_pdf_mode(argv: list[str]) -> int:
    parser = _build_pdf_parser()
    ns = parser.parse_args(argv)

    path = Path(ns.input)
    if not path.exists() or not path.is_file():
        parser.error(f"input file not found: {path}")

    try:
        text = _extract_pdf_text(path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    tokens = _tokenize_text(
        text,
        lowercase=ns.lowercase,
        with_numbers=ns.with_numbers,
        convert_umlauts=ns.convert_umlauts,
    )
    words = _count_tokens(tokens, ns.min_word_length, ns.max_word_length)
    _write_words(words, ns.output_file, ns.count)
    return 0


def _run_reddit_mode(argv: list[str]) -> int:
    parser = _build_reddit_parser()
    ns = parser.parse_args(argv)

    if ns.posts < 1:
        parser.error("--posts must be >= 1")
    if ns.comments < 0:
        parser.error("--comments must be >= 0")
    if ns.timeout < 1:
        parser.error("--timeout must be >= 1")

    try:
        text = _fetch_reddit_text(ns.subreddits, ns.posts, ns.comments, ns.timeout, ns.user_agent)
    except requests.RequestException as exc:
        print(f"Reddit fetch failed: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Invalid Reddit response: {exc}", file=sys.stderr)
        return 2

    tokens = _tokenize_text(
        text,
        lowercase=ns.lowercase,
        with_numbers=ns.with_numbers,
        convert_umlauts=ns.convert_umlauts,
    )
    words = _count_tokens(tokens, ns.min_word_length, ns.max_word_length)
    _write_words(words, ns.output_file, ns.count)
    return 0


def _run_aggregate_mode(argv: list[str]) -> int:
    parser = _build_aggregate_parser()
    ns = parser.parse_args(argv)

    words: Counter[str] = Counter()
    for raw_path in ns.inputs:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            parser.error(f"input file not found: {path}")

        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            word = line.strip()
            if not word:
                continue
            if ns.lowercase:
                word = word.lower()
            words[word] += 1

    _write_words(words, ns.output_file, ns.count)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    if args and args[0] == "crunch":
        # Support both package execution and direct script execution.
        try:
            from . import crunch  # type: ignore[import-not-found]
        except ImportError:
            import crunch

        return crunch.run(args[1:])

    if args and args[0] == "text":
        return _run_text_mode(args[1:])

    if args and args[0] == "pdf":
        return _run_pdf_mode(args[1:])

    if args and args[0] == "reddit":
        return _run_reddit_mode(args[1:])

    if args and args[0] == "aggregate":
        return _run_aggregate_mode(args[1:])

    try:
        cfg = parse_args(args)
    except FileNotFoundError as exc:
        print(f"Unable to read exclude file: {exc}", file=sys.stderr)
        return 1

    crawler = WordhoundCrawler(cfg)

    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)

    out, out_close = _open_output(cfg.output_file)
    email_out = out
    meta_out = out
    email_close = False
    meta_close = False

    if cfg.include_email and cfg.email_file:
        email_out, email_close = _open_output(cfg.email_file)
    if cfg.include_meta and cfg.meta_file:
        meta_out, meta_close = _open_output(cfg.meta_file)

    try:
        if not cfg.no_words:
            _print_counter(_sorted_items(crawler.words), out, cfg.show_count)

        if cfg.groups > 0:
            if not cfg.no_words:
                out.write("\n")
            _print_counter(_sorted_items(crawler.group_words), out, cfg.show_count)

        if cfg.include_email and crawler.emails:
            lines = "\n".join(sorted(crawler.emails))
            if email_out is out and (not cfg.no_words or cfg.groups > 0):
                email_out.write("\n")
            email_out.write(lines + "\n")

        if cfg.include_meta and crawler.meta_values:
            lines = "\n".join(sorted(v for v in crawler.meta_values if v))
            if lines:
                if meta_out is out and (
                    (not cfg.no_words or cfg.groups > 0) or (cfg.include_email and crawler.emails)
                ):
                    meta_out.write("\n")
                meta_out.write(lines + "\n")
    finally:
        if meta_close:
            meta_out.close()
        if email_close:
            email_out.close()
        if out_close:
            out.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
