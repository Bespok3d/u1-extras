# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
"""Just enough of Klipper to load u1_top_cover, matched to Snapmaker's u1-klipper."""

import operator

REACTOR_START_TIME = 100.
FULL_SPEED = 1.
# purifier.py treats any speed below this as off.
OFF_SPEED_LIMIT = 0.0001
SHORTEST_TURN_OFF_DELAY_SECONDS = 1
PURIFIER_MODE_IDLE = 0


class CommandError(Exception):
    pass


class ConfigError(Exception):
    pass


class FakeConfig:
    """One cfg section; getchoice raises on a value outside the choices, as configfile.py does."""

    def __init__(self, printer, section_name, options):
        self.printer = printer
        self.section_name = section_name
        self.options = options

    def get_printer(self):
        return self.printer

    def get(self, option):
        return self.options[option]

    def getchoice(self, option, choices):
        choice = self.options[option]
        if choice not in choices:
            raise ConfigError(f"Choice '{choice}' for option '{option}' is not a valid choice")
        return choices[choice]


class FakeTimer:
    def __init__(self, callback, waketime):
        self.callback = callback
        self.waketime = waketime


class FakeReactor:
    """A reactor on a simulated clock: time only moves when a test advances it."""

    NEVER = 9999999999999999.

    def __init__(self):
        self.clock = REACTOR_START_TIME
        self.timers = []

    def monotonic(self):
        return self.clock

    def register_timer(self, callback, waketime=NEVER):
        timer = FakeTimer(callback, waketime)
        self.timers.append(timer)
        return timer

    def update_timer(self, timer, waketime):
        timer.waketime = waketime

    def advance(self, seconds):
        """Run every timer that falls due in the next seconds, in time order."""
        end_time = self.clock + seconds
        due_timer = self._next_due_timer(end_time)
        while due_timer is not None:
            self.clock = max(self.clock, due_timer.waketime)
            due_timer.waketime = due_timer.callback(self.clock)
            due_timer = self._next_due_timer(end_time)
        self.clock = end_time

    def _next_due_timer(self, end_time):
        due_timers = [timer for timer in self.timers if timer.waketime <= end_time]
        return min(due_timers, key=operator.attrgetter("waketime"), default=None)


class FakeGCodeCommand:
    def __init__(self, gcode, command, commandline, params):
        self.gcode = gcode
        self.command = command
        self.commandline = commandline
        self.params = params

    def get_command(self):
        return self.command

    def get_commandline(self):
        return self.commandline

    def get_command_parameters(self):
        return self.params

    def get(self, name, default, parser=str, minval=None):
        raw_value = self.params.get(name)
        if raw_value is None:
            return default
        parsed_value = parser(raw_value)
        if minval is not None and parsed_value < minval:
            raise CommandError(
                f"Error on '{self.commandline}': {name} must have minimum of {minval}")
        return parsed_value

    def get_int(self, name, default, minval=None):
        return self.get(name, default, parser=int, minval=minval)

    def get_float(self, name, default, minval=None):
        return self.get(name, default, parser=float, minval=minval)

    def respond_info(self, message):
        self.gcode.respond_info(message)


def is_traditional_gcode(command_name):
    """M106 takes letter parameters, SET_PURIFIER_MODE takes NAME=value ones, as gcode.py splits."""
    return command_name[0].isupper() and command_name[1].isdigit()


def parse_commandline(commandline):
    """Split "M106 P3 S178" or "SET_PURIFIER_MODE MODE=1" into a command name and its parameters."""
    command_name, *words = commandline.split()
    if is_traditional_gcode(command_name):
        return command_name, {word[0]: word[1:] for word in words}
    return command_name, dict(word.upper().split("=", 1) for word in words)


class FakeGCode:
    def __init__(self):
        self.ready_gcode_handlers = {}
        self.responses = []

    def register_command(self, cmd, func):
        if func is None:
            return self.ready_gcode_handlers.pop(cmd, None)
        if cmd in self.ready_gcode_handlers:
            raise ConfigError(f"gcode command {cmd} already registered")
        self.ready_gcode_handlers[cmd] = func
        return None

    def create_gcode_command(self, command, commandline, params):
        return FakeGCodeCommand(self, command, commandline, params)

    def run(self, commandline):
        command_name, params = parse_commandline(commandline)
        gcmd = self.create_gcode_command(command_name, commandline, params)
        self.ready_gcode_handlers[command_name](gcmd)

    def respond_info(self, message):
        self.responses.append("// " + message)


