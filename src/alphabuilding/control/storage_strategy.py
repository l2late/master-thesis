"""
Optuna storage configuration factory.

Abstracts away the storage backend choice (SQLite, Journal, MySQL) so the
MPC hyperparameter optimization pipeline can switch backends without
modifying any orchestration logic.

For Vast.ai remote deployment, use ``StorageType.JOURNAL`` — it is append-only,
crash-safe, and avoids the NFS file-locking issues that plague SQLite when
multiple workers write concurrently.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class StorageType(Enum):
    """Supported Optuna storage backends."""

    SQLITE = "sqlite"
    JOURNAL = "journal"
    MYSQL = "mysql"


@dataclass(frozen=True)
class StorageConfig:
    """
    Configuration for an Optuna storage backend.

    Attributes:
        storage_type: Which backend to use.
        path: File path for SQLite or Journal storage.
        host: MySQL host (only needed for MYSQL type).
        port: MySQL port (default 3306).
        user: MySQL username.
        password: MySQL password.
        database: MySQL database name.
    """

    storage_type: StorageType = StorageType.JOURNAL
    path: Path | None = None
    # MySQL-specific
    host: str | None = None
    port: int = 3306
    user: str | None = None
    password: str | None = None
    database: str | None = None


def create_storage(config: StorageConfig) -> str | Any:
    """
    Create an Optuna storage backend based on configuration.

    Returns either:
    - A URL string (``sqlite:///...`` or ``mysql+pymysql://...``) for use with
      :class:`optuna.storages.RDBStorage`.
    - A :class:`optuna.storages.JournalStorage` instance for the journal backend.

    Args:
        config: Storage configuration.

    Returns:
        Storage backend (URL string) or JournalStorage instance.
    """
    if config.storage_type == StorageType.SQLITE:
        p = config.path or Path("optuna_mpc.db")
        return f"sqlite:///{p}"

    elif config.storage_type == StorageType.JOURNAL:
        from optuna.storages import JournalFileStorage, JournalStorage

        p = config.path or Path("optuna_mpc_journal.log")
        return JournalStorage(JournalFileStorage(str(p)))

    elif config.storage_type == StorageType.MYSQL:
        missing = [
            k
            for k, v in {
                "host": config.host,
                "user": config.user,
                "password": config.password,
                "database": config.database,
            }.items()
            if v is None
        ]
        if missing:
            raise ValueError(
                f"MySQL storage requires {', '.join(missing)} but "
                f"{'is' if len(missing) == 1 else 'are'} not set"
            )
        return (
            f"mysql+pymysql://{config.user}:{config.password}"
            f"@{config.host}:{config.port}/{config.database}"
        )

    else:  # pragma: no cover — defensive guard
        raise ValueError(f"Unknown storage type: {config.storage_type}")
