"""T-017: parse a whitelisted SQL Server export and atomically build SQLite."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_api"))

from app.manse_store import (
    APPLICATION_ID,
    COLUMNS,
    DEFAULT_DATABASE,
    FORMAT_NAME,
    INSERT_SQL,
    SCHEMA_VERSION,
    SQLITE_INDEX_DDL,
    SQLITE_METADATA_DDL,
    SQLITE_TABLE_DDL,
    SQLITE_TERMS_DDL,
    ManseDataError,
    ManseStore,
    data_digest,
    term_datetime,
)

INSERT_PREFIX = "INSERT [dbo].[tb_manse] (" + ", ".join(f"[{name}]" for name in COLUMNS) + ") VALUES ("
INSERT_ROW = re.compile(
    re.escape(INSERT_PREFIX)
    + r"(?P<numbers>-?[0-9]{1,10}(?:, -?[0-9]{1,10}){16}), "
    + r"CAST\(N'(?P<day>[0-9]{4}-[0-9]{2}-[0-9]{2}) 00:00:00\.0000000' AS DateTime2\)\)"
)
HEADER_LINES = {
    "USE [dotongDB]", "GO", "SET ANSI_NULLS ON", "SET QUOTED_IDENTIFIER ON",
    "CREATE TABLE [dbo].[tb_manse](", "[idx] [int] IDENTITY(1,1) NOT NULL,",
    "CONSTRAINT [PK_tb_manse_back] PRIMARY KEY CLUSTERED", "(", "[idx] ASC",
    (")WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, "
     "ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]"), ") ON [PRIMARY]",
    "SET IDENTITY_INSERT [dbo].[tb_manse] ON", "SET IDENTITY_INSERT [dbo].[tb_manse] OFF",
    "[d_gan] [tinyint] NOT NULL,", "[d_ji] [tinyint] NOT NULL,",
    "[sDate] [datetime2](0) NOT NULL CONSTRAINT [DF_back_sDate]  DEFAULT (getdate()),",
}
for _field, _type, _default in (
    ("s_year", "smallint", 1900), ("s_mon", "smallint", 1), ("s_day", "smallint", 1),
    ("l_year", "smallint", 1900), ("l_mon", "smallint", 1), ("l_day", "smallint", 1),
    ("leafMon_YN", "bit", 0), ("div_hour", "smallint", 0), ("div_min", "smallint", 30),
    ("div_name", "tinyint", 0), ("y_gan", "tinyint", 0), ("y_ji", "tinyint", 0),
    ("m_gan", "tinyint", 0), ("m_ji", "tinyint", 0),
):
    HEADER_LINES.add(
        f"[{_field}] [{_type}] NOT NULL CONSTRAINT [DF_back_{_field}]  DEFAULT (({_default})),"
    )
HEADER_COMMENT = re.compile(r"/\*\*\*\*\*\* Object:  Table \[dbo\]\.\[tb_manse\]    Script Date: [^\r\n]{1,100} \*\*\*\*\*\*/")


class ManseImportError(ValueError):
    pass


def _validated_row(match: re.Match, line_number: int) -> tuple:
    numbers = tuple(int(value) for value in match["numbers"].split(", "))
    try:
        solar = date(*numbers[1:4])
        stored_date = date.fromisoformat(match["day"])
    except ValueError:
        raise ManseImportError(f"SQL {line_number}행의 양력 날짜가 올바르지 않습니다.") from None
    if solar != stored_date or not 1 <= numbers[0] <= 2_147_483_647:
        raise ManseImportError(f"SQL {line_number}행의 식별자 또는 양력 날짜가 일치하지 않습니다.")
    limits = {
        4: (1800, 2200), 5: (1, 12), 6: (1, 30), 7: (0, 1),
        8: (0, 24), 9: (0, 59), 10: (0, 24),
        11: (0, 9), 12: (0, 11), 13: (0, 9), 14: (0, 11), 15: (0, 9), 16: (0, 11),
    }
    if any(not minimum <= numbers[index] <= maximum for index, (minimum, maximum) in limits.items()):
        raise ManseImportError(f"SQL {line_number}행에 지원 범위를 벗어난 만세력 값이 있습니다.")
    if numbers[8] == 24 and numbers[9] != 0:
        raise ManseImportError(f"SQL {line_number}행의 24시 절기 표기가 올바르지 않습니다.")
    return (*numbers, solar.isoformat())


def _metadata(rows: list[tuple], source_bytes: bytes, line_count: int) -> dict:
    dates = [row[-1] for row in rows]
    ids = [row[0] for row in rows]
    if len(set(ids)) != len(rows) or len(set(dates)) != len(rows):
        raise ManseImportError("만세력 원본에 중복 idx 또는 양력 날짜가 있습니다.")
    first, last = min(dates), max(dates)
    covered = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
    if covered != len(rows):
        raise ManseImportError("만세력 원본의 양력 날짜 범위에 누락이 있습니다.")
    lunars = defaultdict(list)
    divisions = defaultdict(Counter)
    hour_24 = []
    for row in rows:
        lunars[row[4:8]].append(row[-1])
        if row[10]:
            divisions[row[1]][row[10]] += 1
        if row[8] == 24:
            hour_24.append({"idx": row[0], "sDate": row[-1], "div_name": row[10]})
    duplicate_keys = []
    for key, solar_dates in sorted(lunars.items()):
        if len(solar_dates) > 1:
            duplicate_keys.append({
                "l_year": key[0], "l_mon": key[1], "l_day": key[2], "leafMon_YN": key[3],
                "count": len(solar_dates), "solar_dates": sorted(solar_dates),
            })
    division_anomalies = []
    for year, counts in sorted(divisions.items()):
        missing = sorted(set(range(1, 25)) - set(counts))
        repeated = {str(code): count for code, count in sorted(counts.items()) if count > 1}
        if missing or repeated:
            division_anomalies.append({"year": year, "missing": missing, "repeated": repeated})
    ordered = sorted(rows, key=lambda row: row[0])
    return {
        "format": FORMAT_NAME, "schema_version": SCHEMA_VERSION,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "data_sha256": data_digest(ordered), "source_line_count": line_count,
        "row_count": len(rows), "min_date": first, "max_date": last,
        "min_idx": min(ids), "max_idx": max(ids),
        "lunar_duplicates": duplicate_keys,
        "lunar_duplicate_count": sum(value["count"] - 1 for value in duplicate_keys),
        "div_hour_24": hour_24, "division_code_anomalies": division_anomalies,
    }


def load_script(path: Path) -> tuple[list[tuple], dict]:
    try:
        source_bytes = Path(path).read_bytes()
        if not source_bytes.startswith(b"\xff\xfe"):
            raise ManseImportError("SQL 원본은 BOM이 있는 UTF-16LE 파일이어야 합니다.")
        contents = source_bytes[2:].decode("utf-16-le")
    except (OSError, UnicodeError):
        raise ManseImportError("SQL 원본 파일을 읽을 수 없습니다.") from None
    rows = []
    lines = contents.splitlines()
    for line_number, source_line in enumerate(lines, 1):
        line = source_line.strip()
        if not line or line in HEADER_LINES or HEADER_COMMENT.fullmatch(line):
            continue
        match = INSERT_ROW.fullmatch(line)
        if match is None:
            raise ManseImportError(f"SQL {line_number}행이 허용한 tb_manse 내보내기 형식과 다릅니다.")
        rows.append(_validated_row(match, line_number))
    if not rows:
        raise ManseImportError("SQL 원본에 tb_manse 데이터가 없습니다.")
    return rows, _metadata(rows, source_bytes, len(lines))


def _check_destination(path: Path) -> None:
    if path.is_symlink():
        raise ManseImportError("심볼릭 링크를 만세력 출력 파일로 사용할 수 없습니다.")
    if path.exists():
        try:
            ManseStore(path).metadata()
        except ManseDataError:
            raise ManseImportError("기존 파일은 Woonari 만세력 DB가 아니므로 덮어쓰지 않습니다.") from None


def build_database(source: Path, output: Path = DEFAULT_DATABASE) -> dict:
    output = Path(output)
    _check_destination(output)
    rows, metadata = load_script(Path(source))
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, filename = tempfile.mkstemp(prefix=".manse-", suffix=".sqlite3", dir=output.parent)
    os.close(descriptor)
    temporary = Path(filename)
    try:
        with closing(sqlite3.connect(temporary)) as connection, connection:
            connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            connection.execute(SQLITE_TABLE_DDL)
            connection.execute(SQLITE_TERMS_DDL)
            connection.execute(SQLITE_METADATA_DDL)
            connection.executemany(INSERT_SQL, rows)
            for statement in SQLITE_INDEX_DDL:
                connection.execute(statement)
            terms = []
            for row in rows:
                if row[10] % 2 == 1:
                    record = dict(zip(COLUMNS, row))
                    terms.append((row[0], term_datetime(record).isoformat()))
            connection.executemany("INSERT INTO manse_terms(idx, term_at) VALUES (?, ?)", terms)
            connection.execute(
                "INSERT INTO manse_metadata(id, payload) VALUES (1, ?)",
                (json.dumps(metadata, ensure_ascii=False, sort_keys=True),),
            )
        checked = ManseStore(temporary)
        if checked.metadata() != metadata or data_digest(checked.iter_records()) != metadata["data_sha256"]:
            raise ManseImportError("생성한 만세력 DB의 데이터 검증에 실패했습니다.")
        _check_destination(output)
        temporary.chmod(0o644)
        os.replace(temporary, output)
        return metadata
    except (sqlite3.Error, OSError, ManseDataError):
        raise ManseImportError("만세력 DB를 생성하지 못했습니다. 기존 데이터는 보존했습니다.") from None
    finally:
        temporary.unlink(missing_ok=True)


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SQL Server tb_manse 내보내기를 로컬 만세력 DB로 변환")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_DATABASE)
    options = parser.parse_args(args)
    try:
        result = build_database(options.source, options.output)
    except ManseImportError as error:
        print(f"Woonari 만세력: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
