%% Rigorous System Identification & Benchmarking for EMPC
clear; clc; close all;

% --- 1. Configuration & Data Loading ---
load('../../data/system_id_data.mat'); % u_train, y_train, u_val, y_val, Ts
FileName = 'onezone_2R2C';   % ODE file
Ts = double(Ts);   % in minutes, consistent with iddata below

K_horizon = 96;    % still available for later comparison

% --- 2. Build 1-zone iddata objects from existing splits ---

zone_idx   = 1;  % choose which zone to model
heater_idx = 1;  % assume heater 1 corresponds to zone 1

% Outputs: single zone temperature
y_train_1 = y_train(:, zone_idx);
y_val_1   = y_val(:,   zone_idx);

% Inputs: [Q_heat_zone1, T_amb, Q_solar]
% Adapt column indices to your actual u layout:
Qh_train = u_train(:, heater_idx);
Qh_val   = u_val(:,   heater_idx);

Tamb_train = u_train(:, end-1);   % e.g. second-to-last column
Tamb_val   = u_val(:,   end-1);

Qsol_train = u_train(:, end);     % last column
Qsol_val   = u_val(:,   end);

u_train_1 = [Qh_train, Tamb_train, Qsol_train];
u_val_1   = [Qh_val,   Tamb_val,   Qsol_val];

Order    = [1 3 2];
Ts_model = 0;

ze = iddata(y_train_1, u_train_1, Ts, ...
    'Name', '1-zone room train', ...
    'TimeUnit', 'minutes', ...
    'InterSample', {'zoh'; 'zoh'; 'zoh'});

zv = iddata(y_val_1, u_val_1, Ts, ...
    'Name', '1-zone room val', ...
    'TimeUnit', 'minutes', ...
    'InterSample', {'zoh'; 'zoh'; 'zoh'});



% Optional: for continuous-time ODE with 15-min samples, specify intersample:
% ze.InterSample = 'zoh';
% zv.InterSample = 'zoh';

%% 3. Define initial grey-box model (2 states, 3 inputs, 1 output)


Parameters = [
    1e5;   % C_air
    5e5;   % C_mass
    0.5;   % R_outside room_air
    0.1;   % R_air mass
    0.8;   % alpha_h
    0.2    % alpha_s
];

x0 = [y_train_1(1); y_train_1(1)];

init_sys = idnlgrey(FileName, Order, Parameters, x0, Ts_model, ...
    'Name', '1-zone 2R2C');
init_sys.Parameters(1).Minimum = 1e3;
init_sys.Parameters(2).Minimum = 1e4;
init_sys.Parameters(3).Minimum = 1e-3;
init_sys.Parameters(4).Minimum = 1e-3;

%% 4. Estimate on training data

opt = nlgreyestOptions;
opt.Display = 'on';
opt.SearchOptions.MaxIterations = 50;

sys_est = nlgreyest(ze, init_sys, opt);

%% 5. Inspect fit on train and validation

figure;
compare(ze, sys_est);  title('Training fit: 1-zone 2R2C');

figure;
compare(zv, sys_est);  title('Validation fit: 1-zone 2R2C');