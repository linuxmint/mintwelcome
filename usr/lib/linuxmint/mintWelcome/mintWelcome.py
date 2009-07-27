#!/usr/bin/env python

import sys
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import commands
import os
import gettext
from user import home

# i18n
gettext.install("messages", "/usr/lib/linuxmint/mintWelcome/locale")  

def launch_irc(widget):
	if os.path.exists("/usr/bin/xchat-gnome"):
		os.system("/usr/bin/xchat-gnome &")
	elif os.path.exists("/usr/bin/xchat"):
		os.system("/usr/bin/xchat &")
	elif os.path.exists("/usr/bin/konversation"):
		os.system("/usr/bin/konversation &")

def exit_app(widget, wTree):
	if wTree.get_widget("checkbutton_show").get_active() == True:
		if os.path.exists(home + "/.linuxmint/mintWelcome/norun.flag"):
			os.system("rm -rf " + home + "/.linuxmint/mintWelcome/norun.flag")
	else:
		os.system("mkdir -p " + home + "/.linuxmint/mintWelcome")		
		os.system("touch " + home + "/.linuxmint/mintWelcome/norun.flag")
	gtk.main_quit()

try:
	gladefile = "/usr/lib/linuxmint/mintWelcome/mintWelcome.glade"
	wTree = gtk.glade.XML(gladefile,"main_window")
	wTree.get_widget("main_window").set_title(_("Welcome to Linux Mint"))
	wTree.get_widget("main_window").set_icon_from_file("/usr/lib/linuxmint/mintSystem/icon.png")	
	wTree.get_widget("button_irc").connect("clicked", launch_irc)
	sys.path.append('/usr/lib/linuxmint/mintSystem/python')
	from configobj import ConfigObj
	config = ConfigObj("/etc/linuxmint/info")
	description = config['DESCRIPTION']
	release = config['RELEASE']
	description = description.replace("\"", "")
	release_notes = config['RELEASE_NOTES_URL']
	user_guide = config['USER_GUIDE_URL']
	new_features = config['NEW_FEATURES_URL']
	
	wTree.get_widget("label_title").set_label("<b>" + description + "</b>")
	wTree.get_widget("label_title").set_use_markup(True)
	wTree.get_widget("button_new_features").set_uri(new_features)
	wTree.get_widget("button_release_notes").set_uri(release_notes)
	wTree.get_widget("button_user_guide").set_uri(user_guide)

	if os.path.exists(home + "/.linuxmint/mintWelcome/norun.flag"):		
		wTree.get_widget("checkbutton_show").set_active(False)
	else:
		wTree.get_widget("checkbutton_show").set_active(True)

	wTree.get_widget("main_window").connect("destroy", exit_app, wTree)
	wTree.get_widget("close_button").connect("clicked", exit_app, wTree)

	#i18n
	wTree.get_widget("label_welcome").set_label("<i>" + _("Welcome and thank you for choosing Linux Mint. We hope you'll enjoy using it as much as we did making it. Please make yourself familiar with the new features and the documentation and don't hesitate to send us your feedback.") + "</i>")
	wTree.get_widget("label_welcome").set_use_markup(True)
	wTree.get_widget("frame_discover").set_label("<b>" + _("Discover %s") % ("Linux Mint " + release) + "</b>")
	wTree.get_widget("frame_discover").set_use_markup(True)
	wTree.get_widget("frame_help").set_label("<b>" + _("Find help") + "</b>")
	wTree.get_widget("frame_help").set_use_markup(True)
	wTree.get_widget("frame_contribute").set_label("<b>" + _("Contribute to Linux Mint") + "</b>")
	wTree.get_widget("frame_contribute").set_use_markup(True)
	wTree.get_widget("label_new_features").set_label(_("Browse the list of new features"))
	wTree.get_widget("label_release_notes").set_label(_("Read the release notes"))
	wTree.get_widget("label_user_guide").set_label(_("Download the user guide (PDF)"))
	wTree.get_widget("label_forums").set_label(_("Visit the forums"))
	wTree.get_widget("label_irc").set_label(_("Connect to the chat room"))
	wTree.get_widget("label_sponsor").set_label(_("Become a sponsor"))
	wTree.get_widget("label_donor").set_label(_("Make a donation"))
	wTree.get_widget("label_get_involved").set_label(_("Get involved"))
	wTree.get_widget("checkbutton_show").set_label(_("Show this dialog at startup"))

	gtk.main()
except Exception, detail:
	print detail

