import math
import sys
import traceback

import immutables
from es_aws_functions import aws_functions

from spp_logger import SPPLogger, SPPLoggerConfig


def calculate_adjacent_periods(current_period, periodicity):
    """
    Description: This method uses periodicity to calculate
    what should be the adjacent periods for a row,
    Then uses a filter to confirm whether these periods exist for a record.
    :param current_period: int/str(either) - The current period to find the previous for
    :param periodicity: String - The periodicity of the survey we are imputing for:
    01 = monthly, 02 = annually, 03 = quarterly
    :return: previous_period: String - The previous period.
    """
    monthly = "01"
    annually = "02"
    current_month = str(current_period)[4:]
    current_year = str(current_period)[:4]
    if periodicity == monthly:

        last_month = int(float(current_month)) - int(periodicity)
        last_year = int(current_year)
        if last_month < 1:
            last_year -= 1
            last_month += 12
        if last_month < 10:
            last_month = "0" + str(last_month)

        last_period = str(last_year) + str(last_month)

    elif periodicity == annually:

        last_period = str(int(current_period) - 1)

    else:  # quarterly(03)

        last_month = int(current_month) - 3
        last_year = int(current_year)
        if last_month < 1:
            last_year -= 1
            last_month += 4
        if len(str(last_month)) < 2:
            last_month = "0" + str(last_month)
        last_period = str(last_year) + str(last_month)

    return last_period


def handle_exception(exception, module, run_id, context=None, bpm_queue_url=None):
    """
    Description: Generates an error message from an exception.
    Returns an error message detailing exception type, arguments, and line number.
    :param exception: Exception that has occurred - Type: Exception
    :param module: Name of current module - Type: String
    :param run_id: The current run's ID - Type: String
    :param context: AWS Context object
    (has default so that moving to glue will not require lots of changes)
    :param bpm_queue_url: The url of the queue to send the BPM status message to.
    :return error_message: Error message generated for exception - Type: String
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)[-1]
    error_message = str(exc_type) + " in " + module + " | RunID: " + str(run_id) + \
        " |- " + str(exception.args)
    if context:
        error_message += " | Request ID: " + str(context.aws_request_id)
    error_message += " | Outer line number: " + str(exception.__traceback__.tb_lineno)
    error_message += " | Inner Line number: " + str(tb[1]) + " in: " + str(tb[0])

    if bpm_queue_url:
        status_msg = "ERROR"
        aws_functions.send_bpm_status(bpm_queue_url, module, status_msg, run_id)

    return error_message


def sas_round(num):
    """
    Description: Replicates the sas rounding method by not rounding to nearest even.
    :param num: Decimal number to round - Type: Float
    :return num: Rounded number - Type: Int
    """
    if (num % 1 >= 0.5):
        return math.ceil(num)
    else:
        return math.floor(num)


def get_logger(survey, module_name, environment, run_id, log_level="INFO"):
    """
    Description: Returns the spp-logger with loglevel set.
                 defaults to info.
    :param survey: Name of the current survey - Type: String
    :param module_name: Name of current module - Type: String
    :param environment: Name of the current environment - Type: String
    :param run_id: ID passed from BPM
    :param log_level: the log_level for the logger - Type: String (default=INFO)
    :return logger: The logger - Type: Logger
    """

    # set the logger context attributes
    main_context = immutables.Map(log_correlation_id=str(run_id),
                                  log_correlation_type=survey,
                                  log_level=log_level
                                  )
    # set logger configs
    config = SPPLoggerConfig(
        service="Results",
        component=module_name,
        environment=environment,
        deployment=environment,
    )
    # set the logger with context and configs
    # Stream is configurable as any IO, it defaults to stdout
    logger = SPPLogger(
        name="my_logger",
        config=config,
        context=main_context,
        stream=sys.stdout,
    )
    return logger
