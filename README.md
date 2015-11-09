# Domi-Owned
IBM/Lotus Domino exploitation 

## Summary ##
Domi-Owned is a tool used for compromising IBM/Lotus Domino servers. 

Tested on IBM/Lotus Domino 8.5.3, 9.0.0, and 9.0.1 running on Windows.

## Usage ##
A valid username and password is not required unless `names.nsf` and/or `webadmin.nsf` requires authentication.

#### Fingerprinting ####
Running Domi-Owned with just the `--url` flag will attempt to identify the Domino server version,
as well as check if `names.nsf` and `webadmin.nsf` requires authentication.

#### Dump Hashes ####
To dump all Domino account usernames and passwords from `names.nsf`, run Dominos-OWN with the `--hashdump` flag.

#### Quick Console ####
The Domino Quick Console is active by default; however, it will not show the output of issued command.
A work around to this problem is to redirect the command output to a file, `log.txt`,
that is then displayed as a webpage on the Domino server.

If the `--quickconsole` flag is given, Domi-Owned will access the Domino Quick Console, through `webadmin.nsf`,
allowing the user to issue native Windows cmd.exe commands. Domi-Owned will then retrieve the output of the command
and display the results in real time, through a command line interpreter. Type `exit` to quit the Quick Console
interpreter, which will delete the `log.txt` output file and exit the Domi-Owned script.

## Examples ##
Fingerprint Domino server

`python domi-owned.py --url http://domino-server.com`

Dump Domino account hashes

`python domi-owned.py --url http://domino-server.com -u user -p password --hashdump`

Use the Domino Quick Console to interact with the underlying Windows operating system

`python domi-owned.py --url http://domino-server.com -u user -p password --quickconsole`

## Credits ##
Special Thanks:
 * Jeff McCutchan - jamcut ([@jamcut](https://twitter.com/jamcut)) - For coming up with an awesome name!
