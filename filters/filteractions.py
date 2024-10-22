from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from providers.imap_provider import ImapProvider
from abc import ABC, abstractmethod
from filters.filteractions_criteria import FilterActionCriterion
from typing import override
import yaml

from config.logging_config import setup_logging
import logging

setup_logging()  # Set up the logging system

logger = logging.getLogger(__name__)  # Get the logger for this module

class FilterAction(ABC):
    @abstractmethod
    def apply(self, emails, imap_provider: ImapProvider):
        raise NotImplementedError
    
    @staticmethod
    def create_filter_actions(filters):
        logger.info("Creating filter actions.")
        filter_actions_list = []
        for filter in filters:
            for filter_action, values in filter.items():
                match filter_action:
                    case DeleteFilterAction.DELETE_FILTER_ACTION_TAG:
                        logger.info(f"Creating DeleteFilterAction for filter action: {filter_action}")
                        filter_actions_list.extend(list(map(lambda value: DeleteFilterAction(value), values)))

        logger.info(f"Filter actions created: {filter_actions_list}")
        return filter_actions_list
            
class DeleteFilterAction(FilterAction):
    DELETE_FILTER_ACTION_TAG = "delete"

    def __init__(self, filter_criteria):
        self.filter_criteria = \
            FilterActionCriterion.create_filter_criterion(filter_criteria)
        logger.info(f"DeleteFilterAction initialized with criteria: {self.filter_criteria}")


    def _check_criteria(self, email):
        logger.debug(f"Checking criteria for email: {email}")
        return all(criterion.check_condition(email) \
            for criterion in self.filter_criteria)
                
    @override
    def apply(self, emails, imap_provider: ImapProvider):  
        logger.info("Applying delete filter action.")      
        emails_to_delete = []
        email_data = imap_provider.get_email_data(emails)
        logger.info(f"Email data fetched: {email_data.keys()}")
        for uid, email in email_data.items():
            if self._check_criteria(email):
                logger.info(f"Email {uid} matches criteria for deletion.")
                emails_to_delete.append(uid)
        if emails_to_delete:
            logger.info(f"Deleting emails: {emails_to_delete}")
        imap_provider.delete_emails(emails_to_delete)


class FilterGroup:

    def __init__(self, watching_folder, filter_actions):
        self.watching_folder = watching_folder
        self.filter_actions = FilterAction.create_filter_actions(filter_actions)
        logger.info(f"FilterGroup initialized for folder: {watching_folder}")


    def apply_filters(self, emails, imap_provider: ImapProvider):
        logger.info(f"Applying filters to emails in folder: {self.watching_folder}")

        for filter_action in self.filter_actions:
            logger.debug(f"Applying filter action: {filter_action}")
            filter_action.apply(emails, imap_provider)

    @staticmethod
    def create_filter_groups(filters):
        try:
            with open(filters, 'r') as file:
                filters = yaml.safe_load(file)
                logger.info("FilterActions loaded: {}".format(filters))
        except Exception as e:
            logger.error("Failed to load filter: {}".format(e))
            raise
        
        filter_groups = []
        for filter in filters:
            watching_folder = filter["folder"]
            filter_actions = filter["actions"]
            logger.info(f"Creating FilterGroup for folder: {watching_folder}")
            filter_groups.append(FilterGroup(watching_folder, filter_actions))
        
        logger.info(f"Filter groups created: {filter_groups}")
        return filter_groups
    