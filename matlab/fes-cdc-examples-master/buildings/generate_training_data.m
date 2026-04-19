clc; close all; clear all;

rng(1337)

print_figs = 0;

set(groot, 'defaultAxesTickLabelInterpreter','latex'); 
set(groot, 'defaultLegendInterpreter','latex');


LocalPath = pwd;

addpath(genpath('./fcns'))

buildingType = 'Swissaverage';
demoBuilding = 'SwAvHW80Converted';

Opti = 'OptiT1'; % OptiT4 does not work. The buildingelements file is incorrect, likely needs to be replaced with the ones from t1. this doesn't make sense to me

thermalModelDataDir =   [LocalPath,filesep,'OptiT1',filesep','Swissaverage',filesep,demoBuilding,filesep,'ThermalModel'];
EHFModelDataDir =       [LocalPath,filesep,'OptiT1',filesep','Swissaverage',filesep,demoBuilding,filesep,'EHFM'];

u_type = "hysteresis-random"; %"hyseresis" "hysteresis-random" hysteresis random applies a RBS input sequence while the temperatures are within min and max bounds


%% --------------------------------------------------------------------------------------
% 1) Create a building
% --------------------------------------------------------------------------------------

% Create an empty Building object with an optional identifier argument.
buildingIdentifier = demoBuilding;
B = Building(buildingIdentifier);

%% --------------------------------------------------------------------------------------
% 2) Load the thermal model data
% --------------------------------------------------------------------------------------

% Load the thermal model data. 
B.loadThermalModelData(thermalModelDataDir);

%% ------------
% compute the normals of each building element to validate orientation
% for i = 1:length(B.thermal_model_data.building_elements)
%     be = B.thermal_model_data.building_elements(i);
% 
%     % Skip elements without vertices
%     if isempty(be.vertices) || length(be.vertices) < 3
%         continue
%     end
% 
%     % Extract numeric coordinates from Vertex objects
%     coords = [[be.vertices.x]', [be.vertices.y]', [be.vertices.z]'];
% 
%     % Compute outward normal via cross product of two edges
%     e1 = coords(2,:) - coords(1,:);
%     e2 = coords(3,:) - coords(1,:);
%     n  = cross(e1, e2);
%     n  = n / norm(n);
% 
%     fprintf('BE %s: normal = [%+.2f, %+.2f, %+.2f]  →  ', ...
%         be.identifier, n(1), n(2), n(3));
% 
%     % Interpret dominant direction
%     [~, ax] = max(abs(n));
%     dirs = {'E/W (X)', 'N/S (Y)', 'floor/ceiling (Z)'};
%     signs = {'+E', '+N', '+up'; '-W', '-S', '-down'};
%     sign_idx = 1 + (n(ax) < 0);
%     fprintf('%s\n', signs{sign_idx, ax});
% end

%% --------------------------------------------------------------------------------------
% 3) Declare external heat flux models that should be included
% --------------------------------------------------------------------------------------

% Heat exchange with ambient air and solar gains
EHFModelClassFile = 'BuildingHull.m';                                         % This is the m-file defining this EHF model's class.
EHFModelDataFile = [EHFModelDataDir,filesep,'buildinghull'];                  % This is the spreadsheet containing this EHF model's specification.
EHFModelIdentifier = 'BuildingHull';                                          % This string identifies the EHF model uniquely
B.declareEHFModel(EHFModelClassFile,EHFModelDataFile,EHFModelIdentifier);

% Ventilation
EHFModelClassFile = 'AHU.m'; 
EHFModelDataFile = [EHFModelDataDir,filesep,'ahu']; 
EHFModelIdentifier = 'AHU1';
B.declareEHFModel(EHFModelClassFile,EHFModelDataFile,EHFModelIdentifier);

% InternalGains
EHFModelClassFile = 'InternalGains.m'; 
EHFModelDataFile = [EHFModelDataDir,filesep,'internalgains']; 
EHFModelIdentifier = 'IG';
B.declareEHFModel(EHFModelClassFile,EHFModelDataFile,EHFModelIdentifier);

% TABS
% EHFModelClassFile = 'BEHeatfluxes.m'; 
% EHFModelDataFile = [EHFModelDataDir,filesep,'BEHeatfluxes']; 
% EHFModelIdentifier = 'TABS';
% B.declareEHFModel(EHFModelClassFile,EHFModelDataFile,EHFModelIdentifier);

% Radiators
EHFModelClassFile = 'Radiators.m'; 
EHFModelDataFile = [EHFModelDataDir,filesep,'radiators']; 
EHFModelIdentifier = 'Rad';
B.declareEHFModel(EHFModelClassFile,EHFModelDataFile,EHFModelIdentifier);

%% --------------------------------------------------------------------------------------
% 4) Display thermal model data to Command Window and draw Building (optional) 
% --------------------------------------------------------------------------------------

% % Print the thermal model data in the Command Window for an overview
% B.printThermalModelData;
% 
% 3-D plot of Building with increased font size for plots
% B.drawBuilding;
% zlabel('z [m]','interpreter','latex','fontsize',40)
% xlabel('East','interpreter','latex','fontsize',40) % positive x points to east
% ylabel('North','interpreter','latex','fontsize',40) % positive y points to north
% ax = gca;
% ax.FontSize = 20;

%%
% Two separate PDFs:
%   - building_isometric.pdf
%   - building_floorplan.pdf

