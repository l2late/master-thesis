function generateThermalModel(obj,varargin)
   % GENERATETHERMALMODEL Generates the thermal RC-model (Resistance-Capacitance) for the building one aims to control.
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
   
   
   % Check if Thermal Model Data is loaded
   
   
   if isempty(obj.thermal_model_data.zones) || isempty(obj.thermal_model_data.building_elements) || isempty(obj.thermal_model_data.constructions) ||...
         isempty(obj.thermal_model_data.materials)
      error('generateThermalModel:NoData','Cannot generate model since %s data incomplete.',lower(Constants.thermalmodel_name_str));
   end
   
   tmd = obj.thermal_model_data;
   bm = obj.building_model;
   
   
   n_states_per_layer_approach = false;
   
   if ~isempty(varargin)
      
      if length(varargin)==1
         
         if strcmpi(varargin{1},'n')
            n_states_per_layer_approach = true;
            
            % TODO: remove 2 lines below when n-states-per-layer approach is implemented.
            fprintfDbg(0,'n-states per layer approach currently not supported. Proceeding with standard approach.\n')
            n_states_per_layer_approach = false;
         else
            fprintfDbg(0,'Unknown approch ''%s''. Proceeding with one-state per layer approach.\n',varargin{1});
         end
      else
         error('generateThermalModel:InputArguments','Too many input arguments.');
      end
   end
   
   % Consistency check
   obj.checkThermalModelDataConsistency;
      
   % Clear old values if any
   bm.identifiers = Identifier;
   bm.thermal_submodel = ThermalModel.empty;
   bm.boundary_conditions = struct(Constants.ambient_name_str,BoundaryCondition.empty,Constants.adiabatic_name_str,BoundaryCondition.empty,...
      Constants.ground_name_str,BoundaryCondition.empty,Constants.user_defined_name_str,BoundaryCondition.empty);
   
   % Get number of zones and building elements
   n_zones = length(tmd.zones);
   n_building_elements = length(tmd.building_elements);
   
   Xcap = [];
   A_bar = zeros(n_zones);
   
   for i=1:n_zones
      bm.identifiers.x = [bm.identifiers.x; strcat(Constants.state_variable,'_',tmd.zones(i).identifier)];
      Xcap = blkdiag(Xcap,Constants.C_air*Constants.rho_air*str2double(tmd.zones(i).volume));
   end
   
   % Add building elements
   for i=1:n_building_elements
      
      state_identifiers_be = {};
      Xcap_ele = [];
      
      be_i = tmd.building_elements(i);
      
      net_area = str2double(be_i.area); % computed in checkThermalModelDataConsistency if necessary
      
      if ~isempty(be_i.window_identifier)
         win_idx = tmd.getWindowIdxFromIdentifier(be_i.window_identifier);
         
         % get glass area
         glass_area = tmd.evalStr(tmd.windows(win_idx).glass_area);
         
         % get frame area
         frame_area = tmd.evalStr(tmd.windows(win_idx).frame_area);
         
         net_area = net_area - (glass_area+frame_area);
      end
      
      if ~n_states_per_layer_approach
         % create model using 1_state_per_layer approach
         
         first_resistance = 0;
         first_resistance_set = 0;
         cumulative_resistance = 0;
         last_mass_layer_index = 0;
         total_building_element_capacity = 0;
         total_building_element_resistance = 0;   % Not further used in dave's code (debugging reasons?)
         boundary_conditions.A = BoundaryCondition();
         boundary_conditions.B = BoundaryCondition();
         construction_idx = [];
         
         % check if is no mass layer
         noMassOrConstruction_id = be_i.construction_identifier;
         if ~isempty(ThermalModelData.check_identifier(noMassOrConstruction_id,NoMassConstruction.key))
            
            A_bar_ele = [];
            
            nomass_idx = tmd.getNoMassConstructionIdxFromIdentifier(noMassOrConstruction_id);
            
            % Compute resistance
            last_resistance = 1/(net_area*tmd.evalStr(tmd.nomass_constructions(nomass_idx).U_value));
            
         elseif ~isempty(ThermalModelData.check_identifier(noMassOrConstruction_id,Construction.key))
            
            % get number of layers by considering construction identifier of
            % building element
            
            construction_idx = tmd.getConstructionIdxFromIdentifier(noMassOrConstruction_id);
            n_layers = length(tmd.constructions(construction_idx).material_identifiers);
            % Get number of mass layers
            n_massLayers = 0;
            for j=1:n_layers
               material_idx = tmd.getMaterialIdxFromIdentifier(tmd.constructions(construction_idx).material_identifiers{j});
               m = tmd.materials(material_idx);
               if isempty(m.R_value)
                  n_massLayers = n_massLayers+1;
               end
            end
            
            
            % We have mass layers
            A_bar_ele = zeros(n_massLayers);
            
            for j=1:n_layers
               
               % get material parameters
               material_idx = tmd.getMaterialIdxFromIdentifier(tmd.constructions(construction_idx).material_identifiers{j});
               m = tmd.materials(material_idx);
               
               isMassLayer = isempty(m.R_value);
               
               if isMassLayer
                  
                  state_identifiers_be = [state_identifiers_be; [Constants.state_variable,'_',be_i.identifier,'_','L',...
                     num2str(j),'_',Constants.layer_state_variable,num2str(1),'_',be_i.adjacent_A,be_i.adjacent_B]];
                  
                  
                  % Compute heat capacity and build Xcap_ele
                  heat_capacity = net_area*tmd.evalStr(tmd.constructions(construction_idx).thickness{j});
                  
                  heat_capacity = heat_capacity*tmd.evalStr(m.density);
                  
                  heat_capacity = heat_capacity*tmd.evalStr(m.specific_heat_capacity);
                  
                  Xcap_ele = blkdiag(Xcap_ele,heat_capacity);
                  
                  total_building_element_capacity = total_building_element_capacity + heat_capacity; % Not further used in Dave's code
                  
                  % Compute thermal resistances and build A_bar_ele
                  % if it has mass, add 1/2*thickness*specific_resistance/(area) to cumulative_resistance, possibly set first_resistance                  
                  resistance = 1/net_area*tmd.evalStr(tmd.constructions(construction_idx).thickness{j})/2*tmd.evalStr(m.specific_thermal_resistance);
                  
                  cumulative_resistance = cumulative_resistance + resistance;
                  
                  if first_resistance_set == 0 % if it is the first mass layer, set first_resistance to be the added up resistances
                     first_resistance = cumulative_resistance;
                     first_resistance_set = 1;
                  else % if it is a mass layer and it isnt the first change the A matrix to connect the last_mass layer to the current layer
                     % the A matrix is updated
                     total_building_element_resistance = total_building_element_resistance + cumulative_resistance;
                     A_bar_ele(last_mass_layer_index,last_mass_layer_index) = A_bar_ele(last_mass_layer_index,last_mass_layer_index)-1/cumulative_resistance;
                     A_bar_ele(last_mass_layer_index+1,last_mass_layer_index+1) = A_bar_ele(last_mass_layer_index+1,last_mass_layer_index+1)-1/cumulative_resistance;
                     A_bar_ele(last_mass_layer_index,last_mass_layer_index+1) = A_bar_ele(last_mass_layer_index,last_mass_layer_index+1)+1/cumulative_resistance;
                     A_bar_ele(last_mass_layer_index+1,last_mass_layer_index) = A_bar_ele(last_mass_layer_index+1,last_mass_layer_index)+1/cumulative_resistance;
                  end
                  last_mass_layer_index = last_mass_layer_index+1;
                  cumulative_resistance = resistance; % reset the cumulative resistance
                  
               else % it is a no mass layer
                  
                  R_value = tmd.evalStr(m.R_value);
                  
                  resistance = 1/net_area*R_value;
                  cumulative_resistance = cumulative_resistance + resistance;
                  
               end
               
            end
            last_resistance = cumulative_resistance; % store the last resistance for the connecting to other building elements etc
         else
            error('Bad Construction..');
         end
         
         % Connect first and last elements
         
         
         if ~isempty(construction_idx) % it is not a no mass construction
            
            for c = {'A','B'}
               
               adj = be_i.(['adjacent_',c{1}]);
               cur_conv_coeff = tmd.evalStr(tmd.constructions(construction_idx).(['conv_coeff_adjacent_',c{1}]));
               if ~isempty(ThermalModelData.check_identifier(adj,Zone.key)) % Its a zone
                  conv_coeff.(c{1}) = cur_conv_coeff;
               elseif ~isempty(strfind(adj,Constants.ground_identifier))    % Its ground
                  conv_coeff.(c{1}) = inf; % no convective coefficient if ground
               elseif ~isempty(strfind(adj,Constants.ambient_identifier))   % Its ambient
                  conv_coeff.(c{1}) = cur_conv_coeff;
               elseif ~isempty(strfind(adj,Constants.adiabatic_identifier))   % Its adiabatic
                  conv_coeff.(c{1}) = inf; % use inf here too, even though it will not be used
               elseif ~isempty(strfind(adj,Constants.TBCwFC))   % Its temperature boundary condition with convective coefficient
                  conv_coeff.(c{1}) = cur_conv_coeff;
               else % This assumes the case of temperature boundary condition without convective coefficient
                  conv_coeff.(c{1}) = inf; % no convective coefficient
               end
               if isnan(conv_coeff.(c{1})) || 0 >= conv_coeff.(c{1})
                  error('generateThermalModel:General','Bad value of convective coefficient!');
               end
               
            end
                  
            if ~isempty(state_identifiers_be) % If it has states
               
               boundary_conditions.A.identifier_1 = state_identifiers_be{1};

               if ~isempty(ThermalModelData.check_identifier(be_i.adjacent_A,Zone.key))
                  boundary_conditions.A.identifier_2 = strcat(Constants.state_variable,'_',be_i.adjacent_A);
               else
                  boundary_conditions.A.identifier_2 = be_i.adjacent_A;
               end

               boundary_conditions.A.value = 1/(first_resistance + 1/net_area*1/conv_coeff.A);

               boundary_conditions.B.identifier_1 = state_identifiers_be{end};

               if ~isempty(ThermalModelData.check_identifier(be_i.adjacent_B,Zone.key))
                  boundary_conditions.B.identifier_2 = strcat(Constants.state_variable,'_',be_i.adjacent_B);
               else
                  boundary_conditions.B.identifier_2 = be_i.adjacent_B;
               end

               boundary_conditions.B.value = 1/(last_resistance + 1/net_area*1/conv_coeff.B);

            else % If it is a construction solely from no mass materials
                              
               boundary_conditions.A.identifier_1 = '';
               boundary_conditions.A.identifier_2 = '';
               boundary_conditions.A.value = [];

               % connect adj_zone_A and adj_zone_B
               boundary_conditions.B.identifier_1 = strcat(Constants.state_variable,'_',be_i.adjacent_A);

               if ~isempty(ThermalModelData.check_identifier(be_i.adjacent_B,Zone.key))
                  boundary_conditions.B.identifier_2 = strcat(Constants.state_variable,'_',be_i.adjacent_B);
               else
                  boundary_conditions.B.identifier_2 = be_i.adjacent_B;
               end

               boundary_conditions.B.value = 1/(last_resistance + 1/net_area*1/conv_coeff.A + 1/net_area*1/conv_coeff.B);               

            end
            
         else % it is a no mass construction
            
            % not dynamic layer, leave connect_1 empty
            boundary_conditions.A.identifier_1 = '';
            boundary_conditions.A.identifier_2 = '';
            boundary_conditions.A.value = [];
            
            % connect adj_zone_A and adj_zone_B
            boundary_conditions.B.identifier_1 = strcat(Constants.state_variable,'_',be_i.adjacent_A);
            
            if ~isempty(ThermalModelData.check_identifier(be_i.adjacent_B,Zone.key))
               boundary_conditions.B.identifier_2 = strcat(Constants.state_variable,'_',be_i.adjacent_B);
            else
               boundary_conditions.B.identifier_2 = be_i.adjacent_B;
            end
            
            boundary_conditions.B.value = 1/last_resistance; % no convective coefficients in that case!
            
         end
         
      end
      %{
    else n-states per layer approchach
    else
        Ts_hrs = bm.Ts_hrs;
        if isempty(Ts_hrs)
            error('generateThermalModel:Ts_hrs','Sampling time not yet defined.\n')
        end
        % find the number of required building element states (materials type == 'standard')
        n_states_tot = 0;
        const = 3; % default as in EP
        for i=1:no_layers
            m = mats(i);
            if strcmp(mats(i).type,'standard')
                dx = sqrt(const*m.conductivity*Ts_hrs/(m.density*m.specific_heat_capacity));
                if source_layer_no ~= i
                    n_states_tot = n_states_tot + ceil(m.thickness/dx);
                else
                    n_states_tot = n_states_tot + 1;
                end
            end
        end
    end
      %}
      
      A_bar = blkdiag(A_bar,A_bar_ele);
      Xcap = blkdiag(Xcap,Xcap_ele);
      bm.identifiers.x = [bm.identifiers.x ; state_identifiers_be];
      
      % Connect elements
      for j=1:2
         
         cs = 'AB';
         
         bc_j = boundary_conditions.(cs(j));
         
         tmp = bm.identifiers.x; %#ok<NASGU> % "protective" call to the identifiers, without this, the error message below occasionally appears (???...)
         no_states = numel(bm.identifiers.x);
         no_states2 = numel(bm.identifiers.x);
         if no_states ~= no_states2
            error('Call to identifiers removed identifiers..');
         end
         
         A_tmp{j} = zeros(no_states); %#ok<*AGROW>
         
         if isempty(bc_j.identifier_1) || isempty(bc_j.identifier_2)
            
         elseif strcmp(Constants.ambient_identifier,bc_j.identifier_1) || strcmp(Constants.ambient_identifier,bc_j.identifier_2)
            bm.boundary_conditions.(Constants.ambient_name_str) = [bm.boundary_conditions.(Constants.ambient_name_str) bc_j];
            
         elseif strcmp(Constants.adiabatic_identifier,bc_j.identifier_1) || strcmp(Constants.adiabatic_identifier,bc_j.identifier_2)
            bm.boundary_conditions.(Constants.adiabatic_name_str) = [bm.boundary_conditions.(Constants.adiabatic_name_str) bc_j];

         elseif strcmp(Constants.ground_identifier,bc_j.identifier_1) || strcmp(Constants.ground_identifier,bc_j.identifier_2)
            bm.boundary_conditions.(Constants.ground_name_str) = [bm.boundary_conditions.(Constants.ground_name_str) bc_j];
             
         elseif ~isempty(regexp(bc_j.identifier_1,'^x_\S\d\d\d\d', 'once')) && ~isempty(regexp(bc_j.identifier_2,'x_\S\d\d\d\d', 'once'))
            ind_21 = ismember(bm.identifiers.x,bc_j.identifier_1);
            ind_22 = ismember(bm.identifiers.x,bc_j.identifier_2);
            A_tmp{j}(ind_21,ind_21) = A_tmp{j}(ind_21,ind_21) - bc_j.value;
            A_tmp{j}(ind_22,ind_22) = A_tmp{j}(ind_22,ind_22) - bc_j.value;
            A_tmp{j}(ind_21,ind_22) = A_tmp{j}(ind_21,ind_22) + bc_j.value;
            A_tmp{j}(ind_22,ind_21) = A_tmp{j}(ind_22,ind_21) + bc_j.value;
            
         else
            bm.boundary_conditions.(Constants.user_defined_name_str) = [bm.boundary_conditions.(Constants.user_defined_name_str) bc_j];

         end
      end
      
      A_bar = A_bar+A_tmp{1}+A_tmp{2};
      
      
   end
   
   
   % instantiate thermal model
   bm.thermal_submodel = ThermalModel;
   
   Bq_bar = eye(length(bm.identifiers.x));
   bm.identifiers.q = cellfun(@(x)[Constants.heat_flux_variable,x(2:end)],bm.identifiers.x,'UniformOutput',0);
   
   bm.thermal_submodel.A = Xcap\A_bar;
   bm.thermal_submodel.Bq = Xcap\Bq_bar;
   bm.thermal_submodel.Xcap = Xcap;
   
   obj.building_model = bm;
   obj.thermal_model_data = tmd;
   
   fprintfDbg(1,'New %s of %s ''%s'' created.\n\n',lower(Constants.thermalmodel_name_str),lower(Constants.building_name_str),obj.identifier);
   
end % generateThermalModel
