# checkmail

Check if gmail account exists or not.

## Getting Started

Clone the repository and run
```
poetry install
```

## Help

```
poetry run ./checkmail.py -h
usage: checkmail.py [-h] (-u USERNAME | -U FILE) [-o OUTFILE] [-c COMPARE] [--cmpout CMP_OUTFILE] [-x PROXY] [-t MAXCONN] [--url URL] [--shuffle] [--notify NOTIFY] [-s SLEEP]
                    [-j JITTER] [-H HEADERS] [-A NAME] [--rua] [--only-new] [--timeout TIMEOUT] [-v]

This is a script to check if given account(s) exists or not at GMail. The decision is made upon the existence or not of COMPASS cookie in the response.

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Single username
  -U FILE, --usernames FILE
                        File containing usernames in the format 'user@domain'.
  -o OUTFILE, --out OUTFILE
                        A file to output valid results to (default: valid_users.txt).
  -c COMPARE, --compare COMPARE
                        Compare current result against a previous one and ouput only differences.
  --cmpout CMP_OUTFILE  A file to output the results of usernames comparison (default: cmp_users.txt)
  -x PROXY, --proxy PROXY
                        Use proxy on requests (e.g. http://127.0.0.1:8080)
  -t MAXCONN, --max-connections MAXCONN
                        Maximum number of simultaneous connections (default: 20)
  --url URL             Target URL (default: https://mail.google.com). Potentially useful if pointing at an API Gateway URL generated with something like FireProx to randomize
                        the IP address you are connecting from.
  --shuffle             Shuffle user list.
  --notify NOTIFY       Slack webhook for sending notifications about results (default: None).
  -s SLEEP, --sleep SLEEP
                        Sleep this many seconds between tries (default: 0).
  -j JITTER, --jitter JITTER
                        Maximum of additional delay given in percentage over base delay (default: 0).
  -H HEADERS, --header HEADERS
                        Extra header to include in the request (can be used multiple times).
  -A NAME, --user-agent NAME
                        Send User-Agent NAME to server (default: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110
                        Safari/537.36").
  --rua                 Send random User-Agent in each request.
  --only-new            When used with -c, ommit entries that were not present in compared file, i.e., shows only new observed entries.
  --timeout TIMEOUT     Total timeout for requests, in seconds (default: 60)
  -v, --verbose         Prints detailed information.

EXAMPLE USAGE:
This command will use the provided userlist and output the results.
    poetry run ./checkmail.py --userlist ./userlist.txt

This command uses the specified FireProx URL to check from randomized IP addresses and writes the output to a file. See this for FireProx setup: https://github.com/ustayready/fireprox.
    poetry run ./checkmail.py --userlist ./userlist.txt --url https://api-gateway-endpoint-id.execute-api.us-east-1.amazonaws.com/fireprox --out valid-users.txt

TIPS:
[1] When using along with FireProx, pass option -H "X-My-X-Forwarded-For: 127.0.0.1" to spoof origin IP.
```

## Example

Check for valid users from an input file

```
poetry run ./checkmail.py --timeout 90 -v -t 3 -s 10 --rua -U users.txt --shuffle -x http://127.0.0.1:5566 -o valids.txt
```

Check for valid users and compare the results with a previous result (useful for identifying new accounts)

```
poetry run ./checkmail.py --timeout 60 -v -t 3 -s 10 --rua -U users.txt --shuffle -x http://127.0.0.1:5566 --compare valids.txt --only-new -o newusers.txt
```

## License

This project is licensed under MIT License. For more information, please see [LICENSE](LICENSE).


## Disclaimer

For educational purposes only. Use at your own risk.