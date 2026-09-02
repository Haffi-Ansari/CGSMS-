import socket
import struct
import sys
import time


UDP_IP = "127.0.0.1"
UDP_PORT = 5005

EXPECTED_PACKET_SIZE = 61

PACKET_FORMAT = "<dI3d3dB"

ACTUAL_PACKET_SIZE = struct.calcsize(PACKET_FORMAT)


def decode_packet(data):
    """
    Decode one validated 61-byte telemetry packet.

    Returns:
        tuple containing:
            timestamp
            vehicle_id
            pos_x
            pos_y
            pos_z
            vel_x
            vel_y
            vel_z
            status
    """

    if len(data) != EXPECTED_PACKET_SIZE:
        raise ValueError(
            f"Invalid packet size: expected "
            f"{EXPECTED_PACKET_SIZE}, received {len(data)}"
        )

    return struct.unpack(PACKET_FORMAT, data)


def main():

    print()
    print("=" * 64)
    print("MODULE 4 - LIVE TELEMETRY INGESTION NETWORK ENGINE")
    print("=" * 64)

    print(f"Targeting Loopback Address : {UDP_IP}:{UDP_PORT}")
    print(f"Expected Payload Size      : {EXPECTED_PACKET_SIZE} bytes")
    print(f"Python Packet Format       : {PACKET_FORMAT}")
    print(f"Python Calculated Size     : {ACTUAL_PACKET_SIZE} bytes")
    print("-" * 64)


    if ACTUAL_PACKET_SIZE != EXPECTED_PACKET_SIZE:

        print(
            "[FATAL] Python packet structure does not equal "
            f"{EXPECTED_PACKET_SIZE} bytes."
        )

        sys.exit(1)


    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    packets_received = 0
    valid_packets = 0
    dropped_packets = 0


    try:


        sock.bind((UDP_IP, UDP_PORT))

        print("Network port successfully opened.")
        print("Awaiting telemetry stream...")
        print()


        dropped_packets = 0

        first_packet_time = None
        last_packet_time = None


        while True:


            data, sender_address = sock.recvfrom(2048)

            packets_received += 1


            if len(data) != EXPECTED_PACKET_SIZE:

                dropped_packets += 1

                print(
                    f"[WARNING] Dropped packet #{packets_received}: "
                    f"expected {EXPECTED_PACKET_SIZE} bytes, "
                    f"received {len(data)} bytes."
                )

                continue


            try:

                unpacked_payload = decode_packet(data)

            except struct.error as error:

                dropped_packets += 1

                print(
                    f"[WARNING] Packet decoding failure: {error}"
                )

                continue


            timestamp = unpacked_payload[0]
            vehicle_id = unpacked_payload[1]

            pos_x = unpacked_payload[2]
            pos_y = unpacked_payload[3]
            pos_z = unpacked_payload[4]

            vel_x = unpacked_payload[5]
            vel_y = unpacked_payload[6]
            vel_z = unpacked_payload[7]

            status_flag = unpacked_payload[8]


            valid_packets += 1

            if first_packet_time is None:
                first_packet_time = time.perf_counter()

            last_packet_time = time.perf_counter()


            print(
                f"t={timestamp:6.2f}s | "
                f"ID={vehicle_id} | "
                f"POS=["
                f"{pos_x:8.3f}, "
                f"{pos_y:8.3f}, "
                f"{pos_z:8.3f}] | "
                f"VEL=["
                f"{vel_x:7.3f}, "
                f"{vel_y:7.3f}, "
                f"{vel_z:7.3f}] | "
                f"STATUS={status_flag}"
            )


    except KeyboardInterrupt:

        print()
        print("=" * 64)
        print("MODULE 4 TERMINATED BY OPERATOR")
        print("=" * 64)


    except OSError as error:

        print()
        print("=" * 64)
        print("MODULE 4 NETWORK ERROR")
        print("=" * 64)
        print(f"Error: {error}")
        print()
        print(
            "Check whether another application is already using "
            f"UDP port {UDP_PORT}."
        )



    except Exception as error:

        print()
        print("=" * 64)
        print("MODULE 4 UNEXPECTED ERROR")
        print("=" * 64)
        print(f"Error: {error}")



    finally:

        sock.close()

        print()
        print("-" * 64)
        print("MODULE 4 FINAL DIAGNOSTICS")
        print("-" * 64)
        print(f"Datagrams received : {packets_received}")
        print(f"Valid packets      : {valid_packets}")
        print(f"Dropped packets    : {dropped_packets}")
        print(f"Expected size      : {EXPECTED_PACKET_SIZE} bytes")
        print(f"Packet format      : {PACKET_FORMAT}")
        print("-" * 64)
        print("Network socket safely closed.")
        print(f"UDP port {UDP_PORT} released.")
        print("=" * 64)


if __name__ == "__main__":
    main()