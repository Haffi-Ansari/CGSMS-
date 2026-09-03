"""
=========================================================================
MODULE 5: 3D RADAR GRID CANVAS
=========================================================================

File:
    app/main.py

Purpose:
    Provide a real-time 3D visualization layer for the telemetry pipeline.

    Backend architecture:

        MATLAB Module 1
            |
            v
        Kinematics
            |
            v
        MATLAB Module 2
            |
            v
        61-byte Serialization
            |
            v
        MATLAB Module 3
            |
            | UDP
            v
        127.0.0.1:5005
            |
            v
        Python Module 4 / 5
            |
            v
        Pygame 3D Radar Canvas


MODULE 5 RESPONSIBILITIES
-------------------------
    1. Open a 1024x768 Pygame visualization window.
    2. Maintain a 60 FPS render clock.
    3. Receive telemetry from localhost UDP.
    4. Validate every packet as exactly 61 bytes.
    5. Decode the binary telemetry structure.
    6. Transform 3D coordinates into camera coordinates.
    7. Perform perspective 3D -> 2D projection.
    8. Render a projected 3D coordinate grid.
    9. Render the live vehicle position.
   10. Remain responsive while UDP data is absent.
   11. Safely release the UDP socket and Pygame resources.

PACKET FORMAT
-------------
    Timestamp             double       8 bytes
    Vehicle ID            uint32       4 bytes
    Position X            double       8 bytes
    Position Y            double       8 bytes
    Position Z            double       8 bytes
    Velocity X            double       8 bytes
    Velocity Y            double       8 bytes
    Velocity Z            double       8 bytes
    Segment Status        uint8        1 byte
    -------------------------------------------------
    TOTAL                               61 bytes

BYTE ORDER
----------
    MATLAB's typecast() on the target Windows/x86 environment produces
    native little-endian byte ordering.

    Python therefore uses:

        <dI3d3dB

    where:
        <   = little endian
        d   = double
        I   = unsigned 32-bit integer
        3d  = three position doubles
        3d  = three velocity doubles
        B   = unsigned byte

This is a benign visualization system for simulated telemetry.
=========================================================================
"""

import socket
import struct
import sys

import numpy as np
import pygame


# =========================================================================
# MODULE CONFIGURATION
# =========================================================================

# -------------------------------------------------------------------------
# Display configuration
# -------------------------------------------------------------------------

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

TARGET_FPS = 60


# -------------------------------------------------------------------------
# UDP configuration
# -------------------------------------------------------------------------

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

EXPECTED_PACKET_SIZE = 61

# Must remain synchronized with MATLAB Module 2 serialization.
PACKET_FORMAT = "<dI3d3dB"

ACTUAL_PACKET_SIZE = struct.calcsize(PACKET_FORMAT)


# -------------------------------------------------------------------------
# 3D camera configuration
# -------------------------------------------------------------------------
#
# Coordinate convention:
#
#       Y
#       ^
#       |
#       |
#       +------> X
#      /
#     /
#    Z
#
# The camera is positioned behind the scene looking toward positive Z.
# -------------------------------------------------------------------------

CAMERA_POSITION = np.array(
    [0.0, 70.0, -300.0],
    dtype=np.float64
)

CAMERA_YAW = 0.0
CAMERA_PITCH = 8.0

FOV = 500.0


# -------------------------------------------------------------------------
# Radar grid configuration
# -------------------------------------------------------------------------

GRID_MIN = -200.0
GRID_MAX = 200.0

GRID_STEP = 20.0

GROUND_Y = -20.0


# -------------------------------------------------------------------------
# Rendering configuration
# -------------------------------------------------------------------------

CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

GRID_LINE_WIDTH = 1

VEHICLE_RADIUS = 7


# =========================================================================
# PACKET DECODER
# =========================================================================

