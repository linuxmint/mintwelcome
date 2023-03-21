#!/usr/bin/python3
import apt
import gettext
import gi
import os
import platform
import subprocess
import locale
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, Gdk, GdkPixbuf

def get_desktop_env():
    return os.getenv("XDG_CURRENT_DESKTOP")

NORUN_FLAG = os.path.expanduser("~/.linuxmint/mintwelcome/norun.flag")

# i18n
gettext.install("mintwelcome", "/usr/share/linuxmint/locale")
from locale import gettext as _
locale.bindtextdomain("mintwelcome", "/usr/share/linuxmint/locale")
locale.textdomain("mintwelcome")

LAYOUT_STYLE_LEGACY, LAYOUT_STYLE_NEW = range(2)

class SidebarRow(Gtk.ListBoxRow):

    def __init__(self, page_widget, page_name, icon_name):
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
        builder = Gtk.Builder()
        builder.set_translation_domain("mintwelcome")
        builder.add_from_file('/usr/share/linuxmint/mintwelcome/mintwelcome.ui')

        window = builder.get_object("main_window")
        window.set_icon_name("mintwelcome")
        window.set_position(Gtk.WindowPosition.CENTER)
        window.connect("destroy", Gtk.main_quit)

        with open("/etc/linuxmint/info") as f:
            # in this case, tuples seem slower than lists
            config = dict([line.strip().split("=") for line in f])
        edition = config['EDITION'].replace('"', '')
        release = config['RELEASE']
        release_notes = config['RELEASE_NOTES_URL']
        new_features = config['NEW_FEATURES_URL']
        architecture = "64" if platform.machine() == "x86_64" else "32"
        architecture = "%s-bit" % architecture

        # distro-specific
        dist_name = "Linux Mint"
        if os.path.exists("/usr/share/doc/debian-system-adjustments/copyright"):
            dist_name = "LMDE"

        # Setup the labels in the Mint badge
        builder.get_object("label_version").set_text("%s %s" % (dist_name, release))
        builder.get_object("label_edition").set_text("%s %s" % (edition, architecture))

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
        builder.get_object("button_codecs").connect("clicked", self.visit, "apt://mint-meta-codecs?refresh=yes")
        builder.get_object("button_new_features").connect("clicked", self.visit, new_features)
        builder.get_object("button_release_notes").connect("clicked", self.visit, release_notes)
        builder.get_object("button_mintupdate").connect("clicked", self.launch, "mintupdate")
        builder.get_object("button_mintinstall").connect("clicked", self.launch, "mintinstall")
        builder.get_object("button_timeshift").connect("clicked", self.pkexec, "timeshift-gtk")
        builder.get_object("button_mintdrivers").connect("clicked", self.launch, "driver-manager")
        builder.get_object("button_gufw").connect("clicked", self.launch, "gufw")
        builder.get_object("go_button").connect("clicked", self.go)

        # Settings button depends on DE
        de_is_cinnamon = False
        self.theme = None
        de = get_desktop_env()
        if de in ("Cinnamon", "X-Cinnamon"):
            builder.get_object("button_settings").connect("clicked", self.launch, "cinnamon-settings")
            de_is_cinnamon = True
            self.theme = Gio.Settings(schema="org.cinnamon.desktop.interface").get_string("gtk-theme")
        elif de == "MATE":
            builder.get_object("button_settings").connect("clicked", self.launch, "mate-control-center")
        elif de == "XFCE":
            builder.get_object("button_settings").connect("clicked", self.launch, "xfce4-settings-manager")
        else:
            # Hide settings
            builder.get_object("box_first_steps").remove(builder.get_object("box_settings"))

        # Hide codecs box if they're already installed
        cache = apt.Cache()
        if "mint-meta-codecs" in cache and cache["mint-meta-codecs"].is_installed:
            builder.get_object("box_first_steps").remove(builder.get_object("box_codecs"))

        # Hide drivers if mintdrivers is absent (LMDE)
        if not os.path.exists("/usr/bin/mintdrivers"):
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
        box = builder.get_object("toolbar_bottom")
        checkbox = Gtk.CheckButton()
        checkbox.set_label(_("Show this dialog at startup"))
        if not os.path.exists(NORUN_FLAG):
            checkbox.set_active(True)
        checkbox.connect("toggled", self.on_button_toggled)
        box.pack_end(checkbox)

        scale = window.get_scale_factor()

        self.all_colors = ("blue", "aqua", "teal", "green", "sand", "brown", "grey", "orange", "red", "pink", "purple")
        self.init_color_info()  # Sets self.dark_mode and self.color based on current system configuration

        path = "/usr/share/linuxmint/mintwelcome/colors/"
        if scale == 2:
            path += "hidpi/"
        for color in self.all_colors:
            builder.get_object("img_" + color).set_from_surface(self.surface_for_path("%s/%s.png" % (path, color), scale))
            builder.get_object("button_" + color).connect("clicked", self.on_color_button_clicked, color)

        builder.get_object("switch_dark").set_active(self.dark_mode)
        builder.get_object("switch_dark").connect("state-set", self.on_dark_mode_changed)

        window.set_default_size(800, 500)
        window.show_all()

    def go(self, button):
        self.list_box.select_row(self.first_steps_row)
        self.stack.set_visible_child_name("page_first_steps")

    def surface_for_path(self, path, scale):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

        return Gdk.cairo_surface_create_from_pixbuf(pixbuf, scale)

    def sidebar_row_selected_cb(self, list_box, row):
        self.stack.set_visible_child(row.page_widget)

    def on_button_toggled(self, button):
        if button.get_active():
            if os.path.exists(NORUN_FLAG):
                os.system("rm -rf %s" % NORUN_FLAG)
        else:
            os.system("mkdir -p ~/.linuxmint/mintwelcome")
            os.system("touch %s" % NORUN_FLAG)

    def on_dark_mode_changed(self, button, state):
        self.dark_mode = state
        self.change_color()

    def on_color_button_clicked(self, button, color):
        self.color = color
        self.change_color()

    def change_color(self):
        theme = \
        icon_theme = \
        wm_theme = "Mint-Y"
        cinnamon_theme = "Mint-Y-Dark"
        if self.dark_mode:
            theme = "%s-Dark" % theme
            cinnamon_theme = "%s-Dark" % cinnamon_theme
        if self.color != "green":
            theme = "%s-%s" % (theme, self.color.title())
            icon_theme = "%s-%s" % (icon_theme, self.color.title())
            cinnamon_theme = "Mint-Y-Dark-%s" % self.color.title()

        de = get_desktop_env()
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
            subprocess.call(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", theme])
            subprocess.call(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", icon_theme])
            subprocess.call(["xfconf-query", "-c", "xfwm4", "-p", "/general/theme", "-s", theme])

    def init_color_info(self):
        theme = "Mint-Y"
        dark_theme = "Mint-Y-Dark"
        de = get_desktop_env()
        if de in ("Cinnamon", "X-Cinnamon"):
            setting = Gio.Settings(schema="org.cinnamon.desktop.interface").get_string("gtk-theme")
        elif de == "MATE":
            setting = Gio.Settings(schema="org.mate.interface").get_string("gtk-theme")
        elif de == "XFCE":
            setting = subprocess.check_output(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"]).decode("utf-8").strip()
        else:
            # Instead of letting Py raise a cryptic error message,
            # we use a more specific message
            raise Exception('Unrecognized Desktop Environment: %s' % de)

        if setting.startswith(theme):
            self.dark_mode = setting.startswith(dark_theme)
            setting = setting.replace(dark_theme if self.dark_mode else theme, "")
            if len(setting) <= 1:
                self.color = "green"
            else:
                self.color = setting[1:].lower()
                if not self.color in self.all_colors:  # Assume green if our color is invalid
                    self.color = "green"
        else:
            self.init_default_color_info()  # Bail out if we aren't working with a Mint-Y theme or the theme is unknown

    def init_default_color_info(self):
        self.color = "green"
        self.dark_mode = False

    def visit(self, button, url):
        subprocess.Popen(["xdg-open", url])

    def launch(self, button, command):
        subprocess.Popen([command])

    def pkexec(self, button, command):
        subprocess.Popen(["pkexec", command])

if __name__ == "__main__":
    MintWelcome()
    Gtk.main()
