clear;
clc;
close all;

fprintf('\n');
fprintf('LAUNCHING CGSMS ARCHITECTURE AUTOMATION CHAIN\n');
fprintf('\n');


currentStep = 0;
currentModule = 'Initialization';


try


    currentStep = 1;
    currentModule = 'module1.m';

    fprintf('[1/3] Spinning up Core Kinematics Engine...\n');

    run("module1.m");

    fprintf('[1/3] Core Kinematics Engine: COMPLETE\n');
    fprintf('\n');


    currentStep = 2;
    currentModule = 'module2.m';

    fprintf('[2/3] Linking Telemetry Serialization Engine...\n');

    run("module2.m");

    fprintf('[2/3] Telemetry Serialization Engine: COMPLETE\n');
    fprintf('\n');


    currentStep = 3;
    currentModule = 'module3.m';

    fprintf('[3/3] Opening Broadcast Bridge Channel...\n');

    run("module3.m");

    fprintf('[3/3] Broadcast Bridge Channel: COMPLETE\n');
    fprintf('\n');

    fprintf('\n');
    fprintf('CGSMS ARCHITECTURE AUTOMATION CHAIN: SUCCESS\n');
    fprintf('Physics Core       : ONLINE\n');
    fprintf('Telemetry Packing  : ONLINE\n');
    fprintf('Network Bridge     : ONLINE\n');
    fprintf('UDP Destination    : 127.0.0.1:5005\n');
    fprintf('System Status      : ALL LAYERS FUNCTIONING\n');
    fprintf('Telemetry Status   : DATA PAYLOAD STREAM COMPLETED\n');
    fprintf('\n');


catch ME

    fprintf('\n');
    fprintf('CGSMS ARCHITECTURE AUTOMATION CHAIN: FAILED\n');

    fprintf('Failed Step   : [%d/3]\n', currentStep);
    fprintf('Failed Module : %s\n', currentModule);
    fprintf('Error Message : %s\n', ME.message);

    fprintf('Initiating backend resource cleanup...\n');



    if exist('u', 'var')

        try

            clear u;

            fprintf('UDP object "u" released.\n');

        catch

            fprintf('Warning: UDP object "u" could not be explicitly cleared.\n');

        end

    end


    if exist('uReceiver', 'var')

        try

            clear uReceiver;

            fprintf('UDP receiver object "uReceiver" released.\n');

        catch

            fprintf('Warning: UDP receiver could not be explicitly cleared.\n');

        end

    end


    fprintf('Backend resource cleanup completed.\n');

    fprintf('PIPELINE HALTED - CORRECT THE FAILED MODULE\n');
    fprintf('\n');


    rethrow(ME);

end