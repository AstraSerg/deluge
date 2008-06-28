#!/usr/bin/env python

"""
deluge-shell: Deluge shell.
"""

# deluge-shell: Deluge shell.
#
# Copyright (C) 2007, 2008 Sadrul Habib Chowdhury <sadrul@users.sourceforge.net>
#
# This application is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This application is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this application; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02111-1301
# USA

from deluge.ui.client import aclient as client
import deluge.common as common
import deluge.error
import readline
import logging

import sys

class Enumerate(object):
	def __init__(self, names):
		for number, name in enumerate(names.split()):
			setattr(self, name, number)

NORMAL = chr(27) + '[00;00m'
NORMAL_B = chr(27) + '[01m'
RED = chr(27) + '[00;31m'
RED_B = chr(27) + '[01;31m'
GREEN = chr(27) + '[00;32m'
GREEN_B = chr(27) + '[01;32m'
YELLOW = chr(27) + '[00;33m'
YELLOW_B = chr(27) + '[01;33m'
BLUE = chr(27) + '[00;34m'
BLUE_B = chr(27) + '[01;34m'
MAGENTA = chr(27) + '[00;35m'
MAGENTA_B = chr(27) + '[01;35m'
CYAN = chr(27) + '[01;36m'
CYAN_B = chr(27) + '[01;36m'

COLORS = Enumerate('RED GREEN YELLOW BLUE MAGENTA CYAN DEFAULT')
ATTRS = Enumerate('BOLD NORMAL')

def ATTR(color, attr, str):
	ret = chr(27) + '['
	if attr == ATTRS.BOLD:
		ret = ret + "01"
	else:
		ret = ret + "02"

	colormaps = {
			COLORS.RED : "31",
			COLORS.GREEN : "32",
			COLORS.YELLOW : "33",
			COLORS.BLUE : "34",
			COLORS.MAGENTA : "35",
			COLORS.CYAN : "36",
			COLORS.DEFAULT : "39"
		}

	if color in colormaps:
		ret = ret + ";" + colormaps[color]
	ret = ret + "m"
	return ret + str + chr(27) + "[0m"

status_keys = ["state",
		"save_path",
		"tracker",
		"next_announce",
		"name",
		"total_size",
		"progress",
		"num_seeds",
		"total_seeds",
		"num_peers",
		"total_peers",
		"eta",
		"download_payload_rate",
		"upload_payload_rate",
		"ratio",
		"distributed_copies",
		"num_pieces",
		"piece_length",
		"total_done",
		"files",
		"file_priorities",
		"file_progress",
		"peers",
		"is_seed",
		]

class Command:
	def __init__(self):
		pass

	def execute(self, cmd):
		pass

	def usage(self):
		print ""

	def help(self):
		pass

	def match_torrents(self, array):
		torrents = []
		def _got_session_state(tors):
			if not array or len(array) == 0:
				for tor in tors:
					torrents.append(tor)
				return
			for match in array:
				for tor in tors:
					if match == tor[0:len(match)]:
						torrents.append(tor)
						break
		client.get_session_state(_got_session_state)
		client.force_call()
		return torrents

class CommandAdd(Command):
	"""Command to add a torrent."""
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return

		save_path = None
		readpath = False
		if cmd[1] == '-p':
			if len(cmd) < 4:
				self.usage()
				return
			del cmd[1]
			readpath = True
		else:
			def _got_config(configs):
				global save_path
				save_path = configs['download_location']
			client.get_config(_got_config)
			client.force_call()

		command = " ".join(cmd[1:])
		paths = command.split(';')
		if readpath:
			save_path = paths[0].strip()   # Perhaps verify that the path exists?
			client.set_config({'download_location': save_path})
			del paths[0]

		if not save_path:
			print "There's no save-path specified. You must specify a path to save the downloaded files.\n"
			return

		for iter in range(0, len(paths)):
			paths[iter] = paths[iter].strip()
			if len(paths[iter]) == 0:
				del paths[iter]

		try:
			client.add_torrent_file(paths)
		except Exception, msg:
			print "*** Error:", str(msg), "\n"

	def usage(self):
		print "Usage: add [-p <save-location>;] <torrent-file>; [<torrent-file>; ...]"
		print "       (Note that a ';' must follow a path)"
		print ""

	def help(self):
		print "Add a torrent"

