#!/usr/bin/env python3
import sys
import os
import signal
import select
import socket
import json
import logging
from .. import envs
from ..config import load_config, ConfigError
from .. import var
from ..log_utils import set_logger_config, get_logger


def main():

    daemon_run_id = var.load_daemon_run_id()

    set_logger_config("daemon", daemon_run_id)
    logger = get_logger()

    try:
        logger.info("# Commands daemon")

        logger.info("Opening UNIX socket")
        server_socket = _open_server_socket(logger)

        _setup_signal_handler(logger, server_socket)

        logger.info("Awaiting commands")

        while True:

            msg = _wait_for_command(server_socket)
            logger.info("Received command : %s", msg)

            _process_command(logger, msg)

    # pylint: disable=W0703
    except Exception:
        logger.exception("Daemon crashed")


def _open_server_socket(logger):

    if os.path.exists(envs.SOCKET_PATH):
        logger.warning(
            "The UNIX socket file %s already exists ! Either another "
            "daemon instance is running or the daemon was not exited gracefully "
            "last time.\nRemoving the file and moving on..." % envs.SOCKET_PATH)
        os.remove(envs.SOCKET_PATH)

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server_socket.settimeout(envs.SOCKET_TIMEOUT)
    server_socket.bind(envs.SOCKET_PATH)
    os.chmod(envs.SOCKET_PATH, 0o666)

    return server_socket


def _setup_signal_handler(logger, server_socket):

    handler = _SignalHandler(logger, server_socket)
    signal.signal(signal.SIGTERM, handler.handler)
    signal.signal(signal.SIGINT, handler.handler)


def _wait_for_command(server_socket):

    select.select([server_socket], [], [])
    datagram = server_socket.recv(1024)
    msg = datagram.decode('utf-8')

    return msg


def _process_command(logger, msg):

    try:
        command = json.loads(msg)
    except json.decoder.JSONDecodeError:
        logger.error("Invalid command  \"%s\" ! (JSON decode error)" % msg)
        return

    try:
        if command["type"] == "switch":

            mode = command["args"]["mode"]
            logger.info("Writing requested GPU mode %s" % mode)

            state = var.load_state()

            new_state = {
                "type": "pending_pre_xorg_start",
                "requested_mode": mode,
                "current_mode": state["current_mode"]
            }
            var.write_state(new_state)

        elif command["type"] == "startup":
            logger.info("Writing startup mode %s" % command["args"]["mode"])
            var.write_startup_mode(command["args"]["mode"])

        elif command["type"] == "temp_config":
            if command["args"]["path"] == "":
                logger.info("Removing temporary config file path")
                var.remove_temp_conf_path_var()
            else:
                logger.info("Writing temporary config file path %s" % command["args"]["path"])
                var.write_temp_conf_path_var(command["args"]["path"])

        elif command["type"] == "user_config":
            _replace_user_config(logger, command["args"]["content"])

        else:
            logger.error("Invalid command  \"%s\" ! Unknown type %s" % (msg, command["type"]))

    except KeyError as e:
        logger.error("Invalid command  \"%s\" ! Key error : %s" % (msg, str(e)))


def _replace_user_config(logger, config_content):
    logger.info("Replacing user config at %s with provided content" % envs.USER_CONFIG_PATH)
    with open(envs.USER_CONFIG_PATH, "w") as f:
        f.write(config_content)


class _SignalHandler:
    def __init__(self, logger, server_socket):
        self.logger = logger
        self.server_socket = server_socket

    def handler(self, signum, frame):
        #pylint: disable=unused-argument

        self.logger.info("Process stop requested")

        self.logger.info("Closing and removing the socket...")
        self.server_socket.close()
        os.remove(envs.SOCKET_PATH)

        self.logger.info("Goodbye !")
        sys.exit(0)


if __name__ == '__main__':
    main()
