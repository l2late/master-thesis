classdef BEHeatfluxes < EHFModelBaseClass
   %BEHEATFLUXES 	This class represents the BEHeatfluxes external heat flux model of a building.
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
      
      n_properties@uint64 = uint64(3);                                  % Number of properties required for object instantation
      multiIncludeOk@logical = false;
      
      % Model specific conventions
      BEHeatfluxes_name_str@char = 'BE heatfluxes';                   % Name of the model
      BEHeatfluxes_identifier@char = 'BEH';                           % Short name of the model
      
      % Required file header for the specific model data file
      BEHeatfluxes_file_header@cell =  {'buildingelement_identifier' 'layer_number' 'control_identifier','heating_cooling_selection'};
      header_be_id_str@char = 'buildingelement_identifier';
      header_layer_str@char = 'layer_number';
      header_u_id_str@char = 'control_identifier';
      header_hcsel_str@char = 'heating_cooling_selection';
      
      % signal labels
      heating_str@char = 'heat';
      cooling_str@char = 'cool';
      
   end
   
   properties(Access=private)
      
      BEHSpecs = struct('be_id',{},'layer_number',{},'u_id',{},'hcsel',{}, 'be_area',{});
      
   end
   
   methods
      
      function obj = BEHeatfluxes(building,EHF_identifier,source_file)
         
         % check arguments
         if ~isa(building,Constants.building_name_str)
            error('BEHeatfluxes:Argument','Argument error. Argument 1 is required to be of type ''%s''.\n',Constants.building_name_str);
         end
         
         % check if building has a thermal model
         if isempty(building.building_model.thermal_submodel)
            error('BEHeatfluxes:NoThermalModel','%s with %s required.\n',Constants.building_name_str,Constants.thermalmodel_name_str);
         end
         
         % check if file exists
         if ~(exist(source_file,'file') == 2)
            error('BEHeatfluxes:UnknownFile','File ''%s'' does not exist. Valid file file path (string) required. Full file path recommended.\n',source_file);
         end
         
         obj.EHF_identifier = EHF_identifier;
         obj.source_file = source_file;
         obj = obj.generateModel(building);
         obj.checkNan();
         
      end % BEHeatfluxes
      
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
         if any(strcmpi({obj.BEHSpecs.hcsel},'h'))
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
         if any(strcmpi({obj.BEHSpecs.hcsel},'c'))
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
         
         
         
         for i = 1:length(obj.BEHSpecs)
            
            
            
            if strcmpi(obj.BEHSpecs(i).hcsel,'h')
               
               idx_u = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHeatfluxes_identifier,'_',obj.BEHSpecs(i).u_id,'_',obj.heating_str));
               cu(idx_u) = cu(idx_u) + obj.BEHSpecs(i).be_area*p.(fn_h)*parameters.Ts_hrs;
               
            elseif strcmpi(obj.BEHSpecs(i).hcsel,'c')
               
               idx_u = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHeatfluxes_identifier,'_',obj.BEHSpecs(i).u_id,'_',obj.cooling_str));
               cu(idx_u) = cu(idx_u) + obj.BEHSpecs(i).be_area*p.(fn_c)*parameters.Ts_hrs;
               
            else
               
               error('getCostVector:heatingSelection','Didnt find an appropriate heating selection.\n');
               
            end
            
         end        
         
         
      end % getCostVector
      
   end % methods
   
   methods(Access=private)
      
      function obj = generateModel(obj,building)
         
         headers = {obj.BEHeatfluxes_file_header};
         [dataTables,anchorIdxs_BEH] = getDataTablesFromFile(obj.source_file,headers);
         dataTable_BEH = dataTables{1};
         
         
         obj = setBEHSpecs(obj,dataTable_BEH,anchorIdxs_BEH,building);
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
         % q^i_BE_layer_state = a^i_BE*(u_BEHeatfluxes_heating-u_BEHeatfluxes_cooling)
         
         % generate EFH
         
         for i = 1:length(obj.BEHSpecs)
            
            be_id = obj.BEHSpecs(i).be_id;
            hcsel = obj.BEHSpecs(i).hcsel;
            area_BE = obj.BEHSpecs(i).be_area;
            
            adj_A = building.thermal_model_data.getValue(be_id,'adjacent_A');
            adj_B = building.thermal_model_data.getValue(be_id,'adjacent_B');
            
            % get number of states per layer
            layer_number = obj.BEHSpecs(i).layer_number;
            n_states_per_layer = sum(~cellfun(@isempty,regexp(obj.identifiers.q,strcat('^',Constants.heat_flux_variable,'_',be_id,'_','L',num2str(layer_number),'_',...
               Constants.layer_state_variable,'\d*_',adj_A,adj_B,'$'),'match')));
            if n_states_per_layer>1
               error('More than 1 state per layer not supported currently');
            end
            %{
% %                 % if number of statest per layer is odd: add heat flux to middle state of layer at layer index
% %                 % if number of statest per layer is even: divide portion of heat flux
% %                 % equally to both states in the center of layer at layer index
% %                 if mod(n_states_per_layer,2) == 0
% %
% %                     state_q_id_1 = strcat(Constants.heat_flux_variable,'_',be_id,'_',Layer.key,num2str(layer_number),'_',...
% %                                          Constants.layer_state_variable,num2str(n_states_per_layer/2),'_',adj_A,adj_B);
% %                     state_q_id_2 = strcat(Constants.heat_flux_variable,'_',be_id,'_',Layer.key,num2str(layer_number),'_',...
% %                                          Constants.layer_state_variable,num2str(n_states_per_layer/2+1),'_',adj_A,adj_B);
% %                     idx_states_q = ismember(obj.identifiers.q,{state_q_id_1,state_q_id_2});
% %
% %                     idx_u_heat = ismember(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHSpecs(i).u_id,'_',obj.heating_str));
% %                     idx_u_cool = ismember(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHSpecs(i).u_id,'_',obj.cooling_str));
% %
% %                     obj.Bq_u(idx_states_q,idx_u_heat) = obj.Bq_u(idx_states_q,idx_u_heat) + 0.5*area_BE;
% %                     obj.Bq_u(idx_states_q,idx_u_cool) = obj.Bq_u(idx_states_q,idx_u_cool) - 0.5*area_BE;
% %
% %                 else
% %                     idx_state_q = ismember(obj.identifiers.q,strcat(Constants.heat_flux_variable,'_',be_id,'_',Layer.key,num2str(layer_number),'_',...
% %                                           Constants.layer_state_variable,num2str(floor(n_states_per_layer/2)+1),'_',adj_A,adj_B));
% %
% %                     idx_u_heat = ismember(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHSpecs(i).u_id,'_',obj.heating_str));
% %                     idx_u_cool = ismember(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHSpecs(i).u_id,'_',obj.cooling_str));
% %
% %                     obj.Bq_u(idx_state_q,idx_u_heat) = obj.Bq_u(idx_state_q,idx_u_heat) + area_BE;
% %                     obj.Bq_u(idx_state_q,idx_u_cool) = obj.Bq_u(idx_state_q,idx_u_cool) - area_BE;
% %                 end
% %             end
            %}
            
            idx_state_q = getIdIndex(obj.identifiers.q,strcat(Constants.heat_flux_variable,'_',be_id,'_','L',num2str(layer_number),'_',...
               Constants.layer_state_variable,num2str(floor(n_states_per_layer/2)+1),'_',adj_A,adj_B));
            
            if strcmp(hcsel,'h')
               idx_u_heat = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHeatfluxes_identifier,'_',obj.BEHSpecs(i).u_id,'_',obj.heating_str));
               obj.Bq_u(idx_state_q,idx_u_heat) = obj.Bq_u(idx_state_q,idx_u_heat) + area_BE;
            elseif strcmp(hcsel,'c')
               idx_u_cool = getIdIndex(obj.identifiers.u,strcat(Constants.input_variable,'_',obj.BEHeatfluxes_identifier,'_',obj.BEHSpecs(i).u_id,'_',obj.cooling_str));
               obj.Bq_u(idx_state_q,idx_u_cool) = obj.Bq_u(idx_state_q,idx_u_cool) - area_BE;
            else
               error('This should have been caught before');
            end
            
         end
         
      end % generateModel
      
      function obj = generateIdentifiers(obj,building)
         
         % input identifiers
         obj.identifiers = Identifier;
         obj.identifiers.x = building.building_model.identifiers.x;
         obj.identifiers.q = building.building_model.identifiers.q;
         
         unique_u_ids = unique({obj.BEHSpecs.u_id});
         
         for i=1:length(unique_u_ids)
            u_id = unique_u_ids{i};
            idx_u_id = find(strcmp({obj.BEHSpecs.u_id},u_id));
            hcsel = obj.BEHSpecs(idx_u_id).hcsel; %#ok<FNDSB>
            if strcmp(hcsel,'h')
               hc_str = obj.heating_str;
               obj.identifiers.constraints{end+1} = strcat('Q_',obj.BEHeatfluxes_identifier,'_',u_id,'_',hc_str,'_min');
               obj.identifiers.constraints{end+1} = strcat('Q_',obj.BEHeatfluxes_identifier,'_',u_id,'_',hc_str,'_max');
            else
               hc_str = obj.cooling_str;
               obj.identifiers.constraints{end+1} = strcat('Q_',obj.BEHeatfluxes_identifier,'_',u_id,'_',hc_str,'_min');
               obj.identifiers.constraints{end+1} = strcat('Q_',obj.BEHeatfluxes_identifier,'_',u_id,'_',hc_str,'_max');
            end
            obj.identifiers.u{end+1} = strcat(Constants.input_variable,'_',obj.BEHeatfluxes_identifier,'_',u_id,'_',hc_str);
            
         end
         
      end
      
      function obj = setBEHSpecs(obj,dataTable_BEH,anchorIdxs_BEH,building)
         
         header = dataTable_BEH(1,:);
         body = dataTable_BEH(2:end,:);
         
         idx_be_id = getIdIndex(header,obj.header_be_id_str);
         idx_layer = getIdIndex(header,obj.header_layer_str);
         idx_u_id = getIdIndex(header,obj.header_u_id_str);
         idx_hcsel = getIdIndex(header,obj.header_hcsel_str);
         
         
         for i = 1:size(body,1)
            
            be_id = ThermalModelData.check_identifier(body{i,idx_be_id},BuildingElement.key);
            layer_number = str2double(ThermalModelData.check_value(body{i,idx_layer},false));
            u_id = ThermalModelData.check_special_identifier(body{i,idx_u_id});
            hcsel = body{i,idx_hcsel};
            
            if isempty(be_id) || isempty(u_id) || isempty(layer_number) || isempty(hcsel)
               error('ERR');
            end
            
            if hcsel ~= 'h' && hcsel ~= 'c'
               error('ERR');
            end
            
            % check if building element identifier exists in current building
            unknown_BE = setdiff(be_id,{building.thermal_model_data.building_elements.identifier});
            if ~isempty(unknown_BE)
               error('setBEHSpecs:Consistency','%s identifier of file ''%s'' not contained in building Data:\nColumn ''%s'' at row %d: ''%s''\n',Constants.buildingelement_name_str,sprintf('%s',regexprep(obj.source_file,'\','\\')),obj.BEHeatfluxes_file_header{1},anchorIdxs_BEH.row+1+i,be_id);
            end
            
            % check if current building element has layer specified in its
            % construction (number of specified layers must be greater or equal layer_number)
            c_id = building.thermal_model_data.getValue(be_id,'construction_identifier');
            material_identifiers = building.thermal_model_data.getValue(c_id,'material_identifiers');
            if layer_number > length(material_identifiers)
               error('setBEHSpecs:Consistency','Specified %s ''%d'' exceeds number of layers in specified %s ''%s'' at row %d column %d.\n',obj.BEHeatfluxes_file_header{2},layer_number,lower(Constants.buildingelement_name_str),be_id,anchorIdxs_BEH.row+1+i,anchorIdxs_BEH.col);
            end
            
            % check if previously there was a u_id with different hcsel
            idx_same_u_id = strcmp({obj.BEHSpecs.u_id},u_id);
            hcsel_of_same_u_id = {obj.BEHSpecs(idx_same_u_id).hcsel};
            if any(~strcmp(hcsel_of_same_u_id,hcsel))
               error('ERR');
            end
            
            % assign specifications
            obj.BEHSpecs(end+1).be_id = be_id;
            obj.BEHSpecs(end).layer_number = layer_number;
            obj.BEHSpecs(end).u_id = u_id;
            obj.BEHSpecs(end).hcsel = hcsel;
            obj.BEHSpecs(end).be_area = building.thermal_model_data.getValue(be_id,'area');
            
         end
         
      end % setBEHSpecs
      
      
   end % methods(Access=private)
end % classdef



