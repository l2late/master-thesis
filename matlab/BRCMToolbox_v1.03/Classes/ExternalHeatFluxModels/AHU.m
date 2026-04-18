classdef AHU < EHFModelBaseClass
   %AHU 	This class represents the Air Handling Unit (AHU) external heat flux model of a building.
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
      
      n_properties@uint64 = uint64(3);   % number of required properties for object instantion
      multiIncludeOk@logical = true;
      
      % Model specific conventions
      AHU_EHF_name_str@char = 'Air handling unit';                                         % model name
      AHU_key@char = 'AHU';                                                                % model specific key
      AHU_spec_file_header@cell = {'AHU_specification' 'key' 'value'};                       % header for the AHU specification data file
      AHU_airflow_spec_file_header@cell = ...
         {'airflow_specification' 'zone_identifier' 'flow_fraction' 'from_identifier'};      % header for the airflow specification in the data file
      header_key_str@char = 'key';
      header_value_str@char = 'value';
      header_zone_identifier_str@char = 'zone_identifier';
      header_flow_fraction_str@char = 'flow_fraction';
      header_from_identifier_str@char = 'from_identifier';
      
      % AHU key specifications
      hasERC_str@char = 'hasERC';                                  % heat exchanger(ERC) tag for the parsing of the AHU specification
      ERCefficiency_str@char = 'ERCefficiency';                    % heat exchanger(ERC) efficiency tag
      hasEvapCooler_str@char = 'hasEvapCooler';                    % evaporative cooler tag
      evapCoolerEfficiency_str@char = 'EvapCoolerEfficiency';      % evaporative cooler efficiency tag
      hasHeater_str@char = 'hasHeater';                            % heater tag
      hasCooler_str@char = 'hasCooler';                            % cooler tag
      has_AHU_Tin_str@char = 'has_AHU_Tin';                        % source temperature tag
      AHU_Tin_str@char = 'Tin';                                    % source temperature tag
      
      % signal specifications
      ERC_str@char = 'ERC';
      noERC_str@char = 'noERC';
      evapCooler_str@char = 'evapCooler';
      deltaWB_str@char = 'Dwb';
      heater_str@char = 'heater';
      cooler_str@char = 'cooler';
      
      % properties for constraints generation in order to identify constraint and cost parameter fields
      mdot_min_str@char = 'mdot_min';
      mdot_max_str@char = 'mdot_max';
      Q_heat_min_str@char = 'Q_heat_min';
      Q_heat_max_str@char = 'Q_heat_max';
      Q_cool_min_str@char = 'Q_cool_min';
      Q_cool_max_str@char = 'Q_cool_max';
      T_supply_min_str@char = 'T_supply_min';
      T_supply_max_str@char = 'T_supply_max';
      v_fullModel_str@char = 'v_fullModel';
      mdotERC_nonneg_str@char = 'mdotERC_nonneg';
      mdotNoERC_nonneg_str@char = 'mdotNoERC_nonneg';
      evapCooler_nonneg_str@char = 'evapCooler_nonneg';
      evapCooler_max_str@char = 'evapCooler_max';
      x_str@char = 'x';
      
   end
   
   properties(SetAccess=private)
      
      has_AHU_Tin@logical = false;                                                                 % flag indicating if source temperature to AHU is different from ambient
      hasERC@logical = false;                                                                      % flag indicating if AHU has a heat exchanger
      ERCefficiency@double = 0;                                                                    % efficiency of the heat exchanger
      hasHeater@logical = false;                                                                   % flag indicating if AHU has a heater
      hasCooler@logical = false;                                                                   % flag indicating if AHU has a cooler
      hasEvapCooler@logical = false;                                                               % flag indicating if AHU has an evaporative Cooler
      evapCoolerEfficiency@double = 0;                                                             % efficiency of the evaporative cooler
      return_zones = struct('identifier',{},'total_return_flow_fraction',{});                      % stores the AHU return zones and their flow fraction
      supply_zones = struct('identifier',{},'total_supply_flow_fraction',{});                      % stores the AHU supply zones and their flow fraction
      airflowSpecs = struct('zone_identifier',{},'flow_fraction',{},'from_identifier',{});         % stores full airflow specification
      
   end % (SetAccess=private)
   
   methods
      
      function obj = AHU(Building,EHF_identifier,source_file)
         
         % check arguments
         if ~isa(Building,Constants.building_name_str)
            error('AHU:Argument','Argument error. Argument 1 is required to be of type ''%s''.\n',Constants.building_name_str);
         end
         
         % check if building has a thermal model
         if isempty(Building.building_model.thermal_submodel)
            error('AHU:NoThermalModel','%s with %s required.\n',Constants.building_name_str,Constants.thermalmodel_name_str);
         end
         
         % check if file exists
         if ~(exist(source_file,'file') == 2)
            error('AHU:UnknownFile','File ''%s'' does not exist. Valid file file path (string) required. Full file path recommended.\n',source_file);
         end
         
         obj.identifiers = Identifier;
         obj.EHF_identifier = EHF_identifier;
         obj.source_file = source_file;
         obj = obj.generateModel(Building);
         obj.checkNan();
         
      end
      
      function [Fx,Fu,Fv,g,constraint_identifiers] = getConstraintsMatrices(obj,parameters)
         
         p = parameters;
         
         % Generate constraint matrices
         n_x = length(obj.identifiers.x);
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         n_c = length(obj.identifiers.constraints);
         
         % check if min/max fields in parameters are existent and make sense
         chkFieldsMinMaxVal{1,1} = obj.mdot_min_str;
         chkFieldsMinMaxVal{1,2} = obj.mdot_max_str;
         chkFieldsMinMaxVal{1,3} = @(x)x>=0;
         chkFieldsMinMaxVal{2,1} = obj.T_supply_min_str;
         chkFieldsMinMaxVal{2,2} = obj.T_supply_max_str;
         chkFieldsMinMaxVal{2,3} = @(x)true;
         
         if obj.hasHeater          
            chkFieldsMinMaxVal{end+1,1} = obj.Q_heat_min_str;
            chkFieldsMinMaxVal{end,2}   = obj.Q_heat_max_str;
            chkFieldsMinMaxVal{end,3} = @(x)x>=0;      
         end
         
         if obj.hasCooler
            
            chkFieldsMinMaxVal{end+1,1} = obj.Q_cool_min_str;
            chkFieldsMinMaxVal{end,2}   = obj.Q_cool_max_str;
            chkFieldsMinMaxVal{end,3} = @(x)x>=0;
            
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
         
         % check non min/max fields
         chkFields = {obj.x_str,obj.identifiers_fullModel_str,obj.v_fullModel_str};
         for i=1:length(chkFields)
            if ~isfield(p,chkFields{i})
               error('getContraintsMatrices:parameters','Field %s not found.\n',[obj.EHF_identifier,'.',chkFields{i}]);
            end
         end
         
         % extract everything from full model disturbances: v_AMB or v_AHU_Tin / v_DeltaWB
         if obj.has_AHU_Tin
            idx_v_AMB_or_v_AHU_Tin = getIdIndex(p.(obj.identifiers_fullModel_str).v,strcat(Constants.disturbance_variable,'_',obj.EHF_identifier,'_',obj.AHU_Tin_str));
         else
            idx_v_AMB_or_v_AHU_Tin = getIdIndex(p.(obj.identifiers_fullModel_str).v,strcat(Constants.disturbance_variable,'_',Constants.var_ambient_identifier));
         end
         v_AMB_or_v_AHU_Tin = p.(obj.v_fullModel_str)(idx_v_AMB_or_v_AHU_Tin);
         
         if obj.hasEvapCooler
            idx_v_DeltaWB = getIdIndex(p.(obj.identifiers_fullModel_str).v,strcat(Constants.disturbance_variable,'_',obj.EHF_identifier,'_',obj.deltaWB_str));
            v_DeltaWB = p.(obj.v_fullModel_str)(idx_v_DeltaWB);
         end
         
         Fx = zeros(n_c,n_x);
         Fu = zeros(n_c,n_u);
         Fv = zeros(n_c,n_v);
         g = zeros(n_c,1);
         
         C_air = Constants.C_air;
         
         % ---------------------------------------------------------------------------------------------------------------------
         % min and max on total supply air massflow
         idx_c_airmass_min = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.mdot_min_str));
         idx_c_airmass_max = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.mdot_max_str));
         idx_u_noERC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.noERC_str));
         
         % noERC
         Fu(idx_c_airmass_min,idx_u_noERC) = Fu(idx_c_airmass_min,idx_u_noERC)             - 1;
         Fu(idx_c_airmass_max,idx_u_noERC) = Fu(idx_c_airmass_max,idx_u_noERC)             + 1;
         g(idx_c_airmass_min,1) = g(idx_c_airmass_min,1)                                   - p.(obj.mdot_min_str);
         g(idx_c_airmass_max,1) = g(idx_c_airmass_max,1)                                   + p.(obj.mdot_max_str);
         
         % ERC
         if obj.hasERC
            idx_u_ERC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.ERC_str));
            Fu(idx_c_airmass_min,idx_u_ERC) = Fu(idx_c_airmass_min,idx_u_ERC)             - 1;
            Fu(idx_c_airmass_max,idx_u_ERC) = Fu(idx_c_airmass_max,idx_u_ERC)             + 1;    
         end
         
         % ---------------------------------------------------------------------------------------------------------------------
         % non-negativity on mdotNoERC
         idx_mdotNoERC_nonneg = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.mdotNoERC_nonneg_str));
         
         Fu(idx_mdotNoERC_nonneg,idx_u_noERC) = Fu(idx_mdotNoERC_nonneg,idx_u_noERC)       - 1;
         
         % ---------------------------------------------------------------------------------------------------------------------
         % non-negativity on mdotERC
         if obj.hasERC
            
            idx_mdotERC_nonneg = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.mdotERC_nonneg_str));
            idx_u_ERC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.ERC_str));
            
            Fu(idx_mdotERC_nonneg,idx_u_ERC) = Fu(idx_mdotERC_nonneg,idx_u_ERC)           - 1;
            
         end
         
         % ---------------------------------------------------------------------------------------------------------------------
         % min/max constraints on heater
         if obj.hasHeater
            
            idx_c_heater_min = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.Q_heat_min_str));
            idx_c_heater_max = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.Q_heat_max_str));
            idx_u_heater = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.heater_str));
            
            Fu(idx_c_heater_min,idx_u_heater) = Fu(idx_c_heater_min,idx_u_heater)          - 1;
            Fu(idx_c_heater_max,idx_u_heater) = Fu(idx_c_heater_max,idx_u_heater)          + 1;
            
            g(idx_c_heater_min,1) = g(idx_c_heater_min,1)                                  - p.(obj.Q_heat_min_str);
            g(idx_c_heater_max,1) = g(idx_c_heater_max,1)                                  + p.(obj.Q_heat_max_str);
            
         end
         
         % ---------------------------------------------------------------------------------------------------------------------
         % min/max constraints on cooler
         if obj.hasCooler
            
            idx_c_cooler_min = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.Q_cool_min_str));
            idx_c_cooler_max = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.Q_cool_max_str));
            idx_u_cooler = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.cooler_str));
            
            Fu(idx_c_cooler_min,idx_u_cooler) = Fu(idx_c_cooler_min,idx_u_cooler)            - 1;
            Fu(idx_c_cooler_max,idx_u_cooler) = Fu(idx_c_cooler_max,idx_u_cooler)            + 1;
            
            g(idx_c_cooler_min,1) = g(idx_c_cooler_min,1)                                    - p.(obj.Q_cool_min_str);
            g(idx_c_cooler_max,1) = g(idx_c_cooler_max,1)                                    + p.(obj.Q_cool_max_str);
            
         end
         
         % ---------------------------------------------------------------------------------------------------------------------
         % min/max constraints on evaporative cooler
         if obj.hasEvapCooler
            
            idx_evapCooler_nonneg = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.evapCooler_nonneg_str));
            idx_evapCooler_max = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.evapCooler_max_str));
            idx_u_ERC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.ERC_str));
            idx_u_evapC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.evapCooler_str));
            
            Fu(idx_evapCooler_nonneg,idx_u_evapC) = Fu(idx_evapCooler_nonneg,idx_u_evapC)         - 1;
            Fu(idx_evapCooler_max,idx_u_evapC) = Fu(idx_evapCooler_max,idx_u_evapC)               + 1;
            Fu(idx_evapCooler_max,idx_u_ERC) = Fu(idx_evapCooler_max,idx_u_ERC)                   - 1;
            
         end
         
         % ---------------------------------------------------------------------------------------------------------------------
         % min and max supply temperature
         idx_c_T_supply_min = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.T_supply_min_str));
         idx_c_T_supply_max = getIdIndex(obj.identifiers.constraints,strcat(obj.EHF_identifier,'_',obj.T_supply_max_str));
         
         % compute T_return = sum_k Dflow_k * x_k, k is return zone
         idx_return_zones = find(ismember(obj.identifiers.x,strcat(Constants.state_variable,'_',{obj.return_zones.identifier})));
         T_return = sum([obj.return_zones.total_return_flow_fraction]'.*p.(obj.x_str)(idx_return_zones));
         
         % u_noERC
         Fu(idx_c_T_supply_min,idx_u_noERC) = Fu(idx_c_T_supply_min,idx_u_noERC)             - C_air*v_AMB_or_v_AHU_Tin + C_air*p.(obj.T_supply_min_str);
         Fu(idx_c_T_supply_max,idx_u_noERC) = Fu(idx_c_T_supply_max,idx_u_noERC)             + C_air*v_AMB_or_v_AHU_Tin - C_air*p.(obj.T_supply_max_str);
         
         if obj.hasERC
            
            Fu(idx_c_T_supply_min,idx_u_ERC) = Fu(idx_c_T_supply_min,idx_u_ERC)              - C_air*(obj.ERCefficiency*(T_return-v_AMB_or_v_AHU_Tin) + v_AMB_or_v_AHU_Tin) +  C_air*p.(obj.T_supply_min_str);
            Fu(idx_c_T_supply_max,idx_u_ERC) = Fu(idx_c_T_supply_max,idx_u_ERC)              + C_air*(obj.ERCefficiency*(T_return-v_AMB_or_v_AHU_Tin) + v_AMB_or_v_AHU_Tin) -  C_air*p.(obj.T_supply_max_str);
            
         end
         
         if obj.hasHeater
            
            Fu(idx_c_T_supply_min,idx_u_heater) = Fu(idx_c_T_supply_min,idx_u_heater)       - 1;
            Fu(idx_c_T_supply_max,idx_u_heater) = Fu(idx_c_T_supply_max,idx_u_heater)       + 1;
            
         end
         
         if obj.hasCooler
            
            Fu(idx_c_T_supply_min,idx_u_cooler) = Fu(idx_c_T_supply_min,idx_u_cooler)       + 1;
            Fu(idx_c_T_supply_max,idx_u_cooler) = Fu(idx_c_T_supply_max,idx_u_cooler)       - 1;
            
         end
         
         if obj.hasEvapCooler
            
            idx_u_evapC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.evapCooler_str));
            
            Fu(idx_c_T_supply_min,idx_u_evapC) = Fu(idx_c_T_supply_min,idx_u_evapC)         - (-C_air * obj.ERCefficiency * obj.evapCoolerEfficiency * v_DeltaWB);
            Fu(idx_c_T_supply_max,idx_u_evapC) = Fu(idx_c_T_supply_max,idx_u_evapC)         + (-C_air * obj.ERCefficiency * obj.evapCoolerEfficiency * v_DeltaWB);
            
         end
         
         constraint_identifiers = obj.identifiers.constraints;
         
      end % getConstraintsMatrices
      
      function [cu] = getCostVector(obj,parameters) 
         

         p = parameters;
         cu = zeros(length(obj.identifiers.u),1);
         
         fn = 'costPerKgAirTransported';
         if ~isfield(p,fn)
            error('getCostVector:parameters','Field %s not found.\n',[obj.EHF_identifier,'.',fn]);
         end
         if numel(p.(fn)) ~= 1 || ~isnumeric(p.(fn))
            error('getCostVector:parameters','Bad parameter values in fields %s.\n',[obj.EHF_identifier,'.',fn]);
         end
         if p.(fn)<=0
            error('getCostVector:parameters','Parameter value %s must be positive.\n',[obj.EHF_identifier,'.',fn]);
         end 
         fn_m = fn;

         if obj.hasHeater
            fn = 'costPerJouleHeated';
            if ~isfield(p,fn)
               error('getCostVector:parameters','Field %s not found.\n',[obj.EHF_identifier,'.',fn]);
            end
            if numel(p.(fn)) ~= 1 || ~isnumeric(p.(fn))
               error('getCostVector:parameters','Bad parameter values in fields %s.\n',[obj.EHF_identifier,'.',fn]);
            end
            if p.(fn)<=0
               error('getCostVector:parameters','Parameter value %s must be positive.\n',[obj.EHF_identifier,'.',fn]);
            end 
            fn_h = fn;
         end
         if obj.hasCooler
            fn = 'costPerJouleCooled';
            if ~isfield(p,fn)
               error('getCostVector:parameters','Field %s not found.\n',[obj.EHF_identifier,'.',fn]);
            end
            if numel(p.(fn)) ~= 1 || ~isnumeric(p.(fn))
               error('getCostVector:parameters','Bad parameter values in fields %s.\n',[obj.EHF_identifier,'.',fn]);
            end
            if p.(fn)<=0
               error('getCostVector:parameters','Parameter value %s must be positive.\n',[obj.EHF_identifier,'.',fn]);
            end      
            fn_c = fn;
         end
         if obj.hasEvapCooler
            fn = 'costPerKgCooledByEvapCooler';
            if ~isfield(p,fn)
               error('getCostVector:parameters','Field %s not found.\n',[obj.EHF_identifier,'.',fn]);
            end
            if numel(p.(fn)) ~= 1 || ~isnumeric(p.(fn))
               error('getCostVector:parameters','Bad parameter values in fields %s.\n',[obj.EHF_identifier,'.',fn]);
            end
            if p.(fn)<=0
               error('getCostVector:parameters','Parameter value %s must be positive.\n',[obj.EHF_identifier,'.',fn]);
            end      
            fn_evap = fn;
         end         
         if obj.hasERC         
            idx_u_mdot_erc = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.ERC_str));
            cu(idx_u_mdot_erc) = cu(idx_u_mdot_erc) + p.(fn_m)*parameters.Ts_hrs;
         end
         idx_u_mdot_noEerc = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.noERC_str));
         cu(idx_u_mdot_noEerc) = cu(idx_u_mdot_noEerc) + p.(fn_m)*parameters.Ts_hrs;
            
         if obj.hasHeater
            idx_u_heater = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.heater_str));
            cu(idx_u_heater) = cu(idx_u_heater) + p.(fn_h)*parameters.Ts_hrs;
         end
         
         if obj.hasCooler
            idx_u_rad = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.cooler_str));
            cu(idx_u_rad) = cu(idx_u_rad) + p.(fn_c)*parameters.Ts_hrs;
         end
         
         if obj.hasEvapCooler
            idx_u_evapCooler = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.evapCooler_str));
            cu(idx_u_evapCooler) = cu(idx_u_evapCooler) + p.(fn_evap)*parameters.Ts_hrs;
         end
         
                  
      end % getCostVector
      
      
   end % methods
   
   methods(Access=private)
      
      function obj = generateModel(obj,building)
         
         headers = [{obj.AHU_spec_file_header}; {obj.AHU_airflow_spec_file_header}];
         [dataTables,anchorIdxs] = getDataTablesFromFile(obj.source_file,headers);
         dataTable_spec = dataTables{1};
         dataTable_airflow = dataTables{2};
         anchorIdxs_spec.row = anchorIdxs.row(1);
         anchorIdxs_spec.col = anchorIdxs.col(1);
         
         obj = obj.setSpecs(dataTable_spec,anchorIdxs_spec);
         obj = obj.generateIdentifiers(building);
         obj = obj.setAirflowSpecs(dataTable_airflow,building);
         
         % initialize matrix Bq_u according to number of controlled windows
         % get dimensions and initalize matrices
         n_x = length(obj.identifiers.x); % we assume that n_q = n_x
         n_q = length(obj.identifiers.q);
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         
         Aq = zeros(n_q,n_x);
         Bq_u = zeros(n_q,n_u);
         Bq_v = zeros(n_q,n_v);
         Bq_vu = zeros(n_q,n_v,n_u);
         Bq_xu = zeros(n_q,n_x,n_u);
         
         % constant indices
         idx_u_noERC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.noERC_str));
         
         if obj.has_AHU_Tin
            idx_v_AMBorAHUTin = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',obj.EHF_identifier,'_',obj.AHU_Tin_str));
         else
            idx_v_AMBorAHUTin = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',Constants.var_ambient_identifier));
         end
         
         % heat capacitiy of air
         C_air = Constants.C_air;
         
         % set coefficients to model the effects of the AHU on zones that directly get supplied by it
         for i = 1:length(obj.supply_zones)
            
            zone_q_id = strcat(Constants.heat_flux_variable,'_',obj.supply_zones(i).identifier);
            zone_x_id = strcat(Constants.state_variable,'_',obj.supply_zones(i).identifier);
            
            % noERC part
            idx_q_zone = getIdIndex(obj.identifiers.q,zone_q_id);
            idx_x_zone = getIdIndex(obj.identifiers.x,zone_x_id);
            
            Bq_vu(idx_q_zone,idx_v_AMBorAHUTin,idx_u_noERC) = Bq_vu(idx_q_zone,idx_v_AMBorAHUTin,idx_u_noERC)          + obj.supply_zones(i).total_supply_flow_fraction*C_air;
            Bq_xu(idx_q_zone,idx_x_zone,idx_u_noERC) = Bq_xu(idx_q_zone,idx_x_zone,idx_u_noERC)                        - obj.supply_zones(i).total_supply_flow_fraction*C_air;
            
            % Set ERC part
            if obj.hasERC
               idx_u_ERC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.ERC_str));
               
               % all the inflow
               Bq_vu(idx_q_zone,idx_v_AMBorAHUTin,idx_u_ERC) = Bq_vu(idx_q_zone,idx_v_AMBorAHUTin,idx_u_ERC)          + obj.supply_zones(i).total_supply_flow_fraction*C_air*(1-obj.ERCefficiency);
               
               % return zones part
               for j=1:length(obj.return_zones)
                  idx_x_return_zone = getIdIndex(obj.identifiers.x,strcat(Constants.state_variable,'_',obj.return_zones(j).identifier));
                  Bq_xu(idx_q_zone,idx_x_return_zone,idx_u_ERC) = Bq_xu(idx_q_zone,idx_x_return_zone,idx_u_ERC)      + obj.supply_zones(i).total_supply_flow_fraction*C_air*obj.ERCefficiency*obj.return_zones(j).total_return_flow_fraction;
               end
               
               % all the outflow
               Bq_xu(idx_q_zone,idx_x_zone,idx_u_ERC) = Bq_xu(idx_q_zone,idx_x_zone,idx_u_ERC)                        - obj.supply_zones(i).total_supply_flow_fraction*C_air;
            end
            
            % set heater part
            if obj.hasHeater
               idx_u_heater = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.heater_str));
               
               Bq_u(idx_q_zone,idx_u_heater) = Bq_u(idx_q_zone,idx_u_heater)                                          + obj.supply_zones(i).total_supply_flow_fraction;
            end
            
            % set cooler part
            if obj.hasCooler
               idx_u_cooler = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.cooler_str));
               
               Bq_u(idx_q_zone,idx_u_cooler) = Bq_u(idx_q_zone,idx_u_cooler)                                          - obj.supply_zones(i).total_supply_flow_fraction;
            end
            
            % set evapCooler part
            if obj.hasEvapCooler && obj.hasERC;
               idx_v_wb = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',obj.EHF_identifier,'_',obj.deltaWB_str));
               idx_u_evapC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.evapCooler_str));
               Bq_vu(idx_q_zone,idx_v_wb,idx_u_evapC) = Bq_vu(idx_q_zone,idx_v_wb,idx_u_evapC)                        - obj.supply_zones(i).total_supply_flow_fraction*C_air*obj.ERCefficiency*obj.evapCoolerEfficiency;
            end
            
         end
         
         % consider air flow between zones
         for i = 1:length(obj.airflowSpecs)
            
            if ~strcmp(obj.airflowSpecs(i).from_identifier,obj.AHU_key)
               
               zone_q_id = strcat(Constants.heat_flux_variable,'_',obj.airflowSpecs(i).zone_identifier);
               zone_x_id = strcat(Constants.state_variable,'_',obj.airflowSpecs(i).zone_identifier);
               zone_x_id_from = strcat(Constants.state_variable,'_',obj.airflowSpecs(i).from_identifier);
               flow_fraction = obj.airflowSpecs(i).flow_fraction;
               
               idx_q_zone = getIdIndex(obj.identifiers.q,zone_q_id);
               idx_x_zone = getIdIndex(obj.identifiers.x,zone_x_id);
               idx_x_zone_From = getIdIndex(obj.identifiers.x,zone_x_id_from);
               
               % noERC part
               Bq_xu(idx_q_zone,idx_x_zone,idx_u_noERC) = Bq_xu(idx_q_zone,idx_x_zone,idx_u_noERC)                     - flow_fraction*C_air;
               Bq_xu(idx_q_zone,idx_x_zone_From,idx_u_noERC) = Bq_xu(idx_q_zone,idx_x_zone_From,idx_u_noERC)           + flow_fraction*C_air;
               
               % ERC part
               if obj.hasERC
                  idx_u_ERC = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.ERC_str));
                  
                  Bq_xu(idx_q_zone,idx_x_zone,idx_u_ERC) = Bq_xu(idx_q_zone,idx_x_zone,idx_u_ERC)                    - flow_fraction*C_air;
                  Bq_xu(idx_q_zone,idx_x_zone_From,idx_u_ERC) = Bq_xu(idx_q_zone,idx_x_zone_From,idx_u_ERC)          + flow_fraction*C_air;
               end
            end
         end
         
         obj.Aq = Aq;
         obj.Bq_u = Bq_u;
         obj.Bq_v = Bq_v;
         obj.Bq_vu = Bq_vu;
         obj.Bq_xu = Bq_xu;
         
         
      end % generateModel
      
      function obj = setAirflowSpecs(obj,dataTable_flow,building)
         
         header = dataTable_flow(1,:);
         body = dataTable_flow(2:end,:);
         
         idx_zone_id = getIdIndex(header,obj.header_zone_identifier_str);
         idx_flow_frac = getIdIndex(header,obj.header_flow_fraction_str);
         idx_from_id = getIdIndex(header,obj.header_from_identifier_str);
         
         
         
         allZoneIds = {building.thermal_model_data.zones.identifier};
         
         for i=1:size(body,1)
            zone_identifier = body{i,idx_zone_id};
            if ~any(strcmp(zone_identifier,allZoneIds))
               error('Could not find %s in zones.\n',zone_identifier);
            end
            flow_fraction = str2double(ThermalModelData.check_value(body{i,idx_flow_frac},false));
            
            from_identifier = body{i,idx_from_id};
            if ~strcmp(from_identifier,obj.AHU_key) && ~any(strcmp(from_identifier,allZoneIds))
               error('Could not find %s in zones.\n',from_identifier);
            end
            obj.airflowSpecs(i).zone_identifier = zone_identifier;
            obj.airflowSpecs(i).flow_fraction = flow_fraction;
            obj.airflowSpecs(i).from_identifier = from_identifier;
            
         end
         
         airflowZones = setdiff(unique([{obj.airflowSpecs.zone_identifier},{obj.airflowSpecs.from_identifier}]),obj.AHU_key);
         
         % check: no negative net flow per zone
         % set return_zones
         total_return_flow = 0;
         cnt_return_zones = 1;
         for i=1:length(airflowZones)
            
            z = airflowZones{i};
            idx_in = find(strcmp(z,{obj.airflowSpecs.zone_identifier}));
            idx_out = find(strcmp(z,{obj.airflowSpecs.from_identifier}));
            flow_in = sum([obj.airflowSpecs(idx_in).flow_fraction]);
            flow_out = sum([obj.airflowSpecs(idx_out).flow_fraction]);
            total_return_flow_fraction = flow_in-flow_out;
            if total_return_flow_fraction<0
               error('getAirflowInfo:FlowBalance','Total AHU outflow of zone %s is larger than total AHU inflow.\n',z);
            elseif total_return_flow_fraction > 0
               obj.return_zones(cnt_return_zones).identifier = z;
               obj.return_zones(cnt_return_zones).total_return_flow_fraction = total_return_flow_fraction;
               cnt_return_zones = cnt_return_zones+1;
               total_return_flow = total_return_flow+total_return_flow_fraction;
            end
            
         end
         
         % check total return flow
         if total_return_flow ~= 1
            error('getAirflowInfo:AHU_ret','Total AHU return is not equal to 1: AHU return = %f.\n',total_return_flow);
         end
         
         total_supply_flow = 0;
         cnt_supply_zones = 1;
         for i=1:length(airflowZones)
            z = airflowZones{i};
            idx_zone = find(strcmp(z,{obj.airflowSpecs.zone_identifier}));
            idx_AHUin = find(strcmp(obj.AHU_key,{obj.airflowSpecs.from_identifier}));
            idx_zoneAHUin = intersect(idx_AHUin,idx_zone);
            if ~isempty(idx_zoneAHUin)
               total_supply_flow_fraction = sum([obj.airflowSpecs(idx_zoneAHUin).flow_fraction]);
               obj.supply_zones(cnt_supply_zones).identifier = z;
               obj.supply_zones(cnt_supply_zones).total_supply_flow_fraction = total_supply_flow_fraction;
               cnt_supply_zones = cnt_supply_zones+1;
               total_supply_flow = total_supply_flow+total_supply_flow_fraction;
            end
         end
         
         % check total supply flow
         if total_return_flow ~= 1
            error('getAirflowInfo:AHU_sup','Total AHU return is not equal to 1: AHU supply = %f.\n',total_supply_flow);
         end
         
      end % setAirflowSpecs
      
      function obj = setSpecs(obj,dataTable_spec,anchorIdxs_spec)
         
         
         header = dataTable_spec(1,:);
         body = dataTable_spec(2:end,:);
         
         requiredSpecs = {obj.hasERC_str,...
            obj.ERCefficiency_str,...
            obj.hasEvapCooler_str,...
            obj.evapCoolerEfficiency_str,...
            obj.hasHeater_str,...
            obj.hasCooler_str,...
            obj.has_AHU_Tin_str};
         
         allowedValues = {'bool','in0To1','bool','in0To1','bool','bool','bool'};
         
         idx_key = getIdIndex(header,obj.header_key_str);
         idx_value = getIdIndex(header,obj.header_value_str);
         
         for i=1:length(requiredSpecs)
            rS = requiredSpecs{i};
            aV = allowedValues{i};
            rowIdxBody = find(strcmpi(rS,body(:,idx_key))); % keys are in the second row
            if numel(rowIdxBody) ~= 1
               error('XLSFile:Keys','In file ''%s'': Missing AHU specification key/s %s.\n',sprintf('%s',regexprep(obj.source_file,'\','\\')),rS);
            end
            valStr = body(rowIdxBody,idx_value); % values are in the third row
            valNum = str2double(valStr);
            if strcmp(aV,'bool')
               if valNum ~= 1 && valNum ~= 0
                  error('XLSFile:Value',[Constants.error_msg_xlsFile('',obj.source_file,anchorIdxs_spec.row+i+1,anchorIdxs_spec.row+2),' must be 0 or 1']);
               end
               val = valNum;
            elseif strcmp(aV,'in0To1')
               if valNum > 1 || valNum < 0
                  error('XLSFile:Value',[Constants.error_msg_xlsFile('',obj.source_file,anchorIdxs_spec.row+i+1,anchorIdxs_spec.row+2),' must be in[0,1]']);
               end
               val = valNum;
            elseif strcmp(aV,'str')
               val = valStr;
            else
               error('Did not recognize allowed Value%s\n',aV);
            end
            specs.(rS) = val;
         end
         
         
         % set efficiencies to zero if no specific system is available
         if ~specs.(obj.hasERC_str)
            specs.(obj.ERCefficiency_str) = 0;
         end
         
         if ~specs.(obj.hasEvapCooler_str)
            specs.(obj.evapCoolerEfficiency_str) = 0;
         end
         
         obj.has_AHU_Tin = specs.(obj.has_AHU_Tin_str) == 1;
         obj.hasERC = specs.(obj.hasERC_str) == 1;
         obj.ERCefficiency =  specs.(obj.ERCefficiency_str);
         obj.hasHeater = specs.(obj.hasHeater_str) == 1;
         obj.hasCooler = specs.(obj.hasCooler_str) == 1;
         obj.hasEvapCooler = specs.(obj.hasEvapCooler_str) == 1;
         obj.evapCoolerEfficiency = specs.(obj.evapCoolerEfficiency_str);
         
         
         if obj.hasEvapCooler && ~obj.hasERC
            error('Cannot use evaporative cooler without ERC');
         end
         
         
      end % setSpecs
      
      function obj = generateIdentifiers(obj,building)
         
         obj.identifiers = Identifier;
         
         obj.identifiers.x = building.building_model.identifiers.x;
         obj.identifiers.q = building.building_model.identifiers.q;
         
         obj.identifiers.u = [obj.identifiers.u ; strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.noERC_str)];
         
         % min and max supply air massflow
         obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.mdot_min_str)];
         obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.mdot_max_str)];
         obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.mdotNoERC_nonneg_str)];
         
         if obj.has_AHU_Tin
            obj.identifiers.v = [obj.identifiers.v;strcat(Constants.disturbance_variable,'_',obj.EHF_identifier,'_',obj.AHU_Tin_str)];
         else
            obj.identifiers.v = [obj.identifiers.v;strcat(Constants.disturbance_variable,'_',Constants.var_ambient_identifier)];
         end
         
         if obj.hasERC
            obj.identifiers.u = [obj.identifiers.u;strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.ERC_str)];
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.mdotERC_nonneg_str)];
         end
         
         if obj.hasEvapCooler
            obj.identifiers.u = [obj.identifiers.u;strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.evapCooler_str)];
            obj.identifiers.v = [obj.identifiers.v;strcat(Constants.disturbance_variable,'_',obj.EHF_identifier,'_',obj.deltaWB_str)];
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.evapCooler_nonneg_str)];
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.evapCooler_max_str)];
         end
         
         if obj.hasHeater
            obj.identifiers.u = [obj.identifiers.u;strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.heater_str)];
            % min and max heater power
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat( obj.EHF_identifier,'_',obj.Q_heat_min_str)];
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat( obj.EHF_identifier,'_',obj.Q_heat_max_str)];
         end
         
         if obj.hasCooler
            obj.identifiers.u = [obj.identifiers.u; strcat(Constants.input_variable,'_',obj.EHF_identifier,'_',obj.cooler_str)];
            % min and max cooler power
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.Q_cool_min_str)];
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.Q_cool_max_str)];
         end
         
         % min and max supply temperature
         obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.T_supply_min_str)];
         obj.identifiers.constraints = [obj.identifiers.constraints;strcat(obj.EHF_identifier,'_',obj.T_supply_max_str)];
         
      end % generateIdentifiers
      
   end % methods(Access=private)
end % classdef


