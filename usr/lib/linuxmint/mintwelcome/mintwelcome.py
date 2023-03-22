#!/usr/bin/python3
from typing import Final
# Can't use `StrEnum` because it requires Py 3.11+
from enum import Enum #StrEnum

from os import path as os_path, getenv, system
from subprocess import call as subp_call, check_output as subp_check_output, Popen as subp_Popen

from gettext import install as getxt_install
from gi import require_version as gi_req_ver
gi_req_ver("Gtk", "3.0")
from gi.repository import Gtk, Gio, Gdk, GdkPixbuf

# i18n
getxt_install("mintwelcome", "/usr/share/linuxmint/locale")
from locale import gettext as _, bindtextdomain as locale_bindtxtdom, textdomain as locale_txtdom
locale_bindtxtdom("mintwelcome", "/usr/share/linuxmint/locale")
locale_txtdom("mintwelcome")

NORUN_FLAG: Final = os_path.expanduser("~/.linuxmint/mintwelcome/norun.flag")

class Color(Enum):
    BLUE = "blue"
    AQUA = "aqua"
    TEAL = "teal"
    GREEN = "green"
    SAND = "sand"
    BROWN = "brown"
    GREY = "grey"
    ORANGE = "orange"
    RED = "red"
    PINK = "pink"
    PURPLE = "purple"

# to-do: add fn similar to `dict.get`, but for enums, using try-except
COLORSET: Final[set[str]] = set(e.value for e in Color)

DEFAULT_COLOR: Final = Color.GREEN.value
DEFAULT_THEME: Final = "Mint-Y"
DARK_SUFFIX: Final = "-Dark"
DEFAULT_DARK_THEME: Final = DEFAULT_THEME + DARK_SUFFIX

MMC: Final = "mint-meta-codecs"

# to-do
'''
class DesktopEnvs(Enum):
    CINNAMON = "Cinnamon"
    X_CINNAMON = "X-Cinnamon"
    MATE = "MATE"
    XFCE = "XFCE"
'''

def get_desktop_env():
    """
    Get `XDG_CURRENT_DESKTOP` environment variable,
    return `None` if it doesn't exist.
    """
    return getenv("XDG_CURRENT_DESKTOP")


class SidebarRow(Gtk.ListBoxRow):

    def __init__(self, page_widget, page_name: str, icon_name: str):
        Gtk.ListBoxRow.__init__(self)
        self.page_widget = page_widget
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_border_width(6)
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        box.pack_start(image, False, False, 0)
        label = Gtk.Label()
        label.set_text(page_name)
        box.pack_start(label, False, False, 0)
        self.add(box)