class StockFan:
    """fan.py's M106, recording each command line it was handed."""

    def __init__(self, gcode):
        self.handled_commandlines = []
        gcode.register_command("M106", self.cmd_M106)

    def cmd_M106(self, gcmd):  # noqa: N802 - Klipper's cmd_<COMMAND> naming
        self.handled_commandlines.append(gcmd.commandline)


class StockPurifierMode:
    """purifier.py's SET_PURIFIER_MODE, recording the parameters it was handed."""

    def __init__(self, gcode):
        self.handled_params = []
        self.handled_commandlines = []
        gcode.register_command("SET_PURIFIER_MODE", self.cmd_SET_PURIFIER_MODE)

    def cmd_SET_PURIFIER_MODE(self, gcmd):  # noqa: N802 - Klipper's cmd_<COMMAND> naming
        self.handled_params.append(dict(gcmd.get_command_parameters()))
        self.handled_commandlines.append(gcmd.get_commandline())


class FakeVirtualSdcard:
    def __init__(self, print_file_path):
        self.print_file_path = print_file_path

    def file_path(self):
        return self.print_file_path


class FakePurifier:
    """The exhaust fan side of purifier.py: speed, delayed turn-off, mode and floor."""

    def __init__(self, reactor, power_detected, purifier_mode, stored_delay_seconds):
        self.reactor = reactor
        self.power_detected = power_detected
        self.purifier_mode = purifier_mode
        self.stored_delay_seconds = stored_delay_seconds
        self.exhaust_speed = 0.
        self.exhaust_fan_speed_threshold = 0
        self.exhaust_is_off = True
        self.turn_off_timer = reactor.register_timer(self._turn_off_timer_fired)

    def set_exhaust_fan_speed(self, speed):
        if not self.power_detected and speed > 0:
            return
        self.reactor.update_timer(self.turn_off_timer, self.reactor.NEVER)
        self.exhaust_speed = 0. if speed < OFF_SPEED_LIMIT else min(speed, FULL_SPEED)
        self.exhaust_is_off = self.exhaust_speed == 0.

    def set_exhaust_fan_delay_turn_off(self, delay):
        if self.exhaust_is_off:
            return
        if delay < SHORTEST_TURN_OFF_DELAY_SECONDS:
            self.set_exhaust_fan_speed(0)
            return
        self.reactor.update_timer(self.turn_off_timer, self.reactor.monotonic() + delay)

    def setup_idle_mode(self):
        """SET_PURIFIER_MODE MODE=0, as the stock PRINT_END and CANCEL_PRINT send it."""
        self.exhaust_fan_speed_threshold = 0
        self.set_exhaust_fan_delay_turn_off(self.stored_delay_seconds)
        self.purifier_mode = PURIFIER_MODE_IDLE

    def _turn_off_timer_fired(self, eventtime):
        self.set_exhaust_fan_speed(0)
        return self.reactor.NEVER

    def get_status(self, eventtime):
        return {
            "power_detected": self.power_detected,
            "mode": self.purifier_mode,
            "exhaust_fan": {
                "speed": self.exhaust_speed,
                "delay": self.stored_delay_seconds,
                "speed_threshold": self.exhaust_fan_speed_threshold,
            },
        }


class FakePrinter:
    def __init__(self):
        self.reactor = FakeReactor()
        self.gcode = FakeGCode()
        self.event_handlers = {}
        self.config_error = ConfigError
        self.objects = {"gcode": self.gcode}
        self.shut_down = False

    def config_for(self, section_name, options):
        return FakeConfig(self, section_name, options)

    def get_reactor(self):
        return self.reactor

    def is_shutdown(self):
        return self.shut_down

    def lookup_object(self, name, default=ConfigError):
        if name in self.objects:
            return self.objects[name]
        if default is ConfigError:
            raise ConfigError(f"Unknown config object '{name}'")
        return default

    def register_event_handler(self, event, callback):
        self.event_handlers.setdefault(event, []).append(callback)

    def send_event(self, event):
        for callback in self.event_handlers.get(event, []):
            callback()
