import os
from pathlib import Path
from optimus_manager.bash import exec_bash, BashError
import optimus_manager.envs as envs
import optimus_manager.checks as checks
from .pci import get_gpus_bus_ids
from .config import load_extra_xorg_options
from .hacks.manjaro import remove_mhwd_conf
from .log_utils import get_logger


class XorgSetupError(Exception):
    pass


def configure_xorg(config, requested_gpu_mode):

    bus_ids = get_gpus_bus_ids()
    xorg_extra = load_extra_xorg_options()

    if requested_gpu_mode == "nvidia":
        xorg_conf_text = _generate_nvidia(config, bus_ids, xorg_extra)
    elif requested_gpu_mode == "integrated" and "intel" in bus_ids:
        xorg_conf_text = _generate_intel(config, bus_ids, xorg_extra)
    elif requested_gpu_mode == "integrated" and "amd" in bus_ids:
        xorg_conf_text = _generate_amd(config, bus_ids, xorg_extra)
    elif requested_gpu_mode == "hybrid" and "intel" in bus_ids:
        xorg_conf_text = _generate_hybrid_intel(config, bus_ids, xorg_extra)
    elif requested_gpu_mode == "hybrid" and "amd" in bus_ids:
        xorg_conf_text = _generate_hybrid_amd(config, bus_ids, xorg_extra)

    remove_mhwd_conf()
    _write_xorg_conf(xorg_conf_text)


def cleanup_xorg_conf():

    logger = get_logger()

    logger.info("Removing %s (if present)", envs.XORG_CONF_PATH)

    try:
        os.remove(envs.XORG_CONF_PATH)
    except FileNotFoundError:
        pass


def is_xorg_running():

    try:
        exec_bash("pidof X")
        return True
    except BashError:
        pass

    try:
        exec_bash("pidof Xorg")
        return True
    except BashError:
        pass

    return False


def is_there_a_default_xorg_conf_file():
    return os.path.isfile("/etc/X11/xorg.conf")


def is_there_a_MHWD_file():
    return os.path.isfile("/etc/X11/xorg.conf.d/90-mhwd.conf")


def do_xsetup(requested_mode):

    logger = get_logger()

    if requested_mode == "nvidia":

        logger.info("Running xrandr commands")

        try:
            exec_bash("xrandr --setprovideroutputsource modesetting NVIDIA-0")
            exec_bash("xrandr --auto")
        except BashError as e:
            logger.error("Cannot setup PRIME : %s", str(e))


    script_path = _get_xsetup_script_path(requested_mode)

    logger.info("Running %s", script_path)

    try:
        exec_bash(script_path)
    except BashError as e:
        logger.error("ERROR : cannot run %s : %s", script_path, str(e))


def set_DPI(config):

    dpi_str = config["nvidia"]["dpi"]

    if dpi_str == "":
        return

    try:
        exec_bash("xrandr --dpi %s" % dpi_str)
    except BashError as e:
        raise XorgSetupError("Cannot set DPI : %s" % str(e))

def _get_xsetup_script_path(requested_mode):

    logger = get_logger()

    if requested_mode == "integrated":

        bus_ids = get_gpus_bus_ids()
        if "intel" in bus_ids:

            if Path(envs.XSETUP_SCRIPTS_PATHS["intel"]).exists():

                logger.warning(
                    "The custom xsetup script path %s is deprecated."
                    "It will still work for now, but you should move its content to %s.",
                    envs.XSETUP_SCRIPTS_PATHS["intel"],
                    envs.XSETUP_SCRIPTS_PATHS["integrated"])

                script_name = "intel"

            else:
                script_name = "integrated"

        else:
            script_name = "integrated"

    elif requested_mode == "nvidia":
        script_name = "nvidia"
    elif requested_mode == "hybrid":
        script_name = "hybrid"
    else:
        assert False

    script_path = envs.XSETUP_SCRIPTS_PATHS[script_name]

    return script_path


