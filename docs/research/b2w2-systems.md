# B2W2 systems: an inventory for per-game switches

Each B2W2-only system is a compile-time switch that each game's config picks (Q7, `03-architecture.md`, "B2W2
systems"). This is a first inventory, taken 2026-11-04 from pokebw2 at `41f42ca` by file, overlay and save block names
(**Verified** that the files exist; what each one does is from its name unless a row says it was traced). A system's
entry points are traced when its switch is built; so far, only the C-Gear's.

| System | Code | Save block | Switch |
| --- | --- | --- | --- |
| C-Gear | `ov079/c_gear_sw.c` (the bottom screen), `ov080/no_gear.c` (the screen before it), `ov088/c_gear_power_onoff.c`, `ov012/event_cgear_poweron.c`, `system/c_gear_savedata.c` | `SAVE_BLOCK_CGEAR` | **`KALEIDO_NO_CGEAR`** (patch `0006`), traced below |
| Pass Powers | `system/pass_power.c`, `ov156/field_pass_power.c`, `ov328/gpower_app.c`, `ov014/event_pass_power.c`, `ov012/pass_power_check.c` | none named for it | — |
| Entralink and Funfest missions | `ov036/field_palace_sys.c`, `ov033/entralink_warp.c`, `ov033/event_funfest_mission.c`, `ov085/fmission_view*.c`, `ov309/fmission_app*.c`, `ov024`–`ov027` and `ov071`/`ov072` (`fest_mission_*.c`) | `SAVE_BLOCK_FUNFEST` | — |
| Join Avenue | `system/join_avenue_savedata.c`, `ov012/scrcmd_join_avenue_store.c` (its other code is unnamed so far) | `SAVE_BLOCK_JOIN_AVENUE` | — |
| Hidden Grottoes | `ov012/hidden_hollow.c`, `ov036/hidden_hollow_generate.c`, `ov036/scrcmd_hidden_hollow.c` | none named for it | — |
| Pokémon World Tournament | no file named for it yet | `SAVE_BLOCK_TOURNAMENT` | — |
| Medal Rally | `system/medal_box.c`, `ov145/medalbox*.c`, `ov187/medal_info_*.c`, `ov036/scrcmd_medal.c` | `SAVE_BLOCK_MEDAL_BOX` | — |
| Pokéstar Studios | `ov062/pokewood_*.c`, `ov023/event_pokewood.c`, `system/pokewood_savedata.c` | `SAVE_BLOCK_POKEWOOD` | — |
| Memory Link | `system/memory_link_savedata.c`, `system/high_link_savedata.c` | `SAVE_BLOCK_HIGH_LINK` | — |
| Seasons | `system/season.c`, `ov012/season_form.c`, `ov035/event_season_banner.c` | — | — |
| Unova Pokédex | `ov296`–`ov299` (`pokedex_*.c`) | `SAVE_BLOCK_POKEDEX` | — |
| Musical | `ov012/musical_*.c`, `ov209`, `ov210`, `system/musical_savedata.c` | `SAVE_BLOCK_MUSICAL` | — |
| Key System | `ov332/key_system_*.c`, `ov012/scrcmd_keysystem.c`, `system/key_data_savedata.c` | `SAVE_BLOCK_KEY_DATA` | — |
| Dream Radar | `ov018/event_research_radar.c`, `ov310/research_radar.c` | `SAVE_BLOCK_DREAM_RADAR` | — |
| Wi-Fi features (GTS, Global Link, Wi-Fi Club, battles, Geonet) | `ov000`–`ov011` (`event_*`), `ov173`, `ov190`, `ov191`, `ov195`, `ov199`, `ov214`, `ov290`, `ov312` | `SAVE_BLOCK_WORLDTRADE`, `SAVE_BLOCK_WIFI_LIST` and others | — |
| Infrared and wireless (beacons, IR battles and trades, compatibility checks) | `gfl/net_irc_wireless.c`, `ov031/net_irc.c`, `ov083`/`ov084` (`beacon_view*.c`), `ov174`–`ov180` (`irc_*.c`), `ov216` (spin trade) | — | — |

## The C-Gear (`KALEIDO_NO_CGEAR`)

Traced at `41f42ca` (**Verified** in the code):

- Black 2 hands the C-Gear over in Aspertia City, after the first rival battle: `res/field/scripts/aspertia_city.s`
  runs script command `0x197`, `CGearPowerOn`, after "obtained the C-Gear!".
- That command, `Scrcmd_ProcFld_CGearPowerOn` (`src/ov036/scrcmd_proc_fld.c`), is the only caller of
  `CGearSettings_SetOn(..., 1)`. It then starts the event that shows the C-Gear switching on.
- Everything else asks `CGearSettings_IsOn` (`src/system/c_gear_savedata.c`):
  - the field's bottom screen, which stays the "no gear" screen while it is 0
    (`FieldSubscreen_GetOverrideScreen`, `src/ov036/field_subscreen.c`);
  - the start menu's "start the C-Gear?" step (`src/ov162/startmenu.c`);
  - whether wireless communication may start (`GSYS_CanBootGameComm`, `src/system/game_system.c`);
  - the trainer card (`src/ov012/trcard_sys.c`).

With `KALEIDO_NO_CGEAR`, `CGearSettings_IsOn` always says no, and command `0x197` reads its operand and lets the
script go on. A script command that returns FALSE lets the next one run at once (`VM_Run`, `src/system/vm.c`). The
C-Gear's code and data stay in the build.

`CGearSettings_IsOn` is in ARM9 main, and the switch shortens it, so the code after it moves (**Verified**,
2026-11-04). Red's patch went from about 420 KB to 5.9 MB, and its build needs `--allow-stale-secure-area` (R-27),
which every game build passes. Its DSi checks still pass. Taking them out, which would free RAM (R-05), is later work. Black 2's
script still says the C-Gear was obtained: a Kaleido game's own scripts won't hand it out.
