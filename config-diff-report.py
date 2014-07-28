#!/bin/env python3
# -*- coding: utf-8 -*-
''' Generate LaTeX report about difference between current
    and previously saved RouterOS configurations
'''

import paramiko
import difflib
import sys
import socket
import traceback
import getpass
import subprocess
import os
import datetime
import shutil

file_config_name_postfix = '_config.txt'
file_diff_name = 'diff.txt'
hostname_file_name = 'hostname.txt'
latex_command = 'xelatex'
backup_dir_name = 'report_backups'
original_report_file_name = 'report.pdf'

def get_transport(host):
    ''' Ask username/password for given host and try to connect to it
        Return the "transport" object (I have no idea what that means)
    '''
    port = 22

    # Try to connect
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    except Exception as ex:
        print('*** Connect failed: ' + str(ex))
        traceback.print_exc()
        sys.exit(1)

    transport = paramiko.Transport(sock)
    try:
        transport.start_client()
    except paramiko.SSHException:
        print('*** SSH negotiation failed.')
        sys.exit(1)

    username = ''
    while len(username) == 0:
        username = input('Username: ')

    password = getpass.getpass('Password for %s@%s: ' % (username, host))
    transport.auth_password(username, password)

    return transport


def write_diff(file_name, old, new):
    ''' Calculates the difference between old and new config strings
        Writes the difference in file_name and on the console
    '''
    with open(file_name, 'w') as file_diff:
        for diffline in difflib.ndiff(old.splitlines(), new.splitlines()):
            if diffline[:2] in ['+ ', '- ']:
                print(diffline)
                print(diffline, file=file_diff)

def get_new_config(transport):
    ''' Fetches configuration from MikroTik RouterOS
    '''
    chan = transport.open_session()
    chan.exec_command('/export compact hide-sensitive')

    new = ''

    while True:
        if chan.recv_ready():
            new += chan.recv(4096).decode('ascii')
        if chan.exit_status_ready():
            print('exit status: %s' % chan.recv_exit_status())
            break
        if chan.recv_stderr_ready():
            print('error: %s' % chan.recv_stderr(4096).decode('ascii'))

    chan.close()
    transport.close()
    return new

def get_old_write_new_config(new, filename_config):
    ''' Writes new configuration into filename_config
        Returns the old configuration read from the same file
    '''
    try:
        file_config = open(filename_config, 'r+')
        old = file_config.read()
        file_config.seek(0)
        file_config.truncate()
    except FileNotFoundError:
        print('Old config file not found, creating one with new config.')
        file_config = open(filename_config, 'w')
        old = ''

    file_config.writelines(new)
    file_config.close()

    return old


hostname = ''
while len(hostname) == 0:
    hostname = input('RouterOS IP address: ')

with open(hostname_file_name, 'w') as hostname_file:
    hostname_file.write(hostname)

t = get_transport(hostname)
new_config = get_new_config(t)
old_config = get_old_write_new_config(new_config,
                                      hostname + file_config_name_postfix)
write_diff(file_diff_name, old_config, new_config)


if subprocess.call([latex_command, 'report.tex']) != 0:
    print('Could not execute ' + latex_command + '!!!')
    input()
    exit()


os.makedirs(backup_dir_name, exist_ok=True)
shutil.copy(original_report_file_name, backup_dir_name)
os.chdir(backup_dir_name)

current_date_time = datetime.datetime.now().strftime('%y-%m-%d_%H-%M')
result_file_name = current_date_time + \
                   '__' + \
                   hostname + \
                   '__' + \
                   original_report_file_name

os.rename(original_report_file_name, result_file_name)

if sys.platform.startswith('linux'):
    subprocess.call(['xdg-open', result_file_name])
else:
    os.startfile(result_file_name)