% pdfWidthCm    = 12.0;   % A4 width is 21.0 cm, leave a tiny margin
% pdfHeightIso  = 7.0;
% pdfHeightTop  = 7.0;
% 
% %% 1) Isometric / current 3D-like view
% figIso = B.drawBuilding;
% axIso = get(figIso, 'CurrentAxes');
% 
% xlabel(axIso, 'East',  'interpreter', 'latex', 'fontsize', 40);
% ylabel(axIso, 'North', 'interpreter', 'latex', 'fontsize', 40);
% zlabel(axIso, 'z [m]', 'interpreter', 'latex', 'fontsize', 40);
% axIso.FontSize = 26;
% 
% view(axIso, 3);              % close to MATLAB's default 3D view
% axis(axIso, 'tight');
% tightAxes(axIso);
% exportgraphics(figIso,'building_isometric.pdf','ContentType','vector')
% 
% %% 2) Floorplan / top view
% figTop = B.drawBuilding;
% axTop = get(figTop, 'CurrentAxes');
% 
% xlabel(axTop, 'East',  'interpreter', 'latex', 'fontsize', 40);
% ylabel(axTop, 'North', 'interpreter', 'latex', 'fontsize', 40);
% zlabel(axTop, '');
% axTop.FontSize = 26;
% 
% view(axTop, 0, 90);          % view from above
% axis(axTop, 'tight');
% tightAxes(axTop);
% exportgraphics(figTop,'building_floorplan.pdf','ContentType','vector')

%% --------------------------------------------------------------------------------------
% 5) Generate thermal model and full model
% --------------------------------------------------------------------------------------

% Generate thermal model (optional)
% B.generateThermalModel;

% Generate (full) building model (includes thermal model generation if not yet done)
B.generateBuildingModel;

% Display all available identifiers (these are the names of the control inputs / disturbances / states in the same order as they appear in the matrices)
% B.building_model.printIdentifiers;

% Disretization
Ts_hrs = 0.25; % in units of hours
% Ts_hrs = 1/60; % 1 minute in units of hours
B.building_model.setDiscretizationStep(Ts_hrs);
B.building_model.discretize();

%% --------------------------------------------------------------------------------------
% 7) Retrieve Matrices and generate costs and constraints
% --------------------------------------------------------------------------------------

% model is
% x_{k+1} = Ax_k + Bu*u_k + Bv*v_k + sum_{i=1}^{n_u}(Bvu,i * v_k + Bxu,i * x_k) * u_{k,i}
 
% Access of full model matrices
% full model should be both thermal and external combined

% note to self regarding bilinearity
% there are 10 disturbances and 8 inputs
% the matrices Bvu: [113×10×8 double] give us the bilinearity for each
% input

A_disc = B.building_model.discrete_time_model.A; % same for Bu,Bv,Bvu,Bxu
Bu_disc = B.building_model.discrete_time_model.Bu;
Bv_disc = B.building_model.discrete_time_model.Bv;
Bvu_disc = B.building_model.discrete_time_model.Bvu;
Bxu_disc = B.building_model.discrete_time_model.Bxu;


A_cont = B.building_model.continuous_time_model.A; % same for Bu,Bv,Bvu,Bxu
Bu_cont = B.building_model.continuous_time_model.Bu;
Bv_cont = B.building_model.continuous_time_model.Bv;
Bxu_cont = B.building_model.continuous_time_model.Bxu;
Bvu_cont = B.building_model.continuous_time_model.Bvu;


% stiffness_ratio = min(real(eig(A_cont)))/max(real(eig(A_cont)));

%% Model reduction

sys_disc = ss(A_disc, [Bu_disc, Bv_disc], eye(size(A_disc,1)), []);
sys_disc.Ts = Ts_hrs;

assess_model_reduction = 0;
if assess_model_reduction == 1
    % Get Hankel singular values to assess state importance
    hsv = hsvd(sys_disc);

    % User-controlled settings
    fs = 20;                    % master font size
    fig_w = 900;                % figure width in pixels
    fig_h = 600;                % figure height in pixels

    % Create figure
    f = figure('Position', [100 100 fig_w fig_h]);

    % Plot
    semilogy(hsv, 'o-', 'LineWidth', 2);
    xline(10, 'k--', 'LineWidth', 1.5)
    grid off

    % Labels
    xlabel('State Number', 'Interpreter', 'latex');
    ylabel('Hankel Singular Value', 'Interpreter', 'latex');
    title('Hankel Singular Values', 'Interpreter', 'latex');

    % Apply one font size to the whole axes
    ax = gca;
    ax.FontSize = fs;

    % Optional: make title/labels exactly the same size as fs
    ax.TitleFontSizeMultiplier = 1;
    ax.LabelFontSizeMultiplier = 1;

    % Save as PDF
    exportgraphics(f, 'hankel_singular_values.pdf', 'ContentType', 'vector');
    % Find states contributing 99% of system energy
    cumulative_energy = cumsum(hsv.^2) / sum(hsv.^2);
    n_reduced = find(cumulative_energy > 0.99, 1, 'first');
    fprintf('States for 99%% energy: %d (from %d)\n', n_reduced, length(hsv));

end

%% Load weather data
year = 2021;
[dt_weather, Tamb_raw, SolRad_raw] = getTamb();

% Create datetime array for simulation
startDate = datetime(year, 1, 1, 0, 0, 0);
endDate = startDate + years(1);
dt = (startDate:minutes(Ts_hrs*60):endDate)';

% Interpolate ambient temperature to match simulation timestep
Tamb = interp1(dt_weather, Tamb_raw, dt, 'linear', 'extrap');
fprintf('Resampled weather data from %d to %d samples\n', ...
    length(Tamb_raw), length(Tamb));

fprintf('Minimum Ambient Temp: %.1f\n',min(Tamb))
fprintf('Maximum Ambient Temp: %.1f\n',max(Tamb))
n_timeSteps = length(Tamb);

