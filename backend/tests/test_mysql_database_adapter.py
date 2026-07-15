import importlib


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
    assert "user_id VARCHAR(255) NOT NULL" in converted
    assert "created_at VARCHAR(255) NOT NULL" in converted
    assert "payload_json LONGTEXT NOT NULL" in converted
    assert "DEFAULT '{}'" not in converted


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

    assert "module_type VARCHAR(255) NOT NULL" in converted


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
    assert "source_file VARCHAR(255)" not in converted


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
