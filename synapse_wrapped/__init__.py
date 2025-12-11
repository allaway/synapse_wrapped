"""
Synapse Wrapped - Generate Spotify Wrapped-style visualizations for Synapse.org users
"""

__version__ = "0.1.0"

from synapse_wrapped.generator import generate_wrapped, generate_wrapped_batch

__all__ = ["generate_wrapped", "generate_wrapped_batch"]