fprintf('Simulation period: %s to %s\n', datestr(dt(1)), datestr(dt(end)));
fprintf('Number of timesteps: %d (%.1f days)\n', n_timeSteps, n_timeSteps*Ts_hrs/24);

% Interpolate Solar Radiaton to match simulation timestep
SolRad = interp1(dt_weather, SolRad_raw, dt, 'linear', 'extrap');
fprintf('Resampled weather data from %d to %d samples\n', ...
    length(SolRad_raw), length(SolRad));

fprintf('Minimum Total Solar Radiation: %.1f\n',min(SolRad))
fprintf('Maximum Total Solar Radiation: %.1f\n',max(SolRad))

%% Get constraints
% Get constraint matrices such that % Fx*x+Fu*u+Fv*v <= g. These are the constraints for one particular set of potentially 
% time-varying constraintsParameters. Every row of the matrices represents one constraint the name of which is the 
% corresponding entry in constraint_identifiers. The parameters that have to be passed must be in the form 
% constraintsParameters.<EHF_identifier>.<parameters>. Check the documentation to learn which <parameters> are necessary for
% a particular EHF model.


constraintsParameters = struct();

% u_n_max = 1;
% u_h_max = 1000;
% u_c_max = 100;
u_n_max = 0;
u_h_max = 0;
u_c_max = 0;

constraintsParameters.AHU1.T_supply_max = 30;
constraintsParameters.AHU1.T_supply_min = 0;
constraintsParameters.AHU1.Q_heat_max = u_h_max;
constraintsParameters.AHU1.Q_cool_max = u_c_max;
constraintsParameters.AHU1.Q_heat_min = 0;
constraintsParameters.AHU1.Q_cool_min = 0;
constraintsParameters.AHU1.mdot_min = 0;
constraintsParameters.AHU1.mdot_max = u_n_max;
constraintsParameters.AHU1.x = 23*ones(length(B.building_model.identifiers.x),1);
constraintsParameters.AHU1.v_fullModel = 20*ones(length(B.building_model.identifiers.v),1);

%% Get zone areas to compute the heat inputs

u_max = 50; %original was 50

% Assign your array to a shorter variable name for clarity
zones_array = B.thermal_model_data.zones;
num_zones = numel(zones_array);
%    The curly braces {} are crucial here.
all_area_strings = {zones_array.area};

% 2. Convert the entire cell array of strings to a numeric vector
zone_areas = str2double(all_area_strings);

% After the loop, the 'areas' variable will contain [area1, area2, area3, area4, area5]
u_max_areas = ones(1, num_zones) * u_max;

constraintsParameters.Rad.Q_rad_Radiator1_min = 0;
constraintsParameters.Rad.Q_rad_Radiator1_max = u_max;
constraintsParameters.Rad.Q_rad_Radiator2_min = 0;
constraintsParameters.Rad.Q_rad_Radiator2_max = u_max;
constraintsParameters.Rad.Q_rad_Radiator3_min = 0;
constraintsParameters.Rad.Q_rad_Radiator3_max = u_max;
constraintsParameters.Rad.Q_rad_Radiator4_min = 0;
constraintsParameters.Rad.Q_rad_Radiator4_max = u_max;
constraintsParameters.Rad.Q_rad_Radiator5_min = 0;
constraintsParameters.Rad.Q_rad_Radiator5_max = u_max;

[Fx,Fu,Fv,g] = B.building_model.getConstraintsMatrices(constraintsParameters);

% Soften x constraints into cost function with slack variables. then we are
% left with Fu*u <= g from the model Fx*x + Fu*u + Fv*v <= g

% I'm setting the constraints on the states separately from the Fx matrix
% after the identifiers are made

if abs(sum(sum(Fx(:,:)))) > 1e-8
    warning('Constraints on the states are being ignored')
elseif abs(sum(sum(Fv(:,:)))) > 1e-8
    warning('Constraints on the disturbances are being ignored, and there really shouldnt be any')
end

% Get cost vector such that J = cu*u. This is the cost for one particular set of potentially 
% time-varying costParameters. The parameters that have to be passed must be in the form 
% costParameters.<EHF_identifier>.<parameters>. Check the documentation to learn which <parameters> are necessary for
% a particular EHF model. 
costParameters = struct();

% costs for AHU
costParameters.AHU1.costPerJouleHeated = 10;
costParameters.AHU1.costPerJouleCooled = 10;
costParameters.AHU1.costPerKgAirTransported = 1;
costParameters.AHU1.costPerKgCooledByEvapCooler = 10;
costParameters.Rad.costPerJouleHeated = 10;
cu = B.building_model.getCostVector(costParameters);

% set up simulation environment in order to get indices for all the control
% inputs
SimExp = SimulationExperiment(B);
% SimExp.printIdentifiers();
identifiers = SimExp.getIdentifiers();
len_v = length(identifiers.v);
len_u = length(identifiers.u);
len_x = length(identifiers.x);

%% export model
export_model = 0;
if export_model==1
    % Add this to the end of your MATLAB script
    save_path = fullfile(LocalPath, 'building_plant_data.mat');
    time_posix = posixtime(dt); 

    % Save dynamics matrices
    % Note: Python will read these matrices. 
    % Bvu and Bxu are 3D arrays (bilinear terms).
    save(save_path, 'A_cont', 'Bu_cont', 'Bv_cont', 'Bvu_cont', 'Bxu_cont', ...
         'Tamb', 'SolRad', 'Ts_hrs', 'time_posix', 'identifiers', '-v7');

    fprintf('Model data exported to %s\n', save_path);
