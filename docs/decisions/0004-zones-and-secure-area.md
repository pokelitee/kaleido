# 0004. Reuse zone IDs for Tier 1; build without the ARM7 BIOS

- Status: Accepted (by the owner, 2026-11-03)
- Date: 2026-11-03

## Context

E4a (`docs/research/e4a-new-zone.md`) found two things at pokebw2 `41f42ca`:

- **Appending zones** gives the first new zone ID 615, which three places in the code already use to mean "no zone"
  (`ZONE_MAX`, the zone-header cache's start value, the initial place-name zone). A `KALEIDO_EXTRA_ZONES` switch moves
  them to 0xffff, but that changes ARM9 main code.
- **Any change that moves code in ARM9 main** changes bytes in its first 16 KiB. dsd then needs the DS ARM7 BIOS's
  Blowfish key to recompute the DSi values derived from the encrypted secure area, and refuses to build otherwise
  (R-27). The owner has no DS to dump a BIOS from.

Tier 1 needs at most FireRed/LeafGreen's 425 maps, fewer than B2W2's 615 zones. DS mode is the hard limit (Q4); DSi
mode is tested but never required. A modified hybrid can't boot in DSi mode from the system menu anyway, because its
RSA signature can't be redone (`hardware-and-rom.md`).

## Options

1. **Supply a BIOS**: the owner dumps the DS ARM7 BIOS and every build passes it. Needs hardware the owner doesn't have.
2. **Reuse zone IDs, and let dsd keep stale secure-area values**: no zone sentinel change for Tier 1; a small dsd change
   for every other ARM9 main change.
3. **Keep engine changes out of ARM9 main**: unrealistic; zones, DS Protect callers and B2W2 system switches all touch
   it.

## Decision

Option 2, with option 1 still supported.

- **Zones**: Tier 1 Kanto zones reuse existing zone IDs. A layer overrides a zone's header, events, scripts and text
  files; the upstream constant keeps its name. A mapping in the Kanto region layer records which zone ID holds which
  Kanto location. Zones whose IDs the code treats specially (gates, Entree Forest, Black Tower, the PWT, Join Avenue and
  others) are avoided or neutralized. Phase 1 lists them. Appending zones with `KALEIDO_EXTRA_ZONES`
  (`docs/research/e4a-extra-zones.patch`) stays available for later tiers.
- **dsd**: Kaleido's dsd adds `dsd rom build --allow-stale-secure-area`
  (`docs/research/dsd-allow-stale-secure-area.patch`, MIT, offered upstream). With it, a ROM whose ARM9 secure area
  changed builds without the BIOS and keeps the extracted secure-area values. Those are stale: the two secure-area
  sector digests, the ARM9-with-secure-area SHA1-HMAC, and the secure-area CRC.
- **configure.py**: Kaleido's engine patch adds `--allow-stale-secure-area` and `--arm7-bios PATH`, both passed to
  `dsd rom build`. A builder with a BIOS uses `--arm7-bios`, and every value is then correct.

## Consequences

- E4a's ROM builds. **Verified**: everything `verify_dsi_rom.py` can check is valid; it skips the secure-area values by
  design. With the patched dsd, the untouched pin still rebuilds Black 2 byte for byte.
- DS mode doesn't check the stale values. DSi mode through a loader that verifies them would fail. Whether
  nds-bootstrap or Unlaunch verify them is **Unverified** (E7).
- Kaleido's toolchain includes a patched dsd until upstream takes the change. So bootstrap builds dsd from
  `ds-decomp` and `ds-rom` at pinned commits plus the patch, which adds Rust as a tool. Building takes about 35 minutes
  the first time.
- Zone constants keep Unova names in Kanto games. The region's mapping and the validator keep that readable.
