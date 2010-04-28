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
import webkit
import string

# i18n
gettext.install("mintwelcome", "/usr/share/linuxmint/locale")

class MintWelcome():
	def __init__(self):
		gladefile = "/usr/lib/linuxmint/mintWelcome/mintWelcome.glade"
		wTree = gtk.glade.XML(gladefile,"main_window")
		wTree.get_widget("main_window").set_title(_("Welcome to Linux Mint"))
		wTree.get_widget("main_window").set_icon_from_file("/usr/share/linuxmint/logo.png")	

		sys.path.append('/usr/lib/linuxmint/common')
		from configobj import ConfigObj
		config = ConfigObj("/etc/linuxmint/info")
		description = config['DESCRIPTION']
		codename = config['CODENAME']
		edition = config['EDITION']
		release = config['RELEASE']
		description = description.replace("\"", "")
		self.release_notes = config['RELEASE_NOTES_URL']
		self.user_guide = config['USER_GUIDE_URL']
		self.new_features = config['NEW_FEATURES_URL']
	
		wTree.get_widget("main_window").connect("destroy", gtk.main_quit)	

		browser = webkit.WebView()
		wTree.get_widget("scrolled_welcome").add(browser)
		browser.connect("button-press-event", lambda w, e: e.button == 3)
		subs = {}
		subs['release'] = release + " (" + codename + ")"
		subs['edition'] = edition
		subs['title'] = _("Welcome to Linux Mint")
		subs['release_title'] = _("Release")
		subs['edition_title'] = _("Edition")
		subs['discover_title'] = _("Documentation")
		subs['find_help_title'] = _("Support")
		subs['contribute_title'] = _("Project")
		subs['community_title'] = _("Community")
		subs['new_features'] = _("New features")
		subs['know_problems'] = _("Known problems")
		subs['user_guide'] = _("User guide (PDF)")
		subs['forums'] = _("Forums")
		subs['irc'] = _("Chat room")
		subs['sponsor'] = _("Sponsors")
		subs['donation'] = _("Donations")
		subs['get_involved'] = _("How to get involved")
		subs['ideas'] = _("Idea pool")
		subs['software'] = _("Software reviews")
		subs['hardware'] = _("Hardware database")
		subs['tutorials'] = _("Tutorials")
		subs['show'] = _("Show this dialog at startup")
		subs['close'] = _("Close")
		if os.path.exists(home + "/.linuxmint/mintWelcome/norun.flag"):		
			subs['checked'] = ("")
		else:
			subs['checked'] = ("CHECKED")

		subs['welcome'] = _("Welcome and thank you for choosing Linux Mint. We hope you'll enjoy using it as much as we did designing it. The links below will help you get started with your new operating system. Have a great time and don't hesitate to send us your feedback.")
		template = open("/usr/lib/linuxmint/mintWelcome/templates/welcome.html").read()		
		html = string.Template(template).safe_substitute(subs)
		browser.load_html_string(html, "file:/")	
		browser.connect('title-changed', self.title_changed)
		wTree.get_widget("main_window").show_all()

	def title_changed(self, view, frame, title):	
		if title.startswith("nop"):
		    return
		# call directive looks like:
		#  "call:func:arg1,arg2"
		#  "call:func"
		if title == "event_irc":
			if os.path.exists("/usr/bin/xchat-gnome"):
				os.system("/usr/bin/xchat-gnome &")
			elif os.path.exists("/usr/bin/xchat"):
				os.system("/usr/bin/xchat &")
			elif os.path.exists("/usr/bin/konversation"):
				os.system("/usr/bin/konversation &")
			elif os.path.exists("/usr/bin/quassel"):
				os.system("/usr/bin/quassel &")
		elif title == "event_new_features":
			os.system("xdg-open " + self.new_features)
		elif title == "event_known_problems":
			os.system("xdg-open " + self.release_notes)
		elif title == "event_user_guide":
			os.system("xdg-open " + self.user_guide)
		elif title == "event_forums":
			os.system("xdg-open http://forums.linuxmint.com")
		elif title == "event_tutorials":
			os.system("xdg-open http://community.linuxmint.com/tutorial")
		elif title == "event_ideas":
			os.system("xdg-open http://community.linuxmint.com/idea")
		elif title == "event_software":
			os.system("xdg-open http://community.linuxmint.com/software")
		elif title == "event_hardware":
			os.system("xdg-open http://community.linuxmint.com/hardware")
		elif title == "event_get_involved":
			os.system("xdg-open http://www.linuxmint.com/get_involved.php")
		elif title == "event_sponsor":
			os.system("xdg-open http://www.linuxmint.com/sponsors.php")
		elif title == "event_donation":
			os.system("xdg-open http://www.linuxmint.com/donors.php")
		elif title == "event_close_true":
			if os.path.exists(home + "/.linuxmint/mintWelcome/norun.flag"):
				os.system("rm -rf " + home + "/.linuxmint/mintWelcome/norun.flag")
			gtk.main_quit()
		elif title == "event_close_false":
			os.system("mkdir -p " + home + "/.linuxmint/mintWelcome")		
			os.system("touch " + home + "/.linuxmint/mintWelcome/norun.flag")
			gtk.main_quit()
		elif title == "checkbox_checked":
			if os.path.exists(home + "/.linuxmint/mintWelcome/norun.flag"):
				os.system("rm -rf " + home + "/.linuxmint/mintWelcome/norun.flag")
		elif title == "checkbox_unchecked":
			os.system("mkdir -p " + home + "/.linuxmint/mintWelcome")		
			os.system("touch " + home + "/.linuxmint/mintWelcome/norun.flag")		


if __name__ == "__main__":
	MintWelcome()	
	gtk.main()

