import os

from pathlib import Path
from providers.imap_provider import ImapProvider

ACCOUNTS_DIR = 'config/accounts'

accounts = Path('ACCOUNTS_DIR')
imap_providers = ImapProvider.create_imap_providers(accounts)

for imap_provider in imap_providers:
    imap_provider.listen()