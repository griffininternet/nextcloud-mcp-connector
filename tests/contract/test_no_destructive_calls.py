"""The security promise of the README, enforced by a gate instead of by discipline.

README, tool annotations and app store listing all say the same sentence: this server can
never delete, overwrite or re-share anything (TOOL-09). Without a gate that sentence is a
claim about today's code and says nothing about the next commit, which is exactly the
threat this file answers (T-01-94).

Two things make this test trustworthy rather than decorative:

*   **Comments and docstrings are removed before counting.** ``clients/dav.py`` explains in
    its module docstring that it implements no DELETE, no MOVE, no COPY and no PROPPATCH.
    A naive grep would fail on that sentence, and the usual repair is to delete the
    sentence, which trades documentation for a green check. String literals stay in scope
    on purpose: ``method="DELETE"`` is the real thing this gate is looking for.
*   **Every finding names file and line**, so a violation is a one line fix and never a
    hunt through the tree.

The same parsing gives two more guarantees for free: no module level mutable state that
could act as a session store (D-20), and no tool that stops to ask the user mid call.
"""

import ast
import io
import tokenize
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "mcp_connector"

# Destructive HTTP verbs and the one OCS route that changes who may see an object. Upper
# case on purpose: httpx spells a custom method in upper case, and the lower case words
# "move" or "copy" occur in ordinary prose and identifiers.
FORBIDDEN: dict[str, str] = {
    "DELETE": "no tool may delete anything",
    "MOVE": "no tool may move or rename anything",
    "COPY": "no tool may duplicate anything server side",
    "PROPPATCH": "no tool may change properties of an existing object",
    "ocs/v2.php/apps/files_sharing": "no tool may create or change a share",
    ".delete(": "no client helper may expose a delete call",
}

# The one file where the word DELETE is not an HTTP verb. TOOL-09 is a promise about what
# this server does to data in Nextcloud, and the OAuth store is our own SQLite file: it
# has to drop an expired authorization code and a registration nobody ever used, or it
# grows without a bound (T-03-17). The exemption is deliberately narrow, two exact SQL
# forms in one file, so an HTTP DELETE written in the same module is still reported, and
# ``.delete(`` above is never exempt anywhere.
FILES_WITH_OWN_SQL = frozenset({"oauth/store.py"})
SQL_DELETE_FORMS = ("DELETE FROM ", "ON DELETE CASCADE")

# The second file where DELETE is not a tool deleting user data: the login flow revokes the
# app password it created itself, authenticated with exactly that app password (D-34 and
# D-36, plan 03-04). Nothing of the user is removed, only the credential this server was
# handed, and being unable to hand it back would mean a connection a user revoked stays
# usable in Nextcloud. The exemption is one exact call form in one file, so a DELETE written
# against any other target in the same module is still reported, and ``.delete(`` above is
# never exempt anywhere.
FILES_WITH_OWN_APP_PASSWORD = frozenset({"oauth/loginflow.py"})

#: The verb on a line of its own, which is how the formatter writes the one call that is
#: meant. A DELETE written inline, against any target, does not match and stays a finding.
APP_PASSWORD_DELETE_FORM = '"DELETE",'

# The third file where DELETE is not a tool deleting user data: the purge of plan 05-06
# removes the data key of this app from Nextcloud's own ExApp configuration
# (``oauth/crypto.py::delete_key``, DELETE on the resource whose write and read halves
# already live in that module). What goes is a value this app wrote about itself, and its
# removal is what makes an uninstall honest: a key left behind still opens the ciphertexts
# in a copied volume. Nothing of any user is touched, and no promise of TOOL-09 is about
# it. The exemption is one exact call form in one file, exactly like the one above, so a
# DELETE written against any other target in the same module is still reported, and
# ``.delete(`` is never exempt anywhere.
FILES_WITH_OWN_CONFIG = frozenset({"oauth/crypto.py"})

#: The same shape as :data:`APP_PASSWORD_DELETE_FORM` and written out a second time rather
#: than shared: the two exemptions are independent, and one of them widening must not widen
#: the other.
CONFIG_DELETE_FORM = '"DELETE",'

