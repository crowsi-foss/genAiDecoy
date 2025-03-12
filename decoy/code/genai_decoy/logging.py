import logging
import ecs_logging

# Set up the global ECS logger
logger = logging.getLogger("genai_decoy")
handler = logging.StreamHandler()
handler.setFormatter(ecs_logging.StdlibFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def ecs_log(event_type, message, **kwargs):
    """
    Logs messages in ECS (Elastic Common Schema) compatible format.

    Parameters:
    - event_type (str): Type of the event (e.g., "error", "info").
    - message (str): The message to log.
    - kwargs (dict): Additional metadata fields for ECS logging.
    """
    if event_type == "error":
        logger.error(message, extra=kwargs)
    else:
        logger.info(message, extra=kwargs)

