# Self-Hosted AI GTM Lab — Notes

## Day 1 — Docker, n8n, Webhooks (6 Jul 2026)

### What is Docker?
Docker is a tool that runs applications inside isolated boxes called
containers. Instead of installing an app and all its dependencies by hand,
I pull one pre-packaged image and run it. It let me self-host n8n without
manually installing Node.js, databases or config.

### Container vs image
An image is the blueprint or recipe — static and reusable (n8nio/n8n is an
image). A container is a running instance made from that image — the recipe
cooked into a live dish. One image can produce many containers.

### What is a volume?
A volume is persistent storage that lives outside the container, on my
machine, managed by Docker. It survives when the container is stopped,
removed or rebuilt. I proved this when my Lead Intake workflow was still
there after a reboot — the container was gone but the n8n_data volume kept
my work.

### What is a port?
A port is a numbered door on a machine for network traffic. n8n listens on
port 5678. The flag -p 5678:5678 maps my laptop's door 5678 to the
container's door 5678, which is why localhost:5678 reaches n8n.

### What is localhost?
Localhost is my own computer's network address (also written 127.0.0.1).
localhost:5678 means "knock on door 5678 of this machine".

### What is a webhook?
A webhook is a URL that waits for incoming data. When another system POSTs
JSON to it, the workflow fires automatically. It's push, not pull — I don't
poll for data, the data comes to me.

### What is JSON?
JSON is the text format data travels in: key-value pairs inside curly braces
(e.g. "industry": "Beauty"). Objects sit inside { }, lists inside [ ]. A
Python dictionary is the same shape, which matters for next week.

### What is a status code? (200 OK)
A status code is a 3-digit number in an HTTP response saying what happened.
200 OK means the server received my request, processed it successfully, and
sent back a valid response. My Glow Beauty payload returning 200 proved the
full round trip worked — data in, response out.

### Why this matters for GTM Engineering
A webhook is the entry point for enriched account data from tools like Clay.
From there the data can be validated, scored, routed and pushed into a CRM
like HubSpot with no manual work. Self-hosting it in Docker shows I can run
the infrastructure, not just use no-code tools.

### What I built today
Self-hosted n8n in Docker. A Lead Intake workflow with a Webhook node
(POST /lead-intake) and a Respond to Webhook node. Tested it with a Glow
Beauty payload — got 200 OK back and saw the data land in the node output.