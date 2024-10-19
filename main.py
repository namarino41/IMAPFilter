import os

from pathlib import Path
from providers.imap_provider import ImapProvider
from concurrent.futures import ThreadPoolExecutor


ACCOUNTS_DIR = 'config/accounts'

accounts = Path(ACCOUNTS_DIR)

for account in accounts.iterdir():
    imap_provider = ImapProvider.create_imap_providers(account)
    ThreadPoolExecutor(max_workers=1).submit(imap_provider.listen)

