import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator

from zeroconf import ServiceBrowser, Zeroconf
from time import sleep, time
import socket
from typing import cast
from leglight import LegLight
import logging

class Discovery:
    def __init__(self, on_update):
        self.known = dict()
        self.on_update = on_update
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, "_elg._tcp.local.", self)

    def remove_service(self, zeroconf, type, name):
        del self.known[(type, name)]
        self.on_update()

    def add_service(self, zeroconf, type, name):
        # Get the info from mDNS and shove it into a LegLight object
        info = zeroconf.get_service_info(type, name)
        ip = socket.inet_ntoa(info.addresses[0])
        port = cast(int, info.port)
        lname = info.name
        server = info.server
        logging.debug("Found light @ {}:{}".format(ip, port))
        self.known[(type, name)] = LegLight(address=ip, port=port, name=lname, server=server)
        self.on_update()

    def close(self):
        self.zeroconf.close()

def menuitem_response(w, buf):
    print(f"{w=}, {buf=}")

def toggle_light(menu_item, light, isOn, render):
    if isOn:
        light.off()
    else:
        light.on()
    render()

def create_menu(ind, discovery, render):
    found_any = False
    menu = Gtk.Menu()
    for light in discovery.known.values():
        isOn = light.isOn
        onMsg = "On" if isOn else "Off"
        menu_item = Gtk.MenuItem(label=f"{light} - {onMsg}")
        menu_item.connect("activate", toggle_light, light, isOn, render)
        menu.append(menu_item)
        menu_item.show()
        found_any = True
    if not found_any:
        menu_item = Gtk.MenuItem(label="No devices found")
        menu_item.set_sensitive(False)
        menu.append(menu_item)
        menu_item.show()
    ind.set_menu(menu)

def main():
    ind = appindicator.Indicator.new("keylight", "indicator-messages", appindicator.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(appindicator.IndicatorStatus.ACTIVE)

    def render():
        create_menu(ind, discovery, render)

    discovery = Discovery(lambda: GLib.idle_add(render))
    render()
    Gtk.main()

if __name__ == "__main__":
    main()