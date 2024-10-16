import os

from pathlib import Path
from providers.imap_provider import ImapProvider

ACCOUNTS_DIR = 'config/accounts'

accounts = Path(ACCOUNTS_DIR)
# imap_providers = ImapProvider.create_imap_providers(accounts)

for account in accounts.iterdir():
    imap_provider = ImapProvider.create_imap_providers(account)
    imap_provider.listen()