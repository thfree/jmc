##
## account.py
## Login : <dax@happycoders.org>
## Started on  Fri Jan 19 18:21:44 2007 David Rousselie
## $Id$
## 
## Copyright (C) 2007 David Rousselie
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##

import sys
import logging
import email
import email.Header
import traceback

import poplib
import imaplib
import socket

from sqlobject.inheritance import InheritableSQLObject
from sqlobject.col import StringCol, IntCol, BoolCol

from jcl.model import account
from jcl.model.account import Account, PresenceAccount
from jmc.lang import Lang

IMAP4_TIMEOUT = 10
POP3_TIMEOUT = 10

## All MY* classes are implemented to add a timeout (settimeout)
## while connecting
class MYIMAP4(imaplib.IMAP4):
    def open(self, host = '', port = imaplib.IMAP4_PORT):
        """Setup connection to remote server on "host:port"
            (default: localhost:standard IMAP4 port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	self.sock.settimeout(IMAP4_TIMEOUT)
        self.sock.connect((host, port))
	self.sock.settimeout(None)
        self.file = self.sock.makefile('rb')

class MYIMAP4_SSL(imaplib.IMAP4_SSL):
    def open(self, host = '', port = imaplib.IMAP4_SSL_PORT):
        """Setup connection to remote server on "host:port".
            (default: localhost:standard IMAP4 SSL port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	self.sock.settimeout(IMAP4_TIMEOUT)
        self.sock.connect((host, port))
	self.sock.settimeout(None)
        self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)

class MYPOP3(poplib.POP3):
    def __init__(self, host, port = poplib.POP3_PORT):
        self.host = host
        self.port = port
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
		self.sock.settimeout(POP3_TIMEOUT)
                self.sock.connect(sa)
		self.sock.settimeout(None)
            except socket.error, msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
        self.file = self.sock.makefile('rb')
        self._debugging = 0
        self.welcome = self._getresp()

class MYPOP3_SSL(poplib.POP3_SSL):
    def __init__(self, host, port = poplib.POP3_SSL_PORT, keyfile = None, certfile = None):
        self.host = host
        self.port = port
        self.keyfile = keyfile
        self.certfile = certfile
        self.buffer = ""
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
		self.sock.settimeout(POP3_TIMEOUT)
                self.sock.connect(sa)
		self.sock.settimeout(None)
            except socket.error, msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
        self.file = self.sock.makefile('rb')
        self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)
        self._debugging = 0
        self.welcome = self._getresp()

