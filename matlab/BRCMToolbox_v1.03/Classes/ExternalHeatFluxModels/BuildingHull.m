classdef BuildingHull < EHFModelBaseClass
   %BUILDINGHULL 	This class represents the Building Hull external heat flux model of a building.
   % See the documentation for a detailed description of this class
   % ------------------------------------------------------------------------
   % This file is part of the BRCM Toolbox v1.03.
   %
   % The BRCM Toolbox - Building Resistance-Capacitance Modeling for Model Predictive Control.
   % Copyright (C) 2013  Automatic Control Laboratory, ETH Zurich.
   % 
   % The BRCM Toolbox is free software; you can redistribute it and/or modify
   % it under the terms of the GNU General Public License as published by
   % the Free Software Foundation, either version 3 of the License, or
   % (at your option) any later version.
   % 
   % The BRCM Toolbox is distributed in the hope that it will be useful,
   % but WITHOUT ANY WARRANTY; without even the implied warranty of
   % MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   % GNU General Public License for more details.
   % 
   % You should have received a copy of the GNU General Public License
   % along with the BRCM Toolbox.  If not, see <http://www.gnu.org/licenses/>.
   %
   % For support check www.brcm.ethz.ch.
   % ------------------------------------------------------------------------
   
   
   properties(Hidden,Constant)
      
      n_properties@uint64 = uint64(3);        % Number of properties required for object instantation
      multiIncludeOk@logical = false;
      
      % Model specific conventions
      building_hull_name_str@char = 'Building hull';    % name of model
      blind_name_str@char = 'Blind';                    % blind control signal label tag
      solGlobFac_name_str@char = 'SolGlobFac';          % facade solar group signal label tag
      
      % Required file headers for the specific model data file
      windowSpecs_header@cell = {'window_solar_group' 'buildingelement_identifier' 'disturbance_identifier' 'control_identifier' 'secondary_gains_fraction'};
      %         windowSpecs_header@cell = {'window_solar_group' 'buildingelement_identifier' 'disturbance_identifier' 'control_identifier' 'secondary_gains_fraction' 'thermal_resistance [m^2K/W]'};
      facadeSpecs_header@cell = {'facade_solar_group' 'buildingelement_identifier' 'disturbance_identifier' 'absorptance'};
      infiltrationSpecs_header@cell = {'infiltration_specification','zone_identifier','airchangerate'};
      header_be_id_str@char = 'buildingelement_identifier';
      header_u_id_str@char = 'control_identifier';
      header_airchangerate_str@char = 'airchangerate';
      header_zone_id_str@char = 'zone_identifier';
      header_v_id_str@char = 'disturbance_identifier';
      header_secGainsFrac_str@char = 'secondary_gains_fraction';
      header_absorp_str@char = 'absorptance';
      
      solarDisturbanceLabel@char = 'solGlobFac';
      blindsInputLabel@char = 'blinds';
      bposMinConstraintLabel@char = 'blindsMin';
      bposMaxConstraintLabel@char = 'blindsMax';
      
      % properties for constraints generation in order to identify the
      % and find the specific parameter field
      t@char = 't';
      blind_pos_min@char = 'blind_pos_min';
      blind_pos_max@char = 'blind_pos_max';
      
   end
   
   properties(Access=private)
      
      facadeSpecs = struct('be_id',{},'v_id',{},'absorp',{});
      %        windowSpecs = struct('be_id',{},'v_id',{},'u_id',{},'secGainsFrac',{},'rValue',{});
      windowSpecs = struct('be_id',{},'v_id',{},'u_id',{},'secGainsFrac',{});
      infiltrationSpecs = struct('zone_id',{},'airchangerate',{});
      
   end
   
   methods
      
      function obj = BuildingHull(Building, EHF_identifier, source_file)
         
         % check arguments
         if ~isa(Building,Constants.building_name_str)
            error('BuildingHull:Argument','Argument error. Argument 1 is required to be of type ''%s''.\n',Constants.building_name_str);
         end
         
         % check if building has a thermal model
         if isempty(Building.building_model.thermal_submodel)
            error('BuildingHull:NoThermalModel','%s with %s required.\n',Constants.building_name_str,Constants.thermalmodel_name_str);
         end
         
         % check if file exists
         if ~(exist(source_file,'file') == 2)
            error('BuildingHull:UnknownFile','File ''%s'' does not exist. Valid file file path (string) required. Full file path recommended.\n',source_file);
         end
         
         obj.identifiers = Identifier;
         obj.EHF_identifier = EHF_identifier;
         obj.source_file = source_file;
         obj = obj.generateModel(Building);
         obj.checkNan();
         
      end
      
      function [Fx,Fu,Fv,g,constraint_identifiers] = getConstraintsMatrices(obj,parameters)
         
         p = parameters;
         
         n_x = length(obj.Aq);
         n_u = length(obj.identifiers.u); % n_u always even in this model
         n_v = length(obj.identifiers.v);
         n_c = length(obj.identifiers.constraints);
         
         % check if fields in parameters are existent
         % check if min/max fields in parameters are existent and make sense
         chkFieldsMinMaxVal = cell(n_u,4);
         for i=1:n_u
          
            chkFieldsMinMaxVal{i,1} = ['BPos',obj.identifiers.u{i}(2:end),'_min'];
            chkFieldsMinMaxVal{i,2} = ['BPos',obj.identifiers.u{i}(2:end),'_max'];
            chkFieldsMinMaxVal{i,3} = @(x)x>=0;
            chkFieldsMinMaxVal{i,4} = obj.identifiers.u{i};
            getIdIndex(obj.identifiers.constraints,chkFieldsMinMaxVal{i,1}); % just to check if the field exists
            getIdIndex(obj.identifiers.constraints,chkFieldsMinMaxVal{i,2}); % just to check if the field exists
            
         end
         
         for i = 1:size(chkFieldsMinMaxVal,1)
            
            fn_min = chkFieldsMinMaxVal{i,1};
            fn_max = chkFieldsMinMaxVal{i,2};
            
            if ~isfield(p,fn_min) || ~isfield(p,fn_max)
               error('getContraintsMatrices:parameters','Field %s or %s not found.\n',[obj.EHF_identifier,'.',fn_min],[obj.EHF_identifier,'.',fn_max]);
            end
            if numel(p.(fn_min)) ~= 1 || ~isnumeric(p.(fn_min)) || numel(p.(fn_max)) ~= 1 || ~isnumeric(p.(fn_max))
               error('getContraintsMatrices:parameters','Bad parameter values in fields %s or %s.\n',[obj.EHF_identifier,'.',fn_min],[obj.EHF_identifier,'.',fn_max]);
            end
            if p.(fn_min)>p.(fn_max)
               error('getContraintsMatrices:parameters','Parameter value %s larger than %s.\n',[obj.EHF_identifier,'.',fn_min],[obj.EHF_identifier,'.',fn_max]);
            end
            if ~(chkFieldsMinMaxVal{i,3}(p.(fn_min)) || chkFieldsMinMaxVal{i,3}(p.(fn_max)))
               error('getContraintsMatrices:parameters','Bad parameter values in fields %s or %s.\n',[obj.EHF_identifier,'.',fn_min],[obj.EHF_identifier,'.',fn_max]);
            end
            
         end
         
         Fx = zeros(n_c,n_x);
         Fu = zeros(n_c,n_u);
         Fv = zeros(n_c,n_v);
         g = zeros(n_c,1);
         
         for i = 1:size(chkFieldsMinMaxVal,1)
            
            fn_min = chkFieldsMinMaxVal{i,1};
            fn_max = chkFieldsMinMaxVal{i,2};
            u_id = chkFieldsMinMaxVal{i,4};
            
            idx_min = getIdIndex(obj.identifiers.constraints,fn_min);
            idx_max = getIdIndex(obj.identifiers.constraints,fn_max);
            idx_u = getIdIndex(obj.identifiers.u,u_id);
            
            Fu(idx_min,idx_u) = -1;
            g(idx_min,1) = -p.(fn_min);
            
            Fu(idx_max,idx_u) = 1;
            g(idx_max,1) = p.(fn_max);
            
         end
         
         constraint_identifiers = obj.identifiers.constraints;
         
         
      end % getConstraintsMatrices
      
      function [cu] = getCostVector(obj,parameters)  %#ok<INUSD>
         
         cu = zeros(length(obj.identifiers.u),1);
         
      end % getCostVector
      
   end % methods
   
   methods(Access=private)
      
      function obj = generateModel(obj,building)
         
         headers = [{obj.facadeSpecs_header}; {obj.windowSpecs_header}; {obj.infiltrationSpecs_header}];
         [dataTables,anchorIdxs] = getDataTablesFromFile(obj.source_file,headers);
         dataTable_fac = dataTables{1};
         dataTable_win = dataTables{2};
         dataTable_inf = dataTables{3};
         anchorIdxs_fac.row = anchorIdxs.row(1);
         anchorIdxs_fac.col = anchorIdxs.col(1);
         anchorIdxs_win.row = anchorIdxs.row(2);
         anchorIdxs_win.col = anchorIdxs.col(2);
         anchorIdxs_inf.row = anchorIdxs.row(3);
         anchorIdxs_inf.col = anchorIdxs.col(3); 
         
         
         obj = setFacadeSpecs(obj,dataTable_fac,anchorIdxs_fac,building);
         obj = setWindowSpecs(obj,dataTable_win,anchorIdxs_win,building);
         obj = setInfiltrationSpecs(obj,dataTable_inf,anchorIdxs_inf,building);
         obj = generateIdentifiers(obj,building);
         

         
         
         % initialize matrix Bq_u according to number of controlled windows
         % get dimensions and initalize matrices
         n_x = length(obj.identifiers.x);
         n_q = length(obj.identifiers.q);
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         
         % we assume that n_q = n_x
         obj.Aq = zeros(n_q,n_x);
         obj.Bq_u = zeros(n_q,n_u);
         obj.Bq_v = zeros(n_q,n_v);
         obj.Bq_xu = zeros(n_q,n_x,n_u);
         obj.Bq_vu = zeros(n_q,n_v,n_u);
         
                  
         bc = building.building_model.boundary_conditions;
         tmd = building.thermal_model_data;
         
         % ----------------------------------------------------------------------------------------------------------------------------------
         % GROUND TEMPERATURE
         % The model is as follows: area of exterior wall / Resistance of
         % Exterior wall times ground temperature minus temperature of
         % outermost layer of floor
         
         % q^i_EWo_j = a^i_EWo_j / R_EW * (v_GND - x^i_EWo_j)
         
         % where R_EW = 1 / alpha_EW + R_spec_EW * d_last_layer / 2
         % R_EW is stored in the connection information (value)
         % identifier 1: state
         % identifier 2: 'GND', in our setup(AMB,GND,ADB) are always stored in identifier 2
         n_connections_GND = length(bc.ground);
         
         for i = 1:n_connections_GND
            
            idx_v_GND = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',Constants.var_ground_identifier));
            % get indices of the states
            idx_q = getIdIndex(obj.identifiers.q,strcat(Constants.heat_flux_variable,bc.ground(i).identifier_1(2:end)));
            idx_x = getIdIndex(obj.identifiers.x,bc.ground(i).identifier_1);
            
            % Set matrix Aq
            obj.Aq(idx_q,idx_x)  = obj.Aq(idx_q,idx_x)                       - bc.ground(i).value;
            
            % Set first column of matix Bq_v
            obj.Bq_v(idx_q,idx_v_GND) = obj.Bq_v(idx_q,idx_v_GND)            + bc.ground(i).value;
            
         end
         
         % ----------------------------------------------------------------------------------------------------------------------------------
         % USER DEFINED
         n_connections_UDEF = length(bc.user_defined);
         for i=1:n_connections_UDEF

            idx_q = getIdIndex(obj.identifiers.q,strcat(Constants.heat_flux_variable,bc.user_defined(i).identifier_1(2:end)));
            idx_x = getIdIndex(obj.identifiers.x,bc.user_defined(i).identifier_1);
            idx_v = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',bc.user_defined(i).identifier_2));
            
            % Set matrix Aq
            obj.Aq(idx_q,idx_x)  = obj.Aq(idx_q,idx_x)                       - bc.user_defined(i).value;
            
            % Set first column of matix Bq_v
            obj.Bq_v(idx_q,idx_v) = obj.Bq_v(idx_q,idx_v)                    + bc.user_defined(i).value;
            
         end
         
         
         % ----------------------------------------------------------------------------------------------------------------------------------
         % FACADE BUILDING ELEMENTS
         % The model is as follows ( EW = Exterior Wall) See section 3.2.2
         % from "Semi-Automated Modular Modeling of Buildings for Model
         % Predictive Control"
         % q^i_EWo_j = a^i_EW_j / R_EW * (v_AMB - x^i_EWo_j) + gamma_absorptance * v^i_solGlob_EW_j,
         % where R_EW = 1/alpha_EW + R_spec_EW * d_last_layer / 2
         
         idx_v_AMB = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',Constants.var_ambient_identifier));
         
         % conduction part
         for i=1:length(bc.ambient)
            
            if ~isempty(ismember(obj.identifiers.x,bc.ambient(i).identifier_1))
               id_x = bc.ambient(i).identifier_1;
            else
               id_x = bc.ambient(i).identifier_2;
            end
            idx_x = getIdIndex(obj.identifiers.x,id_x);
            idx_q = getIdIndex(obj.identifiers.q,[Constants.heat_flux_variable,id_x(2:end)]);
            
            % set matrix coeffiecients
            obj.Aq(idx_q,idx_x) = obj.Aq(idx_q,idx_x)                        - bc.ambient(i).value;
            obj.Bq_v(idx_q,idx_v_AMB) = obj.Bq_v(idx_q,idx_v_AMB)            + bc.ambient(i).value;
            
         end
         
         
         % radiation part
         for i = 1:length(obj.facadeSpecs)
            
            id_BE = obj.facadeSpecs(i).be_id;
            idx = tmd.getBuildingElementIdxFromIdentifier(id_BE);
            adj_A = tmd.building_elements(idx).adjacent_A;
            adj_B = tmd.building_elements(idx).adjacent_B;
            
            
            % compute net area of BE
            net_area = getAreasFromBE(id_BE,tmd);
            
            % get input q identifiers of the outer building element layers
            [q_id_adj_A, q_id_adj_B] =  getBEOuterQXIds(id_BE,tmd,obj.identifiers);
            if isempty(q_id_adj_A)
               error('Was this a no mass construction?');
            end
            
            idx_v_facade = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',obj.solarDisturbanceLabel,'_',obj.facadeSpecs(i).v_id));
            
            if strcmp(Constants.ambient_identifier,adj_A)
               idx_q = getIdIndex(obj.identifiers.q,q_id_adj_A);
            elseif strcmp(Constants.ambient_identifier,adj_B)
               idx_q = getIdIndex(obj.identifiers.q,q_id_adj_B);
            else
               error('This should have been caught before..');
            end
            
            obj.Bq_v(idx_q,idx_v_facade) = obj.Bq_v(idx_q,idx_v_facade)+net_area*obj.facadeSpecs(i).absorp;
            
         end
         
         
         % ----------------------------------------------------------------------------------------------------------------------------------
         % WINDOW CONDUCTION
         
         
         % For base conduction part (independent of blinds)
         for i = 1:length(obj.windowSpecs)
            
            id_BE = obj.windowSpecs(i).be_id;
            idx_BE = tmd.getBuildingElementIdxFromIdentifier(id_BE);
            
            adj_A = tmd.building_elements(idx_BE).adjacent_A;
            adj_B = tmd.building_elements(idx_BE).adjacent_B;
            
            % get zone identifier of current BE
            if strcmp(adj_A,Constants.ambient_identifier)
               zone_id = adj_B;
            elseif strcmp(adj_B,Constants.ambient_identifier)
               zone_id = adj_A;
            end
            
            % get window identifier of current BE and its area
            win_id = tmd.building_elements(idx_BE).window_identifier;
            
            % get window and frame area
            [U_win,area_win_glass,area_win_frame] = getUAWin(win_id,tmd);
            
            idx_q = getIdIndex(obj.identifiers.q,strcat(Constants.heat_flux_variable,'_',zone_id));
            idx_x = getIdIndex(obj.identifiers.x,strcat(Constants.state_variable,'_',zone_id));
            
            a_win_glassAndFrame = area_win_frame + area_win_glass;
            obj.Aq(idx_q,idx_x) = obj.Aq(idx_q,idx_x) - U_win*a_win_glassAndFrame;
            obj.Bq_v(idx_q,idx_v_AMB) = obj.Bq_v(idx_q,idx_v_AMB) + U_win*a_win_glassAndFrame;
            
         end
         
         
         
         % Conduction part dependent on blinds position (CURRENTLY NOT CONSIDERED)
         
         % %             u_ids = unique({obj.windowSpecs.u_id});
         % %             u_ids(cellfun(@(x)strcmp(x,Constants.EMPTY_str),u_ids)) = [];
         % %
         % %
         % %
         % %             % iterate over all blinds control signals
         % %             for i = 1:length(u_ids)
         % %
         % %                 % get index of the blinds signal
         % %                 idx_u = find(ismember(obj.identifiers.u,u_ids{i}));
         % %
         % %                 % get all BE with windows that have the current blinds control
         % %                 idx_u_inWinSpec = find(ismember({obj.windowSpecs.u_id},u_ids{i}));
         % %                 BE_ids_controlled = {obj.windowSpecs(idx_u_inWinSpec).be_id};
         % %
         % %                 % get all zones influenced by current blinds control
         % %                 idx_BE = find(ismember({tmd.building_elements.identifier},BE_ids_controlled));
         % %                 zone_ids_with_same_blind_control = union({tmd.building_elements(idx_BE).adjacent_A},{tmd.building_elements(idx_BE).adjacent_B});
         % %                 % remove 'AMB','GND','ADB' from set
         % %                 zone_ids_with_same_blind_control = setdiff(zone_ids_with_same_blind_control,Constants.exterior);
         % %
         % %                 for j = 1:length(zone_ids_with_same_blind_control)
         % %
         % %                     % get all BE of zone j, that have windows with current blinds control
         % %                     BE_ids_with_windows_zone_j = intersect(BE_ids_controlled,tmd.getAllBEIdsFromZoneId(zone_ids_with_same_blind_control{j}));
         % %
         % %                     n_windows_zone_j = length(BE_ids_with_windows_zone_j);
         % %
         % %                     % total conductive coefficient
         % %                     UA_blindsOpen = 0;
         % %                     UA_blindsClosed = 0;
         % %
         % %                     % iterate over all windows in specific zone to calculate
         % %                     for k = 1:n_windows_zone_j
         % %
         % %                         idx_BE_with_win = tmd.getBuildingElementIdxFromIdentifier(BE_ids_with_windows_zone_j{k});
         % %                         win_id = tmd.building_elements(idx_BE_with_win).window_identifier;
         % %                         idx_win = tmd.getWindowIdxFromIdentifier(win_id);
         % %
         % %                         % get glass area of window k
         % %                         if ThermalModelData.is_Parameter_identifier(tmd.windows(idx_win).glass_area)
         % %                             parameter_idx = tmd.getParameterIdxFromIdentifier(tmd.windows(idx_win).glass_area);
         % %                             a_win_glass = str2double(tmd.parameters(parameter_idx).value);
         % %                         else
         % %                             a_win_glass = str2double(tmd.windows(idx_win).glass_area);
         % %                         end
         % %
         % %                         % get frame area
         % %                         if ThermalModelData.is_Parameter_identifier(tmd.windows(idx_win).frame_area)
         % %                             parameter_idx = tmd.getParameterIdxFromIdentifier(tmd.windows(idx_win).frame_area);
         % %                             a_win_frame = str2double(tmd.parameters(parameter_idx).value);
         % %                         else
         % %                             a_win_frame = str2double(tmd.windows(idx_win).frame_area);
         % %                         end
         % %
         % %
         % %                         % get U-value of window k
         % %                         if ThermalModelData.is_Parameter_identifier(tmd.windows(idx_win).U_value)
         % %                             try
         % %                                 param_idx = tmd.getParameterIdxFromIdentifier(tmd.windows(idx_win).U_value);
         % %                                 U_win = str2double(tmd.parameters(param_idx).value);
         % %
         % %                                 if ~(U_win>0)
         % %                                     error('generateModel:U_value','At %s index ''%d'': Resistance ''%s'' required to be greater zero.\n',lower(Constants.parameter_name_str),param_idx,U_win);
         % %                                 end
         % %
         % %                             catch
         % %                                 error('generateModel:U_value','%s ''%s'' not in data.\n',Constants.parameter_name_str,tmd.windows(idx_win).U_value);
         % %                             end
         % %                         else
         % %                             U_win = str2double(tmd.windows(idx_win).U_value);
         % %                         end
         % %
         % %                         % get thermal resistance according when blinds are closed
         % %                         idx_BE_window_spec = getIdIndex({obj.windowSpecs.be_id},BE_ids_with_windows_zone_j{k});
         % %                         R_bl = obj.windowSpecs(idx_BE_window_spec).rValue;
         % %                         a_win_glassAndFrame = a_win_frame + a_win_glass;
         % %
         % %                         UA_blindsClosed = UA_blindsClosed   + a_win_glassAndFrame/(1/U_win+R_bl);
         % %                         UA_blindsOpen = UA_blindsOpen       + a_win_glassAndFrame*(1/U_win);
         % %                     end
         % %
         % %                     % set conductive part in the model
         % %                     q_id = strcat(Constants.heat_flux_variable,'_',zone_ids_with_same_blind_control{j});
         % %                     x_id = strcat(Constants.state_variable,'_',zone_ids_with_same_blind_control{j});
         % %                     idx_q = getIdIndex(obj.identifiers.q,q_id);
         % %                     idx_x = getIdIndex(obj.identifiers.x,x_id);
         % %
         % %                     % compute coefficient
         % %                     Delta_Ua_win_tot_j = UA_blindsOpen - UA_blindsClosed;
         % %
         % %
         % %                     obj.Aq(idx_q,idx_x) = obj.Aq(idx_q,idx_x) + Delta_Ua_win_tot_j;
         % %                     obj.Bq_v(idx_q,idx_v_AMB) = obj.Bq_v(idx_q,idx_v_AMB) - Delta_Ua_win_tot_j;
         % %                     obj.Bq_xu(idx_q,idx_x,idx_u) = obj.Bq_xu(idx_q,idx_x,idx_u) - Delta_Ua_win_tot_j;
         % %                     obj.Bq_vu(idx_q,idx_v_AMB,idx_u) = obj.Bq_vu(idx_q,idx_v_AMB,idx_u) + Delta_Ua_win_tot_j;
         % %                 end
         % %             end
         % ----------------------------------------------------------------------------------------------------------------------------------
         % WINDOW RADIATION
         
         for i = 1:length(obj.windowSpecs);
            
            % get BE id from window specification and its index from building data
            id_BE = obj.windowSpecs(i).be_id;
            idx_BE = tmd.getBuildingElementIdxFromIdentifier(id_BE);
            
            adj_A = tmd.building_elements(idx_BE).adjacent_A;
            adj_B = tmd.building_elements(idx_BE).adjacent_B;
            
            % get zone identifier of current BE
            if strcmp(adj_A,Constants.ambient_identifier)
               zone_id = adj_B;
            elseif strcmp(adj_B,Constants.ambient_identifier)
               zone_id = adj_A;
            else
               error('This should have been caught before..');
            end
            
            % get window identifier of current BE and its area
            id_win = tmd.building_elements(idx_BE).window_identifier;
            idx_win = tmd.getWindowIdxFromIdentifier(id_win);
            
            % get window area
            a_win_glass = tmd.evalStr(tmd.windows(idx_win).glass_area);
            
            % get frame area
            a_win_frame = tmd.evalStr(tmd.windows(idx_win).frame_area);
            
            % get SHGC
            SHGC = tmd.evalStr(tmd.windows(idx_win).SHGC);
            
            % get secondary heat gains fraction
            secondary_gains_fraction = obj.windowSpecs(i).secGainsFrac;
            
            % index of input v signal
            idx_v = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',obj.solarDisturbanceLabel,'_',obj.windowSpecs(i).v_id));
            
            % if window has blinds control we set have to set the bilinear part: matrix Bq_vu
            if ~isempty(obj.windowSpecs(i).u_id)
               hasBlinds = true;
            else
               hasBlinds = false;
            end
            
            % get all BE associated with current zone identifier
            BE_ids_in_zone_j = tmd.getAllBEIdsFromZoneId(zone_id);
            
            rm_inds = [];
            % remove all that dont appear in the state identifiers
            for k=1:length(BE_ids_in_zone_j)
               if all(cellfun(@isempty,strfind(obj.identifiers.x,BE_ids_in_zone_j{k})))
                  rm_inds(end+1) = k; %#ok<AGROW>
               end
            end
            BE_ids_in_zone_j(rm_inds) = [];
            
            n_BE_in_zone_j = length(BE_ids_in_zone_j);
            
            % iterate over all BE in order to get areas and to compute total area. in case of a double connected BE, its area is counted once in areas_BE_in_zone_j
            % but double in totArea_BE_in_zone_j
            [areas_BE_in_zone_j,totArea_BE_in_zone_j] = getAreasFromBE(BE_ids_in_zone_j,tmd);
            
            % set matrix coefficients Bq_v, Bq_vu
            for k = 1:n_BE_in_zone_j
               
               % get idx of BE
               idx = tmd.getBuildingElementIdxFromIdentifier(BE_ids_in_zone_j{k});
               adj_A = tmd.building_elements(idx).adjacent_A;
               adj_B = tmd.building_elements(idx).adjacent_B;
               
               % get input q identifiers of the outer building element layers
               [q_id_adj_A, q_id_adj_B] =  getBEOuterQXIds(BE_ids_in_zone_j{k},tmd,obj.identifiers);
               if isempty(q_id_adj_A) % then it was a no mass construction...
                  continue;
               end
               
               % set the matrices
               if strcmp(adj_A,zone_id)
                  idx_q = getIdIndex(obj.identifiers.q,q_id_adj_A);
                  if hasBlinds
                     idx_u = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.blindsInputLabel,'_',obj.windowSpecs(i).u_id));
                     obj.Bq_vu(idx_q,idx_v,idx_u) = obj.Bq_vu(idx_q,idx_v,idx_u) + areas_BE_in_zone_j(k)/totArea_BE_in_zone_j*(1-secondary_gains_fraction)*(a_win_glass+a_win_frame)*SHGC;
                  else
                     obj.Bq_v(idx_q,idx_v) = obj.Bq_v(idx_q,idx_v) + areas_BE_in_zone_j(k)/totArea_BE_in_zone_j*(1-secondary_gains_fraction)*(a_win_glass+a_win_frame)*SHGC;
                  end
               end
               
               if strcmp(adj_B,zone_id)
                  idx_q = getIdIndex(obj.identifiers.q,q_id_adj_B);
                  if hasBlinds
                     idx_u = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.blindsInputLabel,'_',obj.windowSpecs(i).u_id));
                     obj.Bq_vu(idx_q,idx_v,idx_u) = obj.Bq_vu(idx_q,idx_v,idx_u) + areas_BE_in_zone_j(k)/totArea_BE_in_zone_j*(1-secondary_gains_fraction)*(a_win_glass+a_win_frame)*SHGC;
                  else
                     obj.Bq_v(idx_q,idx_v) = obj.Bq_v(idx_q,idx_v) + areas_BE_in_zone_j(k)/totArea_BE_in_zone_j*(1-secondary_gains_fraction)*(a_win_glass+a_win_frame)*SHGC;
                  end
               end
               
            end
            
            % set radiation part into the zone node
            idx_q = getIdIndex(obj.identifiers.q,strcat(Constants.heat_flux_variable,'_',zone_id));
            
            % set Bq_vu
            if hasBlinds
               obj.Bq_vu(idx_q,idx_v,idx_u) = obj.Bq_vu(idx_q,idx_v,idx_u) + secondary_gains_fraction*(a_win_glass+a_win_frame)*SHGC;
               % set Bq_v
            else
               obj.Bq_v(idx_q,idx_v) = obj.Bq_v(idx_q,idx_v) + secondary_gains_fraction*(a_win_glass+a_win_frame)*SHGC;
            end
         end
         
         % ----------------------------------------------------------------------------------------------------------------------------------
         % INFILTRATION
         for i = 1:length(obj.infiltrationSpecs);
            
            % get BE id from window specification and its index from building data
            zone_id = obj.infiltrationSpecs(i).zone_id;
            airchangerate = obj.infiltrationSpecs(i).airchangerate;
            
            zone_idx = getIdIndex({tmd.zones.identifier},zone_id);
            zone_volume = tmd.evalStr(tmd.zones(zone_idx).volume);
            
            zone_q_id = strcat(Constants.heat_flux_variable,'_',zone_id);
            zone_x_id = strcat(Constants.state_variable,'_',zone_id);
            
            idx_q_zone = getIdIndex(obj.identifiers.q,zone_q_id);
            idx_x_zone = getIdIndex(obj.identifiers.x,zone_x_id);

            
            % Set matrix Aq
            obj.Aq(idx_q_zone,idx_x_zone)  = obj.Aq(idx_q_zone,idx_x_zone)             - airchangerate*zone_volume/3600*Constants.C_air*Constants.rho_air;
            
            % Set first column of matix Bq_v
            obj.Bq_v(idx_q_zone,idx_v_AMB) = obj.Bq_v(idx_q_zone,idx_v_AMB)            + airchangerate*zone_volume/3600*Constants.C_air*Constants.rho_air;

         end         
         
      end % generateModel
      
      function obj = setFacadeSpecs(obj,dataTable_fac,anchorIdxs_fac,building)
         
         header = dataTable_fac(1,:);
         body = dataTable_fac(2:end,:);
         
         idx_be_id = getIdIndex(header,obj.header_be_id_str);
         idx_v_id = getIdIndex(header,obj.header_v_id_str);
         idx_absorp = getIdIndex(header,obj.header_absorp_str);
         
         
         for i=1:size(body,1)
            
            be_id = body{i,idx_be_id}; % 2, because the identifiers are located in the 2nd column of the block
            absorptance = str2double(ThermalModelData.check_value(body{i,idx_absorp},false));
            disturbance_identifier = ThermalModelData.check_special_identifier(body{i,idx_v_id});
            
            % check if current building element exists and has ambient identifier in adjacent_A or adjacent_B and if current building element is already specified
            be_idx = building.thermal_model_data.getBuildingElementIdxFromIdentifier(be_id);
            if isempty(be_idx)
               error('getFacadeSpecs:Consistency_Identifier','%s identifier ''%s'' of file ''%s'' at row %d column %d NOT contained in building Data.\n',Constants.buildingelement_name_str,be_id,sprintf('%s',regexprep(obj.source_file,'\','\\')),anchorIdxs_fac.row+1+i,anchorIdxs_fac.col+idx_be_id-1);
            end
            adj_A = building.thermal_model_data.building_elements(be_idx).adjacent_A;
            adj_B = building.thermal_model_data.building_elements(be_idx).adjacent_B;
            if ~(strcmp(adj_A,Constants.ambient_identifier) || strcmp(adj_B,Constants.ambient_identifier))
               error('getFacadeSpecs:Consistency_Adjacent','%s ''%s'' of file ''%s'' at row %d column %d has NOT ''%s'' identifier in adjacent A or B.\n',Constants.buildingelement_name_str,be_id,sprintf('%s',regexprep(obj.source_file,'\','\\')),anchorIdxs_fac.row+1+i,anchorIdxs_fac.col+idx_be_id-1,Constants.ambient_identifier);
            end
            be_id_already_used = intersect({obj.facadeSpecs.be_id},be_id);
            if ~isempty(be_id_already_used)
               error('getFacadeSpecs:Identifier',[Constants.error_msg_xlsFile(Constants.buildingelement_name_str,obj.source_file,anchorIdxs_fac.row+1+i,anchorIdxs_fac.col+idx_be_id-1),...
                  '%s identifier ''%s'' is already specified.\n'],Constants.buildingelement_name_str,be_id);
            end
            
            % check solar absorption
            if strcmp(absorptance,Constants.NULL_str)
               error('XLSFile:SolarAbsorption',[Constants.error_msg_xlsFile('Facade solar group',obj.source_file,anchorIdxs_fac.row+1+i,anchorIdxs_fac.col+idx_absorp-1),...
                  Constants.error_msg_value('Facade solar group',body{i,idx_absorp},'solar absorption',true,'between 0 and 1')]);
            elseif ~isnan(str2double(absorptance)) && ~(str2double(absorptance) >= 0 && str2double(absorptance) <= 1)
               error('XLSFile:SolarAbsorption',[Constants.error_msg_xlsFile('Facade solar group',obj.source_file,anchorIdxs_fac.row+1+i,anchorIdxs_fac.col+idx_absorp-1),...
                  Constants.error_msg_value('Facade solar group',body{i,idx_absorp},'solar absorption',true,'between 0 and 1')]);
            end
            
            if isempty(disturbance_identifier)
               error('Bad disturbance identifier');
            end
            
            obj.facadeSpecs(i).be_id = be_id;
            obj.facadeSpecs(i).absorp = absorptance;
            obj.facadeSpecs(i).v_id = disturbance_identifier;
            
         end
                  
      end % setFacadeSpecs
      
      function obj = setWindowSpecs(obj,dataTable_win,anchorIdxs_win,building)
         
         header = dataTable_win(1,:);
         body = dataTable_win(2:end,:);
         
         idx_be_id = getIdIndex(header,obj.header_be_id_str);
         idx_u_id = getIdIndex(header,obj.header_u_id_str);
         idx_v_id = getIdIndex(header,obj.header_v_id_str);
         idx_secGainsFrac = getIdIndex(header,obj.header_secGainsFrac_str);
         
         % get valid specifications
         for i = 1:size(body,1)
            
            % check entries
            be_id = ThermalModelData.check_identifier(body{i,idx_be_id},BuildingElement.key);
            v_id = ThermalModelData.check_special_identifier(body{i,idx_v_id});
            u_id = ThermalModelData.check_special_identifier(body{i,idx_u_id});
            secondary_gains_fraction_str = ThermalModelData.check_value(body{i,idx_secGainsFrac},false);
            %               resistance_str =  ThermalModelData.check_value(body{i,6},false);
            
            % u_signal_id and thermal resistance can be empty, but not either/or
            if (isempty(be_id) || isempty(v_id) || isempty(secondary_gains_fraction_str))% || (isempty(resistance_str) && ~isempty(u_id)) || (~isempty(resistance_str) && isempty(u_id))
               error('ERR');
            end
            
            % check if current building element exists and has ambient identifier in adjacent_A or adjacent_B
            be_idx = building.thermal_model_data.getBuildingElementIdxFromIdentifier(be_id);
            if isempty(be_idx)
               error('getWindowSpecs:Consistency_Identifier','%s identifier ''%s'' of file ''%s'' at row %d column %d NOT contained in building Data.\n',Constants.buildingelement_name_str,be_id,sprintf('%s',regexprep(obj.source_file,'\','\\')),anchorIdxs_win.row+1+i,anchorIdxs_win.col+idx_be_id);
            end
            adj_A = building.thermal_model_data.building_elements(be_idx).adjacent_A;
            adj_B = building.thermal_model_data.building_elements(be_idx).adjacent_B;
            if ~(strcmp(adj_A,Constants.ambient_identifier) || strcmp(adj_B,Constants.ambient_identifier))
               error('getWindowSpecs:Consistency_Adjacent','%s ''%s'' of file ''%s'' at row %d column %d has NOT ''%s'' identifier in adjacent A or B.\n',Constants.buildingelement_name_str,be_id,sprintf('%s',regexprep(obj.source_file,'\','\\')),anchorIdxs_win.row+1+i,anchorIdxs_win.col+idx_be_id,Constants.ambient_identifier);
            end
            
            % check if builing element has window
            if isempty(building.thermal_model_data.building_elements(be_idx).window_identifier)
               error('ExternalHeatFluxGenerator_buildingHullSolar:Consistency_Window','%s ''%s'' of file ''%s'' at row %d column %d has NO window.\n',Constants.buildingelement_name_str,be_id,sprintf('%s',regexprep(obj.source_file,'\','\\')),anchorIdxs_win.row+1+i,anchorIdxs_win.col+idx_be_id);
            end
            
            % check if current building element is already specified
            be_id_already_used = intersect({obj.windowSpecs.be_id},be_id);
            if ~isempty(be_id_already_used)
               error('getWindowSpecs:Identifier',[Constants.error_msg_xlsFile(Constants.buildingelement_name_str,obj.source_file,anchorIdxs_win.row+1+i,anchorIdxs_win.col+idx_be_id),...
                  '%s identifier ''%s'' is already specified.\n'],Constants.buildingelement_name_str,be_id);
            end
            
            % check fraction
            secondary_gains_fraction = str2double(secondary_gains_fraction_str);
            if isnan(secondary_gains_fraction) || (~(secondary_gains_fraction >= 0 && secondary_gains_fraction <= 1))
               error('XLSFile:SolarAbsorption',[Constants.error_msg_xlsFile('Window solar group',obj.source_file,anchorIdxs_win.row+1+i,anchorIdxs_win.col+idx_secGainsFrac),...
                  Constants.error_msg_value('Window solar group',dataTable_win{i,idx_secGainsFrac},'secondary gains fraction',false,'between 0 and 1')]);
            end
            
            % assign specifications
            obj.windowSpecs(end+1).be_id = be_id;
            obj.windowSpecs(end).v_id = v_id;
            obj.windowSpecs(end).secGainsFrac = secondary_gains_fraction;
            
            % check if blinds control is available, then a feasible thermal resistance must be defined and assigned to specifications
            if ~isempty(u_id) %&& ~isempty(resistance_str)
               
               %                   R_bl = str2double(resistance_str);
               %                   if isnan(R_bl) || ~(R_bl>=0)
               %                       error('getWindowSpecs:Resistance','Resistance ''%s'' required to be non-negative.\n',resistance_str);
               %                   end
               
               obj.windowSpecs(end).u_id = u_id;
               %                    obj.windowSpecs(end).rValue = R_bl;
            else
               obj.windowSpecs(end).u_id = Constants.EMPTY_str;
            end
            
         end
         
         % check if all BE with windows have been specified
         idx_windowBE = find(~cellfun(@isempty,regexprep({building.thermal_model_data.building_elements.window_identifier},'\s','')));
         be_ids_windowBE = {building.thermal_model_data.building_elements(idx_windowBE).identifier};
         d1 = setdiff(be_ids_windowBE,{obj.windowSpecs.be_id});
         d2 = setdiff({obj.windowSpecs.be_id},be_ids_windowBE);
         if ~isempty(d1)
            error('getWindowSpecs:BE','The following building element(s) have windows but did not appear in the window specifications: %s \n',d1{:});
         end
         if ~isempty(d2)
            error('This should have been caught before');
         end
         
      end % setWindowSpecs
      
      function obj = setInfiltrationSpecs(obj,dataTable_inf,anchorIdxs_inf,building)
                  
         header = dataTable_inf(1,:);
         body = dataTable_inf(2:end,:);
         
         idx_zone_id = getIdIndex(header,obj.header_zone_id_str);
         idx_airchangerate = getIdIndex(header,obj.header_airchangerate_str);

         % get valid specifications
         for i = 1:size(body,1)
            
            % check entries
            zone_id = body{i,idx_zone_id};
            airchangerate_str = body{i,idx_airchangerate};
            
            try
               getIdIndex({building.thermal_model_data.zones.identifier},zone_id);
            catch e
               error('setInfiltrationSpecs:General',[Constants.error_msg_xlsFile(Constants.buildingelement_name_str,obj.source_file,anchorIdxs_inf.row+1+i,anchorIdxs_inf.col+idx_zone_id),...
                  '%s identifier ''%s'' not found.\n'],Constants.zone_name_str,zone_id);
            end
            
            % check if zone identifier is already specified
            zone_id_already_used = intersect({obj.infiltrationSpecs.zone_id},zone_id);
            if ~isempty(zone_id_already_used)
               error('getWindowSpecs:General',[Constants.error_msg_xlsFile(Constants.buildingelement_name_str,obj.source_file,anchorIdxs_inf.row+1+i,anchorIdxs_inf.col+idx_zone_id),...
                  '%s identifier ''%s'' is already specified.\n'],Constants.buildingelement_name_str,zone_id);
            end
            
            % check fraction
            if isempty(airchangerate_str)
               airchangerate = 0;
            else
               airchangerate = str2double(airchangerate_str);
            end
            if isnan(airchangerate) || airchangerate < 0
               error('getWindowSpecs:General',[Constants.error_msg_xlsFile('Infiltration Specification',obj.source_file,anchorIdxs_inf.row+1+i,anchorIdxs_inf.col+idx_airchangerate),...
                  'Infiltration Air Change Rate [1/h] must be positive.\n']);
            end
            
            % assign specifications
            obj.infiltrationSpecs(end+1).zone_id = zone_id;
            obj.infiltrationSpecs(end).airchangerate = airchangerate;
            
         end
         
      
      end % setInfiltrationSpecs
      
      
      function obj = generateIdentifiers(obj,building)
         
         obj.identifiers = Identifier;
         
         obj.identifiers.x = building.building_model.identifiers.x;
         obj.identifiers.q = building.building_model.identifiers.q;
         
         % set ambient identifier
         obj.identifiers.v = [obj.identifiers.v;strcat(Constants.disturbance_variable,'_',Constants.var_ambient_identifier)];
         
         % set ground identifier if required
         n_connections_GND = length(building.building_model.boundary_conditions.ground);
         if n_connections_GND
            obj.identifiers.v = [obj.identifiers.v;strcat(Constants.disturbance_variable,'_',Constants.var_ground_identifier)];
         end
         

         % set variable names 
         unique_adj = unique([{building.thermal_model_data.building_elements.adjacent_A},{building.thermal_model_data.building_elements.adjacent_B}]);
         unique_adj = setdiff(unique_adj,Constants.exterior);
         for i=1:length(unique_adj)
            if ~isempty(regexprep(unique_adj{i},'^Z\d\d\d\d',''))
               obj.identifiers.v = [obj.identifiers.v;strcat(Constants.disturbance_variable,'_',unique_adj{i})];
            end
         end
         
         
         % set input v identifiers
         
         % facade solar group
         v_ids = {obj.facadeSpecs.v_id,obj.windowSpecs.v_id}';
         v_ids(cellfun(@(x)strcmp(x,Constants.EMPTY_str),v_ids)) = []; % remove empty string, below code is due to experienced issue in Matlab WINDOWS version
         if ~isempty(v_ids)
            obj.identifiers.v = [obj.identifiers.v; unique(strcat(Constants.disturbance_variable,'_',obj.solarDisturbanceLabel,'_',v_ids))];
         end
         
         % set input u identifiers
         u_ids = {obj.windowSpecs.u_id}';
         u_ids(cellfun(@(x)strcmp(x,Constants.EMPTY_str),u_ids)) = []; % remove empty string, below code is due to experienced issue in Matlab WINDOWS version
         if ~isempty(u_ids)
            obj.identifiers.u = [obj.identifiers.u; unique(strcat(Constants.input_variable,'_',obj.blindsInputLabel,'_',u_ids))];
         end
         
         % constraints due to blind identifiers
         for i = 1:length(obj.identifiers.u)
            obj.identifiers.constraints = [obj.identifiers.constraints; strcat('BPos',obj.identifiers.u{i}(2:end),'_min')];
            obj.identifiers.constraints = [obj.identifiers.constraints; strcat('BPos',obj.identifiers.u{i}(2:end),'_max')];
         end
         
      end % generateIdentifiers
      
      
      
   end % methods(Access=private)
end % classdef

function [areas_BE_in_zone_j,totArea_BE_in_zone_j] = getAreasFromBE(BE_ids,thermal_model_data)
   
   if ~iscell(BE_ids)
      BE_ids = {BE_ids};
   end
   
   totArea_BE_in_zone_j = 0;
   areas_BE_in_zone_j = zeros(length(BE_ids),1);
   for k = 1:length(BE_ids)
      
      % get idx of BE
      idx = thermal_model_data.getBuildingElementIdxFromIdentifier(BE_ids{k});
      
      % get BE area, net area if BE has window
      id_win = thermal_model_data.building_elements(idx).window_identifier;
      if ~isempty(id_win)
         
         [~,glass_area,frame_area] = getUAWin(id_win,thermal_model_data);
         
         a_win_glassAndFrame_k =  glass_area+frame_area;
      else
         a_win_glassAndFrame_k = 0;
      end
      
      try
         areas_BE_in_zone_j(k) = thermal_model_data.building_elements(idx).computeArea - a_win_glassAndFrame_k;
      catch %#ok<*CTCH>
         areas_BE_in_zone_j(k) = str2double(thermal_model_data.building_elements(idx).area) - a_win_glassAndFrame_k;
      end
      
      % catch internal masses and floor-ceiling BEs
      if strcmp(thermal_model_data.building_elements(idx).adjacent_A,thermal_model_data.building_elements(idx).adjacent_B)
         factor = 2;
      else
         factor = 1;
      end
      
      totArea_BE_in_zone_j = totArea_BE_in_zone_j + factor*areas_BE_in_zone_j(k);
   end
   
end

function [q_id_adj_A, q_id_adj_B, x_id_adj_A, x_id_adj_B] =  getBEOuterQXIds(id_BE,thermal_model_data,identifiers)
   
   % get idx of BE
   idx_BE = thermal_model_data.getBuildingElementIdxFromIdentifier(id_BE);
   adj_A = thermal_model_data.building_elements(idx_BE).adjacent_A;
   adj_B = thermal_model_data.building_elements(idx_BE).adjacent_B;
   
   
   % get state identifiers of the outer building element layers
   expr = ['x_',id_BE,'_L(\d*)_s(\d*)_',adj_A,adj_B];
   r = regexp(identifiers.x,expr,'tokens');
   idx_BE_states = find(~cellfun(@isempty,r));
   if isempty(idx_BE_states) && ~strncmp(NoMassConstruction.key,thermal_model_data.building_elements(idx_BE).construction_identifier,length(NoMassConstruction.key))
      error('Did not find proper BE states');
   end
   L = nan(numel(idx_BE_states),1);
   s = nan(numel(idx_BE_states),1);
   for l=1:numel(idx_BE_states)
      L(l) = str2double(r{idx_BE_states(l)}{1}{1});
      s(l) = str2double(r{idx_BE_states(l)}{1}{2});
   end
   if any(isnan(L)) || any(isnan(s))
      error('Bad match');
   end
   [~,idx_adj_A] = min(1000*L+s);                      % its on adjacent A side --> first layer, first state per layer
   [~,idx_adj_B] = max(1000*L+s);                      % its on adjacent B side --> last layer, last state per layer
   x_id_adj_A = identifiers.x{idx_BE_states(idx_adj_A)};
   x_id_adj_B = identifiers.x{idx_BE_states(idx_adj_B)};
   
   % get the q identifiers to the outer building element layers
   q_id_adj_A = [Constants.heat_flux_variable,x_id_adj_A(2:end)];
   q_id_adj_B = [Constants.heat_flux_variable,x_id_adj_B(2:end)];
   
end

function [U_win,area_win_glass,area_win_frame] = getUAWin(win_id,thermal_model_data)
   
   idx_win = thermal_model_data.getWindowIdxFromIdentifier(win_id);
   
   % get glass area
   area_win_glass = thermal_model_data.evalStr(thermal_model_data.windows(idx_win).glass_area);
   
   % get frame area
   area_win_frame = thermal_model_data.evalStr(thermal_model_data.windows(idx_win).frame_area);
   
   % get U_win
   U_win = thermal_model_data.evalStr(thermal_model_data.windows(idx_win).U_value);
   if ~(U_win>0)
      error('generateModel:U_value','At %s index ''%d'': Resistance ''%s'' required to be greater zero.\n',lower(Constants.parameter_name_str),param_idx,U_win);
   end
   
end