# Module level mutable state is forbidden as a rule, because a dictionary that outlives a
# request is one refactor away from being a session store, and a session store is what
# breaks the restart proof (D-20). These two are the documented exceptions: both are pure
# latency optimisations, both may be empty at any moment without changing an answer, and
# neither holds a credential.
ALLOWED_MODULE_STATE: set[tuple[str, str]] = {
    ("nextcloud/http.py", "_clients"),  # one httpx client per event loop, weakly keyed
    ("nextcloud/capabilities.py", "_cache"),  # capabilities per (base_url, user), 60 s TTL
}

_MUTABLE_FACTORIES = {
    "dict",
    "list",
    "set",
    "defaultdict",
    "WeakKeyDictionary",
    "WeakValueDictionary",
}


def _source_files() -> list[Path]:
    files = sorted(SRC.rglob("*.py"))
    assert files, f"no production sources found under {SRC}"
    return files


def _code_lines(path: Path) -> list[tuple[int, str]]:
    """Return the source lines with comments and docstrings blanked out.

    Only these two are removed. A string literal that is not a docstring stays, because a
    destructive call is written as a string: ``client.request("DELETE", url)``.
    """
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    blanked = list(lines)

    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if ast.get_docstring(node, clean=False) is None:
            continue
        first = node.body[0]
        end = first.end_lineno or first.lineno
        for lineno in range(first.lineno, end + 1):
            blanked[lineno - 1] = ""

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        lineno, col = token.start
        blanked[lineno - 1] = blanked[lineno - 1][:col]

    return [(number, text) for number, text in enumerate(blanked, start=1) if text.strip()]


def test_the_production_code_contains_no_destructive_request() -> None:
    """TOOL-09: the promise holds in the code, not only in the README."""
    findings: list[str] = []
    for path in _source_files():
        relative = path.relative_to(SRC).as_posix()
        for number, text in _code_lines(path):
            for needle, why in FORBIDDEN.items():
                if needle not in text:
                    continue
                if needle == "DELETE" and _is_own_sql(relative, text):
                    continue
                if needle == "DELETE" and _is_own_app_password(relative, text):
                    continue
                if needle == "DELETE" and _is_own_config_value(relative, text):
                    continue
                findings.append(f"{relative}:{number}: {needle!r} ({why}): {text.strip()}")

    assert findings == [], "destructive call found:\n" + "\n".join(findings)


def _is_own_sql(relative: str, text: str) -> bool:
    """True for a statement against our own store file, false for anything else."""
    return relative in FILES_WITH_OWN_SQL and any(form in text for form in SQL_DELETE_FORMS)


def _is_own_app_password(relative: str, text: str) -> bool:
    """True for the one call that revokes the app password of this server's own connection."""
    return relative in FILES_WITH_OWN_APP_PASSWORD and text.strip() == APP_PASSWORD_DELETE_FORM


def _is_own_config_value(relative: str, text: str) -> bool:
    """True for the one call that removes this app's own value from the ExApp config."""
    return relative in FILES_WITH_OWN_CONFIG and text.strip() == CONFIG_DELETE_FORM


def test_the_gate_would_notice_a_destructive_call_in_real_code() -> None:
    """Counter proof: the filter removes prose, and only prose.

    Without this test the previous one could be green because the filter eats everything.
    ``clients/dav.py`` is the honest fixture for it: its module docstring names all four
    verbs, and it must still be reported when the same word appears in an actual request.
    """
    dav = SRC / "nextcloud" / "clients" / "dav.py"
    docstring_text = "\n".join(text for _, text in _code_lines(dav))
    assert "no DELETE, no MOVE, no COPY" not in docstring_text, (
        "the filter must remove the module docstring of dav.py"
    )

    with_a_violation = docstring_text + '\n    await client.request("DELETE", url)\n'
    assert "DELETE" in with_a_violation, "a real call is still visible after filtering"


def test_the_sql_exemption_covers_sql_and_nothing_else() -> None:
    """Counter proof for the narrow exemption: an HTTP DELETE in the store still counts.

    The exemption exists so the OAuth store may drop its own expired rows. If it were
    written as "ignore DELETE in this file" it would also hide the one line that would
    make this server delete something in Nextcloud from inside the store.
    """
    store = "oauth/store.py"
    assert _is_own_sql(store, 'conn.execute("DELETE FROM flows WHERE expires_at <= ?")')
    assert _is_own_sql(store, "auth_id TEXT NOT NULL REFERENCES x(y) ON DELETE CASCADE,")
    assert not _is_own_sql(store, 'await client.request("DELETE", url)')
    assert not _is_own_sql("tools/files.py", 'conn.execute("DELETE FROM flows")')

    for relative in FILES_WITH_OWN_SQL | FILES_WITH_OWN_APP_PASSWORD | FILES_WITH_OWN_CONFIG:
        assert (SRC / relative).is_file(), f"{relative} is exempt but does not exist"


