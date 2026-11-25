"""Synthetic publication safety checks; never embed production credentials."""

import json
import unittest

from repository_secrets import redact


class RedactionTests(unittest.TestCase):
    def test_reviewed_social_constants_are_public_in_only_their_exact_paths(self):
        cases = [
            ('python_api/app/auth_providers.py', b'token = "https://kauth.kakao.com/oauth/token"\n'),
            ('python_api/app/auth_providers.py', b'token = "https://oauth2.googleapis.com/token"\n'),
            ('python_api/app/auth_providers.py', b'token = "https://nid.naver.com/oauth2/token"\n'),
            ('python_api/app/auth_settings.py', b'"KAKAO_CLIENT_SECRET": "kakao_client_secret"\n'),
            ('python_api/app/auth_settings.py', b'"GOOGLE_CLIENT_SECRET": "google_client_secret"\n'),
            ('python_api/app/auth_settings.py', b'"NAVER_CLIENT_SECRET": "naver_client_secret"\n'),
            ('python_api/app/auth_settings.py', b'auth_public_base_url = "http://127.0.0.1:9090"\n'),
            ('python_api/app/auth_store.py', b'secret = "VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin"\n')
        ]
        for path, source in cases:
            with self.subTest(path=path, source=source):
                self.assertEqual(redact(source, path), (source, []))
                other, findings = redact(source, 'other_project/' + path)
                self.assertNotEqual(other, source)
                self.assertEqual(len(findings), 1)

    def test_social_module_allowlist_does_not_exempt_actual_credentials(self):
        cases = [
            ('python_api/app/auth_providers.py', b'token = "fixture_changed_provider_secret"\n'),
            ('python_api/app/auth_settings.py', b'"KAKAO_CLIENT_SECRET": "fixture_changed_kakao_secret"\n'),
            ('python_api/app/auth_settings.py', b'"GOOGLE_CLIENT_SECRET": "fixture_changed_google_secret"\n'),
            ('python_api/app/auth_settings.py', b'"NAVER_CLIENT_SECRET": "fixture_changed_naver_secret"\n'),
            ('python_api/app/auth_store.py', b'secret = "fixture_changed_schema_secret"\n')
        ]
        for path, source in cases:
            with self.subTest(path=path):
                result, findings = redact(source, path)
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0]['kind'], 'api_secret_literal')
                self.assertNotIn(b'fixture_changed_', result)

    def test_social_public_literals_do_not_hide_adjacent_secrets_or_changed_urls(self):
        source = (
            b'token = "https://oauth2.googleapis.com/token"\n'
            b'client_secret = "fixture_adjacent_secret"\n'
            b'token = "https://oauth2.googleapis.com/token?client_secret=fixture_query_secret"\n'
        )
        result, findings = redact(source, 'python_api/app/auth_providers.py')
        self.assertEqual(len(findings), 2)
        self.assertIn(b'token = "https://oauth2.googleapis.com/token"', result)
        self.assertNotIn(b'fixture_', result)
        self.assertEqual([source[row['start']:row['end']] for row in findings], [
            b'fixture_adjacent_secret',
            b'https://oauth2.googleapis.com/token?client_secret=fixture_query_secret'
        ])

    def test_social_loopback_exception_is_exact_and_does_not_cover_passwords(self):
        source = (
            b'auth_public_base_url = "http://127.0.0.1:9090"\n'
            b'auth_public_base_url = "http://192.0.2.20:9090"\n'
            b'auth_public_base_url = "http://127.0.0.2:9090"\n'
            b'password = "127.0.0.1"\n'
        )
        result, findings = redact(source, 'python_api/app/auth_settings.py')
        self.assertEqual(len(findings), 3)
        self.assertIn(b'"http://127.0.0.1:9090"', result)
        self.assertNotIn(b'192.0.2.20', result)
        self.assertNotIn(b'127.0.0.2', result)
        self.assertIn(b'password = "REDACTED_CREDENTIAL_PASSWORD"', result)
        self.assertEqual(redact(result, 'python_api/app/auth_settings.py'), (result, []))

    def test_large_single_line_rules_preserve_data_and_redact_only_credentials(self):
        rules = [{"name": "normal-rule", "value": "harmless-value"} for _ in range(20000)]
        source = json.dumps({"rules": rules, "api_key": "fixture_private_key"}).encode()
        result, rows = redact(source, 'rules.json')
        decoded = json.loads(result)
        self.assertEqual(decoded['rules'], rules)
        self.assertEqual(decoded['api_key'], 'REDACTED_API_SECRET_LITERAL')
        self.assertEqual(len(rows), 1)
        self.assertEqual(source[rows[0]['start']:rows[0]['end']], b'fixture_private_key')
        self.assertEqual(rows[0]['line'], 1)

    def test_multiple_replacements_keep_original_offsets_and_line_numbers(self):
        source = b'password="fixture_first"\r\n\r\napi_key="fixture_second"\n'
        result, rows = redact(source, 'fixture.ini')
        self.assertEqual([row['line'] for row in rows], [1, 3])
        self.assertEqual([source[row['start']:row['end']] for row in rows],
                         [b'fixture_first', b'fixture_second'])
        self.assertEqual(result.count(b'\r\n'), 2)
        self.assertEqual(redact(result, 'fixture.ini'), (result, []))

    def test_connection_string_preserves_cp949_crlf_and_identifiers(self):
        source = '\' 한글 주석\r\nconn.Open "Provider=SQLOLEDB;Server=192.0.2.1;UID=fixture_user;PWD=fixture_secret;Database=fixture_db"\r\n'.encode('cp949')
        result, rows = redact(source, 'function/dbcon.asp')
        self.assertEqual(source.count(b'\r\n'), result.count(b'\r\n'))
        self.assertTrue(result.startswith("' 한글 주석\r\n".encode('cp949')))
        for value in (b'192.0.2.1', b'fixture_user', b'fixture_secret', b'fixture_db'):
            self.assertNotIn(value, result)
        self.assertIn(b'Provider=SQLOLEDB', result)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(set(row) == {'path', 'start', 'end', 'kind', 'line'} for row in rows))
        self.assertTrue(all(row['line'] == 2 for row in rows))

    def test_literal_settings_and_cdo(self):
        source = b'DB_Pwd = "fixture_secret"\r\nDB_Id = "fixture_user"\r\nDB_IP = "192.0.2.1"\r\n.Fields("http://schemas.microsoft.com/cdo/configuration/sendpassword") = "fixture_mail_secret"\r\n'
        result, rows = redact(source, 'function/dbcon.asp')
        self.assertEqual(len(rows), 4)
        self.assertNotIn(b'fixture_', result)
        self.assertEqual(redact(result, 'function/dbcon.asp'), (result, []))

    def test_request_variables_column_names_and_generic_settings_untouched(self):
        source = b'pwd = Request("password")\r\nuser = rs("password")\r\nsql = "select password from member where uid=" & user\r\npassword_field = "password"\r\ntype = "password"\r\napi_key = "your-api-key"\r\nconn.Open "Provider=SQLOLEDB;Server=" & dbhost & ";PWD=" & dbpwd\r\n'
        self.assertEqual(redact(source, 'old/member/example.asp'), (source, []))

    def test_xml_element_connection_string(self):
        source = b'<connection>Provider=SQLOLEDB;Data Source=192.0.2.1;User ID=fixture_user;Password=fixture_secret;</connection>\r\n'
        result, rows = redact(source, 'function/Path.xml')
        self.assertEqual(len(rows), 3)
        self.assertNotIn(b'fixture_', result)

    def test_offsets_are_original_and_include_commented_credentials(self):
        source = b"' conn.Open \"DSN=fixture_dsn;UID=fixture_user;PWD=fixture_secret\"\r\n"
        result, rows = redact(source, 'old/function/dbcon.asp')
        self.assertEqual(len(rows), 3)
        self.assertEqual([source[r['start']:r['end']] for r in rows], [b'fixture_dsn', b'fixture_user', b'fixture_secret'])
        self.assertEqual(redact(result, 'old/function/dbcon.asp'), (result, []))

    def test_multiline_private_key_preserves_line_endings(self):
        source = b'-----BEGIN PRIVATE KEY-----\r\nZml4dHVyZQ==\r\n-----END PRIVATE KEY-----\r\n'
        result, rows = redact(source, 'fixture.pem')
        self.assertEqual(len(rows), 1)
        self.assertEqual(source.count(b'\r\n'), result.count(b'\r\n'))
        self.assertNotIn(b'PRIVATE KEY', result)

    def test_xml_password_and_short_default_are_real_configuration(self):
        source = b'<Dbconfig><UserID>fixture_user</UserID><Password>test</Password></Dbconfig>\r\n'
        result, rows = redact(source, 'old/With_Dbcon.xml')
        # The outer XML element does not consume nested credential elements.
        self.assertEqual(len(rows), 2)
        self.assertNotIn(b'>test<', result)
        self.assertNotIn(b'fixture_user', result)

    def test_unquoted_configuration_and_readme_label(self):
        for source, path in [(b'DB_PWD=test\r\n', 'fixture.env'), (b'Password: example\r\n', 'README.txt')]:
            result, rows = redact(source, path)
            self.assertEqual(len(rows), 1)
            self.assertNotEqual(source, result)

    def test_positional_open_with_semicolon_and_dynamic_source(self):
        source = b'conn.Open dsnVariable, "fixture_user", "fixture_secret";\r\n'
        result, rows = redact(source, 'old/function/dbcon.asp')
        self.assertEqual(len(rows), 2)
        self.assertIn(b'dsnVariable', result)
        self.assertNotIn(b'fixture_', result)

    def test_connection_id_alias_and_application_settings(self):
        source = b'conn.Open "Driver={SQL Server};Server=192.0.2.1;ID=fixture_user;PWD=test"\r\n'
        result, rows = redact(source, 'old/function/b_include/_dbopen.asp')
        self.assertEqual(len(rows), 3)
        self.assertNotIn(b'fixture_user', result)
        source = b'<add key="Password" value="example" />\r\n'
        result, rows = redact(source, 'web.config')
        self.assertEqual(len(rows), 1)
        self.assertNotIn(b'value="example"', result)

    def test_dynamic_vb_connection_fragments_are_never_literal_values(self):
        source = b'conn.Open "Provider=SQLOLEDB;PWD=" & passwordVariable & ";UID=" & userVariable & ";Database=" & databaseVariable\r\n'
        self.assertEqual(redact(source, 'old/function/b_include/_dbopen.asp'), (source, []))

    def test_database_host_reused_in_comment_and_alias_variable(self):
        source = b'Set conn = Server.CreateObject("ADODB.Connection")\r\nDB_Srv = "192.0.2.1,1433" \' previous 192.0.2.2\r\n'
        result, rows = redact(source, 'old/unse/example.asp')
        self.assertEqual(len(rows), 2)
        self.assertNotIn(b'192.0.2.', result)
        self.assertIn(b',1433', result)

    def test_inner_single_quoted_connection_credentials(self):
        source = b'conn.Open "Provider=SQLOLEDB;Data Source=192.0.2.1;UserID=\'fixture_user\';Password=\'fixture_secret\';Database=fixture_db"\r\n'
        result, rows = redact(source, 'old/inc_common/DBConnection.asp')
        self.assertEqual(len(rows), 4)
        self.assertNotIn(b'fixture_', result)
        self.assertIn(b"UserID='REDACTED_DATABASE_USERNAME'", result)
        self.assertIn(b"Password='REDACTED_DATABASE_PASSWORD'", result)

    def test_hostname_alias_resolved_from_connection_string(self):
        source = b'LocationAlias = "fixture-db.invalid"\r\nconn.Open "Provider=SQLOLEDB;Data Source=" & LocationAlias & ";UID=" & userVariable\r\n'
        result, rows = redact(source, 'function/dbcon.asp')
        self.assertEqual(len(rows), 1)
        self.assertNotIn(b'fixture-db.invalid', result)
        self.assertIn(b'& LocationAlias &', result)


if __name__ == '__main__':
    unittest.main()
