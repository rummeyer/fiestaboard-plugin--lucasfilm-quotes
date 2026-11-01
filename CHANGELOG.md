# Changelog

All notable changes to this plugin are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version here is the source of truth for `manifest.json` — a test fails if
the two drift apart.

## [Unreleased]

## [1.0.0] — 2026-11-01

### Added

- A random quote from a Lucasfilm movie on every refresh, word-wrapped and
  centered, signed with the character who said it.
- Only quotes that fit the board: a Note gets the short ones, a Flagship the
  long ones too. A name too long for its row is shortened to the name the
  character goes by (`- OBI-WAN`, `- ACKBAR`).
- 537 quotes from 23 movies and 99 characters in `quotes.json`, shipped with
  the plugin: Star Wars, Indiana Jones, and American Graffiti, Howard the Duck,
  Labyrinth, Willow, Tucker and Red Tails. Each quote has its movie, each movie
  its year and franchise, each character the shorter names they go by.
- Quotes signed with the name the character goes by in that movie
  (`- THE EMPEROR`, `- PRINCESS LEIA`), and filed under the one character.
- **Franchises**, **Movies** and **Characters** pickers, with how many quotes
  each brings.
- **Character name** (*When it fits*, *Always*, *Never*), **Skip swearing**,
  left alignment, and no repeat of the last 50 quotes where it can be avoided.
- `{{lucasfilm_quotes.quote}}`, `.character`, `.movie`, `.year`, `.franchise`,
  `.block` and `.line1` … `.line6`.
- A setup guide in `docs/SETUP.md`, board screenshots of a Note, a Flagship and
  a 2x2 note array, and the board-shape conformance test of FiestaBoard core.