end

%% Collect relevant identifiers (inputs, disturbances, states of the rooms)

% inputs
idx_u_AHU_n = getIdIndex('u_AHU1_noERC',identifiers.u); % this one contributes to the bilinear term
idx_u_AHU_h = getIdIndex('u_AHU1_heater',identifiers.u);
idx_u_AHU_c = getIdIndex('u_AHU1_cooler',identifiers.u);

% the ith radiator does indeed correspond to the ith room (zone)
idx_u_rad_1 = getIdIndex('u_rad_Radiator1',identifiers.u);
idx_u_rad_2 = getIdIndex('u_rad_Radiator2',identifiers.u);
idx_u_rad_3 = getIdIndex('u_rad_Radiator3',identifiers.u);
idx_u_rad_4 = getIdIndex('u_rad_Radiator4',identifiers.u);
idx_u_rad_5 = getIdIndex('u_rad_Radiator5',identifiers.u);

% disturbances
    %ambient temps
idx_v_Tamb = getIdIndex('v_Tamb',identifiers.v); % this also contributes to the bilinear term
idx_v_Tgnd = getIdIndex('v_Tgnd',identifiers.v);

    %internal heat gains (people)
idx_v_IGZ1 = getIdIndex('v_IG_ZoneOne',identifiers.v);
idx_v_IGZ2 = getIdIndex('v_IG_ZoneTwo',identifiers.v);
idx_v_IGZ3 = getIdIndex('v_IG_ZoneThree',identifiers.v);
idx_v_IGZ4 = getIdIndex('v_IG_ZoneFour',identifiers.v);
idx_v_IGZ5 = getIdIndex('v_IG_ZoneFive',identifiers.v);

    %solar heat gains
idx_v_SolE = getIdIndex('v_solGlobFac_E',identifiers.v);
idx_v_SolN = getIdIndex('v_solGlobFac_N',identifiers.v);
idx_v_SolS = getIdIndex('v_solGlobFac_S',identifiers.v);
% idx_v_SolW = getIdIndex('v_solGlobFac_W',identifiers.v); % somehow this
% doesn't exist

% rooms
idx_x_room1 = getIdIndex('x_Z0001',identifiers.x);
idx_x_room2 = getIdIndex('x_Z0002',identifiers.x);
idx_x_room3 = getIdIndex('x_Z0003',identifiers.x);
idx_x_room4 = getIdIndex('x_Z0004',identifiers.x);
idx_x_room5 = getIdIndex('x_Z0005',identifiers.x);

% make index vectors
room_vec = [idx_x_room1, idx_x_room2, idx_x_room3, idx_x_room4, idx_x_room5];
dist_vec = [idx_v_Tamb];
u_rad_vec = [idx_u_rad_1, idx_u_rad_2, idx_u_rad_3, idx_u_rad_4, idx_u_rad_5];
u_ahu_vec = [idx_u_AHU_n, idx_u_AHU_h, idx_u_AHU_c];

%% Check model

check_time_constants = 0;
if check_time_constants == 1
    [V, D] = eig(A_disc);
    eig_A = diag(D);
    tau_discrete = -Ts_hrs ./ log(abs(eig_A));

    % For each room state, find which eigenmode dominates
    for i = 1:length(room_vec)
        room_idx = room_vec(i);
        % Find which eigenvector has largest component for this room
        [~, dominant_mode] = max(abs(V(room_idx, :)));
        room_time_constant(i) = tau_discrete(dominant_mode);
        fprintf('Room %d (x_%d): tau = %.4f hours\n', i, room_idx, room_time_constant(i));
    end
    
    % After checking eigenvalues
    if any(abs(eig_A) >= 1.0)
        warning('Unstable discretization detected!');
        fprintf('Max eigenvalue magnitude: %.4f\n', max(abs(eig_A)));
    end
end


%% internal heat gain parameters

% watts per human
% wph = 100;
wph = 0;
% nPeople = 15;
nPeople = 0;
% area of rooms
a1 = 84;
a2 = 84;
a3 = 84;
a4 = 132;
a5 = 36;

ihg_vec = [idx_v_IGZ1, idx_v_IGZ2, idx_v_IGZ3, idx_v_IGZ4, idx_v_IGZ5];

ihg_area(idx_v_IGZ1) = a1;
ihg_area(idx_v_IGZ2) = a2;
ihg_area(idx_v_IGZ3) = a3;
ihg_area(idx_v_IGZ4) = a4;
ihg_area(idx_v_IGZ5) = a5;

% the unit of disturbance is W/m^2, so we have to weight by the area of
% room

load('ihg_model.mat');
t_space_dist = internalHeatGain.t_space_dist;
p_array = internalHeatGain.p_array;

%% Simulation with Hysteresis Control loop

