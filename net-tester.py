# implement an iperf client in Python using sockets

import socket
import time
import threading
import argparse
import sys
from typing import Optional
import csv
from typing import List
import struct

""""
    Usage
    -----
    - Instantiate with an optional CSV file path. Use none to disable, or a path
      like "results.csv" to enable CSV output. By default the class output performance results to "results.csv".
    - Call log_stat() to record individual measurements.
    - Call summary() to print aggregated statistics.
    - Call close() to close any open CSV resource before program exit.

"""

""" mn --custom topology.py --topo courseworkTopo --switch=lxbr --link=tc --controller=none"""
""" python3 net-tester.py -s -p 5001"""  """python3 net-tester.py -c 192.168.3.2 -p 5001 -t 10 -i 1"""
""" python3 net-tester.py -s -u"""  """python3 net-tester.py -c 192.168.3.2 -p 5001 -t 10 -i 1 -u"""
""" python3 net-tester.py -s -u -a"""  """python3 net-tester.py -c 192.168.3.2 -p 5001 -t 10 -i 1 -u -a"""


class Logger:
    """
    Logger
    ------
    Logger class for recording and displaying network test metrics"""

    INFO = '\033[94m[INFO]\033[0m '
    ERROR = '\033[91m[ERROR]\033[0m '

    class Stat:
        """A class to model a single measurement record"""

        def __init__(self, timestamp: float, bandwidth: Optional[float] = None,
                     loss: Optional[float] = None, jitter: Optional[float] = None):
            self.timestamp = timestamp
            self.bandwidth = bandwidth
            self.loss = loss
            self.jitter = jitter

    def __init__(self, csv_output: Optional[str] = "results.csv"):
        """Initialize Logger with optional CSV output"""
        self.stats: List[Logger.Stat] = []  # List to store measurements
        self.csv_output = csv_output        # CSV file path or None
        self.csv_file = None               # File handle for CSV
        self.csv_writer = None             # CSV writer object

        # If the csv parameter is None, then disable CSV output
        if csv_output:
            self.csv_file = open(csv_output, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(
                ['timestamp', 'elapsed', 'bandwidth_mbps', 'loss_percent', 'jitter_ms'])

    def log_stat(self, timestamp: float, ip: str, port: int, bandwidth: Optional[float] = None,
                 loss: Optional[float] = None, jitter: Optional[float] = None) -> None:
        """
        Log a measurement (all parameters optional)
        - timestamp: Time of measurement (float)
        - ip: Client IP address (str)
        - port: Client port number (int)
        - bandwidth: Bandwidth in Mbps (float, optional)
        - loss: Packet loss in percent (float, optional)
        - jitter: Jitter in milliseconds (float, optional)
        """
        stat = Logger.Stat(timestamp, bandwidth, loss, jitter)
        self.stats.append(stat)
        elapsed = 0.0
        if len(self.stats) > 1:
            elapsed = timestamp - self.stats[0].timestamp

        # Write to CSV if enabled
        if self.csv_writer:
            self.csv_writer.writerow([
                ip, port,
                timestamp,
                f"{elapsed:.3f}",
                f"{bandwidth:.2f}" if bandwidth is not None else "",
                f"{loss:.2f}" if loss is not None else "",
                f"{jitter:.2f}" if jitter is not None else ""
            ])
            self.csv_file.flush()

        parts = [f"[{int(elapsed):03d}s] [Client:{ip}:{port}]"]

        if bandwidth is not None:
            parts.append(f"Bandwidth: {bandwidth:.2f} Mbps")
        if loss is not None:
            parts.append(f"Loss: {loss:.2f}%")
        if jitter is not None:
            parts.append(f"Jitter: {jitter:.2f} ms")

        print(" ".join(parts))

    def summary(self) -> None:
        """
        Print summary statistics
        1. Duration of the test
        2. Number of measurements
        3. For each metric (bandwidth, loss, jitter):
           - Average
           - Minimum
           - Maximum
        4. If CSV output was enabled, print the path to the CSV file
        """
        if not self.stats:
            print(f"{Logger.INFO}No statistics recorded")
            return

        print(f"\n{Logger.INFO}=== Test Summary ===")
        print(
            f"  Duration: {int(self.stats[-1].timestamp - self.stats[0].timestamp)}s")
        print(f"  Measurements: {len(self.stats)}")

        # Calculate averages
        bw_values = [
            s.bandwidth for s in self.stats if s.bandwidth is not None]
        loss_values = [s.loss for s in self.stats if s.loss is not None]
        jitter_values = [s.jitter for s in self.stats if s.jitter is not None]

        if bw_values:
            print(f"  Bandwidth: avg={sum(bw_values)/len(bw_values):.2f} Mbps, "
                  f"min={min(bw_values):.2f}, max={max(bw_values):.2f}")
        if loss_values:
            print(f"  Loss: avg={sum(loss_values)/len(loss_values):.2f}%, "
                  f"min={min(loss_values):.2f}, max={max(loss_values):.2f}")
        if jitter_values:
            print(f"  Jitter: avg={sum(jitter_values)/len(jitter_values):.2f} ms, "
                  f"min={min(jitter_values):.2f}, max={max(jitter_values):.2f}")

        if self.csv_output:
            self.log_success(f"Results saved to {self.csv_output}")

    def close(self) -> None:
        """Close CSV file if open"""
        if self.csv_file:
            self.csv_file.close()

    def log_info(self, message: str) -> None:
        """
        Print an info message to stdout
        """
        print(f"{Logger.INFO}{message}")

    def log_error(self, message: str) -> None:
        """
        Print an info message to stdout
        """
        print(f"{Logger.ERROR}{message}")

# Below you can find sample function signatures for the net-tester client and server.
# You can modify them as needed.


# ---------------------- TCP stubs ----------------------

def tester_tcp_client(log: Logger, server_ip: str, server_port: int,
                      duration: int, interval: int) -> None:
    """TCP client (Task 2)
    TODO:
      - Connect and send for 'duration' seconds (chunks of 'window')

      - Every 'interval' seconds, compute and log bandwidth
    """
    log.log_info(f"Starting TCP client to {server_ip}:{server_port} "
                 f"for {duration}s")

    # make tcp socket and conections
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    log.log_info(f"conected to {server_ip}:{server_port}")

    data_packet = b'a' * 2048  # 1Kb of a at a time to send

    # initialise tracking for the data cominucation
    start_time = time.time()
    end_time = start_time + duration
    bytes_sent = 0
    next_report_time = start_time + interval
    bytes_current_interval = 0
    last_report = start_time

    try:
        while True:
            current_time = time.time()
            if current_time >= end_time:
                break

            while current_time < min(next_report_time, end_time):
                try:

                    # sending data
                    # client_socket.sendall(data_packet)
                    client_socket.sendall(data_packet)
                    sent = len(data_packet)
                    bytes_sent += sent
                    bytes_current_interval += sent
                except BrokenPipeError:
                    log.log_error("lost connection")
                    return
                current_time = time.time()

            # check if need to repot
            if current_time >= next_report_time:
                # calculate the bandwidth for the current interval
                interval_duration = (current_time -
                                     (last_report))

            # if its not 0 convert to Mbps
                if interval_duration > 0:
                    bandwidth_Mbps = (
                        (bytes_current_interval * 8) / (interval_duration * 1000000))

                    log.log_stat(current_time,
                                 server_ip,
                                 server_port,
                                 bandwidth=bandwidth_Mbps)

                # reset ready for nrxt interval
                bytes_current_interval = 0
                next_report_time += interval
                last_report = current_time

            # calculate the time and bandwidth
            final_interval = time.time() - last_report
            if final_interval > 0:
                final_interval = time.time() - (next_report_time - interval)
                if final_interval > 0 and bytes_current_interval > 0:
                    final_bandwidth = (
                        (bytes_current_interval * 8) / (final_interval * 1000000))
                    log.log_stat(current_time,
                                 server_ip,
                                 server_port,
                                 bandwidth=final_bandwidth)

    except ConnectionRefusedError:
        log.log_error(f"cant connect to{server_ip}:{server_port}")
    except Exception as e:
        log.log_error(f"error: {e}")

    # close the socket
    finally:
        client_socket.close()
        log.log_info('client socket got closed')


def tester_tcp_server(log: Logger, port: int) -> None:
    """TCP server (Task 2)
    TODO:
      - Listen on 'port'; accept multiple clients
      - Receive/discard bytes; optionally log per-client bandwidth
    """
    log.log_info(f"Starting TCP server on port {port}")

    # tcp socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind the socket to the port and all hosts host
    server_socket.bind(('0.0.0.0', port))

    # staret listenning
    server_socket.listen()

    # store the threads
    thread = []

    def handle_client(client_socket: socket.socket, adress):
        """to handle one client"""
        try:
            # keep reciving data untill conection closes
            while True:
                data = client_socket.recv(2024)
                if not data:
                    break
        except Exception:
            pass
        finally:
            client_socket.close()
    try:
        while True:
            # acept new connection
            client_socket, address = server_socket.accept()

            # make a thread for thr new connection
            t = threading.Thread(target=handle_client, args=(
                client_socket, address), daemon=True)

            t.start()
            thread.append(t)

    # handle exeptions
    except KeyboardInterrupt:
        log.log_info('server is shutting down')
    finally:
        server_socket.close()


# ---------------------- UDP stubs ----------------------

def tester_udp_client(log: Logger, server_ip: str, server_port: int,
                      duration: int, interval: int,
                      rate_kbps: int, ack: bool) -> None:
    """UDP client
    Task 3 (ack == False):
      - Send datagrams at 'rate_kbps'
      - First 4 bytes = big-endian ID; start at 1; send ID=0 to end
      - Client may log sending rate, but server computes metrics
    Task 4 (ack == True):
      - Receive acks (ID + server receive timestamp)
      - Compute client-side BW / loss (via timeout) / jitter from acks and log
    """
    log.log_info(f"Starting UDP client to {server_ip}:{server_port} "
                 f"for {duration}s at {rate_kbps} Kbps (ack={ack})")
    # Common setup (safe if left unused):
    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Do not forger to bind the client socket to a port if you want to receive ACKs

    if not ack:
        # -------------------- UDP without acks --------------------
        # TODO:
        #       * every 'interval' seconds, optionally log sending rate
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #   - Compute packet trasnmission interval to match rate_kbps using you datagram size
        packet_size = 1472
        header_size = 4
        payload_size = packet_size - header_size
        payload = b'a' * payload_size

        # calculate send interval
        rate_bps = rate_kbps * 1000  # bits per second

        # bits per each packet
        packet_bits = packet_size * 8

        # amount of seconds between each interval]
        send_interval = packet_bits / rate_bps

        # initialize the test variable start

        start_time = time. time()
        end_time = start_time + duration
        packrt_id = 1  # for incrementing

        byets__sent = 0

        try:
            #   - Loop until 'duration' elapsed:
            # send loop
            while time.time() < end_time:
                #       * Build payload: 4B ID (big-endian) + (pkt_size-4) bytes
                # header big ending in an unsigned integer
                header = struct.pack('!I', packrt_id)

                packet = header + payload

            #       * sendto(...)
                # send to server client
                client_socket.sendto(packet, (server_ip, server_port))
                byets__sent += len(packet)
                packrt_id += 1

            #       * sleep until next send (pkt_interval)
                # wait for interval
                next_send_time = start_time + (packrt_id - 1) * send_interval
                sleep_time = next_send_time - time.time()
                # sleep for the amount of interval
                if sleep_time > 0:
                    time.sleep(sleep_time)

            #   - Send ID=0 to signal end; close socket
            header = struct.pack('!I', 0)
            packet = header + payload
            client_socket.sendto(packet, (server_ip, server_port))

        except ConnectionRefusedError:
            log.log_error(f"cant connect to{server_ip}:{server_port}")
        except Exception as e:
            log.log_error(f"error: {e}")

        # close the socket
        finally:
            client_socket.close()
            log.log_info('client socket got closed')

    else:
        # -------------------- UDP with acks --------------------
        # TODO:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # cbind to recive ack
        client_socket.bind(('0.0.0.0', 0))
        client_port = client_socket.getsockname()[1]
        log.log_info(f"UDP is client listening on port{client_port}")

        client_socket.settimeout(0.2)

        packet_size = 1472
        header_size = 4
        payload_size = packet_size - header_size
        payload = b'a' * payload_size

        # calculate send interval
        rate_bps = rate_kbps * 1000  # bits per second

        # bits per each packet
        packet_bits = packet_size * 8

        # amount of seconds between each interval]
        send_interval = packet_bits / rate_bps

        # initialize the test variable start

        start_time = time. time()
        end_time = start_time + duration
        next_report_time = start_time + interval

        packet_id = 1  # for incrementing
        byets_acked = 0

        #   - Keep track of pending ACKs and received ACK timestamps
        pending_acks = {}
        ack_times = {}
        ack_recived = set()

        #   - Same sending loop as Task 3
        try:
            while time.time() < end_time:
                current_time = time.time()

                expected_send_time = start_time + \
                    (packet_id - 1) * send_interval

                #       * parse 4B ID + server-timestamp (specify your chosen encoding)
                if current_time >= expected_send_time:
                    packet = struct.pack('!I', packet_id) + payload

                    # send
                    client_socket.sendto(packet, (server_ip, server_port))

                    # track ack
                    pending_acks[packet_id] = current_time
                    packet_id += 1

                #   - Non-blocking recv for acks:
                while True:
                    try:
                        ack_data, _ = client_socket.recvfrom(100)
                        if len(ack_data) >= 4:

                            # unpack
                            ack_id = struct.unpack('!I', ack_data[:4])[0]

                            #       * compute RTT / arrival deltas; update metrics
                            if ack_id != 0 and ack_id not in ack_recived:
                                ack_recived.add(ack_id)

                                # record arrival time
                                ack_times[ack_id] = time.time()
                                byets_acked += packet_size

                                # remove from the pending
                                pending_acks.pop(ack_id, None)
                    except socket.timeout:
                        break

        #   - Every 'interval' seconds, log client-side BW/loss/jitter via log.report(...)
                if current_time >= next_report_time:
                    total_duration = current_time - start_time

                    # bandwidth
                    if total_duration > 0:
                        bamdwidth_mbps = (
                            byets_acked * 8) / (total_duration * 1000000)
                    else:
                        bamdwidth_mbps = 0

                    # loss
                    lost = 0
                    for sequence, sent_time in list(pending_acks.items()):
                        if current_time - sent_time > 1:
                            lost += 1
                            del pending_acks[sequence]
                    total_sent = packet_id - 1
                    if total_sent > 0:
                        loss = (lost / total_sent * 100)
                    else:
                        loss = 0

                    # jitter
                    jitter = 0
                    if len(ack_times) >= 2:
                        sorted_ack = sorted(ack_times.items())
                        deltas = []
                        for i in range(1, len(sorted_ack)):
                            if sorted_ack[i][0] == sorted_ack[i-1][0] + 1:
                                arrial_fiffrence = sorted_ack[i][1] - \
                                    sorted_ack[i-1][1]
                                deltas.append(
                                    abs(arrial_fiffrence - send_interval))
                        if deltas:
                            jitter = sum(deltas) / len(deltas) * 1000  # ms

                    log.log_stat(current_time, server_ip, server_port,
                                 bandwidth=bamdwidth_mbps, loss=loss, jitter=jitter)

                    next_report_time += interval

            #   - End with ID=0; close socket
            last_packet = struct.pack('!I', 0) + payload
            client_socket.sendto(last_packet, (server_ip, server_port))

            # final report
            time.sleep(0.3)
            if time.time() >= next_report_time or len(ack_times) == 0:
                current_time = time.time()
                total_duration = current_time - start_time
                if total_duration > 0:
                    bamdwidth_mbps = (byets_acked * 8) / \
                        total_duration * 1000000
                else:
                    bamdwidth_mbps = 0

                log.log_stat(current_time, server_ip, server_port,
                             bandwidth=bamdwidth_mbps, loss=loss, jitter=jitter)

        except KeyboardInterrupt:
            log.log_info("interupt")

            current_time = time.time()
            total_duration = current_time - start_time
            if total_duration > 0:
                bamdwidth_mbps = (byets_acked * 8) / (total_duration * 1000000)
            else:
                bamdwidth_mbps = 0

            log.log_stat(current_time, server_ip, server_port,
                         bandwidth=bamdwidth_mbps, loss=loss, jitter=jitter)

        finally:
            client_socket.close()


def tester_udp_server(log: Logger, port: int, rate: int, interval: int, ack: bool) -> None:
    """UDP server
    Task 3 (ack == False):
      - Receive datagrams from multiple clients (track by (ip,port))
      - Compute per-client bandwidth / jitter / loss from arrivals
      - Periodically log per-client metrics via log.report(...)
    Task 4 (ack == True):
      - Same as Task 3, plus send an ack for each received datagram:
        4B ID (big-endian)
    """
    log.log_info(f"Starting UDP server on port {port} (ack={ack})")
    # Common setup (safe if left unused):

    if not ack:
        # -------------------- server-only metrics --------------------
        # TODO:
        #   - When elapsed >= interval (per client), compute:
        #     then log via: log.report("server", ip, port, bandwidth=..., loss=..., jitter=...)
        # create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('0.0.0.0', port))

        # set the details
        packet_size = 1472
        rate_bps = rate * 1024
        packet_bits = packet_size * 8
        estimate_interval = packet_bits / rate_bps

        # dictionary for keeping clients stats
        clients = {}
        try:

            #   - recvfrom(...) loop
            while True:
                # recive packets
                data, client_address = server_socket.recvfrom(
                    1500)  # abit bigger than 1472
                current_time = time.time()

            #   - Parse ID from first 4B; update per-client stats
                if len(data) < 4:
                    # ignore ivalid packet
                    continue
                packet_id = struct.unpack('!I', data[:4])[0]

                # set client stats
                if client_address not in clients:
                    # ad the new client
                    clients[client_address] = {'start_time': current_time,
                                               'last_report_time': current_time,
                                               'next_report_time': current_time + interval,
                                               'arrival_time': [],
                                               'current_interval_byets': 0,
                                               'total_byets': 0,
                                               'recived_count': 0,
                                               'min_id': packet_id,
                                               'max_id': packet_id}

                client = clients[client_address]

                # final report and calculate bandwidth, jitter, loss
                if packet_id == 0:

                    if client['recived_count'] > 0:
                        #       * bandwidth (bytes/elapsed)
                        total_duration = current_time - client['start_time']
                        if total_duration > 0:
                            bamdwidth_mbps = (
                                client['total_byets'] * 8 / 1000000) / total_duration
                        else:
                            bamdwidth_mbps = 0

                #       * loss = 1 - (recv_count / (max_id - min_id + 1))
                        expected = client['max_id'] - client['min_id'] + 1
                        if expected > 0:
                            loss = (
                                1 - (client['recived_count'] / expected)) * 100
                        else:
                            loss = 0

                #       * jitter from consecutive arrival deltas
                        jitter = 0
                        if client['recived_count'] >= 2:
                            # sort the arrived packets based on their ID
                            sorted_arrivals = sorted(
                                client['arrival_time'], key=lambda x: x[0])
                            deltas = []
                            for i in range(1, len(sorted_arrivals)):
                                if sorted_arrivals[i][0] == sorted_arrivals[i-1][0] + 1:
                                    arrial_fiffrence = sorted_arrivals[i][1] - \
                                        sorted_arrivals[i-1][1]
                                    delta = abs(arrial_fiffrence -
                                                estimate_interval)
                                    deltas.append(delta)
                            if deltas:
                                jitter = sum(deltas) / len(deltas) * 1000  # ms

                        # load the stats
                        log.log_stat(current_time, client_address[0], client_address[1],
                                     bandwidth=bamdwidth_mbps, loss=loss, jitter=jitter)
                    log.log_info(
                        f"terminating datagram, finishing UDP session from {client_address}")
                    # remoive the client whenuploaded its starts
                    del clients[client_address]
                    continue

                # update the stats of the normal packets
                client['arrival_time'].append((packet_id, current_time))
                client['current_interval_byets'] += len(data)
                client['total_byets'] += len(data)
                client['recived_count'] += 1
                client['min_id'] = min(client['min_id'], packet_id)
                client['max_id'] = max(client['max_id'], packet_id)

                # check if its time to report the interval details
                if current_time >= client['next_report_time']:
                    duration = current_time - client['last_report_time']
                    if duration > 0 and client['current_interval_byets'] > 0:
                        # band width
                        bamdwidth_mbps = (
                            client['current_interval_byets'] * 8 / 1000000) / duration

                        # loss
                        expected = client['max_id'] - client['min_id'] + 1
                        if expected > 0:
                            loss = (
                                1 - (client['recived_count'] / expected)) * 100
                        else:
                            loss = 0

                        # jitter
                        jitter = 0
                        if client['recived_count'] >= 2:
                            # sort the arrived packets based on their ID
                            sorted_arrivals = sorted(
                                client['arrival_time'], key=lambda x: x[0])
                            deltas = []
                            for i in range(1, len(sorted_arrivals)):
                                if sorted_arrivals[i][0] == sorted_arrivals[i-1][0] + 1:
                                    arrial_fiffrence = sorted_arrivals[i][1] - \
                                        sorted_arrivals[i-1][1]
                                    delta = abs(arrial_fiffrence -
                                                estimate_interval)
                                    deltas.append(delta)
                            if deltas:
                                jitter = sum(deltas) / len(deltas) * 1000  # ms

                        # load the stats for summary
                        log.log_stat(current_time, client_address[0], client_address[1],
                                     bandwidth=bamdwidth_mbps, loss=loss, jitter=jitter)

                    # reset
                    client['current_interval_byets'] = 0
                    client['last_report_time'] = current_time
                    client['next_report_time'] += interval
        except KeyboardInterrupt:
            log.log_info('server is shutting down')
        finally:
            server_socket.close()

    else:
        # -------------------- add acknowledgements --------------------
        # TODO:
        #   - Same as above, and for each received datagram:
        # create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('0.0.0.0', port))

        packet_size = 1472
        packet_bits = packet_size * 8
        # every second
        estimate_interval = packet_bits / (rate * 1000)

        # dictionary for keeping clients stats
        clients = {}

        try:

            while True:
                # recive packets
                data, client_address = server_socket.recvfrom(
                    1500)  # abit bigger than 1472
                current_time = time.time()

        #       * Build ack: 4B ID + timestamp (e.g., float via struct.pack
                if len(data) < 4:
                    # ignore ivalid packet
                    continue

                packet_id = struct.unpack('!I', data[:4])[0]
                ack_packet = struct.pack('!I', packet_id)
                server_socket.sendto(ack_packet, client_address)

                # set client stats
                if client_address not in clients:
                    # ad the new client
                    clients[client_address] = {'start_time': current_time,
                                               'last_report_time': current_time,
                                               'next_report_time': current_time + interval,
                                               'arrival_time': [],
                                               'total_byets': 0,
                                               'recived_count': 0,
                                               'last_sequence': 0,
                                               'expected_sequence': 1}

                client = clients[client_address]
        #       * sendto(ack, (ip, port))
                if packet_id == 0:
                    log.log_info(
                        f"terminating datagram, finishing UDP session from {client_address}")
                    # remoive the client whenuploaded its starts
                    del clients[client_address]
                    continue

        # update the stats of the normal packets
                client['arrival_time'].append((packet_id, current_time))
                client['total_byets'] += len(data)
                client['recived_count'] += 1
                client['last_sequence'] = packet_id
                if packet_id > client['expected_sequence']:
                    client['expected_sequence'] = packet_id + 1

        #   - Continue periodic logging as in Task 3
                # check if its time to report the interval details
                if current_time >= client['next_report_time']:
                    duration = current_time - client['last_report_time']
                    if duration > 0:
                        # band width
                        bamdwidth_mbps = (
                            client['total_byets'] * 8 / 1000000) / duration

                        # loss
                        expected = client['expected_sequence'] - 1
                        if expected > 0:
                            loss = (
                                1 - (client['recived_count'] / expected)) * 100
                        else:
                            loss = 0

                        # jitter
                        jitter = 0
                        if client['recived_count'] >= 2:
                            # sort the arrived packets based on their ID
                            sorted_arrivals = sorted(
                                client['arrival_time'], key=lambda x: x[0])
                            deltas = []
                            for i in range(1, len(sorted_arrivals)):
                                if sorted_arrivals[i][0] == sorted_arrivals[i-1][0] + 1:
                                    arrial_fiffrence = sorted_arrivals[i][1] - \
                                        sorted_arrivals[i-1][1]
                                    delta = abs(arrial_fiffrence -
                                                estimate_interval)
                                    deltas.append(delta)
                            if deltas:
                                jitter = sum(deltas) / len(deltas) * 1000  # ms

                        # load the stats for summary
                        log.log_stat(current_time, client_address[0], client_address[1],
                                     bandwidth=bamdwidth_mbps, loss=loss, jitter=jitter)

                    # reset
                    client['current_interval_byets'] = 0
                    client['last_report_time'] = current_time
                    client['next_report_time'] += interval
        except KeyboardInterrupt:
            log.log_info('server is shutting down')
        finally:
            server_socket.close()
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SCC.231 net-tester application")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("-s", "--server", action="store_true",
                      help="Run in server mode")
    mode.add_argument("-c", "--client", metavar="ADDR",
                      help="Run in client mode, connect to ADDR")

    parser.add_argument("-p", "--port", type=int,
                        default=5001, help="Port (default 5001)")
    parser.add_argument("-u", "--udp", action="store_true",
                        help="Use UDP (default TCP)")
    parser.add_argument("-a", "--ack", action="store_true",
                        help="(UDP) Enable acknowledgements")
    parser.add_argument("-t", "--duration", type=int,
                        default=60, help="Test duration seconds (default 60)")
    parser.add_argument("-i", "--interval", type=int, default=1,
                        help="Report interval seconds (default 1)")
    parser.add_argument("-r", "--rate", type=int, default=1000,
                        help="(UDP) send rate Kbps (default 1000)")
    parser.add_argument('-l', '--log', type=str, default=None,
                        help='Path to CSV log file (default: None)')

    args = parser.parse_args()
    log = Logger(csv_output=args.log)

    if args.server:
        if args.udp:
            # Task 3/4 (no-op until implemented)
            tester_udp_server(log, args.port, args.rate,
                              args.interval, args.ack)
        else:
            # Task 2 (no-op until implemented)
            tester_tcp_server(log, args.port)
    else:
        if args.udp:
            tester_udp_client(log, args.client, args.port,
                              args.duration, args.interval,
                              args.rate, args.ack)        # Task 3/4 (no-op until implemented)
        else:
            tester_tcp_client(log, args.client, args.port,
                              args.duration, args.interval)  # Task 2 (no-op until implemented)
    log.summary()
    log.close()