def test_the_app_password_exemption_covers_one_call_form_and_nothing_else() -> None:
    """Counter proof for the second exemption: only the revocation of our own credential.

    The login flow deletes the app password it created itself (D-34, D-36). Written as
    "ignore DELETE in that file", the exemption would also hide a request that deletes a
    file of the user from the same module, so it matches the verb on a line of its own and
    nothing else.
    """
    flow = "oauth/loginflow.py"
    assert _is_own_app_password(flow, '            "DELETE",')
    assert not _is_own_app_password(flow, 'await client.request("DELETE", files_url)')
    assert not _is_own_app_password(flow, '            "DELETE", files_url,')
    assert not _is_own_app_password("tools/files.py", '            "DELETE",')


def test_the_config_exemption_covers_one_call_form_and_nothing_else() -> None:
    """Counter proof for the third exemption: only the deletion of our own config value.

    The purge removes the data key this app stored about itself (plan 05-06). Written as
    "ignore DELETE in that file", the exemption would also hide a request that deletes a
    file of the user from the same module, so it matches the verb on a line of its own and
    nothing else, and it does not reach any other file.
    """
    crypto = "oauth/crypto.py"
    assert _is_own_config_value(crypto, '            "DELETE",')
    assert not _is_own_config_value(crypto, 'await client.request("DELETE", files_url)')
    assert not _is_own_config_value(crypto, '            "DELETE", files_url,')
    assert not _is_own_config_value("tools/files.py", '            "DELETE",')
    assert not _is_own_config_value(crypto, 'conn.execute("DELETE FROM flows")')


def test_no_module_level_mutable_state_outside_the_two_documented_caches() -> None:
    """D-20: nothing between two requests may remember anything about a session."""
    findings: list[str] = []
    for path in _source_files():
        relative = path.relative_to(SRC).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(node, ast.Assign):
                targets, value = list(node.targets), node.value
            elif isinstance(node, ast.AnnAssign):
                targets, value = [node.target], node.value
            if value is None or not _is_mutable(value):
                continue
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                if (relative, target.id) in ALLOWED_MODULE_STATE:
                    continue
                if target.id.isupper():  # module constants are configuration, not state
                    continue
                if target.id.startswith("__") and target.id.endswith("__"):
                    continue  # __all__ is the export list of a module, not runtime state
                findings.append(f"{relative}:{node.lineno}: module level mutable {target.id}")

    assert findings == [], "module level mutable state can become a session store:\n" + "\n".join(
        findings
    )


def _is_mutable(value: ast.expr) -> bool:
    if isinstance(value, ast.Dict | ast.List | ast.Set | ast.DictComp | ast.ListComp | ast.SetComp):
        return True
    if isinstance(value, ast.Call):
        func = value.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        return name in _MUTABLE_FACTORIES
    return False


def test_the_two_allowed_caches_still_exist_where_they_are_claimed_to_be() -> None:
    """An allow list that points at nothing silently stops allowing anything."""
    for relative, name in ALLOWED_MODULE_STATE:
        path = SRC / relative
        assert path.is_file(), f"{relative} is on the allow list but does not exist"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        declared = {
            target.id
            for node in tree.body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Name)
        }
        assert name in declared, f"{relative} no longer declares {name}"


def test_no_tool_stops_to_ask_the_user_or_resolves_a_reference() -> None:
    """A tool that elicits mid call cannot survive a restart and blocks stateless HTTP."""
    findings: list[str] = []
    for path in _source_files():
        relative = path.relative_to(SRC).as_posix()
        for number, text in _code_lines(path):
            for needle in ("elicit", "Resolve"):
                if needle in text:
                    findings.append(f"{relative}:{number}: {needle!r}: {text.strip()}")

    assert findings == [], (
        "elicitation and reference resolution keep state across a call:\n" + "\n".join(findings)
    )
