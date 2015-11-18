# Domi-Owned
## Summary ##
Domi-Owned is a tool used for compromising IBM/Lotus Domino servers. 

Tested on IBM/Lotus Domino 8.5.2, 8.5.3, 9.0.0, and 9.0.1 running on Windows.

## Usage ##
A valid username and password is not required unless 'names.nsf' and/or 'webadmin.nsf' requires authentication.

#### Fingerprinting ####
Running Domi-Owned with just the `--url` flag will attempt to identify the Domino server version,
as well as check if 'names.nsf' and 'webadmin.nsf' requires authentication.

#### Dump Hashes ####
To dump all Domino accounts with a __non-empty__ hash from 'names.nsf', run Domi-Owned with the `--hashdump` flag.
This prints the results to the screen and writes them to separate out files depending on the hash type (Domino 5, Domino 6, Domino 8).

#### Quick Console ####
The Domino Quick Console is active by default; however, it will not show the command's output.
A work around to this problem is to redirect the command output to a file, in this case 'log.txt', that is then displayed as a web page on the Domino server.

If the `--quickconsole` flag is given, Domi-Owned will access the Domino Quick Console, through 'webadmin.nsf',
allowing the user to issue native Windows cmd.exe commands. Domi-Owned will then retrieve the output of the command
and display the results in real time, through a command line interpreter. Type `exit` to quit the Quick Console
interpreter, which will also delete the 'log.txt' output file.

## Examples ##
###### Fingerprint Domino server

`python domi-owned.py --url http://domino-server.com`

###### Dump Domino account hashes

`python domi-owned.py --url http://domino-server.com -u user -p password --hashdump`

###### Interact with the Domino Quick Console

`python domi-owned.py --url http://domino-server.com -u user -p password --quickconsole`

## Credits ##
Special Thanks:
 * Jeff McCutchan - jamcut ([@jamcut](https://twitter.com/jamcut)) - For coming up with an awesome name!
