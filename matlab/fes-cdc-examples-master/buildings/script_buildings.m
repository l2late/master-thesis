%     This program compares FES to a hysteresis controller on a building
%     automation example. It has been developed by modifying the example
%     code that comes with the BRCM toolbox.
%
%     Copyright (C) 2021  Mathias Hudoba de Badyn
% 
%     This program is free software: you can redistribute it and/or modify
%     it under the terms of the GNU General Public License as published by
%     the Free Software Foundation, either version 3 of the License, or
%     (at your option) any later version.
% 
%     This program is distributed in the hope that it will be useful,
%     but WITHOUT ANY WARRANTY; without even the implied warranty of
%     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%     GNU General Public License for more details.

clc; close all; clear all;

rng(1337)

print_figs = 0;

set(groot, 'defaultAxesTickLabelInterpreter','latex'); 
set(groot, 'defaultLegendInterpreter','latex');


LocalPath = pwd;

addpath(genpath('./fcns'))

buildingType = 'Swissaverage';
demoBuilding = 'SwAvHW80Converted';
% demoBuilding = 'SwTaHW30Converted';

Opti = 'OptiT1'; % OptiT4 does not work. The buildingelements file is incorrect, likely needs to be replaced with the ones from t1. this doesn't make sense to me

thermalModelDataDir =   [LocalPath,filesep,'OptiT1',filesep','Swissaverage',filesep,demoBuilding,filesep,'ThermalModel'];
EHFModelDataDir =       [LocalPath,filesep,'OptiT1',filesep','Swissaverage',filesep,demoBuilding,filesep,'EHFM'];

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
EHFModelClassFile = 'BEHeatfluxes.m'; 
EHFModelDataFile = [EHFModelDataDir,filesep,'BEHeatfluxes']; 
EHFModelIdentifier = 'TABS';
B.declareEHFModel(EHFModelClassFile,EHFModelDataFile,EHFModelIdentifier);

% Radiators
EHFModelClassFile = 'Radiators.m'; 
EHFModelDataFile = [EHFModelDataDir,filesep,'radiators']; 
EHFModelIdentifier = 'Rad';
B.declareEHFModel(EHFModelClassFile,EHFModelDataFile,EHFModelIdentifier);

%% --------------------------------------------------------------------------------------
% 4) Display thermal model data to Command Window and draw Building (optional) 
% --------------------------------------------------------------------------------------

% Print the thermal model data in the Command Window for an overview
% B.printThermalModelData;

% 3-D plot of Building with increased font size for plots
% B.drawBuilding;
% 
% zlabel('z [m]','interpreter','latex','fontsize',40)
% xlabel('East','interpreter','latex','fontsize',40)
% ylabel('North','interpreter','latex','fontsize',40)
% ax = gca;
% ax.FontSize = 35;

%% --------------------------------------------------------------------------------------
% 5) Generate thermal model and full model
% --------------------------------------------------------------------------------------

% Generate thermal model (optional)
B.generateThermalModel;

% Generate (full) building model (includes thermal model generation if not yet done)
B.generateBuildingModel;

% Display all available identifiers (these are the names of the control inputs / disturbances / states in the same order as they appear in the matrices)
B.building_model.printIdentifiers;

% Disretization
Ts_hrs = 0.05; % in units of hours
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

[~,~,nu] = size(Bvu_disc);

% Get constraint matrices such that % Fx*x+Fu*u+Fv*v <= g. These are the constraints for one particular set of potentially 
% time-varying constraintsParameters. Every row of the matrices represents one constraint the name of which is the 
% corresponding entry in constraint_identifiers. The parameters that have to be passed must be in the form 
% constraintsParameters.<EHF_identifier>.<parameters>. Check the documentation to learn which <parameters> are necessary for
% a particular EHF model.


constraintsParameters = struct();

u_n_max = 1;
u_h_max = 1000;
u_c_max = 100;

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


u_max = 50; %original was 50

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

% If the building_model B.building_model should be saved to use the model in another place, it is necessary that the Classes folder 
% is on the path, otherwise the saved data can not be loaded correctly. If only the matrices are needed, then just 
% the B.building_model.discrete_time_model should be saved and the Classes folder is not necessary.


% set up simulation environment in order to get indices for all the control
% inputs
SimExp = SimulationExperiment(B);
SimExp.printIdentifiers();
identifiers = SimExp.getIdentifiers();
len_v = length(identifiers.v);
len_u = length(identifiers.u);
len_x = length(identifiers.x);

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

