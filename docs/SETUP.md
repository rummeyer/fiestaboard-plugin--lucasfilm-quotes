# Lucasfilm Quotes Setup Guide

Show a quote from Star Wars, Indiana Jones or another Lucasfilm movie on your Vestaboard, signed with the character who said it.

## Overview

**What it does:**

- A new quote on every refresh, word-wrapped and centered
- Only quotes that fit your board: the short ones on a Note, the long ones too on a Flagship
- Signed with the character's name, or the name they go by when the full one does not fit (`- OBI-WAN`, `- ACKBAR`)
- Optionally only quotes from the franchises or movies you choose, or by the characters you choose

**Prerequisites:** None. It works out of the box. The 537 quotes ship with the plugin, so there is no account, no API key and nothing to download.

## Quick Setup

### 1. Enable the Plugin

Open **Integrations** in FiestaBoard, find **Lucasfilm Quotes** and install it. Then open its card and switch **Enabled** on.

### 2. Configure Lucasfilm Quotes

Nothing is required. To narrow the quotes down, pick **Franchises**, **Movies** or **Characters**. Each option shows how many quotes it brings. Switch on **Skip swearing** if the board hangs where children read it.

### 3. Create a Board Template

Create a page and put this on its **first** line, with the line set to left alignment and no wrap:

```
{{lucasfilm_quotes.block}}
```

That one variable fills the board. FiestaBoard splits it across the board rows, and the rows are exactly as wide as the board, so nothing gets cut or shifted.

### 4. View on Your Board

The board shows a quote like this on a Note:

![Lucasfilm Quotes on a Note](./board-display.png)

And like this on a Flagship:

![Lucasfilm Quotes on a Flagship](./board-flagship.png)

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{lucasfilm_quotes.block}}` | The whole layout, rows separated by newlines | see above |
| `{{lucasfilm_quotes.line1}}` … `{{lucasfilm_quotes.line6}}` | The same rows one by one; empty past the board's height | |
| `{{lucasfilm_quotes.quote}}` | The quote as board text, not wrapped | `IT'S A TRAP!` |
| `{{lucasfilm_quotes.character}}` | The character's full name, as they go by in the movie | `ADMIRAL ACKBAR` |
| `{{lucasfilm_quotes.movie}}` | The movie | `STAR WARS: EPISODE VI - RETURN OF THE JEDI` |
| `{{lucasfilm_quotes.year}}` | The year the movie came out | `1983` |
| `{{lucasfilm_quotes.franchise}}` | The franchise, empty for a movie outside one | `STAR WARS` |

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| Franchises | any | Only quotes from the movies of these franchises. |
| Movies | any | Only quotes from these movies. Combined with franchises, each quote is from one of the chosen franchises or one of the chosen movies. |
| Characters | any | Only quotes by these characters. Combined with franchises or movies, each quote is by one of the chosen characters and from one of the chosen franchises or movies. |
| Character name | When it fits | Sign the quote with the character's name: **When it fits**, **Always** (only quotes with room for it, on a Note 99 instead of 221) or **Never**. |
| Skip swearing | off | Leave out the quotes with a *damn*, *hell* or *bastard* in them. |
| Alignment | Centered | Centered, with the name centered below; or left-aligned, with the name flush right. |
| Refresh interval | 3600 s | How long a quote stays up. Minimum 60 s. |

### Environment Variables

None.

## Troubleshooting

**A Note shows the same few quotes.** A Note fits 221 of the 537 quotes, fewer when you pick franchises, movies or characters. The plugin does not repeat any of the last 50 while another one fits, so a narrow selection comes round again sooner.

**The quote is cut off with `...`.** None of the chosen quotes fits this board. Pick more, or none.

**The board shows "No quotes match the chosen franchises, movies and characters".** The characters you picked say nothing in the movies you picked, like Yoda in Labyrinth. Pick another movie, or leave one of the pickers empty.

**There is no name under the quote.** On a Note many quotes take all three rows. The name is left off rather than the quote cut. Set **Character name** to *Always* to show signed quotes only.
