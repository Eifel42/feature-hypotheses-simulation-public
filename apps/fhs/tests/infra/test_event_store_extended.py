# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
#
# Disclaimer: This software is provided "as is", without warranty of any kind,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and noninfringement.
# In no event shall the authors or copyright holders be liable for any claim,
# damages or other liability, whether in an action of contract, tort or
# otherwise, arising from, out of or in connection with the software or the
# use or other dealings in the software.

"""Extended tests for SqliteEventStore - covering __eq__ NotImplemented path."""

from fhs.infra.event_store import SqliteEventStore


def test_equality_with_different_type(tmp_path):
    """Test __eq__ returns NotImplemented for non-SqliteEventStore comparison."""
    store = SqliteEventStore(tmp_path / "e.db")
    # Comparing with a different type should return False (via NotImplemented)
    assert store != "not_a_store"
    assert store != 42
    assert store is not None
