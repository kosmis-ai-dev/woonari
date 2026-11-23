"""CR-012/T-024: portable source execution and private diagnostic boundaries."""

import hashlib
import json
from datetime import date, datetime

import pytest

from app.errors import DomainError
from app.models import Birth
from app.ported_interlife_leaves import (
    SERVICES,
    _data,
    _program,
    _run,
    _safe_where,
    decide,
    source_birth_dates,
)
from app.ported_ziwei import execute
from app.service_models import ServiceRequest
from tools.source_inventory import load_snapshot


class FixedRandom:
    def __init__(self):
        self.index = 0

    def seed(self, value=None):
        pass

    def random(self):
        self.index += 1
        return (self.index % 10) / 10


def request(parameters=None):
    return ServiceRequest(birth=Birth(year=1974, month=3, day=2, hour=8, minute=30, gender='male'),
                          partner=Birth(year=1975, month=4, day=5, hour=10, gender='female'),
                          target_date=date(2026, 11, 18), include_ai=False,
                          parameters={'server_time': '2026-11-18T12:34:00', **(parameters or {})})


def test_complete_frozen_source_metadata_and_statement_coverage():
    data = _data()
    inventory = load_snapshot()['files']
    assert len(data['services']) == 74
    assert len(data['sources']) >= 296
    for path, entry in data['sources'].items():
        assert {key: entry[key] for key in ('sha256', 'lines')} == inventory[path]
    coverage = data['source_statement_coverage']
    assert len(coverage) > 20000
    assert not any(row['category'] == 'unaccounted' for row in coverage.values())
    assert {row['category'] for row in coverage.values()} <= {
        'compiled', 'native_f_saju_delegate', 'structural_or_procedure_boundary',
        'unused_procedure', 'cookie_transport',
    }
    assert all(len(row['sha256']) == 64 for row in coverage.values())


@pytest.mark.parametrize('service_id', sorted(SERVICES))
def test_every_available_leaf_returns_diagnostics_without_original_asp(service_id):
    result = decide(service_id, request())
    assert result['facts']['source_algorithm_complete'] is True
    assert result['facts']['sql_executed'] is False
    assert result['facts']['source_rows_trusted'] is False
    assert result['unresolved']
    assert all(selector.get('table') for selector in result['selectors'])


def test_missing_titles_are_facts_but_direct_body_text_is_narrative():
    result = decide('interlife-jum-4', request())
    assert any('J036.db_title [' in field for field in result['unresolved'])
    assert not any('J037.db_data [' in field for field in result['unresolved'])
    assert any('J037.db_data [' in field for field in result['facts']['narrative_only_fields'])
    assert any(row['table'] == 'J036' and row['role'] == 'calculation' for row in result['selectors'])
    assert any(row['table'] == 'J037' and row['role'] == 'narrative' for row in result['selectors'])
    assert 'source_terms_required' not in result['unresolved']
    assert 'source_server_variable' not in result['unresolved']


def test_response_end_halts_source_before_fortune_body():
    identifier = 'old/unse/interlife/UNSE_DATA/common/function.asp:512'
    result = _run('interlife-jum-4', request({'source_queries': {
        identifier: [{'rows': [], 'columns': ['result_var'], 'record_count': 0}],
    }}), rng=FixedRandom())
    assert result['halts']
    assert result['state']['__source_halted__'] is True
    assert not any(row['body'] for row in result['queries'])


def test_source_rows_are_private_and_never_make_diagnostic_data_trusted():
    identifier = 'old/unse/interlife/UNSE_DATA/solve/J/J036.asp:12'
    row = {'DB_title': 'PRIVATE_ROW_TITLE_123456', 'DB_title_1': 'PRIVATE_ROW_KEYWORD_987654',
           'DB_data': 'PRIVATE_ROW_TEXT', 'DB_data_1': 'PRIVATE_OTHER_TEXT'}
    result = decide('interlife-jum-4', request({'source_queries': {
        identifier: [{'rows': [row], 'columns': list(row), 'record_count': 1}],
    }}))
    assert 'source_rows_unverified' in result['unresolved']
    assert result['facts']['source_rows_trusted'] is False
    encoded = json.dumps(result, ensure_ascii=False)
    assert 'PRIVATE_' not in encoded
    assert '19740302' not in encoded
    assert '1974-03-02' not in encoded
    assert '1975-04-05' not in encoded


def test_array_global_and_rng_state_are_shared_only_within_one_request():
    data = _data()
    before = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    first = _run('interlife-jum-4', request(), rng=FixedRandom())
    _run('interlife-name-3', request(), rng=FixedRandom())
    repeated = _run('interlife-jum-4', request(), rng=FixedRandom())
    assert [(row['id'], row['sql']) for row in first['queries'] if row['body']] == [
        (row['id'], row['sql']) for row in repeated['queries'] if row['body']]
    assert first['state']['guesu'] == repeated['state']['guesu']
    assert first['state']['guesu'] != first['state'].get('no')
    assert hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == before


