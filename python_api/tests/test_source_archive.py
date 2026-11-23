"""CR-015 / T-034: fixed source lookups and fail-closed provenance checks."""

import hashlib
import json
from copy import deepcopy
from datetime import datetime

import pytest

import app.source_archive as archive


def spec(source, target, columns):
    return {
        "source_table": source, "target_table": target, "file": source + ".json",
        "source_sha256": "a" * 64, "data_sha256": "b" * 64, "row_count": 1,
        "columns": [{"name": c, "sql_type": ("int" if c in {"num", "div_flag", "div_date", "fw_no", "month", "day", "idx", "birthMon_ref", "birthDay_ref"}
                                               else "smalldatetime" if c.startswith("date_") else "text"), "max_length": 16,
                     "precision": 0, "scale": 0, "nullable": c in {"origin", "parent"}} for c in columns],
        "primary_key": [],
    }


@pytest.fixture
def registry():
    return {"format": archive.FORMAT, "tables": [
        spec("tbPreLife", "woonari_source_tbprelife",
             ["num", "div_flag", "div_date", "content", "character", "parent", "child"]),
        spec("TB_FlowerLuck", "woonari_source_tb_flowerluck",
             ["fw_no", "month", "day", "name_h", "name_e", "fw_word", "fw_column", "origin", "story", "unse"]),
        spec("TB_Saju_OtherUnse", "woonari_source_tb_saju_otherunse",
             ["unse", "sipkyuk_code", "sipkyuk", *[f"desc{i}" for i in range(1, 7)]]),
    ]}


class Connection:
    def __init__(self, registry):
        self.database, self.queries, self.closed = "woonari", [], 0
        self.registry = registry
        self.metadata, self.counts = [], []
        self.records = {
            "woonari_source_tbprelife": [{"num": 1, "div_flag": 1, "div_date": 3,
                "content": "<b>전통 이야기</b>를 관찰의 계기로 삼습니다.",
                "character": "서로의 차이를 살펴봅니다.", "parent": "가족의 의견을 듣습니다.",
                "child": "대화의 시간을 마련합니다."}],
            "woonari_source_tb_flowerluck": [{"fw_no": 1, "month": 3, "day": 2,
                "name_h": "예시꽃", "name_e": "Example flower", "fw_word": "관심",
                "fw_column": "예시 분류", "origin": "예시 원산지",
                "story": "작은 관심에 관한 전통 이야기입니다.", "unse": "꾸준한 관찰을 권합니다."}],
            "woonari_source_tb_saju_otherunse": [{"unse": "Hp", "sipkyuk_code": "2", "sipkyuk": "예시",
                **{f"desc{i}": f"대화 조언 {i}입니다." for i in range(1, 7)}}],
        }
        self.freeze()

    def freeze(self):
        self.metadata, self.counts = [], []
        for s in self.registry["tables"]:
            rows = [tuple(r[c["name"]] for c in s["columns"]) for r in self.records[s["target_table"]]]
            s["data_sha256"] = hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":"),
                default=lambda value: value.isoformat(timespec="microseconds")).encode()).hexdigest()
            value = {"format": archive.TABLE_FORMAT, **s, "registry_sha256": "c" * 64,
                     "mapping_status": "unverified"}
            self.metadata.append((s["source_table"], s["source_sha256"], s["data_sha256"],
                                  s["row_count"], json.dumps(value)))
            self.counts.append((s["source_table"], s["row_count"]))

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def execute(self, sql, values=()):
        assert sql.startswith("SELECT ")
        self.queries.append((sql, values))
        if "DATABASE()" in sql:
            self.result = [(self.database,)]
        elif "FROM woonari_source_metadata" in sql:
            self.result = self.metadata
        elif "COUNT(*)" in sql:
            self.result = self.counts
        else:
            columns = [c.strip(" `") for c in sql.removeprefix("SELECT ").split(" FROM ")[0].split(",")]
            target = sql.split(" FROM `")[1].split("`", 1)[0]
            records = [{"_woonari_row": ordinal, **r} for ordinal, r in enumerate(self.records[target], 1)]
            if " WHERE " in sql:
                keys = [k.split("`")[1] for k in sql.split(" WHERE ")[1].split(" ORDER BY ")[0].split(" AND ")]
                matched = [r for r in records if all(r.get(k) == v for k, v in zip(keys, values))][:2]
            else:
                matched = records
            self.result = [tuple(r[c] for c in columns) for r in matched]

    def fetchone(self):
        return self.result[0]

    def fetchall(self):
        return self.result

    def close(self):
        self.closed += 1


