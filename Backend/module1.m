clear;
clc;
close all;


dt = 0.05;

updateFrequency = 1 / dt;

simulationDuration = 30.0;

transitionTime = 15.0;


A = [-100.0, 50.0, -100.0];

B = [100.0, 0.0, 100.0];

recoveryWaypoint = [0.0, -10.0, 0.0];

AB = B - A;

distanceAB = norm(AB);

nominalSpeed = distanceAB / transitionTime;

initialVelocity = directionAB * nominalSpeed;

Vx_initial = initialVelocity(1);
Vy_initial = initialVelocity(2);
Vz_initial = initialVelocity(3);

time = 0:dt:simulationDuration;

numSteps = length(time);


Time = zeros(numSteps, 1);

Position = zeros(numSteps, 3);

Velocity = zeros(numSteps, 3);

Segment_Status = zeros(numSteps, 1);

currentPosition = A;
currentVelocity = initialVelocity;


for k = 1:numSteps

    currentTime = time(k);


    if currentTime < transitionTime

        if k > 1
            currentPosition = currentPosition + ...
                              initialVelocity * dt;
        end

        currentVelocity = initialVelocity;

        % Segment status.
        currentStatus = 0;

    else


        if ~exist("transitionPosition", "var")
            transitionPosition = currentPosition;
        end


        elapsedTransitionTime = currentTime - transitionTime;

        transitionDuration = ...
            simulationDuration - transitionTime;

        progress = elapsedTransitionTime / transitionDuration;

        progress = max(0.0, min(1.0, progress));


        smoothBlend = ...
            10 * progress^3 ...
            - 15 * progress^4 ...
            + 6 * progress^5;


        blendDerivative = ...
            30 * progress^2 ...
            - 60 * progress^3 ...
            + 30 * progress^4;


        displacementToRecovery = ...
            recoveryWaypoint - transitionPosition;

        currentPosition = ...
            transitionPosition + ...
            smoothBlend .* displacementToRecovery;


        currentVelocity = ...
            displacementToRecovery .* ...
            blendDerivative ./ transitionDuration;


        % Segment status.
        currentStatus = 1;


        if progress >= 1.0

            currentPosition = recoveryWaypoint;
            currentVelocity = [0.0, 0.0, 0.0];

        end

    end



    Time(k) = currentTime;

    Position(k, :) = currentPosition;

    Velocity(k, :) = currentVelocity;

    Segment_Status(k) = currentStatus;

end


transitionIndex = find( ...
    abs(Time - transitionTime) < dt / 10, ...
    1 ...
);

transitionPoint = Position(transitionIndex, :);

finalPoint = Position(end, :);


fprintf('\n');
fprintf('====================================================\n');
fprintf('MODULE 1 - KINEMATIC TRAJECTORY SIMULATION\n');
fprintf('====================================================\n');

fprintf('Update frequency : %.1f Hz\n', updateFrequency);
fprintf('Time step        : %.3f s\n', dt);
fprintf('Duration         : %.1f s\n', simulationDuration);

fprintf('\nPrimary Route\n');
fprintf('A = [%.2f, %.2f, %.2f]\n', A);
fprintf('B = [%.2f, %.2f, %.2f]\n', B);

fprintf('\nInitial Velocity\n');
fprintf('Vx = %.4f\n', Vx_initial);
fprintf('Vy = %.4f\n', Vy_initial);
fprintf('Vz = %.4f\n', Vz_initial);
fprintf('Speed = %.4f units/s\n', nominalSpeed);

fprintf('\nTransition Point @ t = %.2f s\n', transitionTime);
fprintf('X = %.4f\n', transitionPoint(1));
fprintf('Y = %.4f\n', transitionPoint(2));
fprintf('Z = %.4f\n', transitionPoint(3));

fprintf('\nRecovery Waypoint\n');
fprintf('[%.2f, %.2f, %.2f]\n', recoveryWaypoint);

fprintf('\nFinal Position\n');
fprintf('[%.4f, %.4f, %.4f]\n', finalPoint);

fprintf('\n====================================================\n');


figure( ...
    'Name', 'Module 1 - 3D Kinematic Trajectory', ...
    'NumberTitle', 'off' ...
);

hold on;

segment0 = Segment_Status == 0;

plot3( ...
    Position(segment0, 1), ...
    Position(segment0, 2), ...
    Position(segment0, 3), ...
    'r-', ...
    'LineWidth', 2.0 ...
);


segment1 = Segment_Status == 1;

plot3( ...
    Position(segment1, 1), ...
    Position(segment1, 2), ...
    Position(segment1, 3), ...
    'g-', ...
    'LineWidth', 2.0 ...
);


plot3( ...
    A(1), A(2), A(3), ...
    'ko', ...
    'MarkerSize', 9, ...
    'MarkerFaceColor', 'b' ...
);


plot3( ...
    transitionPoint(1), ...
    transitionPoint(2), ...
    transitionPoint(3), ...
    'ks', ...
    'MarkerSize', 9, ...
    'MarkerFaceColor', 'y' ...
);


plot3( ...
    finalPoint(1), ...
    finalPoint(2), ...
    finalPoint(3), ...
    'kd', ...
    'MarkerSize', 9, ...
    'MarkerFaceColor', 'm' ...
);


xlabel('X Coordinate');
ylabel('Y Coordinate');
zlabel('Z Coordinate');

title('3D Vehicle Kinematic Trajectory');

legend( ...
    'Segment 0 - Primary Route', ...
    'Segment 1 - Alternate Route', ...
    'Starting Coordinate A', ...
    'Transition Point t = 15 s', ...
    'Final Recovery Waypoint', ...
    'Location', ...
    'best' ...
);

grid on;
grid minor;

axis equal;

view(3);

hold off;

velocityMagnitude = sqrt( ...
    Velocity(:,1).^2 + ...
    Velocity(:,2).^2 + ...
    Velocity(:,3).^2 ...
);

figure( ...
    'Name', 'Velocity Magnitude Verification', ...
    'NumberTitle', 'off' ...
);

plot( ...
    Time, ...
    velocityMagnitude, ...
    'LineWidth', 1.8 ...
);

hold on;

xline( ...
    transitionTime, ...
    '--k', ...
    'Transition t = 15 s', ...
    'LineWidth', 1.2 ...
);

xlabel('Time [s]');
ylabel('Velocity Magnitude');

title('Vehicle Velocity Magnitude');

grid on;
grid minor;

hold off;
