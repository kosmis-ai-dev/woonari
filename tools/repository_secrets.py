"""Redact literal publication credentials without decoding legacy source bytes.

CR-005 / T-012, CR-012 / T-025. Findings contain offsets and classifications only. Originals are
never written. This is a publication filter, not a general credential detector.
"""

from __future__ import annotations

import re

_LITERAL = re.compile(rb'"((?:""|[^"\r\n])*)"|\'([^\'\r\n]*)\'')
_CONNECTION_FIELD = re.compile(
    rb'\b(password|pwd|user\s*id|uid|id|username|server|data\s+source|'
    rb'initial\s+catalog|database|dsn)\s*=\s*'
    rb'(?:\'(?P<single>[^\'\r\n]*)\'|""(?P<double>[^"\r\n]*)""|'
    rb'(?P<plain>[^;"\'\r\n<>]*))', re.IGNORECASE
)
_CONNECTION_CONTEXT = re.compile(
    rb'\b(provider|data\s+source|server|driver|dsn|initial\s+catalog|database)\s*=', re.IGNORECASE
)
_ASSIGNMENT = re.compile(
    rb'(?P<key>[A-Za-z_][A-Za-z0-9_.-]*)["\']?\s*(?:=|:)\s*'
    rb'(?P<quote>["\'])(?P<value>[^"\'\r\n]*)(?P=quote)', re.IGNORECASE
)
_QUOTED_MAPPING_KEY = re.compile(rb'[A-Za-z_][A-Za-z0-9_.-]*["\']\s*:')
_CDO = re.compile(
    rb'(?:sendpassword|sendusername|smtpserver)["\']\s*\)\s*=\s*'
    rb'["\'](?P<value>[^"\'\r\n]*)["\']', re.IGNORECASE
)
_PLACEHOLDER = re.compile(
    rb'^(?:|\*+|x+|y+|'
    rb'your[-_ ].*|change.*|replace.*|REDACTED.*|<.*>|\$\{.*\}|None|null)$', re.IGNORECASE
)
_XML_ELEMENT = re.compile(
    rb'<(?P<key>[A-Za-z_][A-Za-z0-9_.-]*)\b[^>]*>'
    rb'(?P<value>[^<\r\n]*)</(?P=key)\s*>', re.IGNORECASE
)
_UNQUOTED = re.compile(
    rb'^\s*(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_.-]*)\s*'
    rb'(?:=|:)\s*(?P<value>[^"\'\r\n#;]+?)\s*(?:[#;].*)?$', re.IGNORECASE
)
_OPEN_ARGS = re.compile(
    rb'\b(?:\w*conn\w*|\w*dbcon\w*|con|cnn)\.open\s*\(?\s*'
    rb'(?P<source>"[^"\r\n]*"|\'[^\'\r\n]*\'|[^,\r\n]+)\s*,\s*'
    rb'["\'](?P<username>[^"\'\r\n]*)["\']\s*,\s*'
    rb'["\'](?P<password>[^"\'\r\n]*)["\']', re.IGNORECASE
)
_NON_CREDENTIAL_VALUE = re.compile(
    rb'[<>]|\b(?:select|update|insert|delete|where|function)\b', re.IGNORECASE
)
_TOKEN = re.compile(
    rb'\b(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}|'
    rb'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{40,}|'
    rb'(?:AKIA|ASIA)[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{15,})\b'
)
_PRIVATE_KEY = re.compile(
    rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'
    rb'.*?-----END (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----', re.DOTALL
)
_IPV4 = re.compile(rb'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
_HOST_REFERENCE = re.compile(
    rb'(?:data\s+source|server)\s*=\s*"\s*&\s*([A-Za-z_]\w*)', re.IGNORECASE
)

# Reviewed public OAuth/schema literals, not credentials. Keep this keyed by the
# exact repository path, finding kind and literal bytes: a changed value or any
# other credential in these modules must still pass through normal redaction.
_PUBLIC_AUTH_LITERALS = {
    ("python_api/app/auth_providers.py", "api_secret_literal"): frozenset({
        b"https://kauth.kakao.com/oauth/token",
        b"https://oauth2.googleapis.com/token",
        b"https://nid.naver.com/oauth2/token"
    }),
    ("python_api/app/auth_settings.py", "api_secret_literal"): frozenset({
        b"kakao_client_secret", b"google_client_secret", b"naver_client_secret"
    }),
    ("python_api/app/auth_settings.py", "service_host"): frozenset({b"127.0.0.1"}),
    ("python_api/app/config.py", "service_host"): frozenset({b"127.0.0.1"}),
    ("python_api/app/auth_store.py", "api_secret_literal"): frozenset({
        b"VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin"
    })
}


def _kind(key: bytes, path: str) -> str | None:
    key = re.sub(rb'[^a-z0-9]', b'', key.lower())
    context = path.lower()
    if re.search(rb'(?:password|passwd|pwd|pass|pw)$', key):
        return "credential_password"
    if re.search(rb'(?:api|secret|access|auth|client).*key|secret$|token$', key):
        return "api_secret_literal"
    if re.fullmatch(rb'(?:str)?(?:db|smtp|mail|ftp)(?:user|userid|username|uid|id)', key):
        return "service_username"
    if re.fullmatch(rb'(?:str)?(?:db|smtp|mail|ftp)(?:server|host|ip|address|datasource)', key):
        return "service_host"
    if key in {b'dbname', b'dbsource', b'dbdatabase'}:
        return "database_name"
    if 'dbcon' in context:
        if b'db' in key and key.endswith(b'id'):
            return "service_username"
        if b'db' in key and key.endswith(b'name'):
            return "database_name"
        if b'db' in key and re.search(rb'addr|host|server|ip', key):
            return "service_host"
    if key in {b'user', b'username', b'userid', b'uid', b'host', b'hostname', b'server', b'ip'} and (
        "dbcon" in context or "sftp" in context or "smtp" in context
    ):
        return "service_username" if key in {b'user', b'username', b'userid', b'uid'} else "service_host"
    return None


def _usable(value: bytes) -> bool:
    return bool(value.strip()) and not _PLACEHOLDER.fullmatch(value.strip())


def _replacement(value: bytes, kind: str) -> bytes:
    token = b'REDACTED_' + kind.upper().encode('ascii')
    # A private-key block can span lines; retain every original line ending.
    return b''.join(
        (token if part and not re.fullmatch(rb'\r\n|\r|\n', part) else part)
        for part in re.split(rb'(\r\n|\r|\n)', value)
    )


def redact(content: bytes, path: str) -> tuple[bytes, list[dict]]:
    """Return a sanitized copy and value-free findings using ORIGINAL offsets.

    ``start`` is inclusive and ``end`` exclusive. Source paths, line numbers,
    identifiers, table/column names and text outside matching literals remain.
    """
    ranges: list[tuple[int, int, str]] = []
    host_variables = {match.group(1).lower() for match in _HOST_REFERENCE.finditer(content)}

    def add(start: int, end: int, kind: str) -> None:
        value = content[start:end]
        if value in _PUBLIC_AUTH_LITERALS.get((path, kind), ()):
            return
        if start < end and _usable(value):
            ranges.append((start, end, kind))

    for match in _PRIVATE_KEY.finditer(content):
        add(match.start(), match.end(), 'private_key')
    for match in _TOKEN.finditer(content):
        add(match.start(), match.end(), 'api_token')

    offset = 0
    for line in content.splitlines(keepends=True):
        # Process full connection-string fields, including XML element text.
        if _CONNECTION_CONTEXT.search(line):
            quote_offset = quote_count = 0
            first_open, first_close = line.find(b'<'), line.find(b'>')
            for match in _CONNECTION_FIELD.finditer(line):
                field_group = next(group for group in ('single', 'double', 'plain') if match.group(group) is not None)
                start, end = match.span(field_group)
                value = match.group(field_group)
                # Reject unquoted VB expressions and request-derived variables.
                quote_count += line.count(b'"', quote_offset, start)
                quote_offset = start
                in_string = quote_count % 2 == 1
                xml_text = 0 <= first_open < match.start() and 0 <= first_close < match.start()
                if not (in_string or xml_text):
                    continue
                if re.search(rb'\b(?:request|session|application)\s*\(', value, re.IGNORECASE):
                    continue
                key = re.sub(rb'\s+', b'', match.group(1).lower())
                kind = 'database_password' if key in {b'password', b'pwd'} else (
                    'database_username' if key in {b'userid', b'uid', b'id', b'username'} else (
                        'database_host' if key in {b'server', b'datasource'} else 'database_name'
                    )
                )
                add(offset + start, offset + end, kind)

        quote_offset = quote_count = 0
        for match in _ASSIGNMENT.finditer(line):
            # A closing connection-string quote is not an opening literal:
            # "PWD=" & pwdVariable & ";..." must retain the VB expression.
            quote_count += line.count(b'"', quote_offset, match.start())
            quote_offset = match.start()
            inside_double_string = quote_count % 2 == 1
            quoted_mapping_key = bool(_QUOTED_MAPPING_KEY.match(line, match.start()))
            if inside_double_string and not quoted_mapping_key:
                continue
            kind = _kind(match.group('key'), path)
            value = match.group('value')
            if match.group('key').lower() in host_variables:
                kind = 'database_host'
            elif kind is None:
                for address in _IPV4.finditer(value):
                    if all(int(part) <= 255 for part in address.group().split(b'.')):
                        start = match.start('value') + address.start()
                        end = match.start('value') + address.end()
                        add(offset + start, offset + end, 'service_host')
            if (
                kind is None
                and 'dbcon' in path.lower()
                and b'db' in match.group('key').lower()
                and re.fullmatch(rb'\d{1,3}(?:\.\d{1,3}){3}', value)
            ):
                kind = 'database_host'
            if kind and not _NON_CREDENTIAL_VALUE.search(value):
                start, end = match.span('value')
                add(offset + start, offset + end, kind)

        for match in _CDO.finditer(line):
            start, end = match.span('value')
            kind = 'smtp_password' if b'sendpassword' in match.group().lower() else (
                'smtp_username' if b'sendusername' in match.group().lower() else 'smtp_host'
            )
            add(offset + start, offset + end, kind)

        for match in _XML_ELEMENT.finditer(line):
            kind = _kind(match.group('key'), path)
            if kind:
                start, end = match.span('value')
                add(offset + start, offset + end, kind)

        # .NET appSettings-style named credential values, not arbitrary value=.
        setting = re.search(rb'<add\s+[^>]*\bkey=["\']([^"\']+)["\'][^>]*>', line, re.IGNORECASE)
        if setting:
            kind = _kind(setting.group(1), path)
            value = re.search(rb'\bvalue=["\']([^"\']*)["\']', setting.group(), re.IGNORECASE)
            if kind and value:
                start, end = value.span(1)
                add(offset + setting.start() + start, offset + setting.start() + end, kind)

        # Environment/INI and prose labels can contain unquoted credentials;
        # never apply this rule to executable ASP/Python variable expressions.
        if path.lower().endswith(('.env', '.ini', '.conf', '.properties', '.txt', '.md')):
            match = _UNQUOTED.match(line.rstrip(b'\r\n'))
            if match:
                kind = _kind(match.group('key'), path)
                value = match.group('value')
                if kind and not _NON_CREDENTIAL_VALUE.search(value):
                    start, end = match.span('value')
                    add(offset + start, offset + end, kind)

        # Legacy connection targets are also repeated as plain/commented IPs
        # beside ADODB configuration, under inconsistent variable names.
        if _IPV4.search(line):
            nearby = content[max(0, offset - 2048):offset + len(line) + 2048]
            if re.search(rb'ADODB\.Connection|ConnectionString|\bdbcon\b|\bDSN\b', nearby, re.IGNORECASE):
                for match in _IPV4.finditer(line):
                    if all(int(part) <= 255 for part in match.group().split(b'.')):
                        add(offset + match.start(), offset + match.end(), 'database_host')

        # ADODB .Open with explicit DSN, username, password positional literals.
        for match in _OPEN_ARGS.finditer(line):
            for group, kind in (('username', 'database_username'), ('password', 'database_password')):
                start, end = match.span(group)
                add(offset + start, offset + end, kind)
            source = match.group('source')
            if source.startswith((b'"', b"'")) and b'=' not in source:
                start, end = match.span('source')
                add(offset + start + 1, offset + end - 1, 'database_name')
        offset += len(line)

    # Prefer outer matches, collapse duplicate detections, never rewrite twice.
    chosen: list[tuple[int, int, str]] = []
    for item in sorted(set(ranges), key=lambda row: (row[0], -row[1], row[2])):
        if chosen and item[0] < chosen[-1][1]:
            continue
        chosen.append(item)
    findings, parts = [], []
    previous = line_offset = 0
    line_number = 1
    for start, end, kind in chosen:
        line_number += content.count(b'\n', line_offset, start)
        line_offset = start
        findings.append({'path': path, 'start': start, 'end': end, 'kind': kind, 'line': line_number})
        parts.extend((content[previous:start], _replacement(content[start:end], kind)))
        previous = end
    parts.append(content[previous:])
    return b''.join(parts), findings