@pytest.fixture
def connected(registry, monkeypatch):
    monkeypatch.setattr(archive, "_registry", lambda: (deepcopy(registry), "c" * 64))
    connection = Connection(registry)
    store = archive.MySQLSourceArchiveStore(lambda: connection)
    monkeypatch.setattr(archive, "_factory", lambda: store)
    return connection, store


def past_decision():
    return {"facts": {}, "unresolved": [], "selectors": [{
        "id": "past-year", "table": "tbPreLife", "where": {"div_flag": 1, "div_date": 3},
        "columns": ["content", "character", "parent", "child"],
    }]}


def flower_decision():
    return {"facts": {}, "unresolved": [archive._FLOWER_MISSING], "selectors": [
        {"id": "flower-facts", "table": "flowerluck", "where": {"month": 3, "day": 2},
         "columns": ["name_h", "name_e", "fw_word", "fw_column", "origin"], "role": "calculation"},
        {"id": "flower-reading", "table": "flowerluck", "where": {"month": 3, "day": 2},
         "columns": ["story", "unse"]},
    ]}


def test_verified_past_lookup_preserves_keys_and_input(connected):
    connection, _ = connected
    decision = past_decision()
    original = deepcopy(decision)
    result = archive.resolve_decision("preluck", decision)
    selector = result["selectors"][0]
    assert decision == original
    assert selector["source_data_status"] == "verified"
    assert selector["source_anchors"]["content"]["scope"] == "source_definition"
    assert selector["source_anchors"]["content"]["text"] == "전통 이야기를 관찰의 계기로 삼습니다."
    assert "<b>" not in json.dumps(selector, ensure_ascii=False)
    assert selector["source_provenance"]["where"] == {"div_flag": 1, "div_date": 3}
    assert result["facts"]["source_archive"]["member_rows_used"] is False
    assert connection.closed == 1


def test_complete_flower_facts_resolve_only_matched_dependency(connected):
    decision = flower_decision()
    decision["unresolved"].append("별도 확인 필요")
    result = archive.resolve_decision("flowerluck", decision)
    assert result["unresolved"] == ["별도 확인 필요"]
    assert result["facts"]["verified_source_facts"]["values"]["name_h"] == "예시꽃"
    assert "source_anchors" not in result["selectors"][0]
    assert result["selectors"][1]["source_anchors"]["unse"]["scope"] == "source_definition"


def test_legitimate_null_flower_fact_is_preserved_without_invented_classification(connected):
    connection, _ = connected
    connection.records["woonari_source_tb_flowerluck"][0]["origin"] = None
    connection.freeze()
    result = archive.resolve_decision("flowerluck", flower_decision())
    assert archive._FLOWER_MISSING not in result["unresolved"]
    assert result["facts"]["verified_source_facts"]["values"]["origin"] is None
    assert result["facts"]["verified_source_facts"]["null_fields"] == ["origin"]


def test_number_lookup_uses_explicit_source_category_and_columns(connected):
    decision = {"facts": {}, "unresolved": [], "selectors": [{
        "id": "number-reading", "table": "tbSaju_otherunse",
        "where": {"unse": "Hp", "sipkyuk_code": "2"}, "columns": ["desc1", "desc2"],
    }]}
    result = archive.resolve_decision("hpluck", decision)
    assert result["selectors"][0]["source_anchors"]["desc2"]["text"] == "대화 조언 2입니다."
    assert not result["unresolved"]
    assert archive.resolve_decision("carluck", decision)["unresolved"]


@pytest.mark.parametrize("text", ["수명은 50세까지입니다.", "질병에 걸리는 운입니다.", "부모가 일찍 사망합니다.",
                                  "일찍 죽으니 운을 조심하세요.", "短命할 수 있습니다."])
