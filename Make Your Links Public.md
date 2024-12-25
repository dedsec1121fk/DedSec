First ensure you have cloudflared installed:
pkg install cloudflared

Then after you run a program from the memu or the Scripts directory anyway s,copy the address similar to http://10.000.000.000:4040,then swipe from left to right on Termux and left down tap NEW SESSION,tap 0 if you're using my menu,then write: cloudflared tunnel --url http://10.000.000.000:4040 (the url you just copied paste it after the --url thing) and now afte a few seconds if you scroll up you will see something similar to this:

2024-12-25T08:37:24Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
2024-12-25T08:37:24Z INF |  https://economic-nursing-namespace-wi.trycloudflare.com

As you can see it generated a random url that you can now use anywhere in the world.
To close them close the Termux sessions.
