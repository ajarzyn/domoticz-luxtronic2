# Luxtronic2 plugin based on sockets
# Author: ajarzyna, 2021
"""
<plugin key="LUXT2" name="Luxtronic2 based on sockets." author="ajarzyn" version="0.0.3">
    <description>
        <h2>Luxtronic2 based on sockets.</h2><br/>
        Be aware:
         Values greater than 30 seconds will cause a message to be regularly logged about the plugin not responding.
         The plugin will actually function correctly with values greater than 30 though.
    </description>
    <params>
        <param field="Address" label="luxtronic2 IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="luxtronic2 Port" width="30px" required="true" default="8889"/>

        <param field="Mode2" label="Data pull interval in seconds" width="150px" default="25"/>
        <param field="Mode3" label="Lang" width="150px">
            <options>
                <option label="English" value="0" default="true"/>
                <option label="Polish" value="1"/>
                <option label="Dutch" value="2"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0" default="true"/>
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import socket
import struct


_IDS = {
    'Heating supply temperature': [
        'Temperatura zasilania',
        'Temperatuur aanvoer'
    ],
    'Heating return temperature': [
        'Temperatura powrótu',
        'Temperatuur retour',
    ],
    'Heating return temperature - target': [
        'Temperatura powrótu - cel',
        'Retour berekend'
    ],
    'Outside temperature': [
        'Temperatura zewnętrzna',
        'Buitentemperatuur'
    ],
    'Outside temperature - average': [
        'Temperatura zewnętrzna - średnia',
        'Buitentemperatuur - gemiddeld'
    ],
    'Hot water temperature': [
        'Temperatura cwu',
        'Tapwater gemeten'
    ],
    'Hot water temperature - target': [
        'Temperatura cwu - cel',
        'Tapwater ingesteld'
    ],
    'Ground source temperature - in': [
        'Temperatura dolne źródło-wejście',
        'Bron-in'
    ],
    'Ground source temperature - out': [
        'Temperatura dolne źródło-wyjście',
        'Bron-uit'
    ],
    'OM 1 Temperature': [
        'Temperatura zasilanie OM 1',
        'Menggroep1 aanvoer'
    ],
    'OM 1 Temperature - target': [
        'Temperatura zasilanie OM 1 - cel',
        'Menggroep1 aanvoer ingesteld'
    ],
    'Heating mode': [
        'Obieg grzewczy',
        'Verwarmingsbedrijf'
    ],
    'Hot water mode': [
        'Woda użytkowa',
        'Warmwater'
    ],
    'Cooling': [
        'Chłodzenie',
        'Koelbedrijf'
    ],
    'Operating time': [
        'Czas pracy',
        'Bedrijfstijd Verdichter 1'
    ],
    'Cycles': [
        'Cykli',
        'Impuls VD1'
    ],
    'Energy produced - heating': [
        'Energia wyprodukowana - ogrzewanie',
        'Verbruik verwarmen'
    ],
    'Energy produced - hot water': [
        'Energia wyprodukowana - c.w.u',
        'Verbruik warmwater'
    ],
    'Energy produced - sum': [
        'Energia wyprodukowana - Razem',
        'Verbruik gezamelijk'
    ],
    'Automat.|2nd h. source|Party|Holidays|Off': [
        'Automat.|II źr. ciepła|Party|Wakacje|Wył.',
        'Automatisch|2e warm.opwek|Party|Vakantie|Uit',
    ],
    'No requirement': [
        'Brak zapotrzebowania',
        'Geen vraag',
    ],
    'Working mode': [
        'Stan pracy',
        'Bedrijfsmode'
    ],
    'Swimming pool mode / Photovaltaik': [
        'Tryb basen / Fotowoltaika',
        'Zwembad / Fotovoltaïek'
        ],
    'EVUM': [
        'EVU',
        'EVU'
        ],
    'Defrost': [
        'Rozmrażanie',
        'Ontdooien'
        ],
    'Heating external source mode': [
        'Ogrzewanie z zewnętrznego źródła',
        'Verwarmen 2e warm.opwek'
        ],
    'Flow': [
        'Przepływ',
        'Debiet'
    ],
    'Compressor frequency': [
        'Częstotliwość sprężarki',
        'Freq. '
    ],
    'Temperature +-': [
        'Temperatura +-',
        '[DE]Temperature +-. '
    ],
    'Actual room temperature': [
        'Temperatura pokojowa',
        'Raumtemperatur Ist. '
    ],
    'Room temperature set': [
        'Temperatura pokojowa - cel',
        'Raumtemperatur Soll'
    ]
}


# Read callbacks
def to_float(data_list: list, data_idx: int, divider: float) -> dict:
    converted = float(data_list[data_idx] / divider)
    return {'sValue': str(converted)}


def to_number(data_list: list, data_idx: int, divider: float = 1.0) -> dict:
    converted = float(data_list[data_idx] / divider)
    return {'nValue': int(converted)}


def selector_switch_level_mapping(data_list: list, data_idx: int, mapping: list) -> dict:
    level = mapping.index(data_list[data_idx]) * 10
    return {'nValue': int(level), 'sValue': str(level)}


def to_power_counter(data_list: list, cumulative_power_data_idx: int, additional_data_list: list) -> dict:
    power_sum_div, power_curr_data_idx, power_curr_div, state_curr_data_idx, acceptable_state = additional_data_list
    sum_of_power = str(float(data_list[cumulative_power_data_idx] / power_sum_div))
    if int(data_list[state_curr_data_idx]) in acceptable_state:
        current_power = str(float(data_list[power_curr_data_idx] / power_curr_div))
        return {'sValue': f"{current_power};{sum_of_power}"}
    else:
        return {'sValue': f"0;{sum_of_power}"}


def to_alert(data_list: list, data_idx: int, mapping: list) -> dict:
    Domoticz.Debug(str(data_list[data_idx]) + " " + str(mapping))
    return {'nValue': int(mapping[data_list[data_idx]][0]), 'sValue': str(mapping[data_list[data_idx]][1])}


# Write callbacks
def command_to_number(*_args, Command: str, **_kwargs):
    return 1 if Command == 'On' else 0


def available_writes_level_with_divider(write_data_list: list, *_args,
                                        available_writes, Level, **_kwargs):
    divider, available_writes_idx = write_data_list
    return available_writes[available_writes_idx].get_val()[int(Level / divider)]


def ids(text):
    return _IDS[text][int(Parameters["Mode3"])-1] if int(Parameters["Mode3"]) else text


class Field:
    def __init__(self, *args, **kwargs):
        if len(args) == len(kwargs) == 0:
            self.name = 'Unknown'
            self.vales = []
        else:
            self.name, self.vales = args

    def get_name(self):
        return self.name

    def get_val(self):
        return self.vales


SOCKET_COMMANDS = {
    'WRIT_PARAMS': 3002,
    'READ_PARAMS': 3003,
    'READ_CALCUL': 3004,
    'READ_VISIBI': 3005
}


class BasePlugin:
    def __init__(self):
        self.active_connection = None
        self.name = None
        self.host = None
        self.port = None

        self.devices_parameters_list = []

        self.units = {}
        self.available_writes = {}
        self.dev_lists = {}
        for command in SOCKET_COMMANDS.keys():
            self.dev_lists[command] = {}

    def prepare_devices_list(self):
        self.available_writes = {
            -1: Field(),
            1: Field(ids('Temperature +-'), [a for a in range(-50, 51, 5)]),
            3: Field(ids('Heating mode'), [0, 1, 2, 3, 4]),
            4: Field(ids('Hot water mode'), [0, 1, 2, 3, 4]),
            105: Field(ids('Hot water temperature - target'), [a for a in range(300, 651, 5)]),
            108: Field(ids('Cooling'), [0, 1])
        }

        work_modes_mapping = [(3, ids('Heating mode')),
                              (4, ids('Hot water mode')),
                              (2, ids('Swimming pool mode / Photovaltaik')),
                              (2, ids('EVUM')),
                              (1, ids('Defrost')),
                              (0, ids('No requirement')),
                              (4, ids('Heating external source mode')),
                              (1, ids('Cooling'))]

        hot_water_temps = '|'.join([str(a / 10) for a in self.available_writes[105].get_val()])
        heating_temps = '|'.join([str(a / 10) for a in self.available_writes[1].get_val()])

        self.devices_parameters_list = [
            # 0 Data group/socket command,
            # 1 idx in returned data,
            # 2 tuple(data modification callback, list of additional read data (conversion, indexes, relates)),
            # 3 Domoticz devices dictionary options,
            # 4 Name of the domoticz device,
            # 5 tuple(write callback, list of additional write needed data (conversion, indexes))
            ['READ_CALCUL', 10, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Heating supply temperature')],

            ['READ_CALCUL', 11, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Heating return temperature')],

            ['READ_CALCUL', 12, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Heating return temperature - target')],

            ['READ_CALCUL', 15, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Outside temperature')],

            ['READ_CALCUL', 16, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Outside temperature - average')],

            ['READ_CALCUL', 17, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Hot water temperature')],

            ['READ_CALCUL', 19, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Ground source temperature - in')],

            ['READ_CALCUL', 20, (to_float, 10),
             dict(TypeName='Temperature', Used=1), ids('Ground source temperature - out')],

            ['READ_CALCUL', 21, (to_float, 10),
             dict(TypeName='Temperature', Used=0), ids('OM 1 Temperature')],

            ['READ_CALCUL', 22, (to_float, 10),
             dict(TypeName='Temperature', Used=0), ids('OM 1 Temperature - target')],

            ['READ_CALCUL', 151, (to_power_counter, [1/100, 257, 1, 80, [0]]),
             dict(TypeName='kWh', Used=1), ids('Energy produced - heating')],

            ['READ_CALCUL', 152, (to_power_counter, [1/100, 257, 1, 80, [1]]),
             dict(TypeName='kWh', Used=1), ids('Energy produced - hot water')],

            ['READ_CALCUL', 154, (to_power_counter, [1/100, 257, 1, 80, [0, 1]]),
             dict(TypeName='kWh', Used=1), ids('Energy produced - sum')],

            ['READ_PARAMS', 3, (selector_switch_level_mapping, self.available_writes[3].get_val()),
             dict(TypeName='Selector Switch', Image=7, Used=1,
                  Options={'LevelActions': '|||||',
                           'LevelNames': ids('Automat.|2nd h. source|Party|Holidays|Off'),
                           'LevelOffHidden': 'false',
                           'SelectorStyle': '1'}),
             ids('Heating mode'), (available_writes_level_with_divider, [10, 3])],

            ['READ_PARAMS', 4, (selector_switch_level_mapping, self.available_writes[4].get_val()),
             dict(TypeName='Selector Switch', Image=7, Used=1,
                  Options={'LevelActions': '|||||',
                           'LevelNames': ids('Automat.|2nd h. source|Party|Holidays|Off'),
                           'LevelOffHidden': 'false',
                           'SelectorStyle': '1'}),
             ids('Hot water mode'), (available_writes_level_with_divider, [10, 4])],

            ['READ_PARAMS', 108, [to_number],
             dict(TypeName='Switch', Image=9, Used=0), ids('Cooling'), [command_to_number]],

            # TODO: To be changed into thermostat: ['READ_PARAMS', 1, (to_float, [10]),
            #  dict(Type=242, Subtype=1, Used=1), IDS('Temperature +-'), 'WRIT_PARAMS'],
            ['READ_PARAMS', 1, (selector_switch_level_mapping, self.available_writes[1].get_val()),
             dict(TypeName='Selector Switch', Used=1,
                  Options={'LevelActions': heating_temps.count('|'),
                           'LevelNames': heating_temps,
                           'LevelOffHidden': 'true',
                           'SelectorStyle': '1'}),
             ids('Temperature +-'), (available_writes_level_with_divider, [10, 1])],

            # TODO: To be changed into thermostat: ['READ_PARAMS', 105, (to_float, [10]),
            #  dict(Type=242, Subtype=1, Used=1), IDS('Hot water temperature - target'), 'WRIT_PARAMS'],
            ['READ_PARAMS', 105, (selector_switch_level_mapping, self.available_writes[105].get_val()),
             dict(TypeName='Selector Switch', Used=1,
                  Options={'LevelActions': hot_water_temps.count('|'),
                           'LevelNames': hot_water_temps,
                           'LevelOffHidden': 'true',
                           'SelectorStyle': '1'}),
             ids('Hot water temperature - target'), (available_writes_level_with_divider, [10, 105])],

            ['READ_CALCUL', 80, (to_alert, work_modes_mapping),
             dict(TypeName='Alert', Image=15, Used=1), ids('Working mode')],

            ['READ_CALCUL', 173, (to_float, 1),
             dict(TypeName='Custom', Used=1, Options={'Custom': '1;l/h'}), ids('Flow')],

            ['READ_CALCUL', 231, (to_float, 1),
             dict(TypeName='Custom', Used=0, Options={'Custom': '1;Hz'}), ids('Compressor frequency')],

            ['READ_CALCUL', 227, (to_float, 10),
             dict(TypeName='Temperature', Used=0), ids('Actual room temperature')],

            ['READ_CALCUL', 228, (to_float, 10),
             dict(TypeName='Temperature', Used=0), ids('Room temperature set')],

            # ['READ_CALCUL', 56, 'time', dict(), IDS('Operating time')],
            # ['READ_CALCUL', 57, 1, dict(TypeName='Temperature', Used=1), IDS('Cycles')],
            # ['READ_CALCUL', 22, 10, dict(TypeName='Temperature', Used=1), IDS('')],
            # ['READ_CALCUL', 22, 10, dict(TypeName='Temperature', Used=1), IDS('')],
        ]

        class Unit:
            def __init__(self, domoticz_id, message, address, read_conversion, dev_params, name, write_conversion=None):
                self.id = domoticz_id
                self.message = message
                self.address = address
                self.data_conversion_callback, *self._read_args = read_conversion

                self.dev_params = dev_params
                self.name = name
                if write_conversion is not None:
                    self.write_conversion_callback, *self._write_args = write_conversion
                else:
                    self.write_conversion_callback = write_conversion

            def update_domoticz_dev(self, data_list):
                update_device(Unit=self.id, **self.data_conversion_callback(data_list, self.address, *self._read_args))

            def prepare_data_to_send(self, **kwargs):
                return ('WRIT_PARAMS', self.address,
                        self.write_conversion_callback(*self._write_args, **kwargs))

        for dev_idx in range(len(self.devices_parameters_list)):
            tmp_unit = Unit(dev_idx + 1, *self.devices_parameters_list[dev_idx])
            tmp_unit.dev_params.update(dict(Name=tmp_unit.name, Unit=tmp_unit.id))

            self.units[tmp_unit.name] = tmp_unit
            self.dev_lists[tmp_unit.message][tmp_unit.id] = tmp_unit
            if tmp_unit.write_conversion_callback is not None:
                self.dev_lists['WRIT_PARAMS'][tmp_unit.id] = tmp_unit

    def create_devices(self):
        self.prepare_devices_list()
        for unit in self.units.values():
            if unit.id not in Devices:
                Domoticz.Device(**unit.dev_params).Create()

            else:
                # Do not change "Used" option which can be set by user.
                update_params = unit.dev_params
                update_params.pop('Used', None)
                update_device(**update_params)

    def initialize_connection(self):
        self.active_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.active_connection.connect((self.host, int(self.port)))
            return True
        except OSError as msg:
            self.active_connection.close()
            Domoticz.Error(f"Connection failed, check ip. Error: str({msg})")
            return False

    def send_message(self, command, address, value):
        if self.initialize_connection() is False:
            return

        self.active_connection.send(struct.pack('!i', command))
        self.active_connection.send(struct.pack('!i', address))
        if command == SOCKET_COMMANDS['WRIT_PARAMS']:
            Domoticz.Debug(f"SendMessage {command} {address} {value}")
            self.active_connection.send(struct.pack('!i', value))
        if struct.unpack('!i', self.active_connection.recv(4))[0] != command:
            Domoticz.Debug("Error: REQ_CALCULATED CMD")
            return None

        length = 0
        stat = 0

        if command == SOCKET_COMMANDS['READ_PARAMS']:
            length = struct.unpack('!i', self.active_connection.recv(4))[0]
        elif command == SOCKET_COMMANDS['READ_CALCUL']:
            stat = struct.unpack('!i', self.active_connection.recv(4))[0]
            length = struct.unpack('!i', self.active_connection.recv(4))[0]
        elif command == SOCKET_COMMANDS['READ_VISIBI']:
            pass
        elif command == SOCKET_COMMANDS['WRIT_PARAMS']:
            pass

        data_list = []

        for i in range(length):
            data_list.append(struct.unpack('!i', self.active_connection.recv(4))[0])

        self.active_connection.close()
        return command, stat, length, data_list

    def process_socket_message(self, command='READ_PARAMS', address=0, value=0):
        if command is 'WRIT_PARAMS':
            if value not in self.available_writes[address].get_val():
                Domoticz.Error(f"Incorrect value for {self.available_writes[address].get_name()} value: {value}"
                               f"but avaialble writables are: {self.available_writes[address].get_val()} for {address}")
                return
        else:
            address = 0
            value = 0

        raw_data = command, 0, 0, 0
        try:
            raw_data = self.send_message(SOCKET_COMMANDS[command], address, value)
        except socket.error:
            if self.initialize_connection():
                raw_data = self.send_message(SOCKET_COMMANDS[command], address, value)

        return raw_data

    def update(self, message):
        command, stat, data_length, data_list = self.process_socket_message(message)
        if data_length > 0:
            for device in self.dev_lists[message].values():
                device.update_domoticz_dev(data_list)

    def update_all(self):
        self.update('READ_CALCUL')
        self.update('READ_PARAMS')

    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            dump_config_to_log()

        self.name = Parameters['Name']
        self.host = Parameters['Address']
        self.port = Parameters['Port']

        Domoticz.Heartbeat(int(Parameters['Mode2']))

        self.create_devices()

        if self.initialize_connection() is False:
            return

        self.update_all()

    def onStop(self):
        Domoticz.Debug("onStop - Plugin is stopping.")
        self.active_connection.close()
        self.active_connection = None

    def onDisconnect(self, Connection):
        Domoticz.Debug(f"onDisconnect called for connection to: {Connection.Address}:{Connection.Port}")

    def onConnect(self, Connection, status, Description):
        Domoticz.Debug(f"onConnect called for connection to: {Connection.Address}:{Connection.Port}")

    def onMessage(self, Connection, Data):
        Domoticz.Debug(f"onMessage called for connection to: {Connection.Address}:{Connection.Port}")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(f"onCommand called for Unit:{str(Unit)} Command:{str(Command)} Level: {str(Level)}")

        argument_list = locals()
        argument_list.pop('self', None)

        self.process_socket_message(
            *self.dev_lists['WRIT_PARAMS'][Unit].prepare_data_to_send(
                available_writes=self.available_writes,
                **argument_list))
        self.update('READ_PARAMS')

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called.")
        self.update_all()


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


def update_device(Unit: int = None, nValue: int = None, sValue: str = None, Image: int = None, SignalLevel: int = None,
                  BatteryLevel: int = None, Options: dict = None, TimedOut: int = None, Name: str = None,
                  TypeName: str = None, Type: int = None, Subtype: int = None, Switchtype: int = None,
                  Used: int = None, Description: str = None, Color: str = None, SuppressTriggers: int = None):

    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit not in Devices:
        global _plugin
        _plugin.create_devices()

    args = {}
    update_needed = False

    # Must always be passed for update
    args["nValue"] = 0
    if nValue is not None:
        args["nValue"] = nValue
        update_needed = True
    elif Devices[Unit].nValue is not None:
        args["nValue"] = Devices[Unit].nValue

    if sValue is not None:
        args["sValue"] = sValue
        update_needed = True
    else:
        args["sValue"] = Devices[Unit].sValue

    if TypeName:
        pass
        Devices[Unit].Update(TypeName=TypeName)

    if Image is not None and Image != Devices[Unit].Image:
        args["Image"] = Image
    if SignalLevel is not None and SignalLevel != Devices[Unit].SignalLevel:
        args["SignalLevel"] = SignalLevel
    if BatteryLevel is not None and BatteryLevel != Devices[Unit].BatteryLevel:
        args["BatteryLevel"] = BatteryLevel
    if Options is not None and Options != Devices[Unit].Options:
        args["Options"] = Options
    if TimedOut is not None and TimedOut != Devices[Unit].TimedOut:
        args["TimedOut"] = TimedOut
    if Name is not None and Name != Devices[Unit].Name:
        args["Name"] = Name
    if Type is not None and Type != Devices[Unit].Type:
        args["Type"] = Type
    if Subtype is not None and Subtype != Devices[Unit].Subtype:
        args["Subtype"] = Subtype
    if Switchtype is not None and Switchtype != Devices[Unit].Switchtype:
        args["Switchtype"] = Switchtype
    if Used is not None and Used != Devices[Unit].Used:
        args["Used"] = Used
    if Description is not None and Description != Devices[Unit].Description:
        args["Description"] = Description
    if Color is not None and Color != Devices[Unit].Color:
        args["Color"] = Color
    if SuppressTriggers is not None and SuppressTriggers != Devices[Unit].SuppressTriggers:
        args["SuppressTriggers"] = SuppressTriggers

    if len(args) > 2:
        update_needed = True

    if update_needed:
        Domoticz.Debug(f"update_device unit: {str(Unit)} Name: {Devices[Unit].Name} with parameters: {str(args)}")
        Devices[Unit].Update(**args)


# Generic helper functions
def dump_config_to_log():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug(f"'{x}':'{str(Parameters[x])}'")
    Domoticz.Debug(f"Device count: {str(len(Devices))}")
    for x in Devices:
        Domoticz.Debug(f"Device:           {str(x)} - {str(Devices[x])} ")
        Domoticz.Debug(f"Device ID:       '{str(Devices[x].ID)}'        ")
        Domoticz.Debug(f"Device Name:     '{Devices[x].Name}'           ")
        Domoticz.Debug(f"Device nValue:    {str(Devices[x].nValue)}     ")
        Domoticz.Debug(f"Device sValue:   '{Devices[x].sValue}'         ")
        Domoticz.Debug(f"Device LastLevel: {str(Devices[x].LastLevel)}  ")
    return
