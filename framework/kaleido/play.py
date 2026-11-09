"""kaleido play <game> <route>: runs a game's built ROM in py-desmume (ADR 0005) and drives it with a route, waiting on
the game's state instead of counting frames. On the builder's machine only, never in CI: it needs the ROM.

A route is content/games/<game>/play/<route>.txt. Its steps are separated by commas or lines; # starts a comment:

    start ROUTE SAVE        first, if at all: begin from savestate SAVE of another route of the game, instead of
                            from power-on. Each savestate records the ROM it was made on; when SAVE is missing or
                            comes from another build, ROUTE runs first to make it
    wait N                  run N frames
    KEY[*N][/F]             press KEY (A B X Y L R START SELECT UP DOWN LEFT RIGHT) N times, F frames after each (30)
    hold KEY N              hold KEY for N frames
    walk DIRECTION N [fight]
                            walk N tiles UP, DOWN, LEFT or RIGHT, holding the key until the player's tile has moved
                            that far; fail if something stops the player first. With fight, an event that starts on the
                            way, such as a wild battle in the grass, is pressed through with A, and the walk goes on
    repeat PRESSES until CONDITION [for N] [timeout N]
                            press each of PRESSES in turn until CONDITION holds for N frames (1); fail after timeout
                            frames (36000, ten minutes of game time)
    until CONDITION [for N] [timeout N]
                            run frames until CONDITION holds
    check CONDITION         a playtest check: report whether it holds, and screenshot it when it doesn't
    shot NAME               screenshot to NAME.png
    save NAME / load NAME   savestate to NAME.dst, or restore it

Conditions, each one optionally after `not`:

    field                   the field map is up with the player on it, and no event (script) runs
    event                   an event runs
    zone ZONE               the player is in ZONE (a ZONE_ constant or a number)
    at X Z                  the player stands on tile (X, Z)
    player-visible          the player's actor isn't hidden
    flag FLAG               a saved event flag is set (a constant or a number)
    var VAR OP VALUE        a saved event variable compares as OP (== != < <= > >=) with VALUE (a number or a
                            constant, such as KANTO_STORY_IN_LAB)

Constants come from the game's merged tree: generated/zones.txt, flags.txt and vars.txt, and the `#define`s of
res/field/scripts/*.inc (frlg_story.inc's KANTO_VAR_STORY). The game's state is read through the build's own link
map, build/<game>/engine/build/b2_us/arm9.o.xMAP, so it follows Kaleido's changes to ARM9 and the overlays.

Screenshots and savestates come from the ROM: they go to build/<game>/play/<route>/ and are never committed."""

import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from kaleido.config import ConfigError, Paths
from kaleido.games import Game
from kaleido.hashing import file_hash
from kaleido.validate import constant_values

KEYS = ("A", "B", "X", "Y", "L", "R", "START", "SELECT", "UP", "DOWN", "LEFT", "RIGHT")
PRESS = re.compile(rf"({'|'.join(KEYS)})(?:\*(\d+))?(?:/(\d+))?")
DEFINE = re.compile(r"^\s*#define\s+([A-Z][A-Z0-9_]*)\s+(0x[0-9A-Fa-f]+|\d+)\s*(?://.*)?$", re.MULTILINE)
XMAP_SYMBOL = re.compile(r"^\s+([0-9A-F]{8}) [0-9A-F]{8} \.\w+\s+(\S+)\t", re.MULTILINE)
COMPARISONS = {
    "==": int.__eq__,
    "!=": int.__ne__,
    "<": int.__lt__,
    "<=": int.__le__,
    ">": int.__gt__,
    ">=": int.__ge__,
}
DEFAULT_AFTER = 30
DEFAULT_TIMEOUT = 36_000
PRESS_FRAMES = 6
# A tile's step on the field's grid, x to the right and z down
DIRECTIONS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
# A walk that hasn't moved the player a tile in this many frames is stopped. The first tile also turns the player:
# FireRed's new game, facing down, took more than 40 frames to step left and fewer than 60
WALK_FRAMES_PER_TILE = 90
# After the last tile, the frames the step takes to finish
WALK_SETTLE_FRAMES = 20
# A walk that fights presses A this often until the field is back and has stayed up this long, or fails after the
# timeout: a wild battle at level 5 takes a few thousand frames
FIGHT_AFTER = 30
FIGHT_SETTLE_FRAMES = 60
FIGHT_TIMEOUT = 20_000
MAIN_RAM = range(0x02000000, 0x02400000)
VARS_START = 0x4000
EVENT_FLAG_TEMP_0 = 0x4000
# Beside each savestate, the SHA1 of the ROM it was made on: a savestate holds the RAM of one build only
ROM_ID_SUFFIX = ".rom"
# The routes being run for each other's checkpoints, outermost first, so that a cycle of starts is refused
CHAIN_VARIABLE = "KALEIDO_PLAY_CHAIN"
HARNESS_PYTHON = Path("build/harness-venv/bin/python")
HARNESS_REQUIREMENTS = "framework/requirements-harness.txt"

