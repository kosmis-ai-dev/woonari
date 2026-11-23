"""Meaningful boundary checks for T-013 / CR-006; no real AWS calls."""

from __future__ import annotations

import copy
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import aws_cli_entry
import isolated_aws as aws
from project_context import DEFAULTS


class AwsIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.aws_dir = self.state / "aws"
        self.aws_dir.mkdir()
        self.config = copy.deepcopy(DEFAULTS)
        self.config["aws"]["account_id"] = "123456789012"
        self.addCleanup(patch.stopall)
        patch.object(aws, "STATE", self.state).start()

    def write_profile(self, content=None):
        if content is None:
            content = (
                "[profile woonari]\nsso_session = woonari\nsso_account_id = 123456789012\n"
                "sso_role_name = developer\n[sso-session woonari]\n"
                "sso_start_url = https://example.awsapps.com/start\nsso_region = ap-northeast-2\n"
            )
        (self.aws_dir / "config").write_text(content)

    def test_external_credentials_and_endpoint_environment_are_removed(self):
        external = {
            "AWS_ACCESS_KEY_ID": "external-marker", "AWS_SECRET_ACCESS_KEY": "external-marker",
            "AWS_SESSION_TOKEN": "external-marker", "AWS_ROLE_ARN": "external-marker",
            "AWS_WEB_IDENTITY_TOKEN_FILE": "/other-project/token", "AWS_PROFILE": "external",
            "AWS_CONFIG_FILE": "/other-project/config", "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI": "/token",
            "AWS_ENDPOINT_URL": "https://example.invalid", "AWS_DATA_PATH": "/other-project/models",
            "BOTO_CONFIG": "/other-project/boto", "GH_TOKEN": "external-marker",
        }
        with patch.dict(os.environ, external):
            environment = aws.aws_environment(self.config)
        self.assertNotIn("external-marker", environment.values())
        self.assertNotIn("AWS_ACCESS_KEY_ID", environment)
        self.assertNotIn("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", environment)
        self.assertNotIn("AWS_WEB_IDENTITY_TOKEN_FILE", environment)
        self.assertNotIn("AWS_ENDPOINT_URL", environment)
        self.assertNotIn("AWS_DATA_PATH", environment)
        self.assertNotIn("GH_TOKEN", environment)
        self.assertEqual(environment["AWS_PROFILE"], "woonari")
        self.assertEqual(environment["AWS_CONFIG_FILE"], str(self.aws_dir / "config"))
        self.assertEqual(environment["AWS_EC2_METADATA_DISABLED"], "true")
        self.assertEqual(environment["BOTO_CONFIG"], os.devnull)

    def test_unknown_new_account_cannot_run_any_service(self):
        self.config["aws"]["account_id"] = ""
        with patch.object(aws, "load_config", return_value=self.config), \
                patch.object(aws, "private_dir"), patch.object(aws.subprocess, "run") as run, \
                self.assertRaisesRegex(RuntimeError, "new AWS account ID"):
            aws.main(["s3", "ls"])
        run.assert_not_called()

    def test_wrong_sso_account_is_rejected_before_login(self):
        self.write_profile("[profile woonari]\nsso_account_id = 999999999999\n")
        with patch.object(aws, "load_config", return_value=self.config), \
                patch.object(aws, "private_dir"), patch.object(aws.subprocess, "run") as run, \
                self.assertRaisesRegex(RuntimeError, "different account"):
            aws.main(["sso", "login"])
        run.assert_not_called()

    def test_external_providers_and_role_chains_are_rejected(self):
        for setting in ("credential_source = Ec2InstanceMetadata", "source_profile = external",
                        "credential_process = external-helper", "role_arn = external-role",
                        "web_identity_token_file = /other/token", "endpoint_url = https://example.invalid"):
            with self.subTest(setting=setting):
                self.write_profile("[profile woonari]\n" + setting + "\n")
                with self.assertRaisesRegex(RuntimeError, "External AWS"):
                    aws.validate_profile(self.config)

    def test_other_profiles_and_defaults_are_rejected(self):
        for section in ("[default]\nregion = us-east-1\n", "[profile unrelated]\nregion = us-east-1\n",
                        "[DEFAULT]\nregion = us-east-1\n"):
            self.write_profile(section)
            with self.assertRaises(RuntimeError):
                aws.validate_profile(self.config)

    def test_profile_symlink_is_rejected(self):
        outside = self.state / "outside-config"
        outside.write_text("[profile woonari]\nsso_account_id = 123456789012\n")
        (self.aws_dir / "config").symlink_to(outside)
        with self.assertRaisesRegex(RuntimeError, "symlinks"):
            aws.validate_profile(self.config)

    def test_override_and_abbreviated_override_arguments_are_rejected(self):
        for option in ("--profile", "--profile=other", "--pro", "--endpoint-url=https://example.invalid",
                       "--end", "--no-sign-request", "--no-sign", "--debug", "--cli-input-json"):
            with self.subTest(option=option), self.assertRaisesRegex(RuntimeError, "overrides"):
                aws.validate_arguments(["s3", "ls", option])

    def test_logout_and_credential_switching_are_rejected(self):
        for command in (["sso", "logout"], ["logout"], ["login"],
                        ["configure", "set", "credential_process", "anything"],
                        ["sts", "assume-role", "--role-arn", "other"], ["sso-oidc", "create-token"]):
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                aws.validate_arguments(command)

    def test_codeartifact_login_cannot_modify_shared_package_manager_config(self):
        for command in (["codeartifact", "login", "--tool", "pip"],
                        ["codeartifact", "--region", "ap-northeast-2", "login", "--tool", "npm"]):
            with self.subTest(command=command), patch.object(aws.subprocess, "run") as run, \
                    self.assertRaisesRegex(RuntimeError, "shared pip/npm"):
                aws.main(command)
            run.assert_not_called()

    def test_eks_update_kubeconfig_cannot_modify_shared_kubernetes_config(self):
        for command in (["eks", "update-kubeconfig", "--name", "project-cluster"],
                        ["eks", "--region", "ap-northeast-2", "update-kubeconfig", "--name", "cluster"]):
            with self.subTest(command=command), patch.object(aws.subprocess, "run") as run, \
                    self.assertRaisesRegex(RuntimeError, "kubeconfig"):
                aws.main(command)
            run.assert_not_called()

    def test_high_level_role_arn_switch_and_abbreviation_are_rejected(self):
        for option in ("--role-arn", "--role-arn=project-role", "--role-ar"):
            with self.subTest(option=option), patch.object(aws.subprocess, "run") as run, \
                    self.assertRaisesRegex(RuntimeError, "overrides"):
                aws.main(["cloudformation", "deploy", option])
            run.assert_not_called()

    def test_high_level_assume_role_arn_switch_and_abbreviation_are_rejected(self):
        for option in ("--assume-role-arn", "--assume-role-arn=project-role", "--assume-role-ar"):
            with self.subTest(option=option), patch.object(aws.subprocess, "run") as run, \
                    self.assertRaisesRegex(RuntimeError, "overrides"):
                aws.main(["eks", "get-token", option])
            run.assert_not_called()

    def test_matching_profile_is_accepted(self):
        self.write_profile()
        aws.validate_profile(self.config)

    def test_enabled_history_blocks_secret_retrieval(self):
        self.write_profile("[profile woonari]\ncli_history = enabled\n")
        with patch.object(aws, "load_config", return_value=self.config), \
                patch.object(aws, "private_dir"), patch.object(aws.subprocess, "run") as run, \
                self.assertRaisesRegex(RuntimeError, "history must be disabled"):
            aws.main(["secretsmanager", "get-secret-value", "--secret-id", "inter"])
        run.assert_not_called()

    def test_enabled_history_blocks_bedrock_prompts_and_responses(self):
        self.write_profile("[profile woonari]\ncli_history = enabled\n")
        with patch.object(aws, "load_config", return_value=self.config), \
                patch.object(aws, "private_dir"), patch.object(aws.subprocess, "run") as run, \
                self.assertRaisesRegex(RuntimeError, "history must be disabled"):
            aws.main(["bedrock-runtime", "converse", "--model-id", "fixture-model"])
        run.assert_not_called()

    def test_static_credentials_may_only_come_from_private_profile(self):
        (self.aws_dir / "credentials").write_text(
            "[woonari]\naws_access_key_id = project-marker\naws_secret_access_key = project-marker\n"
        )
        aws.validate_profile(self.config)

    def test_sts_mismatch_never_runs_requested_command(self):
        self.write_profile()
        with patch.object(aws, "load_config", return_value=self.config), \
                patch.object(aws, "private_dir"), patch.object(aws, "cli_prefix", return_value=["bootstrap"]), \
                patch.object(aws.subprocess, "run", return_value=SimpleNamespace(
                    returncode=0, stdout='{"Account":"999999999999"}'
                )) as run, self.assertRaisesRegex(RuntimeError, "account mismatch"):
            aws.main(["ec2", "describe-instances"])
        self.assertEqual(run.call_count, 1)
        self.assertIn("get-caller-identity", run.call_args.args[0])

    def test_sts_failure_never_runs_requested_command(self):
        self.write_profile()
        with patch.object(aws, "load_config", return_value=self.config), \
                patch.object(aws, "private_dir"), patch.object(aws, "cli_prefix", return_value=["bootstrap"]), \
                patch.object(aws.subprocess, "run", return_value=SimpleNamespace(returncode=1)) as run, \
                self.assertRaisesRegex(RuntimeError, "authentication failed"):
            aws.main(["s3", "ls"])
        self.assertEqual(run.call_count, 1)

    def test_matching_sts_identity_allows_command_with_same_isolated_environment(self):
        self.write_profile()
        with patch.object(aws, "load_config", return_value=self.config), \
                patch.object(aws, "private_dir"), patch.object(aws, "cli_prefix", return_value=["bootstrap"]), \
                patch.object(aws.subprocess, "run", side_effect=[
                    SimpleNamespace(returncode=0, stdout='{"Account":"123456789012"}'),
                    SimpleNamespace(returncode=0),
                ]) as run:
            self.assertEqual(aws.main(["s3", "ls"]), 0)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].kwargs["env"], run.call_args_list[1].kwargs["env"])
        self.assertEqual(run.call_args_list[1].args[0], ["bootstrap", "s3", "ls"])

    def test_unsupported_cli_layout_fails_closed(self):
        binary = self.state / "aws-binary"
        binary.write_bytes(b"compiled binary, no Python shebang")
        with patch.object(aws.shutil, "which", return_value=str(binary)), \
                self.assertRaisesRegex(RuntimeError, "cannot isolate SSO caches"):
            aws.cli_prefix({"PATH": "/irrelevant"})

    def test_cache_redirect_preserves_home_and_unrelated_paths(self):
        original = os.path.expanduser
        try:
            aws_cli_entry.install_path_redirect(self.aws_dir)
            self.assertEqual(os.path.expanduser("~/.aws/sso/cache"), str(self.aws_dir / "sso/cache"))
            self.assertEqual(os.path.expanduser(b"~/.aws/cli/cache"), os.fsencode(self.aws_dir / "cli/cache"))
            self.assertEqual(os.path.expanduser("~/.aws-other"), original("~/.aws-other"))
            self.assertEqual(os.path.expanduser("~/documents"), original("~/documents"))
            self.assertEqual(os.path.expanduser("~"), original("~"))
        finally:
            os.path.expanduser = original


if __name__ == "__main__":
    unittest.main()
