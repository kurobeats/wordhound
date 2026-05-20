from __future__ import annotations

import argparse
import itertools
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

LOWER_DEFAULT = "abcdefghijklmnopqrstuvwxyz"
UPPER_DEFAULT = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUMBER_DEFAULT = "0123456789"
SYM_DEFAULT = "!@#$%^&*()-_+=~`[]{}|\\:;\"'<>,.?/ "


@dataclass
class CrunchConfig:
    min_len: int
    max_len: int
    lower: str
    upper: str
    numbers: str
    symbols: str
    pattern: str | None
    literal: str | None
    start: str | None
    end: str | None
    invert: bool
    duplicate_limits: dict[str, int]
    output: str | None
    chunk_lines: int | None
    permute_words: list[str] | None


def _copy_without_dupes(value: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for ch in value:
        if ch not in seen:
            seen.add(ch)
            out.append(ch)
    return "".join(out)


def _split_head(argv: list[str]) -> tuple[int, int, list[str], list[str]]:
    if len(argv) < 2:
        raise ValueError("Usage: wordhound crunch <min> <max> [charset strings] [options]")

    try:
        min_len = int(argv[0])
        max_len = int(argv[1])
    except ValueError as exc:
        raise ValueError("min and max must be integers") from exc

    if min_len < 0 or max_len < min_len:
        raise ValueError("min/max values are invalid")

    i = 2
    charset_tokens: list[str] = []
    while i < len(argv) and not argv[i].startswith("-") and len(charset_tokens) < 4:
        charset_tokens.append(argv[i])
        i += 1

    return min_len, max_len, charset_tokens, argv[i:]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wordhound crunch", description="Crunch-style wordlist generator")
    parser.add_argument("-o", dest="output")
    parser.add_argument("-t", dest="pattern")
    parser.add_argument("-l", dest="literal")
    parser.add_argument("-s", dest="start")
    parser.add_argument("-e", dest="end")
    parser.add_argument("-i", dest="invert", action="store_true")
    parser.add_argument("-d", dest="duplicate_limits", action="append", default=[])
    parser.add_argument("-c", dest="chunk_lines", type=int)
    parser.add_argument("-p", dest="permute_words", nargs="+")
    parser.add_argument("-q", dest="permute_file")

    # Parsed for compatibility but intentionally unsupported for now.
    parser.add_argument("-b", dest="byte_limit")
    parser.add_argument("-f", dest="charset_file", nargs=2)
    parser.add_argument("-r", dest="resume", action="store_true")
    parser.add_argument("-u", dest="disable_progress", action="store_true")
    parser.add_argument("-z", dest="compression")

    return parser


def _parse_duplicate_limits(values: list[str]) -> dict[str, int]:
    limits = {"@": sys.maxsize, ",": sys.maxsize, "%": sys.maxsize, "^": sys.maxsize}
    for value in values:
        match = re.match(r"^(\d+)([@,%\^]*)$", value)
        if not match:
            raise ValueError("-d must be in the format [n][@,%^]")
        n = int(match.group(1))
        symbols = match.group(2) or "@"
        for sym in symbols:
            limits[sym] = n
    return limits


def _parse_config(argv: list[str]) -> CrunchConfig:
    min_len, max_len, csets, rest = _split_head(argv)

    parser = _build_parser()
    ns = parser.parse_args(rest)

    if ns.byte_limit or ns.charset_file or ns.resume or ns.compression:
        raise ValueError("Options -b, -f, -r, and -z are not yet implemented in wordhound crunch")

    if ns.chunk_lines is not None and ns.chunk_lines < 1:
        raise ValueError("-c must be >= 1")

    lower = _copy_without_dupes(csets[0]) if len(csets) > 0 and csets[0] != "+" else LOWER_DEFAULT
    upper = _copy_without_dupes(csets[1]) if len(csets) > 1 and csets[1] != "+" else UPPER_DEFAULT
    numbers = _copy_without_dupes(csets[2]) if len(csets) > 2 and csets[2] != "+" else NUMBER_DEFAULT
    symbols = _copy_without_dupes(csets[3]) if len(csets) > 3 and csets[3] != "+" else SYM_DEFAULT

    duplicate_limits = _parse_duplicate_limits(ns.duplicate_limits)

    if ns.pattern is not None and (len(ns.pattern) != min_len or len(ns.pattern) != max_len):
        raise ValueError("When using -t, min and max must equal pattern length")

    if ns.literal is not None and ns.pattern is None:
        raise ValueError("-l requires -t")

    if ns.literal is not None and len(ns.literal) != len(ns.pattern):
        raise ValueError("-l value length must match -t pattern length")

    if ns.start is not None and len(ns.start) != min_len:
        raise ValueError("-s length must equal min length")

    if ns.end is not None and len(ns.end) != max_len:
        raise ValueError("-e length must equal max length")

    if ns.chunk_lines is not None and ns.output != "START":
        raise ValueError("-c currently requires -o START")

    if ns.permute_words is not None and ns.permute_file is not None:
        raise ValueError("Use only one of -p or -q")

    if (ns.permute_words is not None or ns.permute_file is not None) and ns.start is not None:
        raise ValueError("-s cannot be used with -p/-q")

    permute_words = ns.permute_words
    if ns.permute_file:
        path = Path(ns.permute_file)
        if not path.exists():
            raise ValueError(f"Permute file not found: {path}")
        permute_words = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    if permute_words:
        permute_words = sorted(permute_words)

    return CrunchConfig(
        min_len=min_len,
        max_len=max_len,
        lower=lower,
        upper=upper,
        numbers=numbers,
        symbols=symbols,
        pattern=ns.pattern,
        literal=ns.literal,
        start=ns.start,
        end=ns.end,
        invert=ns.invert,
        duplicate_limits=duplicate_limits,
        output=ns.output,
        chunk_lines=ns.chunk_lines,
        permute_words=permute_words,
    )


def _char_type(ch: str, cfg: CrunchConfig) -> str | None:
    if ch in cfg.lower:
        return "@"
    if ch in cfg.upper:
        return ","
    if ch in cfg.numbers:
        return "%"
    if ch in cfg.symbols:
        return "^"
    return None


def _too_many_duplicates(word: str, cfg: CrunchConfig) -> bool:
    if not word:
        return False

    run_char = word[0]
    run_len = 1
    for ch in word[1:]:
        if ch == run_char:
            run_len += 1
        else:
            run_char = ch
            run_len = 1

        ctype = _char_type(run_char, cfg)
        if ctype and run_len > cfg.duplicate_limits[ctype]:
            return True

    return False


def _active_placeholder(ch: str, literal: str | None, idx: int) -> bool:
    if ch not in "@,%^":
        return False
    if literal is None:
        return True
    return literal[idx] != ch


def _charset_for_placeholder(ch: str, cfg: CrunchConfig) -> str:
    if ch == "@":
        return cfg.lower
    if ch == ",":
        return cfg.upper
    if ch == "%":
        return cfg.numbers
    if ch == "^":
        return cfg.symbols
    raise ValueError(f"Unsupported placeholder: {ch}")


def _iter_pattern_words(cfg: CrunchConfig) -> Iterable[str]:
    assert cfg.pattern is not None

    charsets: list[str | None] = []
    for i, ch in enumerate(cfg.pattern):
        if _active_placeholder(ch, cfg.literal, i):
            charsets.append(_charset_for_placeholder(ch, cfg))
        else:
            charsets.append(None)

    positions = [i for i, cset in enumerate(charsets) if cset is not None]
    if not positions:
        yield cfg.pattern
        return

    idxs = [0] * len(positions)
    line = list(cfg.pattern)
    for pos_i, pos in enumerate(positions):
        line[pos] = charsets[pos][0]  # type: ignore[index]

    def to_word() -> str:
        return "".join(line)

    start = cfg.start
    end = cfg.end
    started = start is None

    while True:
        word = to_word()

        if not started and word == start:
            started = True
        if started and not _too_many_duplicates(word, cfg):
            yield word

        if end is not None and word == end:
            break

        order = range(len(positions)) if cfg.invert else range(len(positions) - 1, -1, -1)
        carry = True
        for oi in order:
            pos = positions[oi]
            cset = charsets[pos]  # type: ignore[index]
            idxs[oi] += 1
            if idxs[oi] < len(cset):
                line[pos] = cset[idxs[oi]]
                carry = False
                break
            idxs[oi] = 0
            line[pos] = cset[0]

        if carry:
            break


def _iter_plain_words(cfg: CrunchConfig) -> Iterable[str]:
    for length in range(cfg.min_len, cfg.max_len + 1):
        cset = cfg.lower
        if not cset:
            return

        idxs = [0] * length
        line = [cset[0]] * length

        start = cfg.start if cfg.start and len(cfg.start) == length else None
        end = cfg.end if cfg.end and len(cfg.end) == length else None
        started = start is None

        if start is not None:
            try:
                for i, ch in enumerate(start):
                    idxs[i] = cset.index(ch)
                    line[i] = ch
            except ValueError as exc:
                raise ValueError("-s includes characters not found in charset") from exc

        while True:
            word = "".join(line)

            if not started and word == start:
                started = True
            if started and not _too_many_duplicates(word, cfg):
                yield word

            if end is not None and word == end:
                break

            order = range(length) if cfg.invert else range(length - 1, -1, -1)
            carry = True
            for pos in order:
                idxs[pos] += 1
                if idxs[pos] < len(cset):
                    line[pos] = cset[idxs[pos]]
                    carry = False
                    break
                idxs[pos] = 0
                line[pos] = cset[0]
            if carry:
                break


def _iter_placeholder_expansions(pattern: str, literal: str | None, cfg: CrunchConfig) -> Iterable[str]:
    dyn_positions: list[int] = []
    dyn_sets: list[str] = []
    base = list(pattern)

    for i, ch in enumerate(pattern):
        if _active_placeholder(ch, literal, i):
            dyn_positions.append(i)
            dyn_sets.append(_charset_for_placeholder(ch, cfg))

    if not dyn_positions:
        yield pattern
        return

    for combo in itertools.product(*dyn_sets):
        line = base[:]
        for i, pos in enumerate(dyn_positions):
            line[pos] = combo[i]
        yield "".join(line)


def _iter_permute_words(cfg: CrunchConfig) -> Iterable[str]:
    words = cfg.permute_words or []
    if not words:
        return

    for perm in itertools.permutations(words, len(words)):
        if cfg.pattern is None:
            word = "".join(perm)
            if not _too_many_duplicates(word, cfg):
                yield word
            continue

        slots = []
        for i, ch in enumerate(cfg.pattern):
            if not _active_placeholder(ch, cfg.literal, i):
                slots.append(i)

        if len(slots) != len(perm):
            raise ValueError("With -p/-q and -t, non-placeholder count in pattern must match number of words")

        base = list(cfg.pattern)
        for i, pos in enumerate(slots):
            base[pos] = perm[i]

        template = "".join(base)
        for expanded in _iter_placeholder_expansions(template, cfg.literal, cfg):
            if not _too_many_duplicates(expanded, cfg):
                yield expanded


class _Writer:
    def __init__(self, output: str | None, chunk_lines: int | None):
        self.output = output
        self.chunk_lines = chunk_lines
        self.stdout_mode = output is None
        self.start_mode = output == "START"

        self._fh = None
        self._line_count = 0
        self._file_index = 0
        self._first: str | None = None
        self._last: str | None = None

        if self.stdout_mode:
            self._fh = sys.stdout
        elif self.start_mode:
            self._open_start_file()
        else:
            self._fh = open(output, "w", encoding="utf-8")

    def _open_start_file(self) -> None:
        self._file_index += 1
        self._line_count = 0
        self._first = None
        self._last = None
        self._fh = open("START", "w", encoding="utf-8")

    def _finalize_start_file(self) -> None:
        if self._fh is not None and self._fh is not sys.stdout:
            self._fh.close()
        if self._first is None or self._last is None:
            Path("START").unlink(missing_ok=True)
            return

        safe_first = self._first.replace("/", " ")
        safe_last = self._last.replace("/", " ")
        target = f"{safe_first}-{safe_last}.txt"
        Path("START").rename(target)

    def write(self, word: str) -> None:
        assert self._fh is not None

        if self.start_mode and self.chunk_lines and self._line_count >= self.chunk_lines:
            self._finalize_start_file()
            self._open_start_file()

        self._fh.write(word + "\n")
        self._line_count += 1

        if self.start_mode:
            if self._first is None:
                self._first = word
            self._last = word

    def close(self) -> None:
        if self.start_mode:
            self._finalize_start_file()
            return

        if self._fh is not None and self._fh is not sys.stdout:
            self._fh.close()


def run(argv: list[str]) -> int:
    try:
        cfg = _parse_config(argv)
    except ValueError as exc:
        print(f"wordhound crunch error: {exc}", file=sys.stderr)
        return 2

    if cfg.pattern and cfg.start and len(cfg.start) != len(cfg.pattern):
        print("wordhound crunch error: -s must match pattern length", file=sys.stderr)
        return 2
    if cfg.pattern and cfg.end and len(cfg.end) != len(cfg.pattern):
        print("wordhound crunch error: -e must match pattern length", file=sys.stderr)
        return 2

    writer = _Writer(cfg.output, cfg.chunk_lines)
    try:
        if cfg.permute_words is not None:
            iterable = _iter_permute_words(cfg)
        elif cfg.pattern is not None:
            iterable = _iter_pattern_words(cfg)
        else:
            iterable = _iter_plain_words(cfg)

        for word in iterable:
            writer.write(word)
    except ValueError as exc:
        print(f"wordhound crunch error: {exc}", file=sys.stderr)
        return 2
    finally:
        writer.close()

    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
