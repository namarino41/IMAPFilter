import re
from abc import ABC, abstractmethod


from config.logging_config import setup_logging
import logging

setup_logging()  # Set up the logging system

logger = logging.getLogger(__name__)  # Get the logger for this module


class FilterActionCriterion(ABC):
    EMAIL_ADDRESS_SELECTOR = re.compile('<(.*?)>')

    @abstractmethod
    def check_condition(self, email):
        raise NotImplementedError
    
    @staticmethod
    def create_filter_criterion(criterion):
        filter_criteria_list = []
        for criterion, value in criterion.items():
            match criterion: 
                case FromFilterActionCriterion.FROM_CRITERIA_TAG:
                    filter_criteria_list.append(FromFilterActionCriterion(value))
        
        return filter_criteria_list
    
class FromFilterActionCriterion(FilterActionCriterion):
    FROM_CRITERIA_TAG = "from"

    def __init__(self, value):
        self.value = value
        print(value)

    def check_condition(self, email):
        sender_address = re.search(self.EMAIL_ADDRESS_SELECTOR, email.get(self.FROM_CRITERIA_TAG)).group(1)
        if sender_address != self.value:
            return False
        return True
