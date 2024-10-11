from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from providers.imap_provider import ImapProvider
from abc import ABC, abstractmethod
from filters.filteractions_criteria import FilterActionCriterion
from typing import override

from config.logging_config import setup_logging
import logging

setup_logging()  # Set up the logging system

logger = logging.getLogger(__name__)  # Get the logger for this module


class FilterAction(ABC):
    FILTER_CRITERION_FROM = "from"

    @abstractmethod
    def apply(self, emails, imap_provider: ImapProvider):
        raise NotImplementedError
    
    @staticmethod
    def create_filter_actions(filters):
        filter_actions_list = []
        for filter, values in filters.items():
            match filter:
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