def test_medical_or_lifespan_source_claims_never_enter_anchors(connected, text):
    connection, _ = connected
    connection.records["woonari_source_tbprelife"][0]["content"] = text
    connection.freeze()
    result = archive.resolve_decision("preluck", past_decision())
    anchor = result["selectors"][0]["source_anchors"]["content"]
    assert anchor["scope"] == "general_advice_only" and "text" not in anchor
    assert text not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize("case", ["duplicate", "wrong_database", "source_hash", "count", "column", "key"])
def test_invalid_source_is_a_dependency_instead_of_an_exception(connected, case):
    connection, _ = connected
    decision = past_decision()
    if case == "duplicate":
        connection.records["woonari_source_tbprelife"] *= 2
    elif case == "wrong_database":
        connection.database = "another_project"
    elif case == "source_hash":
        row = connection.metadata[0]
        connection.metadata[0] = (row[0], "d" * 64, *row[2:])
    elif case == "count":
        connection.counts[0] = (connection.counts[0][0], 2)
    elif case == "column":
        decision["selectors"][0]["columns"] = ["member_secret"]
    else:
        decision["selectors"][0]["where"]["div_date"] = "3 OR 1=1"
    result = archive.resolve_decision("preluck", decision)
    assert result["unresolved"]
    assert result["facts"]["source_archive"]["status"] == "unavailable"
    assert "source_anchors" not in result["selectors"][0]
    assert connection.closed == 1


def test_missing_text_row_stays_general_advice_without_fabricated_source_text(connected):
    connection, _ = connected
    decision = past_decision()
    decision["selectors"][0]["where"]["div_date"] = 4
    result = archive.resolve_decision("preluck", decision)
    assert not result["unresolved"]
    selector = result["selectors"][0]
    assert selector["source_data_status"] == "missing_source_row"
    assert selector["source_anchors"]["content"] == {
        "scope": "general_advice_only", "reason": "missing_source_row",
    }


def test_lifetime_uses_verified_aliases_without_crossing_category_keys(connected, registry):
    connection, _ = connected
    connection.records["woonari_source_tb_saju_otherunse"][0]["unse"] = "social"
    for source, target, key, value in (
        ("TB_Saju_Private", "woonari_source_tb_saju_private", "hname", "甲子"),
        ("TB_Saju_DangSaju", "woonari_source_tb_saju_dangsaju", "dang_code", "a"),
    ):
        item = spec(source, target, [key, "desc1", "desc2", "desc3"])
        registry["tables"].append(item)
        connection.records[target] = [{key: value, "desc1": "관찰에 관한 원본 조언입니다.",
                                       "desc2": "대화를 권합니다.", "desc3": "꾸준함을 권합니다."}]
    connection.freeze()
    decision = {"facts": {}, "unresolved": [], "selectors": [
        {"id": "private", "table": "tbSaju_private", "where": {"hname": "甲子"}, "columns": ["desc1"]},
        {"id": "dang", "table": "tbSaju_dangsaju", "where": {"dang_code": "a"}, "columns": ["desc2"]},
        {"id": "social", "table": "tbSaju_otherunse", "where": {"unse": "social", "sipkyuk_code": "2"}, "columns": ["desc1"]},
        {"id": "money", "table": "tbSaju_otherunse", "where": {"unse": "money", "sipkyuk_code": "2"}, "columns": ["desc2"]},
    ]}
    result = archive.resolve_decision("lifetime", decision)
    assert not result["unresolved"]
    assert [s["source_data_status"] for s in result["selectors"]] == [
        "verified", "verified", "verified", "missing_source_row",
    ]
    assert result["selectors"][1]["source_anchors"]["desc2"]["scope"] == "source_definition"


def test_unknown_services_do_not_issue_source_queries(connected):
    connection, _ = connected
    original = past_decision()
    assert archive.resolve_decision("starluck", original) == original
    assert connection.queries == []


@pytest.mark.parametrize("after_cache", [False, True])
def test_same_count_source_text_mutation_never_becomes_a_trusted_anchor(connected, after_cache):
    connection, store = connected
    if after_cache:
        assert not store.resolve("preluck", past_decision())["unresolved"]
    connection.records["woonari_source_tbprelife"][0]["content"] = "변조된 원문입니다."
    result = store.resolve("preluck", past_decision())
    assert result["unresolved"]
    assert result["facts"]["source_archive"]["status"] == "unavailable"
    assert "변조된 원문" not in json.dumps(result, ensure_ascii=False)
    assert "source_anchors" not in result["selectors"][0]


