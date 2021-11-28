# Luxtronic2 plugin based on sockets
# Author: ajarzyna, 2021
"""
<plugin key="LUXT2" name="Luxtronic2 based on sockets." author="ajarzyn" version="0.0.1">
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

SOCKET_COMMANDS = {
    'WRIT_PARAMS': 3002,
    'READ_PARAMS': 3003,
    'READ_CALCUL': 3004,
    'READ_VISIBI': 3005
}

class Field:
    def __init__(self):
        self.__int__('Unknown', [])

    def __init__(self, name, values):
        self.name = name
        self.vales = values

    def get_name(self):
        return self.name

    def get_val(self):
        return self.vales

_IDS = {
    "HST": [
        'Heating supply temperature',
        'Temperatura zasilania',
        'Temperatuur aanvoer'
    ],
    "HRT": [
        'Heating return temperature',
        'Temperatura powrótu',
        'Temperatuur retour',
    ],
    "HRTT": [
        'Heating return temperature - target',
        'Temperatura powrótu - cel',
        'Retour berekend'
    ],
    'OT': [
        'Outside temperature',
        'Temperatura zewnętrzna',
        'Buitentemperatuur'
    ],
    'OTA': [
        'Outside temperature - average',
        'Temperatura zewnętrzna - średnia',
        'Buitentemperatuur - gemiddeld'
    ],
    'HWT': [
        'Hot water temperature',
        'Temperatura cwu',
        'Tapwater gemeten'
    ],
    'HWTT': [
        'Hot water temperature - target',
        'Temperatura cwu - cel',
        'Tapwater ingesteld'
    ],
    'GSTI': [
        'Ground source temperature - in',
        'Temperatura dolne źródło-wejście',
        'Bron-in'
    ],
    'GSTO': [
        'Ground source temperature - out',
        'Temperatura dolne źródło-wyjście',
        'Bron-uit'
    ],
    'OM1T': [
        'OM 1 Temperature',
        'Temperatura zasilanie OM 1',
        'Menggroep1 aanvoer'
    ],
    'OM1TT': [
        'OM 1 Temperature - target',
        'Temperatura zasilanie OM 1 - cel',
        'Menggroep1 aanvoer ingesteld'
    ],
    'HM': [
        'Heating mode',
        'Obieg grzewczy',
        'Verwarmingsbedrijf'
    ],
    'HWM': [
        'Hot water mode',
        'Woda użytkowa',
        'Warmwater'
    ],
    'CM': [
        'Cooling',
        'Chłodzenie',
        'Koelbedrijf'
    ],
    'OTC': [
        'Operating time',
        'Czas pracy',
        'Bedrijfstijd Verdichter 1'
    ],
    'CYC': [
        'Cycles',
        'Cykli',
        'Impuls VD1'
    ],

    'EPH': [
        'Energy produced - heating',
        'Energia wyprodukowana - ogrzewanie',
        'Verbruik verwarmen'
    ],
    'EPHW': [
        'Energy produced - hot water',
        'Energia wyprodukowana - c.w.u',
        'Verbruik warmwater'
    ],
    'EPS': [
        'Energy produced - sum',
        'Energia wyprodukowana - Razem',
        'Verbruik gezamelijk'
    ],
    'HWM_OPTIONS': [
        'Automat.|2nd h. source|Party|Holidays|Off',
        'Automat.|II źr. ciepła|Party|Wakacje|Wył.',
        'Automatisch|2e warm.opwek|Party|Vakantie|Uit',
    ],
    'OFF': [
        'No requirement',
        'Brak zapotrzebowania',
        'Geen vraag',
    ],
    'WM': [
        'Working mode',
        'Stan pracy',
        'Bedrijfsmode'
    ],
    'SPM': [
        'Swimming pool mode / Photovaltaik',
        'Tryb basen / Fotowoltaika',
        'Zwembad / Fotovoltaïek'
        ],
    'EVUM': [
        'EVU',
        'EVU',
        'EVU'
        ],
    'DFM': [
        'Defrost',
        'Rozmrażanie',
        'Ontdooien'
        ],
    'HES': [
        'Heating external source mode',
        'Ogrzewanie z zewnętrznego źródła',
        'Verwarmen 2e warm.opwek'
        ]
}


def to_float(data: int, divider: float) -> dict:
    converted = float(data / divider)
    return {'s_value': str(converted)}


def to_switch(data: int, divider: float = 1.0) -> dict:
    converted = float(data / divider)
    return {'n_value': int(converted)}


def to_selector_switch(data: int, divider: float = 1.0) -> dict:
    converted = float(data/divider)
    return {'n_value': int(converted), 's_value': str(converted)}


def mode_to_alert(data: int) -> dict:
    conversion_table = {
        -1: [0, 'UNKNOWN'],
        0: [3, IDS('HM')],  # Heating
        1: [4, IDS('HWM')],
        2: [2, IDS('SPM')],
        3: [2, IDS('EVUM')],
        4: [1, IDS('DFM')],
        5: [0, IDS('OFF')],
        6: [4, IDS('HES')],
        7: [1, IDS('CM')]
    }
    if data not in conversion_table.keys():
        Domoticz.Error(f"Unknown work mode {str(data)}")
        data = -1
    return {'n_value': conversion_table[data][0], 's_value': conversion_table[data][1]}

def IDS(text):
    return _IDS[text][int(Parameters["Mode3"])]

class BasePlugin:
    def __init__(self):
        self.active_connection = None
        self.UNITS = {}

        self.DEV_LISTS = {}
        for command in SOCKET_COMMANDS.keys():
            self.DEV_LISTS[command] = {}

    def PrepareDevicesList(self):
        self.dev_list = [
            # Name, socket command, idx, data modification callback, Domoticz devices options, is writable
            ['READ_CALCUL', 10,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('HST')],
            ['READ_CALCUL', 11,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('HRT')],
            ['READ_CALCUL', 12,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('HRTT')],
            ['READ_CALCUL', 15,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('OT')],
            ['READ_CALCUL', 16,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('OTA')],
            ['READ_CALCUL', 17,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('HWT')],
            ['READ_CALCUL', 18,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('HWTT')],
            ['READ_CALCUL', 19,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('GSTI')],
            ['READ_CALCUL', 20,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('GSTO')],
            ['READ_CALCUL', 21,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('OM1T')],
            ['READ_CALCUL', 22,  (to_float, [10]), dict(TypeName="Temperature", Used=1), IDS('OM1TT')],

            # ['READ_CALCUL', 56, "time", dict(), IDS('OTC')],
            # ['READ_CALCUL', 57, 1, dict(TypeName="Temperature", Used=1), IDS('CYC')],
            # ['READ_CALCUL', 22, 10, dict(TypeName="Temperature", Used=1), IDS('')],
            # ['READ_CALCUL', 22, 10, dict(TypeName="Temperature", Used=1), IDS('')],
            ['READ_CALCUL', 151, (to_float, [10]), dict(TypeName="Counter Incremental", Used=1), IDS('EPH')],
            ['READ_CALCUL', 152, (to_float, [10]), dict(TypeName="Counter Incremental", Used=1), IDS('EPHW')],
            ['READ_CALCUL', 154, (to_float, [10]), dict(TypeName="Counter Incremental", Used=1), IDS('EPS')],



            # Writables
            ['READ_PARAMS', 3, (to_selector_switch, [1/10]), dict(TypeName="Selector Switch", Image=7, Used=1,
                                 Options={"LevelActions": "|||||",
                                          "LevelNames": IDS('HWM_OPTIONS'),
                                          "LevelOffHidden": "false",
                                          "SelectorStyle": "1"}), IDS('HM'), 'WRIT_PARAMS'],
            ['READ_PARAMS', 4, (to_selector_switch, [1/10]), dict(TypeName="Selector Switch", Image=7, Used=1,
                                 Options={"LevelActions": "|||||",
                                          "LevelNames": IDS('HWM_OPTIONS'),
                                          "LevelOffHidden": "false",
                                          "SelectorStyle": "1"}), IDS('HWM'), 'WRIT_PARAMS'],
            ['READ_PARAMS', 108, (to_switch, []), dict(TypeName="Switch", Image=9, Used=1), IDS('CM'), 'WRIT_PARAMS'],

            ['READ_CALCUL', 80, (mode_to_alert, []), dict(TypeName="Alert", Image=15, Used=1), IDS('WM')],
        ]

        class Unit:
            def __init__(self, id, message, address, div_fact, dev_params, name, writ_message=None):
                self.id = id
                self.message = message
                self.address = address
                self.data_callback = div_fact[0]
                self.div_fact = div_fact[1]
                self.dev_params = dev_params
                self.name = name
                self.writ_message = writ_message

            def updateDomoticzDev(self, data_list):
                update_device(unit=self.id, **self.data_callback(data_list[self.address], *self.div_fact))

            def prepareDataToSend(self, data):
                return (self.writ_message, self.address, data)


        for dev_idx in range(len(self.dev_list)):
            tmp_unit = Unit(dev_idx+1, *self.dev_list[dev_idx])
            tmp_unit.dev_params.update(dict(Name=tmp_unit.name, Unit=tmp_unit.id))

            self.UNITS[tmp_unit.name] = tmp_unit
            self.DEV_LISTS[tmp_unit.message][tmp_unit.id] = tmp_unit
            if tmp_unit.writ_message:
                self.DEV_LISTS[tmp_unit.writ_message][tmp_unit.id] = tmp_unit

    def CreateDevices(self):
        for unit in self.UNITS.values():
            if unit.id not in Devices:
                Domoticz.Device(**unit.dev_params).Create()

    def InitializeConnection(self):
        self.active_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.active_connection.connect((self.host, int(self.port)))

    def SendMessage(self, command, address, value):
        self.InitializeConnection()

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

    def ProcessSocketMessage(self, command='READ_PARAMS', address=0, value=0):
        AVAILABLE_WRITES = {
            3: Field(IDS('HM'), [0, 1, 2, 3, 4]),
            4: Field(IDS('HWM'), [0, 1, 2, 3, 4]),
            108: Field(IDS('CM'), [0, 1])
        }

        if command is 'WRIT_PARAMS':
            if value not in AVAILABLE_WRITES[address].get_val():
                Domoticz.Error(f"Incorrect value for {AVAILABLE_WRITES[address].get_name()} value: {value}"
                               f"but avaialble writables are: {AVAILABLE_WRITES[address].get_val()} for {address} ")
                return
        else:
            address = 0
            value = 0

        try:
            raw_data = self.SendMessage(SOCKET_COMMANDS[command], address, value)
        except:
            self.InitializeConnection()
            raw_data = self.SendMessage(SOCKET_COMMANDS[command], address, value)

        return raw_data

    def Update(self, message):
        command, stat, data_length, data_list = self.ProcessSocketMessage(message)
        if data_length > 0:
            for device in self.DEV_LISTS[message].values():
                device.updateDomoticzDev(data_list)

    def UpdateAll(self):
        self.Update('READ_CALCUL')
        self.Update('READ_PARAMS')

    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()

        self.PrepareDevicesList()

        self.name = Parameters['Name']
        self.host = Parameters['Address']
        self.port = Parameters['Port']

        Domoticz.Heartbeat(int(Parameters['Mode2']))

        self.InitializeConnection()

        # Create devices for roomba
        self.CreateDevices()
        self.UpdateAll()

    def onStop(self):
        Domoticz.Debug("onStop - Plugin is stopping.")
        self.active_connection.close()
        self.active_connection = None

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called for connection to: " + Connection.Address + ":" + Connection.Port)

    def onConnect(self, Connection, status, Description):
        Domoticz.Debug("onConnect called for connection to: " + Connection.Address + ":" + Connection.Port)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called for connection to: " + Connection.Address + ":" + Connection.Port)

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        data = Level
        if Unit == self.UNITS[IDS('CM')].id:
            data = 1 if Command == 'On' else 0
        elif Unit == self.UNITS[IDS('HM')].id:
            data = int(Level / 10)
        elif Unit == self.UNITS[IDS('HWM')].id:
            data = int(Level / 10)

        self.ProcessSocketMessage(*self.DEV_LISTS['WRIT_PARAMS'][Unit].prepareDataToSend(data))
        self.Update('READ_PARAMS')

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called.")
        self.UpdateAll()


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


def update_device(unit,
                  n_value=-1, s_value="", image_id=-1, sig_lvl=-1, bat_lvl=-1, opt={}, timed_out=-1, name="",
                  type_name="", type=-1, sub_type=-1, switch_type=-1, used=-1, descr="", color="", supp_trigg=-1):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    Domoticz.Debug("update_device unit:" + str(unit))
    if unit in Devices:
        args = {}
        # Must always be passed for update
        if n_value != -1:
            args["nValue"] = n_value
        else:
            args["nValue"] = Devices[unit].nValue
        s_value = str(s_value)
        if len(s_value) > 0:
            args["sValue"] = s_value
        else:
            args["sValue"] = Devices[unit].sValue

        Domoticz.Debug(str(args))
        # Optionals
        if image_id != -1:
            args["Image"] = image_id
        if sig_lvl != -1:
            args["SignalLevel"] = sig_lvl
        if bat_lvl != -1:
            args["BatteryLevel"] = bat_lvl
        opt = str(opt)
        if len(opt) > 0:
            args["Options"] = opt
        if timed_out != -1:
            args["TimedOut"] = timed_out
        name = str(name)
        if len(name) > 0:
            args["Name"] = name
        type_name = str(type_name)
        if len(type_name) > 0:
            args["TypeName"] = type_name
        if type != -1:
            args["Type"] = type
        if sub_type != -1:
            args["Subtype"] = sub_type
        if switch_type != -1:
            args["Switchtype"] = switch_type
        if used != -1:
            args["Used"] = used
        descr = str(descr)
        if len(descr) > 0:
            args["Description"] = descr
        color = str(color)
        if len(color) > 0:
            args["Color"] = color
        if supp_trigg != -1:
            args["SuppressTriggers"] = supp_trigg
        Domoticz.Debug("Update with " + str(args))
        Devices[unit].Update(**args)
    else:
        global _plugin
        _plugin.CreateDevices()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