% rooms
idx_x_room1 = getIdIndex('x_Z0001',identifiers.x);
idx_x_room2 = getIdIndex('x_Z0002',identifiers.x);
idx_x_room3 = getIdIndex('x_Z0003',identifiers.x);
idx_x_room4 = getIdIndex('x_Z0004',identifiers.x);
idx_x_room5 = getIdIndex('x_Z0005',identifiers.x);

% set constraints on rooms

room_vec = [idx_x_room1, idx_x_room2, idx_x_room3, idx_x_room4, idx_x_room5];
dist_vec = [idx_v_Tamb];
u_rad_vec = [idx_u_rad_1, idx_u_rad_2, idx_u_rad_3, idx_u_rad_4, idx_u_rad_5];
u_ahu_vec = [idx_u_AHU_n, idx_u_AHU_h, idx_u_AHU_c];


%% internal heat gain parameters

% watts per human
wph = 100;

nPeople = 15;

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


%% Feedback Optimization

% cost is 1/2 u'*H*u + cu*u + 0.5*sum max(0, Tmin-x,x-Tmax)^2

H = 0.1*diag(cu);
h = cu;
A = A_cont;
Bu = Bu_cont;
Bv = Bv_cont;
Bxu = Bxu_cont;
Bvu = Bvu_cont;

% initial conditions and alg params

x = 15*ones(len_x,1);
v = zeros(len_v,1);
u = zeros(len_u,1);

alp = 1E-4; %learning rate
eta = 500000; %state cost

% time-dependent disturbances
t_space = 0:Ts_hrs:96; % timespace in hours
v_gnd = 10; % constant ground temp

x_array = zeros(len_x, length(t_space));
u_array = zeros(len_u, length(t_space));
xcon_array_min = zeros(length(room_vec), length(t_space));
xcon_array_max = zeros(length(room_vec), length(t_space));
ihg_array = zeros(length(room_vec), length(t_space));
temp_array = zeros(length(t_space));

% array and vectors for thermostat, as well as hysteresis params
x_hys_array = zeros(size(x_array));
u_hys_array = zeros(len_u, length(t_space));
v_array = zeros(len_v,length(t_space));

x_hys = x;
u_hys = zeros(len_u,1);

% hysteresis values are set as a function of constraints

% % keep temp about 20
% h_low = 18;
% h_high = 22;
% 
% % turn cooler on at 25
% c_low = 22;
% c_high = 25;

options =  optimset('Display','off');

for ii = 1:length(t_space)
    
    fprintf('iteration %i\n',ii)
    
    % reset disturbance vector
    v = zeros(len_v,1);
    
    % set state constraints and record them
    
    xCon = setConstraints(room_vec, t_space(ii));
    for jj = 1:length(room_vec)
        ind = room_vec(jj);
        xcon_array_min(jj,ii) = xCon.T_min(ind);
        xcon_array_max(jj,ii) = xCon.T_max(ind);
    end
    
    % get hysteresis values for AHU
    
    h_setpoint = 0.5*(xCon.T_min(ind) + xCon.T_max(ind)) - 1;
    c_setpoint = 0.5*(xCon.T_min(ind) + xCon.T_max(ind)) + 1;
    
    h_low = h_setpoint - 1;
    h_high = h_setpoint + 1;
    
    c_low = c_setpoint - 1;
    c_high = c_setpoint + 1;
    
        
    % get measurable disturbances
    
    v(idx_v_Tamb) = 5*sin(2*pi*t_space(ii)/24 + 3*pi/2) + 15;
    v(idx_v_Tgnd) = v_gnd;
    
    
    % simple solar irradiation model in W/m^2
    v(idx_v_SolN) = max(0, (600*sin(2*pi*t_space(ii)/24 + 3*pi/2)-100)*cos(pi/4));
    v(idx_v_SolE) = max(0, (600*sin(2*pi*t_space(ii)/24 + 3*pi/2)-100)*cos(pi/4));
    
    % get grad phi

    grad_phi = gradPhi(x,u,v,H,h,room_vec,dist_vec,A,Bu,Bvu,Bxu,xCon,eta);
    
    % update control
    u = u - alp*grad_phi;
    
    % project control onto control set
   
    % project AHU and radiators separately - this makes zero difference
    % than just doing the quadprog projection on everything. oh well.
    
    %hardcode the indices, not easy to do it in general
    % first 9 rows of Fu and g are for the AHU
    
