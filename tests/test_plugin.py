"""Behaviour of the Lucasfilm Quotes plugin: the text, the layout, the choice and the data file."""

import json
import re

import pytest
from src.devices import BoardContext
from src.plugins.base import OptionsRequest, OptionsUnavailable

from plugins import lucasfilm_quotes as lf
from plugins.lucasfilm_quotes import (
    BARE,
    FULL,
    OVERFLOW,
    Quote,
    QuotesError,
    align,
    choose,
    name_line,
    name_variants,
    parse_collection,
    parse_keys,
    place,
    to_board_text,
    truncate,
    wrap,
)

from .conftest import BLASTER, FRIENDS, KALI, POWER, QUOTES, SNAKES, SPEECH, TRAP, TRY, collection

NOTE = BoardContext.from_device_type("note")
FLAGSHIP = BoardContext.from_device_type("flagship")


def quote(entry):
    """The parsed :class:`Quote` for one fixture entry."""
    return parse_collection(collection(entry))[0]


def render(plugin, board=FLAGSHIP):
    """One fresh render, past the base class's result cache."""
    plugin.clear_cache()
    return plugin.get_data(board)


class TestBoardText:
    def test_text_is_uppercased(self):
        assert to_board_text("It's a trap!") == "IT'S A TRAP!"

    def test_curly_quotes_and_dashes_become_the_boards_own(self):
        assert to_board_text("I’m “fine” – really…") == 'I\'M "FINE" - REALLY...'

    def test_accents_are_dropped(self):
        assert to_board_text("Chirrut Îmwe, Padmé") == "CHIRRUT IMWE, PADME"

    def test_characters_without_a_tile_are_left_out(self):
        assert to_board_text("Use * the Force") == "USE THE FORCE"

    def test_whitespace_collapses(self):
        assert to_board_text("  Never tell \n me   the odds ") == "NEVER TELL ME THE ODDS"


class TestWrap:
    def test_rows_break_between_words(self):
        assert wrap("SNAKES. WHY'D IT HAVE TO BE SNAKES?", 15) == ["SNAKES. WHY'D", "IT HAVE TO BE", "SNAKES?"]

    def test_a_word_longer_than_a_row_is_split(self):
        assert wrap("A WOOKIEEEEEEEE", 8) == ["A", "WOOKIEEE", "EEEEE"]

    def test_nothing_gives_no_rows(self):
        assert wrap("", 15) == []


class TestNames:
    def test_the_full_name_comes_first_then_the_short_ones(self):
        assert name_variants("Obi-Wan Kenobi", ("Obi-Wan",)) == ["Obi-Wan Kenobi", "Obi-Wan"]

    def test_a_name_without_short_ones_stays_as_it_is(self):
        assert name_variants("Yoda") == ["Yoda"]

    def test_repeats_and_blanks_are_left_out(self):
        assert name_variants(" Chewbacca ", ("Chewbacca", "")) == ["Chewbacca"]

    def test_the_longest_name_that_fits_is_used(self):
        assert name_line("Admiral Ackbar", ("Ackbar",), 22) == "- ADMIRAL ACKBAR"
        assert name_line("Admiral Ackbar", ("Ackbar",), 15) == "- ACKBAR"

    def test_a_name_that_never_fits_is_left_off(self):
        assert name_line("Palpatine", (), 8) == ""


class TestTruncate:
    def test_the_last_row_ends_in_an_ellipsis(self):
        assert truncate(["ONE", "TWO", "THREE"], 2, 15) == ["ONE", "TWO..."]

    def test_a_full_last_row_gives_up_its_last_word(self):
        assert truncate(["HOKEY RELIGIONS", "AND"], 1, 15) == ["HOKEY..."]

    def test_a_row_without_spaces_is_cut_short(self):
        assert truncate(["ABCDEFGHIJKLMNO"], 1, 15) == ["ABCDEFGHIJKL..."]

    def test_trailing_punctuation_is_not_doubled(self):
        assert truncate(["SNAKES,", "WHY"], 1, 15) == ["SNAKES..."]

    def test_no_rows_stay_no_rows(self):
        assert truncate([], 3, 15) == []


class TestAlign:
    @pytest.mark.parametrize(("alignment", "row"), [("center", " AB  "), ("left", "AB   "), ("right", "   AB")])
    def test_rows_are_padded_to_the_board(self, alignment, row):
        assert align("AB", 5, alignment) == row