def decode_packet(data):
    """
    Decode one validated 61-byte telemetry packet.

    Parameters
    ----------
    data : bytes
        Raw UDP payload.

    Returns
    -------
    tuple
        Decoded telemetry fields.

    Packet structure:
        timestamp
        vehicle_id
        position x/y/z
        velocity x/y/z
        status
    """

    # ---------------------------------------------------------------------
    # Strict packet validation.
    # ---------------------------------------------------------------------

    if len(data) != EXPECTED_PACKET_SIZE:

        raise ValueError(
            f"Invalid packet size: expected "
            f"{EXPECTED_PACKET_SIZE}, received {len(data)}"
        )


    # ---------------------------------------------------------------------
    # Preserve the original Module 4 structure.unpack logic.
    # ---------------------------------------------------------------------

    unpacked_payload = struct.unpack(
        PACKET_FORMAT,
        data
    )


    # ---------------------------------------------------------------------
    # Preserve the original Module 4 variable assignments.
    # ---------------------------------------------------------------------

    timestamp = unpacked_payload[0]

    vehicle_id = unpacked_payload[1]

    pos_x = unpacked_payload[2]
    pos_y = unpacked_payload[3]
    pos_z = unpacked_payload[4]

    vel_vx = unpacked_payload[5]
    vel_vy = unpacked_payload[6]
    vel_vz = unpacked_payload[7]

    status_flag = unpacked_payload[8]


    return (
        timestamp,
        vehicle_id,
        pos_x,
        pos_y,
        pos_z,
        vel_vx,
        vel_vy,
        vel_vz,
        status_flag
    )


# =========================================================================
# 3D CAMERA TRANSFORMATION
# =========================================================================

def world_to_camera(point):
    """
    Transform a world-space 3D point into camera-space coordinates.

    Parameters
    ----------
    point : numpy.ndarray
        [X, Y, Z] world coordinate.

    Returns
    -------
    numpy.ndarray
        [Xc, Yc, Zc] camera-space coordinate.

    Transformation sequence:
        1. Translate relative to camera position.
        2. Apply yaw rotation.
        3. Apply pitch rotation.
    """

    # ---------------------------------------------------------------------
    # Convert to NumPy vector.
    # ---------------------------------------------------------------------

    point = np.asarray(
        point,
        dtype=np.float64
    )


    # ---------------------------------------------------------------------
    # Translate world coordinate relative to camera.
    # ---------------------------------------------------------------------

    translated = point - CAMERA_POSITION


    # ---------------------------------------------------------------------
    # Convert camera angles to radians.
    # ---------------------------------------------------------------------

    yaw = np.radians(CAMERA_YAW)
    pitch = np.radians(CAMERA_PITCH)


    # ---------------------------------------------------------------------
    # Yaw rotation.
    #
    # Rotation around vertical Y axis.
    # ---------------------------------------------------------------------

    cos_yaw = np.cos(yaw)
    sin_yaw = np.sin(yaw)

    yaw_matrix = np.array(
        [
            [cos_yaw, 0.0, -sin_yaw],
            [0.0,     1.0,  0.0],
            [sin_yaw, 0.0,  cos_yaw]
        ],
        dtype=np.float64
    )

    rotated_yaw = yaw_matrix @ translated


    # ---------------------------------------------------------------------
    # Pitch rotation.
    #
    # Rotation around X axis.
    # ---------------------------------------------------------------------

    cos_pitch = np.cos(pitch)
    sin_pitch = np.sin(pitch)

    pitch_matrix = np.array(
        [
            [1.0,       0.0,        0.0],
            [0.0, cos_pitch, -sin_pitch],
            [0.0, sin_pitch,  cos_pitch]
        ],
        dtype=np.float64
    )

    rotated = pitch_matrix @ rotated_yaw


    return rotated


# =========================================================================
# 3D -> 2D PERSPECTIVE PROJECTION
# =========================================================================

