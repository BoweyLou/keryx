from knowledge_gateway.policies import WriteClass, WritePolicyError, WritePolicyManager
from knowledge_gateway.writing import apply_managed_section_patch


def test_write_policy_blocks_class_c_by_default() -> None:
    manager = WritePolicyManager(allow_class_c=False, allowed_targets=["02 Projects", "07 Tasks"])

    try:
        manager.assert_allowed(write_class=WriteClass.CLASS_C, note_path="02 Projects/Hermes/Overview.md")
    except WritePolicyError as exc:
        assert "disabled by default" in str(exc)
    else:
        raise AssertionError("expected write policy failure")


def test_managed_section_patch_updates_only_target_region() -> None:
    original = """
    # Overview

    ## Summary
    <!-- AGENT:BEGIN summary -->
    old summary
    <!-- AGENT:END summary -->

    ## Human Notes
    Keep this text intact.
    """

    updated = apply_managed_section_patch(original, section="summary", replacement="new summary")

    assert "new summary" in updated
    assert "Keep this text intact." in updated
    assert "old summary" not in updated

