#!/usr/bin/env python

import gi
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf

import sys
import commands
import os
import gettext
from user import home
import string

# i18n
gettext.install("mintwelcome", "/usr/share/linuxmint/locale")

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

class MintWelcome():
    def __init__(self):
        window = Gtk.Window()
        window.set_title(_("Welcome Screen"))
        window.set_icon_from_file("/usr/share/linuxmint/logo.png")
        window.set_position(Gtk.WindowPosition.CENTER)
        window.connect("destroy", Gtk.main_quit)

        sys.path.append('/usr/lib/linuxmint/common')
        from configobj import ConfigObj
        config = ConfigObj("/etc/linuxmint/info")
        codename = config['CODENAME'].capitalize()
        edition = config['EDITION']
        release = config['RELEASE']
        desktop = config['DESKTOP']
        self.release_notes = config['RELEASE_NOTES_URL']
        self.user_guide = "http://www.linuxmint.com/documentation.php" # Switch to config['USER_GUIDE_URL'] when mintdoc is ready and localized
        self.new_features = config['NEW_FEATURES_URL']

        # distro-specific
        self.dist_name = "Linux Mint"
        self.codec_pkg_name = "mint-meta-codecs"
        if os.path.exists("/usr/share/doc/debian-system-adjustments/copyright"):
            self.dist_name = "LMDE"
            self.codec_pkg_name = "mint-meta-debian-codecs"

        bgcolor =  Gdk.RGBA()
        bgcolor.parse("rgba(0,0,0,0)")
        fgcolor =  Gdk.RGBA()
        fgcolor.parse("#3e3e3e")

        main_box = Gtk.VBox()

        event_box = Gtk.EventBox()
        event_box.set_name("event_box")
        event_box.override_background_color(Gtk.StateType.NORMAL, bgcolor)
        event_box.override_color(Gtk.StateType.NORMAL, fgcolor)
        main_box.pack_start(event_box, True, True, 0)

        vbox = Gtk.VBox()
        vbox.set_border_width(12)
        vbox.set_spacing(0)
        event_box.add(vbox)

        headerbox = Gtk.VBox()
        logo = Gtk.Image()
        if "KDE" in desktop:
            logo.set_from_file("/usr/lib/linuxmint/mintWelcome/icons/logo_header_kde.png")
        else:
            logo.set_from_file("/usr/lib/linuxmint/mintWelcome/icons/logo_header.png")
        headerbox.pack_start(logo, False, False, 0)
        label = Gtk.Label()
        if "KDE" in desktop:
            label.set_markup("<span font='12.5' fgcolor='#3e3e3e'>%s %s '<span fgcolor='#3267b8'>%s</span>'</span>" % (self.dist_name, release, codename))
        else:
            label.set_markup("<span font='12.5' fgcolor='#3e3e3e'>%s %s '<span fgcolor='#709937'>%s</span>'</span>" % (self.dist_name, release, codename))
        headerbox.pack_start(label, False, False, 0)
        label = Gtk.Label()
        label.set_markup("<span font='8' fgcolor='#3e3e3e'><i>%s</i></span>" % edition)
        headerbox.pack_start(label, False, False, 2)
        vbox.pack_start(headerbox, False, False, 10)

        welcome_label = Gtk.Label()
        welcome_message = _("Welcome and thank you for choosing Linux Mint. We hope you'll enjoy using it as much as we did designing it. The links below will help you get started with your new operating system. Have a great time and don't hesitate to send us your feedback.")
        welcome_label.set_markup("<span font='9' fgcolor='#3e3e3e'>%s</span>" % welcome_message)
        welcome_label.set_line_wrap(True)
        vbox.pack_start(welcome_label, False, False, 10)

        separator = Gtk.Image()
        separator.set_from_file('/usr/lib/linuxmint/mintWelcome/icons/separator.png')
        vbox.pack_start(separator, False, False, 10)

        liststore = Gtk.ListStore(Pixbuf, str, str, str, Pixbuf, Pixbuf)
        self.iconview = Gtk.IconView.new()
        self.iconview.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.iconview.connect("item-activated", self.item_activated)
        self.iconview.connect("motion-notify-event", self.on_pointer_motion)
        self.iconview.connect("button-press-event", self.on_mouse_click)
        self.iconview.set_model(liststore)
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_text_column(2)
        self.iconview.set_tooltip_column(3)
        self.iconview.set_columns(4)
        self.iconview.set_margin(0)
        self.iconview.set_spacing(6)
        self.iconview.set_item_padding(3)
        self.iconview.set_row_spacing(20)
        self.iconview.set_column_spacing(20)
        self.iconview.override_background_color(Gtk.StateType.NORMAL, bgcolor)
        self.iconview.override_color(Gtk.StateType.NORMAL, fgcolor)
        #self.iconview.connect("selection-changed", self.item_activated)
        hbox = Gtk.HBox()
        hbox.pack_start(self.iconview, True, True, 30)
        vbox.pack_start(hbox, False, False, 10)


        actions = []

        add_codecs = False
        if ("Gnome" in desktop or "MATE" in desktop) and "debian" not in codename:
            # Some GNOME editions (Cinnamon, MATE) can come without codecs
            import apt
            cache = apt.Cache()
            if self.codec_pkg_name in cache:
                pkg = cache[self.codec_pkg_name]
                if not pkg.is_installed:
                    add_codecs = True

        self.last_selected_path = None

        if add_codecs:
            actions.append(['user_guide', _("Documentation"), _("Learn all the basics to get started with Linux Mint")])
            actions.append(['software', _("Apps"), _("Install additional software")])
            actions.append(['driver', _("Drivers"), _("Manage the drivers for your devices")])
            actions.append(['codecs', _("Multimedia codecs"), _("Add all the missing multimedia codecs")])
            actions.append(['forums', _("Forums"), _("Seek help from other users in the Linux Mint forums")])
            actions.append(['chatroom', _("Chat room"), _("Chat live with other users in the chat room")])
            actions.append(['get_involved', _("Getting involved"), _("Find out how to get involved in the Linux Mint project")])
            actions.append(['donors', _("Donations"), _("Make a donation to the Linux Mint project")])
        else:
            actions.append(['new_features', _("New features"), _("See what is new in this release")])
            actions.append(['user_guide', _("Documentation"), _("Learn all the basics to get started with Linux Mint")])
            actions.append(['software', _("Apps"), _("Install additional software")])
            actions.append(['driver', _("Drivers"), _("Manage the drivers for your devices")])
            actions.append(['forums', _("Forums"), _("Seek help from other users in the Linux Mint forums")])
            actions.append(['chatroom', _("Chat room"), _("Chat live with other users in the chat room")])
            actions.append(['get_involved', _("Getting involved"), _("Find out how to get involved in the Linux Mint project")])
            actions.append(['donors', _("Donations"), _("Make a donation to the Linux Mint project")])

        for action in actions:
            desat_pixbuf = Pixbuf.new_from_file('/usr/lib/linuxmint/mintWelcome/icons/desat/%s.png' % action[0])
            color_pixbuf = Pixbuf.new_from_file('/usr/lib/linuxmint/mintWelcome/icons/color/%s.png' % action[0])
            pixbuf = desat_pixbuf
            liststore.append([pixbuf, action[0], action[1], action[2], desat_pixbuf, color_pixbuf])

        hbox = Gtk.HBox()
        hbox.set_border_width(6)
        main_box.pack_end(hbox, False, False, 0)
        checkbox = Gtk.CheckButton()
        checkbox.set_label(_("Show this dialog at startup"))
        checkbox.override_color(Gtk.StateType.NORMAL, fgcolor)
        if not os.path.exists(home + "/.linuxmint/mintWelcome/norun.flag"):
            checkbox.set_active(True)
        checkbox.connect("toggled", self.on_button_toggled)
        hbox.pack_end(checkbox, False, False, 2)

        window.add(main_box)
        window.set_default_size(540, 420)

        css_provider = Gtk.CssProvider()
        css = """
 #event_box {
      background-image: -gtk-gradient (linear,
                                       left top,
       left bottom,
       from (#d6d6d6),
       color-stop (0.5, #efefef),
       to (#d6d6d6));
    }
"""

        css_provider.load_from_data(css.encode('UTF-8'))
        screen = Gdk.Screen.get_default()
        style_context = window.get_style_context()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        window.show_all()

    def on_pointer_motion(self, widget, event):
        path= self.iconview.get_path_at_pos(event.x, event.y)
        if path !=None:
                if path == self.last_selected_path:
                    return
                self.unhighlight_icon(widget)
                treeiter = widget.get_model().get_iter(path)
                widget.get_model().set_value(treeiter, 0, widget.get_model().get_value(treeiter, 5))
                self.last_selected_path = path
        #If we're outside of an item, deselect all items (turn off highlighting)
        if path == None:
            self.unhighlight_icon(widget)
            self.iconview.unselect_all()

    def unhighlight_icon(self, widget):
        if self.last_selected_path != None:
                treeiter = widget.get_model().get_iter(self.last_selected_path)
                widget.get_model().set_value(treeiter, 0, widget.get_model().get_value(treeiter, 4))
                self.last_selected_path = None

    def on_button_toggled(self, button):
        if button.get_active():
            if os.path.exists(home + "/.linuxmint/mintWelcome/norun.flag"):
                os.system("rm -rf " + home + "/.linuxmint/mintWelcome/norun.flag")
        else:
            os.system("mkdir -p " + home + "/.linuxmint/mintWelcome")
            os.system("touch " + home + "/.linuxmint/mintWelcome/norun.flag")

    def on_mouse_click(self,widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            path= self.iconview.get_path_at_pos(event.x, event.y)
            #if left click, activate the item to execute
            if event.button == 1 and path != None:
                self.item_activated(widget, path)

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
        elif value == "known_problems":
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

if __name__ == "__main__":
    MintWelcome()
    Gtk.main()
