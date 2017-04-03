# Domi-Owned
## Summary ##
Domi-Owned is a tool used for compromising IBM/Lotus Domino servers. 

Tested on IBM/Lotus Domino 8.5.2, 8.5.3, 9.0.0, and 9.0.1 running on Windows and Linux.

## Requirements ##
Domi-Owned uses Python 3, which can be install through your distribution's package manager (apt, yum, etc...)

Run `pip3 install -r requirements.txt` to install the required python modules.
 * [asyncio](https://github.com/python/asyncio)
 * [aiohttp](https://github.com/KeepSafe/aiohttp)
 * [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
 * [inflect](https://github.com/pwdyson/inflect.py)
 * [requests](https://github.com/kennethreitz/requests)
 * [tabulate](https://bitbucket.org/astanin/python-tabulate)
 * [tqdm](https://github.com/noamraph/tqdm)

## Usage ##
A valid username and password is not required unless 'names.nsf' and/or 'webadmin.nsf' requires authentication.

### Fingerprinting ###
Running Domi-Owned with the `fingerprint` action argument, and a URL will attempt to identify the Domino server version, as well as check if 'names.nsf' and 'webadmin.nsf' requires authentication.

If a username and password are given, using the `--username` and `--password` arguments, Domi-Owned will check to see if that account can access 'names.nsf' and 'webadmin.nsf' with those credentials.

#### Example: ####
`./domi-owned.py fingerprint http://domino-server.com`

[![asciicast](https://asciinema.org/a/70ai7hzvnpy9s725hn6csi95t.png)](https://asciinema.org/a/70ai7hzvnpy9s725hn6csi95t)


### Enumerate ###
To enumerate what common or default Domino directories are accessible, run Domi-Owned with the `enumerate` action argument, and the server URL. Optionally, supply Domi-Owned with a username and password, using the `--username` and `--password` arguments, to see what directories that specific user has access to. To use a custom directory wordlist supply Domi-Owned with a file containing a list of web directories using the `--wordlist` argument.

#### Example: ####
`./domi-owned.py enumerate http://domino-server.com`

[![asciicast](https://asciinema.org/a/djovybmla84o692cy9g05ubag.png)](https://asciinema.org/a/djovybmla84o692cy9g05ubag)


### Reverse Brute Force ###
To perform a reverse brute force attack against a Domino server, run Domi-Owned with the `bruteforce` action argument, the server URL, and a list of usernames. Optionally, a password can be specified with the `--password` argument. If a password is not provided, Domi-Owned will use the username, from the username list, as the account password (i.e. 'admin:admin' or 'jsmith:jsmith'). Domi-Owned will then try to authenticate to 'names.nsf', returning successful accounts.

#### Example: ####
`./domi-owned.py bruteforce http://domino-server.com usernames.txt --password PASSWORD`

[![asciicast](https://asciinema.org/a/ecd067vqxx2l2b30bvdynhoau.png)](https://asciinema.org/a/ecd067vqxx2l2b30bvdynhoau)


### Hash Dump ###
To dump all Domino accounts with a __non-empty__ hash, run Domi-Owned with the `hashdump` action argument and the server URL. Optionally, supply Domi-Owned with a username and password using the `--username` and `--password` arguments. This will print the results to the screen and write the account hashes to separate out-files, depending on the hash type (Domino 5, Domino 6, Domino 8).

#### Example: ####
`./domi-owned.py hashdump http://domino-server.com --username USERNAME --password PASSWORD`

[![asciicast](https://asciinema.org/a/bshcclg89hzlx0lmdg9b9q9zx.png)](https://asciinema.org/a/bshcclg89hzlx0lmdg9b9q9zx)


### Quick Console ###
The Domino Quick Console is active by default; however, it will not show the output of issued commands. A work around to this problem is to redirect the command output to a file, in this case 'log.txt', that is then displayed as a web page on the Domino server.

If the `quickconsole` action argument is given, Domi-Owned will access the Domino Quick Console, through 'webadmin.nsf', allowing the user to issue native Windows or Linux commands. Optionally, supply a username and password using the `--username` and `--password` arguments. Domi-Owned will then retrieve the output of the command and display the results in real time through a command line interpreter. Type `exit` to quit the Quick Console interpreter. Upon exit, Domi-Owned will  delete the 'log.txt' output file.

#### Example: ####
`./domi-owned.py quickconsole http://domino-server.com --username USERNAME --password PASSWORD`

[![asciicast](https://asciinema.org/a/84kphfh12ngm5iwn5qc9q1hke.png)](https://asciinema.org/a/84kphfh12ngm5iwn5qc9q1hke)


## Credits ##
Special Thanks:
 * Jeff McCutchan - jamcut ([@jamcut](https://twitter.com/jamcut)) - For coming up with an awesome name!