def test_disappearing_previously_verified_row_is_not_an_original_missing_key(connected):
    connection, store = connected
    assert not store.resolve("preluck", past_decision())["unresolved"]
    connection.records["woonari_source_tbprelife"] = []
    result = store.resolve("preluck", past_decision())
    assert result["unresolved"]
    assert result["facts"]["source_archive"]["status"] == "unavailable"


def test_provenance_cache_and_status_actual_recheck(connected):
    connection, store = connected
    store.resolve("preluck", past_decision())
    store.resolve("preluck", past_decision())
    assert sum("FROM woonari_source_metadata" in sql for sql, _ in connection.queries) == 1
    assert sum("COUNT(*)" in sql for sql, _ in connection.queries) == 1
    status = archive.archive_status()
    assert status["actual_connection_checked"] and status["table_count"] == 3
    assert status["row_count"] == 3
    assert sum("COUNT(*)" in sql for sql, _ in connection.queries) == 2
    assert "예시꽃" not in json.dumps(status, ensure_ascii=False)


def test_connection_error_is_sanitized_and_unconfigured_is_explicit(monkeypatch):
    def broken():
        raise RuntimeError("private-host-and-password")
    monkeypatch.setattr(archive, "_factory", broken)
    assert "private-host-and-password" not in json.dumps(archive.archive_status())
    assert archive.resolve_decision("preluck", past_decision())["unresolved"]
    monkeypatch.setattr(archive, "_factory", None)
    assert archive.archive_status()["status"] == "not_connected"
    assert archive.resolve_decision("preluck", past_decision()) == past_decision()


def test_html_script_and_placeholder_cleanup():
    assert archive._plain_text("<script>secret()</script><p>{name}&nbsp;관찰</p>") == "당신 관찰"


@pytest.mark.parametrize("field,bad", [("target_table", "member"),
    ("target_table", "woonari_source_x` JOIN member"), ("source_sha256", "invalid"), ("row_count", True)])
def test_registry_rejects_invalid_targets_and_provenance(tmp_path, monkeypatch, registry, field, bad):
    value = deepcopy(registry)
    value["tables"][0][field] = bad
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(value))
    monkeypatch.setattr(archive, "REGISTRY_PATH", path)
    with pytest.raises(archive.SourceArchiveError):
        archive._registry()


def install_source(connection, registry, source, target, columns, records):
    item = spec(source, target, columns)
    item['row_count'] = len(records)
    registry['tables'].append(item)
    connection.records[target] = records
    connection.freeze()


def stone_decision(*, lunar=False):
    unresolved = [archive._STONE_MISSING]
    if lunar:
        unresolved.append('원본 탄생석 음력 분기는 lmyMonth/lmyDay가 미할당입니다.')
    return {'facts': {}, 'unresolved': unresolved, 'selectors': [
        {'id': 'stone-facts', 'table': 'stoneluck', 'where': {'month': 3},
         'columns': ['stname_h', 'stname_e', 'symbol'], 'role': 'calculation'},
        {'id': 'stone-reading', 'table': 'stoneluck', 'where': {'month': 3}, 'columns': ['unse']},
    ]}


def add_stone(connection, registry, *, symbol='~symCode34~관심~symCode34~', content='<b>관찰</b>~symCode32~조언'):
    columns = ['idx', 'birthMon_ref', 'stoneName_kor', 'stoneName_en', 'stoneLang',
               'contents', 'date_write', 'date_edit']
    row = {'idx': 1, 'birthMon_ref': 3, 'stoneName_kor': '예시보석',
           'stoneName_en': 'Example stone', 'stoneLang': symbol, 'contents': content,
           'date_write': datetime(2010, 1, 1, 12, 30), 'date_edit': datetime(2010, 1, 1, 12, 30)}
    install_source(connection, registry, 'TB_birthStoneLuck', 'woonari_source_tb_birthstoneluck', columns, [row])
    return row


def test_solar_stone_maps_verified_month_and_columns_with_raw_rows_unchanged(connected, registry):
    connection, _ = connected
    row = add_stone(connection, registry)
    original = deepcopy(row)
    result = archive.resolve_decision('jewelryluck', stone_decision())
    assert not result['unresolved']
    assert result['facts']['verified_source_facts']['values'] == {
        'stname_h': '예시보석', 'stname_e': 'Example stone', 'symbol': '"관심"',
    }
    assert result['selectors'][1]['source_anchors']['unse']['text'] == '관찰 조언'
    assert result['selectors'][1]['source_provenance']['text_projection_profile'] == archive.TEXT_PROFILE
    assert row == original
    assert '~symCode' in row['contents']