% loop over temperature margin values
for T_margin = 2 
    % initial conditions
    x = 20*ones(len_x,1);  % Warmer default
    %x_hys(room_vec) = 20;       % Room air at setpoint
    v = zeros(len_v,1);
    u_full = zeros(len_u,1);

    % time-dependent disturbances
    % sim_duration_hrs = 100 * 24;
    % t_space = 0:Ts_hrs:sim_duration_hrs; % timespace in hours

    t_space = (0:length(dt)-1) * Ts_hrs;
    % Before simulation loop, create aligned Tamb arraydd
    Tamb = Tamb(1:length(t_space));
    v_gnd = 10; % constant ground temp

    % state constraints
    xcon_array_min = zeros(length(room_vec), length(t_space));
    xcon_array_max = zeros(length(room_vec), length(t_space));
    % internal heat gain
    ihg_array = zeros(length(room_vec), length(t_space));
    temp_array = zeros(1,length(t_space));

    % array and vectors for thermostat, as well as hysteresis params
    x_array = zeros(len_x, length(t_space));
    u_array = zeros(len_u, length(t_space));
    v_array = zeros(len_v,length(t_space));

    % this is used to create the prbs signal for PRBS and HysteresisPRBS case
    u_prbs_array = zeros(len_u, length(t_space));
    u_prbs_array(idx_u_rad_1, :) = prbs(n_timeSteps, u_max_areas(1), 0, Ts_hrs);
    u_prbs_array(idx_u_rad_2, :) = prbs(n_timeSteps, u_max_areas(2), 0, Ts_hrs);
    u_prbs_array(idx_u_rad_3, :) = prbs(n_timeSteps, u_max_areas(3), 0, Ts_hrs);
    u_prbs_array(idx_u_rad_4, :) = prbs(n_timeSteps, u_max_areas(4), 0, Ts_hrs);
    u_prbs_array(idx_u_rad_5, :) = prbs(n_timeSteps, u_max_areas(5), 0, Ts_hrs);

    for ii = 1:length(t_space)
        if mod(ii, 10000) == 0
            fprintf('Step %d/%d (%.1f%%)\n', ii, n_timeSteps, 100*ii/n_timeSteps);
        end

        % reset disturbance vector
        v = zeros(len_v,1);

        % set state constraints and record them
        xCon = setConstraints(room_vec, t_space(ii), T_margin);
        for jj = 1:length(room_vec)
            ind = room_vec(jj);
            xcon_array_min(jj,ii) = xCon.T_min(ind);
            xcon_array_max(jj,ii) = xCon.T_max(ind);
        end

        % get hysteresis values for AHU
        h_setpoint = 0.5*(xCon.T_min(ind) + xCon.T_max(ind));
        c_setpoint = 0.5*(xCon.T_min(ind) + xCon.T_max(ind)) + 1;

        % TODO: How is this different from margins for the constraints?
        h_low = h_setpoint - T_margin;
        h_high = h_setpoint + T_margin;

        c_low = c_setpoint - T_margin;
        c_high = c_setpoint + T_margin;

        % get measurable disturbances
        v(idx_v_Tamb) = Tamb(ii);
        v(idx_v_Tgnd) = v_gnd;

         % simple solar irradiation model in W/m^2
    %     v(idx_v_SolS) = max(0, (600*sin(2*pi*t_space(ii)/24 + 3*pi/2)-100)*cos(pi/4));
    %     v(idx_v_SolN) = 0.5 * max(0, (600*sin(2*pi*t_space(ii)/24 + 3*pi/2)-100)*cos(pi/4));
    %     v(idx_v_SolE) = 0.5 * max(0, (600*sin(2*pi*t_space(ii)/24 + 3*pi/2)-100)*cos(pi/4));
        v(idx_v_SolS) = SolRad(ii);
        v(idx_v_SolN) = 0.5 * SolRad(ii);
        v(idx_v_SolE) = 0.5 * SolRad(ii);

        % get hysteresis for AHU - use different parameters
        u_full = getAHU(room_vec, u_ahu_vec, x, u_full, h_low, h_high, c_low, c_high, u_n_max, u_h_max, u_c_max);

        u_AHU_hys = u_full(1:3);

        % hysteresis loop control for radiators
        if u_type == "hysteresis"
            % shape [8x1] 3 AHU + 5 Radiators
            u_rad = getThermo(room_vec, u_rad_vec, x, u_full, h_low, h_high, u_max);
            % reset u_hys so I can add it together with the AHU control
    %       u_hys(1:3) = u_AHU_proj_hys;
            u_full(1:3) = zeros(3,1); 
            u_full(4:len_u) = u_rad(4:len_u);
        elseif u_type == "hysteresis-random"
            current_rbs_values = u_prbs_array(u_rad_vec, ii); 
            % shape [8x1] 3 AHU + 5 Radiators
            u_rad = getHysteresisRBS(room_vec, u_rad_vec, x, u_full, h_low, h_high, u_max, current_rbs_values);
            % reset u_hys so I can add it together with the AHU control
    %       u_hys(1:3) = u_AHU_proj_hys;
            u_full(1:3) = zeros(3,1); 
            u_full(4:len_u) = u_rad(4:len_u);
        elseif u_type == "random"
            u_rad = u_prbs_array(:,ii);
            u_full(1:3) = zeros(3,1); 
            u_full(4:len_u) = u_rad(4:len_u);
        end

        if u_full(idx_u_AHU_n) > 1
            keyboard
        end

        % get unmeasurable disturbances    
        [v_ihg, ihg] = getIHG(ihg_vec, ihg_area, wph, t_space_dist, p_array, t_space(ii), nPeople, len_v);

        v = v + v_ihg; % should be complementary

        vec_bl_hys = zeros(size(x));

        for jj = 1:len_u
            vec_bl_hys = vec_bl_hys + (Bvu_disc(:,:,jj)*v + Bxu_disc(:,:,jj)*x)*u_full(jj);
        end
    %     fprintf("%f\n", sum(vec_bl_hys,'all'))

        % store values in data array
        x_array(:,ii) = x;

        % propagate discrete dynamics
        x = A_disc*x + Bu_disc*u_full + Bv_disc*v + vec_bl_hys;

        u_array(:,ii) = u_full;
        ihg_array(:,ii) = ihg;
        temp_array(:,ii) = v(idx_v_Tamb);
        v_array(:,ii) = v;

    end

    rad_idx = idx_u_rad_1:1:len_u;
    rad_inputs = u_array(rad_idx,:);

    %% Plot intermediate results

    plot_intermediate = 0;
    legend_fontsize = 10;
    start_days = 30;
    start_idx = start_days*24/Ts_hrs;
    hours_plot_length = 1*24;
    plot_length = hours_plot_length/Ts_hrs; % One week
    end_idx = min(start_idx + plot_length - 1, length(dt));
    time_range = start_idx:end_idx;
    plot_time = dt(time_range);
    room_temps = x_array(room_vec,:);

    if plot_intermediate == 1
        fig = figure('Name', 'PRBS - All Rooms', ...
               'Color', 'white', ...
               'Position', [100, 100, 1500, 1200]);

        sgtitle(sprintf('RBS with Hysteresis Backup Control'), 'FontSize', 14, 'FontWeight', 'bold');
    %     sgtitle(sprintf('PRBS Control (Samples %d to %d)', ...
    %         start_idx, end_idx), 'FontSize', 14, 'FontWeight', 'bold');

        % Preallocate axes handle array
        ax = gobjects(1, 5);
    %     ax = gobjects(1, 6);

        ax(1) =subplot(6, 1, 1);
        plot(plot_time, temp_array(time_range), 'g', 'LineWidth', 2);
        ylabel('Temperature (°C)');

        % Right Y-Axis for Solar Radiation
        yyaxis right;
        plot(plot_time, v_array(idx_v_SolS, time_range), '--','Color', [1 0.5 0],'linewidth',2)
        ylabel('Total Solar Radiation (W/m²)');
        set(gca, 'YColor', 'r');
    %     ylim([0 u_max+10]);

        legend('Ambient Temperature','Solar Irradiation', 'Location', 'NorthWest','Fontsize',legend_fontsize);
        grid on;
        title('Disturbances', 'FontWeight', 'normal');
