
"""
Global utilities for managing application-wide state and configuration.
"""

import threading
from typing import Optional, Dict, Any

class GlobalState:
    """Thread-safe global state manager for application-wide configuration."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = {
            'LANGUAGE': 'en',  # Default language
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a global state value."""
        with self._lock:
            return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a global state value."""
        with self._lock:
            self._state[key] = value
    
    def get_language(self) -> str:
        """Get the current language setting."""
        return self.get('LANGUAGE', 'en')
    
    def set_language(self, language: str) -> None:
        """Set the current language setting."""
        self.set('LANGUAGE', language)
    
    def update(self, **kwargs) -> None:
        """Update multiple state values at once."""
        with self._lock:
            self._state.update(kwargs)
    
    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all global state."""
        with self._lock:
            return self._state.copy()

# Global instance
_global_state = GlobalState()

# Convenience functions for external access
def get_global(key: str, default: Any = None) -> Any:
    """Get a global state value."""
    return _global_state.get(key, default)

def set_global(key: str, value: Any) -> None:
    """Set a global state value."""
    _global_state.set(key, value)

def get_language() -> str:
    """Get the current language setting."""
    language = _global_state.get_language()
    if not language:
        language = 'en'
    return language

def set_language(language: str) -> None:
    """Set the current language setting."""
    _global_state.set_language(language)

def update_globals(**kwargs) -> None:
    """Update multiple global values at once."""
    _global_state.update(**kwargs)

def get_all_globals() -> Dict[str, Any]:
    """Get a copy of all global state."""
    return _global_state.get_all()