def project_point(point):
    """
    Project a 3D camera-space point onto the 2D Pygame display.

    Perspective equations:

        screen_x = center_x + Xc * FOV / Zc

        screen_y = center_y - Yc * FOV / Zc

    Returns
    -------
    tuple or None
        (screen_x, screen_y) if visible,
        otherwise None.
    """

    camera_point = world_to_camera(point)

    x_camera = camera_point[0]
    y_camera = camera_point[1]
    z_camera = camera_point[2]


    # ---------------------------------------------------------------------
    # Prevent division by zero and reject points behind the camera.
    # ---------------------------------------------------------------------

    NEAR_CLIP = 1.0

    if z_camera <= NEAR_CLIP:

        return None


    # ---------------------------------------------------------------------
    # Perspective projection.
    # ---------------------------------------------------------------------

    screen_x = CENTER_X + (
        x_camera * FOV / z_camera
    )

    screen_y = CENTER_Y - (
        y_camera * FOV / z_camera
    )


    return (
        int(screen_x),
        int(screen_y)
    )


# =========================================================================
# GRID GENERATION
# =========================================================================

def generate_grid_segments():
    """
    Generate the 3D line segments forming the radar floor.

    Grid plane:
        Y = GROUND_Y

    X range:
        -200 -> +200

    Z range:
        -200 -> +200

    Returns
    -------
    list
        List of ((x1,y1,z1), (x2,y2,z2)) segments.
    """

    segments = []

    grid_values = np.arange(
        GRID_MIN,
        GRID_MAX + GRID_STEP,
        GRID_STEP
    )


    # ---------------------------------------------------------------------
    # Lines running along X.
    # ---------------------------------------------------------------------

    for z in grid_values:

        start = np.array(
            [GRID_MIN, GROUND_Y, z],
            dtype=np.float64
        )

        end = np.array(
            [GRID_MAX, GROUND_Y, z],
            dtype=np.float64
        )

        segments.append(
            (start, end)
        )


    # ---------------------------------------------------------------------
    # Lines running along Z.
    # ---------------------------------------------------------------------

    for x in grid_values:

        start = np.array(
            [x, GROUND_Y, GRID_MIN],
            dtype=np.float64
        )

        end = np.array(
            [x, GROUND_Y, GRID_MAX],
            dtype=np.float64
        )

        segments.append(
            (start, end)
        )


    return segments


# =========================================================================
# GRID RENDERER
# =========================================================================

def draw_grid(surface, grid_segments):
    """
    Project and draw every 3D radar grid segment.

    The grid is rendered onto a transparent overlay so that the grid can
    visually behave like a lightweight HUD layer.
    """

    # ---------------------------------------------------------------------
    # Transparent overlay.
    # ---------------------------------------------------------------------

    overlay = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.SRCALPHA
    )


    # ---------------------------------------------------------------------
    # Semi-transparent teal HUD grid line.
    # ---------------------------------------------------------------------

    grid_color = (
        0,
        190,
        180,
        95
    )


    # ---------------------------------------------------------------------
    # Project each 3D line onto the screen.
    # ---------------------------------------------------------------------

    for start, end in grid_segments:

        projected_start = project_point(start)
        projected_end = project_point(end)


        # ---------------------------------------------------------------
        # Skip lines that are outside the camera's visible depth.
        # ---------------------------------------------------------------

        if projected_start is None:
            continue

        if projected_end is None:
            continue


        # ---------------------------------------------------------------
        # Draw projected line.
        # ---------------------------------------------------------------

        pygame.draw.line(
            overlay,
            grid_color,
            projected_start,
            projected_end,
            GRID_LINE_WIDTH
        )


    # ---------------------------------------------------------------------
    # Composite transparent grid onto the main display.
    # ---------------------------------------------------------------------

    surface.blit(
        overlay,
        (0, 0)
    )


# =========================================================================
# VEHICLE RENDERER
# =========================================================================