class MailAccount(PresenceAccount):
    """ Wrapper to mail connection and action.
    Abstract class, do not represent real mail connection type"""

    # Define constants
    DIGEST = 1
    RETRIEVE = 2
    default_encoding = "iso-8859-1"
    possibles_actions = [PresenceAccount.DO_NOTHING, \
                         DIGEST, \
                         RETRIEVE]

    login = StringCol(default = "")
    password = StringCol(default = None)
    host = StringCol(default = "localhost")
    port = IntCol(default = 110)
    ssl = BoolCol(default = False)
    interval = IntCol(default = 5)
    store_password = BoolCol(default = True)
    live_email_only = BoolCol(default = False)
    
    lastcheck = IntCol(default = 0)
    waiting_password_reply = BoolCol(default = False)
    first_check = BoolCol(default = True)
    
    def _init(self, *args, **kw):
        """MailAccount init
        Initialize class attributes"""
        PresenceAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.MailAccount")
        self.connection = None
        self.connected = False
        self.default_lang_class = Lang.en # TODO: use String
    
    def _get_register_fields(cls):
        """See Account._get_register_fields
        """
        def password_post_func(password):
            if password is None or password == "":
                return None
            return password
        
        return PresenceAccount.get_register_fields() + \
               [("login", "text-single", None, account.string_not_null_post_func, \
                 account.mandatory_field), \
                ("password", "text-private", None, password_post_func, \
                 (lambda field_name: None)), \
                ("host", "text-single", None, account.string_not_null_post_func, \
                 account.mandatory_field), \
                ("port", "text-single", None, account.int_post_func, \
                 account.mandatory_field), \
                ("ssl", "boolean", None, account.default_post_func, \
                 (lambda field_name: None)), \
                ("store_password", "boolean", None, account.default_post_func, \
                 (lambda field_name: True)), \
                ("live_email_only", "boolean", None, account.default_post_func, \
                 lambda field_name: False)]
    
    get_register_fields = classmethod(_get_register_fields)
    
    def _get_presence_actions_fields(cls):
        """See PresenceAccount._get_presence_actions_fields
        """
        return {'chat_action': (cls.possibles_actions, \
                                RETRIEVE), \
                'online_action': (cls.possibles_actions, \
                                  RETRIEVE), \
                'away_action': (cls.possibles_actions, \
                                RETRIEVE), \
                'xa_action': (cls.possibles_actions, \
                              RETRIEVE), \
                'dnd_action': (cls.possibles_actions, \
                               RETRIEVE), \
                'offline_action': (cls.possibles_actions, \
                                   PresenceAccount.DO_NOTHING)}
    
    get_presence_actions_fields = classmethod(_get_presence_actions_fields)

    def get_decoded_part(self, part, charset_hint):
        content_charset = part.get_content_charset()
        result = u""
        try:
            if content_charset:
                result = unicode(part.get_payload(decode=True).decode(content_charset))
            else:
                result = unicode(part.get_payload(decode=True))
        except Exception, e:
            try:
                result = unicode(part.get_payload(decode=True).decode("iso-8859-1"))
            except Exception, e:
                try:
                    result = unicode(part.get_payload(decode=True).decode(default_encoding))
                except Exception, e:
                    if charset_hint is not None:
                        try:
                            result = unicode(part.get_payload(decode=True).decode(charset_hint))
                        except Exception, e:
                            type, value, stack = sys.exc_info()
                            print >>sys.stderr, "".join(traceback.format_exception
                                                        (type, value, stack, 5))

        return result
            
    def format_message(self, email_msg, include_body = True):
        from_decoded = email.Header.decode_header(email_msg["From"])
        charset_hint = None
        email_from = u""
        result = u"From : "
        for i in range(len(from_decoded)):
            try:
                if from_decoded[i][1]:
                    charset_hint = from_decoded[i][1]
                    email_from += unicode(from_decoded[i][0].decode(from_decoded[i][1]))
                else:
                    email_from += unicode(from_decoded[i][0])
            except Exception,e:
                try:
                    email_from += unicode(from_decoded[i][0].decode("iso-8859-1"))
                except Exception, e:
                    try:
                        email_from += unicode(from_decoded[i][0].decode(default_encoding))
                    except Exception, e:
                        type, value, stack = sys.exc_info()
                        print >>sys.stderr, "".join(traceback.format_exception
                                                    (type, value, stack, 5))
        result += email_from + u"\n"

        subject_decoded = email.Header.decode_header(email_msg["Subject"])
        result += u"Subject : "
        for i in range(len(subject_decoded)):
            try:
                if subject_decoded[i][1]:
                    charset_hint = subject_decoded[i][1]
                    result += unicode(subject_decoded[i][0].decode(subject_decoded[i][1]))
                else:
                    result += unicode(subject_decoded[i][0])
            except Exception,e:
                try:
                    result += unicode(subject_decoded[i][0].decode("iso-8859-1"))
                except Exception, e:
                    try:
                        result += unicode(subject_decoded[i][0].decode(default_encoding))
                    except Exception, e:
                        if charset_hint is not None:
                            try:
                                result += unicode(subject_decoded[i][0].decode(charset_hint))
                            except Exception, e:
                                type, value, stack = sys.exc_info()
                                print >>sys.stderr, "".join(traceback.format_exception
                                                            (type, value, stack, 5))
                                
        result += u"\n\n"

        if include_body:
            action = {
                "text/plain" : lambda part: self.get_decoded_part(part, charset_hint),
                "text/html" : lambda part: "\n<<<HTML part skipped>>>\n"
                }
            for part in email_msg.walk():
                content_type = part.get_content_type()
                if action.has_key(content_type):
                    result += action[content_type](part) + u'\n'
        return (result, email_from)

    def format_message_summary(self, email_msg):
        return self.format_message(email_msg, False)
        
    def get_status_msg(self):
	return self.get_type() + "://" + self.login + "@" + self.host + ":" + \
	    unicode(self.port)

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def get_mail_list(self):
        raise NotImplementedError

    def get_mail(self, index):
        raise NotImplementedError

    def get_mail_summary(self, index):
        raise NotImplementedError

    def get_next_mail_index(self, mail_list):
        raise NotImplementedError

    def is_mail_list_valid(self, mail_list):
        return (mail_list and mail_list != [] and mail_list[0] != '')

    # Does not modify server state but just internal JMC state
    def mark_all_as_read(self):
        raise NotImplementedError