%     if t_space(ii) >=40
%         keyboard
%     end
    
    % get hysteresis for AHU - use different parameters
    u_hys = getAHU(room_vec, u_ahu_vec, x_hys, u_hys, h_low, h_high, c_low, c_high, u_n_max, u_h_max, u_c_max);
    %getAHU(room_vec, u_ahu_vec, x, u, h_low, h_high, c_low, c_high, u_n_max, u_h_max, u_c_max)
    
    
    Fu_AHU = Fu(1:9,1:3);
    g_AHU  = g(1:9);
    u_AHU  = u(1:3);
    u_AHU_hys = u_hys(1:3);
    
    Fu_rad = Fu(10:end,4:end);
    g_rad  = g(10:end);
    u_rad  = u(4:end);

    u_rad_proj = infNormProj(Fu_rad,u_rad,g_rad);

    %  x = quadprog(H,f,A,b,Aeq,beq,lb,ub,x0,options);
    u_AHU_proj = quadprog(2*eye(length(u_AHU)),-2*u_AHU,Fu_AHU,g_AHU,[],[],[],[],[],options);
    u_AHU_proj_hys = quadprog(2*eye(length(u_AHU_hys)),-2*u_AHU_hys,Fu_AHU,g_AHU,[],[],[],[],[],options);
    
    % put AHU and radiators back together
    u = [u_AHU_proj; u_rad_proj];
    
    % hysteresis loop control for radiators
    u_hys_rad = getThermo(room_vec, u_rad_vec, x_hys, u_hys, h_low, h_high, u_max);
    
    % reset u_hys so I can add it together with the AHU control
    u_hys(1:3) = u_AHU_proj_hys;
    u_hys(4:len_u) = u_hys_rad(4:len_u);
    
    if u_hys(idx_u_AHU_n) > 1
        keyboard
    end
   
    % get unmeasurable disturbances    
    [v_ihg, ihg] = getIHG(ihg_vec, ihg_area, wph, t_space_dist, p_array, t_space(ii), nPeople, len_v);

    v = v + v_ihg; % should be complementary
    
    vec_bl = zeros(size(x));
    vec_bl_hys = zeros(size(x));
    
    for jj = 1:len_u
        vec_bl = vec_bl + (Bvu_disc(:,:,jj)*v + Bxu_disc(:,:,jj)*x)*u(jj);
        vec_bl_hys = vec_bl_hys + (Bvu_disc(:,:,jj)*v + Bxu_disc(:,:,jj)*x_hys)*u_hys(jj);
    end
    
    % propagate discrete dynamics
    x = A_disc*x + Bu_disc*u + Bv_disc*v + vec_bl;
    x_hys = A_disc*x_hys + Bu_disc*u_hys + Bv_disc*v + vec_bl_hys;
    
    % store values in data array
    x_array(:,ii) = x;
    u_array(:,ii) = u;
    x_hys_array(:,ii) = x_hys;
    u_hys_array(:,ii) = u_hys;
    
    ihg_array(:,ii) = ihg;
    temp_array(:,ii) = v(idx_v_Tamb);
    v_array(:,ii) = v;
      
    
end

%% plot data

% room temps

h1 = figure;
set(h1, 'position', [675 669 570 159]);

for ii = 1:length(room_vec)
    plot(t_space, x_array(room_vec(ii),:),'linewidth',2), hold on
end
plot(t_space, xcon_array_min(1,:),'k--')
plot(t_space, xcon_array_max(1,:),'k--')
ylabel('Room Temp [$^\cdot$C]','interpreter','latex','fontsize',14)
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
xlim([t_space(1) t_space(end)]);
ylim([15 26]);
legend({'Rm1','Rm2','Rm3','Rm4','Rm5'},'location','southeast')

% controls - radiatiors feedback opt
h2 = figure;
set(h2, 'position', [675 669 570 159]);

for ii = idx_u_rad_1:len_u
    plot(t_space, u_array(ii,:),'linewidth',2), hold on
end
rad_ub = constraintsParameters.Rad.Q_rad_Radiator1_max;
plot(t_space, rad_ub*ones(size(t_space)),'--k')
legend('Rad1','Rad2','Rad3','Rad4','Rad5')
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
ylabel('Radiator [W/m$^2$]','interpreter','latex','fontsize',14)
xlim([t_space(1) t_space(end)]);
ylim([0 60]);

% controls - AHU air flow
h3 = figure;
set(h3, 'position', [675 669 570 159]);
plot(t_space, u_array(idx_u_AHU_n,:),'linewidth',2), hold on
xlim([t_space(1) t_space(end)]);
legend('Air Flow','interpreter','latex')
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
ylabel('Air Flow [kg/s]','interpreter','latex','fontsize',14)
ylim([0 1.05])