def draw_vehicle(
    surface,
    position,
    status_flag
):
    """
    Render the latest telemetry position.

    The position is transformed through the same 3D camera and perspective
    projection used by the radar grid.
    """

    projected_position = project_point(position)


    # ---------------------------------------------------------------------
    # Nothing to draw if vehicle is behind camera / clipped.
    # ---------------------------------------------------------------------

    if projected_position is None:

        return


    # ---------------------------------------------------------------------
    # Status controls visualization state.
    #
    # Status 0 is the nominal active telemetry state generated by the
    # current Module 1 simulation.
    #
    # Any non-zero status receives a different visual treatment while
    # remaining purely a visualization state.
    # ---------------------------------------------------------------------

    if status_flag == 0:

        vehicle_color = (
            255,
            255,
            255
        )

        glow_color = (
            0,
            220,
            200,
            70
        )

    else:

        vehicle_color = (
            255,
            210,
            80
        )

        glow_color = (
            255,
            180,
            40,
            70
        )


    # ---------------------------------------------------------------------
    # Create soft circular glow.
    # ---------------------------------------------------------------------

    glow_surface = pygame.Surface(
        (80, 80),
        pygame.SRCALPHA
    )

    glow_center = (
        40,
        40
    )


    for radius in range(28, 8, -4):

        alpha = int(
            8 + (28 - radius) * 2
        )

        pygame.draw.circle(
            glow_surface,
            (
                glow_color[0],
                glow_color[1],
                glow_color[2],
                alpha
            ),
            glow_center,
            radius
        )


    # ---------------------------------------------------------------------
    # Position the glow around the projected vehicle.
    # ---------------------------------------------------------------------

    glow_position = (
        projected_position[0] - 40,
        projected_position[1] - 40
    )

    surface.blit(
        glow_surface,
        glow_position
    )


    # ---------------------------------------------------------------------
    # Draw crisp vehicle marker.
    # ---------------------------------------------------------------------

    pygame.draw.circle(
        surface,
        vehicle_color,
        projected_position,
        VEHICLE_RADIUS
    )


    # ---------------------------------------------------------------------
    # Draw small center point.
    # ---------------------------------------------------------------------

    pygame.draw.circle(
        surface,
        (
            0,
            0,
            0
        ),
        projected_position,
        2
    )


# =========================================================================
# HUD RENDERER
# =========================================================================

def draw_hud(
    surface,
    telemetry,
    packets_received,
    valid_packets,
    dropped_packets,
    fps
):
    """
    Draw lightweight telemetry information over the radar canvas.
    """

    font = pygame.font.Font(
        None,
        22
    )

    small_font = pygame.font.Font(
        None,
        18
    )


    # ---------------------------------------------------------------------
    # Header.
    # ---------------------------------------------------------------------

    title = font.render(
        "3D TELEMETRY RADAR",
        True,
        (
            200,
            255,
            250
        )
    )

    surface.blit(
        title,
        (25, 20)
    )


    # ---------------------------------------------------------------------
    # Network status.
    # ---------------------------------------------------------------------

    network_text = small_font.render(
        f"UDP  {UDP_IP}:{UDP_PORT}",
        True,
        (
            120,
            210,
            205
        )
    )

    surface.blit(
        network_text,
        (25, 50)
    )


    # ---------------------------------------------------------------------
    # Rendering statistics.
    # ---------------------------------------------------------------------

    fps_text = small_font.render(
        f"FPS: {fps:5.1f}",
        True,
        (
            170,
            220,
            215
        )
    )

    surface.blit(
        fps_text,
        (25, 75)
    )


    # ---------------------------------------------------------------------
    # Packet statistics.
    # ---------------------------------------------------------------------

    packet_text = small_font.render(
        f"RX: {valid_packets}/{packets_received}",
        True,
        (
            170,
            220,
            215
        )
    )

    surface.blit(
        packet_text,
        (25, 100)
    )


    # ---------------------------------------------------------------------
    # Dropped packet count.
    # ---------------------------------------------------------------------

    drop_text = small_font.render(
        f"Dropped: {dropped_packets}",
        True,
        (
            170,
            220,
            215
        )
    )

    surface.blit(
        drop_text,
        (25, 125)
    )


    # ---------------------------------------------------------------------
    # Latest telemetry.
    # ---------------------------------------------------------------------

    if telemetry is not None:

        (
            timestamp,
            vehicle_id,
            pos_x,
            pos_y,
            pos_z,
            vel_x,
            vel_y,
            vel_z,
            status_flag
        ) = telemetry


        telemetry_lines = [
            f"TIME   : {timestamp:8.2f} s",
            f"ASSET  : {vehicle_id}",
            f"POS    : [{pos_x:7.2f}, {pos_y:7.2f}, {pos_z:7.2f}]",
            f"VEL    : [{vel_x:7.2f}, {vel_y:7.2f}, {vel_z:7.2f}]",
            f"STATUS : {status_flag}"
        ]


        telemetry_x = SCREEN_WIDTH - 330
        telemetry_y = 25


        for line in telemetry_lines:

            rendered_line = small_font.render(
                line,
                True,
                (
                    200,
                    240,
                    235
                )
            )

            surface.blit(
                rendered_line,
                (
                    telemetry_x,
                    telemetry_y
                )
            )

            telemetry_y += 25


