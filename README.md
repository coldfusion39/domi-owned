# Domi-Owned
## Summary ##
Domi-Owned is a tool used for compromising IBM/Lotus Domino servers. 

Tested on IBM/Lotus Domino 8.5.2, 8.5.3, 9.0.0, and 9.0.1 running on Windows and Linux.

## Usage ##
A valid username and password is not required unless 'names.nsf' and/or 'webadmin.nsf' requires authentication.

#### Fingerprinting ####
Running Domi-Owned with just a URL will attempt to identify the Domino server version,
as well as check if 'names.nsf' and 'webadmin.nsf' requires authentication.

If a username and password are given, using the'-u' and '-p' flags respectively, Domi-Owned will check to see if that account can
access 'names.nsf' and 'webadmin.nsf' with those credentials.

#### Reverse Brute Force ####
To perform a reverse brute force attack against a Domino server, specify a file containing
a list of usernames with `-u`, a password with `-p`, and the `--bruteforce` flag.
Domi-Owned will then try to authenticate to 'names.nsf', returning successful accounts.

#### Dump Hashes ####
To dump all Domino accounts with a __non-empty__ hash, run Domi-Owned with the `--hashdump` flag.
This prints the results to the screen and writes them to separate out files depending on the hash type (Domino 5, Domino 6, Domino 8).

#### Quick Console ####
The Domino Quick Console is active by default; however, it will not show the output of issued commands.
A work around to this problem is to redirect the command output to a file, in this case 'log.txt', that is then displayed as a web page on the Domino server.

If the `--quickconsole` flag is given, Domi-Owned will access the Domino Quick Console, through 'webadmin.nsf',
allowing the user to issue native Windows or Linux commands. Domi-Owned will then retrieve the output of the command
and display the results in real time through a command line interpreter. Type `exit` to quit the Quick Console
interpreter, which will also delete the 'log.txt' output file.

## Examples ##
###### Fingerprint Domino server

`./domi-owned.py http://domino-server.com`

[![asciicast](https://asciinema.org/a/3ersiac69gte67ckfyi1bjqjw.png)](https://asciinema.org/a/3ersiac69gte67ckfyi1bjqjw?autoplay=1)

###### Preform a reverse brute force attack

`./domi-owned.py http://domino-server.com -u /root/wordlists/usernames.txt -p password --bruteforce`

[![asciicast](https://asciinema.org/a/e0k09i2y83rllv8gqn9aqfdam.png)](https://asciinema.org/a/e0k09i2y83rllv8gqn9aqfdam?autoplay=1)

###### Dump Domino account hashes

`./domi-owned.py http://domino-server.com -u user -p password --hashdump`

[![asciicast](https://asciinema.org/a/a4k4hkrpo4vngtdq90tv95zm0.png)](https://asciinema.org/a/a4k4hkrpo4vngtdq90tv95zm0?autoplay=1)

###### Interact with the Domino Quick Console

`./domi-owned.py http://domino-server.com -u user -p password --quickconsole`

[![asciicast](https://asciinema.org/a/ds9uhrv5w88aoagp4ziok0f0z.png)](https://asciinema.org/a/ds9uhrv5w88aoagp4ziok0f0z?autoplay=1)

## Credits ##
Special Thanks:
 * Jeff McCutchan - jamcut ([@jamcut](https://twitter.com/jamcut)) - For coming up with an awesome name!
