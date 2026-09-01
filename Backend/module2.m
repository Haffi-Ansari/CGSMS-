
clearvars -except Time Vehicle_ID Position Velocity Segment_Status;
clc;

EXPECTED_PACKET_SIZE = 61;


requiredVariables = {
    'Time'
    'Vehicle_ID'
    'Position'
    'Velocity'
    'Segment_Status'
    };

for variableIndex = 1:numel(requiredVariables)

    variableName = requiredVariables{variableIndex};

    if ~exist(variableName, 'var')

        error( ...
            'MODULE 2 ERROR: Required variable "%s" was not found. Run Module 1 first.', ...
            variableName);

    end

end


numSteps = length(Time);

if length(Vehicle_ID) ~= numSteps
    error('MODULE 2 ERROR: Vehicle_ID length does not match Time.');
end

if size(Position, 1) ~= numSteps || size(Position, 2) ~= 3
    error('MODULE 2 ERROR: Position must be an N-by-3 matrix.');
end

if size(Velocity, 1) ~= numSteps || size(Velocity, 2) ~= 3
    error('MODULE 2 ERROR: Velocity must be an N-by-3 matrix.');
end

if length(Segment_Status) ~= numSteps
    error('MODULE 2 ERROR: Segment_Status length does not match Time.');
end


packetBufferHistory = zeros( ...
    numSteps, ...
    EXPECTED_PACKET_SIZE, ...
    'uint8');

serializedPacketCount = 0;


for k = 1:numSteps


    serializedTimestamp = double(Time(k));

    timestampBytes = typecast( ...
        serializedTimestamp, ...
        'uint8');

    serializedVehicleID = uint32(Vehicle_ID(k));

    vehicleIDBytes = typecast( ...
        serializedVehicleID, ...
        'uint8');


    serializedPositionX = double(Position(k, 1));
    serializedPositionY = double(Position(k, 2));
    serializedPositionZ = double(Position(k, 3));

    positionXBytes = typecast( ...
        serializedPositionX, ...
        'uint8');

    positionYBytes = typecast( ...
        serializedPositionY, ...
        'uint8');

    positionZBytes = typecast( ...
        serializedPositionZ, ...
        'uint8');


    serializedVelocityX = double(Velocity(k, 1));
    serializedVelocityY = double(Velocity(k, 2));
    serializedVelocityZ = double(Velocity(k, 3));

    velocityXBytes = typecast( ...
        serializedVelocityX, ...
        'uint8');

    velocityYBytes = typecast( ...
        serializedVelocityY, ...
        'uint8');

    velocityZBytes = typecast( ...
        serializedVelocityZ, ...
        'uint8');


    serializedStatus = uint8(Segment_Status(k));

    statusBytes = typecast( ...
        serializedStatus, ...
        'uint8');


    packetBuffer = [ ...
        timestampBytes, ...
        vehicleIDBytes, ...
        positionXBytes, ...
        positionYBytes, ...
        positionZBytes, ...
        velocityXBytes, ...
        velocityYBytes, ...
        velocityZBytes, ...
        statusBytes ...
        ];


    if length(packetBuffer) ~= EXPECTED_PACKET_SIZE

        error( ...
            ['MODULE 2 ERROR: Invalid packet size at frame %d. ', ...
             'Expected %d bytes but generated %d bytes.'], ...
            k, ...
            EXPECTED_PACKET_SIZE, ...
            length(packetBuffer));

    end


    packetBufferHistory(k, :) = packetBuffer;

    serializedPacketCount = serializedPacketCount + 1;

end


fprintf('\n');
fprintf('============================================================\n');
fprintf(' MODULE 2: SERIALIZATION COMPLETE\n');
fprintf('============================================================\n');
fprintf('Frames processed : %d\n', numSteps);
fprintf('Packets created  : %d\n', serializedPacketCount);
fprintf('Packet size      : %d bytes\n', EXPECTED_PACKET_SIZE);
fprintf('Buffer dimensions: %d x %d\n', ...
    size(packetBufferHistory, 1), ...
    size(packetBufferHistory, 2));
fprintf('Status           : SUCCESS\n');
fprintf('============================================================\n');
fprintf('\n');