def _generate_nvidia(config, bus_ids, xorg_extra):

    integrated_gpu = "intel" if "intel" in bus_ids else "amd"
    xorg_extra_lines = xorg_extra["nvidia-mode"]["nvidia-gpu"]

    text = _make_modules_paths_section()

    text += "Section \"ServerLayout\"\n" \
            "\tIdentifier \"layout\"\n" \
            "\tScreen 0 \"nvidia\"\n" \
            "\tInactive \"integrated\"\n" \
            "EndSection\n\n"

    text += _make_nvidia_device_section(config, bus_ids, xorg_extra_lines)

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"nvidia\"\n" \
            "\tDevice \"nvidia\"\n" \
            "\tOption \"AllowEmptyInitialConfiguration\"\n"

    if config["nvidia"]["allow_external_gpus"] == "yes":
        text += "\tOption \"AllowExternalGpus\"\n"

    text += "EndSection\n\n"

    text += "Section \"Device\"\n" \
            "\tIdentifier \"integrated\"\n" \
            "\tDriver \"modesetting\"\n"
    text += "\tBusID \"%s\"\n" % bus_ids[integrated_gpu]
    text += "EndSection\n\n"

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"integrated\"\n" \
            "\tDevice \"integrated\"\n" \
            "EndSection\n\n"

    text += _make_server_flags_section(config)

    return text


def _make_modules_paths_section():

    return "Section \"Files\"\n" \
           "\tModulePath \"/usr/lib/nvidia\"\n" \
           "\tModulePath \"/usr/lib32/nvidia\"\n" \
           "\tModulePath \"/usr/lib32/nvidia/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib32/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib64/nvidia/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib64/nvidia/xorg\"\n" \
           "\tModulePath \"/usr/lib64/xorg/modules\"\n" \
           "EndSection\n\n"


def _generate_intel(config, bus_ids, xorg_extra):
    xorg_extra_lines = xorg_extra["integrated-mode"]["integrated-gpu"]
    text = _make_intel_device_section(config, bus_ids, xorg_extra_lines)
    return text

def _generate_amd(config, bus_ids, xorg_extra):
    xorg_extra_lines = xorg_extra["integrated-mode"]["integrated-gpu"]
    text = _make_amd_device_section(config, bus_ids, xorg_extra_lines)
    return text

def _generate_hybrid_intel(config, bus_ids, xorg_extra):

    xorg_extra_lines_integrated = xorg_extra["hybrid-mode"]["integrated-gpu"]
    xorg_extra_lines_nvidia = xorg_extra["hybrid-mode"]["nvidia-gpu"]

    text = _make_modules_paths_section()

    text += "Section \"ServerLayout\"\n" \
           "\tIdentifier \"layout\"\n" \
           "\tScreen 0 \"intel\"\n" \
           "\tInactive \"nvidia\"\n" \
           "\tOption \"AllowNVIDIAGPUScreens\"\n" \
           "EndSection\n\n"

    text += _make_intel_device_section(config, bus_ids, xorg_extra_lines_integrated)

    text += "Section \"Screen\"\n" \
           "\tIdentifier \"intel\"\n" \
           "\tDevice \"intel\"\n"

    if config["nvidia"]["allow_external_gpus"] == "yes":
        text += "\tOption \"AllowExternalGpus\"\n"

    text += "EndSection\n\n"

    text += _make_nvidia_device_section(config, bus_ids, xorg_extra_lines_nvidia)

    text += "Section \"Screen\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDevice \"nvidia\"\n" \
           "EndSection\n\n"

    text += _make_server_flags_section(config)

    return text

def _generate_hybrid_amd(config, bus_ids, xorg_extra):

    xorg_extra_lines_integrated = xorg_extra["hybrid-mode"]["integrated-gpu"]
    xorg_extra_lines_nvidia = xorg_extra["hybrid-mode"]["nvidia-gpu"]

    text = _make_modules_paths_section()

    text += "Section \"ServerLayout\"\n" \
           "\tIdentifier \"layout\"\n" \
           "\tScreen 0 \"amd\"\n" \
           "\tOption \"AllowNVIDIAGPUScreens\"\n" \
           "EndSection\n\n"

    text += _make_amd_device_section(config, bus_ids, xorg_extra_lines_integrated)

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"amd\"\n" \
            "\tDevice \"amd\"\n"

    if config["nvidia"]["allow_external_gpus"] == "yes":
        text += "\tOption \"AllowExternalGpus\"\n"

    text += "EndSection\n\n"

    text += _make_nvidia_device_section(config, bus_ids, xorg_extra_lines_nvidia)

    text += "Section \"Screen\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDevice \"nvidia\"\n" \
           "EndSection\n\n"

    text += _make_server_flags_section(config)

    return text

