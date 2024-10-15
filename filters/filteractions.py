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

class FilterGroup:

    def __init__(self, watching_folder, filter_actions):
        self.watching_folder = watching_folder
        self.filter_actions = FilterAction.create_filter_actions(filter_actions)

    def apply_filters(self, emails, imap_provider: ImapProvider):
        for filter_action in self.filter_actions:
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
            filter_groups.append(FilterGroup(watching_folder, filter_actions))
        
        return filter_groups
    
    def __eq__(self, other):
        if isinstance(other, FilterGroup):
            return self.watching_folder == other.watching_folder
        return False

    def __hash__(self):
        return hash(self.watching_folder)


class FilterAction(ABC):
    @abstractmethod
    def apply(self, emails, imap_provider: ImapProvider):
        raise NotImplementedError
    
    @staticmethod
    def create_filter_actions(filters):
        filter_actions_list = []
        for filter in filters:
            for filter_action, values in filter.items():
                match filter_action:
                    case DeleteFilterAction.DELETE_FILTER_ACTION_TAG:
                        filter_actions_list.extend(list(map(lambda value: DeleteFilterAction(value), values)))

        return filter_actions_list
            
class DeleteFilterAction(FilterAction):
    DELETE_FILTER_ACTION_TAG = "delete"

    def __init__(self, filter_criteria):
        self.filter_criteria = \
            FilterActionCriterion.create_filter_criterion(filter_criteria)

    def _check_criteria(self, email):
        return all(criterion.check_condition(email) \
            for criterion in self.filter_criteria)
                
    @override
    def apply(self, emails, imap_provider: ImapProvider):        
        emails_to_delete = []
        email_data = imap_provider.get_email_data(emails)
        for uid, email in email_data.items():
            if self._check_criteria(email):
                emails_to_delete.append(uid)
        imap_provider.delete_emails(emails_to_delete)
