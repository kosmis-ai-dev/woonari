"""CR-015 / T-034: read verified non-personal source definitions from MySQL.

Archive restoration and personal selection are separate checks. Only the fixed
aliases below have source consumers with matching keys and columns. An archive
table with a similar name is never substituted automatically.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager, suppress
from copy import deepcopy
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from app.rules import GANJI

REGISTRY_PATH = Path(__file__).with_name("data") / "fortune_archive_registry.json"
METADATA_TABLE = "woonari_source_metadata"
CACHE_SECONDS = 300
FORMAT = "woonari.fortune-archive.v1"
TABLE_FORMAT = "woonari.fortune-archive-table.v1"
TEXT_PROFILE = "woonari.symcode-ascii-punctuation.v1"

# Proven from the original consumers' selected columns and equality predicates.
# Coverage and exact source rows are checked again before reading any definition.
VERIFIED_TABLE_ALIASES = {
    "tbPreLife": "tbPreLife",
    "flowerluck": "TB_FlowerLuck",
    "tbSaju_otherunse": "TB_Saju_OtherUnse",
    "tbSaju_private": "TB_Saju_Private",
    "tbSaju_dangsaju": "TB_Saju_DangSaju",
    "birthluck": "TB_birthDayLuck",
    "stoneluck": "TB_birthStoneLuck",
}
_SERVICE_TABLES = {
    "preluck": {"tbPreLife"},
    "flowerluck": {"flowerluck"},
    "carluck": {"tbSaju_otherunse"},
    "hpluck": {"tbSaju_otherunse"},
    "jusoluck": {"tbSaju_otherunse"},
    "lifetime": {"tbSaju_private", "tbSaju_dangsaju", "tbSaju_otherunse"},
    "birthluck": {"birthluck"},
    "jewelryluck": {"stoneluck"},
}
_KEYS = {
    "tbPreLife": ("div_flag", "div_date"),
    "TB_FlowerLuck": ("month", "day"),
    "TB_Saju_OtherUnse": ("unse", "sipkyuk_code"),
    "TB_Saju_Private": ("hname",),
    "TB_Saju_DangSaju": ("dang_code",),
    "TB_birthDayLuck": ("month", "day"),
    "TB_birthStoneLuck": ("month",),
}
_TEXT_COLUMNS = {
    "tbPreLife": {"content", "character", "parent", "child"},
    "TB_FlowerLuck": {"name_h", "name_e", "fw_word", "fw_column", "origin", "story", "unse"},
    "TB_Saju_OtherUnse": {f"desc{i}" for i in range(1, 7)},
    "TB_Saju_Private": {"desc1", "desc2", "desc3"},
    "TB_Saju_DangSaju": {"desc1", "desc2", "desc3"},
    "TB_birthDayLuck": {"unse"},
    "TB_birthStoneLuck": {"stname_h", "stname_e", "symbol", "unse"},
}
_PHYSICAL_COLUMNS = {
    "TB_birthDayLuck": {"month": "birthMon_ref", "day": "birthDay_ref", "unse": "contents"},
    "TB_birthStoneLuck": {"month": "birthMon_ref", "stname_h": "stoneName_kor",
                         "stname_e": "stoneName_en", "symbol": "stoneLang", "unse": "contents"},
}
_FLOWER_FACTS = {"name_h", "name_e", "fw_word", "fw_column", "origin"}
_STONE_FACTS = {"stname_h", "stname_e", "symbol"}
_FLOWER_MISSING = "원본 날짜별 꽃이름·꽃말·분류·원산지 자료가 없어 임의 배정하지 않습니다."
_STONE_MISSING = "stoneluck의 월별 보석이름·상징 자료가 없어 임의 배정하지 않습니다."
_HEX = re.compile(r"[a-f0-9]{64}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")
_UNSAFE_DEFINITION = re.compile(
    r"수명|단명|요절|사망|자살|자해|질병|불치|건강|죽|壽命|寿命|短命|早死|夭折|死亡|"
    r"(?:[0-9]+|몇)\s*세(?:에|까지)|(?:cancer|suicide|lifespan)", re.IGNORECASE,
)
_factory: Callable[[], Any] | None = None


class SourceArchiveError(Exception):
    """A value-free failure: never includes a SQL statement, row, or connection."""


class SourceTransportError(SourceArchiveError):
    pass


def _decode_transport(value: str) -> str:
    # Explicit Python display profile; the backup contains no original decoder.
    # Stored rows and their hashes remain untouched.
    allowed = {32, 34, 40, 41, 44, 45, 46, 47, 58, 59, 60, 61, 62, 63}

    def replace(match):
        raw = match.group(1)
        code = int(raw)
        if code not in allowed or str(code) != raw:
            raise SourceTransportError("지원하지 않는 원본 문구 전송 표기입니다.")
        return chr(code)

    result = re.sub(r"~symCode([0-9]+)~", replace, value)
    if re.search(r"~symcode", result, flags=re.IGNORECASE):
        raise SourceTransportError("원본 문구 전송 표기의 형식을 확인할 수 없습니다.")
    return result


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        elif not self.hidden and tag in {"br", "p", "div", "li", "tr"}:
            self.values.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1
        elif not self.hidden and tag in {"p", "div", "li", "tr"}:
            self.values.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.values.append(data)


def _plain_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > 100_000:
        raise SourceArchiveError("복원 정의의 문자열 형식을 확인할 수 없습니다.")
    parser = _PlainText()
    parser.feed(unescape(_decode_transport(value)))
    parser.close()
    result = "".join(parser.values)
    result = re.sub(r"\{(?:name|NAME)\}", "당신", result)
    return re.sub(r"\s+", " ", result).strip()


def _identifier(value: object, *, target=False) -> str:
    if (not isinstance(value, str) or not _IDENTIFIER.fullmatch(value)
            or (target and not value.startswith("woonari_source_"))):
        raise SourceArchiveError("복원 표 식별자를 확인할 수 없습니다.")
    return value


def _registry() -> tuple[dict, str]:
    try:
        raw = REGISTRY_PATH.read_bytes()
        value = json.loads(raw)
        if value.get("format") != FORMAT or not isinstance(value.get("tables"), list):
            raise ValueError
        names, targets = set(), set()
        for spec in value["tables"]:
            source = spec["source_table"]
            target = _identifier(spec["target_table"], target=True)
            if (not isinstance(source, str) or not source or source in names or target in targets
                    or type(spec["row_count"]) is not int or spec["row_count"] < 0
                    or not _HEX.fullmatch(spec["source_sha256"])
                    or not _HEX.fullmatch(spec["data_sha256"])):
                raise ValueError
            columns = spec["columns"]
            if (not isinstance(columns, list) or not columns
                    or len({_identifier(c["name"]) for c in columns}) != len(columns)):
                raise ValueError
            names.add(source)
            targets.add(target)
        return value, hashlib.sha256(raw).hexdigest()
    except Exception:
        raise SourceArchiveError("복원 자료의 고정 출처 목록을 확인할 수 없습니다.") from None


def configure_source_archive_store(factory: Callable[[], Any] | None) -> None:
    global _factory
    _factory = factory


def is_source_archive_configured() -> bool:
    return _factory is not None


def archive_status() -> dict:
    if _factory is None:
        return {"status": "not_connected", "actual_connection_checked": False,
                "issues": ["복원 원본 자료용 MySQL 연결이 설정되지 않았습니다."]}
    try:
        return _factory().status()
    except Exception:
        return {"status": "unavailable", "actual_connection_checked": False,
                "issues": ["복원 원본 자료의 연결·출처·실제 행 수를 확인할 수 없습니다."]}


class MySQLSourceArchiveStore:
    def __init__(self, connector: Callable[[], Any]):
        self.connector = connector
        self._verified: dict[str, dict] = {}
        self._expires_at = 0.0
        self._registry_sha256 = ""
        self._frozen_rows: dict[str, dict[int, tuple]] = {}
        self._lock = threading.RLock()

    @contextmanager
    def _connection(self):
        connection = None
        try:
            connection = self.connector()
            with connection.cursor() as cursor:
                cursor.execute("SELECT DATABASE()")
                if cursor.fetchone() != ("woonari",):
                    raise SourceArchiveError("복원 자료는 woonari DB에서만 읽습니다.")
            yield connection
        except SourceArchiveError:
            raise
        except Exception:
            raise SourceArchiveError("복원 원본 자료의 연결 또는 조회를 확인할 수 없습니다.") from None
        finally:
            if connection is not None:
                with suppress(Exception):
                    connection.close()

    def _provenance(self, connection, *, refresh=False) -> dict[str, dict]:
        registry, registry_sha = _registry()
        now = time.monotonic()
        with self._lock:
            if (not refresh and self._verified and now < self._expires_at
                    and self._registry_sha256 == registry_sha):
                return self._verified
            expected = {s["source_table"]: s for s in registry["tables"]}
            if not expected:
                raise SourceArchiveError("복원 원본 자료 목록이 비어 있습니다.")
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT source_table, source_sha256, data_sha256, row_count, payload "
                    f"FROM {METADATA_TABLE} ORDER BY source_table"
                )
                actual = cursor.fetchall()
                if len(actual) != len(expected):
                    raise SourceArchiveError("복원 표 출처 기록이 완전하지 않습니다.")
                seen = set()
                for source, source_sha, data_sha, count, payload in actual:
                    if source not in expected or source in seen:
                        raise SourceArchiveError("복원 표 출처 기록을 확인할 수 없습니다.")
                    spec = expected[source]
                    metadata = json.loads(payload)
                    checks = {
                        "format": TABLE_FORMAT, "source_table": source,
                        "target_table": spec["target_table"], "source_sha256": source_sha,
                        "data_sha256": data_sha, "row_count": count,
                        "columns": spec["columns"], "primary_key": spec.get("primary_key", []),
                        "registry_sha256": registry_sha, "mapping_status": "unverified",
                    }
                    if (source_sha != spec["source_sha256"] or data_sha != spec["data_sha256"]
                            or type(count) is not int or count != spec["row_count"]
                            or not isinstance(metadata, dict)
                            or any(metadata.get(k) != v for k, v in checks.items())):
                        raise SourceArchiveError("복원 표의 고정 출처 또는 데이터 해시가 다릅니다.")
                    seen.add(source)
                statements = [
                    f"SELECT %s AS source_table, COUNT(*) AS row_count FROM `{s['target_table']}`"
                    for s in expected.values()
                ]
                cursor.execute(" UNION ALL ".join(statements), tuple(expected))
                counts = cursor.fetchall()
                if (len(counts) != len(expected)
                        or len({r[0] for r in counts}) != len(expected)
                        or any(source not in expected or type(count) is not int
                               or count != expected[source]["row_count"] for source, count in counts)):
                    raise SourceArchiveError("복원 표의 실제 행 수가 원본과 다릅니다.")
                frozen = {}
                for source in set(VERIFIED_TABLE_ALIASES.values()) & set(expected):
                    spec = expected[source]
                    columns = ", ".join(f"`{c['name']}`" for c in spec["columns"])
                    cursor.execute(
                        f"SELECT `_woonari_row`, {columns} FROM `{spec['target_table']}` "
                        "ORDER BY `_woonari_row` ASC"
                    )
                    source_rows = cursor.fetchall()
                    if len(source_rows) != spec["row_count"]:
                        raise SourceArchiveError("연결 원본 표의 실제 행 수가 다릅니다.")
                    by_ordinal = {}
                    for ordinal, row in enumerate(source_rows, 1):
                        if type(row[0]) is not int or row[0] != ordinal:
                            raise SourceArchiveError("연결 원본 표의 보관 행 순서가 다릅니다.")
                        by_ordinal[ordinal] = self._normalize_row(spec, row[1:])
                    encoded = json.dumps(list(by_ordinal.values()), ensure_ascii=False,
                                         separators=(",", ":")).encode("utf-8")
                    if hashlib.sha256(encoded).hexdigest() != spec["data_sha256"]:
                        raise SourceArchiveError("연결 원본 표의 본문 또는 값이 고정 원본과 다릅니다.")
                    frozen[source] = by_ordinal
            self._verified = expected
            self._frozen_rows = frozen
            self._registry_sha256 = registry_sha
            self._expires_at = now + CACHE_SECONDS
            return expected

    @staticmethod
    def _normalize_row(spec: dict, row) -> tuple:
        if len(row) != len(spec["columns"]):
            raise SourceArchiveError("연결 원본 행의 열 수가 다릅니다.")
        result = []
        for column, value in zip(spec["columns"], row):
            if value is None:
                if not column["nullable"]:
                    raise SourceArchiveError("필수 원본 열이 비어 있습니다.")
            elif column["sql_type"] in {"tinyint", "smallint", "int", "bigint", "bit"}:
                if type(value) is not int:
                    raise SourceArchiveError("원본 정수 형식이 다릅니다.")
            elif column["sql_type"] in {"char", "varchar", "nchar", "nvarchar", "text", "ntext"}:
                if not isinstance(value, str):
                    raise SourceArchiveError("원본 문자열 형식이 다릅니다.")
            elif column["sql_type"] in {"smalldatetime", "datetime", "datetime2"}:
                if isinstance(value, str):
                    value = datetime.fromisoformat(value)
                if type(value) is not datetime or value.tzinfo is not None:
                    raise SourceArchiveError("원본 날짜·시간 형식이 다릅니다.")
                value = value.isoformat(timespec="microseconds")
            else:
                raise SourceArchiveError("연결 원본의 열 형식이 확인되지 않았습니다.")
            result.append(value)
        return tuple(result)

    def status(self) -> dict:
        with self._connection() as connection:
            specs = self._provenance(connection, refresh=True)
        mapped = set(VERIFIED_TABLE_ALIASES.values())
        return {
            "status": "verified_archive", "database": "woonari",
            "actual_connection_checked": True, "table_count": len(specs),
            "row_count": sum(s["row_count"] for s in specs.values()),
            "tables": [{"source_table": source, "target_table": spec["target_table"],
                        "row_count": spec["row_count"],
                        "status": "restored" if spec["row_count"] else "restored_empty",
                        "lookup_mapping": "verified_for_fixed_consumers" if source in mapped else "not_verified"}
                       for source, spec in specs.items()],
            "note": "복원 검증과 개인별 판정 준비는 별개입니다. 빈 원본·미검증 조회 규칙을 AI로 보완하지 않습니다.",
        }

    def resolve(self, service_id: str, decision: dict) -> dict:
        result = deepcopy(decision)
        aliases = _SERVICE_TABLES.get(service_id)
        if aliases is None:
            return result
        selected = [s for s in result.get("selectors", []) if s.get("table") in aliases]
        if not selected:
            return result
        all_facts = {}
        source = ""
        spec = None
        try:
            with self._connection() as connection:
                specs = self._provenance(connection)
                for selector in selected:
                    source = VERIFIED_TABLE_ALIASES[selector["table"]]
                    spec = specs.get(source)
                    if spec is None:
                        raise SourceArchiveError("해당 원본 표가 복원 목록에 없습니다.")
                    available = {c["name"] for c in spec["columns"]}
                    physical = _PHYSICAL_COLUMNS.get(source, {})
                    columns = selector.get("columns")
                    where = selector.get("where")
                    if (not isinstance(columns, list) or not columns
                            or set(columns) - _TEXT_COLUMNS[source]
                            or not isinstance(where, dict) or set(where) != set(_KEYS[source])
                            or {physical.get(c, c) for c in columns} - available
                            or {physical.get(c, c) for c in where} - available):
                        raise SourceArchiveError("확인된 원본 열·조회 조건과 다릅니다.")
                    self._validate_keys(source, where, service_id)
                    sql = (
                        "SELECT `_woonari_row`, "
                        + ", ".join(f"`{c['name']}`" for c in spec["columns"])
                        + f" FROM `{spec['target_table']}` WHERE "
                        + " AND ".join(f"`{physical.get(k, k)}` = %s" for k in _KEYS[source])
                        + " ORDER BY `_woonari_row` ASC LIMIT 2"
                    )
                    with connection.cursor() as cursor:
                        cursor.execute(sql, tuple(where[k] for k in _KEYS[source]))
                        rows = cursor.fetchall()
                    provenance = {"source_table": source, "source_sha256": spec["source_sha256"],
                                  "data_sha256": spec["data_sha256"], "where": deepcopy(where)}
                    provenance["text_projection_profile"] = TEXT_PROFILE
                    if not rows:
                        positions = {c["name"]: i for i, c in enumerate(spec["columns"])}
                        with self._lock:
                            expected_rows = self._frozen_rows.get(source, {})
                        if any(all(r[positions[physical.get(key, key)]] == where[key] for key in _KEYS[source])
                               for r in expected_rows.values()):
                            raise SourceArchiveError("고정 원본에 있는 선택 행이 사라졌습니다.")
                        selector.update(source_data_status="missing_source_row", source_provenance=provenance)
                        if selector.get("role") != "calculation" and selector.get("narrative") is not False:
                            selector["source_anchors"] = {
                                c: {"scope": "general_advice_only", "reason": "missing_source_row"}
                                for c in columns
                            }
                        continue
                    if len(rows) != 1:
                        raise SourceArchiveError("원본 선택키에 정확히 한 행이 대응하지 않습니다.")
                    row = rows[0]
                    if not row or type(row[0]) is not int:
                        raise SourceArchiveError("원본 보관 행을 확인할 수 없습니다.")
                    current = self._normalize_row(spec, row[1:])
                    with self._lock:
                        frozen = self._frozen_rows.get(source, {}).get(row[0])
                    if frozen != current:
                        raise SourceArchiveError("조회한 원본 행이 검증된 보관 행과 다릅니다.")
                    values = dict(zip((c["name"] for c in spec["columns"]), current))
                    anchors = {}
                    for column in columns:
                        value = values[physical.get(column, column)]
                        try:
                            text = _plain_text(value)
                        except SourceTransportError:
                            if selector.get("role") == "calculation" or selector.get("narrative") is False:
                                raise
                            anchors[column] = {"scope": "general_advice_only", "reason": "unsupported_source_transport"}
                            continue
                        if selector.get("role") == "calculation" or selector.get("narrative") is False:
                            if source == "TB_FlowerLuck" and column in _FLOWER_FACTS:
                                # A stored NULL is a verified absence, not a missing
                                # row or a request to invent a taxonomy value.
                                all_facts[column] = None if value is None else text
                            elif source == "TB_birthStoneLuck" and column in _STONE_FACTS:
                                all_facts[column] = None if value is None else text
                            continue
                        if not text:
                            anchors[column] = {"scope": "general_advice_only", "reason": "empty_source_definition"}
                        elif _UNSAFE_DEFINITION.search(text):
                            anchors[column] = {"scope": "general_advice_only", "reason": "sensitive_source_definition"}
                        else:
                            anchors[column] = {"text": text, "scope": "source_definition", **provenance}
                    selector.update(source_data_status="verified", source_provenance=provenance)
                    if anchors:
                        selector["source_anchors"] = anchors
            facts_complete = ((source == "TB_FlowerLuck" and set(all_facts) == _FLOWER_FACTS)
                              or (source == "TB_birthStoneLuck" and set(all_facts) == _STONE_FACTS))
            if spec and facts_complete:
                resolved_message = _FLOWER_MISSING if source == "TB_FlowerLuck" else _STONE_MISSING
                result["unresolved"] = [u for u in result.get("unresolved", []) if u != resolved_message]
                result.setdefault("facts", {})["verified_source_facts"] = {
                    "source_table": source, "values": all_facts,
                    "source_sha256": spec["source_sha256"], "data_sha256": spec["data_sha256"],
                    "null_fields": [key for key, value in all_facts.items() if value is None],
                    "missing_value_policy": "원본 NULL·빈 값은 그대로 없는 정보이며 분류·원산지·상징을 추정하지 않습니다.",
                    "text_projection_profile": TEXT_PROFILE,
                }
            result.setdefault("facts", {})["source_archive"] = {
                "status": ("verified_lookup" if all(s.get("source_data_status") == "verified"
                                                     for s in selected) else "missing_source_rows"),
                "source_tables": sorted({VERIFIED_TABLE_ALIASES[s["table"]] for s in selected}),
                "selector_count": len(selected), "member_rows_used": False,
                "verified_selector_count": sum(s.get("source_data_status") == "verified" for s in selected),
                "missing_selector_count": sum(s.get("source_data_status") == "missing_source_row" for s in selected),
            }
        except Exception:
            self._expires_at = 0.0
            # Returning an explicit dependency keeps include_ai=false useful and
            # prevents a DB/configuration error becoming a model-generated fact.
            result.setdefault("unresolved", []).append(
                f"{source}: 복원 원본의 출처·조회키·유일한 행을 확인하지 못했습니다. "
                "복원 자료 상태를 확인하세요."
            )
            result.setdefault("facts", {})["source_archive"] = {
                "status": "unavailable", "source_table": source, "member_rows_used": False,
            }
        return result

    @staticmethod
    def _validate_keys(source: str, where: dict, service_id: str) -> None:
        if source == "tbPreLife":
            flag, day = where["div_flag"], where["div_date"]
            if (type(flag) is not int or flag not in (1, 2, 3) or type(day) is not int
                    or not 1 <= day <= {1: 60, 2: 12, 3: 30}[flag]):
                raise SourceArchiveError("전생 원본 선택키 범위가 다릅니다.")
        elif source in {"TB_FlowerLuck", "TB_birthDayLuck"}:
            if any(type(where[k]) is not int or not 1 <= where[k] <= bound
                   for k, bound in (("month", 12), ("day", 31))):
                raise SourceArchiveError("탄생화 원본 날짜키 범위가 다릅니다.")
        elif source == "TB_birthStoneLuck":
            if type(where["month"]) is not int or not 1 <= where["month"] <= 12:
                raise SourceArchiveError("탄생석 원본 월키 범위가 다릅니다.")
        elif source == "TB_Saju_Private":
            if where["hname"] not in GANJI:
                raise SourceArchiveError("개인 사주 원본 일주 키가 다릅니다.")
        elif source == "TB_Saju_DangSaju":
            if where["dang_code"] not in tuple("abcdefghijkl"):
                raise SourceArchiveError("당사주 원본 선택키가 다릅니다.")
        else:
            expected = {"carluck": {"carnum"}, "hpluck": {"Hp"}, "jusoluck": {"juso"},
                        "lifetime": {"social", "money"}}[service_id]
            if (where["unse"] not in expected or not isinstance(where["sipkyuk_code"], str)
                    or where["sipkyuk_code"] not in tuple(str(i) for i in range(10))):
                raise SourceArchiveError("번호 원본 선택키 범위가 다릅니다.")


def resolve_decision(service_id: str, decision: dict) -> dict:
    if service_id not in _SERVICE_TABLES or _factory is None:
        return deepcopy(decision)
    try:
        return _factory().resolve(service_id, decision)
    except Exception:
        result = deepcopy(decision)
        result.setdefault("unresolved", []).append("복원 원본 자료의 연결을 확인하지 못했습니다.")
        return result
