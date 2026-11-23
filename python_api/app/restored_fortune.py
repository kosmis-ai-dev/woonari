"""CR-014 / T-031: inspect restored source data without inventing its meaning.

This is a read-only staging adapter. A row's presence is not evidence of a
completed fortune: the backup contains empty annual templates for 2021–2050.
"""

import json
from collections.abc import Callable
from contextlib import suppress
from decimal import Decimal
from typing import Any

from app.errors import DomainError

ANNUAL_TABLE = "woonari_legacy_year_luck"
MONTH_TABLE = "woonari_legacy_year_luck_month"
METADATA_TABLE = "woonari_legacy_fortune_metadata"
SOURCE_HASHES = {
    "TB_yearLuck": "869a1074b7c8e55c4fdd5ff45401317297ce2d10330e5fbeab7ee0a0d3c9e4b7",
    "TB_yearLuck_mon": "f427c8bb5d34da799f9b1c51f55863e9851e7f5db78b08a3b3edc8e8976e49d5",
}
DATA_HASHES = {
    "TB_yearLuck": "306c0076ec4b6062c034c7425d84af36d84268f958355c60e61c6bc28c03641b",
    "TB_yearLuck_mon": "0e0d965e48774252cb227423612bc0e323bfa6f2182c2c1ce4f1fdbd115526da",
}
MAPPING_REQUIREMENTS = [
    "일간을 gan_ref(0~9)로 바꾸는 원본 규칙: 표준 천간 순서와 도깨비 memno 순서는 서로 다릅니다.",
    "gend_ref의 0/1이 각각 어떤 성별인지 정하는 원본 규칙",
    "chapter 1~7의 항목명과 score1~11의 항목·기간 정의",
    "월별 gan_act/ji_act와 표시기간을 정하는 원본 호출 코드",
]
BACKUP_FINDING = (
    "MSSQL 백업은 복원됐지만 구 yearfortune del은 0행입니다. 별도 TB_yearLuck은 7,000행이며 "
    "2001~2020년에는 본문이 있고 2021~2050년은 빈 본문·별점 1·점수 0인 초기 행입니다. "
    "2027년 140행도 미작성 상태이며 사주 키·성별·항목 매핑은 미검증입니다. "
    "GET /v1/restored-data?year=2027에서 적재 상태와 필요한 자료를 확인하세요."
)
_factory: Callable[[], Any] | None = None


def configure_restored_fortune_store(factory: Callable[[], Any] | None) -> None:
    global _factory
    _factory = factory


def restored_data_status(year: int = 2027) -> dict:
    if type(year) is not int or not 2001 <= year <= 2050:
        raise DomainError("invalid_restored_year", "복원 자료의 조회 연도는 2001~2050년입니다.")
    if _factory is None:
        return {
            "status": "not_connected", "requested_year": year, "ready_for_ai": False,
            "issues": ["복원 판정 자료의 MySQL 어댑터가 연결되지 않았습니다."],
            "required_mapping": MAPPING_REQUIREMENTS.copy(),
        }
    return _factory().status(year)


class MySQLRestoredFortuneStore:
    """Uses only the project's injected MySQL connector; no credentials or SQL input."""

    def __init__(self, connector: Callable[[], Any]):
        self.connector = connector

    def status(self, year: int) -> dict:
        connection = None
        try:
            connection = self.connector()
            with connection.cursor() as cursor:
                cursor.execute("SELECT DATABASE()")
                if cursor.fetchone() != ("woonari",):
                    raise ValueError("wrong database")
                cursor.execute(
                    f"SELECT source_table, source_sha256, data_sha256, row_count, payload "
                    f"FROM {METADATA_TABLE} ORDER BY source_table"
                )
                metadata = {}
                for source, source_hash, data_hash, count, payload in cursor.fetchall():
                    value = json.loads(payload)
                    if (
                        source not in SOURCE_HASHES or source in metadata
                        or source_hash != SOURCE_HASHES[source]
                        or type(count) is not int
                        or count != (7000 if source == "TB_yearLuck" else 1200)
                        or value.get("format") != "woonari.restored-fortune.v1"
                        or value.get("source_table") != source
                        or value.get("source_sha256") != source_hash
                        or data_hash != DATA_HASHES[source]
                        or value.get("data_sha256") != data_hash
                        or value.get("row_count") != count
                        or value.get("mapping_status") != "unverified"
                    ):
                        raise ValueError("invalid provenance")
                    metadata[source] = count
                if set(metadata) != set(SOURCE_HASHES) or len(metadata) != 2:
                    raise ValueError("missing provenance")
                for source, table in (("TB_yearLuck", ANNUAL_TABLE),
                                      ("TB_yearLuck_mon", MONTH_TABLE)):
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    if cursor.fetchone() != (metadata[source],):
                        raise ValueError("inconsistent row count")
                default_numeric = " AND ".join(
                    ["starPoint = 1", *[f"score{i} = 0" for i in range(1, 12)],
                     *[f"idx_bujeok{i} = 0" for i in range(1, 6)]]
                )
                cursor.execute(
                    "SELECT COUNT(*), SUM(CHAR_LENGTH(contents) > 0), "
                    f"SUM(CHAR_LENGTH(contents) = 0 AND {default_numeric}), "
                    "COUNT(DISTINCT gan_ref, gend_ref, chapter) "
                    f"FROM {ANNUAL_TABLE} WHERE year_act = %s",
                    (year,),
                )
                rows, populated, placeholders, unique_keys = cursor.fetchone()
                if not (
                    type(rows) is int and type(unique_keys) is int
                    and rows == unique_keys == 140
                    and all(type(v) in (int, Decimal) and v == int(v)
                            and 0 <= v <= rows for v in (populated, placeholders))
                ):
                    raise ValueError("invalid coverage")
                populated, placeholders = int(populated), int(placeholders)
            issues = []
            if placeholders:
                issues.append(
                    f"{year}년 {placeholders}행은 본문이 비어 있고 별점 1·점수 0·부적 0인 초기 행입니다. "
                    "완성된 해당 연도 판정 자료로 사용할 수 없습니다."
                )
            if populated != rows:
                issues.append(f"{year}년 실제 본문이 있는 행은 {populated}/{rows}건입니다.")
            issues.append("복원 표를 개인 사주에 연결하는 원본 키·항목 매핑이 아직 검증되지 않았습니다.")
            return {
                "status": "staged_unverified", "database": "woonari",
                "requested_year": year, "ready_for_ai": False,
                "source_tables": metadata,
                "annual": {
                    "row_count": rows, "nonempty_content_rows": populated,
                    "placeholder_rows": placeholders,
                    "all_rows_have_content": populated == rows and placeholders == 0,
                    "source_order_evidence": {
                        "BU_query": ["chapter ASC", "idx DESC"],
                        "BU_result": ["a_chapter ASC"],
                        "getter_result": "no ORDER BY",
                    },
                },
                "required_mapping": MAPPING_REQUIREMENTS.copy(), "issues": issues,
                "policy": "기존 yearfortune에 자동 대입하거나 빈 판정을 AI로 생성하지 않습니다.",
            }
        except Exception:
            # Driver exceptions may contain private endpoints or connection values.
            raise DomainError(
                "restored_data_unavailable", "복원 판정 자료의 연결·출처·행 구성을 확인할 수 없습니다.", 503,
            ) from None
        finally:
            if connection is not None:
                with suppress(Exception):
                    connection.close()
