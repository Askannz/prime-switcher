import sys
from ..config import load_config, copy_user_config
from .. import var
from ..xorg import cleanup_xorg_conf
from ..checks import is_ac_power_connected, is_nvidia_display_connected
from ..kernel_parameters import get_kernel_parameters
from ..log_utils import set_logger_config, get_logger


def main():

    var.cleanup_tmp_vars()

    daemon_run_id = var.make_daemon_run_id()
    var.write_daemon_run_id(daemon_run_id)

    set_logger_config("daemon", daemon_run_id)
    logger = get_logger()

    startup_mode = None

    try:
        logger.info("# Daemon pre-start hook")

        cleanup_xorg_conf()
        copy_user_config()
        config = load_config()

        kernel_parameters = get_kernel_parameters()
        if kernel_parameters["startup_mode"] is not None:
            startup_mode = kernel_parameters["startup_mode"]
        else:
            startup_mode = config["optimus"]["startup_mode"]

        logger.info("Startup mode is: %s", startup_mode)

        if startup_mode == "auto":
            if is_ac_power_connected():
                eff_startup_mode = config["optimus"]["startup_auto_extpower_mode"]
            else:
                eff_startup_mode = config["optimus"]["startup_auto_battery_mode"]
            logger.info("Effective startup mode is: %s", eff_startup_mode)
        elif startup_mode == "auto_nvdisplay":
            if is_nvidia_display_connected():
                eff_startup_mode = config["optimus"]["startup_auto_nvdisplay_on_mode"]
            else:
                eff_startup_mode = config["optimus"]["startup_auto_nvdisplay_off_mode"]
            logger.info("Effective startup mode is: %s", eff_startup_mode)
        else:
            eff_startup_mode = startup_mode

        state = {
            "type": "pending_pre_xorg_start",
            "requested_mode": eff_startup_mode,
            "current_mode": None
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:

        logger.exception("Daemon startup error")

        state = {
            "type": "startup_failed",
            "startup_mode": startup_mode,
            "daemon_run_id": daemon_run_id
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Daemon pre-start hook completed successfully.")
        logger.info("Calling Xorg pre-start hook.")


if __name__ == "__main__":
    main()
