"""T-017: exact literal parsing and atomic, source-preserving import."""

import hashlib
import sqlite3
from datetime import date, timedelta

import import_manse as importer
import pytest
from app.manse_store import COLUMNS, ManseStore, record_digest


def fixture_row(index, solar, lunar_day=20, division=0, hour=0, minute=0):
    return (
        index, solar.year, solar.month, solar.day, 2023, 11, lunar_day, 0,
        hour, minute, division, 9, 3, 0, 0, 0, 0, solar.isoformat(),
    )


def sql_line(row):
    integers = ", ".join(str(value) for value in row[:-1])
    return importer.INSERT_PREFIX + integers + f", CAST(N'{row[-1]} 00:00:00.0000000' AS DateTime2))"


def source_file(tmp_path, rows, suffix=""):
    path = tmp_path / "source.sql"
    content = "\n".join(sql_line(row) for row in rows)
    path.write_text(content + suffix, encoding="utf-16")
    return path


def test_import_preserves_raw_values_duplicate_lunar_keys_and_source(tmp_path):
    first = date(2024, 1, 1)
    rows = [
        fixture_row(3, first, division=23, hour=24),
        fixture_row(1, first + timedelta(days=1)),
        fixture_row(2, first + timedelta(days=2), lunar_day=21, division=1),
    ]
    source = source_file(tmp_path, rows)
    original = source.read_bytes()
    output = tmp_path / "calendar.sqlite3"

    metadata = importer.build_database(source, output)

    store = ManseStore(output)
    assert list(store.iter_records()) == sorted(rows)
    assert store.metadata() == metadata
    assert metadata["row_count"] == 3
    assert metadata["lunar_duplicate_count"] == 1
    assert metadata["div_hour_24"][0]["idx"] == 3
    assert metadata["source_sha256"] == hashlib.sha256(original).hexdigest()
    assert metadata["data_sha256"] == record_digest(sorted(rows))
    assert source.read_bytes() == original
    assert store.solar_record(first)["div_hour"] == 24
    assert tuple(store.solar_record(first)) == COLUMNS


def test_repeated_import_replaces_owned_dataset_without_appending(tmp_path):
    rows = [fixture_row(1, date(2024, 1, 1), division=23)]
    source = source_file(tmp_path, rows)
    output = tmp_path / "calendar.sqlite3"

    first = importer.build_database(source, output)
    second = importer.build_database(source, output)

    assert first == second
    assert list(ManseStore(output).iter_records()) == rows


@pytest.mark.parametrize("malicious", [
    "\nDROP TABLE tb_manse;",
    "\nINSERT INTO unrelated VALUES (1);",
    "\nSELECT load_extension('fixture');",
])
def test_unapproved_sql_is_rejected_and_existing_database_survives(tmp_path, malicious):
    rows = [fixture_row(1, date(2024, 1, 1))]
    source = source_file(tmp_path, rows)
    output = tmp_path / "calendar.sqlite3"
    importer.build_database(source, output)
    original = output.read_bytes()
    source_file(tmp_path, rows, malicious)

    with pytest.raises(importer.ManseImportError, match="허용한"):
        importer.build_database(source, output)

    assert output.read_bytes() == original


def test_integer_expressions_and_unexpected_column_names_are_rejected(tmp_path):
    row = fixture_row(1, date(2024, 1, 1))
    for content in (sql_line(row).replace("VALUES (1,", "VALUES (1 + 1, "),
                    sql_line(row).replace("[idx]", "[unexpected]")):
        source = tmp_path / "source.sql"
        source.write_text(content, encoding="utf-16")
        with pytest.raises(importer.ManseImportError, match="허용한"):
            importer.load_script(source)


def test_existing_unrelated_sqlite_database_is_never_replaced(tmp_path):
    source = source_file(tmp_path, [fixture_row(1, date(2024, 1, 1))])
    output = tmp_path / "other.sqlite3"
    with sqlite3.connect(output) as connection:
        connection.execute("CREATE TABLE unrelated(id INTEGER)")
    original = output.read_bytes()

    with pytest.raises(importer.ManseImportError, match="덮어쓰지"):
        importer.build_database(source, output)

    assert output.read_bytes() == original


def test_failed_atomic_replace_preserves_previous_database(tmp_path, monkeypatch):
    source = source_file(tmp_path, [fixture_row(1, date(2024, 1, 1))])
    output = tmp_path / "calendar.sqlite3"
    importer.build_database(source, output)
    original = output.read_bytes()

    def failure(*_args):
        raise OSError("synthetic filesystem failure")

    monkeypatch.setattr(importer.os, "replace", failure)
    with pytest.raises(importer.ManseImportError, match="기존 데이터는 보존"):
        importer.build_database(source, output)

    assert output.read_bytes() == original
    assert not list(tmp_path.glob(".manse-*"))


@pytest.mark.parametrize("rows, error", [
    ([fixture_row(1, date(2024, 1, 1)), fixture_row(1, date(2024, 1, 2))], "중복"),
    ([fixture_row(1, date(2024, 1, 1)), fixture_row(2, date(2024, 1, 3))], "누락"),
])
def test_duplicate_ids_and_date_gaps_fail_before_database_creation(tmp_path, rows, error):
    source = source_file(tmp_path, rows)
    output = tmp_path / "calendar.sqlite3"
    with pytest.raises(importer.ManseImportError, match=error):
        importer.build_database(source, output)
    assert not output.exists()


def test_lunar_and_ganji_ranges_reject_invalid_literals(tmp_path):
    row = list(fixture_row(1, date(2024, 1, 1)))
    row[11] = 10
    source = source_file(tmp_path, [row])
    with pytest.raises(importer.ManseImportError, match="지원 범위"):
        importer.load_script(source)


def test_utf8_or_non_midnight_timestamp_is_not_silently_converted(tmp_path):
    path = tmp_path / "source.sql"
    row = fixture_row(1, date(2024, 1, 1))
    path.write_text(sql_line(row), encoding="utf-8")
    with pytest.raises(importer.ManseImportError, match="UTF-16LE"):
        importer.load_script(path)
    path.write_text(sql_line(row).replace("00:00:00", "12:30:00"), encoding="utf-16")
    with pytest.raises(importer.ManseImportError, match="허용한"):
        importer.load_script(path)
