from __future__ import annotations

from datetime import datetime, timezone

import time
from urllib import parse
import aiohttp
import base64
import time
import json
import copy
import contextlib
import os
import asyncio
import discord
import websockets
from discord.ext import commands, tasks
from os.path import exists

import matplotlib.pyplot as plt
import numpy as np
from math import sin, cos, radians

class FailedToConnect(Exception):
    pass
class InvalidRequest(Exception):
    def __init__(self, *args, code=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code
class InvalidAttributeCombination(Exception):
    pass


class Auth:
    """ Holds the authentication information """

    @staticmethod
    def get_basic_token(email: str, password: str) -> str:
        return base64.b64encode(f"{email}:{password}".encode("utf-8")).decode("utf-8")

    def __init__(
            self,
            email: str = None,
            password: str = None,
            token: str = None,
            appid: str = None,
            creds_path: str = None,
            cachetime: int = 120,
            max_connect_retries: int = 1,
            session: aiohttp.ClientSession() = None,
            refresh_session_period: int = 180,
            item_id: str = "",
    ):
        self.session: aiohttp.ClientSession() = session or aiohttp.ClientSession()
        self.max_connect_retries: int = max_connect_retries
        self.refresh_session_period: int = refresh_session_period

        self.token: str = token or Auth.get_basic_token(email, password)
        self.creds_path: str = creds_path or f"{os.getcwd()}/creds/{self.token}.json"
        self.appid: str = appid or 'e3d5ea9e-50bd-43b7-88bf-39794f4e3d40'
        self.sessionid: str = ""
        self.key: str = ""
        self.new_key: str = ""
        self.spaceid: str = ""
        self.spaceids: dict[str: str] = {
            "uplay": "0d2ae42d-4c27-4cb7-af6c-2099062302bb",
            "psn": "0d2ae42d-4c27-4cb7-af6c-2099062302bb",
            "xbl": "0d2ae42d-4c27-4cb7-af6c-2099062302bb"
        }
        self.profileid: str = ""
        self.userid: str = ""
        self.expiration: str = ""
        self.new_expiration: str = ""

        self.cachetime: int = cachetime
        self.cache = {}

        self._login_cooldown: int = 0
        self._session_start: float = time.time()

    async def _ensure_session_valid(self) -> None:
        if not self.session:
            await self.refresh_session()
        elif 0 <= self.refresh_session_period <= (time.time() - self._session_start):
            await self.refresh_session()

    async def refresh_session(self) -> None:
        """ Closes the current session and opens a new one """
        if self.session:
            try:
                await self.session.close()
            except:
                pass

        self.session = aiohttp.ClientSession()
        self._session_start = time.time()

    async def get_session(self) -> aiohttp.ClientSession():
        """ Retrieves the current session, ensuring it's valid first """
        await self._ensure_session_valid()
        return self.session

    def save_creds(self) -> None:
        """ Saves the credentials to a file """

        if not os.path.exists(os.path.dirname(self.creds_path)):
            os.makedirs(os.path.dirname(self.creds_path))

        if not os.path.exists(self.creds_path):
            with open(self.creds_path, 'w') as f:
                json.dump({}, f)

        # write to file, overwriting the old one
        with open(self.creds_path, 'w') as f:
            json.dump({
                "sessionid": self.sessionid,
                "key": self.key,
                "new_key": self.new_key,
                "spaceid": self.spaceid,
                "profileid": self.profileid,
                "userid": self.userid,
                "expiration": self.expiration,
                "new_expiration": self.new_expiration,
            }, f, indent=4)

    def load_creds(self) -> None:
        """ Loads the credentials from a file """

        if not os.path.exists(self.creds_path):
            return

        with open(self.creds_path, "r") as f:
            data = json.load(f)

        self.sessionid = data.get("sessionid", "")
        self.key = data.get("key", "")
        self.new_key = data.get("new_key", "")
        self.spaceid = data.get("spaceid", "")
        self.profileid = data.get("profileid", "")
        self.userid = data.get("userid", "")
        self.expiration = data.get("expiration", "")
        self.new_expiration = data.get("new_expiration", "")

        self._login_cooldown = 0

    async def connect(self, _new: bool = False) -> None:
        """ Connect to Ubisoft, automatically called when needed """
        self.load_creds()

        if self._login_cooldown > time.time():
            raise FailedToConnect("Login on cooldown")

        # If keys are still valid, don't connect again
        if _new:
            if self.new_key and datetime.fromisoformat(self.new_expiration[:26]+"+00:00") > datetime.now(timezone.utc):
                return
        else:
            if self.key and datetime.fromisoformat(self.expiration[:26]+"+00:00") > datetime.now(timezone.utc):
                await self.connect(_new=True)
                return

        session = await self.get_session()
        headers = {
            "User-Agent": "UbiServices_SDK_2020.Release.58_PC64_ansi_static",
            "Content-Type": "application/json; charset=UTF-8",
            "Ubi-AppId": self.appid,
            "Authorization": "Basic " + self.token
        }

        if _new:
            headers["Ubi-AppId"] = self.appid
            headers["Authorization"] = "Ubi_v1 t=" + self.key

        resp = await session.post(
            url="https://public-ubiservices.ubi.com/v3/profiles/sessions",
            headers=headers,
            data=json.dumps({"rememberMe": True})
        )

        data = await resp.json()

        if "ticket" in data:
            if _new:
                self.new_key = data.get('ticket')
                self.new_expiration = data.get('expiration')
            else:
                self.key = data.get("ticket")
                self.expiration = data.get("expiration")
            self.profileid = data.get('profileId')
            self.sessionid = data.get("sessionId")
            self.spaceid = data.get("spaceId")
            self.userid = data.get("userId")
        else:
            message = "Unknown Error"
            if "message" in data and "httpCode" in data:
                message = f"HTTP {data['httpCode']}: {data['message']}"
            elif "message" in data:
                message = data["message"]
            elif "httpCode" in data:
                message = str(data["httpCode"])
            raise FailedToConnect(message)

        self.save_creds()
        await self.connect(_new=True)

    async def close(self) -> None:
        """ Closes the session associated with the auth object """
        self.save_creds()
        await self.session.close()

    async def get(self, *args, retries: int = 0, json_: bool = True, new: bool = False, **kwargs) -> dict | str:
        if (not self.key and not new) or (not self.new_key and new):
            last_error = None
            for _ in range(self.max_connect_retries):
                try:
                    await self.connect()
                    break
                except FailedToConnect as e:
                    last_error = e
            else:
                # assume this error is going uncaught, so we close the session
                await self.close()

                if last_error:
                    raise last_error
                else:
                    raise FailedToConnect("Unknown Error")

        if "headers" not in kwargs:
            kwargs["headers"] = {}

        authorization = kwargs["headers"].get("Authorization") or "Ubi_v1 t=" + (self.new_key if new else self.key)
        appid = kwargs["headers"].get("Ubi-AppId") or self.appid

        kwargs["headers"]["Authorization"] = authorization
        kwargs["headers"]["Ubi-AppId"] = appid
        kwargs["headers"]["Ubi-LocaleCode"] = kwargs["headers"].get("Ubi-LocaleCode") or "en-US"
        kwargs["headers"]["Ubi-SessionId"] = kwargs["headers"].get("Ubi-SessionId") or self.sessionid
        kwargs["headers"]["User-Agent"] = kwargs["headers"].get("User-Agent") or "UbiServices_SDK_2020.Release.58_PC64_ansi_static"
        kwargs["headers"]["Connection"] = kwargs["headers"].get("Connection") or "keep-alive"
        kwargs["headers"]["expiration"] = kwargs["headers"].get("expiration") or self.expiration

        session = await self.get_session()
        resp = await session.get(*args, **kwargs)

        if json_:
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                message = text.split("h1>")
                message = message[1][:-2] if len(message) > 1 else text
                raise InvalidRequest(f"Received a text response, expected JSON response. Message: {message}")

            if "httpCode" in data:
                if data["httpCode"] == 401:
                    if retries >= self.max_connect_retries:
                        # wait 30 seconds before sending another request
                        self._login_cooldown = time.time() + 30

                    # key no longer works, so remove key and let the following .get() call refresh it
                    self.key = None
                    return await self.get(*args, retries=retries + 1, **kwargs)
                else:
                    msg = data.get("message", "")
                    if data["httpCode"] == 404:
                        msg = f"Missing resource {data.get('resource', args[0])}"
                    raise InvalidRequest(f"HTTP {data['httpCode']}: {msg}", code=data["httpCode"])

            return data
        else:
            return await resp.text()
    async def get_db(self, *args, retries: int = 0, json_: bool = True, new: bool = False, **kwargs) -> dict | str:
        if (not self.key and not new) or (not self.new_key and new):
            last_error = None
            for _ in range(self.max_connect_retries):
                try:
                    await self.connect()
                    break
                except FailedToConnect as e:
                    last_error = e
            else:
                # assume this error is going uncaught, so we close the session
                await self.close()

                if last_error:
                    raise last_error
                else:
                    raise FailedToConnect("Unknown Error")

        if "headers" not in kwargs:
            kwargs["headers"] = {}

        authorization = kwargs["headers"].get("Authorization") or "Ubi_v1 t=" + (self.new_key if new else self.key)
        appid = kwargs["headers"].get("Ubi-AppId") or self.appid


        kwargs["headers"]["content-type"] = "application/json"
        kwargs["headers"]["Authorization"] = authorization
        kwargs["headers"]["Ubi-AppId"] = appid
        kwargs["headers"]["Ubi-LocaleCode"] = kwargs["headers"].get("Ubi-LocaleCode") or "en-US"
        kwargs["headers"]["Ubi-SessionId"] = kwargs["headers"].get("Ubi-SessionId") or self.sessionid
        kwargs["headers"]["User-Agent"] = kwargs["headers"].get("User-Agent") or "UbiServices_SDK_2020.Release.58_PC64_ansi_static"
        kwargs["headers"]["Connection"] = kwargs["headers"].get("Connection") or "keep-alive"
        kwargs["headers"]["expiration"] = kwargs["headers"].get("expiration") or self.expiration

        query = {
            "operationName":"GetItemDetails",
            "variables": {
                "spaceId":"0d2ae42d-4c27-4cb7-af6c-2099062302bb",
                "itemId": self.item_id,
                "tradeId":"",
                "fetchTrade":False
            },
            "query":"query GetItemDetails($spaceId: String!, $itemId: String!, $tradeId: String!, $fetchTrade: Boolean!) {\n  game(spaceId: $spaceId) {\n    id\n    marketableItem(itemId: $itemId) {\n      id\n      item {\n        ...SecondaryStoreItemFragment\n        ...SecondaryStoreItemOwnershipFragment\n        __typename\n      }\n      marketData {\n        ...MarketDataFragment\n        __typename\n      }\n      paymentLimitations {\n        id\n        paymentItemId\n        minPrice\n        maxPrice\n        __typename\n      }\n      __typename\n    }\n    viewer {\n      meta {\n        id\n        trades(filterBy: {states: [Created], itemIds: [$itemId]}) {\n          nodes {\n            ...TradeFragment\n            __typename\n          }\n          __typename\n        }\n        trade(tradeId: $tradeId) @include(if: $fetchTrade) {\n          ...TradeFragment\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment SecondaryStoreItemFragment on SecondaryStoreItem {\n  id\n  assetUrl\n  itemId\n  name\n  tags\n  type\n  viewer {\n    meta {\n      id\n      isReserved\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SecondaryStoreItemOwnershipFragment on SecondaryStoreItem {\n  viewer {\n    meta {\n      id\n      isOwned\n      quantity\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MarketDataFragment on MarketableItemMarketData {\n  id\n  sellStats {\n    id\n    paymentItemId\n    lowestPrice\n    highestPrice\n    activeCount\n    __typename\n  }\n  buyStats {\n    id\n    paymentItemId\n    lowestPrice\n    highestPrice\n    activeCount\n    __typename\n  }\n  lastSoldAt {\n    id\n    paymentItemId\n    price\n    performedAt\n    __typename\n  }\n  __typename\n}\n\nfragment TradeFragment on Trade {\n  id\n  tradeId\n  state\n  category\n  createdAt\n  expiresAt\n  lastModifiedAt\n  failures\n  tradeItems {\n    id\n    item {\n      ...SecondaryStoreItemFragment\n      ...SecondaryStoreItemOwnershipFragment\n      __typename\n    }\n    __typename\n  }\n  payment {\n    id\n    item {\n      ...SecondaryStoreItemQuantityFragment\n      __typename\n    }\n    price\n    transactionFee\n    __typename\n  }\n  paymentOptions {\n    id\n    item {\n      ...SecondaryStoreItemQuantityFragment\n      __typename\n    }\n    price\n    transactionFee\n    __typename\n  }\n  paymentProposal {\n    id\n    item {\n      ...SecondaryStoreItemQuantityFragment\n      __typename\n    }\n    price\n    __typename\n  }\n  viewer {\n    meta {\n      id\n      tradesLimitations {\n        ...TradesLimitationsFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SecondaryStoreItemQuantityFragment on SecondaryStoreItem {\n  viewer {\n    meta {\n      id\n      quantity\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TradesLimitationsFragment on UserGameTradesLimitations {\n  id\n  buy {\n    resolvedTransactionCount\n    resolvedTransactionPeriodInMinutes\n    activeTransactionCount\n    __typename\n  }\n  sell {\n    resolvedTransactionCount\n    resolvedTransactionPeriodInMinutes\n    activeTransactionCount\n    resaleLocks {\n      itemId\n      expiresAt\n      __typename\n    }\n    __typename\n  }\n  __typename\n}"
        }
        kwargs["data"] = json.dumps(query)

        session = await self.get_session()
        resp = await session.post(*args, **kwargs)

        if json_:
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                message = text.split("h1>")
                message = message[1][:-2] if len(message) > 1 else text
                raise InvalidRequest(f"Received a text response, expected JSON response. Message: {message}")

            if "httpCode" in data:
                if data["httpCode"] == 401:
                    if retries >= self.max_connect_retries:
                        # wait 30 seconds before sending another request
                        self._login_cooldown = time.time() + 30

                    # key no longer works, so remove key and let the following .get() call refresh it
                    self.key = None
                    return await self.get(*args, retries=retries + 1, **kwargs)
                else:
                    msg = data.get("message", "")
                    if data["httpCode"] == 404:
                        msg = f"Missing resource {data.get('resource', args[0])}"
                    raise InvalidRequest(f"HTTP {data['httpCode']}: {msg}", code=data["httpCode"])

            return data
        else:
            return await resp.text()
    
    async def try_query_db(self):
        await asyncio.sleep(0.08)

        res = await self.get_db(f"https://public-ubiservices.ubi.com/v1/profiles/me/uplay/graphql")

        failed = False
        try:
            res["errors"]
            failed = True
            print("Rate Limited!")
        except:
            pass
        if (failed):
            return -1
        
        name = None
        tags = None
        item_type = None

        lowest_buyer = None
        highest_buyer = None
        volume_buyers = None

        lowest_seller = None
        highest_seller = None
        volume_sellers = None

        last_sold = None
        
        asset_url = None
        try:
            name = res["data"]["game"]["marketableItem"]["item"]["name"]
        except:
            print(f'ERR')    
        try:
            tags = res["data"]["game"]["marketableItem"]["item"]["tags"]
        except:
            print(f'ERR')    
        try:
            item_type = res["data"]["game"]["marketableItem"]["item"]["type"]
        except:
            print(f'ERR')    

        try:
            lowest_buyer = res["data"]["game"]["marketableItem"]["marketData"]["buyStats"][0]["lowestPrice"]
        except:
            print(f'ERR')    
        try:
            highest_buyer = res["data"]["game"]["marketableItem"]["marketData"]["buyStats"][0]["highestPrice"]
        except:
            print(f'ERR')   
        try: 
            volume_buyers = res["data"]["game"]["marketableItem"]["marketData"]["buyStats"][0]["activeCount"]
        except:
            print(f'ERR')    

        try:
            lowest_seller = res["data"]["game"]["marketableItem"]["marketData"]["sellStats"][0]["lowestPrice"]
        except:
            print(f'ERR')    
        try:
            highest_seller = res["data"]["game"]["marketableItem"]["marketData"]["sellStats"][0]["highestPrice"]
        except:
            print(f'ERR')    
        try:
            volume_sellers = res["data"]["game"]["marketableItem"]["marketData"]["sellStats"][0]["activeCount"]
        except:
            print(f'ERR')    
        
        try:
            last_sold = res["data"]["game"]["marketableItem"]["marketData"]["lastSoldAt"][0]["price"]
        except:
            print(f'ERR')    

        try:
            asset_url = res["data"]["game"]["marketableItem"]["item"]["assetUrl"]
        except:
            print(f'ERR')    
        
        return [
            name,
            item_type,
            tags,

            lowest_buyer,
            highest_buyer,
            volume_buyers,

            lowest_seller,
            highest_seller,
            volume_sellers,

            last_sold,

            asset_url
        ]

account_platform_blocklist = [
    'Coders Rank', 'Fiverr', 'HackerNews', 'Modelhub (NSFW)', 'metacritic', 'xHamster (NSFW)',
    'CNET'
]
async def get_all_accounts(name, sites):
	print(f"Starting check for accounts on {name}...")

	name = name.replace(" ", "%20")
	
	async with websockets.connect(f"wss://namefind.fly.dev/api/v1/handles/{name}") as websocket:
		data = await websocket.recv()
		while data != "null":
			parsed_data = json.loads(data)

			if not parsed_data['site'] in account_platform_blocklist:
				print(f"\n**{parsed_data['site']}**: {parsed_data['url']}")

				sites.append(f"\n**{parsed_data['site']}**: {parsed_data['url']}")
			
			data = await websocket.recv()
		await websocket.close()
		
	print(f"Closing check for accounts on {name}...")

intents = discord.Intents.default()
intents.message_content = True

if ( not exists("assets/data.json") ):
    with open('assets/data.json', 'w') as f:
        f.write("{}")

if ( not exists("assets/ids.json") ):
    with open('assets/ids.json', 'w') as f:
        f.write('{"black ice r4-c": "aee4bdf2-0b54-4c6d-af93-9fe4848e1f76"}')

data_file = open("assets/data.json", "r")
data = json.loads(data_file.read())
data_file.close()

item_id_file = open("assets/ids.json", "r")
item_ids = json.loads(item_id_file.read())
item_id_file.close()

client = commands.Bot(command_prefix='.', intents=intents)

@client.event
async def on_ready():
    print("Connected!")
    print(time.time())

    save_agent.start()
    scan_market.start()

@client.event
async def on_message(message):
    if message.author != client.user:
        cmd = message.content.split(" ")

        name_map_file = open("assets/ids.json", "r")
        name_map = json.loads(name_map_file.read())
        name_map_file.close()

        match cmd.pop(0):
            case "econ":
                match cmd.pop(0):
                    case "dox":
                        auth = Auth(os.environ["AUTH_EMAIL"], os.environ["AUTH_PW"])

                        debug = False

                        profile = {
                            "profile_id": " ".join(cmd).lower(),
                            "linked": []
                        }

                        if debug:
                            print(json.dumps(data, indent=3))
                            print("Profile ID: " + profile['profile_id'])
                        
                        if len(profile['profile_id']) < 20:
                            profile_from_name = await auth.get(f"https://public-ubiservices.ubi.com/v3/profiles?nameOnPlatform={profile['profile_id']}&platformType=uplay")
                            profile['profile_id'] = profile_from_name['profiles'][0]['idOnPlatform']

                        player = await auth.get(f"https://public-ubiservices.ubi.com/v1/profiles/{profile['profile_id']}")
                        persona = await auth.get(f"https://public-ubiservices.ubi.com/v1/profiles/persona?profileIds={profile['profile_id']}&spaceId=0d2ae42d-4c27-4cb7-af6c-2099062302bb")
                        stats = await auth.get(f"https://public-ubiservices.ubi.com/v2/spaces/0d2ae42d-4c27-4cb7-af6c-2099062302bb/title/r6s/skill/full_profiles?profile_ids={profile['profile_id']}&platform_families=pc")
                        profiles = await auth.get(f"https://public-ubiservices.ubi.com/v3/users/{profile['profile_id']}/profiles")
            
                        if debug:
                            print("Player:")
                            print(json.dumps(player, indent=3))
                            print("Persona:")
                            print(json.dumps(persona, indent=3))
                            print("Stats:")
                            print(json.dumps(stats, indent=3))
                            print("Profiles:")
                            print(json.dumps(profiles, indent=3))

                        for platform in profiles["profiles"]:
                            match platform['platformType']:
                                case "uplay":
                                    profile['linked'].append(f"**Uplay**:\n\tLink: https://r6.tracker.network/r6/search?name={profile['profile_id']}&platform=4")
                                case "steam":
                                    profile['linked'].append(f"**Steam**:\n\tLink: https://findsteamid.com/steamid/{platform['idOnPlatform']}")
                                case "xbl":
                                    profile['linked'].append(f"**XBL**:\n\tLink: https://xboxgamertag.com/search/{platform['nameOnPlatform']}")
                                case "twitch":
                                    profile['linked'].append(f"**Twitch**:\n\tLink: https://www.twitch.tv/{platform['nameOnPlatform']}")
                                case _:
                                    # OCD
                                    upper_first = list(platform['platformType'])
                                    upper_first[0] = upper_first[0].upper()
                                    upper_first = ''.join(upper_first)

                                    profile['linked'].append(f"**{upper_first}**:\n\tName: **{platform['nameOnPlatform']}**\n\tID: **{platform['idOnPlatform']}**")
                        
                        profile['uplay'] = player['nameOnPlatform']
                        profile['nickname'] = persona['personas'][0]['nickname'] if (persona['personas'] and persona['personas'][0]['obj']['Enabled']) else "Offline/No Nickname"
                        
                        ranked_board = next((item for item in stats['platform_families_full_profiles'][0]['board_ids_full_profiles'] if item['board_id'] == "ranked"), None)['full_profiles'][0]
                        profile['peak_mmr'] = ranked_board['profile']['max_rank_points']
                        profile['mmr'] = ranked_board['profile']['rank_points']
                        profile['kills'] = ranked_board['season_statistics']['kills']
                        profile['deaths'] = ranked_board['season_statistics']['deaths']
                        profile['wins'] = ranked_board['season_statistics']['match_outcomes']['wins']
                        profile['losses'] = ranked_board['season_statistics']['match_outcomes']['losses']
                        profile['kd'] = round((profile['kills'] + 1) / (profile['deaths'] + 1), 2)
                        profile['wl'] = round((profile['wins'] + 1) / (profile['losses'] + 1 + profile['wins'] + 1) * 100, 2)

                        if debug:
                            print(json.dumps(ranked_board, indent=3))

                        print(f"Blocked {profile['uplay']} ({profile['nickname']})\n")
                        print(f"Rank: {profile['mmr']} ({profile['peak_mmr']})")
                        print(f"KD: {profile['kd']} ({profile['kills']} kills - {profile['deaths']} deaths)")
                        print(f"WL: {profile['wl']} ({profile['wins']} wins - {profile['losses']} losses)")
                        print(f"R6 Tracker: https://r6.tracker.network/profile/pc/{profile['profile_id']}\n\n\n")

                        await client.wait_until_ready()

                        msg = f"\n## Player:\n\tUplay: **{profile['uplay']}**\n\tNickname: **{profile['nickname']}**"
                        msg += f"\n### Rank:\n\tCurrent: **{profile['mmr']}**\n\tPeak: **{profile['peak_mmr']}**)"
                        msg += f"\n### Stats:\n\tKD: **{profile['kd']}**\n\tKills: **{profile['kills']}**\n\tDeaths: **{profile['deaths']}**\n\n\tWL: **{profile['wl']}**\n\tWins: **{profile['wins']}**\n\tLosses: **{profile['losses']}**"
                    
                        profiles_str = '\n'.join(profile['linked'])
                        msg += f"\n### Linked Accounts:\n{profiles_str}"

                        embed=discord.Embed(title=f'Blocked Player (@wydbolt)', description=f'{msg}', color=0xFF5733)
                        embed.set_thumbnail(url=f"https://ubisoft-avatars.akamaized.net/{profile['profile_id']}/default_tall.png")
                        
                        await message.channel.send(embed=embed)

                        print(json.dumps(profiles['profiles'],indent=2))

                        blacklist_platforms = ['epic', 'steam', 'amazon']
                        usernames = list(set([x['nameOnPlatform'] for x in profiles['profiles'] if x['nameOnPlatform'] and not x['platformType'] in blacklist_platforms]))

                        if len(usernames) == 0:
                            return
                        
                        joined_usernames = '\n'.join(usernames)
                        embed=discord.Embed(title=f'Please wait while potential accounts are fetched!', description=f"This could take some time.\n\n## Usernames:\n{joined_usernames}", color=0xFF5733)
                        embed.set_thumbnail(url=f"https://ubisoft-avatars.akamaized.net/{profile['profile_id']}/default_tall.png")
                        
                        await message.channel.send(embed=embed)

                        links = []

                        for username in usernames:
                            links.append(f"\n\n## {username}")

                            await get_all_accounts(username, links)

                        links = ''.join(links)

                        embed=discord.Embed(title=f'Potential Linked Accounts', description=links, color=0xFF5733)
                        embed.set_thumbnail(url=f"https://ubisoft-avatars.akamaized.net/{profile['profile_id']}/default_tall.png")
                        
                        await message.channel.send(embed=embed)

                        await auth.close()
                    case "list":
                        msg = ""
                        item_no = 0
                        for key, value in name_map.items():
                            msg += f'{key}\n'
                            item_no += 1
                            if ( item_no > 99 ):
                                break
                        embed=discord.Embed(title=f'Tracked Skins', description=f'# Ask Bolt for new Items.\n\n# Skins:\n{msg}', color=0xFF5733)
                        embed.set_thumbnail(url="https://github.com/hiibolt/hiibolt/assets/91273156/4a7c1e36-bf24-4f5a-a501-4dc9c92514c4")
                        await message.channel.send(embed=embed)
                        return
                    case "id":
                        item_id = " ".join(cmd).lower()
                        _data = None
                        try:
                            _data = data[item_id]
                        except:
                            msg = "We aren't tracking this item ID!"
                            embed=discord.Embed(title=f'Help', description=f'# Ask @hiibolt on GH/DC for help!\n\n## {msg}', color=0xFF5733)
                            embed.set_thumbnail(url="https://github.com/hiibolt/hiibolt/assets/91273156/4a7c1e36-bf24-4f5a-a501-4dc9c92514c4")
                            await message.channel.send(embed=embed)
                        if ( _data == None):
                            return

                        cleaned_data = [x[0] for x in _data["sold"] if x[0]]
                        sold_len = len(cleaned_data)
                        ten_RAP = round(sum(cleaned_data[-10:]) / max(1, min(10, sold_len)))
                        hundred_RAP = round(sum(cleaned_data[-100:]) / max(1, min(100, sold_len)))
                        all_time_RAP = round(sum(cleaned_data) / max(1, sold_len))

                        msg = f'# Buy:\n\tMinimum Buyer: **{_data["data"][0]}** R6 credits\n\tMaximum Buyer: **{_data["data"][1]}** R6 credits\n\tVolume Buyers: **{_data["data"][2]}**\n'
                        msg += f'# Sell:\n\tMinimum Seller: **{_data["data"][3]}** R6 credits\n\tMaximum Seller: **{_data["data"][4]}** R6 credits\n\tVolume Sellers: **{_data["data"][5]}**\n\tLast Sold: **{_data["sold"][-1][0]}**\n\n'
                        msg += f'### Quick Analysis:\n\tHighest Buyer vs. Lowest Seller: **{(_data["data"][3] or 0) - (_data["data"][1] or 0)}** R6 credits\n\tLast Sale vs. Lowest Seller: **{(_data["data"][3] or 0) - (_data["sold"][-1][0] or 0)} ({round(100 -((_data["sold"][-1][0] or 0) / (_data["data"][3] or 1)) * 100, 2)}%)** R6 credits\n'
                        msg += f'### RAP:\n\t10 - **{ten_RAP}**\n\t100 - **{hundred_RAP}**\n\tAll Time - **{all_time_RAP}**\n\n\t*(Total Data: {sold_len})*\n### Tags:\n\n{_data["tags"]}\n### Item ID:\n\t{item_id}'
                        embed=discord.Embed(title=f'{_data["name"]} ({_data["type"]})', url=f'https://www.ubisoft.com/en-us/game/rainbow-six/siege/marketplace?route=buy%252Fitem-details&itemId={item_id}', description=f'{msg}', color=0xFF5733)
                        embed.set_thumbnail(url=_data["asset_url"])
                        await message.channel.send(embed=embed)
                    case "name":
                        _data = None
                        try:
                            item_id = name_map[" ".join(cmd).lower()]
                            _data = data[item_id]
                        except:
                            msg = "We aren't tracking this item name, try a different name or run 'econ list'!"
                            embed=discord.Embed(title=f'Help', description=f'# Ask @hiibolt on GH/DC for help!\n\n## {msg}', color=0xFF5733)
                            embed.set_thumbnail(url="https://github.com/hiibolt/hiibolt/assets/91273156/4a7c1e36-bf24-4f5a-a501-4dc9c92514c4")
                            await message.channel.send(embed=embed)
                        if ( _data == None):
                            return

                        cleaned_data = [x[0] for x in _data["sold"] if x[0]]
                        sold_len = len(cleaned_data)
                        ten_RAP = round(sum(cleaned_data[-10:]) / max(1, min(10, sold_len)))
                        hundred_RAP = round(sum(cleaned_data[-100:]) / max(1, min(100, sold_len)))
                        all_time_RAP = round(sum(cleaned_data) / max(1, sold_len))

                        msg = f'# Buy:\n\tMinimum Buyer: **{_data["data"][0]}** R6 credits\n\tMaximum Buyer: **{_data["data"][1]}** R6 credits\n\tVolume Buyers: **{_data["data"][2]}**\n'
                        msg += f'# Sell:\n\tMinimum Seller: **{_data["data"][3]}** R6 credits\n\tMaximum Seller: **{_data["data"][4]}** R6 credits\n\tVolume Sellers: **{_data["data"][5]}**\n\tLast Sold: **{_data["sold"][-1][0]}**\n\n'
                        msg += f'### Quick Analysis:\n\tHighest Buyer vs. Lowest Seller: **{(_data["data"][3] or 0) - (_data["data"][1] or 0)}** R6 credits\n\tLast Sale vs. Lowest Seller: **{(_data["data"][3] or 0) - (_data["sold"][-1][0] or 0)} ({round(100 -((_data["sold"][-1][0] or 0) / (_data["data"][3] or 1)) * 100, 2)}%)** R6 credits\n'
                        msg += f'### RAP:\n\t10 - **{ten_RAP}**\n\t100 - **{hundred_RAP}**\n\tAll Time - **{all_time_RAP}**\n\n\t*(Total Data: {sold_len})*\n### Tags:\n\n{_data["tags"]}\n### Item ID:\n\t{item_id}'
                        embed=discord.Embed(title=f'{_data["name"]} ({_data["type"]})', url=f'https://www.ubisoft.com/en-us/game/rainbow-six/siege/marketplace?route=buy%252Fitem-details&itemId={item_id}', description=f'{msg}', color=0xFF5733)
                        embed.set_thumbnail(url=_data["asset_url"])
                        await message.channel.send(embed=embed)
                    case "graph":
                        num = cmd.pop(0)
                        unit_type = cmd.pop(0)

                        item_id = " ".join(cmd).lower()
                        _data = copy.deepcopy(data[item_id])
                        unit = "days"
                        dividend = 86400
                        
                        match num:
                            case "all":
                                pass
                            case _:
                                _data["sold"] = [x for x in _data["sold"] if x[0]]
                                _data["sold"] = _data["sold"][-int(num):]
                                
                        match unit_type:
                            case "days":
                                pass
                            case "hours":
                                unit = "hours"
                                dividend = 86400 / 24
                            case "minutes":
                                unit = "minutes"
                                dividend = 86400 / 24 / 60
                            case _:
                                msg = "The following units are available:\n\t- days\n\t- hours\n\t- minutes"
                                embed=discord.Embed(title=f'Help', description=f'# Ask @hiibolt on GH/DC for help!\n\n# Skins:\n{msg}', color=0xFF5733)
                                embed.set_thumbnail(url="https://github.com/hiibolt/hiibolt/assets/91273156/4a7c1e36-bf24-4f5a-a501-4dc9c92514c4")
                                await message.channel.send(embed=embed)

                        cleaned_data = [x[0] for x in _data["sold"] if x[0]]
                        cleaned_times = [(time.time() - x[1]) / dividend for x in _data["sold"] if x[0]]
                     
                        print(f'{cleaned_times} vs {cleaned_data}')

                        plt.scatter( np.array(cleaned_times), np.array(cleaned_data) )
                        plt.xlabel( f' Time ({unit} ago) ' )
                        plt.ylabel( " Purchase Amount " )

                        trendline = np.polyfit( np.array(cleaned_times), np.array(cleaned_data), 1 )
                        trendline_function = np.poly1d( trendline )
                        plt.plot( cleaned_times, trendline_function(cleaned_times) )
                        plt.title( f'{_data["name"]} ({_data["type"]})' )
                        plt.savefig( f"graphs/{item_id}.png" )
                        plt.clf()

                        file = discord.File(f'graphs/{item_id}.png')
                        e = discord.Embed()
                        e.set_image(url=f'attachment://{item_id}.png')
                        await message.channel.send(file = file, embed=e)
                    case "profit":
                        purchase_price = float(cmd.pop(0))
                        profitable_sell = purchase_price * 1.1

                        item_id = " ".join(cmd).lower()
                        _data = None
                        try:
                            _data = data[item_id]
                        except:
                            msg = "We aren't tracking this item ID!"
                            embed=discord.Embed(title=f'Help', description=f'# Ask @hiibolt on GH/DC for help!\n\n## {msg}', color=0xFF5733)
                            embed.set_thumbnail(url="https://github.com/hiibolt/hiibolt/assets/91273156/4a7c1e36-bf24-4f5a-a501-4dc9c92514c4")
                            await message.channel.send(embed=embed)
                        if ( _data == None):
                            return
                        
                        cleaned_data = [x[0] for x in _data["sold"] if x[0]]
                        sold_len = len(cleaned_data)
                        ten_RAP = round(sum(cleaned_data[-10:]) / max(1, min(10, sold_len)))

                        msg = f'\n### Purchased At:\n\t**{purchase_price}** R6 credits\n### Sale Price to Break Even:\n\t**{profitable_sell}** R6 credits\n### Current Net Gain if Sold:\n\t**{((ten_RAP or 0) - purchase_price) * 0.90}** R6 credits'
                        embed=discord.Embed(title=f'Profit Margins', description=f'{msg}', color=0xFF5733)
                        embed.set_thumbnail(url="https://github.com/hiibolt/hiibolt/assets/91273156/4a7c1e36-bf24-4f5a-a501-4dc9c92514c4")
                        await message.channel.send(embed=embed)
                    case _:
                        msg = "The following commands are available:\n\n\t- econ name <item name>\n\n\t- econ id <item id>\n\n\t- econ graph <# entries (1, 2, ... | all)> <unit (days | hours | minutes)>\n\n\t- econ profit <what you purchased for> <item id>"
                        embed=discord.Embed(title=f'Help', description=f'# Ask @hiibolt on GH/DC for help!\n\n# Skins:\n{msg}', color=0xFF5733)
                        embed.set_thumbnail(url="https://github.com/hiibolt/hiibolt/assets/91273156/4a7c1e36-bf24-4f5a-a501-4dc9c92514c4")
                        await message.channel.send(embed=embed)

@tasks.loop(minutes=10)
async def save_agent():
    with contextlib.suppress(Exception):
        print("[ WRITING TO 'data.json' ]")

        data_file = open("assets/data.json", "w")
        data_file.write(json.dumps(data, indent=2))
        data_file.close()

        print("[ FINISHED WRITING TO 'data.json' ]")

@tasks.loop(minutes=5)
async def scan_market():
    with contextlib.suppress(Exception):
        auth = Auth(os.environ["AUTH_EMAIL"], os.environ["AUTH_PW"])
        print("[ Authenticated ]")

        for key, item_id in item_ids.items():
            auth.item_id = item_id
            res = await auth.try_query_db()
            if (not res):
                print("Rate Limited!")
                continue

            # Meta: NAME | TYPE | TAGS - Buyers: LOW | HIGH | VOL - Sellers: LOW | HIGH | VOL
            try:
                data[item_id]
            except:
                data[item_id] = {
                    "name": res[0],
                    "type": res[1],
                    "tags": res[2],
                    "asset_url": res[10],
                    "sold": [],
                    "data": None
                }
            if data[item_id]["data"] == None or data[item_id]["data"] != [res[3], res[4], res[5], res[6], res[7], res[8]]:
                data[item_id]["data"] = [res[3], res[4], res[5], res[6], res[7], res[8]]
                print("NEW PRIMARY DATA")
            
            if len(data[item_id]["sold"]) == 0 or data[item_id]["sold"][len(data[item_id]["sold"]) - 1][0] != res[9]:
                data[item_id]["sold"] = data[item_id]["sold"] + [[res[9], time.time()]]
                print("NEW LAST SOLD")
            
        await auth.close()
        print("[ Closing Session ]")
                            

client.run(os.environ["TOKEN"])