def test_stone_source_data_cannot_repair_unassigned_original_lunar_branch(connected, registry):
    connection, _ = connected
    add_stone(connection, registry)
    result = archive.resolve_decision('jewelryluck', stone_decision(lunar=True))
    assert archive._STONE_MISSING not in result['unresolved']
    assert result['unresolved'] == ['원본 탄생석 음력 분기는 lmyMonth/lmyDay가 미할당입니다.']


def test_birthday_main_row_does_not_resolve_missing_wiki_dependencies(connected, registry):
    connection, _ = connected
    install_source(connection, registry, 'TB_birthDayLuck', 'woonari_source_tb_birthdayluck',
                   ['idx', 'birthMon_ref', 'birthDay_ref', 'contents', 'date_write', 'date_edit'], [{
                       'idx': 1, 'birthMon_ref': 3, 'birthDay_ref': 2, 'contents': '대화~symCode32~조언',
                       'date_write': datetime(2010, 1, 1), 'date_edit': datetime(2010, 1, 1)}])
    decision = {'facts': {}, 'unresolved': ['wiki_story·wiki_person 원본 자료가 필요합니다.'], 'selectors': [
        {'id': 'birth-reading', 'table': 'birthluck', 'where': {'month': 3, 'day': 2}, 'columns': ['unse']},
        {'id': 'birth-events', 'table': 'wiki_story', 'where': {'month': 3, 'day': 2}, 'columns': ['e_name'], 'role': 'calculation'},
    ]}
    result = archive.resolve_decision('birthluck', decision)
    assert result['selectors'][0]['source_anchors']['unse']['text'] == '대화 조언'
    assert result['unresolved'] == decision['unresolved']
    assert 'source_data_status' not in result['selectors'][1]


@pytest.mark.parametrize('token', ['~symCode65~', '~symCode032~', '~symCode32', '~symCode-1~', '~SYMCode32~'])
def test_unknown_transport_is_not_grounded_or_exposed(token, connected, registry):
    connection, _ = connected
    add_stone(connection, registry, content=token)
    result = archive.resolve_decision('jewelryluck', stone_decision())
    assert result['selectors'][1]['source_anchors']['unse'] == {
        'scope': 'general_advice_only', 'reason': 'unsupported_source_transport',
    }
    assert token not in json.dumps(result, ensure_ascii=False)


def test_unknown_fact_transport_remains_an_explicit_dependency(connected, registry):
    connection, _ = connected
    add_stone(connection, registry, symbol='~symCode65~')
    result = archive.resolve_decision('jewelryluck', stone_decision())
    assert result['unresolved']
    assert result['facts']['source_archive']['status'] == 'unavailable'
    assert 'verified_source_facts' not in result['facts']


def test_bounded_ascii_projection_decodes_punctuation_before_removing_hidden_script():
    encoded = '~symCode60~script~symCode62~secret()~symCode60~~symCode47~script~symCode62~안내~symCode44~~symCode32~끝~symCode46~'
    assert archive._plain_text(encoded) == '안내, 끝.'
    assert archive._plain_text('&lt;script&gt;secret()&lt;/script&gt;안내') == '안내'
    assert archive._decode_transport('~symCode34~A~symCode34~~symCode58~~symCode40~B~symCode41~') == '"A":(B)'


def test_datetime_canonicalization_matches_mysql_and_export_forms():
    item = spec('sample', 'woonari_source_sample', ['date_write'])
    assert archive.MySQLSourceArchiveStore._normalize_row(item, (datetime(2010, 1, 1, 12, 30),)) == ('2010-01-01T12:30:00.000000',)
    assert archive.MySQLSourceArchiveStore._normalize_row(item, ('2010-01-01T12:30:00',)) == ('2010-01-01T12:30:00.000000',)
    with pytest.raises(archive.SourceArchiveError):
        archive.MySQLSourceArchiveStore._normalize_row(item, ('2010-01-01T12:30:00+09:00',))