# =========================================================================
# NETWORK RECEIVER
# =========================================================================

def create_udp_receiver():
    """
    Create and configure the localhost UDP telemetry receiver.

    The socket is explicitly non-blocking so the render loop can never
    become stuck waiting for network traffic.
    """

    # ---------------------------------------------------------------------
    # Preserve Module 4 socket creation.
    # ---------------------------------------------------------------------

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


    # ---------------------------------------------------------------------
    # Allow rapid development restarts.
    # ---------------------------------------------------------------------

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )


    # ---------------------------------------------------------------------
    # Bind to the same local endpoint used by Module 3.
    # ---------------------------------------------------------------------

    sock.bind(
        (UDP_IP, UDP_PORT)
    )


    # ---------------------------------------------------------------------
    # NON-BLOCKING MODE
    #
    # recvfrom() will immediately raise BlockingIOError when no packet
    # is waiting instead of freezing the graphics engine.
    # ---------------------------------------------------------------------

    sock.setblocking(False)


    return sock


# =========================================================================
# TELEMETRY INGESTION
# =========================================================================

def receive_latest_telemetry(
    sock,
    statistics,
    current_telemetry
):
    """
    Drain currently available UDP packets without blocking.

    Only the newest valid packet is returned.

    This is important because rendering occurs at 60 FPS while telemetry
    arrives at approximately 20 FPS. The visualization should show the
    latest known state rather than building an unnecessary queue of stale
    positions.

    Parameters
    ----------
    sock :
        Non-blocking UDP socket.

    statistics : dict
        Runtime packet counters.

    current_telemetry :
        Most recently decoded telemetry.

    Returns
    -------
    tuple
        Latest telemetry state.
    """

    latest_telemetry = current_telemetry


    # ---------------------------------------------------------------------
    # Process a bounded number of datagrams per render frame.
    #
    # The limit prevents a burst of packets from monopolizing the graphics
    # thread.
    # ---------------------------------------------------------------------

    MAX_PACKETS_PER_FRAME = 50

    packets_processed_this_frame = 0


    while packets_processed_this_frame < MAX_PACKETS_PER_FRAME:

        try:

            data, sender_address = sock.recvfrom(
                2048
            )

        except BlockingIOError:

            # -------------------------------------------------------------
            # No packet currently available.
            # -------------------------------------------------------------

            break


        except OSError as error:

            print(
                f"[WARNING] UDP receive error: {error}"
            )

            break


        packets_processed_this_frame += 1

        statistics["packets_received"] += 1


        # -----------------------------------------------------------------
        # Strict 61-byte packet filter.
        # -----------------------------------------------------------------

        if len(data) != EXPECTED_PACKET_SIZE:

            statistics["dropped_packets"] += 1

            continue


        # -----------------------------------------------------------------
        # Decode validated packet.
        # -----------------------------------------------------------------

        try:

            latest_telemetry = decode_packet(
                data
            )

            statistics["valid_packets"] += 1


        except (ValueError, struct.error) as error:

            statistics["dropped_packets"] += 1

            print(
                f"[WARNING] Packet decoding failure: {error}"
            )


    return latest_telemetry


