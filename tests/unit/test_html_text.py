"""What ``tools.html_text`` does with the HTML a mail body actually is.

Every line of this file corresponds to a measurement against this working tree with lxml
6.1.1 (``10-RESEARCH.md``, section "HTML zu Text"), so these tests are a regression guard
over one library version and not a wish list: where the measurement showed a rough edge (the
leftover of an internal DTD subset, a non breaking space that stays one), the measured value
is written down as the expectation instead of a nicer one that no run produced.

Pure function tests, no network and no fixtures: the function takes a string and returns a
string, and everything that reaches it was written by a stranger.
"""

from pathlib import Path

from mcp_connector.tools.html_text import to_text

#: Appears in this file and nowhere else. If an external entity were ever resolved, the file
#: it points at would be this one, and this word would turn up in the converted text.
SENTINEL = "kanarienvogel-4711"


def test_an_empty_body_becomes_empty_text_instead_of_raising() -> None:
    """Measured: ``document_fromstring("")`` and ``("   ")`` raise ``ParserError``.

    A mail without a body is ordinary (attachments only), and with HTTP 206 the body is
    missing by design, so the empty case must be the cheapest one and not a crash in the
    full text path (T-10-15).
    """
    assert to_text("") == ""
    assert to_text("   ") == ""
    assert to_text("\n") == ""
    assert to_text("\n\t \r\n") == ""


def test_entities_come_back_as_the_characters_they_stand_for() -> None:
    """The half ``lxml`` buys: named and numeric entities, resolved once and correctly."""
    text = to_text("<p>A&amp;B, &uuml;ber, hei&szlig;t, x&nbsp;y, 100&#8364;</p>")

    assert text == "A&B, über, heißt, x\xa0y, 100€", (
        "the non breaking space stays a non breaking space: it is what the sender wrote, "
        "and rewriting it would be a second opinion about foreign text"
    )


def test_a_plain_text_mail_in_the_form_the_app_delivers_becomes_readable_prose() -> None:
    """Trap 4, the most expensive one of the family, and correction K2 of the research.

    Even without an HTML part the body runs through ``convertLinks``, so through
    ``htmlspecialchars`` and HTMLPurifier. A converter that looked at ``hasHtmlBody`` would
    hand ``Gr&uuml;&szlig;e`` and ``<a href=...>`` to the model for every text mail.
    """
    body = (
        "Gr&uuml;&szlig;e aus Hamburg,<br>"
        "die Stra&szlig;e ist gesperrt.<br>"
        '<a href="https://example.org/x">https://example.org/x</a>'
    )

    text = to_text(body)

    assert "Grüße aus Hamburg," in text
    assert "die Straße ist gesperrt." in text
    assert "https://example.org/x" in text
    assert "&uuml;" not in text
    assert "&szlig;" not in text
    assert "<a " not in text
    assert "href=" not in text


def test_block_elements_end_a_line_instead_of_gluing_two_words_together() -> None:
    """Measured without this step: ``Hallo & tschüssZeile2Zeile3``, one word chain."""
    text = to_text("<p>Hallo &amp; tschüss</p><div>Zeile2<br>Zeile3</div>")

    assert text == "Hallo & tschüss\n\nZeile2\nZeile3"
    assert "tschüssZeile2" not in text


def test_every_block_element_of_the_requirement_list_breaks_the_line() -> None:
    """``p``, ``div``, ``br``, ``li``, ``tr``, ``h1`` to ``h6``, ``blockquote``, ``table``."""
    cases = {
        "p": "<p>eins</p><p>zwei</p>",
        "div": "<div>eins</div><div>zwei</div>",
        "br": "eins<br>zwei",
        "li": "<ul><li>eins</li><li>zwei</li></ul>",
        "tr": "<table><tr><td>eins</td></tr><tr><td>zwei</td></tr></table>",
        "h1": "<h1>eins</h1>zwei",
        "h2": "<h2>eins</h2>zwei",
        "h3": "<h3>eins</h3>zwei",
        "h4": "<h4>eins</h4>zwei",
        "h5": "<h5>eins</h5>zwei",
        "h6": "<h6>eins</h6>zwei",
        "blockquote": "<blockquote>eins</blockquote>zwei",
        "table": "<table>eins</table>zwei",
    }

    for tag, source in cases.items():
        text = to_text(source)

        assert "einszwei" not in text, f"<{tag}> must not glue its neighbours together"
        assert text.splitlines()[0].strip() == "eins", tag
        assert text.splitlines()[-1].strip() == "zwei", tag