% controls - AHU heating and cooling
h4 = figure;
set(h4, 'position', [675 669 570 159]);
for ii = idx_u_AHU_c:-1:idx_u_AHU_h
    plot(t_space, u_array(ii,:),'linewidth',2), hold on
end
legend('Cooling Power','Heating Power')
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
ylabel('Power [W/m$^2$]','interpreter','latex','fontsize',14)
xlim([t_space(1) t_space(end)]);
ylim([0 60]);


% internal heat gains - disturbance 1
h5 = figure;
set(h5, 'position', [675 669 570 159]);
for ii = 1:length(room_vec)
    plot(t_space, ihg_array(ii,:)), hold on
end
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
ylabel('IHG [W/m$^2$]','interpreter','latex','fontsize',14)
[~,ind] = min(abs(24-t_space));
xlim([t_space(1) t_space(ind)]);
legend('Rm1','Rm2','Rm3','Rm4','Rm5')

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

for ii = 1:length(room_vec)
    plot(t_space, x_hys_array(room_vec(ii),:)), hold on
end
plot(t_space, xcon_array_min(1,:),'k--')
plot(t_space, xcon_array_max(1,:),'k--')
% plot(t_space, xcon_array_min(1,:),'k--')
% plot(t_space, xcon_array_max(1,:),'k--')
ylabel('Room Temp [$^\cdot$C]','interpreter','latex','fontsize',14)
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
xlim([t_space(1) t_space(end)]);
ylim([15 30]);
legend('Rm1','Rm2','Rm3','Rm4','Rm5')

% controls - radiatiors hysteresis
h8 = figure;
set(h8, 'position', [675 669 570 159]);

for ii = idx_u_rad_1:len_u
    plot(t_space, u_hys_array(ii,:),'linewidth',2), hold on
end
rad_ub = constraintsParameters.Rad.Q_rad_Radiator1_max;
plot(t_space, rad_ub*ones(size(t_space)),'--k')
legend('Rad1','Rad2','Rad3','Rad4','Rad5')
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
ylabel('Radiator [W/m$^2$]','interpreter','latex','fontsize',14)
xlim([t_space(1) t_space(end)]);
ylim([0 60]);

% controls - AHU air flow hysteresis
h9 = figure;
set(h9, 'position', [675 669 570 159]);
plot(t_space, u_hys_array(idx_u_AHU_n,:),'linewidth',2), hold on
xlim([t_space(1) t_space(end)]);
legend('Air Flow','interpreter','latex')
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
ylabel('Air Flow [kg/s]','interpreter','latex','fontsize',14)

% controls - AHU heating and cooling hysteresis
h10 = figure;
set(h10, 'position', [675 669 570 159]);
for ii = idx_u_AHU_c:-1:idx_u_AHU_h
    plot(t_space, u_hys_array(ii,:),'linewidth',2), hold on
end
legend('Cooling Power','Heating Power')
xlabel('Time [Hrs]','interpreter','latex','fontsize',14)
ylabel('Power [W/m$^2$]','interpreter','latex','fontsize',14)
xlim([t_space(1) t_space(end)]);
ylim([0 u_h_max+10]);

%% get costs

% cumulative costs
[fopt_cost,fopt_u_cost] = getCumCost(H,cu,eta,x_array,u_array,xcon_array_min, xcon_array_max, t_space,room_vec);
[hyst_cost,hyst_u_cost] = getCumCost(H,cu,eta,x_hys_array,u_hys_array,xcon_array_min, xcon_array_max, t_space,room_vec);

% cumulative constraint violations per room

cVio_hys = getConstViolation(t_space, x_hys_array, xcon_array_min, xcon_array_max, room_vec)/5;
cVio_opt = getConstViolation(t_space, x_array, xcon_array_min, xcon_array_max, room_vec)/5;

cVio_red = 100*(cVio_opt - cVio_hys)/cVio_hys
cost_red = 100*(fopt_cost  - hyst_cost)/hyst_cost

%% print figures


if print_figs == 1
    print(h1, '-depsc', 'rms.eps')
    print(h2, '-depsc', 'rad.eps')
    print(h3, '-depsc', 'ahu_af.eps')
    print(h4, '-depsc', 'ahu_hc.eps')
    print(h5, '-depsc', 'dist_ihg.eps')
    print(h6, '-depsc', 'dist_temp.eps')
    print(h65, '-depsc', 'dist_solar.eps')
    print(h7, '-depsc', 'rms_hys.eps')
    print(h8, '-depsc', 'rad_hys.eps')
    print(h9, '-depsc', 'ahu_af_hys.eps')
    print(h10, '-depsc', 'ahu_hc_hys.eps')
end
