from pydbus import SystemBus
from gi.repository import GLib
from pydbus import SessionBus
from pydbus.generic import signal
from pydbus.generic import bound_signal
import types
import threading
import time
import pickle
import json

from xml.dom import minidom




"""
    Turns out to be a wrapper class around slightly customised pydbus 0.6.0
    Only signals properly function here. Methods, properties, etc need to be accessed via
    that library directly
"""
class IOTC_IPC:

    class DBUSServer(object):

        """
            <node>
                <interface name="org.freedesktop.SignalIface">
                    <signal name="SomethingHappened">
                        <arg direction="out" type="au" name="id"/>
                        <arg direction="out" type="u" name="reason"/>
                        <arg direction="out" type="s" name="text"/>
                        <arg direction="out" type="u" name="another"/>
                    </signal>
                <method name='Hello'>
                    <arg type='s' name='response' direction='out'/>
                </method>
                </interface>
            </node>
        """
        SomethingHappened = signal()


        def Hello(self):
            """returns the string 'Hello, World!'"""
            return "Hello, World!"

        interface = None
        use_custom_xml = False
        def __init__(self, iface: str):
            interface = iface


    class Sender:

        bus = None
        server_obj = None
        loop = None

        _dbus_obj_name = None
        _dbus_iface = None

        def __init__(self, dbus_obj_name: str, dbus_iface: str, *, is_standalone: bool = False, is_system: bool = False):

            if (is_standalone):
                self.loop = GLib.MainLoop()
            self.server_obj = IOTC_IPC.DBUSServer(dbus_iface)

            if is_system:
                self.bus = SystemBus()
            else:
                self.bus = SessionBus()

            self._dbus_obj_name = dbus_obj_name
            self._dbus_iface = dbus_iface


        # TODO: maybe add a way to change parts of xml

        # should be run only after everyting is set up
        def start_server(self, *, standalone = False):
            self.bus.publish(self._dbus_obj_name, self.server_obj, use_xml_var = self.server_obj.use_custom_xml)
            # TODO: loop.run() here?
            # objdetect_tfl.py uses gtk.main loop - maybe glib loop.run not needed in that situation?
            if (standalone):
                self.loop.run()

        def bind_signal(self, new_signal: str):
            # TODO: unfisnished?

            # TODO: DID THIS WORK? this seems to be a weird hack, double check later
            setattr(self.server_obj, new_signal, bound_signal(signal(), self.server_obj))

            # setattr(self.server_obj, new_signal, signal())

            # newattr = getattr(self.server_obj, new_signal)
            # self.server_obj.__dict__[new_signal] = types.MethodType( signal, getattr(self.server_obj, new_signal))

            # another = getattr(self.server_obj, new_signal)
            # print(self.server_obj.__dict__)
            # print("_________________________________")
            # print(getattr(self.server_obj, new_signal))
            # print(getattr(self.server_obj, new_signal).__dict__)
            # help(print(getattr(self.server_obj, new_signal)))

        # TODO: probably need to parse XML here and create signals, args etc
        def change_server_xml(self, new_xml):
            self.server_obj.xml_content = new_xml
            self.server_obj.use_custom_xml = True

        def signal_emit(self, signal: str, *arg):
            getattr(self.server_obj, signal)(*arg)

        # TODO: re-visit as it doesn't work
        def __del__(self):
            if self.loop is not None:
                self.loop.quit()

    class Receiver:

        bus = None
        server_obj = None
        loop = None

        registered_signals = {}

        dbus_types_map = {
            "u": int,
            "au": list,
            "s": str,
            "b": bool
        }

        type_counters = {
            "u": 0,
            "au": 0,
            "s": 0,
            "b": 0
        }

        def __init__(self, dbus_obj_name: str, *, is_standalone: bool = False, is_system: bool = False):

            if (is_standalone):
                self.loop = GLib.MainLoop()

            if is_system:
                self.bus = SystemBus()
            else:
                self.bus = SessionBus()

            self.server_obj = self.bus.get(dbus_obj_name)
                # if (not self.server_obj):
                #     return False
                # return True


        def default_callback(self, *params):
            print(params)
            if (params is not None):
                recvd_json = self.default_parser(*params)
                print(recvd_json)
            else:
                print("Signal with no args")

        def connect_signal(self, signal, callback = default_callback) -> bool:
            try:
                getattr(self.server_obj, signal).connect(callback)
                self.registered_signals[signal] = getattr(self.server_obj, signal).__signal__._args
            except AttributeError:
                print("This dbus service doesn't have signal named " + signal)
                return False
            except:
                print("Unknown error")
                return False
            return True

        def run(self):
            self.loop.run()

        def __del__(self):

            self.loop.quit()


        # better write your own specific handler
        def default_parser(self, *params):

            self.type_counters_offsets = self.type_counters.copy()

            req_signal = None
            for signal in self.registered_signals:
                signal_attributes_mathed_received_params = True
                if (type(self.registered_signals[signal]) == list):
                    for attr_type in self.registered_signals[signal]:
                        found_attr_in_passed_params = False
                        for param in params:
                            #print("signal %s attr type %s param %s" % (signal, attr_type, str(type(param))))
                            if (self.dbus_types_map[attr_type] == type(param)):
                                if (self.type_counters[attr_type] > 0):
                                    self.type_counters[attr_type] -= 1
                                    continue

                                self.type_counters[attr_type] = self.type_counters_offsets[attr_type] + 1

                                self.type_counters_offsets[attr_type] += 1
                                found_attr_in_passed_params = True
                                break
                        if (not found_attr_in_passed_params):
                            signal_attributes_mathed_received_params = False
                            break
                else:
                    print("not list")
                    # TODO?
                if (signal_attributes_mathed_received_params):
                    print("that's our signal: " + signal)
                    req_signal = signal
                    break
                else:
                    for x in self.type_counters:
                        self.type_counters[x] = 0
                    for x in self.type_counters_offsets:
                        self.type_counters_offsets[x] = 0

            if (req_signal is None):
                print("Could not validate received parameters against registered signals")
                return ""

            print(self.type_counters)

            for x in self.type_counters:
                self.type_counters[x] = 0
            types = getattr(self.server_obj, req_signal).__signal__._args

            print(len(types))

            print(self.type_counters)
            print((str)(type(types)))
            output = {}
            for i in range (len(params)):
                print("elem " + (str)(i) + " data [" + (str)(params[i]) + "] type: " + (str)(type(params[i])))

                if (type(params[i]) == self.dbus_types_map[types[i]]):
                    print("Accepted type " + (str)(self.dbus_types_map[types[i]]))
                    if (types[i] == "au"):
                        print(bytes(params[i]))
                        barr = bytes(params[i])
                        print(pickle.loads(barr))
                        output[types[i] + (str)(self.type_counters[types[i]])] = pickle.loads(barr)
                        self.type_counters[types[i]]+=1
                    else:
                        output[types[i] + (str)(self.type_counters[types[i]])] = params[i]
                        self.type_counters[types[i]]+=1

            print(self.type_counters)
            for x in self.type_counters:
                self.type_counters[x] = 0
            return json.dumps(output, indent = 4)

        def read_object(self):
            if self.con is None:
                self.__init__(self)

            data = None
            data = self.con.recv()
            data = pickle.loads(data)

            return data


if __name__ == "__main__":
    # r = IOTC_IPC.Receiver
    x = IOTC_IPC.Sender()
    while 1:
        x.send_key_value("a", "b")