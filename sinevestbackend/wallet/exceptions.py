class InsufficientFundsError(Exception):
    """
    Raised by wallet/services.py when a debit, lock, or unlock operation
    would move a wallet's available_balance or locked_balance negative.
    """