def _make_nvidia_device_section(config, bus_ids, xorg_extra_lines):

    options = config["nvidia"]["options"].replace(" ", "").split(",")

    text = "Section \"Device\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDriver \"nvidia\"\n"
    text += "\tBusID \"%s\"\n" % bus_ids["nvidia"]
    if "overclocking" in options:
        text += "\tOption \"Coolbits\" \"28\"\n"
    if "triple_buffer" in options:
        text += "\tOption \"TripleBuffer\" \"true\"\n"

    for line in xorg_extra_lines:
        text += ("\t" + line + "\n")

    text += "EndSection\n\n"

    return text

def _make_intel_device_section(config, bus_ids, xorg_extra_lines):

    logger = get_logger()

    if config["intel"]["driver"] == "intel" and not checks.is_xorg_intel_module_available():
        logger.warning("The Xorg module intel is not available. Defaulting to modesetting.")
        driver = "modesetting"
    else:
        driver = config["intel"]["driver"]

    dri = int(config["intel"]["dri"])

    text = "Section \"Device\"\n" \
           "\tIdentifier \"intel\"\n"
    text += "\tDriver \"%s\"\n" % driver
    text += "\tBusID \"%s\"\n" % bus_ids["intel"]
    if config["intel"]["accel"] != "":
        text += "\tOption \"AccelMethod\" \"%s\"\n" % config["intel"]["accel"]
    if config["intel"]["tearfree"] != "":
        tearfree_enabled_str = {"yes": "true", "no": "false"}[config["intel"]["tearfree"]]
        text += "\tOption \"TearFree\" \"%s\"\n" % tearfree_enabled_str
    text += "\tOption \"DRI\" \"%d\"\n" % dri

    for line in xorg_extra_lines:
        text += ("\t" + line + "\n")

    text += "EndSection\n\n"

    return text


def _make_amd_device_section(config, bus_ids, xorg_extra_lines):

    logger = get_logger()

    if config["amd"]["driver"] == "amdgpu" and not checks.is_xorg_amdgpu_module_available():
        logger.warning("The Xorg module amdgpu is not available. Defaulting to modesetting.")
        driver = "modesetting"
    else:
        driver = config["amd"]["driver"]

    dri = int(config["amd"]["dri"])

    text = "Section \"Device\"\n" \
           "\tIdentifier \"amd\"\n"
    text += "\tDriver \"%s\"\n" % driver
    text += "\tBusID \"%s\"\n" % bus_ids["amd"]
    if config["amd"]["tearfree"] != "":
        tearfree_enabled_str = {"yes": "true", "no": "false"}[config["amd"]["tearfree"]]
        text += "\tOption \"TearFree\" \"%s\"\n" % tearfree_enabled_str
    text += "\tOption \"DRI\" \"%d\"\n" % dri

    for line in xorg_extra_lines:
        text += ("\t" + line + "\n")

    text += "EndSection\n\n"

    return text


def _make_server_flags_section(config):
    if config["nvidia"]["ignore_abi"] == "yes":
        return (
            "Section \"ServerFlags\"\n"
            "\tOption \"IgnoreABI\" \"1\"\n"
            "EndSection\n\n"
        )
    return ""

def _write_xorg_conf(xorg_conf_text):

    logger = get_logger()

    filepath = Path(envs.XORG_CONF_PATH)

    try:
        os.makedirs(filepath.parent, mode=0o755, exist_ok=True)
        with open(filepath, 'w') as f:
            logger.info("Writing to %s", envs.XORG_CONF_PATH)
            f.write(xorg_conf_text)
    except IOError:
        raise XorgSetupError("Cannot write Xorg conf at %s" % str(filepath))
