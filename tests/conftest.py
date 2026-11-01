"""Shared fixtures for the Lucasfilm Quotes plugin tests.

The plugin tests run on a small hand-built collection in quotes.json's shape,
not on the real file, so a change to the quotes never breaks a test of the
layout. The real file has tests of its own.
"""

import json
import pathlib

import pytest

from plugins import lucasfilm_quotes as lf
from plugins.lucasfilm_quotes import LucasfilmQuotesPlugin

MANIFEST = json.loads((pathlib.Path(__file__).resolve().parent.parent / "manifest.json").read_text())

FRANCHISES = {
    "star_wars": {"name": "Star Wars"},
    "indiana_jones": {"name": "Indiana Jones"},
}

MOVIES = {
    "a_new_hope": {"name": "Star Wars: Episode IV – A New Hope", "year": 1977, "franchise": "star_wars"},
    "empire_strikes_back": {
        "name": "Star Wars: Episode V – The Empire Strikes Back",
        "year": 1980,
        "franchise": "star_wars",
    },
    "raiders_of_the_lost_ark": {"name": "Raiders of the Lost Ark", "year": 1981, "franchise": "indiana_jones"},
    "return_of_the_jedi": {
        "name": "Star Wars: Episode VI – Return of the Jedi",
        "year": 1983,
        "franchise": "star_wars",
    },
    "temple_of_doom": {"name": "Indiana Jones and the Temple of Doom", "year": 1984, "franchise": "indiana_jones"},
    "labyrinth": {"name": "Labyrinth", "year": 1986, "franchise": None},
}

CHARACTERS = {
    "admiral_ackbar": {"name": "Admiral Ackbar", "short_names": ["Ackbar"]},
    "darth_vader": {"name": "Darth Vader", "short_names": ["Vader"]},
    "han_solo": {"name": "Han Solo", "short_names": ["Han"]},
    "indiana_jones": {"name": "Indiana Jones", "short_names": ["Indy"]},
    "obi_wan_kenobi": {"name": "Obi-Wan Kenobi", "short_names": ["Obi-Wan"]},
    "palpatine": {"name": "Palpatine", "short_names": []},
    "sarah_williams": {"name": "Sarah Williams", "short_names": ["Sarah"]},
    "yoda": {"name": "Yoda", "short_names": []},
}

# Fits a Note with its name, shortened: one row of quote, a blank and "- ACKBAR".
TRAP = {"character": "admiral_ackbar", "movie": "return_of_the_jedi", "text": "It's a trap!"}
# Fits a Note only without a name: three rows of quote.
TRY = {"character": "yoda", "movie": "empire_strikes_back", "text": "Do. Or do not. There is no try."}
# Fits a Note only without a name; fits a 2x2 note array with it.
SNAKES = {
    "character": "indiana_jones",
    "movie": "raiders_of_the_lost_ark",
    "text": "Snakes. Why'd it have to be snakes?",
}
# Too long for a Note; fits a Flagship with its name.
BLASTER = {
    "character": "han_solo",
    "movie": "a_new_hope",
    "text": "Hokey religions and ancient weapons are no match for a good blaster at your side, kid.",
}
# Signed with the name the character goes by in this movie.
FRIENDS = {
    "character": "palpatine",
    "movie": "return_of_the_jedi",
    "text": "Your faith in your friends is yours.",
    "as": "The Emperor",
}
# Fits a Note with its name, from a movie outside any franchise.
POWER = {"character": "sarah_williams", "movie": "labyrinth", "text": "You have no power over me!"}
# Fits a Note without its name, and has swearing in it.
KALI = {"character": "indiana_jones", "movie": "temple_of_doom", "text": "Prepare to meet Kali... in hell!"}
# Longer than any board.
SPEECH = {
    "character": "obi_wan_kenobi",
    "movie": "a_new_hope",
    "text": (
        "You must learn the ways of the Force if you're to come with me to Alderaan, for the Force will be with "
        "you, always, and an elegant weapon for a more civilized age."
    ),
}

QUOTES = [TRAP, TRY, SNAKES, BLASTER, FRIENDS, POWER, KALI, SPEECH]

# The quotes the committed previews were rendered from, one per board.
PREVIEW_QUOTES = {"note": TRAP, "flagship": BLASTER, "note_array": SNAKES}


def collection(*quotes, franchises=None, movies=None, characters=None):
    """A data file holding *quotes*, shaped like the real ``quotes.json``."""
    return {
        "franchises": FRANCHISES if franchises is None else franchises,
        "movies": MOVIES if movies is None else movies,
        "characters": CHARACTERS if characters is None else characters,
        "quotes": list(quotes),
    }


class FakeData:
    """Stands in for quotes.json: *body* is what the file holds, or the error reading it raises."""

    def __init__(self):
        self.body = collection(*QUOTES)

    def __call__(self):
        if isinstance(self.body, Exception):
            raise self.body
        return lf.parse_collection(self.body)


@pytest.fixture(autouse=True)
def fresh_memory():
    """Each test starts with no quotes remembered as recently shown."""
    lf.clear_recent()
    yield
    lf.clear_recent()


@pytest.fixture
def manifest():
    return MANIFEST


@pytest.fixture
def source(monkeypatch):
    fake = FakeData()
    monkeypatch.setattr(lf, "load_quotes", fake)
    return fake


@pytest.fixture
def make_plugin(source):
    """Build a configured plugin instance whose quotes come from the fake collection."""

    def _make(**config):
        plugin = LucasfilmQuotesPlugin(MANIFEST)
        plugin.config = dict(config)
        return plugin

    return _make
