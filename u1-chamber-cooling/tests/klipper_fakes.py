# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
"""Just enough of Klipper to load u1_chamber_cooling, matched to Snapmaker's u1-klipper."""


class ConfigError(Exception):
    pass


class FakeConfig:
    """One cfg section; getchoice raises on a value outside the choices, as configfile.py does."""

    def __init__(self, printer, options):
        self.printer = printer
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

    def get_int(self, name, default):
        raw_value = self.params.get(name)
        if raw_value is None:
            return default
        return int(raw_value)

    def respond_info(self, message):
        self.gcode.respond_info(message)


def parse_extended_commandline(commandline):
    """Split "SET_PURIFIER_MODE MODE=1 FAN_SPEED=0.6" into a command name and its parameters."""
    command_name, *words = commandline.split()
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
        command_name, params = parse_extended_commandline(commandline)
        gcmd = self.create_gcode_command(command_name, commandline, params)
        self.ready_gcode_handlers[command_name](gcmd)

    def respond_info(self, message):
        self.responses.append("// " + message)


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


class FakePrinter:
    def __init__(self):
        self.gcode = FakeGCode()
        self.event_handlers = {}
        self.config_error = ConfigError
        self.objects = {"gcode": self.gcode}

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