class TestPlace:
    def test_a_short_quote_fits_a_note_with_its_short_name(self):
        placement = place(quote(TRAP), 15, 3, show_name=True, alignment="center")
        assert placement.fit == FULL
        assert placement.rows == [" IT'S A TRAP!  ", "               ", "   - ACKBAR    "]

    def test_a_quote_that_fills_the_board_is_shown_without_its_name(self):
        placement = place(quote(TRY), 15, 3, show_name=True, alignment="center")
        assert placement.fit == BARE
        assert not any(row.strip().startswith("-") for row in placement.rows)

    def test_a_name_too_long_for_any_row_makes_the_fit_bare(self):
        assert place(quote(POWER), 15, 3, show_name=True, alignment="center").fit == FULL
        assert place(quote(POWER), 6, 6, show_name=True, alignment="center").fit == BARE

    def test_with_the_name_turned_off_every_quote_that_fits_is_full(self):
        assert place(quote(TRY), 15, 3, show_name=False, alignment="center").fit == FULL

    def test_the_quote_is_signed_with_the_name_from_its_movie(self):
        rows = place(quote(FRIENDS), 22, 6, show_name=True, alignment="center").rows
        assert "- THE EMPEROR" in [row.strip() for row in rows]

    def test_left_aligned_quotes_are_signed_flush_right(self):
        rows = place(quote(TRAP), 15, 3, show_name=True, alignment="left").rows
        assert rows == ["IT'S A TRAP!   ", "               ", "       - ACKBAR"]

    def test_a_long_quote_only_fits_a_flagship(self):
        assert place(quote(BLASTER), 15, 3, show_name=True, alignment="center").fit == OVERFLOW
        assert place(quote(BLASTER), 22, 6, show_name=True, alignment="center").fit == FULL

    def test_a_quote_longer_than_the_board_is_cut_off(self):
        placement = place(quote(SPEECH), 22, 6, show_name=True, alignment="center")
        assert placement.fit == OVERFLOW
        assert placement.spill > 0
        assert placement.rows[-1].rstrip().endswith("...")

    def test_a_word_too_long_for_a_row_does_not_count_as_fitting(self):
        long_word = Quote(id=0, text="Chewbacca!", character="Han Solo", character_id="han_solo")
        assert place(long_word, 5, 3, show_name=False, alignment="center").fit == OVERFLOW

    @pytest.mark.parametrize("entry", QUOTES)
    @pytest.mark.parametrize(("width", "height"), [(15, 3), (22, 6), (30, 6)])
    def test_every_row_is_exactly_as_wide_as_the_board(self, entry, width, height):
        rows = place(quote(entry), width, height, show_name=True, alignment="center").rows
        assert len(rows) == height
        assert all(len(row) == width for row in rows)


class TestChoose:
    def test_only_quotes_that_fit_are_chosen(self):
        quotes = parse_collection(collection(*QUOTES))
        chosen = {choose(quotes, 15, 3, show_name=True, alignment="center")[0].text for _ in range(300)}
        assert chosen == {entry["text"] for entry in (TRAP, TRY, SNAKES, FRIENDS, POWER, KALI)}

    def test_a_flagship_gets_the_long_ones_too(self):
        quotes = parse_collection(collection(*QUOTES))
        chosen = {choose(quotes, 22, 6, show_name=True, alignment="center")[0].text for _ in range(300)}
        assert BLASTER["text"] in chosen
        assert SPEECH["text"] not in chosen

    def test_a_quote_shown_lately_is_passed_over(self):
        quotes = parse_collection(collection(TRAP, POWER))
        lf.remember_shown(quotes[0])
        assert all(choose(quotes, 15, 3, show_name=True, alignment="center")[0] == quotes[1] for _ in range(20))

    def test_when_all_were_shown_lately_the_oldest_comes_next(self):
        quotes = parse_collection(collection(TRAP, POWER, TRY))
        for index in (1, 0, 2):
            lf.remember_shown(quotes[index])
        assert choose(quotes, 15, 3, show_name=True, alignment="center")[0] == quotes[1]

    def test_showing_a_quote_again_makes_it_the_most_recent(self):
        quotes = parse_collection(collection(TRAP, POWER))
        lf.remember_shown(quotes[0])
        lf.remember_shown(quotes[1])
        lf.remember_shown(quotes[0])
        assert choose(quotes, 15, 3, show_name=True, alignment="center")[0] == quotes[1]

    def test_signed_only_keeps_the_quotes_with_room_for_the_name(self):
        quotes = parse_collection(collection(TRAP, TRY, SNAKES, POWER))
        chosen = {
            choose(quotes, 15, 3, show_name=True, alignment="center", signed_only=True)[0].text for _ in range(100)
        }
        assert chosen == {TRAP["text"], POWER["text"]}

    def test_signed_only_takes_any_that_fits_when_none_has_room_for_the_name(self):
        quotes = parse_collection(collection(TRY, SNAKES, BLASTER))
        chosen = {
            choose(quotes, 15, 3, show_name=True, alignment="center", signed_only=True)[0].text for _ in range(100)
        }
        assert chosen == {TRY["text"], SNAKES["text"]}

    def test_when_nothing_fits_the_least_overflowing_quote_is_cut_off(self):
        quotes = parse_collection(collection(SPEECH, BLASTER))
        chosen, placement = choose(quotes, 15, 3, show_name=True, alignment="center")
        assert chosen.text == BLASTER["text"]
        assert placement.fit == OVERFLOW


