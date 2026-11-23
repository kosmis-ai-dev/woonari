"""CR-015 / T-033: lossless, allowlisted MSSQL fortune-data archive for MySQL.

Only the checked-in registry can select tables and schemas. Private source rows
are validated before credentials are obtained. Existing application tables are
never altered; source keys retain their original, still-unverified semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
from collections import defaultdict
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))

from isolated_db import DatabaseCheckError, connect_mysql

DATABASE = "woonari"
REGISTRY = ROOT / "python_api/app/data/fortune_archive_registry.json"
PRIVATE_ROOT = ROOT / ".local/woonari/restore"
FORMAT = "woonari.fortune-archive.v1"
TABLE_FORMAT = "woonari.fortune-archive-table.v1"
METADATA_TABLE = "woonari_source_metadata"
METADATA_COLUMNS = ("source_table", "source_sha256", "data_sha256", "row_count", "payload")
ORDINAL = "_woonari_row"
LOCK_NAME = "woonari_cr015_fortune_archive"
BATCH_SIZE = 250
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_ ]{0,63}\Z")
ALLOWED_SOURCE_TABLES = frozenset({
    "dayfortune_test", "kjy_gp_character", "kjy_gp_content", "kjy_gp_gan", "kjy_gp_yukgap",
    "kjy_TB_Totalun", "kjy_tbSaju_dangsaju", "kjy_tbSaju_otherunse", "kjy_tbSaju_private",
    "TB_advice_2016", "TB_birthDayLuck", "TB_birthFlowerLuck", "TB_BirthLuck", "TB_birthSignLuck",
    "TB_birthStoneLuck", "TB_bloodTypeLuck", "TB_board_conText", "TB_board_conText_illust",
    "TB_bujeok", "tb_bujeokMap", "tb_bujeokPiece", "TB_CodeDetail del", "TB_dayfortune_2010 del",
    "TB_dayLuck", "tb_dayLuck_backUp", "TB_dayLuck_free", "tb_dayLuck_new del",
    "TB_dayLuck_old del", "TB_deathGodExplanation", "TB_FlowerLuck", "tb_Hanja", "tb_manse",
    "TB_maritalAdviceLuck", "TB_maritalDeathGodLuck", "tb_maritalHarmonyLuck",
    "tb_maritalPersonalLuck", "TB_meetingLuck", "TB_MoneyLuck", "TB_monLuck", "TB_monLuck del",
    "TB_MonthFor del", "tb_nameAppraisal", "TB_NameSolve del", "TB_NameSolve_KJY del",
    "tb_personalCompLuck", "TB_PreLife del", "TB_PreLife2 del", "TB_preLifeLuck", "TB_product",
    "TB_Product_Detail del", "TB_Product_Map del", "TB_Product2 del", "TB_ProductList del",
    "TB_Saju_DangSaju", "TB_Saju_OtherUnse", "TB_Saju_Private", "TB_sajuAdviceLuck",
    "TB_sky_tarot del", "TB_sky_tarotmind del", "TB_sms_dayLuck", "TB_sms_proverb",
    "TB_StarCoupleLuck", "TB_StarLuck del", "TB_sweetLuck", "TB_SweetLuck2 del", "tb_tarotLuck",
    "tb_unseCon", "tb_wholeLifeLuck", "TB_yearLuck", "tb_yearluck del", "TB_yearLuck_mon",
    "tb_yearLuck_mon del", "TB_yearluck3 del", "TB_yearluck4 del", "TB_yearluck5 del",
    "tbPreLife", "totalun", "yearfortune del",
})
TEXT_TYPES = {"char", "varchar", "nchar", "nvarchar", "text", "ntext", "sysname"}
INTEGER_LIMITS = {
    "tinyint": (0, 255), "smallint": (-32768, 32767),
    "int": (-2147483648, 2147483647), "bigint": (-9223372036854775808, 9223372036854775807),
}
DATETIME_TYPES = {"datetime", "smalldatetime", "datetime2"}
BINARY_TYPES = {"binary", "varbinary", "image", "timestamp", "rowversion"}
DECIMAL_TYPES = {"decimal", "numeric", "money", "smallmoney"}
FLOAT_TYPES = {"float", "real"}


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    sql_type: str
    max_length: int
    precision: int
    scale: int
    nullable: bool

    @property
    def mysql_type(self) -> str:
        if self.sql_type in TEXT_TYPES:
            return "LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
        if self.sql_type in BINARY_TYPES:
            return "LONGBLOB"
        if self.sql_type in {"bit", "tinyint"}:
            return "TINYINT UNSIGNED"
        if self.sql_type in INTEGER_LIMITS:
            return self.sql_type.upper()
        if self.sql_type in DATETIME_TYPES:
            return "DATETIME(6)"
        if self.sql_type in {"date", "time"}:
            return "DATE" if self.sql_type == "date" else "TIME(6)"
        if self.sql_type in DECIMAL_TYPES:
            return f"DECIMAL({self.precision},{self.scale})"
        if self.sql_type in FLOAT_TYPES:
            return "FLOAT" if self.sql_type == "real" else "DOUBLE"
        raise ValueError("unsupported SQL type")


@dataclass(frozen=True)
class TableSpec:
    source_table: str
    target_table: str
    file: str
    source_sha256: str
    data_sha256: str
    row_count: int
    columns: tuple[ColumnSpec, ...]
    primary_key: tuple[str, ...]


@dataclass(frozen=True)
class Snapshot:
    spec: TableSpec
    rows: list[tuple]
    metadata: dict


def target_name(source: str) -> str:
    slug = re.sub(r"[^a-z0-9_]", "_", source.lower())
    target = "woonari_source_" + slug
    if len(target) > 64:
        target = target[:55] + "_" + hashlib.sha256(source.encode()).hexdigest()[:8]
    return target


def _column(value: dict) -> ColumnSpec:
    names = ("name", "sql_type", "max_length", "precision", "scale", "nullable")
    column = ColumnSpec(**{name: value[name] for name in names})
    if (not isinstance(column.name, str) or IDENTIFIER.fullmatch(column.name) is None
            or column.name.casefold() == ORDINAL or not isinstance(column.sql_type, str)
            or any(type(v) is not int for v in (column.max_length, column.precision, column.scale))
            or type(column.nullable) is not bool or not 0 <= column.scale <= 30
            or not 0 <= column.precision <= 53
            or (column.sql_type in DECIMAL_TYPES
                and not 1 <= column.precision <= 38)
            or (column.sql_type in DECIMAL_TYPES and column.scale > column.precision)
            or (column.sql_type in {"datetime2", "time"} and column.scale > 6)):
        raise ValueError("invalid column")
    _ = column.mysql_type  # Reject unsupported types before any DB connection.
    return column


def table_spec(value: dict, *, require_data_hash: bool = True) -> TableSpec:
    source = value["source_table"]
    columns = tuple(_column(item) for item in value["columns"])
    data_hash = value.get("data_sha256", "")
    if (source not in ALLOWED_SOURCE_TABLES or value.get("source_schema", "dbo") != "dbo"
            or value["target_table"] != target_name(source)
            or value["file"] != value["target_table"] + ".json"
            or not isinstance(value["source_sha256"], str)
            or SHA256.fullmatch(value["source_sha256"]) is None
            or type(value["row_count"]) is not int or not 0 <= value["row_count"] <= 1_000_000
            or not columns or len(columns) > 512
            or len({c.name.casefold() for c in columns}) != len(columns)
            or (require_data_hash and
                (not isinstance(data_hash, str) or SHA256.fullmatch(data_hash) is None))):
        raise ValueError("invalid table registry")
    primary = value["primary_key"]
    if (not isinstance(primary, list) or len(primary) != len(set(primary))
            or any(name not in {c.name for c in columns} for name in primary)
            or any(c.nullable for c in columns if c.name in primary)):
        raise ValueError("invalid source primary key")
    return TableSpec(source, value["target_table"], value["file"], value["source_sha256"],
                     data_hash, value["row_count"], columns, tuple(primary))


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _invalid_constant(_value):
    raise ValueError("nonfinite JSON number")


def _json(raw: bytes):
    return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def data_digest(rows: list[tuple]) -> str:
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def normalize(column: ColumnSpec, value, *, source: bool):
    """Return canonical lossless JSON values, equally for source and MySQL reads."""
    kind = column.sql_type
    if value is None:
        if not column.nullable:
            raise ValueError("NULL in required column")
        return None
    if kind in TEXT_TYPES:
        if not isinstance(value, str) or len(value.encode("utf-8")) > 16_000_000:
            raise ValueError("invalid text")
        return value
    if kind in INTEGER_LIMITS:
        if type(value) is not int or not INTEGER_LIMITS[kind][0] <= value <= INTEGER_LIMITS[kind][1]:
            raise ValueError("invalid integer")
        return value
    if kind == "bit":
        if source:
            if type(value) is not bool:
                raise ValueError("invalid source bit")
        elif type(value) is not int or value not in (0, 1):
            raise ValueError("invalid stored bit")
        return int(value)
    if kind in DATETIME_TYPES:
        if source and not isinstance(value, str):
            raise ValueError("invalid datetime input")
        if isinstance(value, str):
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?", value) is None:
                raise ValueError("invalid datetime text")
            value = datetime.fromisoformat(value)
        if type(value) is not datetime or value.tzinfo is not None or value.year < 1000:
            raise ValueError("invalid datetime")
        return value.isoformat(timespec="microseconds")
    if kind == "date":
        if source and not isinstance(value, str):
            raise ValueError("invalid date input")
        if isinstance(value, str):
            value = date.fromisoformat(value)
        if type(value) is not date or value.year < 1000:
            raise ValueError("invalid date")
        return value.isoformat()
    if kind == "time":
        if source and not isinstance(value, str):
            raise ValueError("invalid time input")
        if isinstance(value, str):
            value = time.fromisoformat(value)
        if not source and type(value) is timedelta:
            if not timedelta(0) <= value < timedelta(days=1):
                raise ValueError("invalid time interval")
            value = (datetime(2000, 1, 1) + value).time()
        if type(value) is not time or value.tzinfo is not None:
            raise ValueError("invalid time")
        return value.isoformat(timespec="microseconds")
    if kind in DECIMAL_TYPES:
        if not isinstance(value, (str, Decimal)):
            raise ValueError("invalid exact decimal")
        with localcontext() as context:
            context.prec = 80
            number = Decimal(value)
            scaled = number.quantize(Decimal(1).scaleb(-column.scale))
            if (not number.is_finite() or number != scaled
                    or abs(number) >= Decimal(10) ** (column.precision - column.scale)):
                raise ValueError("decimal precision loss")
            return format(scaled, "f")
    if kind in FLOAT_TYPES:
        if type(value) not in (str, int, float):
            raise ValueError("invalid float")
        number = float(value)
        if kind == "real":
            number = struct.unpack("!f", struct.pack("!f", number))[0]
        if not math.isfinite(number):
            raise ValueError("nonfinite float")
        return number
    if kind in BINARY_TYPES:
        if source:
            if not isinstance(value, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", value):
                raise ValueError("invalid binary hex")
            return "0x" + value[2:].lower()
        if not isinstance(value, bytes):
            raise ValueError("invalid binary storage")
        return "0x" + value.hex()
    raise ValueError("unsupported type")


def validate_rows(spec: TableSpec, values) -> list[tuple]:
    if not isinstance(values, list) or len(values) != spec.row_count:
        raise ValueError("row count mismatch")
    names = tuple(c.name for c in spec.columns)
    keys = set()
    positions = tuple(names.index(key) for key in spec.primary_key)
    result = []
    for item in values:
        if not isinstance(item, dict) or set(item) != set(names):
            raise ValueError("source column mismatch")
        row = tuple(normalize(column, item[column.name], source=True) for column in spec.columns)
        if positions:
            key = tuple(row[position] for position in positions)
            if key in keys:
                raise ValueError("duplicate source primary key")
            keys.add(key)
        result.append(row)
    return result


def inspect_export(table: dict, path: Path) -> tuple[list[tuple], str]:
    """Build a canonical digest for an audited private export before registry freeze."""
    spec = table_spec(table, require_data_hash=False)
    if path.name != spec.file or path.is_symlink() or not path.is_file():
        raise ValueError("invalid export file")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != spec.source_sha256:
        raise ValueError("source file digest mismatch")
    rows = validate_rows(spec, _json(raw))
    return rows, data_digest(rows)


def load_registry() -> tuple[dict, str, tuple[TableSpec, ...]]:
    if REGISTRY.is_symlink() or not REGISTRY.is_file():
        raise ValueError("missing trusted registry")
    raw = REGISTRY.read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError("oversized registry")
    registry = _json(raw)
    if (not isinstance(registry, dict) or registry.get("format") != FORMAT
            or registry.get("source_backup") != "dbkosmis_20251106.bak"
            or not isinstance(registry.get("tables"), list) or not registry["tables"]):
        raise ValueError("invalid registry")
    specs = tuple(table_spec(value) for value in registry["tables"])
    if (len({s.source_table for s in specs}) != len(specs)
            or len({s.target_table.casefold() for s in specs}) != len(specs)):
        raise ValueError("duplicate registry table")
    return registry, hashlib.sha256(raw).hexdigest(), specs


def local_snapshots(directory: Path) -> list[Snapshot]:
    try:
        registry, registry_hash, specs = load_registry()
        directory = Path(directory)
        relative = directory.resolve(strict=True).relative_to(PRIVATE_ROOT.resolve(strict=True))
        for ancestor in (PRIVATE_ROOT, *(PRIVATE_ROOT / Path(*relative.parts[:i])
                                        for i in range(1, len(relative.parts) + 1))):
            if ancestor.is_symlink():
                raise ValueError("symlink export directory")
        result = []
        for value, spec in zip(registry["tables"], specs, strict=True):
            rows, digest = inspect_export(value, directory / spec.file)
            if digest != spec.data_sha256:
                raise ValueError("canonical source digest mismatch")
            metadata = {
                "format": TABLE_FORMAT, "source_table": spec.source_table,
                "target_table": spec.target_table, "source_sha256": spec.source_sha256,
                "data_sha256": digest, "row_count": len(rows),
                "columns": [asdict(column) for column in spec.columns],
                "primary_key": list(spec.primary_key), "registry_sha256": registry_hash,
                "source_backup": registry["source_backup"], "mapping_status": "unverified",
                "ordinal_semantics": "export snapshot order; not an ASP query order",
            }
            result.append(Snapshot(spec, rows, metadata))
        return result
    except Exception:  # noqa: BLE001 - no source text or private paths in errors
        raise DatabaseCheckError("운세 원본 자료의 허용 목록·해시·열·형식·키를 검증하지 못했습니다.") from None


def _quote(names) -> str:
    return ", ".join(f"`{name}`" for name in names)


def _create_tables(cursor, snapshots: list[Snapshot]) -> None:
    # All DDL precedes the data transaction because MySQL DDL commits implicitly.
    for snapshot in snapshots:
        spec = snapshot.spec
        columns = ", ".join(f"`{column.name}` {column.mysql_type} "
                            + ("NULL" if column.nullable else "NOT NULL")
                            for column in spec.columns)
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS `{DATABASE}`.`{spec.target_table}` ("
            f"`{ORDINAL}` BIGINT NOT NULL, {columns}, PRIMARY KEY (`{ORDINAL}`)) "
            "ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
        )
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS `{DATABASE}`.`{METADATA_TABLE}` ("
        "`source_table` VARCHAR(128) NOT NULL, `source_sha256` CHAR(64) NOT NULL, "
        "`data_sha256` CHAR(64) NOT NULL, `row_count` BIGINT NOT NULL, `payload` LONGTEXT NOT NULL, "
        "PRIMARY KEY (`source_table`)) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
    )


def _verify_schema(cursor, snapshots: list[Snapshot]) -> None:
    targets = tuple(s.spec.target_table for s in snapshots) + (METADATA_TABLE,)
    placeholders = ", ".join("%s" for _ in targets)
    parameters = (DATABASE, *targets)
    cursor.execute(
        "SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s "
        f"AND TABLE_NAME IN ({placeholders})", parameters,
    )
    engines = dict(cursor.fetchall())
    if set(engines) != set(targets) or any(engine != "InnoDB" for engine in engines.values()):
        raise DatabaseCheckError("운세 원본 보관 테이블의 InnoDB 엔진을 확인할 수 없습니다.")
    cursor.execute(
        "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, EXTRA, COLUMN_TYPE, "
        "COLLATION_NAME, NUMERIC_PRECISION, NUMERIC_SCALE, DATETIME_PRECISION, "
        "CHARACTER_MAXIMUM_LENGTH FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s "
        f"AND TABLE_NAME IN ({placeholders}) ORDER BY TABLE_NAME, ORDINAL_POSITION", parameters,
    )
    schemas = defaultdict(list)
    for table, *row in cursor.fetchall():
        schemas[table].append(tuple(row))
    expected = {s.spec.target_table: (ColumnSpec(ORDINAL, "bigint", 8, 19, 0, False),
                                     *s.spec.columns) for s in snapshots}
    expected[METADATA_TABLE] = (
        ColumnSpec("source_table", "varchar", 128, 0, 0, False),
        ColumnSpec("source_sha256", "char", 64, 0, 0, False),
        ColumnSpec("data_sha256", "char", 64, 0, 0, False),
        ColumnSpec("row_count", "bigint", 8, 19, 0, False),
        ColumnSpec("payload", "text", 16, 0, 0, False),
    )
    for table, columns in expected.items():
        actual = schemas[table]
        if len(actual) != len(columns):
            raise DatabaseCheckError("기존 운세 원본 보관 테이블의 열 구성이 다릅니다.")
        for column, row in zip(columns, actual, strict=True):
            name, kind, nullable, extra, full_type, collation, precision, scale, dt_precision, length = row
            mysql_type = column.mysql_type.split()[0].split("(")[0].lower()
            if table == METADATA_TABLE and column.name in METADATA_COLUMNS[:3]:
                mysql_type = "varchar" if column.name == "source_table" else "char"
            valid = (
                name == column.name and kind == mysql_type and not extra
                and nullable == ("YES" if column.nullable else "NO")
                and ("unsigned" in full_type.lower()) == (column.sql_type in {"tinyint", "bit"})
                and (column.sql_type not in TEXT_TYPES or collation == "utf8mb4_bin")
                and (column.sql_type not in DECIMAL_TYPES
                     or (precision, scale) == (column.precision, column.scale))
                and (column.sql_type not in DATETIME_TYPES | {"time"} or dt_precision == 6)
            )
            if (not valid or (table == METADATA_TABLE and column.name in METADATA_COLUMNS[:3]
                              and length != column.max_length)):
                raise DatabaseCheckError("기존 운세 원본 보관 테이블의 형식·정밀도·문자열 구성이 다릅니다.")
    cursor.execute(
        "SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME "
        "FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=%s "
        f"AND TABLE_NAME IN ({placeholders}) ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX", parameters,
    )
    indexes = defaultdict(lambda: defaultdict(list))
    for table, name, nonunique, _position, column in cursor.fetchall():
        indexes[table][(name, nonunique)].append(column)
    for table in targets:
        desired = {("PRIMARY", 0): ["source_table" if table == METADATA_TABLE else ORDINAL]}
        if dict(indexes[table]) != desired:
            raise DatabaseCheckError("운세 원본 보관 테이블의 유일 키 구성이 다릅니다.")
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE EVENT_OBJECT_SCHEMA=%s "
        f"AND EVENT_OBJECT_TABLE IN ({placeholders})", parameters,
    )
    if cursor.fetchone() != (0,):
        raise DatabaseCheckError("트리거가 있는 운세 원본 보관 테이블은 자동 적재하지 않습니다.")


def _remote_rows(cursor, spec: TableSpec) -> list[tuple]:
    cursor.execute(
        f"SELECT `{ORDINAL}`, {_quote(c.name for c in spec.columns)} "
        f"FROM `{DATABASE}`.`{spec.target_table}` ORDER BY `{ORDINAL}` FOR UPDATE"
    )
    result = []
    for index, record in enumerate(cursor.fetchall(), 1):
        if len(record) != len(spec.columns) + 1 or type(record[0]) is not int or record[0] != index:
            raise ValueError("invalid snapshot ordinal")
        result.append(tuple(normalize(column, value, source=False)
                            for column, value in zip(spec.columns, record[1:], strict=True)))
    return result


def _parameters(spec: TableSpec, rows: list[tuple], start: int) -> list[tuple]:
    result = []
    for index, row in enumerate(rows, start + 1):
        stored = []
        for column, value in zip(spec.columns, row, strict=True):
            if value is not None and column.sql_type in BINARY_TYPES:
                value = bytes.fromhex(value[2:])
            stored.append(value)
        result.append((index, *stored))
    return result


def _copy_data(cursor, snapshots: list[Snapshot]) -> list[dict]:
    cursor.execute(f"SELECT {_quote(METADATA_COLUMNS)} FROM `{DATABASE}`.`{METADATA_TABLE}` FOR UPDATE")
    stored_metadata = cursor.fetchall()
    existing = {row[0]: tuple(row) for row in stored_metadata}
    if len(existing) != len(stored_metadata) or set(existing) - {s.spec.source_table for s in snapshots}:
        raise DatabaseCheckError("운세 원본 출처 정보에 알 수 없는 테이블이 있습니다.")
    reports = []
    for snapshot in snapshots:
        spec, rows, metadata = snapshot.spec, snapshot.rows, snapshot.metadata
        payload = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        expected = (spec.source_table, spec.source_sha256, spec.data_sha256, len(rows), payload)
        previous = existing.get(spec.source_table)
        if previous:
            try:
                same = (len(previous) == 5 and previous[:4] == expected[:4]
                        and json.loads(previous[4]) == metadata)
            except (ValueError, TypeError, RecursionError):
                same = False
            if not same:
                raise DatabaseCheckError("기존 운세 원본 출처 정보가 다릅니다. 기존 자료를 보존합니다.")
        remote = _remote_rows(cursor, spec)
        if previous or remote:
            if remote != rows or data_digest(remote) != spec.data_sha256:
                raise DatabaseCheckError("기존 운세 원본 자료가 다릅니다. 덮어쓰지 않고 중단합니다.")
            status = "already_present"
        else:
            statement = (
                f"INSERT INTO `{DATABASE}`.`{spec.target_table}` "
                f"({_quote((ORDINAL, *(c.name for c in spec.columns)))}) "
                f"VALUES ({', '.join('%s' for _ in range(len(spec.columns) + 1))})"
            )
            for offset in range(0, len(rows), BATCH_SIZE):
                cursor.executemany(statement, _parameters(spec, rows[offset:offset + BATCH_SIZE], offset))
            copied = _remote_rows(cursor, spec)
            if copied != rows or data_digest(copied) != spec.data_sha256:
                raise DatabaseCheckError("적재 후 원본 행·해시가 달라 전체 적재를 취소했습니다.")
            status = "imported" if rows else "empty_schema_preserved"
        if not previous:
            cursor.execute(
                f"INSERT INTO `{DATABASE}`.`{METADATA_TABLE}` ({_quote(METADATA_COLUMNS)}) "
                "VALUES (%s, %s, %s, %s, %s)", expected,
            )
        reports.append({"source_table": spec.source_table, "table": spec.target_table,
                        "status": status, "row_count": len(rows), "data_sha256": spec.data_sha256,
                        "source_sha256": spec.source_sha256})
    return reports


def import_mysql(directory: Path) -> dict:
    snapshots = local_snapshots(directory)
    connection = connect_mysql()
    locked = False
    try:
        connection.autocommit(True)
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            if cursor.fetchone() != (DATABASE,):
                raise DatabaseCheckError("운세 원본 자료는 woonari DB에만 적재합니다.")
            cursor.execute("SELECT GET_LOCK(%s, 2)", (LOCK_NAME,))
            if cursor.fetchone() != (1,):
                raise DatabaseCheckError("다른 운세 원본 적재 작업이 진행 중입니다.")
            locked = True
            _create_tables(cursor, snapshots)
            _verify_schema(cursor, snapshots)
        connection.autocommit(False)
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        connection.begin()
        with connection.cursor() as cursor:
            tables = _copy_data(cursor, snapshots)
        connection.commit()
        return {"database": DATABASE, "tables": tables, "table_count": len(tables),
                "row_count": sum(t["row_count"] for t in tables),
                "personal_data_imported": False, "personal_mapping_verified": False}
    except DatabaseCheckError:
        with suppress(Exception):
            connection.rollback()
        raise
    except Exception:  # noqa: BLE001 - SQL errors may contain private source or connection values
        with suppress(Exception):
            connection.rollback()
        raise DatabaseCheckError("운세 원본 자료의 MySQL 적재·검증에 실패했습니다.") from None
    finally:
        if locked:
            with suppress(Exception), connection.cursor() as cursor:
                cursor.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))
        with suppress(Exception):
            connection.close()


def main(args: list[str]) -> int:
    parser = argparse.ArgumentParser(description="회원 자료를 제외한 검증된 운세 원본을 woonari에 보관합니다.")
    parser.add_argument("source_directory", type=Path)
    options = parser.parse_args(args)
    try:
        report = import_mysql(options.source_directory)
    except DatabaseCheckError as error:
        print(f"Woonari 운세 원본: {error}", file=sys.stderr)
        return 1
    except Exception:  # noqa: BLE001 - do not echo unexpected parser/source errors
        print("Woonari 운세 원본: 적재 도구 실행에 실패했습니다.", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
