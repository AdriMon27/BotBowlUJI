#!/usr/bin/env python3
from uji_bot import *

import botbowl.web.server as server

if __name__ == "__main__":
    #server.start_server(debug=True, use_reloader=False, port=1234)
    server.start_server(port=5005)
