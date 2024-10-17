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
        logger.info(f"Creating filter criteria from: {criterion}")
        filter_criteria_list = []
        for criterion, value in criterion.items():
            match criterion: 
                case FromFilterActionCriterion.FROM_CRITERIA_TAG:
                    logger.info(f"Creating FromFilterActionCriterion for criterion: {criterion} with value: {value}")
                    filter_criteria_list.append(FromFilterActionCriterion(value))
        
        logger.info(f"Filter criteria created: {filter_criteria_list}")
        return filter_criteria_list
    
class FromFilterActionCriterion(FilterActionCriterion):
    FROM_CRITERIA_TAG = "from"

    def __init__(self, value):
        self.value = value
        logger.info(f"FromFilterActionCriterion initialized with value: {self.value}")

    def check_condition(self, email):
        logger.debug(f"Checking 'from' criterion for email: {email}")

        sender_address = re.search(self.EMAIL_ADDRESS_SELECTOR, email.get(self.FROM_CRITERIA_TAG)).group(1)
        if sender_address != self.value:
            logger.info(f"Email sender {sender_address} does not match criterion value {self.value}")
            return False
        logger.info(f"Email sender {sender_address} matches criterion value {self.value}")
        return True
