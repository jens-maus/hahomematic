"""Module about parameter visibility within hahomematic."""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
import logging
import os
from typing import Any, Final

from hahomematic import central as hmcu, support as hms
from hahomematic.const import CLICK_EVENTS, UN_IGNORE_WILDCARD, UTF8, Parameter, ParamsetKey
from hahomematic.model.custom import get_required_parameters
from hahomematic.support import element_matches_key, reduce_args

_LOGGER: Final = logging.getLogger(__name__)

_FILE_CUSTOM_UN_IGNORE_PARAMETERS: Final = "unignore"
_IGNORE_MODEL: Final = "ignore_"

# Define which additional parameters from MASTER paramset should be created as data_point.
# By default these are also on the _HIDDEN_PARAMETERS, which prevents these data points
# from being display by default. Usually these enties are used within custom data points,
# and not for general display.
# {model: (channel_no, parameter)}

_CLIMATE_MASTER_PARAMETERS: Final[tuple[Parameter, ...]] = (
    Parameter.GLOBAL_BUTTON_LOCK,
    Parameter.MIN_MAX_VALUE_NOT_RELEVANT_FOR_MANU_MODE,
    Parameter.OPTIMUM_START_STOP,
    Parameter.TEMPERATURE_MAXIMUM,
    Parameter.TEMPERATURE_MINIMUM,
    Parameter.TEMPERATURE_OFFSET,
)
_RELEVANT_MASTER_PARAMSETS_BY_DEVICE: Final[
    Mapping[str, tuple[tuple[int | None, ...], tuple[Parameter, ...]]]
] = {
    "ALPHA-IP-RBG": ((0, 1), _CLIMATE_MASTER_PARAMETERS),
    "HM-CC-RT-DN": ((None, 1), _CLIMATE_MASTER_PARAMETERS),
    "HM-CC-VG-1": ((0, 1), _CLIMATE_MASTER_PARAMETERS),
    "HM-TC-IT-WM-W-EU": ((None,), (Parameter.GLOBAL_BUTTON_LOCK,)),
    "HmIP-BWTH": ((0, 1), _CLIMATE_MASTER_PARAMETERS),
    "HmIP-DRBLI4": (
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 17, 21),
        (Parameter.CHANNEL_OPERATION_MODE,),
    ),
    "HmIP-DRDI3": ((1, 2, 3), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-DRSI1": ((1,), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-DRSI4": ((1, 2, 3, 4), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-DSD-PCB": ((1,), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-FAL": ((0,), (Parameter.GLOBAL_BUTTON_LOCK,)),
    "HmIP-FCI1": ((1,), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-FCI6": (tuple(range(1, 7)), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-FSI16": ((1,), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-HEATING": ((0, 1), _CLIMATE_MASTER_PARAMETERS),
    "HmIP-MIO16-PCB": ((13, 14, 15, 16), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-MOD-RC8": (tuple(range(1, 9)), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIP-RGBW": ((0,), (Parameter.DEVICE_OPERATION_MODE,)),
    "HmIP-STH": ((1,), _CLIMATE_MASTER_PARAMETERS),
    "HmIP-WTH": ((0, 1), _CLIMATE_MASTER_PARAMETERS),
    "HmIP-eTRV": ((0, 1), _CLIMATE_MASTER_PARAMETERS),
    "HmIPW-DRBL4": ((1, 5, 9, 13), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIPW-DRI16": (tuple(range(1, 17)), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIPW-DRI32": (tuple(range(1, 33)), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIPW-FAL": ((0,), (Parameter.GLOBAL_BUTTON_LOCK,)),
    "HmIPW-FIO6": (tuple(range(1, 7)), (Parameter.CHANNEL_OPERATION_MODE,)),
    "HmIPW-STH": ((0, 1), _CLIMATE_MASTER_PARAMETERS),
}

# Ignore events for some devices
_IGNORE_DEVICES_FOR_DATA_POINT_EVENTS: Final[Mapping[str, tuple[Parameter, ...]]] = {
    "HmIP-PS": CLICK_EVENTS,
}

# data points that will be created, but should be hidden.
_HIDDEN_PARAMETERS: Final[tuple[Parameter, ...]] = (
    Parameter.ACTIVITY_STATE,
    Parameter.CHANNEL_OPERATION_MODE,
    Parameter.CONFIG_PENDING,
    Parameter.DIRECTION,
    Parameter.ERROR,
    Parameter.MIN_MAX_VALUE_NOT_RELEVANT_FOR_MANU_MODE,
    Parameter.OPTIMUM_START_STOP,
    Parameter.SECTION,
    Parameter.STICKY_UN_REACH,
    Parameter.TEMPERATURE_MAXIMUM,
    Parameter.TEMPERATURE_MINIMUM,
    Parameter.TEMPERATURE_OFFSET,
    Parameter.UN_REACH,
    Parameter.UPDATE_PENDING,
    Parameter.WORKING,
)

# Parameters within the VALUES paramset for which we don't create data points.
_IGNORED_PARAMETERS: Final[tuple[str, ...]] = (
    "ACCESS_AUTHORIZATION",
    "ACOUSTIC_NOTIFICATION_SELECTION",
    "ADAPTION_DRIVE",
    "AES_KEY",
    "ALARM_COUNT",
    "ALL_LEDS",
    "ARROW_DOWN",
    "ARROW_UP",
    "BACKLIGHT",
    "BEEP",
    "BELL",
    "BLIND",
    "BOOST_STATE",
    "BOOST_TIME",
    "BOOT",
    "BULB",
    "CLEAR_ERROR",
    "CLEAR_WINDOW_OPEN_SYMBOL",
    "CLOCK",
    "CONTROL_DIFFERENTIAL_TEMPERATURE",
    "DATE_TIME_UNKNOWN",
    "DECISION_VALUE",
    "DEVICE_IN_BOOTLOADER",
    "DISPLAY_DATA_ALIGNMENT",
    "DISPLAY_DATA_BACKGROUND_COLOR",
    "DISPLAY_DATA_COMMIT",
    "DISPLAY_DATA_ICON",
    "DISPLAY_DATA_ID",
    "DISPLAY_DATA_STRING",
    "DISPLAY_DATA_TEXT_COLOR",
    "DOOR",
    "EXTERNAL_CLOCK",
    "FROST_PROTECTION",
    "HUMIDITY_LIMITER",
    "IDENTIFICATION_MODE_KEY_VISUAL",
    "IDENTIFICATION_MODE_LCD_BACKLIGHT",
    "INCLUSION_UNSUPPORTED_DEVICE",
    "INHIBIT",
    "INSTALL_MODE",
    "INTERVAL",
    "LEVEL_REAL",
    "OLD_LEVEL",
    "OVERFLOW",
    "OVERRUN",
    "PARTY_SET_POINT_TEMPERATURE",
    "PARTY_TEMPERATURE",
    "PARTY_TIME_END",
    "PARTY_TIME_START",
    "PHONE",
    "PROCESS",
    "QUICK_VETO_TIME",
    "RAMP_STOP",
    "RELOCK_DELAY",
    "SCENE",
    "SELF_CALIBRATION",
    "SERVICE_COUNT",
    "SET_SYMBOL_FOR_HEATING_PHASE",
    "SHADING_SPEED",
    "SHEV_POS",
    "SPEED",
    "STATE_UNCERTAIN",
    "SUBMIT",
    "SWITCH_POINT_OCCURED",
    "TEMPERATURE_LIMITER",
    "TEMPERATURE_OUT_OF_RANGE",
    "TEXT",
    "USER_COLOR",
    "USER_PROGRAM",
    "VALVE_ADAPTION",
    "WINDOW",
    "WIN_RELEASE",
    "WIN_RELEASE_ACT",
)

# Ignore Parameter that end with
_IGNORED_PARAMETERS_WILDCARDS_END: Final[tuple[str, ...]] = (
    "_OVERFLOW",
    "_OVERRUN",
    "_REPORTING",
    "_RESULT",
    "_STATUS",
    "_SUBMIT",
)

# Ignore Parameter that start with
_IGNORED_PARAMETERS_WILDCARDS_START: Final[tuple[str, ...]] = (
    "ADJUSTING_",
    "ERR_TTM_",
    "HANDLE_",
    "IDENTIFY_",
    "PARTY_START_",
    "PARTY_STOP_",
    "STATUS_FLAG_",
    "WEEK_PROGRAM_",
)


# Parameters within the paramsets for which we create data points.
_UN_IGNORE_PARAMETERS_BY_DEVICE: Final[Mapping[str, tuple[Parameter, ...]]] = {
    "HmIP-DLD": (Parameter.ERROR_JAMMED,),
    "HmIP-SWSD": (Parameter.SMOKE_DETECTOR_ALARM_STATUS,),
    "HM-OU-LED16": (Parameter.LED_STATUS,),
    "HM-Sec-Win": (Parameter.DIRECTION, Parameter.WORKING, Parameter.ERROR, Parameter.STATUS),
    "HM-Sec-Key": (Parameter.DIRECTION, Parameter.ERROR),
    "HmIP-PCBS-BAT": (
        Parameter.OPERATING_VOLTAGE,
        Parameter.LOW_BAT,
    ),  # To override ignore for HmIP-PCBS
}

# Parameters by device within the VALUES paramset for which we don't create data points.
_IGNORE_PARAMETERS_BY_DEVICE: Final[Mapping[Parameter, tuple[str, ...]]] = {
    Parameter.CURRENT_ILLUMINATION: (
        "HmIP-SMI",
        "HmIP-SMO",
        "HmIP-SPI",
    ),
    Parameter.LOWBAT: (
        "HM-LC-Sw1-DR",
        "HM-LC-Sw1-FM",
        "HM-LC-Sw1-PCB",
        "HM-LC-Sw1-Pl",
        "HM-LC-Sw1-Pl-DN-R1",
        "HM-LC-Sw1PBU-FM",
        "HM-LC-Sw2-FM",
        "HM-LC-Sw4-DR",
        "HM-SwI-3-FM",
    ),
    Parameter.LOW_BAT: ("HmIP-BWTH", "HmIP-PCBS"),
    Parameter.OPERATING_VOLTAGE: (
        "ELV-SH-BS2",
        "HmIP-BDT",
        "HmIP-BROLL",
        "HmIP-BS2",
        "HmIP-BSL",
        "HmIP-BSM",
        "HmIP-BWTH",
        "HmIP-DR",
        "HmIP-FDT",
        "HmIP-FROLL",
        "HmIP-FSM",
        "HmIP-MOD-OC8",
        "HmIP-PCBS",
        "HmIP-PDT",
        "HmIP-PMFS",
        "HmIP-PS",
        "HmIP-SFD",
    ),
    Parameter.VALVE_STATE: ("HmIPW-FALMOT-C12", "HmIP-FALMOT-C12"),
}

# Some devices have parameters on multiple channels,
# but we want to use it only from a certain channel.
_ACCEPT_PARAMETER_ONLY_ON_CHANNEL: Final[Mapping[str, int]] = {Parameter.LOWBAT: 0}


class ParameterVisibilityCache:
    """Cache for parameter visibility."""

    def __init__(
        self,
        central: hmcu.CentralUnit,
    ) -> None:
        """Init the parameter visibility cache."""
        self._central = central
        self._storage_folder: Final = central.config.storage_folder
        self._required_parameters: Final = get_required_parameters()
        self._raw_un_ignore_list: Final[set[str]] = set(central.config.un_ignore_list or set())

        # un_ignore from custom un_ignore files
        # parameter
        self._custom_un_ignore_values_parameters: Final[set[str]] = set()

        # model, channel_no, paramset_key, parameter
        self._custom_un_ignore_complex: Final[
            dict[str, dict[int | str | None, dict[str, set[str]]]]
        ] = {}
        self._ignore_custom_: Final[list[str]] = []
        self._ignore_parameters_by_device_lower: Final[dict[str, tuple[str, ...]]] = {
            parameter: tuple(model.lower() for model in s)
            for parameter, s in _IGNORE_PARAMETERS_BY_DEVICE.items()
        }

        self._ignore_devices_for_data_point_events_lower: Final[dict[str, tuple[str, ...]]] = {
            model.lower(): tuple(event for event in events)
            for model, events in _IGNORE_DEVICES_FOR_DATA_POINT_EVENTS.items()
        }

        self._un_ignore_parameters_by_device_lower: Final[dict[str, tuple[str, ...]]] = {
            model.lower(): parameters
            for model, parameters in _UN_IGNORE_PARAMETERS_BY_DEVICE.items()
        }

        # model, channel_no, paramset_key, set[parameter]
        self._un_ignore_parameters_by_device_paramset_key: Final[
            dict[str, dict[int | None, dict[ParamsetKey, set[str]]]]
        ] = {}

        # model, channel_no
        self._relevant_master_paramsets_by_device: Final[dict[str, set[int | None]]] = {}
        self._init()

    def _init(self) -> None:
        """Process cache initialisation."""
        for (
            model,
            channels_parameter,
        ) in _RELEVANT_MASTER_PARAMSETS_BY_DEVICE.items():
            model_l = model.lower()
            channel_nos, parameters = channels_parameter
            if model_l not in self._relevant_master_paramsets_by_device:
                self._relevant_master_paramsets_by_device[model_l] = set()
            if model_l not in self._un_ignore_parameters_by_device_paramset_key:
                self._un_ignore_parameters_by_device_paramset_key[model_l] = {}

            def _add_channel(dt_l: str, params: tuple[Parameter, ...], ch_no: int | None) -> None:
                self._relevant_master_paramsets_by_device[dt_l].add(ch_no)
                if ch_no not in self._un_ignore_parameters_by_device_paramset_key[dt_l]:
                    self._un_ignore_parameters_by_device_paramset_key[dt_l][ch_no] = {
                        ParamsetKey.MASTER: set()
                    }
                for parameter in params:
                    self._un_ignore_parameters_by_device_paramset_key[dt_l][ch_no][
                        ParamsetKey.MASTER
                    ].add(parameter)

            if channel_nos:
                for channel_no in channel_nos:
                    _add_channel(dt_l=model_l, params=parameters, ch_no=channel_no)
            else:
                _add_channel(dt_l=model_l, params=parameters, ch_no=None)

    @lru_cache(maxsize=128)
    def model_is_ignored(self, model: str) -> bool:
        """Check if a model should be ignored for custom data points."""
        return element_matches_key(
            search_elements=self._ignore_custom_,
            compare_with=model.lower(),
            do_wildcard_search=True,
        )

    @lru_cache(maxsize=1024)
    def parameter_is_ignored(
        self,
        model: str,
        channel_no: int | None,
        paramset_key: ParamsetKey,
        parameter: str,
    ) -> bool:
        """Check if parameter can be ignored."""
        model_l = model.lower()

        if paramset_key == ParamsetKey.VALUES:
            if self.parameter_is_un_ignored(
                model=model,
                channel_no=channel_no,
                paramset_key=paramset_key,
                parameter=parameter,
            ):
                return False

            if (
                (
                    (
                        parameter in _IGNORED_PARAMETERS
                        or parameter.endswith(tuple(_IGNORED_PARAMETERS_WILDCARDS_END))
                        or parameter.startswith(tuple(_IGNORED_PARAMETERS_WILDCARDS_START))
                    )
                    and parameter not in self._required_parameters
                )
                or hms.element_matches_key(
                    search_elements=self._ignore_parameters_by_device_lower.get(parameter, []),
                    compare_with=model_l,
                )
                or hms.element_matches_key(
                    search_elements=self._ignore_devices_for_data_point_events_lower,
                    compare_with=parameter,
                    search_key=model_l,
                    do_wildcard_search=False,
                )
            ):
                return True

            if (
                accept_channel := _ACCEPT_PARAMETER_ONLY_ON_CHANNEL.get(parameter)
            ) is not None and accept_channel != channel_no:
                return True
        if paramset_key == ParamsetKey.MASTER:
            if parameter in self._custom_un_ignore_complex.get(model_l, {}).get(
                channel_no, {}
            ).get(ParamsetKey.MASTER, []):
                return False  # pragma: no cover

            dt_short = tuple(
                filter(
                    model_l.startswith,
                    self._un_ignore_parameters_by_device_paramset_key,
                )
            )
            if dt_short and parameter not in self._un_ignore_parameters_by_device_paramset_key.get(
                dt_short[0], {}
            ).get(channel_no, {}).get(ParamsetKey.MASTER, []):
                return True

        return False

    def _parameter_is_un_ignored(
        self,
        model: str,
        channel_no: int | str | None,
        paramset_key: ParamsetKey,
        parameter: str,
        custom_only: bool = False,
    ) -> bool:
        """
        Return if parameter is on an un_ignore list.

        This can be either be the users un_ignore file, or in the
        predefined _UN_IGNORE_PARAMETERS_BY_DEVICE.
        """
        model_l = model.lower()

        # check if parameter is in custom_un_ignore
        if (
            paramset_key == ParamsetKey.VALUES
            and parameter in self._custom_un_ignore_values_parameters
        ):
            return True

        # check if parameter is in custom_un_ignore with paramset_key

        search_matrix = (
            (
                (model_l, channel_no),
                (model_l, UN_IGNORE_WILDCARD),
                (UN_IGNORE_WILDCARD, channel_no),
                (UN_IGNORE_WILDCARD, UN_IGNORE_WILDCARD),
            )
            if paramset_key == ParamsetKey.VALUES
            else ((model_l, channel_no),)
        )

        for ml, cno in search_matrix:
            if (
                (custom_un_ignore := self._custom_un_ignore_complex)
                and (channel_values := custom_un_ignore.get(ml))
                and (paramset_key_values := channel_values.get(cno))
                and parameter in paramset_key_values.get(paramset_key, set())
            ):
                return True  # pragma: no cover

        # check if parameter is in _UN_IGNORE_PARAMETERS_BY_DEVICE
        return bool(
            not custom_only
            and (
                un_ignore_parameters := _get_value_from_dict_by_wildcard_key(
                    search_elements=self._un_ignore_parameters_by_device_lower,
                    compare_with=model_l,
                )
            )
            and parameter in un_ignore_parameters
        )

    @lru_cache(maxsize=4096)
    def parameter_is_un_ignored(
        self,
        model: str,
        channel_no: int | None,
        paramset_key: ParamsetKey,
        parameter: str,
        custom_only: bool = False,
    ) -> bool:
        """
        Return if parameter is on an un_ignore list.

        Additionally to _parameter_is_un_ignored these parameters
        from _RELEVANT_MASTER_PARAMSETS_BY_DEVICE are un ignored.
        """
        if not custom_only:
            dt_short = tuple(
                filter(
                    model.lower().startswith,
                    self._un_ignore_parameters_by_device_paramset_key,
                )
            )

            # check if parameter is in _RELEVANT_MASTER_PARAMSETS_BY_DEVICE
            if dt_short and parameter in self._un_ignore_parameters_by_device_paramset_key.get(
                dt_short[0], {}
            ).get(channel_no, {}).get(paramset_key, set()):
                return True

        return self._parameter_is_un_ignored(
            model=model,
            channel_no=channel_no,
            paramset_key=paramset_key,
            parameter=parameter,
            custom_only=custom_only,
        )

    def _add_line_to_cache(self, line: str) -> None:
        """Add line to from un ignore file to cache."""

        # ignore empty line
        if not line.strip():
            return

        if line.lower().startswith(_IGNORE_MODEL):
            self._ignore_custom_.append(line.lower().replace(_IGNORE_MODEL, ""))
            return

        if line_details := self._get_un_ignore_line_details(line=line):
            if isinstance(line_details, str):
                self._custom_un_ignore_values_parameters.add(line_details)
                return

            self._add_complex_un_ignore_entry(
                model=line_details[0],
                channel_no=line_details[1],
                parameter=line_details[2],
                paramset_key=line_details[3],
            )
        else:
            _LOGGER.warning(
                "ADD_LINE_TO_CACHE failed: No supported format detected for un ignore line '%s'. ",
                line,
            )

    def _get_un_ignore_line_details(
        self, line: str
    ) -> tuple[str, int | str | None, str, ParamsetKey] | str | None:
        """
        Check the format of the line for un_ignore file.

        model, channel_no, paramset_key, parameter
        """

        model: str | None = None
        channel_no: int | str | None = None
        paramset_key: ParamsetKey | None = None
        parameter: str | None = None

        if "@" in line:
            data = line.split("@")
            if len(data) == 2:
                if ":" in data[0]:
                    param_data = data[0].split(":")
                    if len(param_data) == 2:
                        parameter = param_data[0]
                        paramset_key = ParamsetKey(param_data[1])
                    else:
                        _LOGGER.warning(
                            "GET_UN_IGNORE_LINE_DETAILS failed: Could not add line '%s' to un ignore cache. "
                            "Only one ':' expected in param_data",
                            line,
                        )
                        return None
                else:
                    _LOGGER.warning(
                        "GET_UN_IGNORE_LINE_DETAILS failed: Could not add line '%s' to un ignore cache. "
                        "No ':' before '@'",
                        line,
                    )
                    return None
                if ":" in data[1]:
                    channel_data = data[1].split(":")
                    if len(channel_data) == 2:
                        model = channel_data[0].lower()
                        _channel_no = channel_data[1]
                        channel_no = (
                            int(_channel_no)
                            if _channel_no.isnumeric()
                            else None
                            if _channel_no == ""
                            else _channel_no
                        )
                    else:
                        _LOGGER.warning(
                            "GET_UN_IGNORE_LINE_DETAILS failed: Could not add line '%s' to un ignore cache. "
                            "Only one ':' expected in channel_data",
                            line,
                        )
                        return None
                else:
                    _LOGGER.warning(
                        "GET_UN_IGNORE_LINE_DETAILS failed: Could not add line '%s' to un ignore cache. "
                        "No ':' after '@'",
                        line,
                    )
                    return None
            else:
                _LOGGER.warning(
                    "GET_UN_IGNORE_LINE_DETAILS failed: Could not add line '%s' to un ignore cache. "
                    "Only one @ expected",
                    line,
                )
                return None
        elif ":" in line:
            _LOGGER.warning(
                "GET_UN_IGNORE_LINE_DETAILS failed: No supported format detected for un ignore line '%s'. ",
                line,
            )
            return None
        if (
            model == UN_IGNORE_WILDCARD
            and channel_no == UN_IGNORE_WILDCARD
            and paramset_key == ParamsetKey.VALUES
        ):
            return parameter
        if model is not None and parameter is not None and paramset_key is not None:
            return model, channel_no, parameter, paramset_key
        return line

    def _add_complex_un_ignore_entry(
        self,
        model: str,
        channel_no: int | str | None,
        paramset_key: ParamsetKey,
        parameter: str,
    ) -> None:
        """Add line to un ignore cache."""
        if paramset_key == ParamsetKey.MASTER:
            if isinstance(channel_no, int) or channel_no is None:
                # add master channel for a device to fetch paramset descriptions
                if model not in self._relevant_master_paramsets_by_device:
                    self._relevant_master_paramsets_by_device[model] = set()
                self._relevant_master_paramsets_by_device[model].add(channel_no)
            else:
                _LOGGER.warning(
                    "ADD_UN_IGNORE_ENTRY: channel_no '%s' must be an integer or None for paramset_key MASTER.",
                    channel_no,
                )
                return
            if model == UN_IGNORE_WILDCARD:
                _LOGGER.warning("ADD_UN_IGNORE_ENTRY: model must be set for paramset_key MASTER.")
                return

            # model, channel_no, paramset_key, parameter
        if model not in self._custom_un_ignore_complex:
            self._custom_un_ignore_complex[model] = {}
        if channel_no not in self._custom_un_ignore_complex[model]:
            self._custom_un_ignore_complex[model][channel_no] = {}
        if paramset_key not in self._custom_un_ignore_complex[model][channel_no]:
            self._custom_un_ignore_complex[model][channel_no][paramset_key] = set()
        self._custom_un_ignore_complex[model][channel_no][paramset_key].add(parameter)

    @lru_cache(maxsize=1024)
    def parameter_is_hidden(
        self,
        model: str,
        channel_no: int | None,
        paramset_key: ParamsetKey,
        parameter: str,
    ) -> bool:
        """
        Return if parameter should be hidden.

        This is required to determine the data_point usage.
        Return only hidden parameters, that are no defined in the un_ignore file.
        """
        return parameter in _HIDDEN_PARAMETERS and not self._parameter_is_un_ignored(
            model=model,
            channel_no=channel_no,
            paramset_key=paramset_key,
            parameter=parameter,
        )

    def is_relevant_paramset(
        self,
        model: str,
        paramset_key: ParamsetKey,
        channel_no: int | None,
    ) -> bool:
        """
        Return if a paramset is relevant.

        Required to load MASTER paramsets, which are not initialized by default.
        """
        if paramset_key == ParamsetKey.VALUES:
            return True
        if paramset_key == ParamsetKey.MASTER:
            for (
                d_type,
                channel_nos,
            ) in self._relevant_master_paramsets_by_device.items():
                if channel_no in channel_nos and hms.element_matches_key(
                    search_elements=d_type,
                    compare_with=model,
                ):
                    return True
        return False

    async def load(self) -> None:
        """Load custom un ignore parameters from disk."""

        def _load() -> None:
            if not hms.check_or_create_directory(self._storage_folder):
                return  # pragma: no cover
            if not os.path.exists(
                os.path.join(self._storage_folder, _FILE_CUSTOM_UN_IGNORE_PARAMETERS)
            ):
                _LOGGER.debug(
                    "LOAD: No file found in %s",
                    self._storage_folder,
                )
                return

            try:
                with open(
                    file=os.path.join(
                        self._storage_folder,
                        _FILE_CUSTOM_UN_IGNORE_PARAMETERS,
                    ),
                    encoding=UTF8,
                ) as fptr:
                    for file_line in fptr.readlines():
                        if "#" not in file_line:
                            self._raw_un_ignore_list.add(file_line.strip())
            except Exception as ex:
                _LOGGER.warning(
                    "LOAD failed: Could not read un_ignore file %s",
                    reduce_args(args=ex.args),
                )

        if self._central.config.load_un_ignore:
            await self._central.looper.async_add_executor_job(_load, name="load-un_ignore-file")

        for line in self._raw_un_ignore_list:
            if "#" not in line:
                self._add_line_to_cache(line)


def check_ignore_parameters_is_clean() -> bool:
    """Check if a required parameter is in ignored parameters."""
    un_ignore_parameters_by_device: list[str] = []
    for params in _UN_IGNORE_PARAMETERS_BY_DEVICE.values():
        un_ignore_parameters_by_device.extend(params)

    return (
        len(
            [
                parameter
                for parameter in get_required_parameters()
                if (
                    parameter in _IGNORED_PARAMETERS
                    or parameter.endswith(tuple(_IGNORED_PARAMETERS_WILDCARDS_END))
                    or parameter.startswith(tuple(_IGNORED_PARAMETERS_WILDCARDS_START))
                )
                and parameter not in un_ignore_parameters_by_device
            ]
        )
        == 0
    )


def _get_value_from_dict_by_wildcard_key(
    search_elements: Mapping[str, Any],
    compare_with: str | None,
    do_wildcard_search: bool = True,
) -> Any | None:
    """Return the dict value by wildcard type."""
    if compare_with is None:
        return None

    for key, value in search_elements.items():
        if do_wildcard_search:
            if key.lower().startswith(compare_with.lower()):
                return value
        elif key.lower() == compare_with.lower():
            return value
    return None