# The fields the harness reads, and the accessor whose Thumb code proves each offset at pokebw2's pin (the instruction
# halfwords). A build whose accessor reads differently stops the run, instead of reading the wrong memory
ACCESSORS = {
    # GameSystem (include/system/game_system.h)
    "GSYS_GetNowEvent": ((0x6980, 0x4770), "GameSystem.event", 0x18),
    "GSYS_GetGameData": ((0x69C0, 0x4770), "GameSystem.gameData", 0x1C),
    "GSYS_GetField": ((0x6A00, 0x4770), "GameSystem.field", 0x20),
    # GameData (src/system/game_data.c): the player's own state, and the event work
    "GameData_GetPlayerState": ((0x2145, 0x0089, 0x1840, 0x4770), "GameData.playerStates[MINE]", 0x114),
    "GameData_GetEventWork": ((0x216B, 0x0089, 0x5840, 0x4770), "GameData.eventWork", 0x1AC),
}
# In the field's overlays, which are loaded only while the field is
FIELD_ACCESSORS = {
    "Field_GetPlayer": ((0x3094, 0x6800, 0x4770), "Field.player", 0x94),
    "FieldPlayer_GetActor": ((0x6840,), "FieldPlayer.core", 0x4),
    "FieldPlayerCore_GetActor": ((0x69C0, 0x4770), "FieldPlayerCore.actor", 0x1C),
    "CheckActorFlag": ((0x6800, 0x4008, 0x4770), "FieldActor.flags", 0x0),
    "GetGPosX": ((0x213C, 0x5E40, 0x4770), "FieldActor.gx", 0x3C),
    "GetGPosZ": ((0x2140, 0x5E40, 0x4770), "FieldActor.gz", 0x40),
}
# SetActorHidden (src/ov012/field_actor.c)
ACTOR_HIDDEN = 0x4


class PlayError(Exception):
    """A route that can't run, or a game whose state can't be read."""


class Memory:
    """Reads the console's memory; py-desmume's, or a test's."""

    def __init__(self, u8: Callable, u16: Callable, u32: Callable, s16: Callable) -> None:
        self.u8, self.u16, self.u32, self.s16 = u8, u16, u32, s16


def read_symbols(xmap: Path) -> dict[str, int]:
    """Each symbol's address in the link map; the first, for a name that appears in more than one object."""
    symbols: dict[str, int] = {}
    for address, name in XMAP_SYMBOL.findall(xmap.read_text(encoding="utf-8", errors="replace")):
        symbols.setdefault(name, int(address, 16))
    return symbols


def read_names(tree: Path) -> dict[str, dict[str, int]]:
    """The constants a route may name, from the merged tree: zones, flags, vars, and the scripts' #defines."""
    defines = {}
    for include in sorted((tree / "res" / "field" / "scripts").glob("*.inc")):
        defines.update((name, int(value, 0)) for name, value in DEFINE.findall(include.read_text(encoding="utf-8")))
    names = {kind: constant_values(tree, kind) for kind in ("zones", "flags", "vars")}
    for kind in names:
        names[kind] = {**defines, **names[kind]}
    return names


