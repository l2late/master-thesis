classdef InternalGains < EHFModelBaseClass
   %INTERNALGAINS 	This class represents the Internal Gain external heat flux model of a building.
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
      
      % model specific conventions
      internal_gains_name_str@char = 'Internal gains';    % model name
      internal_gains_identifier@char = 'IG';             % model signal labe tag
      
      % Required file header for the specific model data file
      internal_gains_file_header@cell = { 'zone_identifier' 'disturbance_identifier'}; % make sure this coincides with below
      header_zone_id_str = 'zone_identifier';
      header_v_id_str = 'disturbance_identifier';     
   end
   
   properties(Access=private)
      igSpecs = struct('zone_id',{},'v_id',{});    
   end
   
   methods
      
      function obj = InternalGains(Building,EHF_identifier,source_file)
         
         % check arguments
         if ~isa(Building,Constants.building_name_str)
            error('InternalGain:Argument','Argument error. Argument 1 is required to be of type ''%s''.\n',Constants.building_name_str);
         end
         
         % check if building has a thermal model
         if isempty(Building.building_model.thermal_submodel)
            error('InternalGain:NoThermalModel','%s with %s required.\n',Constants.building_name_str,Constants.thermalmodel_name_str);
         end
         
         % check if file exists
         if ~(exist(source_file,'file') == 2)
            error('InternalGain:UnknownFile','File ''%s'' does not exist. Valid file file path (string) required. Full file path recommended.\n',source_file);
         end
         
         obj.identifiers = Identifier;
         obj.EHF_identifier = EHF_identifier;
         obj.source_file = source_file;
         obj = obj.generateModel(Building);
         obj.checkNan();
         
      end
      
      function [Fx,Fu,Fv,g,constraint_identifiers] = getConstraintsMatrices(obj,constraintsParameters) %#ok<INUSD>
         
         n_x = length(obj.Aq);
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         n_c = length(obj.identifiers.constraints);
         Fx = zeros(n_c,n_x);
         Fu = zeros(n_c,n_u);
         Fv = zeros(n_c,n_v);
         g = zeros(n_c,1);
         constraint_identifiers = obj.identifiers.constraints;
         
      end % getConstraintsMatrices
      
      function [cu] = getCostVector(obj,parameters)  %#ok<INUSD>
         
         cu = zeros(length(obj.identifiers.u),1);
       
      end % getCostVector
      
   end % methods
   
   methods(Access=private)
      
      function obj = generateModel(obj,building)
         
         headers = {obj.internal_gains_file_header};
         [dataTables,anchorIdxs_ig] = getDataTablesFromFile(obj.source_file,headers);
         dataTable_ig = dataTables{1};
         
         
         obj = setIGSpecs(obj,dataTable_ig,anchorIdxs_ig,building);
         obj = generateIdentifiers(obj,building);
         
         
         % get dimensions and initalize matrices
         n_x = length(obj.identifiers.x);
         n_q = length(obj.identifiers.q); % What does q represent? External Heat Fluxes (EHF)
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         
         % we assume that n_q = n_x
         obj.Aq = zeros(n_q,n_x);
         obj.Bq_u = zeros(n_q,n_u);
         obj.Bq_v = zeros(n_q,n_v);
         obj.Bq_vu = zeros(n_q,n_v,n_u);
         obj.Bq_xu = zeros(n_q,n_x,n_u);
         
         % The model is as follows
         % q^i_zone_IG = a^i * v_IG
         
         for i = 1:length(obj.igSpecs)
            
            % get zone index
            zone_id = obj.igSpecs(i).zone_id;
            idx_zone = building.thermal_model_data.getZoneIdxFromIdentifier(zone_id);
            
            % populate Bq_u matrix
            % get indices of the states
            idx_q_zone = getIdIndex(obj.identifiers.q,strcat(Constants.heat_flux_variable,'_', zone_id));
            idx_v_IG = getIdIndex(obj.identifiers.v,strcat(Constants.disturbance_variable,'_',obj.internal_gains_identifier,'_', obj.igSpecs(i).v_id));
            
            % assign zone area
            % since zone identifiers are unique, we just assign the area
            obj.Bq_v(idx_q_zone, idx_v_IG) = str2double(building.thermal_model_data.zones(idx_zone).area);
         end
         
      end % generateModel
      
      function obj = generateIdentifiers(obj,building)
         
         obj.identifiers = Identifier;
         obj.identifiers.x = building.building_model.identifiers.x;
         obj.identifiers.q = building.building_model.identifiers.q;
         obj.identifiers.v = unique(strcat(Constants.disturbance_variable,'_',obj.internal_gains_identifier,'_',reshapeVector({obj.igSpecs.v_id},'col')));
         
      end
      
      function obj = setIGSpecs(obj,dataTable_ig,anchorIdxs_ig,building)
         
         header = dataTable_ig(1,:);
         body = dataTable_ig(2:end,:);
         
         idx_zone_id = getIdIndex(header,obj.header_zone_id_str);
         idx_v_id = getIdIndex(header,obj.header_v_id_str);
         
         % get valid specifications
         for i = 1:size(body,1)
            
            zone_id = ThermalModelData.check_identifier(body{i,idx_zone_id},Zone.key);
            v_id = ThermalModelData.check_special_identifier(body{i,idx_v_id});
            if isempty(zone_id)
               error('setIGSpecs:Identifier', 'Expected zone identifier at row %d and column %d \n',anchorIdxs_ig.row+i+1, anchorIdxs_ig.col+idx_zone_id)
            end
            if isempty(v_id) && ~isempty(body{i,idx_v_id})
               error('setIGSpecs:Identifier', 'Invalid disturbance identifier at row %d and column %d \n',anchorIdxs_ig.row+i+1, anchorIdxs_ig.col+idx_zone_id)
            end
            if ~isempty(v_id)
               
               % check if zone identifier exists in current building
               unknown_zone = setdiff(zone_id,{building.thermal_model_data.zones.identifier});
               
               if ~isempty(unknown_zone)
                  error('setIGSpecs:Consistency','%s identifier of file ''%s'' not contained in building Data:\nColumn ''%s'' at row %d: ''%s''\n',Constants.zone_name_str,sprintf('%s',regexprep(obj.source_file,'\','\\')),obj.header_zone_id_str,anchorIdxs_ig.row+i+1,zone_id);
               end
               
               obj.igSpecs(end+1).zone_id = zone_id;
               obj.igSpecs(end).v_id = v_id;
               
            end
            
            
         end
         
         n_Rads = length(obj.igSpecs);
         
      end % setIGSpecs
      
   end % methods(Access=private)
end % classdef


