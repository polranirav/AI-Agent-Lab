"""Feature flag tests — per-tenant toggle behavior."""

from feature_flags.service import is_feature_enabled, set_feature_flag

DEMO_TENANT = "11111111-1111-1111-1111-111111111111"
OTHER_TENANT = "99999999-9999-9999-9999-999999999999"


def test_flag_defaults_to_off():
    set_feature_flag(DEMO_TENANT, "test_flag_off", False)
    assert is_feature_enabled(DEMO_TENANT, "test_flag_off") is False


def test_flag_can_be_enabled():
    set_feature_flag(DEMO_TENANT, "use_premium_model", True)
    assert is_feature_enabled(DEMO_TENANT, "use_premium_model") is True


def test_unknown_flag_is_off():
    assert is_feature_enabled(DEMO_TENANT, "never_created_flag") is False


def test_flags_are_per_tenant():
    # Enabling a flag for one tenant must not enable it for another.
    set_feature_flag(DEMO_TENANT, "isolated_flag", True)
    assert is_feature_enabled(DEMO_TENANT, "isolated_flag") is True
    assert is_feature_enabled(OTHER_TENANT, "isolated_flag") is False
