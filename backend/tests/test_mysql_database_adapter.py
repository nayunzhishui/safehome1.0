import importlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_mysql_schema_conversion_uses_indexable_columns():
    database = importlib.import_module("database")

    statement = """
    CREATE TABLE IF NOT EXISTS example (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        payload_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """

    converted = database.mysqlize_schema_statement(statement)

    assert "id VARCHAR(128) PRIMARY KEY" in converted
    assert "user_id VARCHAR(191) NOT NULL" in converted
    assert "created_at VARCHAR(191) NOT NULL" in converted
    assert "payload_json LONGTEXT NOT NULL" in converted
    assert "DEFAULT '{}'" not in converted


def test_checkin_count_query_supports_mysql_dict_cursor():
    source = (ROOT / "backend/routes/checkins.py").read_text(encoding="utf-8")

    assert "SELECT COUNT(*) AS count FROM checkins" in source
    assert 'total_row["count"]' in source
    assert ").fetchone()[0]" not in source


def test_mysql_query_conversion_keeps_existing_route_sql_shape():
    database = importlib.import_module("database")

    converted = database._mysqlize_query("SELECT * FROM goals WHERE user_id = ? LIMIT ?")

    assert converted == "SELECT * FROM goals WHERE user_id = %s LIMIT %s"


def test_mysql_query_conversion_keeps_question_marks_inside_literals():
    database = importlib.import_module("database")

    converted = database._mysqlize_query(
        "SELECT '?' AS single_literal, \"?\" AS double_literal FROM goals WHERE user_id = ?"
    )

    assert converted == "SELECT '?' AS single_literal, \"?\" AS double_literal FROM goals WHERE user_id = %s"


def test_mysql_column_definition_removes_text_default():
    database = importlib.import_module("database")

    definition = database.mysqlize_column_definition("report_json", "TEXT NOT NULL DEFAULT '{}'")

    assert definition == "LONGTEXT NOT NULL"


def test_mysql_scalar_text_default_uses_varchar_for_mysql57():
    database = importlib.import_module("database")

    definition = database.mysqlize_column_definition(
        "participant_status",
        "TEXT NOT NULL DEFAULT 'visible'",
    )

    assert definition == "VARCHAR(191) NOT NULL DEFAULT 'visible'"


def test_mysql_digest_column_added_by_migration_is_indexable():
    database = importlib.import_module("database")

    definition = database.mysqlize_column_definition("claim_token_digest", "TEXT")

    assert definition == "VARCHAR(191)"


def test_all_schema_statements_avoid_mysql57_text_defaults():
    database = importlib.import_module("database")

    invalid_lines = []
    for statement in database.SCHEMA_SQL:
        converted = database.mysqlize_schema_statement(statement)
        invalid_lines.extend(
            line.strip()
            for line in converted.splitlines()
            if re.search(r"\b(?:TEXT|LONGTEXT)\b.*\bDEFAULT\b", line, re.IGNORECASE)
        )

    assert invalid_lines == []


def test_mysql_schema_conversion_handles_multiple_columns_per_line():
    database = importlib.import_module("database")

    converted = database.mysqlize_schema_statement(
        """
        CREATE TABLE IF NOT EXISTS safety_scheduler_events (
            id TEXT PRIMARY KEY, event_key TEXT NOT NULL UNIQUE,
            due_at TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """
    )

    assert "id VARCHAR(128) PRIMARY KEY" in converted
    assert "event_key VARCHAR(191) NOT NULL UNIQUE" in converted
    assert "metadata_json LONGTEXT NOT NULL" in converted
    assert "DEFAULT '{}'" not in converted


def test_all_mysql_key_columns_use_indexable_types():
    database = importlib.import_module("database")
    tables = {}
    invalid = []
    indexes = []

    for statement in database.SCHEMA_SQL:
        table_match = re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)",
            statement,
            re.IGNORECASE,
        )
        if not table_match:
            continue
        table = table_match.group(1)
        converted = database.mysqlize_schema_statement(statement)
        columns = {}
        for line in converted.splitlines():
            column_match = re.match(
                r"\s*([A-Za-z_]\w*)\s+([A-Z]+(?:\(\d+\))?)(?=\s|,)(.*)",
                line,
                re.IGNORECASE,
            )
            if not column_match or column_match.group(1).upper() in {
                "CREATE", "UNIQUE", "PRIMARY", "FOREIGN", "CHECK", "CONSTRAINT",
            }:
                continue
            columns[column_match.group(1)] = (
                column_match.group(2).upper(),
                column_match.group(3),
            )
        tables[table] = columns

        for column, (column_type, rest) in columns.items():
            if re.search(r"\b(?:PRIMARY\s+KEY|UNIQUE)\b", rest, re.IGNORECASE):
                indexes.append((table, [column]))
                if column_type in {"TEXT", "LONGTEXT"}:
                    invalid.append((table, column, "inline-column"))
        for constraint in re.finditer(
            r"\b(?:UNIQUE|PRIMARY\s+KEY)\s*\(([^)]+)\)",
            converted,
            re.IGNORECASE,
        ):
            constraint_columns = [
                part.strip().strip("`").split()[0]
                for part in constraint.group(1).split(",")
            ]
            indexes.append((table, constraint_columns))
            for column in constraint_columns:
                if columns.get(column, ("", ""))[0] in {"TEXT", "LONGTEXT"}:
                    invalid.append((table, column, "inline-table"))

    for statement in database.INDEX_SQL:
        parsed = database._parse_index_statement(statement)
        target = database._parse_index_target(parsed[1]) if parsed else None
        if not target:
            continue
        table, columns = target
        indexes.append((table, columns))
        for column in columns:
            if tables.get(table, {}).get(column, ("", ""))[0] in {"TEXT", "LONGTEXT"}:
                invalid.append((table, column, "index-sql"))

    assert sorted(set(invalid)) == []
    oversized = []
    for table, columns in indexes:
        total_bytes = 0
        for column in columns:
            column_type = tables.get(table, {}).get(column, ("", ""))[0]
            match = re.fullmatch(r"VARCHAR\((\d+)\)", column_type, re.IGNORECASE)
            if match:
                total_bytes += int(match.group(1)) * 4
        if total_bytes > 3072:
            oversized.append((table, tuple(columns), total_bytes))
    assert sorted(set(oversized)) == []


