import email
import re
import time
import os
import yaml
from abc import ABC, abstractmethod
from datetime import datetime
from filters.filteractions import FilterAction, FilterGroup
from imapclient import IMAPClient, exceptions
from typing import override

from config.logging_config import setup_logging
import logging

setup_logging()  # Set up the logging system
logger = logging.getLogger(__name__)  # Get the logger for this module

class ImapProvider(ABC):
    EMAIL_DATA_FORMAT = "RFC822"
    EMAIL_EXISTS = "EXISTS"
    MAX_CONNECTION_TIME = 1620

    def __init__(self, imap_server_url, auth, filter_group):
        logger.info(f"Initializing IMAP provider for folder: {filter_group.watching_folder}")

        self._server = IMAPClient(imap_server_url, use_uid=True)
        self._auth = auth
        self._filter_group = filter_group

        self.connect()
        self._watch_folder()

    @abstractmethod
    def connect(self):   
        raise NotImplementedError
        
    def get_email_data(self, emails):
        logger.info(f"Fetching data for {len(emails)} email(s).")
        email_data = {}
        matching_emails = self._server.search(emails)
        logger.debug(f"Matching emails found: {matching_emails}")
        for uid, message_data in self._server.fetch(matching_emails, \
                                                    self.EMAIL_DATA_FORMAT).items():
            email_data[uid] = email.message_from_bytes( \
                message_data[self.EMAIL_DATA_FORMAT.encode()])
            
        return email_data

    def _watch_folder(self):
        logger.info(f"Checking if folder '{self._filter_group.watching_folder}' is available.")
        available_folders = list(map(lambda response: response[2], \
            self._server.list_folders()))
        if self._filter_group.watching_folder in available_folders:
            self._server.select_folder(self._filter_group.watching_folder, readonly=True)
            logger.info("Watching folder {}".format(self._filter_group.watching_folder))
        else:
            logger.error("folder '{}' does not exist".format(self._filter_group.watching_folder))            
            raise Exception("folder '{}' does not exist in your Gmail account")        
        
    @abstractmethod
    def delete_emails(self, emails, permanently_delete):
        raise NotImplementedError

    @abstractmethod
    def listen(self):
        raise NotImplementedError
            
    @staticmethod
    def create_imap_providers(account):
        account_domain = account.name.split('@')[1]

        auth = os.path.join(account, "credentials.yaml")
        filters = os.path.join(account, "filter.yaml")

        filter_groups = FilterGroup.create_filter_groups(filters)
        for filter_group in filter_groups:
            match account_domain:
                case GmailIMAPProvider.GMAIL_DOMAIN:
                    return GmailIMAPProvider(auth, filter_group)
                

class GmailIMAPProvider(ImapProvider):
    GMAIL_DOMAIN = 'gmail.com'
    GMAIL_IMAP_SERVER_URL = 'imap.gmail.com'

    def __init__(self, auth, filter_group):
        logger.info(f"Gmail IMAP Provider initialized for folder: {filter_group.watching_folder}")
        super().__init__(self.GMAIL_IMAP_SERVER_URL, auth, filter_group)

        self._connect_time = 0

    @override
    def connect(self):
        logger.info("Connecting to Gmail IMAP server.")
        try:
            with open(self._auth, 'r') as file:
                credentials = yaml.safe_load(file)
                user = credentials['user']
                password = credentials['password']
                logger.info("Credentials loaded")
        except Exception as e:
            logger.error("Failed to load credentials: {}".format(e))
            raise

        try:
            success = self._server.login(user, password)
            logger.info(f"Authentication successful: {success}")
        except exceptions.IMAPClientError as e:
            logger.error("Authentication failed: {}".format(e))
            raise

    @override
    def delete_emails(self, emails: list, permanently_delete=False):
        if emails:
            logger.info("{} email selected for deletion from: {}".format(len(emails), \
                self._filter_group.watching_folder))
            self._server.select_folder(self._filter_group.watching_folder)   # Open folder for edits
            for email in emails:
                labels = self._server.get_gmail_labels(email)[email]
                self._server.remove_gmail_labels(email, labels)
                logger.info("{} labels removed from: {}".format(labels, email))
            self._server.delete_messages(emails)
            self._server.uid_expunge(emails)
            logger.info("Emails deleted: {}".format(emails))
        self._server.select_folder(self._filter_group.watching_folder, readonly=True)    # Close folder with "readonly" when finished

    @override
    def listen(self):
        logger.info(f"Started listening for new emails in folder: {self._filter_group.watching_folder}")
        while True:
            try:
                self._idle_connect()
                idle_response = self._server.idle_check()

                self._handle_response(idle_response)
            except (ConnectionResetError, BrokenPipeError, ConnectionError) as e:
                logger.error(f"A connection error has occurred: {e}")
                logger.info("Attempting to reconnect.")
                self.connect()
            # except Exception as e:
                # logger.error(f"An unexpected error has occurred: {e}")
                raise
                # self._server.logout()
                # break

    def _handle_response(self, idle_response):
        if idle_response:
            new_emails = list(map(lambda email: email[0], \
                list(filter(lambda response: self.EMAIL_EXISTS.encode() in response, idle_response))))
            if new_emails:
                logger.info("New emails received: {}".format(new_emails))
                self._idle_disconnect()
                logger.info("Applying filters")
                self._filter_group.apply_filters(new_emails, self)

    def _idle_connect(self):
        if self._connect_time == 0:
            self._server.idle()
        else:
            time_difference = datetime.now() - self._connect_time

            if time_difference >= self.MAX_CONNECTION_TIME:
                self._server.idle_done()
                self._server.idle()
                self._connect_time = datetime.now()

    def _idle_disconnect(self):
        self._server.idle_done()
        self._connect_time = 0

    # @override
    # def _idle_check(self):
    #     response = self._server.noop()
    #     if response[1]:
    #         return response[1]