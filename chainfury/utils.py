import os
import time
import logging
from typing import Any, Dict


class CFEnv:
    """
    Single namespace for all environment variables.

    * CF_FOLDER: database connection string
    """

    CF_FOLDER = lambda: os.path.expanduser(os.getenv("CF_FOLDER", "~/cf"))
    CF_BLOB_STORAGE = lambda: os.path.join(CFEnv.CF_FOLDER(), "blob")


os.makedirs(CFEnv.CF_FOLDER(), exist_ok=True)
os.makedirs(CFEnv.CF_BLOB_STORAGE(), exist_ok=True)


def store_blob(key: str, value: bytes) -> str:
    """A function that stores the information in a file."""
    fp = os.path.join(CFEnv.CF_BLOB_STORAGE(), key)
    with open(fp, "wb") as f:
        f.write(value)
    return fp


def terminal_top_with_text(msg: str = "") -> str:
    """Prints full wodth text message on the terminal

    Args:
        msg (str, optional): The message to print. Defaults to "".

    Returns:
        str: The message to print
    """
    width = os.get_terminal_size().columns
    if len(msg) > width - 5:
        x = "=" * width
        x += "\n" + msg
        x += "\n" + "=" * width // 2  # type: ignore
    else:
        x = "=" * (width - len(msg) - 1) + " " + msg
    return x


def get_logger() -> logging.Logger:
    """Returns a logger object"""
    logger = logging.getLogger("fury")
    lvl = os.getenv("FURY_LOG_LEVEL", "info").upper()
    logger.setLevel(getattr(logging, lvl))
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z")
    )
    logger.addHandler(log_handler)
    return logger


logger = get_logger()
"""
This is the logger object that should be used across the entire package as well as by the user what wants to leverage
existing logging infrastructure.
"""


class UnAuthException(Exception):
    """Raised when the API returns a 401"""


class DoNotRetryException(Exception):
    """Raised when code tells not to retry"""


def exponential_backoff(foo, *args, max_retries=2, retry_delay=1, **kwargs) -> Dict[str, Any]:
    """Exponential backoff function

    Args:
        foo (function): The function to call
        max_retries (int, optional): maximum number of retries. Defaults to 2.
        retry_delay (int, optional): Initial delay in seconds. Defaults to 1.

    Raises:
        e: Max retries reached. Exiting...
        Exception: This should never happen

    Returns:
        Dict[str, Any]: The completion(s) generated by the API.
    """

    for attempt in range(max_retries):
        try:
            out = foo(*args, **kwargs)  # Call the function that may crash
            return out  # If successful, break out of the loop and return
        except DoNotRetryException as e:
            raise e
        except UnAuthException as e:
            raise e
        except Exception as e:
            logger.warning(f"Function crashed: {e}")
            if attempt == max_retries - 1:
                logger.error("Max retries reached. Exiting...")
                raise e
            else:
                delay = retry_delay * (2**attempt)  # Calculate the backoff delay
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)  # Wait for the calculated delay
    raise Exception("This should never happen")


def folder(x: str) -> str:
    """get the folder of this file path"""
    return os.path.split(os.path.abspath(x))[0]


def joinp(x: str, *args) -> str:
    """convienience function for os.path.join"""
    return os.path.join(x, *args)