class IMAPAccount(MailAccount):
    mailbox = StringCol(default = "INBOX") # TODO : set default INBOX in reg_form (use get_register_fields last field ?)

    def _get_register_fields(cls):
        """See Account._get_register_fields
        """
        def password_post_func(password):
            if password is None or password == "":
                return None
            return password
        
        return MailAccount.get_register_fields() + \
               [("mailbox", "text-single", None, account.string_not_null_post_func, \
                 (lambda field_name: "INBOX"))]
    
    get_register_fields = classmethod(_get_register_fields)


    def _init(self, *args, **kw):
	MailAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.IMAPConnection")

    def get_type(self):
	if self.ssl:
	    return "imaps"
	return "imap"
	    
    def get_status(self):
	return MailAccount.get_status(self) + "/" + self.mailbox

    def connect(self):
	self.__logger.debug("Connecting to IMAP server " \
                                     + self.login + "@" + self.host + ":" + str(self.port) \
                                     + " (" + self.mailbox + "). SSL=" \
                                     + str(self.ssl))
	if self.ssl:
	    self.connection = MYIMAP4_SSL(self.host, self.port)
	else:
	    self.connection = MYIMAP4(self.host, self.port)
	self.connection.login(self.login, self.password)
        self.connected = True

    def disconnect(self):
	self.__logger.debug("Disconnecting from IMAP server " \
                                     + self.host)
	self.connection.logout()
        self.connected = False

    def get_mail_list(self):
	self.__logger.debug("Getting mail list")
	typ, data = self.connection.select(self.mailbox)
	typ, data = self.connection.search(None, 'RECENT')
	if typ == 'OK':
	    return data[0].split(' ')
	return None

    def get_mail(self, index):
	self.__logger.debug("Getting mail " + str(index))
	typ, data = self.connection.select(self.mailbox, True)
	typ, data = self.connection.fetch(index, '(RFC822)')
	if typ == 'OK':
            return self.format_message(email.message_from_string(data[0][1]))
	return u"Error while fetching mail " + str(index)
	
    def get_mail_summary(self, index):
	self.__logger.debug("Getting mail summary " + str(index))
	typ, data = self.connection.select(self.mailbox, True)
	typ, data = self.connection.fetch(index, '(RFC822)')
	if typ == 'OK':
            return self.format_message_summary(email.message_from_string(data[0][1]))
	return u"Error while fetching mail " + str(index)

    def get_next_mail_index(self, mail_list):
        if self.is_mail_list_valid(mail_list):
            return mail_list.pop(0)
        else:
            return None

    def mark_all_as_read(self):
        self.get_mail_list()
    
    type = property(get_type)

class POP3Account(MailAccount):
    nb_mail = IntCol(default = 0)
    lastmail = IntCol(default = 0)
    
    def _init(self, *args, **kw):
	MailAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.POP3Account")

    def get_type(self):
	if self.ssl:
	    return "pop3s"
	return "pop3"

    type = property(get_type)

    def connect(self):
	self.__logger.debug("Connecting to POP3 server " \
                            + self.login + "@" + self.host + ":" + str(self.port)\
                            + ". SSL=" + str(self.ssl))
	if self.ssl:
	    self.connection = MYPOP3_SSL(self.host, self.port)
	else:
	    self.connection = MYPOP3(self.host, self.port)
	try:
	  self.connection.apop(self.login, self.password)
	except:
	  self.connection.user(self.login)
	  self.connection.pass_(self.password)
        self.connected = True
	

    def disconnect(self):
	self.__logger.debug("Disconnecting from POP3 server " \
                            + self.host)
	self.connection.quit()
        self.connected = False

    def get_mail_list(self):
	self.__logger.debug("Getting mail list")
	count, size = self.connection.stat()
        self.nb_mail = count 
        return [str(i) for i in range(1, count + 1)]

    def get_mail(self, index):
	self.__logger.debug("Getting mail " + str(index))
	ret, data, size = self.connection.retr(index)
        try:
            self.connection.rset()
        except:
            pass
	if ret[0:3] == '+OK':
            return self.format_message(email.message_from_string('\n'.join(data)))
	return u"Error while fetching mail " + str(index)

    def get_mail_summary(self, index):
	self.__logger.debug("Getting mail summary " + str(index))
	ret, data, size = self.connection.retr(index)
        try:
            self.connection.rset()
        except:
            pass
	if ret[0:3] == '+OK':
            return self.format_message_summary(email.message_from_string('\n'.join(data)))
	return u"Error while fetching mail " + str(index)

    def get_next_mail_index(self, mail_list):
        if self.is_mail_list_valid(mail_list):
            if self.nb_mail == self.lastmail:
                return None
            if self.nb_mail < self.lastmail:
                self.lastmail = 0
            result = int(mail_list[self.lastmail])
            self.lastmail += 1
            return result
        else:
            return None

    def mark_all_as_read(self):
        self.get_mail_list()
        self.lastmail = self.nb_mail
        