%         xlabel('Time');
        xlim([plot_time(1) plot_time(end)])


        for room_idx = 1:5
            ax(room_idx) = subplot(6, 1, room_idx+1);

            % Left Y-Axis for Temperatures
            yyaxis left;
            plot(plot_time, room_temps(room_idx, time_range), 'b-', 'LineWidth', 1.5); hold on;
            stairs(plot_time, xcon_array_min(room_idx, time_range), 'b:', 'LineWidth', 1.5);
            stairs(plot_time, xcon_array_max(room_idx, time_range), 'r:', 'LineWidth', 1.5);
    %         plot(plot_time, temp_array(time_range), 'g--', 'LineWidth', 2);
            ylabel('Temperature (°C)');
            set(gca, 'YColor', 'b');
            ylim([5 30]);

            % Right Y-Axis for Heat Input
            yyaxis right;
            stairs(plot_time, rad_inputs(room_idx, time_range), 'r-', 'LineWidth', 1.5);
            ylabel('Heat Input (W/m²)');
            set(gca, 'YColor', 'r');
            ylim([0 u_max+10]);

            grid on;
            title(['Room ', num2str(room_idx)], 'FontWeight', 'normal');
%             xlabel('Time');

            if room_idx == 1
                legend('Room Temp', '$T_{min}$', '$T_{max}$', ...
                       'Radiator Input', 'Location', 'NorthWest','Fontsize',legend_fontsize);
            end
        end

        % Link x-axis zoom/pan across all subplots
        linkaxes(ax, 'x');
        set(ax, 'XLim', [plot_time(1) plot_time(end)])

        % 2. Save the figure
        filename = ['Hysteresis_PRBS_Control', num2str(Ts_hrs), '_', char(u_type),'_Tmargin_',num2str(T_margin),'.pdf'];
        exportgraphics(fig, filename, 'ContentType', 'vector')
    end
    close all

    %% plot data
    plot_data = 0;
    if plot_data == 1

        % ambient temp - disturbance 2
        h6 = figure;
        set(h6, 'position', [675 669 570 159]);
        plot(t_space, temp_array','linewidth',2)
        xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
        ylabel('Ambient Temp [$^\cdot$C]','interpreter','latex','fontsize',14)

        % solar model - disturbance 3
        h65 = figure;
        set(h65, 'position', [675 669 570 159]);
        plot(t_space, v_array(idx_v_SolN,:) ,'linewidth',2), hold on
        plot(t_space, v_array(idx_v_SolE,:) ,'linewidth',2)
        xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
        ylabel('Solar Irradiation [W/m$^2$]','interpreter','latex','fontsize',14)
        legend('North','East')

        % room temps - hysteresis
        h7 = figure;
        set(h7, 'position', [675 669 570 159]);
        plot(t_space, room_temps), hold on
        plot(t_space, xcon_array_min(1,:),'k--')
        plot(t_space, xcon_array_max(1,:),'k--')
        ylabel('Room Temp [$^\cdot$C]','interpreter','latex','fontsize',14)
        xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
        xlim([t_space(1) t_space(end)]);
        ylim([15 30]);
        legend('Rm1','Rm2','Rm3','Rm4','Rm5')

        % controls - radiatiors hysteresis
        h8 = figure;
        set(h8, 'position', [675 669 570 159]);

        plot(t_space, rad_inputs,'linewidth',2), hold on
        rad_ub = constraintsParameters.Rad.Q_rad_Radiator1_max;
        plot(t_space, rad_ub*ones(size(t_space)),'--k')
        legend('Rad1','Rad2','Rad3','Rad4','Rad5')
        xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
        ylabel('Radiator [W/m$^2$]','interpreter','latex','fontsize',14)
        xlim([t_space(1) t_space(end)]);
        ylim([0 60]);
    end


    %% Plot ambient temperature

    % % ---- Slice settings
    slice_start_hours = 500;
    slice_start_idx = round(slice_start_hours / Ts_hrs);
    % 
    % usable_data_length = length(dt) - slice_start_idx;
    % train_ratio = 0.10;
    % val_ratio   = 0.05;
    % test_ratio  = 0.10;
    % 
    % train_slice_length = int64(usable_data_length * train_ratio);
    % train_slice_end_idx = slice_start_idx + train_slice_length;
    % 
    % val_slice_length = int64(usable_data_length * val_ratio);
    % val_slice_end_idx = train_slice_end_idx + val_slice_length;
    % 
    % test_slice_length = int64(usable_data_length * test_ratio);
    % test_slice_end_idx = val_slice_end_idx + test_slice_length;
    % 
    % % ---- Time markers
    % t_start = dt(slice_start_idx);
    % t_train_end = dt(train_slice_end_idx);
    % t_val_end   = dt(val_slice_end_idx);
    % t_test_end  = dt(test_slice_end_idx);
    % 
    % % ---- Data window
    % idx = slice_start_idx:test_slice_end_idx;
    % dt_plot     = dt(idx);
    % Tamb_plot   = Tamb(idx);
    % SolRad_plot = SolRad(idx);
    % 
    % % ---- Figure
    % h9 = figure('Color','w', ...
    %             'Units','centimeters', ...
    %             'Position',[2 2 24 12]);
    % 
    % tl = tiledlayout(2,1,'TileSpacing','compact','Padding','compact');
    % 
    % % ---- Top subplot: Solar radiation
    % ax1 = nexttile;
    % plot(ax1, dt_plot, SolRad_plot, ...
    %     'Color',[0.85 0.33 0.10], ...
    %     'LineWidth',1.4);
    % hold(ax1,'on')
    % % xline(ax1, t_start,     '--k', 'LineWidth',2);
    % xline(ax1, t_train_end, '--k', 'LineWidth',2);
    % xline(ax1, t_val_end,   '--k', 'LineWidth',2);
    % % xline(ax1, t_test_end,  '--k', 'LineWidth',2);
    % hold(ax1,'off')
    % 
    % ylabel(ax1,'Solar radiation [W/m$^2$]', ...
    %     'Interpreter','latex','FontSize',12)
    % title(ax1,'Solar Radiation and Ambient Temperature -- Rotterdam Airport 2021', ...
    %     'Interpreter','latex','FontSize',13,'FontWeight','bold')
    % 
    % ax1.FontName = 'Times';
    % ax1.FontSize = 11;
    % ax1.LineWidth = 1.0;
    % ax1.Box = 'on';
    % ax1.TickLabelInterpreter = 'latex';
    % grid(ax1,'on')
    % ax1.GridAlpha = 0.12;
    % ax1.MinorGridAlpha = 0.08;
    % ax1.XTickLabel = [];   % hide top x tick labels
    % 
    % % ---- Bottom subplot: Ambient temperature
    % ax2 = nexttile;
    % plot(ax2, dt_plot, Tamb_plot, ...
    %     'Color',[0 0.45 0.74], ...
    %     'LineWidth',1.4);
    % hold(ax2,'on')
    % % xline(ax2, t_start,     '--k', 'LineWidth',1.2);
    % xline(ax2, t_train_end, '--k', 'LineWidth',2);
    % xline(ax2, t_val_end,   '--k', 'LineWidth',2);
    % % xline(ax2, t_test_end,  '--r', 'LineWidth',1.2);
    % hold(ax2,'off')
    % 
    % ylabel(ax2,'Temperature [$^\circ$C]', ...
    %     'Interpreter','latex','FontSize',12)
    % % xlabel(ax2,'Time', ...
    % %     'Interpreter','latex','FontSize',12)
    % 
    % ax2.FontName = 'Times';
    % ax2.FontSize = 11;
    % ax2.LineWidth = 1.0;
    % ax2.Box = 'on';
    % ax2.TickLabelInterpreter = 'latex';
    % grid(ax2,'on')
    % ax2.GridAlpha = 0.12;
    % ax2.MinorGridAlpha = 0.08;
    % 
    % % ---- Shared formatting
    % linkaxes([ax1, ax2],'x')
    % xlim(ax1,[dt_plot(1) dt_plot(end)])
    % 
    % % ---- Section labels centered in each interval on BOTH subplots
    % section_edges = [t_start, t_train_end, t_val_end, t_test_end];
    % section_names = {'Training', 'Validation', 'Test'};
    % 
    % for ax = [ax1, ax2]
    %     yl = ylim(ax);
    %     y_text = yl(2) - 0.08*(yl(2)-yl(1));
    % 
    %     for k = 1:numel(section_names)
    %         t_mid = section_edges(k) + (section_edges(k+1) - section_edges(k))/2;
    %         x_text = ruler2num(t_mid, ax.XAxis);
    % 
    %         text(ax, x_text, y_text, section_names{k}, ...
    %             'Interpreter', 'latex', ...
    %             'HorizontalAlignment', 'center', ...
    %             'VerticalAlignment', 'top', ...
    %             'FontSize', 11, ...
    %             'FontWeight', 'bold', ...
    %             'Color', [0.25 0.25 0.25], ...
    %             'BackgroundColor', 'w', ...
    %             'Margin', 2);
    %     end
    % end
    % 
    % % Set limits explicitly
    % xlim(ax2, [dt_plot(1) dt_plot(end)])
    % 
    % % Choose a regular tick spacing
    % tick_main = dateshift(dt_plot(1), 'start', 'day'):caldays(7):dateshift(dt_plot(end), 'start', 'day');
    % 
    % % Force inclusion of start and end of the plotted interval
    % tick_all = unique([dt_plot(1), tick_main]);
    % 
    % % Apply to both subplots
    % xticks(ax1, tick_all)
    % xticks(ax2, tick_all)
    % 
    % % Optional: cleaner date formatting
    % xtickformat(ax2, 'dd-MMM')
    % xtickformat(ax1, 'dd-MMM')
    % % ---- Export
    % exportgraphics(h9, 'ambient_solar_publication.pdf', 'ContentType', 'vector')

    %% Plot Zone Mean Air Temperatures - Training Set (Subplots)
    % h10 = figure;
    % set(h10, 'position', [100 100 1800 1200]);
    % 
    % % Define training slice indices
    % train_start_idx = slice_start_idx;
    % train_end_idx = slice_start_idx + train_slice_length;
    % 
    % % Extract training data
    % dt_train = dt(train_start_idx:train_end_idx);
    % room_temps_train = room_temps(:, train_start_idx:train_end_idx);
    % 
    % % Create tiled layout
    % tiledlayout(5, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
    % 
    % % Plot each zone in its own subplot
    % for i = 1:5
    %     nexttile
    %     plot(dt_train, room_temps_train(i, :))
    %     xlim tight
    %     ylabel('Temp [$^\circ$C]', 'interpreter', 'latex', 'fontsize', 12)
    %     title(['Zone ', num2str(i)])
    %     grid on
    % end
    % 
    % % Add overall title
    % sgtitle('Zone Mean Air Temperatures - Training Set', 'fontsize', 14)
    % 
    % filename = ["zone_temps_training_subplots", num2str(Ts_hrs), '_', char(u_type),'_Tmargin_',num2str(T_margin),'.png'];
    % exportgraphics(h10, filname, 'Resolution', 300)

    %% Plot Zone Mean Air Temperatures - Discarded Set (Subplots)
    % h11 = figure;
    % set(h11, 'position', [100 100 1800 1200]);
    % 
    % discard_end_idx = slice_start_idx;
    % % Extract training data
    % dt_discard = dt(1:discard_end_idx);
    % room_temps_discard = room_temps(:, 1:discard_end_idx);
    % 
    % % Create tiled layout
    % tiledlayout(5, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
    % 
    % % Plot each zone in its own subplot
    % for i = 1:5
    %     nexttile
    %     plot(dt_discard, room_temps_discard(i, :))
    %     xlim tight
    %     ylabel('Temp [$^\circ$C]', 'interpreter', 'latex', 'fontsize', 12)
    %     title(['Zone ', num2str(i)])
    %     grid on
    % end
    % 
    % % Add overall title
    % sgtitle('Zone Mean Air Temperatures - Discarded Set', 'fontsize', 14)
    % 
    % filename = ["zone_temps_discarded_subplots", num2str(Ts_hrs), '_', char(u_type),'_Tmargin_',num2str(T_margin),'.png'];
    % exportgraphics(h11, filename, 'Resolution', 300)
% 
% 
    %% Write data to CSV

    write_file = 1;

    if write_file
        data_dir = '../../../data/brcm_simulation_results/hysteresis_prbs/';
        first_csv_filename_part = 'five_room_1_year_Ts_';
        filename_only = [first_csv_filename_part, num2str(Ts_hrs), '_', char(u_type),'_Tmargin_',num2str(T_margin),'_real.csv'];
        brcm_csv_filename = fullfile(data_dir, filename_only);
        %brcm_csv_filename = [data_dir, first_csv_filename_part, num2str(Ts_hrs), '_', u_type, '_real.csv'];

        headers = {'Datetime','ZoneMeanAirTemperature 1', 'ZoneMeanAirTemperature 2', 'ZoneMeanAirTemperature 3', 'ZoneMeanAirTemperature 4', 'ZoneMeanAirTemperature 5', 'Environment', 'HeatInput 1', 'HeatInput 2', 'HeatInput 3', 'HeatInput 4', 'HeatInput 5','Total Solar Radiation'};

        % T = array2table([dt room_temps, t_amb, rad_inputs], 'VariableNames', headers);
        % T = table(dt, room_temps, t_amb, rad_inputs, 'VariableNames', headers);
        abs_rad_inputs = rad_inputs .* zone_areas'; 
        T = array2table([room_temps', Tamb, abs_rad_inputs',SolRad], 'VariableNames', headers(2:end));
        T = addvars(T, dt, 'Before', 1, 'NewVariableNames', headers{1});

        sliced_T = T(slice_start_idx:end, :);
        writetable(sliced_T, brcm_csv_filename);
    end
 end

%% plot Zone Mean Air Temperatures at the over the training set

%% --- helpers ---
function tightAxes(ax)
    drawnow;  % update TightInset after labels/view changes

    ax.Units = 'normalized';
    ti = ax.TightInset;      % [left bottom right top]

    pad = 0.01;              % tiny safety padding
    left   = ti(1) + pad;
    bottom = ti(2) + pad;
    width  = 1 - ti(1) - ti(3) - 2*pad;
    height = 1 - ti(2) - ti(4) - 2*pad;

    width  = max(width,  0.01);
    height = max(height, 0.01);

    ax.Position = [left, bottom, width, height];
end

function exportPdf(fig, filename, wCm, hCm)
    fig.Color = 'w';
    fig.Units = 'centimeters';

    pos = fig.Position;
    fig.Position = [pos(1), pos(2), wCm, hCm];

    fig.PaperUnits = 'centimeters';
    fig.PaperSize = [wCm, hCm];
    fig.PaperPosition = [0, 0, wCm, hCm];

    print(fig, filename, '-dpdf', '-painters');
end