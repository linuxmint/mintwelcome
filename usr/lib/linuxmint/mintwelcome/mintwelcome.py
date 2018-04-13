#!/usr/bin/python3

import os
import gettext
import platform
import signal

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf

NORUN_FLAG = os.path.expanduser("~/.linuxmint/mintwelcome/norun.flag")
ICON_SIZE = 48

# i18n
gettext.install("mintwelcome", "/usr/share/linuxmint/locale")

UI_FILE = '/usr/share/linuxmint/mintwelcome/mintwelcome.ui'

signal.signal(signal.SIGINT, signal.SIG_DFL)

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
        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI_FILE)

        window = self.builder.get_object("main_window")
        # window.set_title(_("Welcome Screen"))
        window.set_icon_from_file("/usr/share/linuxmint/logo.png")
        # window.set_position(Gtk.WindowPosition.CENTER)
        window.connect("destroy", Gtk.main_quit)

        with open("/etc/linuxmint/info") as f:
            config = dict([line.strip().split("=") for line in f])

        codename = config['CODENAME'].capitalize()
        edition = config['EDITION'].replace('"', '')
        release = config['RELEASE']
        desktop = config['DESKTOP']
        self.release_notes = config['RELEASE_NOTES_URL']
        self.user_guide = "http://www.linuxmint.com/documentation.php"  # Switch to config['USER_GUIDE_URL'] when mintdoc is ready and localized
        self.new_features = config['NEW_FEATURES_URL']
        architecture = "64-bit"
        if platform.machine() != "x86_64":
            architecture = "32-bit"

        # distro-specific
        self.is_lmde = False
        self.dist_name = "Linux Mint"
        self.codec_pkg_name = "mint-meta-codecs"

        if os.path.exists("/usr/share/doc/debian-system-adjustments/copyright"):
            self.is_lmde = True
            self.dist_name = "LMDE"
            self.codec_pkg_name = "mint-meta-debian-codecs"
        else:
            if "KDE" in desktop:
                self.codec_pkg_name = "mint-meta-codecs-kde"

        # Setup the labels in the header
        self.builder.get_object("label_version").set_text("%s %s" % (self.dist_name, release))
        self.builder.get_object("label_edition").set_text("%s %s" % (edition, architecture))

        # Setup the main stack
        self.stack = Gtk.Stack()
        self.builder.get_object("center_box").pack_start(self.stack, True, True, 0)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        # Create the side navigation bar
        list_box = self.builder.get_object("list_navigation")

        # Check to see if we need to show codecs
        add_codecs = False

        import apt
        cache = apt.Cache()
        if self.codec_pkg_name in cache:
            pkg = cache[self.codec_pkg_name]
            if not pkg.is_installed:
                add_codecs = True

        # Construct the home page
        page_home = self.builder.get_object("page_home")
        self.stack.add_named(page_home, "page_home")
        row_home = SidebarRow(page_home, _("Home"), "go-home-symbolic")
        list_box.add(row_home)

        # Construct the documentation page
        page_documentation = self.builder.get_object("page_documentation")
        self.stack.add_named(page_documentation, "page_documentation")
        row_documentation = SidebarRow(page_documentation, _("Documentation"), "accessories-text-editor-symbolic")
        list_box.add(row_documentation)

        pixbuf = Pixbuf.new_from_file_at_size("/usr/share/linuxmint/mintwelcome/screenshots/user_guide.png", 96, -1)
        self.builder.get_object("image_user_guide").set_from_pixbuf(pixbuf)
        self.builder.get_object("button_user_guide").connect("clicked", self.user_guide_cb)

        pixbuf = Pixbuf.new_from_file_at_size("/usr/share/linuxmint/mintwelcome/screenshots/release_notes.png", 96, -1)
        self.builder.get_object("image_release_notes").set_from_pixbuf(pixbuf)
        self.builder.get_object("button_release_notes").connect("clicked", self.release_notes_cb)

        pixbuf = Pixbuf.new_from_file_at_size("/usr/share/linuxmint/mintwelcome/screenshots/new_features.png", 96, -1)
        self.builder.get_object("image_new_features").set_from_pixbuf(pixbuf)
        self.builder.get_object("button_new_features").connect("clicked", self.new_features_cb)

        # Construct the help page
        page_help = self.builder.get_object("page_help")
        self.stack.add_named(page_help, "page_help")
        row_help = SidebarRow(page_help, _("Get Help"), "help-faq-symbolic")
        list_box.add(row_help)

        pixbuf = Pixbuf.new_from_file_at_size("/usr/share/linuxmint/mintwelcome/screenshots/forums.png", 96, -1)
        self.builder.get_object("image_forums").set_from_pixbuf(pixbuf)
        self.builder.get_object("button_forums").connect("clicked", self.forums_cb)

        pixbuf = Pixbuf.new_from_file_at_size("/usr/share/linuxmint/mintwelcome/screenshots/chat.png", 96, -1)
        self.builder.get_object("image_chat").set_from_pixbuf(pixbuf)
        self.builder.get_object("button_chat").connect("clicked", self.chat_cb)

        # Construct the contribute page
        page_contribute = self.builder.get_object("page_contribute")
        self.stack.add_named(page_contribute, "page_contribute")
        row_contribute = SidebarRow(page_contribute, _("Contribute"), "system-users-symbolic")
        list_box.add(row_contribute)

        list_box.connect("row-activated", self.sidebar_row_selected_cb)

        self.stack.set_visible_child(page_home)

        actions = []

        add_codecs = False

        # import apt
        # cache = apt.Cache()
        # if self.codec_pkg_name in cache:
        #     pkg = cache[self.codec_pkg_name]
        #     if not pkg.is_installed:
        #         add_codecs = True

        self.last_selected_path = None

        if add_codecs:
            if self.is_lmde:
                actions.append(['new_features', _("New features"), _("See what is new in this release")])

            actions.append(['user_guide', _("Documentation"), _("Learn all the basics to get started with Linux Mint")])
            actions.append(['software', _("Apps"), _("Install additional software")])

            if not self.is_lmde:
                actions.append(['driver', _("Drivers"), _("Install hardware drivers")])

            actions.append(['codecs', _("Multimedia codecs"), _("Add all the missing multimedia codecs")])
            actions.append(['forums', _("Forums"), _("Seek help from other users in the Linux Mint forums")])
            actions.append(['chatroom', _("Chat room"), _("Chat live with other users in the chat room")])
            actions.append(['get_involved', _("Getting involved"), _("Find out how to get involved in the Linux Mint project")])
            actions.append(['donors', _("Donations"), _("Make a donation to the Linux Mint project")])
        else:
            actions.append(['new_features', _("New features"), _("See what is new in this release")])

            if self.is_lmde:
                actions.append(['release_notes', _("Release notes"), _("Read the release notes")])

            actions.append(['user_guide', _("Documentation"), _("Learn all the basics to get started with Linux Mint")])
            actions.append(['software', _("Apps"), _("Install additional software")])

            if not self.is_lmde:
                actions.append(['driver', _("Drivers"), _("Install hardware drivers")])

            actions.append(['forums', _("Forums"), _("Seek help from other users in the Linux Mint forums")])
            actions.append(['chatroom', _("Chat room"), _("Chat live with other users in the chat room")])
            actions.append(['get_involved', _("Getting involved"), _("Find out how to get involved in the Linux Mint project")])
            actions.append(['donors', _("Donations"), _("Make a donation to the Linux Mint project")])

        # Construct the bottom toolbar
        box = self.builder.get_object("toolbar_bottom")
        checkbox = Gtk.CheckButton()
        checkbox.set_label(_("Show this dialog at startup"))

        if not os.path.exists(NORUN_FLAG):
            checkbox.set_active(True)

        checkbox.connect("toggled", self.on_button_toggled)
        box.pack_end(checkbox)

        window.set_default_size(800, 500)

        window.show_all()

    def sidebar_row_selected_cb(self, list_box, row):
        self.stack.set_visible_child(row.page_widget)

    def on_button_toggled(self, button):
        if button.get_active():
            if os.path.exists(NORUN_FLAG):
                os.system("rm -rf %s" % NORUN_FLAG)
        else:
            os.system("mkdir -p ~/.linuxmint/mintwelcome")
            os.system("touch %s" % NORUN_FLAG)

    def item_activated(self, view, path):
        treeiter = view.get_model().get_iter(path)
        value = view.get_model().get_value(treeiter, 1)

        if value == "chatroom":
            os.system("xdg-open irc://irc.spotchat.org/linuxmint-help")
        elif value == "restore_data":
            if os.path.exists("/usr/bin/mintbackup"):
                os.system("/usr/bin/mintbackup &")
        elif value == "new_features":
            os.system("xdg-open %s &" % self.new_features)
        elif value == "release_notes":
            os.system("xdg-open %s &" % self.release_notes)
        elif value == "user_guide":
            os.system("xdg-open %s &" % self.user_guide)
        elif value == "forums":
            os.system("xdg-open http://forums.linuxmint.com &")
        elif value == "tutorials":
            os.system("xdg-open http://community.linuxmint.com/tutorial &")
        elif value == "ideas":
            os.system("xdg-open http://community.linuxmint.com/idea &")
        elif value == "software":
            os.system("mintinstall &")
        elif value == "driver":
            os.system("mintdrivers &")
        elif value == "hardware":
            os.system("xdg-open http://community.linuxmint.com/hardware &")
        elif value == "get_involved":
            os.system("xdg-open http://www.linuxmint.com/getinvolved.php &")
        elif value == "sponsors":
            os.system("xdg-open http://www.linuxmint.com/sponsors.php &")
        elif value == "donors":
            os.system("xdg-open http://www.linuxmint.com/donors.php &")
        elif value == "codecs":
            os.system("xdg-open apt://%s?refresh=yes &" % self.codec_pkg_name)

    # Documentation callbacks
    def user_guide_cb(self, button):
        os.system("xdg-open %s &" % self.user_guide)

    def release_notes_cb(self, button):
        os.system("xdg-open %s &" % self.release_notes)

    def new_features_cb(self, button):
        os.system("xdg-open %s &" % self.new_features)

    # Help callbacks
    def forums_cb(self, button):
        os.system("xdg-open http://forums.linuxmint.com &")

    def chat_cb(self, button):
        os.system("xdg-open irc://irc.spotchat.org/linuxmint-help")

if __name__ == "__main__":
    MintWelcome()
    Gtk.main()
