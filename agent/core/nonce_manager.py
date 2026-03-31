"""Thread-safe nonce manager for transaction submission."""

from __future__ import annotations

import threading

from web3 import Web3


class NonceManager:
    """Thread-safe nonce manager for serialized transaction sends."""

    def __init__(self, w3: Web3, address: str):
        self.w3 = w3
        self.address = address
        self._lock = threading.Lock()
        self._nonce: int | None = None

    def initialize(self) -> int:
        with self._lock:
            self._nonce = self.w3.eth.get_transaction_count(self.address, "latest")
            return self._nonce

    def get_and_increment(self) -> int:
        with self._lock:
            if self._nonce is None:
                self._nonce = self.w3.eth.get_transaction_count(self.address, "latest")
            nonce = self._nonce
            self._nonce += 1
            return nonce

    def reset_from_chain(self) -> int:
        with self._lock:
            self._nonce = self.w3.eth.get_transaction_count(self.address, "latest")
            return self._nonce