def event_work_count(tree: Path) -> int:
    header = (tree / "include" / "save" / "event_work.h").read_text(encoding="utf-8")
    found = re.search(r"#define EVENT_WORK_COUNT (\d+)", header)
    if not found:
        raise PlayError("include/save/event_work.h has no EVENT_WORK_COUNT")
    return int(found.group(1))


class GameState:
    """The game's state, read from memory through the build's symbols."""

    def __init__(self, memory: Memory, symbols: dict[str, int], work_count: int) -> None:
        missing = [name for name in ("g_GameSystem", *ACCESSORS, *FIELD_ACCESSORS) if name not in symbols]
        if missing:
            raise PlayError(f"the link map has no {', '.join(missing)}")
        self.memory, self.symbols, self.flags_offset = memory, symbols, work_count * 2
        # Each set of accessors is checked once its code is surely loaded: ARM9's once the game system exists, the
        # field's once the field does
        self.checked: set[int] = set()

    def verify(self, accessors: dict) -> None:
        if id(accessors) in self.checked:
            return
        self.checked.add(id(accessors))
        for name, (code, what, offset) in accessors.items():
            address = self.symbols[name] & ~1
            found = tuple(self.memory.u16(address + 2 * i) for i in range(len(code)))
            if found != code:
                raise PlayError(
                    f"{name} at {address:#x} isn't the code that reads {what} at {offset:#x} "
                    f"({' '.join(f'{h:04x}' for h in found)}); pokebw2's structures changed, update kaleido/play.py"
                )

    def _pointer(self, address: int, offset: int = 0) -> int:
        value = self.memory.u32(address + offset)
        return value if value in MAIN_RAM else 0

    def _offset(self, name: str) -> int:
        return {**ACCESSORS, **FIELD_ACCESSORS}[name][2]

    def game_system(self) -> int:
        gsys = self._pointer(self.symbols["g_GameSystem"])
        if gsys:
            self.verify(ACCESSORS)
        return gsys

    def game_data(self) -> int:
        gsys = self.game_system()
        return self._pointer(gsys, self._offset("GSYS_GetGameData")) if gsys else 0

    def event_running(self) -> bool:
        gsys = self.game_system()
        return bool(gsys and self.memory.u32(gsys + self._offset("GSYS_GetNowEvent")))

    def actor(self) -> int:
        """The player's actor, or 0 while the field isn't up."""
        gsys = self.game_system()
        field = self._pointer(gsys, self._offset("GSYS_GetField")) if gsys else 0
        if not field:
            return 0
        self.verify(FIELD_ACCESSORS)
        player = self._pointer(field, self._offset("Field_GetPlayer"))
        core = self._pointer(player, self._offset("FieldPlayer_GetActor")) if player else 0
        return self._pointer(core, self._offset("FieldPlayerCore_GetActor")) if core else 0

    def field(self) -> bool:
        return bool(self.actor()) and not self.event_running()

    def zone(self) -> int | None:
        game_data = self.game_data()
        return self.memory.u16(game_data + self._offset("GameData_GetPlayerState")) if game_data else None

    def tile(self) -> tuple[int, int] | None:
        actor = self.actor()
        if not actor:
            return None
        return self.memory.s16(actor + self._offset("GetGPosX")), self.memory.s16(actor + self._offset("GetGPosZ"))

    def player_visible(self) -> bool:
        actor = self.actor()
        return bool(actor) and not self.memory.u32(actor + self._offset("CheckActorFlag")) & ACTOR_HIDDEN

    def _event_work(self) -> int:
        game_data = self.game_data()
        return self._pointer(game_data, self._offset("GameData_GetEventWork")) if game_data else 0

    def flag(self, flag: int) -> bool | None:
        work = self._event_work()
        if not work:
            return None
        return bool(self.memory.u8(work + self.flags_offset + flag // 8) & (1 << (flag % 8)))

    def var(self, var: int) -> int | None:
        work = self._event_work()
        return self.memory.u16(work + 2 * (var - VARS_START)) if work else None


@dataclass(frozen=True)
class Condition:
    kind: str
    args: tuple
    negated: bool = False
    text: str = ""

    def holds(self, state: GameState) -> bool:
        if self.kind == "field":
            result = state.field()
        elif self.kind == "event":
            result = state.event_running()
        elif self.kind == "zone":
            result = state.zone() == self.args[0]
        elif self.kind == "at":
            result = state.tile() == self.args
        elif self.kind == "player-visible":
            result = state.player_visible()
        elif self.kind == "flag":
            result = bool(state.flag(self.args[0]))
        else:
            value = state.var(self.args[0])
            result = value is not None and COMPARISONS[self.args[1]](value, self.args[2])
        return result != self.negated


FIELD = Condition("field", (), text="field")


@dataclass(frozen=True)
class Step:
    kind: str
    args: tuple
    line: int
    text: str


def _number(word: str, where: str) -> int:
    try:
        return int(word, 0)
    except ValueError:
        raise PlayError(f"{where}: {word!r} isn't a number") from None


def _press(word: str, where: str) -> tuple[str, int, int]:
    found = PRESS.fullmatch(word)
    if not found:
        raise PlayError(f"{where}: {word!r} isn't a press (KEY, KEY*N, KEY/F or KEY*N/F; keys: {' '.join(KEYS)})")
    return found.group(1), int(found.group(2) or 1), int(found.group(3) or DEFAULT_AFTER)


def parse_condition(words: list[str], where: str, names: dict | None) -> Condition:
    """A condition; with names, its constants resolved, and without them (check, which has no tree), as they're
    written."""
    text = " ".join(words)
    negated = bool(words) and words[0] == "not"
    words = words[1:] if negated else words
    kind, args = (words[0], words[1:]) if words else ("", [])

    def value(word: str, list_name: str) -> int:
        if re.fullmatch(r"0x[0-9A-Fa-f]+|\d+", word):
            return int(word, 0)
        if names is None:
            return 0
        if word not in names[list_name]:
            raise PlayError(f"{where}: {word} isn't a constant of generated/{list_name}.txt or the scripts' #defines")
        return names[list_name][word]

    arity = {"field": 0, "event": 0, "player-visible": 0, "zone": 1, "at": 2, "flag": 1, "var": 3}
    if kind not in arity:
        raise PlayError(f"{where}: {kind!r} isn't a condition ({', '.join(arity)})")
    if len(args) != arity[kind]:
        raise PlayError(f"{where}: {kind} takes {arity[kind]} arguments, not {len(args)}")
    if kind == "zone":
        resolved = (value(args[0], "zones"),)
    elif kind == "at":
        resolved = (_number(args[0], where), _number(args[1], where))
    elif kind == "flag":
        resolved = (value(args[0], "flags"),)
        if names is not None and not 0 < resolved[0] < EVENT_FLAG_TEMP_0:
            raise PlayError(f"{where}: flag {args[0]} isn't a saved flag (1 to {EVENT_FLAG_TEMP_0 - 1:#x})")
    elif kind == "var":
        if args[1] not in COMPARISONS:
            raise PlayError(f"{where}: {args[1]!r} isn't a comparison ({' '.join(COMPARISONS)})")
        resolved = (value(args[0], "vars"), args[1], value(args[2], "vars"))
    else:
        resolved = ()
    return Condition(kind, resolved, negated, text)


def _waiting(words: list[str], where: str, names: dict | None) -> tuple[Condition, int, int]:
    """CONDITION [for N] [timeout N]"""
    hold, timeout = 1, DEFAULT_TIMEOUT
    while len(words) >= 2 and words[-2] in ("for", "timeout"):
        if words[-2] == "for":
            hold = _number(words[-1], where)
        else:
            timeout = _number(words[-1], where)
        words = words[:-2]
    return parse_condition(words, where, names), hold, timeout


def parse_route(text: str, names: dict | None = None) -> list[Step]:
    steps = []
    for number, line in enumerate(text.splitlines(), 1):
        for part in line.split("#", 1)[0].split(","):
            words = part.split()
            if not words:
                continue
            where = f"line {number}"
            command, rest = words[0], words[1:]
            if command == "start":
                if steps or len(rest) != 2 or not all(re.fullmatch(r"[\w-]+", word) for word in rest):
                    raise PlayError(f"{where}: start ROUTE SAVE comes first, and once")
                args = tuple(rest)
            elif command == "wait" and len(rest) == 1:
                args = (_number(rest[0], where),)
            elif command == "hold" and len(rest) == 2:
                args = (_press(rest[0], where)[0], _number(rest[1], where))
            elif command == "walk" and len(rest) in (2, 3):
                if rest[0] not in DIRECTIONS:
                    raise PlayError(f"{where}: walk goes {' '.join(DIRECTIONS)}, not {rest[0]!r}")
                if len(rest) == 3 and rest[2] != "fight":
                    raise PlayError(f"{where}: a walk ends with fight or nothing, not {rest[2]!r}")
                args = (rest[0], _number(rest[1], where), len(rest) == 3)
            elif command in ("shot", "save", "load") and len(rest) == 1 and re.fullmatch(r"[\w-]+", rest[0]):
                args = (rest[0],)
            elif command == "repeat" and "until" in rest:
                presses = rest[: rest.index("until")]
                if not presses:
                    raise PlayError(f"{where}: repeat needs presses before until")
                args = (
                    tuple(_press(word, where) for word in presses),
                    *_waiting(rest[len(presses) + 1 :], where, names),
                )
            elif command == "until":
                args = _waiting(rest, where, names)
            elif command == "check":
                args = (parse_condition(rest, where, names),)
            elif PRESS.fullmatch(command) and not rest:
                args = _press(command, where)
                command = "press"
            else:
                raise PlayError(f"{where}: {part.strip()!r} isn't a step")
            steps.append(Step(command, args, number, part.strip()))
    return steps


class Player:
    """The emulator, the game's state, and the route's outputs."""

    def __init__(self, emulator, keys: dict[str, int], state: GameState, out: Path, rom_id: str = "") -> None:
        self.emulator, self.keys, self.state, self.out, self.rom_id = emulator, keys, state, out, rom_id
        self.frames = 0
        self.failed: list[str] = []

    def run(self, frames: int) -> None:
        # Every frame is drawn. Skipping frames (py-desmume's skip_next_frame each frame) ran a quarter faster, but the
        # screenshots then showed frames from long before, and a savestate made so crashed DeSmuME's software 3D
        # renderer when loaded in the lab
        for _ in range(frames):
            self.emulator.cycle(with_joystick=False)
        self.frames += frames

    def press(self, key: str, hold: int = PRESS_FRAMES, after: int = DEFAULT_AFTER) -> None:
        self.emulator.input.keypad_add_key(self.keys[key])
        self.run(hold)
        self.emulator.input.keypad_rm_key(self.keys[key])
        self.run(after)

    def held(self, condition: Condition, frames: int) -> bool:
        """Whether the condition holds now and for the frames after."""
        for _ in range(frames):
            if not condition.holds(self.state):
                return False
            self.run(1)
        return condition.holds(self.state)

    def wait_for(self, step: Step, presses: tuple, condition: Condition, hold: int, timeout: int) -> None:
        start = self.frames
        while self.frames - start < timeout:
            if condition.holds(self.state) and self.held(condition, hold):
                return
            if presses:
                for key, count, after in presses:
                    for _ in range(count):
                        self.press(key, after=after)
            else:
                self.run(1)
        self.shot(f"timeout-line-{step.line}")
        raise PlayError(f"line {step.line}: {condition.text} didn't hold within {timeout} frames ({step.text})")

    def walk(self, step: Step, direction: str, tiles: int, fight: bool = False) -> None:
        """Holds the direction until the player's tile is `tiles` away; the tile turns over as a step starts. With
        fight, an event on the way is pressed through with A, and the walk goes on from where it stopped."""
        start = self.state.tile()
        if start is None:
            raise PlayError(f"line {step.line}: no player to walk ({step.text})")
        dx, dz = DIRECTIONS[direction]
        tile, moved, frames = start, 0, 0
        self.emulator.input.keypad_add_key(self.keys[direction])
        try:
            while moved < tiles:
                if fight and self.state.event_running():
                    self.emulator.input.keypad_rm_key(self.keys[direction])
                    print(f"line {step.line}: an event at {tile}, pressed through with A", flush=True)
                    self.wait_for(step, (("A", 1, FIGHT_AFTER),), FIELD, FIGHT_SETTLE_FRAMES, FIGHT_TIMEOUT)
                    self.emulator.input.keypad_add_key(self.keys[direction])
                    frames = 0
                    continue
                if frames >= WALK_FRAMES_PER_TILE:
                    self.shot(f"stopped-line-{step.line}")
                    raise PlayError(
                        f"line {step.line}: the player stopped at {tile} after {moved} of {tiles} tiles ({step.text})"
                    )
                self.run(1)
                frames += 1
                now = self.state.tile()
                if now is not None and now != tile:
                    if now != (tile[0] + dx, tile[1] + dz):
                        raise PlayError(f"line {step.line}: the player went from {tile} to {now} ({step.text})")
                    tile, moved, frames = now, moved + 1, 0
        finally:
            self.emulator.input.keypad_rm_key(self.keys[direction])
        self.run(WALK_SETTLE_FRAMES)

    def shot(self, name: str) -> None:
        self.emulator.screenshot().save(self.out / f"{name}.png")

    def save(self, name: str) -> None:
        self.emulator.savestate.save_file(str(self.out / f"{name}.dst"))
        (self.out / f"{name}{ROM_ID_SUFFIX}").write_text(self.rom_id + "\n", encoding="utf-8")

    def step(self, step: Step) -> None:
        if step.kind == "wait":
            self.run(step.args[0])
        elif step.kind == "press":
            key, count, after = step.args
            for _ in range(count):
                self.press(key, after=after)
        elif step.kind == "hold":
            self.press(step.args[0], hold=step.args[1], after=0)
        elif step.kind == "walk":
            self.walk(step, *step.args)
        elif step.kind == "repeat":
            self.wait_for(step, *step.args)
        elif step.kind == "until":
            self.wait_for(step, (), *step.args)
        elif step.kind == "check":
            condition = step.args[0]
            if condition.holds(self.state):
                print(f"line {step.line}: ok, {condition.text}", flush=True)
            else:
                self.failed.append(f"line {step.line}: {condition.text}")
                self.shot(f"failed-line-{step.line}")
                print(f"line {step.line}: FAILED, {condition.text}{self.describe()}", flush=True)
        elif step.kind == "shot":
            self.shot(step.args[0])
        elif step.kind == "save":
            self.save(step.args[0])
        elif step.kind == "load":
            self.emulator.savestate.load_file(str(self.out / f"{step.args[0]}.dst"))
        else:
            raise PlayError(f"line {step.line}: start comes before anything else ({step.text})")

    def describe(self) -> str:
        state = self.state
        return f" (zone {state.zone()}, tile {state.tile()}, event {state.event_running()}, frame {self.frames})"


def _desmume():
    """py-desmume, from the harness's virtual environment: the framework itself needs only the standard library."""
    try:
        from desmume.controls import Keys, keymask
        from desmume.emulator import DeSmuME
    except ImportError:
        return None
    return DeSmuME, {key: keymask(getattr(Keys, f"KEY_{key}")) for key in KEYS}


def output_directory(paths: Paths, game: Game, route_name: str) -> Path:
    return paths.root / "build" / game.id / "play" / route_name


def checkpoint_is_current(directory: Path, save: str, rom_id: str) -> bool:
    """Whether a route's savestate exists and was made on this ROM."""
    stamp = directory / f"{save}{ROM_ID_SUFFIX}"
    return (
        (directory / f"{save}.dst").exists() and stamp.exists() and stamp.read_text(encoding="utf-8").strip() == rom_id
    )


def _checkpoint(paths: Paths, game: Game, route_name: str, source: str, save: str, rom_id: str) -> Path:
    """The savestate a route starts from, running the route that makes it first when it's missing or stale."""
    directory = output_directory(paths, game, source)
    if not checkpoint_is_current(directory, save, rom_id):
        chain = [name for name in os.environ.get(CHAIN_VARIABLE, "").split(",") if name] + [route_name]
        if source in chain:
            raise PlayError(f"start {source} {save}: the routes start from each other ({' -> '.join(chain)})")
        print(f"{route_name}: {source}'s {save} is missing or from another build; running {source} first", flush=True)
        result = subprocess.run(
            [sys.executable, str(paths.root / "kaleido"), "play", game.id, source],
            env={**os.environ, CHAIN_VARIABLE: ",".join(chain)},
        )
        if result.returncode != 0 or not checkpoint_is_current(directory, save, rom_id):
            raise PlayError(f"start {source} {save}: {source} didn't pass, or doesn't save {save}")
    return directory / f"{save}.dst"


def main(paths: Paths, game: Game, route_name: str) -> int:
    loaded = _desmume()
    if loaded is None:
        python = paths.root / HARNESS_PYTHON
        # A virtual environment's python is a link to the system's, so the environment is told by sys.prefix
        environment = python.parent.parent
        if python.exists() and Path(sys.prefix).resolve() != environment.resolve():
            os.execv(python, [str(python), str(paths.root / "kaleido"), *sys.argv[1:]])
        raise ConfigError(
            f"py-desmume isn't installed; set up the harness's environment once:\n"
            f"  python3 -m venv {HARNESS_PYTHON.parent.parent} && "
            f"{HARNESS_PYTHON.parent}/pip install -r {HARNESS_REQUIREMENTS}"
        )
    emulator_class, keys = loaded
    route_file = paths.root / "content" / "games" / game.id / "play" / f"{route_name}.txt"
    rom = paths.root / "build" / game.id / f"kaleido-{game.id}.nds"
    tree = paths.root / "build" / game.id / "engine"
    xmap = tree / "build" / "b2_us" / "arm9.o.xMAP"
    for needed, how in ((route_file, "a route of the game"), (rom, "./kaleido build"), (xmap, "./kaleido build")):
        if not needed.exists():
            raise ConfigError(f"no {needed.relative_to(paths.root)}; it comes from {how}")
    try:
        steps = parse_route(route_file.read_text(encoding="utf-8"), read_names(tree))
        symbols, work_count = read_symbols(xmap), event_work_count(tree)
        rom_id = file_hash(rom, "sha1")
        checkpoint = None
        if steps and steps[0].kind == "start":
            checkpoint = _checkpoint(paths, game, route_name, *steps[0].args, rom_id)
            steps = steps[1:]
        out = output_directory(paths, game, route_name)
        # A run starts clean, so that a screenshot of an earlier run's failure can't be taken for this one's
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        emulator = emulator_class()
        emulator.open(str(rom))
        if checkpoint is not None:
            emulator.savestate.load_file(str(checkpoint))
        memory = Memory(
            emulator.memory.unsigned.read_byte,
            emulator.memory.unsigned.read_short,
            emulator.memory.unsigned.read_long,
            emulator.memory.signed.read_short,
        )
        player = Player(emulator, keys, GameState(memory, symbols, work_count), out, rom_id)
        start = time.monotonic()
        for step in steps:
            player.step(step)
    except PlayError as error:
        raise ConfigError(f"{route_file.relative_to(paths.root)}: {error}") from error
    elapsed = time.monotonic() - start
    print(f"{player.frames} frames in {elapsed:.0f} s; outputs in {out.relative_to(paths.root)}")
    if player.failed:
        print(f"{len(player.failed)} checks failed: {'; '.join(player.failed)}")
        return 1
    return 0
