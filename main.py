from providers.imap_provider import GmailIMAPProvider as gmail

imapProvider = gmail("config/credentials.yaml")
imapProvider.watch_folder(gmail.CommonFolders.ALL.value)
imapProvider.load_filters("config/filter.yaml")
imapProvider.listen(polling_rate=10)
print("DONE")
