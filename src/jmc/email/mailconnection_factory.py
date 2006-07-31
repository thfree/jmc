##
## mailconnection_factory.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Fri May 20 10:41:46 2005 David Rousselie
## $Id: mailconnection_factory.py,v 1.2 2005/09/18 20:24:07 dax Exp $
## 
## Copyright (C) 2005 
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

import jmc.email.mailconnection as mailconnection
from jmc.email.mailconnection import IMAPConnection, POP3Connection

def get_new_mail_connection(type):
    """ Static method to return an empty MailConnection object of given type
    :Parameters:
    - 'type': type of connection to return : 'imap', 'imaps', 'pop3', 'pop3s'
    
    :return: MailConnection of given type in parameter, None if unknown type
    
    :returntype: 'MailConnection'
    """
    if type == "imap":
        return IMAPConnection()
    elif type == "imaps":
        return IMAPConnection(ssl = True)
    elif type == "pop3":
        return POP3Connection()
    elif type == "pop3s":
        return POP3Connection(ssl = True)
    raise Exception, "Connection type \"" + type + "\" unknown"

def str_to_mail_connection(connection_string):
    """ Static methode to create a MailConnection object filled from string 
    
    :Parameters:
    - 'connection_string': string containing MailConnection parameters separated
    by '#'. ex: 'pop3#login#password#host#110#chat_action#online_action#away_action#xa_action#dnd_action#offline_action#check_interval#liv_email_only(#Mailbox)'
    
    :Types:
    - 'connection_string': string
    
    :return: MailConnection of given type found in string parameter
    
    :returntype: 'MailConnection'
    """
    arg_list = connection_string.split("#")
    # optionals values must be the at the beginning of the list to pop them
    # last
    arg_list.reverse()
    type = arg_list.pop()
    login = arg_list.pop()
    password = arg_list.pop()
    if password == "/\\":
        password = None
        store_password = False
    else:
        store_password = True
    host = arg_list.pop()
    port = int(arg_list.pop())
    chat_action = None
    online_action = None
    away_action = None
    xa_action = None
    dnd_action = None
    offline_action = None
    interval = None
    live_email_only = False
    result = None
    if type[0:4] == "imap":
        if len(arg_list) == 9:
            chat_action = int(arg_list.pop())
            online_action = int(arg_list.pop())
            away_action = int(arg_list.pop())
            xa_action = int(arg_list.pop())
            dnd_action = int(arg_list.pop())
            offline_action = int(arg_list.pop())
            interval = int(arg_list.pop())
            live_email_only = (arg_list.pop().lower() == "true")
        else:
            retrieve = bool(arg_list.pop() == "True")
            if retrieve:
                chat_action = online_action = away_action = xa_action = dnd_action = mailconnection.RETRIEVE
            else:
                chat_action = online_action = away_action = xa_action = dnd_action = mailconnection.DIGEST                
            offline_action = mailconnection.DO_NOTHING
        mailbox = arg_list.pop()
        result = IMAPConnection(login = login, \
                                password = password, \
                                host = host, \
                                ssl = (len(type) == 5), \
                                port = port, \
                                mailbox = mailbox)
    elif type[0:4] == "pop3":
        if len(arg_list) == 8:
            chat_action = int(arg_list.pop())
            online_action = int(arg_list.pop())
            away_action = int(arg_list.pop())
            xa_action = int(arg_list.pop())
            dnd_action = int(arg_list.pop())
            offline_action = int(arg_list.pop())
            interval = int(arg_list.pop())
            live_email_only = (arg_list.pop().lower() == "true")
        else:
            retrieve = bool(arg_list.pop() == "True")
            if retrieve:
                chat_action = online_action = away_action = xa_action = dnd_action = mailconnection.RETRIEVE
            else:
                chat_action = online_action = away_action = xa_action = dnd_action = mailconnection.DIGEST                
            offline_action = mailconnection.DO_NOTHING
        result = POP3Connection(login = login, \
                                password = password, \
                                host = host, \
                                port = port, \
                                ssl = (len(type) == 5))
    if result is None:
        raise Exception, "Connection type \"" + type + "\" unknown"
    result.store_password = store_password
    result.chat_action = chat_action
    result.online_action = online_action
    result.away_action = away_action
    result.xa_action = xa_action
    result.dnd_action = dnd_action
    result.offline_action = offline_action
    if interval is not None:
        result.interval = interval
    result.live_email_only = live_email_only
    return result

