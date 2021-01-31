import sys
from ..config import load_config
from .. import var
from ..xorg import do_xsetup, set_DPI
from ..log_utils import set_logger_config, get_logger
from ..pci import get_gpus_bus_ids


def main():

    prev_state = var.load_state()

    if prev_state is None or prev_state["type"] != "pending_post_xorg_start":
        return

    switch_id = prev_state["switch_id"]

    set_logger_config("switch", switch_id)
    logger = get_logger()

    requested_mode = None

    try:
        logger.info("# Xorg post-start hook")

        requested_mode = prev_state["requested_mode"]

        config = load_config()
        bus_ids = get_gpus_bus_ids()
        do_xsetup(requested_mode, config, bus_ids)
        set_DPI(config)

        state = {
            "type": "done",
            "switch_id": switch_id,
            "current_mode": requested_mode
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:

        logger.exception("Xorg post-start setup error")

        state = {
            "type": "post_xorg_start_failed",
            "switch_id": switch_id,
            "requested_mode": requested_mode
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Xorg post-start hook completed successfully.")


if __name__ == "__main__":
    main()