class CommandConfig(Command):
	def execute(self, cmd):
		del cmd[0]
		def _on_get_config(config):
			for key in config:
				if cmd and key not in cmd:	continue
				color = NORMAL
				value = config[key]
				if isinstance(value, bool):
					color = YELLOW
				elif isinstance(value, int) or isinstance(value, float):
					color = GREEN
				elif isinstance(value, str):
					color = CYAN
				elif isinstance(value, list):
					color = MAGENTA
					
				print ("* " + BLUE_B + "%s:" + color + " %s" + NORMAL) % (key, value)
		client.get_config(_on_get_config)

	def usage(self):
		print "Usage: configs [key1 [key2 ...]]"
		print ""

	def help(self):
		print "Show configuration values"

class CommandExit(Command):
	def execute(self, cmd):
		print "Thanks"
		sys.exit(0)

	def help(self):
		print "Exit from the client."

class CommandHelp(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			print NORMAL_B + "Available commands:" + NORMAL
			for cmd in sorted(commands.keys()):
				print "\t*", "%s:" % (BLUE_B + cmd + NORMAL),
				command = commands[cmd]
				command.help()
		else:
			for c in cmd[1:]:
				if c not in commands:
					print RED + "Unknown command:", c + NORMAL
				else:
					print "*", "%s:" % (BLUE_B + c + NORMAL),
					command = commands[c]
					command.help()
					print GREEN,
					command.usage()
					print NORMAL,

	def usage(self):
		print "Usage: help [cmd1 [cmd2 ...]]"
		print ""

	def help(self):
		print "Show help"

class CommandInfo(Command):
	def execute(self, cmd):
		brief = (len(cmd) < 2)
		torrents = self.match_torrents(cmd[1:])
		for tor in torrents:
			self.show_info(tor, brief)

	def usage(self):
		print "Usage: info [<torrent-id> [<torrent-id> ...]]"
		print "       You can give the first few characters of a torrent-id to identify the torrent."
		print ""

	def help(self):
		print "Show information about the torrents"

	def show_info(self, torrent, brief):
		def _got_torrent_status(state):
			print ATTR(COLORS.BLUE, ATTRS.BOLD, "*** ID:"), torrent
			print ATTR(COLORS.BLUE, ATTRS.BOLD, "*** Name:"), state['name']
			print ATTR(COLORS.BLUE, ATTRS.BOLD, "*** Path:"), state['save_path']

			if not state['is_seed']:
				print ATTR(COLORS.GREEN, 0, "*** Completed:"), common.fsize(state['total_done']) + "/" + common.fsize(state['total_size'])
			print ATTR(COLORS.GREEN, 0, "*** Status:"), state['state']

			state['state_i'] = common.TORRENT_STATE.index(state['state'])
			if state['state_i'] == 2: # Downloading
				print ATTR(COLORS.GREEN, 0, "*** Download Speed:"), common.fspeed(state['download_payload_rate'])
			if state['state_i'] in [2, 3]: # Downloading, or Seeding
				print ATTR(COLORS.GREEN, 0, "*** Upload Speed:"), common.fspeed(state['upload_payload_rate'])
			if state['state_i'] == 2: # Downloading
				print ATTR(COLORS.GREEN, 0, "*** ETA:"), "%s" % common.ftime(state['eta'])

			if brief == False:
				print ATTR(COLORS.DEFAULT, ATTRS.BOLD, "*** Seeders:"), "%s (%s)" % (state['num_seeds'], state['total_seeds'])
				print ATTR(COLORS.DEFAULT, ATTRS.BOLD, "*** Peers:"), "%s (%s)" % (state['num_peers'], state['total_peers'])
				print ATTR(COLORS.DEFAULT, ATTRS.BOLD, "*** Share Ratio:"), "%.1f" % state['ratio']
				print ATTR(COLORS.DEFAULT, ATTRS.BOLD, "*** Availability:"), "%.1f" % state['distributed_copies']
				print ATTR(COLORS.CYAN, ATTRS.BOLD, "*** Files:")
				for i, file in enumerate(state['files']):
					status = ""
					if not state['is_seed']:
						if state['file_priorities'][i] == 0:
							status = " - Do not download"
						else:
							status = " - %1.f%% completed" % (state['file_progress'][i] * 100)
					print "\t* %s (%s)%s" % (file['path'], common.fsize(file['size']), status)

				print ATTR(COLORS.MAGENTA, ATTRS.BOLD, "*** Peers:")
				if len(state['peers']) == 0:
					print "\t* None"
				for peer in state['peers']:
					print ("\t*" + BLUE_B + " %-21s" + GREEN_B + " %-25s " + CYAN + "Up: %-12s" + MAGENTA_B + " Down: %-12s" + NORMAL) % \
						(peer['ip'], peer['client'] + ["", " (seed)"][not not peer['seed']],
							common.fspeed(peer['up_speed']), common.fspeed(peer['down_speed']))
			print ""
		client.get_torrent_status(_got_torrent_status, torrent, status_keys)

class CommandPause(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return
		try:
			torrents = self.match_torrents(cmd[1:])
			client.pause_torrent(torrents)
		except Exception, msg:
			print "Error:", str(msg), "\n"

	def usage(self):
		print "Usage: pause <torrent-id> [<torrent-id> ...]"
		print ""

	def help(self):
		print "Pause a torrent"

class CommandResume(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return
		try:
			torrents = self.match_torrents(cmd[1:])
			client.resume_torrent(torrents)
		except Exception, msg:
			print "Error:", str(msg), "\n"

	def usage(self):
		print "Usage: resume <torrent-id> [<torrent-id> ...]"
		print ""

	def help(self):
		print "Resume a torrent"

class CommandRemove(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return
		try:
			torrents = self.match_torrents(cmd[1:])
			client.remove_torrent(torrents, False, False)
		except Exception, msg:
			print "*** Error:", str(msg), "\n"

	def usage(self):
		print "Usage: rm <torrent-id>"
		print ""

	def help(self):
		print "Remove a torrent"

class CommandHalt(Command):
	def execute(self, cmd):
		client.shutdown()

	def help(self):
		print "Shutdown the deluge server."

class CommandConnect(Command):
	def execute(self, cmd):
		host = 'localhost'
		port = 58846
		if len(cmd) > 1:
			host = cmd[1]
		if len(cmd) > 2:
			port = int(cmd[2])

		if host[:7] != "http://":
			host = "http://" + host

		client.set_core_uri("%s:%d" % (host, port))

	def usage(self):
		print "Usage: connect [<host> [<port>]]"
		print "       'localhost' is the default server. 58846 is the default port."
		print ""

	def help(self):
		print "Connect to a new deluge server."

commands = {
	'add' : CommandAdd(),
	'configs' : CommandConfig(),
	'exit' : CommandExit(),
	'help' : CommandHelp(),
	'info' : CommandInfo(),
	'pause' : CommandPause(),
	'quit' : CommandExit(),
	'resume' : CommandResume(),
	'rm' : CommandRemove(),
	'del' : CommandRemove(),
	'halt' : CommandHalt(),
	'connect' : CommandConnect(),
}

logging.disable(logging.ERROR)
client.set_core_uri("http://localhost:58846")

class NullUI:
	def __init__(self, args):
		print "Welcome to deluge-shell. Type 'help' to see a list of available commands."

		readline.read_init_file()

		while True:
			try:
				inp = raw_input("> ").strip()
			except:
				inp = 'quit'

			if len(inp) == 0:	continue
			inp = inp.split(" ")

			print ""
			cmd = inp[0]
			found = False
			if cmd not in commands:
				print RED + "Invalid command!" + NORMAL
				commands['help'].execute([])
			else:
				command = commands[cmd]
				try:
					command.execute(inp)
					client.force_call()
				except deluge.error.NoCoreError, e:
					print "*** Operation failed. You are not connected to a deluge daemon."
					print "    Perhaps you want to 'connect' first."
					print ""
				#except deluge.error.InvalidTorrent, e:
				#	print "*** Operation failed. You tried to perform an operation on a non-existent torrent."
				#	print "    Use the 'info' command for the list of torrents."
				#	print ""
			print

		print "Thanks."

