"""SEO Opportunity Miner agent package.

This module re-exports the latest agent version for compatibility with older
import paths. New code should import specific versions explicitly.
"""

from .v1.agent import *  # noqa: F401,F403

__all__ = [name for name in globals() if not name.startswith("_")]
