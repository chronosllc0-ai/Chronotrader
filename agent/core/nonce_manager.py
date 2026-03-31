# agent/core/nonce_manager.py

import threading
from web3 import Web3

class NonceManager:
    """Thread-safe nonce manager that avoids relying on pending tx count."""
    
    def __init__(self, w3: Web3, address: str):
        self.w3 = w3
        self.address = address
        self._lock = threading.Lock()
        self._nonce: int | None = None
    
    def initialize(self) -> int:
        """Sync nonce from chain. Call once at loop start."""
        with self._lock:
            self._nonce = self.w3.eth.get_transaction_count(self.address, "latest")
            assert self._nonce is not None
            return self._nonce
    
    def get_and_increment(self) -> int:
        """Get current nonce and increment for next tx. Thread-safe."""
        with self._lock:
            if self._nonce is None:
                self._nonce = self.initialize()
            assert self._nonce is not None
            nonce = self._nonce
            self._nonce += 1
            return nonce
    
    def reset_from_chain(self):
        """Re-sync from chain after a failed tx or nonce conflict."""
        with self._lock:
            confirmed = self.w3.eth.get_transaction_count(self.address, "latest")
            self._nonce = confirmed
            return self._nonce