# =========================================================================
# MAIN APPLICATION
# =========================================================================

def main():

    # =====================================================================
    # PACKET STRUCTURE VALIDATION
    # =====================================================================

    if ACTUAL_PACKET_SIZE != EXPECTED_PACKET_SIZE:

        print(
            "[FATAL] Packet structure mismatch."
        )

        print(
            f"Expected: {EXPECTED_PACKET_SIZE} bytes"
        )

        print(
            f"Actual  : {ACTUAL_PACKET_SIZE} bytes"
        )

        sys.exit(1)


    # =====================================================================
    # APPLICATION INITIALIZATION
    # =====================================================================

    print()
    print("=" * 64)
    print("MODULE 5 - 3D RADAR GRID CANVAS")
    print("=" * 64)

    print(
        f"Display Resolution       : "
        f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}"
    )

    print(
        f"Render Target            : "
        f"{TARGET_FPS} FPS"
    )

    print(
        f"UDP Telemetry Endpoint   : "
        f"{UDP_IP}:{UDP_PORT}"
    )

    print(
        f"Telemetry Payload        : "
        f"{EXPECTED_PACKET_SIZE} bytes"
    )

    print(
        f"Binary Packet Format     : "
        f"{PACKET_FORMAT}"
    )

    print(
        f"Verified Structure Size  : "
        f"{ACTUAL_PACKET_SIZE} bytes"
    )

    print("-" * 64)


    # =====================================================================
    # PYGAME INITIALIZATION
    # =====================================================================

    pygame.init()


    # ---------------------------------------------------------------------
    # Display flags.
    #
    # DOUBLEBUF improves frame presentation stability.
    # HWSURFACE requests hardware surface support where the selected
    # Pygame display backend provides it.
    #
    # The renderer itself remains pure Pygame + NumPy mathematics and does
    # not require an OpenGL/Panda3D scene graph.
    # ---------------------------------------------------------------------

    display_flags = (
        pygame.DOUBLEBUF |
        pygame.HWSURFACE
    )


    screen = pygame.display.set_mode(
        (
            SCREEN_WIDTH,
            SCREEN_HEIGHT
        ),
        display_flags
    )


    pygame.display.set_caption(
        "Module 5 - 3D Telemetry Radar"
    )


    # =====================================================================
    # CLOCK
    # =====================================================================

    clock = pygame.time.Clock()


    # =====================================================================
    # UDP INITIALIZATION
    # =====================================================================

    try:

        sock = create_udp_receiver()

    except OSError as error:

        print()
        print("=" * 64)
        print("MODULE 5 NETWORK INITIALIZATION FAILURE")
        print("=" * 64)
        print(f"Unable to bind {UDP_IP}:{UDP_PORT}")
        print(f"Reason: {error}")
        print()
        print(
            "Make sure another receiver is not already occupying "
            "UDP port 5005."
        )

        pygame.quit()

        sys.exit(1)


    print(
        "UDP receiver successfully bound."
    )

    print(
        "Non-blocking telemetry ingestion: ENABLED"
    )

    print(
        "3D projection engine: ONLINE"
    )

    print(
        "Radar grid renderer: ONLINE"
    )

    print("-" * 64)
    print(
        "Visualization running. Close the window or press ESC to exit."
    )
    print()


    # =====================================================================
    # PRE-COMPUTE STATIC RADAR GRID
    # =====================================================================

    grid_segments = generate_grid_segments()


    # =====================================================================
    # TELEMETRY STATE
    # =====================================================================

    telemetry = None


    statistics = {
        "packets_received": 0,
        "valid_packets": 0,
        "dropped_packets": 0
    }


    # =====================================================================
    # APPLICATION STATE
    # =====================================================================

    running = True


    # =====================================================================
    # MAIN REAL-TIME ENGINE
    # =====================================================================

    try:

        while running:


            # =============================================================
            # 1. EVENT PROCESSING
            # =============================================================
            #
            # Pygame events must be processed every frame so the operating
            # system continues to consider the window responsive.
            # =============================================================

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    running = False


                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        running = False


            # =============================================================
            # 2. NON-BLOCKING UDP TELEMETRY INGESTION
            # =============================================================
            #
            # The receiver never waits for a packet.
            #
            # If packets exist:
            #     consume them.
            #
            # If no packets exist:
            #     immediately continue rendering.
            # =============================================================

            telemetry = receive_latest_telemetry(
                sock,
                statistics,
                telemetry
            )


            # =============================================================
            # 3. FRAME BACKGROUND
            # =============================================================

            screen.fill(
                (
                    4,
                    12,
                    15
                )
            )


            # =============================================================
            # 4. RADAR GRID
            # =============================================================

            draw_grid(
                screen,
                grid_segments
            )


            # =============================================================
            # 5. LIVE VEHICLE
            # =============================================================

            if telemetry is not None:

                (
                    timestamp,
                    vehicle_id,
                    pos_x,
                    pos_y,
                    pos_z,
                    vel_vx,
                    vel_vy,
                    vel_vz,
                    status_flag
                ) = telemetry


                vehicle_position = np.array(
                    [
                        pos_x,
                        pos_y,
                        pos_z
                    ],
                    dtype=np.float64
                )


                draw_vehicle(
                    screen,
                    vehicle_position,
                    status_flag
                )


            # =============================================================
            # 6. HUD INFORMATION
            # =============================================================

            draw_hud(
                screen,
                telemetry,
                statistics["packets_received"],
                statistics["valid_packets"],
                statistics["dropped_packets"],
                clock.get_fps()
            )


            # =============================================================
            # 7. PRESENT FRAME
            # =============================================================

            pygame.display.flip()


            # =============================================================
            # 8. 60 FPS FRAME LIMITER
            # =============================================================

            clock.tick(
                TARGET_FPS
            )


    # =====================================================================
    # OPERATOR TERMINATION
    # =====================================================================

    except KeyboardInterrupt:

        print()
        print(
            "MODULE 5 visualization terminated by operator."
        )


    # =====================================================================
    # UNEXPECTED RUNTIME ERROR
    # =====================================================================

    except Exception as error:

        print()
        print("=" * 64)
        print("MODULE 5 RUNTIME FAILURE")
        print("=" * 64)
        print(
            f"Error: {error}"
        )

        raise


    # =====================================================================
    # GUARANTEED RESOURCE CLEANUP
    # =====================================================================

    finally:

        print()
        print("=" * 64)
        print("MODULE 5 SHUTDOWN")
        print("=" * 64)


        # -----------------------------------------------------------------
        # Close UDP socket.
        # -----------------------------------------------------------------

        try:

            sock.close()

            print(
                f"UDP socket closed: {UDP_IP}:{UDP_PORT}"
            )

        except Exception as error:

            print(
                f"[WARNING] UDP socket cleanup issue: {error}"
            )


        # -----------------------------------------------------------------
        # Close Pygame display and release graphics resources.
        # -----------------------------------------------------------------

        try:

            pygame.quit()

            print(
                "Pygame graphics resources released."
            )

        except Exception as error:

            print(
                f"[WARNING] Pygame cleanup issue: {error}"
            )


        # -----------------------------------------------------------------
        # Final diagnostics.
        # -----------------------------------------------------------------

        print("-" * 64)

        print(
            f"Datagrams received : "
            f"{statistics['packets_received']}"
        )

        print(
            f"Valid packets      : "
            f"{statistics['valid_packets']}"
        )

        print(
            f"Dropped packets    : "
            f"{statistics['dropped_packets']}"
        )

        print(
            f"Expected payload   : "
            f"{EXPECTED_PACKET_SIZE} bytes"
        )

        print(
            "Network resource status: RELEASED"
        )

        print(
            "Visualization status   : TERMINATED CLEANLY"
        )

        print("=" * 64)


# =========================================================================
# APPLICATION ENTRY POINT
# =========================================================================

if __name__ == "__main__":

    main()