def test_a_run_of_empty_lines_is_cut_back_to_one() -> None:
    """Mail HTML builds long runs of them out of spacer rows and nested wrappers."""
    text = to_text("<p>eins</p><br><br><br><br><br><p>zwei</p>")

    assert text == "eins\n\nzwei"
    assert "\n\n\n" not in text


def test_broken_markup_is_survived_the_way_the_measurement_showed() -> None:
    """Real mail HTML is broken, and the forgiving parser is the half ``lxml`` buys."""
    assert to_text("<p>unclosed <b>bold") == "unclosed bold"
    assert to_text("<div><p>a<span>b</div></p>c<em>d") == "ab\n\ncd"
    assert to_text("<p>Text ohne Ende") == "Text ohne Ende"


def test_script_and_style_content_never_reaches_the_text_even_when_it_reads_like_prose() -> None:
    """T-10-17. HTMLPurifier in the app cleans too, but the defence belongs here as well."""
    scripted = to_text("<p>hi</p><script>alert('Sehr geehrte Damen und Herren')</script><p>ho</p>")

    assert "Sehr geehrte Damen und Herren" not in scripted
    assert "alert" not in scripted
    assert scripted == "hi\n\nho", "and the words around the dropped block stay"

    styled = to_text("<p>hi</p><style>p{color:red} /* Wichtige Mitteilung */</style>ho")

    assert "Wichtige Mitteilung" not in styled
    assert "color" not in styled
    assert "hi" in styled
    assert "ho" in styled


def test_an_external_entity_is_not_resolved_and_no_file_is_read() -> None:
    """T-10-13. Measured: libxml2's HTML parser resolves none, plus ``no_network=True``.

    The leftover of the internal subset (the two characters ``]>``) is named here as a known
    property instead of treated as a defect: a second cleaning rule over foreign text would
    be a second truth about what the sender wrote.
    """
    attack = (
        f'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "{Path(__file__).as_uri()}">]>'
        "<p>Vorher &xxe; nachher</p>"
    )

    text = to_text(attack)

    assert SENTINEL not in text, "the file behind the entity was read into the answer"
    assert "def test_" not in text
    assert "Vorher" in text
    assert "nachher" in text
    assert text.startswith("]>"), "measured leftover of the internal DTD subset"


def test_an_entity_bomb_does_not_expand() -> None:
    """T-10-14. Measured: no expansion at all, the reference simply stays unresolved."""
    bomb = (
        '<!DOCTYPE x [<!ENTITY a "aaaaaaaaaa">'
        '<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">'
        '<!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">]><p>&c;</p>'
    )

    text = to_text(bomb)

    assert len(text) < 200, len(text)
    assert "aaaaaaaaaa" not in text


def test_a_very_long_mail_comes_back_whole_because_cutting_belongs_to_the_caller() -> None:
    """The byte cap sits at the call site, where the cut can be marked as one (10-05)."""
    source = "<p>Zeile mit etwas Text darin</p>" * 13000
    assert len(source) > 400_000

    text = to_text(source)

    assert text.count("Zeile mit etwas Text darin") == 13000
    assert "truncated" not in text


def test_prose_with_angle_brackets_keeps_the_words_around_them() -> None:
    """Not every body is markup, and the measured behaviour is written down, not wished for."""
    assert to_text("a < b und c > d") == "a < b und c > d"
    assert to_text("Preis < 100 Euro, Menge > 3") == "Preis < 100 Euro, Menge > 3"


def test_a_comment_is_not_part_of_what_the_sender_wrote_but_its_neighbours_are() -> None:
    """Comments carry a callable tag, which is the branch the loop skips on purpose."""
    text = to_text("<p>a</p><!-- interne Notiz --><p>b</p>")

    assert "interne Notiz" not in text
    assert text == "a\n\nb"
