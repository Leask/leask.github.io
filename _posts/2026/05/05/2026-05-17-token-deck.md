---
layout: post
title: 'Token Deck'
author: Leask
date: '2026-05-17 22:00:00 -0400'
categories:
- Computers and Internet
---

Since Codex has recently become the most important tool in my work, without question, keeping an eye on token usage at all times has become crucial. Today, I spent a little time vibe coding a Stream Deck plugin called Token Deck. It can display AI provider quotas, token usage, and Mac hardware status on Stream Deck. The project is open source on GitHub at [leask/token-deck](https://github.com/Leask/Token-Deck).

<img width="2048" height="1527" alt="Screenshot 2026-05-17 at 9 54 57 PM" src="https://github.com/user-attachments/assets/6f1d6ae6-cc68-42c5-900d-fdfeb78be87a" />

Token Deck is a Stream Deck plugin for showing AI provider quota, token usage,
and Mac hardware status on Stream Deck keys. The token action is powered by
[CodexBar](https://github.com/steipete/CodexBar), the hardware actions read
local macOS status directly.

<img width="962" height="932" alt="Screenshot 2026-05-17 at 7 29 55 PM" src="https://github.com/user-attachments/assets/2d8ac047-c8cd-4c4b-9316-11a5033baf5a" />

## Requirements

- macOS with Elgato Stream Deck 7.1 or newer.
- Node.js 24 or newer.
- CodexBar installed and configured.

By default, the plugin uses `CLI` mode and runs a short-lived CodexBar command
at each refresh:

```bash
codexbar usage --provider codex --format json --json-only
```

`HTTP` mode reads an explicitly running CodexBar JSON service:

```bash
codexbar serve --port 8080 --refresh-interval 60
```

The plugin never switches data sources automatically. Pick `CLI` or `HTTP` in
the action settings.

Custom connection fields are optional. If `CLI Path` is empty, Token Deck checks
the common Homebrew paths and then runs `codexbar` from `PATH`. If
`HTTP Endpoint` is empty, Token Deck builds `http://127.0.0.1:<port>/usage` from
the `HTTP Port` setting.

## Architecture

- Stream Deck runtime: Node.js/TypeScript via `@elgato/streamdeck`.
- Token usage source: explicit `CLI` or `HTTP`; there is no hidden fallback
  between data source modes.
- Hardware sources: macOS system commands and Apple SMC readings, kept
  independent from CodexBar.
- Rendering: each action generates a compact SVG image and sends it to the key
  with `setImage`.
- Refresh: every key refreshes on its timer and immediately when pressed.

## Development

```bash
npm install
npm run build
npm run watch
```

The official Stream Deck CLI linked the plugin into:

```text
~/Library/Application Support/com.elgato.StreamDeck/Plugins/com.leask.token-deck.sdPlugin
```

The link points back to this checkout's `com.leask.token-deck.sdPlugin`
directory.

## Actions

`AI Token Usage` renders:

- provider name
- remaining percentage for the primary quota window
- primary reset countdown
- secondary quota mini bar

Pressing the key forces a refresh.

Hardware status actions can be added as separate keys without changing the
token key:

- `CPU Status`
- `Memory Status`
- `Disk Status`
- `GPU Status`
- `Network Status`
- `Temperature Status`
- `Battery Status`
- `Power Status`

The hardware keys refresh automatically and also refresh immediately when
pressed.

`CPU Status` samples aggregate CPU activity over a short interval.

`Memory Status` shows current used memory based on Node's OS memory counters.

`Disk Status` aggregates mounted local physical storage and skips network
mounts, Time Machine local snapshots, and disk images. On macOS APFS volumes are
deduplicated by container, so the internal Data volume and an external USB disk
array are counted once each instead of counting every APFS system volume.

`GPU Status` reads Apple Silicon GPU utilization from `IOAccelerator` when that
counter is exposed by macOS.

`Network Status` samples local interface counters and shows combined download
and upload throughput. Loopback, bridge, AWDL, and other virtual interfaces are
ignored.

`Temperature Status` uses Apple SMC temperature readings when available. If the
native sensor module cannot be loaded in the Stream Deck runtime, it falls back
to macOS thermal pressure from `pmset -g therm` instead of showing an error.

`Battery Status` uses `pmset -g batt` on macOS. It shows internal battery level
on laptops, UPS charge on desktop Macs with a supported UPS, and AC/no battery
when no battery source is present.

`Power Status` reads Apple SMC power keys without requiring sudo. If SMC power
is unavailable, it falls back to Apple power telemetry from `ioreg`, then to
voltage/current-derived power on systems that expose battery amperage.

## Validation

Use these checks before shipping a local change:

```bash
npx tsc --noEmit
npm run build
streamdeck validate com.leask.token-deck.sdPlugin
streamdeck restart com.leask.token-deck
```

Runtime logs are written under:

```text
com.leask.token-deck.sdPlugin/logs/com.leask.token-deck.0.log
```