class TestSettings:
    @pytest.mark.parametrize(
        ("value", "keys"),
        [(None, []), ("", []), ([], []), (["yoda", " han_solo "], ["yoda", "han_solo"]), (["", "x"], ["x"])],
    )
    def test_keys_are_read_from_the_picker(self, value, keys):
        assert parse_keys(value) == keys

    @pytest.mark.parametrize("value", ["yoda", [1], [None], {"yoda": True}])
    def test_anything_else_is_unreadable(self, value):
        assert parse_keys(value) is None

    def test_unreadable_keys_are_reported(self, make_plugin):
        errors = make_plugin().validate_config({"franchises": "star_wars", "movies": [3], "characters": {"a": 1}})
        assert any("Franchises" in error for error in errors)
        assert any("Movies" in error for error in errors)
        assert any("Characters" in error for error in errors)

    def test_a_valid_config_has_no_errors(self, make_plugin):
        config = {"franchises": ["star_wars"], "movies": [], "characters": ["yoda"], "refresh_seconds": 3600}
        assert make_plugin().validate_config(config) == []


class TestCollection:
    def test_each_quote_gets_its_character_movie_and_franchise(self):
        parsed = quote(TRAP)
        assert (parsed.character, parsed.character_id, parsed.short_names) == (
            "Admiral Ackbar",
            "admiral_ackbar",
            ("Ackbar",),
        )
        assert (parsed.movie, parsed.movie_id, parsed.year) == (
            "Star Wars: Episode VI – Return of the Jedi",
            "return_of_the_jedi",
            1983,
        )
        assert (parsed.franchise, parsed.franchise_id) == ("Star Wars", "star_wars")

    def test_a_movie_outside_a_franchise_has_none(self):
        assert (quote(POWER).franchise, quote(POWER).franchise_id) == ("", "")

    def test_a_franchise_the_file_does_not_list_is_no_franchise(self):
        body = collection(TRAP, movies={"return_of_the_jedi": {"name": "Jedi", "year": 1983, "franchise": "trek"}})
        assert parse_collection(body)[0].franchise_id == ""

    def test_a_year_that_is_not_a_number_is_no_year(self):
        body = collection(TRAP, movies={"return_of_the_jedi": {"name": "Jedi", "year": "1983"}})
        assert parse_collection(body)[0].year is None

    def test_the_signature_is_the_name_from_the_movie_or_else_the_characters(self):
        assert (quote(FRIENDS).character, quote(FRIENDS).signature) == ("Palpatine", "The Emperor")
        assert quote(TRAP).signature == "Admiral Ackbar"

    def test_unusable_quotes_are_left_out(self):
        body = collection(
            TRAP,
            "not a quote",
            {"character": "yoda", "movie": "empire_strikes_back", "text": "  "},
            {"character": "nobody", "movie": "empire_strikes_back", "text": "Who?"},
            {"character": "yoda", "movie": "holiday_special", "text": "Who?"},
            {"character": "yoda", "text": "Where?"},
            {"character": "yoda", "movie": "empire_strikes_back"},
        )
        assert [parsed.text for parsed in parse_collection(body)] == [TRAP["text"]]

    def test_quotes_are_numbered_by_their_place_in_the_file(self):
        assert [parsed.id for parsed in parse_collection(collection(TRAP, POWER))] == [0, 1]

    @pytest.mark.parametrize(
        "body", [{}, {"quotes": "x", "characters": [], "movies": None, "franchises": 3}, collection()]
    )
    def test_a_file_without_usable_quotes_is_an_error(self, body):
        with pytest.raises(QuotesError):
            parse_collection(body)

    def test_swearing_is_recognised_in_whole_words_only(self):
        assert lf.has_swearing(quote(KALI))
        assert not lf.has_swearing(quote(TRAP))
        assert not lf.has_swearing(Quote(id=0, text="Hello there.", character="Obi-Wan", character_id="obi"))


