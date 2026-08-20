# Network Performance Testing Tool

A client/server tool (`net-tester.py`) for measuring bandwidth, jitter and
packet loss over TCP and UDP, plus a Mininet topology (`topology.py`) with
three routers, two switches and five hosts for testing it under controlled
link conditions.

No extra dependencies beyond the devcontainer. Standard library only:
`socket`, `threading`, `struct`, `argparse`, `csv`.

## Running it

Bring up the topology:

```
mn --custom topology.py --topo courseworkTopo --switch=lxbr --link=tc --controller=none
```

TCP test:

```
python3 net-tester.py -s -p 5001
python3 net-tester.py -c 192.168.3.2 -p 5001 -t 10 -i 1
```

UDP test, server computes the stats:

```
python3 net-tester.py -s -u -p 5001
python3 net-tester.py -u -c 192.168.3.2 -p 5001 -r 1000 -t 10 -i 1
```

UDP with acknowledgements, client computes the stats instead:

```
python3 net-tester.py -s -u -a -p 5001
python3 net-tester.py -u -a -c 192.168.3.2 -p 5001 -r 1000 -t 10 -i 1
```

Add `-l results.csv` on either end to also log measurements to a CSV file.

## What's in it

**Topology** — five hosts, three routers, two switches, static routes
between every subnet. Router1-router2 runs at 10ms delay / 1% loss with no
bandwidth cap; router1-router3 runs at 100Mbit / 100ms delay. Both set
through the Mininet link API, no external scripts.

**TCP** — the client calls `sendall()` in a loop for the test duration and
lets TCP's congestion control set the pace, reporting the achieved rate
every interval. The server threads each connection, so it handles multiple
clients at once.

**UDP** — the client paces 1472-byte datagrams (4-byte big-endian sequence
number + payload) to a target rate, sending sequence 0 to mark the end of
the stream. The server tracks stats per `(ip, port)` and reports bandwidth,
jitter and loss at each interval.

**UDP with ACKs** — the server echoes each sequence number back as a
4-byte ACK. The client times the round trip, computes its own bandwidth,
jitter and loss from the ACKs, treats a missing ACK as a loss, and ignores
duplicate ACK IDs.

## Takeaways

- Jitter turned out easier than expected once arrival times were stored
  against sequence IDs instead of a flat list, comparing consecutive IDs
  rather than consecutive arrivals is what the spec actually needed.
- Multi-client state was the harder problem. An early version used global
  counters and broke as soon as a second client connected; keying
  everything by `(ip, port)` fixed it.
- Watching `sendall()` throttle itself against the link, next to a UDP
  client that will happily blast packets into a lossy link regardless,
  made the reliable vs best-effort distinction concrete in a way reading
  about it never did.
- Mininet's 1% loss is a statistical average, not a fixed 1-in-100
  pattern. Short test runs showed anywhere from 0% to 3% loss; longer runs
  converged closer to 1%.

## What I'd do differently

- **CSV header mismatch** — `Logger.log_stat()` writes 7 fields (ip, port,
  timestamp, elapsed, bandwidth, loss, jitter) but the header row only has
  5 columns. Output still works, but the header doesn't match the data.
- **Unsafe KeyboardInterrupt path** — in the ACK client, `loss` and
  `jitter` are only assigned inside the interval block. An early Ctrl+C
  hits a `NameError` instead of a clean summary. Should default both to 0.
- **Duplicated ACK/non-ACK logic** — the UDP client and server each have
  near-identical ACK and non-ACK branches. A shared stats helper would
  halve that code and remove the risk of fixing one copy and not the
  other.
- **Redundant TCP reporting** — the client recalculates a "final interval"
  bandwidth figure on every loop pass instead of once at the end,
  producing an occasional stray extra reading.
- **Misleading interface name** — in `topology.py`, host5's own interface
  is named `router1-eth0`, which has nothing to do with router1.
- **Typo'd variable names** — `byets_acked`, `bamdwidth_mbps`,
  `packrt_id`. Harmless, but worth a cleanup pass.

None of the above affects correctness of the measurements, they're the
rough edges I'd fix before building further on this.
