# DS hardware, the Black 2 ROM, emulators and patches

Research note for the Kaleido planning pass, fetched 2026-11-03. Tags: **Verified** (source and date or commit),
**Unverified**, **Assumption**. Two sources were unusable: Bulbapedia returned HTTP 403, and DAT-o-MATIC requires
accepting its terms first; TASVideos' copy of the No-Intro entries was used instead. Claims that rest only on search
snippets are marked Unverified.

Main sources:

- GBATEK, <https://problemkaputt.de/gbatek.htm> (Last-Modified 2025-04-16)
- ByteMatch, <https://bytematch.dev/fuddlesworth/pokebw2> and its JSON API
- melonDS `1e654443e4c0` (2026-10-27)
- nds-bootstrap `d44e30fd` (2026-10-31) and TWiLight Menu++ `e3afe19`
- jmacd/xdelta `5d936d2c` (2026-10-13)

## Corrections to the brief and to our first assumptions

- **Black 2 and White 2 carts have an infrared port.** GBATEK's chip-ID list has "DSi Macronix 512MB ROM+Infrared (eg.
  P-Letter White 2)"; game codes starting with `I` are "NDS and DSi-enhanced games with built-in Infrared port". melonDS
  sets `irversion = 2; // Pokémon HG/SS, B/W, B2/W2` (`src/NDSCart.cpp` line 477). **Verified.**
- **Keep the header game code (`IREO`).** melonDS looks up ROM size and save type by game code (`src/ROMList.cpp` lines
  4456–4457: `IRDO`/`IREO` → 512 MB, save type 6), and an unknown code falls back to a 64 KB EEPROM save. TWiLight Menu++
  and nds-bootstrap key their per-game lists on it too. **Verified.** This settles the save-identity design: the game
  code stays; each game's identity lives inside the save (`03-architecture.md` §8).

## ByteMatch progress for pokebw2

At commit `41f42ca` (2026-10-31), **Verified** from the page and the JSON API:

| Measure (b2_us) | Value |
| --- | --- |
| Code matched | 3,867,578 / 3,867,578 bytes (100%) |
| Data matched | 1,824,388 / 1,824,556 bytes (99.99%) |
| Functions | 43,418 / 43,418 |
| Complete units | 1,792 / 1,800 |
| ARM9 main | 615,694 code bytes, 8,497 functions, 567/574 units |
| Overlays | 3,251,884 code bytes, 34,921 functions, 1,225/1,226 units |
| Libraries | 766,232 code bytes in 574/574 units, including DS Protect (anti-piracy, 18,132 bytes) and irc (infrared, 1,780 bytes) |

- White 2 is the same apart from its code total (3,867,666 bytes, all matched).
- The history endpoint first shows 100% matched code at 2026-10-28.
- There is no ARM7 category, which agrees with `pokebw2.md`: ARM7 is not a decompilation target.

## Memory and binary limits (GBATEK, **Verified**)

| Resource | DS mode | DSi mode |
| --- | --- | --- |
| Main RAM | 4 MB at `0x02000000` | 16 MB (SCFG_EXT9 selects; 32 MB on debug units only) |
| ARM9 binary | ~3.8 MB on a real DS (header max `0x3BFE00`); **2.5 MB on a DSi "even in NDS-mode"** | 2.5 MB ARM9 + 2.5 MB ARM9i |
| ARM7 binary | ~3.8 MB on a DS; 0.25 MB on a DSi | 0.25 MB ARM7 + 1 MB ARM7i |
| ITCM / DTCM | 32 KB / 16 KB | same |
| Shared WRAM | 32 KB + 64 KB ARM7 WRAM | adds WRAM-A/B/C, 256 KB each |
| VRAM | 656 KB (banks A–I) | same |
| ARM9 clock | 67 MHz | 133 MHz (nds-bootstrap FAQ) |

Consequences:

- Kaleido must fit DS mode's 4 MB of main RAM if DS Lite is a target (Q4).
- Kaleido's ARM9 binary must stay under 2.5 MB if it is to run on DSi or 3DS at all, in either mode. E6 measures
  today's size and headroom.

## Black 2 cartridge and ROM

- **Verified** (GBATEK, melonDS ROMList): the cart is 512 MB, with ROM and infrared. The save is 512 KB FLASH (melonDS
  save type 6 → `512*1024` bytes, FLASH). The chip model is **Unverified**.
- **Verified** (GBATEK): on infrared carts, FLASH and IR share the SPI bus, so FLASH commands carry a `00h` prefix
  byte, run at a slower 1 MHz clock, and need delays. Flashcarts and emulators must emulate this.
