
clearvars -except packetBufferHistory;
clc;

EXPECTED_PACKET_SIZE = 61;

DestinationIP   = '127.0.0.1';
DestinationPort = 5005;

if ~exist('packetBufferHistory', 'var')

    error( ...
        ['MODULE 3 ERROR: packetBufferHistory was not found. ', ...
         'Run module2.m first.']);

end

[numSteps, packetSize] = size(packetBufferHistory);

if packetSize ~= EXPECTED_PACKET_SIZE

    error( ...
        ['MODULE 3 ERROR: Invalid Module 2 buffer size. ', ...
         'Expected packets of %d bytes but received %d bytes.'], ...
        EXPECTED_PACKET_SIZE, ...
        packetSize);

end

u = udpport("datagram", "IPV4");

cleanupGuard = onCleanup(@() releaseUDP(u));

transmittedPacketCount = 0;


fprintf('\n');
fprintf('============================================================\n');
fprintf(' MODULE 3: LOCAL UDP NETWORK BRIDGE\n');
fprintf('============================================================\n');
fprintf('Packets available : %d\n', numSteps);
fprintf('Packet size       : %d bytes\n', EXPECTED_PACKET_SIZE);
fprintf('Destination IP    : %s\n', DestinationIP);
fprintf('Destination Port  : %d\n', DestinationPort);
fprintf('------------------------------------------------------------\n');

try

    for k = 1:numSteps

        packetBuffer = packetBufferHistory(k, :);


        if length(packetBuffer) ~= EXPECTED_PACKET_SIZE

            error( ...
                ['MODULE 3 ERROR: Packet %d has invalid size. ', ...
                 'Expected %d bytes but received %d bytes.'], ...
                k, ...
                EXPECTED_PACKET_SIZE, ...
                length(packetBuffer));

        end


        packetBuffer = uint8(packetBuffer);


        write( ...
            u, ...
            packetBuffer, ...
            'uint8', ...
            DestinationIP, ...
            DestinationPort);


        transmittedPacketCount = transmittedPacketCount + 1;


        pause(0.05);

    end


    fprintf('------------------------------------------------------------\n');
    fprintf('UDP transmission complete.\n');
    fprintf('Packets transmitted : %d\n', transmittedPacketCount);
    fprintf('Packet size         : %d bytes\n', EXPECTED_PACKET_SIZE);
    fprintf('Destination         : %s:%d\n', ...
        DestinationIP, ...
        DestinationPort);
    fprintf('UDP stream status   : GRACEFULLY TERMINATED\n');
    fprintf('------------------------------------------------------------\n');


catch ME

    fprintf('\n');
    fprintf('============================================================\n');
    fprintf(' MODULE 3: UDP TRANSMISSION ERROR\n');
    fprintf('============================================================\n');
    fprintf('Packets transmitted before failure: %d\n', ...
        transmittedPacketCount);
    fprintf('Releasing UDP socket...\n');


    if exist('u', 'var')

        try
            clear u;
        catch

        end

    end


    fprintf('UDP socket release attempted.\n');
    fprintf('============================================================\n');

    rethrow(ME);

end


if exist('u', 'var')

    try
        clear u;
    catch

    end

end


fprintf('\n');
fprintf('MODULE 3 RESOURCE STATUS: UDP socket released.\n');
fprintf('Local UDP bridge is ready for the next execution.\n');
fprintf('\n');


function releaseUDP(udpObject)

    try

        if ~isempty(udpObject)

            clear udpObject;

        end

    catch

    end

end