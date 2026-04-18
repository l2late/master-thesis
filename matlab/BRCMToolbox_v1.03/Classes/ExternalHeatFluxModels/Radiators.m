classdef Radiators < EHFModelBaseClass
   %RADIATORS 	This class represents the Radiator external heat flux model of a building.
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
      radiator_name_str@char = 'Radiators';  % Name of the model
      radiator_identifier@char = 'rad';     % Model signal label tag
      
      % Required file header for the specific model data file
      radiator_file_header@cell =  {'zone_identifier' 'control_identifier'}; % make sure this coincides with below
      header_zone_id_str@char = 'zone_identifier';
      header_u_id_str@char = 'control_identifier';
      
   end
   properties(Access=private)
      
      radiatorSpecs = struct('zone_id',{},'u_id',{},'zone_area',{});
      
   end
   
   methods
      
      function obj = Radiators(Building,EHF_identifier,source_file)
         
         % check arguments
         if ~isa(Building,Constants.building_name_str)
            error('Radiator:Argument','Argument error. Argument 1 is required to be of type ''%s''.\n',Constants.building_name_str);
         end
         
         % check if building has a thermal model
         if isempty(Building.building_model.thermal_submodel)
            error('Radiator:NoThermalModel','%s with %s required.\n',Constants.building_name_str,Constants.thermalmodel_name_str);
         end
         
         % check if file exists
         if ~(exist(source_file,'file') == 2)
            error('Radiator:UnknownFile','File ''%s'' does not exist. Valid file file path (string) required. Full file path recommended.\n',source_file);
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
            
            chkFieldsMinMaxVal{i,1} = ['Q',obj.identifiers.u{i}(2:end),'_min'];
            chkFieldsMinMaxVal{i,2} = ['Q',obj.identifiers.u{i}(2:end),'_max'];
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
      
      function [cu] = getCostVector(obj,parameters)
         
         p = parameters;
         cu = zeros(length(obj.identifiers.u),1);
         fn = 'costPerJouleHeated';
         if ~isfield(p,fn)
            error('getCostVector:parameters','Field %s not found.\n',fn);
         end
         if numel(p.(fn)) ~= 1 || ~isnumeric(p.(fn))
            error('getCostVector:parameters','Bad parameter values in fields %s.\n',[obj.EHF_identifier,'.',fn]);
         end
         if p.(fn)<=0
            error('getCostVector:parameters','Parameter value %s must be positive.\n',[obj.EHF_identifier,'.',fn]);
         end
         
         % The model is as follows
         % q^i_zone_radiator = a_i_zone*u_Radiator_k
         
         for i = 1:length(obj.radiatorSpecs)
            
            idx_u_rad = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.radiator_identifier,'_',obj.radiatorSpecs(i).u_id));
            cu(idx_u_rad) = cu(idx_u_rad) + p.(fn)* obj.radiatorSpecs(i).zone_area;
            
         end
         
         
      end % getCostVector
      
   end % methods
   
   methods(Access=private)
      
      function obj = generateModel(obj,building)
         
         headers = {obj.radiator_file_header};
         [dataTables,anchorIdxs_rad] = getDataTablesFromFile(obj.source_file,headers);
         dataTable_rad = dataTables{1};
         
         
         obj = setRadiatorSpecs(obj,dataTable_rad,anchorIdxs_rad,building);
         obj = generateIdentifiers(obj,building);
         
         
         % get dimensions and initalize matrices
         n_x = length(obj.identifiers.x);
         n_q = length(obj.identifiers.q);
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         
         % we assume that n_q = n_x
         obj.Aq = zeros(n_q,n_x);
         obj.Bq_u = zeros(n_q,n_u);
         obj.Bq_v = zeros(n_q,n_v);
         obj.Bq_vu = zeros(n_q,n_v,n_u);
         obj.Bq_xu = zeros(n_q,n_x,n_u);
         
         % The model is as follows
         % q^i_zone_radiator = a_i_zone*v_Radiator_k
         
         for i = 1:length(obj.radiatorSpecs)
            
            % get zone index
            zone_id = obj.radiatorSpecs(i).zone_id;
            
            % populate Bq_u matrix
            % get indices of the states
            idx_q_zone = getIdIndex(building.building_model.identifiers.q,strcat(Constants.heat_flux_variable,'_',zone_id));
            idx_u_rad = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.radiator_identifier,'_',obj.radiatorSpecs(i).u_id));
            
            obj.Bq_u(idx_q_zone,idx_u_rad) = obj.radiatorSpecs(i).zone_area;
            
            
         end
         
      end % generateModel
      
      function obj = generateIdentifiers(obj,building)
         
         % input identifiers
         obj.identifiers = Identifier;
         obj.identifiers.u = unique(strcat(Constants.input_variable,'_',obj.radiator_identifier,'_',{obj.radiatorSpecs.u_id}'));
         obj.identifiers.x = building.building_model.identifiers.x;
         obj.identifiers.q = building.building_model.identifiers.q;
         
         % constraints
         for i = 1:length(obj.identifiers.u)
            obj.identifiers.constraints = [obj.identifiers.constraints;strcat('Q',obj.identifiers.u{i}(2:end),'_min');strcat('Q',obj.identifiers.u{i}(2:end),'_max')];
         end
         
      end
      
      function obj = setRadiatorSpecs(obj,dataTable_rad,anchorIdxs_rad,building)
         
         header = dataTable_rad(1,:);
         body = dataTable_rad(2:end,:);
         
         idx_zone_id = getIdIndex(header,obj.header_zone_id_str);
         idx_u_id = getIdIndex(header,obj.header_u_id_str);
         
         % get valid specifications
         for i = 1:size(body,1)
            
            zone_id = ThermalModelData.check_identifier(body{i,idx_zone_id},Zone.key);
            u_id = ThermalModelData.check_special_identifier(body{i,idx_u_id});
            if isempty(zone_id)
               error('setRadiatorSpecs:Identifier', 'Expected zone identifier at row %d and column %d \n',anchorIdxs_rad.row+i+1,anchorIdxs_rad.col+idx_zone_id)
            end
            if isempty(u_id) && ~isempty(body{i,idx_u_id})
               error('setRadiatorSpecs:Identifier', 'Invalid input identifier at row %d and column %d \n',anchorIdxs_rad.row+i+1,anchorIdxs_rad.col+idx_zone_id)
            end
            if ~isempty(u_id)
               
               % check if zone identifier exists in current building
               unknown_zone = setdiff(zone_id,{building.thermal_model_data.zones.identifier});
               
               if ~isempty(unknown_zone)
                  error('setRadiatorSpecs:Consistency','%s identifier of file ''%s'' not contained in building Data:\nColumn ''%s'' at row %d: ''%s''\n',Constants.zone_name_str,sprintf('%s',regexprep(obj.source_file,'\','\\')),obj.header_zone_id_str,anchorIdxs_rad.row+i+1,zone_id);
               end
               
               idx_zone = building.thermal_model_data.getZoneIdxFromIdentifier(zone_id);
               
               obj.radiatorSpecs(end+1).zone_id = zone_id;
               obj.radiatorSpecs(end).u_id = u_id;
               obj.radiatorSpecs(end).zone_area = building.thermal_model_data.evalStr(building.thermal_model_data.zones(idx_zone).area);
               
            end
            
            
         end
         
         n_Rads = length(obj.radiatorSpecs);
         
      end % setRadiatorSpecs
      
   end  % methods(Access=private)
end % classdef
