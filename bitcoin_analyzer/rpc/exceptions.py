class RPCError(Exception):
    """Base exception for RPC-related errors."""
    pass

class RPCConnectionError(RPCError):
    """Raised when connection to Bitcoin node fails."""
    pass

class RPCAuthenticationError(RPCError):
    """Raised when RPC authentication fails."""
    pass