class MintWelcome():

    def __init__(self):
        from platform import machine as get_arch
        from apt import Cache as apt_Cache

        builder: Final = Gtk.Builder()
        builder.set_translation_domain("mintwelcome")
        builder.add_from_file("/usr/share/linuxmint/mintwelcome/mintwelcome.ui")

        window: Final = builder.get_object("main_window")
        window.set_icon_name("mintwelcome")
        window.set_position(Gtk.WindowPosition.CENTER)
        window.connect("destroy", Gtk.main_quit)

        with open("/etc/linuxmint/info") as f:
            # In this case, tuples seem slower than lists
            config: Final = dict([line.strip().split("=") for line in f])
        edition: Final = config['EDITION'].replace('"', '')
        release: Final = config['RELEASE']
        release_notes: Final = config['RELEASE_NOTES_URL']
        new_features: Final = config['NEW_FEATURES_URL']
        # Since LM is distributed as 64b or 32b,
        # this is a safe assumption
        architecture: Final = ("64" if "64" in get_arch() else "32") + "-bit"

        # distro-specific
        dist_name: Final = \
            "LMDE" if os_path.exists("/usr/share/doc/debian-system-adjustments/copyright") \
            else "Linux Mint"

        # Setup the labels in the Mint badge
        builder.get_object("label_version").set_text(dist_name + " " + release)
        builder.get_object("label_edition").set_text(edition + " " + architecture)

        # Setup the main stack
        self.stack = Gtk.Stack()
        builder.get_object("center_box").pack_start(self.stack, True, True, 0)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        # Action buttons
        builder.get_object("button_forums").connect("clicked", self.visit, "https://forums.linuxmint.com")
        builder.get_object("button_documentation").connect("clicked", self.visit, "https://linuxmint.com/documentation.php")
        builder.get_object("button_contribute").connect("clicked", self.visit, "https://linuxmint.com/getinvolved.php")
        builder.get_object("button_irc").connect("clicked", self.visit, "irc://irc.spotchat.org/linuxmint-help")
        builder.get_object("button_codecs").connect("clicked", self.visit, f"apt://{MMC}?refresh=yes")
        builder.get_object("button_new_features").connect("clicked", self.visit, new_features)
        builder.get_object("button_release_notes").connect("clicked", self.visit, release_notes)
        builder.get_object("button_mintupdate").connect("clicked", self.launch, "mintupdate")
        builder.get_object("button_mintinstall").connect("clicked", self.launch, "mintinstall")
        builder.get_object("button_timeshift").connect("clicked", self.pkexec, "timeshift-gtk")
        builder.get_object("button_mintdrivers").connect("clicked", self.launch, "driver-manager")
        builder.get_object("button_gufw").connect("clicked", self.launch, "gufw")
        builder.get_object("go_button").connect("clicked", self.go)

        # Settings button depends on DE
        self.theme = ""
        de: Final = get_desktop_env()
        if de in ("Cinnamon", "X-Cinnamon"):
            builder.get_object("button_settings").connect("clicked", self.launch, "cinnamon-settings")
            self.theme = Gio.Settings(schema="org.cinnamon.desktop.interface").get_string("gtk-theme")
        elif de == "MATE":
            builder.get_object("button_settings").connect("clicked", self.launch, "mate-control-center")
        elif de == "XFCE":
            builder.get_object("button_settings").connect("clicked", self.launch, "xfce4-settings-manager")
        else:
            # Hide settings
            builder.get_object("box_first_steps").remove(builder.get_object("box_settings"))

        # Hide codecs box if they're already installed
        cache: Final = apt_Cache()
        if MMC in cache and cache[MMC].is_installed:
            builder.get_object("box_first_steps").remove(builder.get_object("box_codecs"))

        # Hide drivers if mintdrivers is absent (LMDE)
        if not os_path.exists("/usr/bin/mintdrivers"):
            builder.get_object("box_first_steps").remove(builder.get_object("box_drivers"))

        # Hide new features page for LMDE
        if dist_name == "LMDE":
            builder.get_object("box_documentation").remove(builder.get_object("box_new_features"))

        # Construct the stack switcher
        self.list_box = builder.get_object("list_navigation")

        page = builder.get_object("page_home")
        self.stack.add_named(page, "page_home")
        self.list_box.add(SidebarRow(page, _("Welcome"), "go-home-symbolic"))
        self.stack.set_visible_child(page)

        page = builder.get_object("page_first_steps")
        self.stack.add_named(page, "page_first_steps")
        self.first_steps_row = SidebarRow(page, _("First Steps"), "dialog-information-symbolic")
        self.list_box.add(self.first_steps_row)

        page = builder.get_object("page_documentation")
        self.stack.add_named(page, "page_documentation")
        self.list_box.add(SidebarRow(page, _("Documentation"), "accessories-dictionary-symbolic"))

        page = builder.get_object("page_help")
        self.stack.add_named(page, "page_help")
        self.list_box.add(SidebarRow(page, _("Help"), "help-browser-symbolic"))

        page = builder.get_object("page_contribute")
        self.stack.add_named(page, "page_contribute")
        self.list_box.add(SidebarRow(page, _("Contribute"), "starred-symbolic"))

        self.list_box.connect("row-activated", self.sidebar_row_selected_cb)

        # Construct the bottom toolbar
        box: Final = builder.get_object("toolbar_bottom")
        checkbox: Final = Gtk.CheckButton()
        checkbox.set_label(_("Show this dialog at startup"))
        if not os_path.exists(NORUN_FLAG):
            checkbox.set_active(True)
        checkbox.connect("toggled", self.on_button_toggled)
        box.pack_end(checkbox)

        scale: int = window.get_scale_factor()

        self.init_color_info()

        path = "/usr/share/linuxmint/mintwelcome/colors/"
        if scale >= 2:
            path += "hidpi/"
        for c in Color:
            color: str = c.value
            builder.get_object("img_" + color).set_from_surface(self.surface_for_path(f"{path}/{color}.png", scale))
            builder.get_object("button_" + color).connect("clicked", self.on_color_button_clicked, color)

        builder.get_object("switch_dark").set_active(self.dark_mode)
        builder.get_object("switch_dark").connect("state-set", self.on_dark_mode_changed)

        window.set_default_size(800, 500)
        window.show_all()

    def go(self, button):
        self.list_box.select_row(self.first_steps_row)
        self.stack.set_visible_child_name("page_first_steps")

    def surface_for_path(self, path: str, scale: int):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

        return Gdk.cairo_surface_create_from_pixbuf(pixbuf, scale)

    def sidebar_row_selected_cb(self, list_box, row):
        self.stack.set_visible_child(row.page_widget)

    def on_button_toggled(self, button):
        if button.get_active():
            if os_path.exists(NORUN_FLAG):
                system("rm -rf " + NORUN_FLAG)
        else:
            system("mkdir -p ~/.linuxmint/mintwelcome")
            system("touch " + NORUN_FLAG)

    def on_dark_mode_changed(self, button, state: bool):
        self.dark_mode = state
        self.change_color()

    def on_color_button_clicked(self, button, color: str):
        self.color = color
        self.change_color()

    def change_color(self):
        theme = DEFAULT_THEME
        icon_theme = DEFAULT_THEME
        wm_theme: Final = DEFAULT_THEME
        cinnamon_theme = DEFAULT_DARK_THEME
        if self.dark_mode:
            theme += DARK_SUFFIX
        color_suffix: Final = "-" + self.color.title()
        if self.color != DEFAULT_COLOR:
            theme += color_suffix
            icon_theme += color_suffix
            cinnamon_theme = DEFAULT_DARK_THEME + color_suffix

        de: Final = get_desktop_env()
        if de in ("Cinnamon", "X-Cinnamon"):
            settings = Gio.Settings(schema="org.cinnamon.desktop.interface")
            settings.set_string("gtk-theme", theme)
            settings.set_string("icon-theme", icon_theme)
            Gio.Settings(schema="org.cinnamon.desktop.wm.preferences").set_string("theme", wm_theme)
            Gio.Settings(schema="org.cinnamon.theme").set_string("name", cinnamon_theme)
        elif de == "MATE":
            settings = Gio.Settings(schema="org.mate.interface")
            settings.set_string("gtk-theme", theme)
            settings.set_string("icon-theme", icon_theme)
            Gio.Settings(schema="org.mate.Marco.general").set_string("theme", wm_theme)
        elif de == "XFCE":
            subp_call(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", theme])
            subp_call(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", icon_theme])
            subp_call(["xfconf-query", "-c", "xfwm4", "-p", "/general/theme", "-s", theme])

    def init_color_info(self):
        """
        Sets `self.dark_mode` and `self.color` based on current system configuration
        """
        theme: Final = DEFAULT_THEME
        dark_theme: Final = DEFAULT_DARK_THEME
        de: Final = get_desktop_env()
        if de in ("Cinnamon", "X-Cinnamon"):
            setting = Gio.Settings(schema="org.cinnamon.desktop.interface").get_string("gtk-theme")
        elif de == "MATE":
            setting = Gio.Settings(schema="org.mate.interface").get_string("gtk-theme")
        elif de == "XFCE":
            setting = subp_check_output(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"]).decode("utf-8").strip()
        elif de is None:
            raise TypeError("No Desktop Environment")
        else:
            raise ValueError("Unrecognized Desktop Environment: " + de)

        if setting.startswith(theme):
            self.dark_mode = setting.startswith(dark_theme)
            setting = setting.replace(dark_theme if self.dark_mode else theme, "")
            if len(setting) <= 1:
                self.color = DEFAULT_COLOR
            else:
                self.color = setting[1:].lower()
                if self.color not in COLORSET:
                    self.color = DEFAULT_COLOR
        else: # Not working with a Mint-Y theme, or theme is unknown
            self.init_default_color_info() # Fall-back

    def init_default_color_info(self):
        self.color = DEFAULT_COLOR
        self.dark_mode = False

    def visit(self, button, url: str):
        subp_Popen(["xdg-open", url])

    def launch(self, button, command: str):
        subp_Popen([command])

    def pkexec(self, button, command: str):
        subp_Popen(["pkexec", command])

if __name__ == "__main__":
    MintWelcome()
    Gtk.main()
