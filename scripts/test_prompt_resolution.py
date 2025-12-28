import sys
from pathlib import Path

# Add plugin root to sys.path
plugin_root = Path(__file__).resolve().parent.parent
sys.path.append(str(plugin_root))

from backend.utils.settings import resolve_system_prompt

def test_resolve_system_prompt():
    defaults = {
        "system_prompt": "Global Default",
        "defaults": {
            "system_prompt_chat": "Chat Default",
            "system_prompt_plan": "Plan Default",
            "system_prompt_edit": "Edit Default"
        }
    }
    
    # Case 1: Both exist
    settings = {
        "system_prompt": "Global User",
        "defaults": {
            "system_prompt_chat": "Chat User"
        }
    }
    resolved = resolve_system_prompt("chat", defaults, settings)
    print(f"Case 1 (Both exist):\n{resolved!r}\n")
    assert "Global Default" in resolved
    assert "Global User" in resolved
    assert "Chat Default" in resolved
    assert "Chat User" in resolved

    # Case 2: Only defaults
    settings = {}
    resolved = resolve_system_prompt("plan", defaults, settings)
    print(f"Case 2 (Only defaults):\n{resolved!r}\n")
    assert resolved == "Global Default\n\nPlan Default"

    # Case 3: Only settings (unlikely but handled)
    defaults_empty = {}
    settings = {
        "system_prompt": "Global User",
        "defaults": {
            "system_prompt_edit": "Edit User"
        }
    }
    resolved = resolve_system_prompt("edit", defaults_empty, settings)
    print(f"Case 3 (Only settings):\n{resolved!r}\n")
    assert resolved == "Global User\n\nEdit User"

    # Case 4: Whitespace only in settings
    settings = {
        "system_prompt": "  ",
        "defaults": {
            "system_prompt_chat": "\n"
        }
    }
    resolved = resolve_system_prompt("chat", defaults, settings)
    print(f"Case 4 (Whitespace only):\n{resolved!r}\n")
    assert resolved == "Global Default\n\nChat Default"

    # Case 5: Both missing
    resolved = resolve_system_prompt("unknown", {}, {})
    print(f"Case 5 (Both missing):\n{resolved!r}\n")
    assert resolved == ""

    print("All tests passed!")

if __name__ == "__main__":
    try:
        test_resolve_system_prompt()
    except AssertionError as e:
        print(f"Test failed!")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