- **Verified** (GBATEK, melonDS): the largest DS/DSi cart is 512 MB, and melonDS refuses larger ROMs ("NDSCart: ROM is
  too large"). Header byte `0x014` gives the capacity as 128 KB << n, so 512 MB is n = `0x0C` (**Assumption**, derived).
  **A Kaleido ROM must stay ≤ 512 MB.** How much of it Black 2 already uses is measured in E6 (header `0x080` and
  `0x210`).
- **Verified** (TASVideos, No-Intro #6149/#6150): Black 2 (USA, Europe) (NDSi Enhanced) SHA1
  `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`, White 2 `b5d7490be7b415b8f1e672a53e978a9cc667e56a`. Both match pokebw2's
  `*.sha1` files.
- **Verified** (TWiLight Menu++ issue #1422, ByteMatch): the game contains anti-piracy (DS Protect). It includes a
  "0 Exp" penalty, and its check address differs by mode (`0x2000800` in DS mode, `0x2004800` in DSi mode).
- **Verified** (TWiLight Menu++ `ndsheaderbanner.cpp`): loaders find anti-piracy fixes by game code plus header CRC16
  (`0x15E`). A modified ROM's CRC won't match, so **no loader will patch Kaleido's anti-piracy for us**.
  - **Assumption**: guarding DS Protect out in source (a `KALEIDO_` define in `lib/dsprot` and its callers) is needed
    and sufficient. Tested in E7.
- Xtransceiver video chat works on DSi/DSi XL/3DS (Serebii, **Verified**). The camera and WPA features are
  **Unverified** (search snippet). Kaleido disables these systems anyway (Q7).

## DSi hybrid layout and what a modified hybrid means

**Verified** (GBATEK) facts:

- The DSi area starts at the first 1 MB boundary after the NDS area.
- The header holds ARM9i/ARM7i offsets (`0x1C0`–`0x1DC`), digest regions and hash tables over 0x400-byte sectors
  (`0x1E0`–`0x204`), modcrypt areas (`0x220`–`0x22C`), and SHA1-HMACs of each program (`0x300`–`0x3A0`).
- An RSA-SHA1 signature covers `0x000`–`0xDFF` (at `0xF80`).
- The HMAC key is public. Because of the RSA signature, though, changed HMACs are not accepted by the DSi launcher,
  and the private key is unknown.
- Modcrypt is AES-CTR. Its IVs come from header `0x300`/`0x314`, and its keys from the game code and header `0x350`.
  It is enabled by header `0x01C` bit 1.

What this means for each boot path:

| Boot path | Expected for a modified hybrid | Evidence |
| --- | --- | --- |
| DS Lite + flashcart, DS mode | Should boot: the original DS firmware has no RSA or whitelist check | **Assumption** (strong); E7 |
| DSi/3DS system menu with a retail-style cart | Won't boot in DSi mode: the RSA signature can't be redone | **Verified** (GBATEK) |
| DSi/3DS + nds-bootstrap / TWiLight Menu++, DSi mode | Loads ARM9i/ARM7i and decrypts modcrypt with header keys; no HMAC or RSA check found | **Verified** (`conf_sd.cpp`); absence of checks is weak evidence |
| Unlaunch | Removes RSA, whitelist and region checks; supports modcrypted DSi areas | **Verified** (unlaunch page, v2.0 2019-08-27) |
| melonDS, DSi direct boot | Decrypts modcrypt the same way | **Verified** (`src/DSi.cpp`) |
| melonDS, DSi firmware boot | The DSi launcher's own anti-homebrew checks apply | **Verified** (melonDS issue #1866) |

- **Assumption**: when Kaleido changes ARM9i or ARM7i, the modcrypt state must stay consistent with header
  `0x300`/`0x314`/`0x350`. pokebw2 re-encrypts with the original keys (`pokebw2.md`); whether that stays consistent
  after the HMACs at `0x300`+ are recomputed is a question for E7, because the IVs live in the same bytes.
- **Verified** (pokebw2 `lib/nitro/src/fs/fs_overlay.c`): overlay digests are checked only when the boot type isn't
  ROM. pokebw2 refills them on every build.
- **Verified** (nds-bootstrap wiki `future.md`): "some ROM hacks are bound to not work on real hardware (e.g. the gen 5
  hacks with fairy type)". Retail Black 2 needed a loader fix for DSi mode (TWiLight Menu++ commit `5bb2b74a`), and
  several issues advise users to switch to DS mode.
- Fallback if hybrids fail: a DS-only build (unit code 00, TWL region removed). **Assumption**: B2's DS-mode path never
  needs the LTD module. E7.

## Emulators and automation

| Emulator | License | Latest | DSi mode | Automation |
| --- | --- | --- | --- | --- |
| melonDS | GPL-3.0 | 1.1 (2025-11-18); master `1e65444` 2026-10-27 | Yes (needs DSi BIOS, firmware, NAND dumps); "better DSi emulation" still on its TODO | No headless or Lua mode. GDB stub on by default. The core builds as a static library, so a custom headless harness is possible (**Assumption**) |
| DeSmuME | GPL-2.0 | 0.9.13 (2022-05-23); master `fc504ee` 2026-10-25 | Not real DSi mode (only a few `Is_DSI()` paths, **Assumption**) | GDB stubs; movies and savestates on the CLI; Lua on Windows only; a C interface library (`desmume_open`, `desmume_cycle`, memory read/write, savestates), wrapped by SkyTemple's py-desmume (GPL-3.0) |
| BizHawk | MIT frontend; GitHub reports `NOASSERTION`, and its LICENSE calls the whole a "minefield" of GPL licenses | 2.11.1 (2026-05-01) | Via its melonDS core ("DS + DSi") | `--lua`, `--chromeless`, sockets; needs Mono and Lua 5.4 on Linux; no headless flag |

All rows **Verified** unless marked.

- B2W2 issues on record: melonDS #2651 (DS-mode crash, low-confidence report from an Android fork), #2658 (DSi-mode
  crash after about two hours), #1530 (graphics glitches). Retail B2W2 boots from DSi firmware in melonDS (#2789).
- **Verified** (Phase 1 spike, 2026-11-04, `harness-spike.md`): py-desmume 0.0.9 installs from PyPI on Linux with
  DeSmuME 0.9.12's core bundled, and runs Black 2 headless with no BIOS or firmware files. It booted the hybrid in DS
  mode, and scripted buttons drove the game to the first battle. ADR 0005 (accepted) makes it Kaleido's DS-mode harness,
  with a melonDS-core harness as the fallback for DSi mode.

## xdelta3 and patch formats

- **Verified** (jmacd/xdelta): latest release v3.2.2 (2026-10-09); Apache-2.0. The GPL line is a separate repo.
- **Verified** (`commandline.md`, `armor.md`):
  - 3.2.x turns on "armor" by default, embedding BLAKE3 digests in the application header; legacy decoders read those
    as file names. `-a` restores the legacy format.
  - The application header stores the source and target file names by default; `-A=` clears it.
  - LZMA secondary compression is used when compiled in; "use `-S none` for the broadest compatibility".
  - The default source window (`-B`) is 64 MiB, but the base ROM is 512 MB.
- **Unverified**: whether output is byte-identical across runs and platforms. No document addresses it.
  **Assumption**: pinning the version and passing `-a -A= -S none` with `-B` covering the 512 MB source gives
  deterministic, widely compatible patches. Phase 1 tests this, along with applying the patch in Delta Patcher (an
  xdelta 3.0 fork, GPL-2.0, v3.1.6) and Rom Patcher JS.
- **Phase 1 (2026-11-04)**: Kaleido pins xdelta3 **3.0.11**, Ubuntu 26.04's package, which predates armor. **Verified**
  on the owner's machine with FireRed's test ROM:
  - by default 3.0.11 writes the file names into the application header (`game.nds//base.nds/`), so patches of the
    same files under other names differ;
  - with `-e -9 -S none -A -B <base size>`, two patches made from differently named copies in different directories
    were byte-identical (420 KB), and applying either to the base ROM gave the built ROM;
  - xdelta3 refuses a source window under 512 KiB.
  Still **Unverified**: the same patch on another machine (Phase 1's exit criterion), and Delta Patcher and Rom Patcher
  JS applying it.
- **Verified** (Rom Patcher JS source): IPS is capped at 16 MB, so it is unsuitable. BPS/UPS at 512 MB: **Unverified**.

## Source ROM hashes for extraction

All **Verified** from pret READMEs (pokefirered `ce6406d8`, pokered `0dbf95cd`, pokeyellow `b452f2ab`). Regions are from
TASVideos where given.

| ROM | SHA1 |
| --- | --- |
| FireRed (USA) | `41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc` |
| FireRed (USA, Rev 1) | `dd5945db9b930750cb39d00c84da8571feebf417` (region **Unverified**) |
| LeafGreen (USA) | `574fa542ffebb14be69902d1d36f1ec0a4afd71e` |
| LeafGreen (USA, Europe) (Rev 1) | `7862c67bdecbe21d1d69ce082ce34327e1c6ed5e` |
| Red (USA, Europe) | `ea9bcae617fdf159b045185467ae58b2e4a48b9a` |
| Blue (USA, Europe) | `d7037c83e1ae5b39bde3c30787637ba1d4c48ce2` |
| Yellow (USA, Europe) | `cc7d03262ebfaf2f06772c1a480c7d9d5f4a38e1` |

## Unknowns only an experiment settles

1. The boot matrix for a modified hybrid (each device, mode and loader), against a DS-only variant (E7).
2. Modcrypt and digest consistency when ARM9i/ARM7i change, and what boot type the game sees under each loader (E7).
3. Real headroom in DS mode (4 MB) and within the DSi's 2.5 MB ARM9 limit (E6).
4. Saves on flashcarts with IR-prefixed SPI and a modified header; whether guarding DS Protect out removes the
   anti-piracy effects (E7, E9).
5. Determinism across machines and compatibility of Kaleido's xdelta3 3.0.11 patches (one machine verified in Phase 1),
   and that the output ROM stays ≤ 512 MB (Phase 1, E6).
