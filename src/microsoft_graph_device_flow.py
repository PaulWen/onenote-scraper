import json
import logging
import os

import msal
import sys  # For simplicity, we'll read config file from 1st CLI param sys.argv[1]

logging.getLogger("msal").setLevel(logging.INFO)
config = json.load(open(sys.argv[1]))

# SerializableTokenCache: https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
tokenCache = msal.SerializableTokenCache()
if os.path.exists("token_cache.bin"):
    tokenCache.deserialize(open("token_cache.bin", "r").read())

app = msal.PublicClientApplication(
    config["client_id"], authority=config["authority"],
    token_cache=tokenCache
)

def retrieveAccessToken():
    result = None
    accounts = app.get_accounts()
    if accounts:
        account = accounts[0]
        result = app.acquire_token_silent(config["scope"], account=account)

    if not result:
        logging.info("No suitable token exists in cache. Let's get a new one from AAD.")

        flow = app.initiate_device_flow(scopes=config["scope"])
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

        print(flow["message"])
        sys.stdout.flush()  # Some terminal needs this to ensure the message is shown

        result = app.acquire_token_by_device_flow(flow)  # By default it will block
        # You can follow this instruction to shorten the block time
        #    https://msal-python.readthedocs.io/en/latest/#msal.PublicClientApplication.acquire_token_by_device_flow
        # or you may even turn off the blocking behavior,
        # and then keep calling acquire_token_by_device_flow(flow) in your own customized loop.

    if "access_token" in result:
        open("token_cache.bin", "w").write(tokenCache.serialize())
        return result['access_token']
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You may need this when reporting a bug
        return None
