"""
Tests for oxutils.s3 module.
"""
import pytest
from unittest.mock import patch


# ── get_s3_storage_backend ────────────────────────────────────────

class TestGetS3StorageBackend:
    """Tests for get_s3_storage_backend()."""

    # ── S3 not enabled ────────────────────────────────────────────

    @patch("oxutils.s3.os.getenv")
    def test_returns_none_when_use_s3_false(self, mock_getenv):
        from oxutils.s3 import get_s3_storage_backend

        mock_getenv.return_value = "False"

        result = get_s3_storage_backend("static")
        assert result is None
        mock_getenv.assert_called_with("OXI_STATIC_STORAGE_USE_S3", "False")

    @patch("oxutils.s3.os.getenv")
    def test_returns_none_when_use_s3_not_set(self, mock_getenv):
        from oxutils.s3 import get_s3_storage_backend

        mock_getenv.return_value = "False"

        result = get_s3_storage_backend("media")
        assert result is None
        mock_getenv.assert_called_with("OXI_MEDIA_STORAGE_USE_S3", "False")

    @patch("oxutils.s3.os.getenv")
    def test_returns_none_when_use_s3_zero(self, mock_getenv):
        from oxutils.s3 import get_s3_storage_backend

        mock_getenv.return_value = "0"

        result = get_s3_storage_backend("static")
        assert result is None

    @patch("oxutils.s3.os.getenv")
    def test_returns_none_when_use_s3_empty(self, mock_getenv):
        from oxutils.s3 import get_s3_storage_backend

        mock_getenv.return_value = ""

        result = get_s3_storage_backend("static")
        assert result is None

    # ── S3 enabled ────────────────────────────────────────────────

    def test_returns_backend_dict_when_enabled(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_ACCESS_KEY_ID", "my-access-key")
        monkeypatch.setenv("OXI_STATIC_STORAGE_SECRET_ACCESS_KEY", "my-secret-key")
        monkeypatch.setenv("OXI_STATIC_STORAGE_BUCKET_NAME", "my-bucket")
        monkeypatch.setenv("OXI_STATIC_STORAGE_ENDPOINT_URL", "https://s3.example.com")

        result = get_s3_storage_backend("static")

        assert result is not None
        assert result["BACKEND"] == "storages.backends.s3.S3Storage"
        assert result["OPTIONS"]["access_key"] == "my-access-key"
        assert result["OPTIONS"]["secret_key"] == "my-secret-key"
        assert result["OPTIONS"]["bucket_name"] == "my-bucket"
        assert result["OPTIONS"]["endpoint_url"] == "https://s3.example.com"

    def test_use_s3_true_variants(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        for value in ("true", "True", "TRUE", "1", "yes", "Yes", "YES"):
            monkeypatch.setenv("OXI_MEDIA_STORAGE_USE_S3", value)
            result = get_s3_storage_backend("media")
            assert result is not None, f"Failed for value: {value}"
            assert result["BACKEND"] == "storages.backends.s3.S3Storage"

    def test_ignores_unset_env_vars(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_ACCESS_KEY_ID", "key")
        # All other vars intentionally left unset

        result = get_s3_storage_backend("static")
        assert result is not None
        assert result["OPTIONS"]["access_key"] == "key"
        assert "secret_key" not in result["OPTIONS"]  # Not set → omitted
        assert "bucket_name" not in result["OPTIONS"]

    # ── Boolean conversion ────────────────────────────────────────

    def test_converts_boolean_values(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_SSL", "false")
        monkeypatch.setenv("OXI_STATIC_STORAGE_GZIP", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_FILE_OVERWRITE", "False")
        monkeypatch.setenv("OXI_STATIC_STORAGE_QUERYSTRING_AUTH", "True")

        result = get_s3_storage_backend("static")
        opts = result["OPTIONS"]

        assert opts["use_ssl"] is False
        assert opts["gzip"] is True
        assert opts["file_overwrite"] is False
        assert opts["querystring_auth"] is True

    # ── Integer conversion ────────────────────────────────────────

    def test_converts_integer_values(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_QUERYSTRING_EXPIRE", "3600")
        monkeypatch.setenv("OXI_STATIC_STORAGE_MAX_MEMORY_SIZE", "1048576")

        result = get_s3_storage_backend("static")
        opts = result["OPTIONS"]

        assert opts["querystring_expire"] == 3600
        assert opts["max_memory_size"] == 1048576

    # ── Quote stripping ───────────────────────────────────────────

    def test_strips_quotes_from_values(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_ACCESS_KEY_ID", '"quoted-key"')
        monkeypatch.setenv("OXI_STATIC_STORAGE_BUCKET_NAME", "'my-bucket'")

        result = get_s3_storage_backend("static")
        opts = result["OPTIONS"]

        assert opts["access_key"] == "quoted-key"
        assert opts["bucket_name"] == "my-bucket"

    # ── Empty values skipped ──────────────────────────────────────

    def test_skips_empty_values_after_trimming(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_ACCESS_KEY_ID", "key123")
        monkeypatch.setenv("OXI_STATIC_STORAGE_BUCKET_NAME", '""')
        monkeypatch.setenv("OXI_STATIC_STORAGE_LOCATION", "''")

        result = get_s3_storage_backend("static")
        opts = result["OPTIONS"]

        assert opts["access_key"] == "key123"
        assert "bucket_name" not in opts  # Stripped to empty → skipped
        assert "location" not in opts      # Stripped to empty → skipped

    # ── kwargs override ───────────────────────────────────────────

    def test_kwargs_override_env_vars(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_STATIC_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_STATIC_STORAGE_BUCKET_NAME", "env-bucket")
        monkeypatch.setenv("OXI_STATIC_STORAGE_REGION_NAME", "env-region")

        result = get_s3_storage_backend(
            "static",
            bucket_name="override-bucket",
            custom_domain="cdn.example.com",
        )
        opts = result["OPTIONS"]

        assert opts["bucket_name"] == "override-bucket"  # kwargs wins
        assert opts["region_name"] == "env-region"        # env still there
        assert opts["custom_domain"] == "cdn.example.com"  # new from kwargs

    # ── All env vars ──────────────────────────────────────────────

    def test_reads_all_supported_env_vars(self, monkeypatch):
        from oxutils.s3 import get_s3_storage_backend

        monkeypatch.setenv("OXI_DATA_STORAGE_USE_S3", "true")
        monkeypatch.setenv("OXI_DATA_STORAGE_ACCESS_KEY_ID", "ak")
        monkeypatch.setenv("OXI_DATA_STORAGE_SECRET_ACCESS_KEY", "sk")
        monkeypatch.setenv("OXI_DATA_STORAGE_BUCKET_NAME", "bn")
        monkeypatch.setenv("OXI_DATA_STORAGE_ENDPOINT_URL", "eu")
        monkeypatch.setenv("OXI_DATA_STORAGE_REGION_NAME", "rn")
        monkeypatch.setenv("OXI_DATA_STORAGE_DEFAULT_ACL", "acl")
        monkeypatch.setenv("OXI_DATA_STORAGE_LOCATION", "loc")
        monkeypatch.setenv("OXI_DATA_STORAGE_CUSTOM_DOMAIN", "cd")
        monkeypatch.setenv("OXI_DATA_STORAGE_SIGNATURE_VERSION", "sv")
        monkeypatch.setenv("OXI_DATA_STORAGE_ADDRESSING_STYLE", "as")
        monkeypatch.setenv("OXI_DATA_STORAGE_USE_SSL", "false")
        monkeypatch.setenv("OXI_DATA_STORAGE_VERIFY", "true")
        monkeypatch.setenv("OXI_DATA_STORAGE_QUERYSTRING_AUTH", "false")
        monkeypatch.setenv("OXI_DATA_STORAGE_QUERYSTRING_EXPIRE", "7200")
        monkeypatch.setenv("OXI_DATA_STORAGE_FILE_OVERWRITE", "true")
        monkeypatch.setenv("OXI_DATA_STORAGE_GZIP", "true")
        monkeypatch.setenv("OXI_DATA_STORAGE_URL_PROTOCOL", "https:")
        monkeypatch.setenv("OXI_DATA_STORAGE_SECURITY_TOKEN", "st")
        monkeypatch.setenv("OXI_DATA_STORAGE_SESSION_PROFILE", "sp")
        monkeypatch.setenv("OXI_DATA_STORAGE_OBJECT_PARAMETERS", "op")
        monkeypatch.setenv("OXI_DATA_STORAGE_MAX_MEMORY_SIZE", "4096")
        monkeypatch.setenv("OXI_DATA_STORAGE_GZIP_CONTENT_TYPES", "gct")
        monkeypatch.setenv("OXI_DATA_STORAGE_PROXIES", "pr")
        monkeypatch.setenv("OXI_DATA_STORAGE_CLOUDFRONT_KEY", "cfk")
        monkeypatch.setenv("OXI_DATA_STORAGE_CLOUDFRONT_KEY_ID", "cfki")
        monkeypatch.setenv("OXI_DATA_STORAGE_CLOUDFRONT_SIGNER", "cfs")
        monkeypatch.setenv("OXI_DATA_STORAGE_CLIENT_CONFIG", "cc")

        result = get_s3_storage_backend("data")
        opts = result["OPTIONS"]

        assert opts["access_key"] == "ak"
        assert opts["secret_key"] == "sk"
        assert opts["bucket_name"] == "bn"
        assert opts["endpoint_url"] == "eu"
        assert opts["region_name"] == "rn"
        assert opts["default_acl"] == "acl"
        assert opts["location"] == "loc"
        assert opts["custom_domain"] == "cd"
        assert opts["signature_version"] == "sv"
        assert opts["addressing_style"] == "as"
        assert opts["use_ssl"] is False
        assert opts["verify"] is True
        assert opts["querystring_auth"] is False
        assert opts["querystring_expire"] == 7200
        assert opts["file_overwrite"] is True
        assert opts["gzip"] is True
        assert opts["url_protocol"] == "https:"
        assert opts["security_token"] == "st"
        assert opts["session_profile"] == "sp"
        assert opts["object_parameters"] == "op"
        assert opts["max_memory_size"] == 4096
        assert opts["gzip_content_types"] == "gct"
        assert opts["proxies"] == "pr"
        assert opts["cloudfront_key"] == "cfk"
        assert opts["cloudfront_key_id"] == "cfki"
        assert opts["cloudfront_signer"] == "cfs"
        assert opts["client_config"] == "cc"


# ── get_s3_static_url ─────────────────────────────────────────────

class TestGetS3StaticUrl:
    """Tests for get_s3_static_url()."""

    def test_returns_none_when_options_is_none(self):
        from oxutils.s3 import get_s3_static_url

        result = get_s3_static_url(None)
        assert result is None

    def test_returns_none_when_no_custom_domain(self):
        from oxutils.s3 import get_s3_static_url

        options = {"OPTIONS": {}}
        result = get_s3_static_url(options)
        assert result is None

    def test_returns_none_when_custom_domain_is_none(self):
        from oxutils.s3 import get_s3_static_url

        options = {"OPTIONS": {"custom_domain": None}}
        result = get_s3_static_url(options)
        assert result is None

    def test_builds_url_with_custom_domain(self):
        from oxutils.s3 import get_s3_static_url

        options = {"OPTIONS": {"custom_domain": "cdn.example.com"}}
        result = get_s3_static_url(options)
        assert result == "https://cdn.example.com/"

    def test_uses_custom_protocol(self):
        from oxutils.s3 import get_s3_static_url

        options = {
            "OPTIONS": {
                "custom_domain": "cdn.example.com",
                "url_protocol": "http",
            }
        }
        result = get_s3_static_url(options)
        assert result == "http://cdn.example.com/"

    def test_appends_location(self):
        from oxutils.s3 import get_s3_static_url

        options = {
            "OPTIONS": {
                "custom_domain": "cdn.example.com",
                "location": "static",
            }
        }
        result = get_s3_static_url(options)
        assert result == "https://cdn.example.com/static/"

    def test_appends_location_with_trailing_slash(self):
        from oxutils.s3 import get_s3_static_url

        options = {
            "OPTIONS": {
                "custom_domain": "cdn.example.com",
                "location": "uploads/images",
            }
        }
        result = get_s3_static_url(options)
        assert result == "https://cdn.example.com/uploads/images/"

    def test_empty_location_does_not_append(self):
        from oxutils.s3 import get_s3_static_url

        options = {"OPTIONS": {"custom_domain": "cdn.example.com", "location": ""}}
        result = get_s3_static_url(options)
        assert result == "https://cdn.example.com/"

    def test_default_protocol_is_https(self):
        from oxutils.s3 import get_s3_static_url

        options = {"OPTIONS": {"custom_domain": "cdn.example.com"}}
        result = get_s3_static_url(options)
        assert result.startswith("https://")

    def test_options_without_options_key_does_not_crash(self):
        from oxutils.s3 import get_s3_static_url

        options = {}
        result = get_s3_static_url(options)
        assert result is None
