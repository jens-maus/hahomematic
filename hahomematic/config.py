"""Global configuration parameters."""

from __future__ import annotations

from hahomematic.const import (
    DEFAULT_CONNECTION_CHECKER_INTERVAL,
    DEFAULT_JSON_SESSION_AGE,
    DEFAULT_LAST_COMMAND_SEND_STORE_TIMEOUT,
    DEFAULT_PING_PONG_MISMATCH_COUNT,
    DEFAULT_PING_PONG_MISMATCH_COUNT_TTL,
    DEFAULT_RECONNECT_WAIT,
    DEFAULT_TIMEOUT,
    DEFAULT_WAIT_FOR_CALLBACK,
)

CALLBACK_WARN_INTERVAL = DEFAULT_CONNECTION_CHECKER_INTERVAL * 40
CONNECTION_CHECKER_INTERVAL = DEFAULT_CONNECTION_CHECKER_INTERVAL
JSON_SESSION_AGE = DEFAULT_JSON_SESSION_AGE
LAST_COMMAND_SEND_STORE_TIMEOUT = DEFAULT_LAST_COMMAND_SEND_STORE_TIMEOUT
PING_PONG_MISMATCH_COUNT = DEFAULT_PING_PONG_MISMATCH_COUNT
PING_PONG_MISMATCH_COUNT_TTL = DEFAULT_PING_PONG_MISMATCH_COUNT_TTL
RECONNECT_WAIT = DEFAULT_RECONNECT_WAIT
TIMEOUT = DEFAULT_TIMEOUT
WAIT_FOR_CALLBACK = DEFAULT_WAIT_FOR_CALLBACK
