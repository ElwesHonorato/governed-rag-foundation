"""Contracts package for worker_scan."""

from contracts.scan_worker_contracts import (
    ScanJobConfigContract,
    ScanQueueConfigContract,
    ScanWorkerConfigContract,
)

__all__ = ["ScanJobConfigContract", "ScanQueueConfigContract", "ScanWorkerConfigContract"]