@pytest.fixture(scope="module")
def body():
    """The real quotes.json."""
    return json.loads(lf.QUOTES_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def quotes(body):
    return parse_collection(body)


class TestDataFile:
    """The quotes that ship with the plugin."""

    def test_every_quote_is_usable(self, body, quotes):
        assert len(quotes) == len(body["quotes"]) == 537

    def test_no_quote_is_there_twice_in_a_movie(self, quotes):
        texts = [(quote.movie_id, re.sub(r"[^A-Z ]", "", to_board_text(quote.text))) for quote in quotes]
        assert len(set(texts)) == len(texts)

    def test_every_quote_reads_on_the_board_as_written(self, quotes):
        """Nothing is dropped for want of a tile."""
        for quote in quotes:
            assert len(to_board_text(quote.text)) == len(quote.text), quote.text

    def test_every_quote_ends_like_a_sentence(self, quotes):
        for quote in quotes:
            assert quote.text[-1] in '.!?"', quote.text

    def test_every_franchise_movie_and_character_is_quoted(self, body, quotes):
        assert {quote.character_id for quote in quotes} == set(body["characters"])
        assert {quote.movie_id for quote in quotes} == set(body["movies"])
        assert {quote.franchise_id for quote in quotes} - {""} == set(body["franchises"])

    def test_every_movie_has_a_year(self, quotes):
        assert all(quote.year for quote in quotes)

    def test_short_names_are_shorter_and_longest_first(self, body):
        for key, character in body["characters"].items():
            lengths = [len(character["name"])] + [len(name) for name in character["short_names"]]
            assert lengths == sorted(lengths, reverse=True), key
            assert len(set(lengths)) == len(lengths), key

    def test_every_name_fits_a_note_in_some_form(self, quotes):
        for quote in quotes:
            assert name_line(quote.signature, quote.short_names, 15), quote.signature

    def test_a_note_and_a_flagship_have_plenty_to_choose_from(self, quotes):
        def fitting(width, height):
            return sum(
                place(quote, width, height, show_name=True, alignment="center").fit > OVERFLOW for quote in quotes
            )

        assert fitting(15, 3) >= 200
        assert fitting(22, 6) >= 500

    def test_a_note_has_enough_quotes_with_room_for_the_name(self, quotes):
        signed = sum(place(quote, 15, 3, show_name=True, alignment="center").fit == FULL for quote in quotes)
        assert signed >= 90

    def test_the_file_is_read_once(self, monkeypatch, tmp_path):
        path = tmp_path / "quotes.json"
        path.write_text(json.dumps(collection(POWER)))
        monkeypatch.setattr(lf, "QUOTES_FILE", path)
        lf.load_quotes.cache_clear()
        try:
            assert [quote.text for quote in lf.load_quotes()] == [POWER["text"]]
            path.write_text(json.dumps(collection(TRAP)))
            assert [quote.text for quote in lf.load_quotes()] == [POWER["text"]]
        finally:
            lf.load_quotes.cache_clear()

    @pytest.mark.parametrize(
        ("content", "message"), [(None, "could not be read"), ("{", "could not be read"), ("[]", "not a JSON object")]
    )
    def test_an_unreadable_file_is_an_error(self, monkeypatch, tmp_path, content, message):
        path = tmp_path / "quotes.json"
        if content is not None:
            path.write_text(content)
        monkeypatch.setattr(lf, "QUOTES_FILE", path)
        lf.load_quotes.cache_clear()
        try:
            with pytest.raises(QuotesError, match=message):
                lf.load_quotes()
        finally:
            lf.load_quotes.cache_clear()


class TestRendering:
    def test_a_note_shows_a_quote_that_fits_it(self, make_plugin):
        result = render(make_plugin(), NOTE)
        assert result.available
        assert len(result.formatted_lines) == 3
        assert to_board_text(BLASTER["text"]) != result.data["quote"]

    def test_the_variables_are_board_text(self, make_plugin, source):
        source.body = collection(TRAP)
        data = render(make_plugin()).data
        assert data["quote"] == "IT'S A TRAP!"
        assert data["character"] == "ADMIRAL ACKBAR"
        assert data["movie"] == "STAR WARS: EPISODE VI - RETURN OF THE JEDI"
        assert data["year"] == "1983"
        assert data["franchise"] == "STAR WARS"

    def test_the_character_variable_is_the_name_from_the_movie(self, make_plugin, source):
        source.body = collection(FRIENDS)
        assert render(make_plugin()).data["character"] == "THE EMPEROR"

    def test_a_movie_outside_a_franchise_leaves_the_franchise_empty(self, make_plugin, source):
        source.body = collection(POWER)
        data = render(make_plugin()).data
        assert (data["movie"], data["franchise"]) == ("LABYRINTH", "")

    def test_the_block_is_the_board_and_the_lines_its_rows(self, make_plugin):
        result = render(make_plugin(), NOTE)
        assert result.data["block"] == "\n".join(result.formatted_lines)
        assert [result.data[f"line{index}"] for index in range(1, 4)] == result.formatted_lines
        assert result.data["line4"] == result.data["line5"] == result.data["line6"] == ""

    def test_without_a_board_the_flagship_shape_is_used(self, make_plugin):
        result = make_plugin().get_data()
        assert len(result.formatted_lines) == 6
        assert all(len(row) == 22 for row in result.formatted_lines)

    def test_the_name_can_be_turned_off(self, make_plugin, source):
        source.body = collection(TRAP)
        assert render(make_plugin(character_name="never"), NOTE).formatted_lines == [
            "               ",
            " IT'S A TRAP!  ",
            "               ",
        ]

    def test_an_unknown_name_setting_means_when_it_fits(self, make_plugin, source):
        source.body = collection(TRAP)
        assert render(make_plugin(character_name="loud"), NOTE).formatted_lines[-1] == "   - ACKBAR    "

    def test_the_alignment_follows_the_setting_and_ignores_an_unknown_one(self, make_plugin, source):
        source.body = collection(TRAP)
        assert render(make_plugin(alignment="left"), NOTE).formatted_lines[0] == "IT'S A TRAP!   "
        assert render(make_plugin(alignment="justify"), NOTE).formatted_lines[0] == " IT'S A TRAP!  "

    def test_only_the_chosen_franchises_are_quoted(self, make_plugin):
        plugin = make_plugin(franchises=["indiana_jones"])
        seen = {render(plugin, NOTE).data["character"] for _ in range(60)}
        assert seen == {"INDIANA JONES"}

    def test_franchises_and_movies_add_up(self, make_plugin):
        plugin = make_plugin(franchises=["indiana_jones"], movies=["labyrinth"])
        seen = {render(plugin, NOTE).data["movie"] for _ in range(80)}
        assert seen == {
            "RAIDERS OF THE LOST ARK",
            "INDIANA JONES AND THE TEMPLE OF DOOM",
            "LABYRINTH",
        }

    def test_characters_narrow_down_the_franchises_and_movies(self, make_plugin):
        plugin = make_plugin(franchises=["star_wars"], characters=["yoda", "sarah_williams"])
        seen = {render(plugin, NOTE).data["character"] for _ in range(40)}
        assert seen == {"YODA"}

    def test_characters_alone_come_from_any_movie(self, make_plugin):
        plugin = make_plugin(characters=["indiana_jones"])
        seen = {render(plugin, NOTE).data["movie"] for _ in range(60)}
        assert seen == {"RAIDERS OF THE LOST ARK", "INDIANA JONES AND THE TEMPLE OF DOOM"}

    def test_always_signed_picks_only_quotes_with_room_for_the_name(self, make_plugin):
        plugin = make_plugin(character_name="always")
        rows = [render(plugin, NOTE).formatted_lines for _ in range(40)]
        assert all(lines[-1].strip().startswith("- ") for lines in rows)

    def test_when_it_fits_also_picks_quotes_without_room_for_the_name(self, make_plugin):
        plugin = make_plugin(character_name="fits")
        seen = {render(plugin, NOTE).data["quote"] for _ in range(100)}
        assert to_board_text(TRY["text"]) in seen

    def test_swearing_can_be_skipped(self, make_plugin, source):
        source.body = collection(KALI, POWER)
        plugin = make_plugin(skip_swearing=True)
        assert {render(plugin, NOTE).data["quote"] for _ in range(30)} == {"YOU HAVE NO POWER OVER ME!"}

    def test_swearing_is_kept_by_default(self, make_plugin, source):
        source.body = collection(KALI)
        assert render(make_plugin(), NOTE).data["quote"] == "PREPARE TO MEET KALI... IN HELL!"

    def test_a_selection_without_quotes_leaves_the_plugin_unavailable(self, make_plugin):
        result = render(make_plugin(movies=["labyrinth"], characters=["yoda"]))
        assert not result.available
        assert "chosen franchises, movies and characters" in result.error

    def test_an_unreachable_collection_leaves_the_plugin_unavailable(self, make_plugin, source):
        source.body = QuotesError("the quote collection is unreachable: offline")
        result = render(make_plugin())
        assert not result.available
        assert "unreachable" in result.error

    def test_a_malformed_file_does_not_break_the_render_loop(self, make_plugin, source):
        source.body = {
            "quotes": [{"character": "yoda", "movie": "m", "text": "Hi"}],
            "characters": {"yoda": "Yoda"},
            "movies": {"m": {"name": "M"}},
        }
        result = render(make_plugin())
        assert not result.available

    def test_an_unexpected_failure_does_not_break_the_render_loop(self, make_plugin, monkeypatch):
        def broken(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(lf, "load_quotes", broken)
        result = render(make_plugin())
        assert not result.available
        assert result.error == "boom"


class TestOptions:
    def test_franchises_are_listed_by_name_without_the_standalone_movies(self, make_plugin, source):
        source.body = collection(TRAP, TRY, SNAKES, POWER)
        options = make_plugin().get_options(OptionsRequest("franchises")).options
        assert [(option.value, option.label, option.description) for option in options] == [
            ("indiana_jones", "Indiana Jones", "1 quote"),
            ("star_wars", "Star Wars", "2 quotes"),
        ]

    def test_movies_are_listed_in_release_order_with_year_and_franchise(self, make_plugin, source):
        source.body = collection(POWER, TRAP, SNAKES, FRIENDS)
        options = make_plugin().get_options(OptionsRequest("movies")).options
        assert [(option.value, option.description) for option in options] == [
            ("raiders_of_the_lost_ark", "1981 · Indiana Jones · 1 quote"),
            ("return_of_the_jedi", "1983 · Star Wars · 2 quotes"),
            ("labyrinth", "1986 · 1 quote"),
        ]

    def test_characters_are_listed_by_name_with_where_they_are_quoted_from(self, make_plugin, source):
        source.body = collection(TRAP, SNAKES, KALI, POWER, FRIENDS)
        options = make_plugin().get_options(OptionsRequest("characters")).options
        assert [(option.value, option.label, option.description) for option in options] == [
            ("admiral_ackbar", "Admiral Ackbar", "Star Wars · 1 quote"),
            ("indiana_jones", "Indiana Jones", "Indiana Jones · 2 quotes"),
            ("palpatine", "Palpatine", "Star Wars · 1 quote"),
            ("sarah_williams", "Sarah Williams", "Labyrinth · 1 quote"),
        ]

    def test_typing_filters_by_any_part_of_the_name(self, make_plugin):
        options = make_plugin().get_options(OptionsRequest("movies", query=" STAR WARS ")).options
        assert [option.value for option in options] == ["a_new_hope", "empire_strikes_back", "return_of_the_jedi"]

    def test_the_list_is_cut_to_the_limit_but_counts_all(self, make_plugin):
        result = make_plugin().get_options(OptionsRequest("characters", limit=2))
        assert len(result.options) == 2
        assert result.total == 7

    def test_an_unreachable_collection_is_a_hint_not_a_crash(self, make_plugin, source):
        source.body = QuotesError("down")
        with pytest.raises(OptionsUnavailable):
            make_plugin().get_options(OptionsRequest("movies"))

    def test_other_pickers_are_left_to_the_base_class(self, make_plugin):
        with pytest.raises(NotImplementedError):
            make_plugin().get_options(OptionsRequest("planets"))