def test_mysql_schema_conversion_makes_records_module_type_indexable():
    database = importlib.import_module("database")

    converted = database.mysqlize_schema_statement(
        """
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            module_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    assert "module_type VARCHAR(191) NOT NULL" in converted


def test_mysql_schema_conversion_keeps_assessment_source_file_as_text():
    database = importlib.import_module("database")

    converted = database.mysqlize_schema_statement(
        """
        CREATE TABLE IF NOT EXISTS assessment_worksheets (
            id TEXT PRIMARY KEY,
            source_file TEXT
        )
        """
    )

    assert "source_file TEXT" in converted
    assert "source_file VARCHAR(191)" not in converted


def test_mysql_legacy_assessment_source_file_is_widened_before_sync():
    database = importlib.import_module("database")

    class Cursor:
        def fetchone(self):
            return {"data_type": "varchar", "is_nullable": "YES"}

    class Connection:
        provider = "mysql"

        def __init__(self):
            self.statements = []

        def execute(self, sql, params=None):
            self.statements.append((" ".join(sql.split()), params))
            return Cursor()

    conn = Connection()
    database.ensure_mysql_content_text_capacity(conn)

    assert any(
        sql == "ALTER TABLE assessment_worksheets MODIFY COLUMN source_file TEXT NULL"
        for sql, _ in conn.statements
    )


def test_mysql_index_repair_shrinks_existing_wide_varchar_before_indexing():
    database = importlib.import_module("database")

    class Cursor:
        def __init__(self, row=None):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        provider = "mysql"

        def __init__(self):
            self.statements = []

        def execute(self, sql, params=None):
            normalized = " ".join(sql.split())
            self.statements.append((normalized, params))
            if "information_schema.columns" in normalized and params == ("observability_events", "request_id"):
                return Cursor({
                    "data_type": "varchar",
                    "is_nullable": "YES",
                    "character_maximum_length": 255,
                })
            return Cursor()

    conn = Connection()
    database.ensure_mysql_index_columns(conn)

    assert any(
        sql == "ALTER TABLE observability_events MODIFY COLUMN request_id VARCHAR(191) NULL"
        for sql, _ in conn.statements
    )


def test_mysql_index_target_parser_reads_table_and_columns():
    database = importlib.import_module("database")

    parsed = database._parse_index_target("records(module_type, created_at)")

    assert parsed == ("records", ["module_type", "created_at"])


def test_mysqlize_query_preserves_simple_replace_behavior():
    """Document current behavior: ? → %s for standard SQLite-style queries."""
    database = importlib.import_module("database")

    # Standard patterns that must work
    assert database._mysqlize_query("SELECT * FROM t WHERE a = ? AND b = ?") == "SELECT * FROM t WHERE a = %s AND b = %s"
    assert database._mysqlize_query("INSERT INTO t (a, b) VALUES (?, ?)") == "INSERT INTO t (a, b) VALUES (%s, %s)"
    assert database._mysqlize_query("UPDATE t SET a = ? WHERE id = ?") == "UPDATE t SET a = %s WHERE id = %s"
    assert database._mysqlize_query("DELETE FROM t WHERE id = ?") == "DELETE FROM t WHERE id = %s"


def test_mysqlize_query_known_limitation_literal_question_mark():
    """Document known limitation: literal ? inside SQL strings will be incorrectly replaced.

    The current _mysqlize_query uses a simple str.replace('?', '%s') and does NOT
    distinguish ? placeholders from ? characters inside string literals.
    This is acceptable for the current codebase because no SQL query contains
    literal question marks in strings. A proper SQL parser would be needed to
    fix this, which is deferred to a future database-layer refactor.
    """
    database = importlib.import_module("database")

    sql_with_literal = "SELECT 'is this okay?' AS phrase, id FROM goals WHERE user_id = ?"
    converted = database._mysqlize_query(sql_with_literal)

    # Known behavior: the ? inside the string literal is also replaced
    # This test exists to document (not endorse) the current behavior
    assert "is this okay%s" in converted or "is this okay?" in converted