def test_original_n005_implicit_call_discards_result_without_fixing_source():
    data = _data()
    route = data['services']['interlife-name-1']['routes'][0]
    program = [node for node in _program(data, route) if data['locations'].get(str(node[1])) == {
        'path': 'old/unse/interlife/UNSE_DATA/solve/N/N005.asp', 'line': 8,
    }]
    assert program
    result = execute(program, {'malun_no': 85}, functions={'__use': lambda kind, value: value})
    assert result['variables']['malun_no'] == 85
    assert not result['source_errors']


def test_additional_form_is_private_and_cannot_override_typed_birth():
    assert 'user_name' in SERVICES['interlife-jum-4']['source_form_fields']
    result = decide('interlife-jum-4', request({'source_form': {'user_name': 'PRIVATE_PERSON_123456'}}))
    assert 'source_form_unverified' in result['unresolved']
    assert 'PRIVATE_PERSON' not in json.dumps(result, ensure_ascii=False)
    with pytest.raises(DomainError):
        decide('interlife-jum-4', request({'source_form': {'request_year': '2000'}}))


def test_explicit_native_calendar_binding_is_validated_without_basic_manse(monkeypatch):
    def wrong_profile(*args):
        raise AssertionError('explicit native profile must not query tb_manse')
    monkeypatch.setattr('app.ported_interlife_leaves.solar_birth', wrong_profile)
    value = request({'source_solunar': 2}).model_copy(update={'partner': None})
    assert source_birth_dates('interlife-jum-4', value) == [date(1974, 3, 2)]
    with pytest.raises(DomainError) as error:
        source_birth_dates('interlife-jum-4', value.model_copy(update={'parameters': {'source_solunar': 1}}))
    assert error.value.code == 'source_calendar_binding_mismatch'


def test_native_hook_forwards_leap_request_tokens_and_original_fallback_policy(monkeypatch):
    def original_profile(birth, binding, tokens, policy):
        assert birth.leap_month is True
        assert binding == 3
        assert tokens == {'year': '2025', 'month': '06', 'day': '01'}
        assert policy == 'original_regular_fallback'
        return datetime(2025, 6, 25, 8, 0), {}
    def basic_profile(*args):
        raise AssertionError('source leap conversion must run before basic manse')
    monkeypatch.setattr('app.ported_interlife_leaves.native_birth', original_profile)
    monkeypatch.setattr('app.ported_interlife_leaves.solar_birth', basic_profile)
    value = request({'source_solunar': 3}).model_copy(update={
        'birth': Birth(year=2025, month=6, day=1, hour=8, gender='male', calendar='lunar', leap_month=True), 'partner': None})
    assert source_birth_dates('interlife-jum-4', value) == [date(2025, 6, 25)]


def test_repeated_original_input_faults_are_counted_without_repeating_output():
    result = decide('interlife-name-6', request())
    rows = [row for row in result['facts']['source_errors'] if row['source']['path'].endswith('/N/N001_2.asp')]
    assert len(rows) == 3
    assert all(row['count'] > 10000 for row in rows)
    assert 'hanjano1' in SERVICES['interlife-name-6']['source_form_fields']


@pytest.mark.parametrize('route', ['name_6-2.asp', 'name_6-3.asp', 'name_6-4.asp', 'name_6.asp'])
def test_all_original_naming_stages_are_executable(route):
    result = _run('interlife-name-6', request({'source_route': route}), rng=FixedRandom())
    assert result['route'].endswith('/' + route)


@pytest.mark.parametrize('sql,table', [
    ("SELECT DB_data FROM N001 WHERE name='甲乙'", 'N001'),
    ("SELECT DB_data FROM S001 WHERE id=12345", 'S001'),
    ("SELECT DB_data FROM S001 WHERE year=1974", 'S001'),
    ("SELECT DB_data FROM S001 WHERE DB_express='19740302'", 'S001'),
])
def test_private_selector_values_never_reach_public_evidence(sql, table):
    output = _safe_where(sql, table)
    assert all(isinstance(value, dict) and value['private_or_unverified_key'] for value in output.values())


@pytest.mark.parametrize('parameters', [
    {'source_queries': {'not_a_frozen_query': []}},
    {'source_queries': {'old/unse/interlife/UNSE_DATA/solve/J/J036.asp:12': [{'rows': 'private_wrong_type'}]}},
    {'source_path_contains_result': 1},
    {'source_request_date': {'year': '1974', 'month': 3, 'day': '02'}},
    {'source_form': {'request_year': '2000'}},
    {'source_form': {'not_an_original_field': '123'}},
    {'source_form': {'user_name': 123}},
    {'source_route': []},
])
def test_investigation_inputs_are_strict_and_errors_do_not_echo_private_data(parameters):
    with pytest.raises(DomainError) as error:
        decide('interlife-jum-4', request(parameters))
    assert error.value.code == 'invalid_service_parameters'
    assert 'private_' not in error.value.message
