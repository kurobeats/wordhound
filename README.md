# Wordhound

A Python 3 implementation inspired by giants.

## Heritage

This project is (now) a modernised implementation that pays homage to three important influences:

- Original WordHound (https://bitbucket.org/mattinfosec/wordhound)
- Crunch-style combinational wordlist generation (https://github.com/crunchsec/crunch)
- CeWL-style website-driven custom wordlist construction (https://github.com/digininja/CeWL)

## Motivation

People are generally poor at true randomness, and many passwords are influenced by personal, organisational, and contextual language. Building dictionaries from those context signals can improve targeted wordlist quality compared with only generic lists.

For background on the original concept, see the PasswordsCon 2014 talk referenced by the original project:

- http://www.irongeek.com/i.php?page=videos/passwordscon2014/target-specific-automated-dictionary-generation-matt-marx

## Features

- Crawl a target URL to configurable depth
- Build wordlists with frequency counts
- Build wordlists from local text files
- Build wordlists from local PDF files
- Build wordlists from Reddit thread content
- Aggregate multiple generated wordlists
- Extract emails from page content and `mailto:` links
- Capture URL structure tokens (domain/subdomain/path components)
- Optional word grouping (n-grams)
- Supports custom headers, proxy, and basic/digest authentication
- Crunch-style combinational wordlist generation

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
main.py --help
```

Additional modes:

```bash
# Crawl a website (existing mode)
main.py https://example.com -d 2 -w words.txt

# Build a wordlist from local text
main.py text ./notes.txt -c -w text_words.txt

# Build a wordlist from local PDF
main.py pdf ./brochure.pdf --lowercase -w pdf_words.txt

# Build a wordlist from one or more subreddits
main.py reddit netsec osint --posts 20 --comments 30 -w reddit_words.txt

# Aggregate multiple wordlists
main.py aggregate words1.txt words2.txt -c -w aggregate.txt
```

Crunch mode:

```bash
main.py crunch 1 4 abc
main.py crunch 8 8 -t @@dog@@@ -s cbdogaaa -o wordlist.txt
main.py crunch 4 4 -p dog cat bird
main.py crunch 3 3 abc + 123 !@# -t @%^
```

Supported Crunch options in this implementation:

- `-t`, `-l`, `-s`, `-e`, `-d`, `-i`, `-o`, `-c`, `-p`, `-q`

Currently not implemented in crunch mode:

- `-b`, `-f`, `-r`, `-z`

Not included in this implementation:

- Twitter functionality
- Original WordHound Twitter API configuration flow
- Original LexEngine threshold configuration flow

## Notes

- Metadata extraction from documents is implemented as best-effort and currently focuses on HTML metadata plus PDF metadata when `pypdf` is available.
- This is a clean Python implementation and not a line-by-line port.

## Acknowledgements

- WordHound: https://github.com/kurobeats/wordhound
- CeWL: https://github.com/digininja/CeWL
- Crunch: https://github.com/crunchsec/crunch
