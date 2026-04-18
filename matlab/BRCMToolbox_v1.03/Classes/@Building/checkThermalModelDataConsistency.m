function checkThermalModelDataConsistency(obj)
   %CHECKTHERMALMODELDATACONSISTENCY Checks whether building's thermal model data is consistent with respect to its elements.
   % e.g. all materials (identifiers) in a construction must exist as materials (identifiers)
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
   
   
   % Feasiblity and syntax are already checked, identifiers of elements are all unique
   
   % Allow only consistency check if all data is available
   % Windows, Parameters and NoMassConstructions are optional
   
   
   if isempty(obj.thermal_model_data.zones) || isempty(obj.thermal_model_data.building_elements) || isempty(obj.thermal_model_data.constructions) ||...
         isempty(obj.thermal_model_data.materials)
      error('checkThermalModelDataConsistency:NoThermalModelData','%s data incomplete. Cannot check consistency.\n',Constants.building_name_str);
   end
   
   tmd = obj.thermal_model_data;
   
   % ZONES
   % Find 'NULL' := Not yet specified string in zone data
   n_zones = length(tmd.zones);
   for i = 1:n_zones
      
      if strcmp(tmd.zones(i).area,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.zone_name_str,i,'area'))
      end
      
      if strcmp(tmd.zones(i).volume,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.zone_name_str,i,'volume'));
      end
      
      if strcmp(tmd.zones(i).group,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.zone_name_str,i,'group identifiers'));
      end
   end
   
   % BUILDING ELEMENTS
   % check if construction identifiers in construction_identifiers exist
   n_BE = length(tmd.building_elements);
   
   % Find 'NULL' := Not yet specified string in BE data
   for i = 1:n_BE
      
      if strcmp(tmd.building_elements(i).construction_identifier,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.buildingelement_name_str,i,'construction identifier'));
      end
      
      if strcmp(tmd.building_elements(i).adjacent_A,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.buildingelement_name_str,i,'adjacent A'));
      end
      
      if strcmp(tmd.building_elements(i).adjacent_B,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.buildingelement_name_str,i,'adjacent B'));
      end
      
      if strcmp(tmd.building_elements(i).window_identifier,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.buildingelement_name_str,i,'window identifier'));
      end
      
      if ischar(tmd.building_elements(i).area) && strcmp(tmd.building_elements(i).area,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.buildingelement_name_str,i,'area'));
      end
      
      if ischar(tmd.building_elements(i).vertices) && strcmp(tmd.building_elements(i).vertices,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.buildingelement_name_str,i,'vertices'));
      end
   end
   
   % MATERIAL
   % Find 'NULL' := Not yet specified string in material data
   n_materials = length(tmd.materials);
   for i = 1:n_materials
      
      if strcmp(tmd.materials(i).specific_heat_capacity,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.material_name_str,i,'specific heat capacity'));
      end
      
      if strcmp(tmd.materials(i).specific_thermal_resistance,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.material_name_str,i,'specific thermal resistance'));
      end
      
      if strcmp(tmd.materials(i).density,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.material_name_str,i,'density'));
      end
   end
   
   % CONSTRUCTION
   n_constructions = length(tmd.constructions);
   % Find 'NULL' := Not yet specified string in material data
   for i = 1:n_constructions
      
%       if ischar(tmd.constructions(i).layers) && strcmp(tmd.constructions(i).layers,Constants.NULL_str)
%          error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.construction_name_str,i,'layer'));
%       end
      
      if strcmp(tmd.constructions(i).conv_coeff_adjacent_A,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.construction_name_str,i,'convective heat coefficient A'));
      end
      
      if strcmp(tmd.constructions(i).conv_coeff_adjacent_B,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.construction_name_str,i,'convective heat coefficient B'));
      end
   end
   
   % WINDOWS
   n_windows = length(tmd.windows);
   % Find 'NULL' := Not yet specified string in window data
   for i = 1:n_windows
      
      if strcmp(tmd.windows(i).glass_area,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.window_name_str,i,'glass area'));
      end
      
      if strcmp(tmd.windows(i).frame_area,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.window_name_str,i,'frame area'));
      end
      
      if strcmp(tmd.windows(i).U_value,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.window_name_str,i,'U-value'));
      end
      
      if strcmp(tmd.windows(i).SHGC,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.window_name_str,i,'SHGC'));
      end
   end
   
   % PARAMETER
   n_params = length(tmd.parameters);
   % Find 'NULL' := Not yet specified string in paramter data
   for i = 1:n_params
      
      if strcmp(tmd.parameters(i).value,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.parameter_name_str,i,'value'));
      end
   end
   
   % NOMASS CONSTRUCTION
   n_nomass = length(tmd.nomass_constructions);
   % Find 'NULL' := Not yet specified string in no mass construction data
   for i = 1:n_nomass
      
      if strcmp(tmd.nomass_constructions(i).U_value,Constants.NULL_str)
         error('checkThermalModelDataConsistency:NULL',Constants.error_NULL_entry(Constants.nomass_construction_name_str,i,'U-value'));
      end
   end
   
   construction_ids_in_BE = {tmd.building_elements.construction_identifier};
   c_ids_NOT_in_construction = setdiff(construction_ids_in_BE,{tmd.constructions.identifier});
   
   % remove known no mass construction from set
   c_ids_NOT_in_construction = setdiff(c_ids_NOT_in_construction,{tmd.nomass_constructions.identifier});
   
   if ~isempty(c_ids_NOT_in_construction)
      
      % get inconsistent indices
      idx = find(ismember(construction_ids_in_BE,c_ids_NOT_in_construction));
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(c_ids_NOT_in_construction,idx);
      
      error('BuildingElement:Inconsistency',['%s/s %s are inconsistent with respect to %ss and/or %ss.\n'...
         'Unknown %s/%s identifier/s:\t %s\n'],...
         Constants.buildingelement_name_str,idx_str,lower(Constants.construction_name_str),lower(Constants.nomass_construction_name_str),...
         lower(Constants.construction_name_str),lower(Constants.nomass_construction_name_str),ids_str);
   end
   
   % check if zone identifiers in adjacent_A exist
   adjA_ids_in_BE = {tmd.building_elements.adjacent_A};
   adjA_ids_in_BE(cellfun(@isempty,regexp(adjA_ids_in_BE,'^Z\d\d\d\d'))) = [];
   adjA_ids_NOT_in_zones = setdiff(adjA_ids_in_BE,{tmd.zones.identifier});
   
   
   if ~isempty(adjA_ids_NOT_in_zones)
      
      % get inconsistent
      idx = find(ismember(adjA_ids_in_BE,adjA_ids_NOT_in_zones));
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(adjA_ids_NOT_in_zones,idx);
      
      error('BuildingElement:Inconsistency',['%s/s %s are inconsistent with respect to %ss in adjacent_A.\n'...
         'Unknown %s identifier/s:\t%s\n'],...
         Constants.buildingelement_name_str,idx_str,lower(Constants.zone_name_str),lower(Constants.zone_name_str),ids_str);
   end
   
   % check if zone identifiers in adjacent_B exist
   adjB_ids_in_BE = {tmd.building_elements.adjacent_B};
   adjB_ids_in_BE(cellfun(@isempty,regexp(adjB_ids_in_BE,'^Z\d\d\d\d'))) = [];
   adjB_ids_NOT_in_zones = setdiff(adjB_ids_in_BE,{tmd.zones.identifier});
   
   if ~isempty(adjB_ids_NOT_in_zones)
      
      % get inconsistent indices
      idx = find(ismember({tmd.building_elements.adjacent_B},adjB_ids_NOT_in_zones));
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(adjB_ids_NOT_in_zones,idx);
      
      error('BuildingElement:Inconsistency',['%s/s %s are inconsistent with respect to %ss in adjacent_B.\n' ...
         'Unknown %s identifier/s:\t %s\n'],...
         Constants.buildingelement_name_str,idx_str,lower(Constants.zone_name_str),lower(Constants.zone_name_str),ids_str);
   end
   
   % check if window identifiers in window_identifier exist
   win_ids_in_BE = {tmd.building_elements.window_identifier};
   
   % remove ''(No window) from set
   %win_ids_in_BE = setdiff(win_ids_in_BE,Constants.EMPTY_str); % This line bugs in WINDOWS
   win_ids_in_BE(cellfun(@(x)strcmp(x,Constants.EMPTY_str),win_ids_in_BE)) = [];
   win_ids_NOT_in_windows = setdiff(win_ids_in_BE,{tmd.windows.identifier});
   
   if ~isempty(win_ids_NOT_in_windows)
      
      % get inconsistent indices
      idx = [];
      for i = 1:n_BE
         if ~isempty(find(ismember(tmd.building_elements(i).window_identifier,win_ids_NOT_in_windows),1))
            idx = [idx i]; %#ok<AGROW>
         end
      end
      
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(win_ids_NOT_in_windows,idx);
      
      error('BuildingElement:Inconsistency',['%s/s %s are inconsistent with respect to %ss.\n'...
         'Unknown window identifier/s:\t %s '],...
         Constants.buildingelement_name_str,idx_str,lower(Constants.window_name_str),lower(Constants.window_name_str),ids_str);
   end
   
   % Check if BE is consistent with zone area, window area
   for i = 1:n_BE
      
      % get indexes of adjacent zones
      zoneA_idx = [];
      if ~isempty(ThermalModelData.check_identifier(tmd.building_elements(i).adjacent_A,Zone.key))
         zoneA_idx = tmd.getZoneIdxFromIdentifier(tmd.building_elements(i).adjacent_A);
      end
      
      zoneB_idx = [];
      if ~isempty(ThermalModelData.check_identifier(tmd.building_elements(i).adjacent_B,Zone.key))
         zoneB_idx = tmd.getZoneIdxFromIdentifier(tmd.building_elements(i).adjacent_B);
      end
      
      % check if adjacent_A and adjacent_B at least contain a zone
      % at least one of the indices zoneA_idx and zoneB_idx should not be
      % empty
      if isempty(zoneA_idx) && isempty(zoneB_idx)
         error('BuildingElement:Adjacent',['%s ''%d'' is inconsistent in adjacent_A and adjacent_B.\n',...
            Constants.error_msg_identifierAdjacentZone(Constants.zone_name_str)],Constants.buildingelement_name_str,i);
      end
      
      adj_A = tmd.building_elements(i).adjacent_A;
      adj_B = tmd.building_elements(i).adjacent_B;
      % check if BE has a window, then adjacent_A or adjacent_B is required
      % to be 'AMB'
      if ~isempty(tmd.building_elements(i).window_identifier) && ~(strcmp(adj_A,Constants.ambient_identifier) || strcmp(adj_B,Constants.ambient_identifier))
         error('BuildingElement:Adjacent','%s ''%d'' has %s specified, but no ''%s'' identifier found in adjacent A or adjacent B.\n',...
            Constants.buildingelement_name_str,i,Constants.window_name_str,Constants.ambient_identifier);
      end
      
      % check if BE has a no mass construction, then adjacent_A and
      % adjacent_B are not allowed to be equal
      if ~isempty(ThermalModelData.check_identifier(tmd.building_elements(i).construction_identifier,NoMassConstruction.key)) && strcmp(adj_A,adj_B)
         error('BuildingElement:Adjacent','%s ''%d'' adjacent A and adjacent B are not allowed to be equal if a %s is specified.\n',Constants.buildingelement_name_str,i,lower(Constants.nomass_construction_name_str));
      end
      
      % get orientation of BE
      if ~strcmp(tmd.building_elements(i).vertices,Constants.EMPTY_str) && tmd.building_elements(i).isHorizontal
         % case horizontal: compare area of BE with adjacent zones
         if isempty(tmd.building_elements(i).area)
            be_area = tmd.building_elements(i).computeArea();
         else
            be_area = tmd.evalStr(tmd.building_elements(i).area);
         end
         
      end
      
      % Does window fit into BE?
      if ~isempty(tmd.building_elements(i).window_identifier)
         win_idx = tmd.getWindowIdxFromIdentifier(tmd.building_elements(i).window_identifier);
         win_area = tmd.evalStr(tmd.windows(win_idx).glass_area) + tmd.evalStr(tmd.windows(win_idx).frame_area);
         
         if ~((tmd.evalStr(tmd.building_elements(i).area)-win_area) >= 0)
            error('BuildingElement:Inconsistency','Area of %s ''%d'' is inconsistent with total %s area.\n',Constants.buildingelement_name_str,i,Constants.window_name_str);
         end
      end
      
      % Is area defined by vertices consistent with area
      if ~isempty(tmd.building_elements(i).vertices) && ~strcmp(tmd.building_elements(i).area,Constants.EMPTY_str)
         if ~(abs(tmd.building_elements(i).computeArea-tmd.evalStr(tmd.building_elements(i).area)) < Constants.tol_area)
            error('BuildingElement:Inconsistency','Vertices and area are inconsistent. Absolute difference between areas exceeds tolerance %f.\n',Constants.tol_area);
         end
      end
      
      % Compute area if vertices are defined
      if (isa(tmd.building_elements(i).vertices,Constants.vertex_name_str) && ~strcmp(tmd.building_elements(i).vertices,Constants.EMPTY_str)) && strcmp(tmd.building_elements(i).area,Constants.EMPTY_str)
         tmd.building_elements(i).area = num2str(tmd.building_elements(i).computeArea,Constants.num2str_precision);
      end
   end
   
   % get current available parameter identifiers
   param_ids = {tmd.parameters.identifier};
   
   % check if parameter identifier in specific_heat_capacity exists
   param_ids_in_material = Constants.EMPTY_str;
   filter_NaN = str2double({tmd.materials.specific_heat_capacity});
   param_ids_in_material = [param_ids_in_material {tmd.materials(isnan(filter_NaN)).specific_heat_capacity}];
   
   % get only unique ones
   param_ids_in_material = unique(param_ids_in_material);
   param_ids_NOT_in_parameters = setdiff(param_ids_in_material,param_ids);
   param_ids_NOT_in_parameters = setdiff(param_ids_NOT_in_parameters,{''});
   
   if ~isempty(param_ids_NOT_in_parameters)
      
      % get inconsistent indices
      idx = find(ismember({tmd.materials.specific_heat_capacity},param_ids_NOT_in_parameters));
      
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(param_ids_NOT_in_parameters,idx);
      
      error('Material:Inconsistency',['specific_heat_capacity of %s/s %s are inconsistent with respect to %ss.\n'...
         'Unknown %s identifier/s:\t %s '],...
         lower(Constants.material_name_str),idx_str,lower(Constants.parameter_name_str),lower(Constants.parameter_name_str),ids_str);
   end
   
   % check if parameter identifier in specific_thermal_resistance exists
   param_ids_in_material = Constants.EMPTY_str;
   filter_NaN = str2double({tmd.materials.specific_thermal_resistance});
   param_ids_in_material = [param_ids_in_material {tmd.materials(isnan(filter_NaN)).specific_thermal_resistance}];
   
   % get only unique ones
   param_ids_in_material = unique(param_ids_in_material);
   param_ids_NOT_in_parameters = setdiff(param_ids_in_material,param_ids);
   param_ids_NOT_in_parameters = setdiff(param_ids_NOT_in_parameters,{''});
   
   if ~isempty(param_ids_NOT_in_parameters)
      
      % get inconsistent indices
      idx = find(ismember({tmd.materials.specific_thermal_resistance},param_ids_NOT_in_parameters));
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(param_ids_NOT_in_parameters,idx);
      
      error('Material:Inconsistency',['specific_thermal_resistance of %s/s  %s are inconsistent with respect to %ss.\n'...
         'Unknown %s identifier/s:\t %s '],...
         lower(Constants.material_name_str),idx_str,lower(Constants.parameter_name_str),lower(Constants.parameter_name_str),ids_str);
   end
   
   % check if parameter identifier in density exists
   param_ids_in_material = Constants.EMPTY_str;
   filter_NaN = str2double({tmd.materials.density});
   param_ids_in_material = [param_ids_in_material {tmd.materials(isnan(filter_NaN)).density}];
   
   % get only unique ones
   param_ids_in_material = unique(param_ids_in_material);
   param_ids_NOT_in_parameters = setdiff(param_ids_in_material,param_ids);
   param_ids_NOT_in_parameters = setdiff(param_ids_NOT_in_parameters,{''});
   
   if ~isempty(param_ids_NOT_in_parameters)
      
      % get inconsistent indices
      idx = find(ismember({tmd.materials.density},param_ids_NOT_in_parameters));
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(param_ids_NOT_in_parameters,idx);
      
      error('Material:Inconsistency',['Density of %s/s %s are inconsistent with respect to %ss.\n'...
         'Unknown %s identifier/s:\t %s '],...
         lower(Constants.material_name_str),idx_str,lower(Constants.parameter_name_str),lower(Constants.parameter_name_str),ids_str);
   end
   
   % CONSTRUCTION
   % check if material identifiers in material_identifiers exist
   % get all material ids from construction
   for i = 1:n_constructions
      
      % check layer consistency
      n_layers = length(tmd.constructions(i).material_identifiers);
      if n_layers ~= length(tmd.constructions(i).thickness)
          error('Construction:Inconsistency','%s ''%s'' is has unequal lengths of material_identifiers and thickness. \n',...
               Constants.construction_name_str,tmd.constructions(i).identifier);
      end
      
      % For a construction with more than one layer, all Material values must have
      % positive entries
      for j = 1:n_layers
         mat_identifier = tmd.constructions(i).material_identifiers{j};
         mat_idx = tmd.getMaterialIdxFromIdentifier(mat_identifier);
         
         if isempty(mat_idx)
            error('Construction:Inconsistency',['%s ''%d'' is inconsistent with respect to %s.\n'...
               'Unknown material identifier:\t %s '],...
               Constants.construction_name_str,i,lower(Constants.material_name_str),sprintf('''%s'' ',mat_identifier));
         else
            % check if all material properties are greater zero or empty if R_value specified
            
            % R_value must be either empty or > 0
            R_valueEmpty = false;
            if isempty(tmd.materials(mat_idx).R_value)
               R_valueEmpty = true;
            else
               if tmd.evalStr(tmd.materials(mat_idx).R_value)<=0
                  error('Construction:Inconsistency',Constants.error_msg_illegal_layer(i,j,'R value'));
               end
            end
            
            % specific_heat_capacity > 0
            if R_valueEmpty
               if tmd.evalStr(tmd.materials(mat_idx).specific_heat_capacity)<=0
                  error('Construction:Inconsistency',Constants.error_msg_illegal_layer(i,j,'Specific heat capacity'));
               end
            end
            
            % specific_thermal_resistance > 0
            if R_valueEmpty
               if tmd.evalStr(tmd.materials(mat_idx).specific_thermal_resistance)<=0
                  error('Construction:Inconsistency',Constants.error_msg_illegal_layer(i,j,'Specific thermal resistance'));
               end
            end
            
            % density > 0            
            if R_valueEmpty
               if tmd.evalStr(tmd.materials(mat_idx).density)<=0
                  error('Construction:Inconsistency',Constants.error_msg_illegal_layer(i,j,'Density'));
               end
            end
            
         end
      end
   end
   
   % check if parameter identifiers in conv_coeff_adjacentA exists
   % tmd.evalStr returns NaN if the string cannot be converted into a number,
   % so in this case we located a parameter identifier
   param_ids_in_construction = Constants.EMPTY_str;
   filter_NaN = str2double({tmd.constructions.conv_coeff_adjacent_A});
   param_ids_in_construction = [param_ids_in_construction {tmd.constructions(isnan(filter_NaN)).conv_coeff_adjacent_A}];
   
   % get only unique ones
   param_ids_in_construction = unique(param_ids_in_construction);
   param_ids_NOT_in_parameters = setdiff(param_ids_in_construction,param_ids);
   param_ids_NOT_in_parameters = setdiff(param_ids_NOT_in_parameters,{''});
   
   if ~isempty(param_ids_NOT_in_parameters)
      
      % get inconsistent indices
      idx = find(ismember({tmd.constructions.conv_coeff_adjacent_A},param_ids_NOT_in_parameters));
      
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(param_ids_NOT_in_parameters,idx);
      
      error('Construction:Inconsistency',['conv_coeff_adjacent_A of %s/s %s are inconsistent with respect to %s.\n'...
         'Unknown %s identifier/s:\t %s '],...
         lower(Constants.construction_name_str),idx_str,lower(Constants.parameter_name_str),lower(Constants.parameter_name_str),ids_str);
   end
   
   % check if parameter identifiers in conv_coeff_adjacentB exists
   param_ids_in_construction = Constants.EMPTY_str;
   filter_NaN = str2double({tmd.constructions.conv_coeff_adjacent_B});
   param_ids_in_construction = [param_ids_in_construction {tmd.constructions(isnan(filter_NaN)).conv_coeff_adjacent_B}];
   
   % get only unique ones
   param_ids_in_construction = unique(param_ids_in_construction);
   param_ids_NOT_in_parameters = setdiff(param_ids_in_construction,param_ids);
   param_ids_NOT_in_parameters = setdiff(param_ids_NOT_in_parameters,{''});
   if ~isempty(param_ids_NOT_in_parameters)
      
      % get inconsistent indices
      idx = find(ismember({tmd.constructions.conv_coeff_adjacent_B},param_ids_NOT_in_parameters));
      
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(param_ids_NOT_in_parameters,idx);
      
      error('Construction:Inconsistency',['conv_coeff_adjacent_B of %s/s %s are inconsistent with respect to %ss.\n'...
         'Unknown %s identifier/s:\t %s '],...
         lower(Constants.material_name_str),idx_str,lower(Constants.parameter_name_str),lower(Constants.parameter_name_str),ids_str);
   end
   
   % WINDOW
   % check if parameter identifier in U_cond_conv exists
   param_ids_in_window = Constants.EMPTY_str;
   filter_NaN = str2double({tmd.windows.U_value});
   param_ids_in_window = [param_ids_in_window {tmd.windows(isnan(filter_NaN)).U_value}];
   
   % get only unique ones
   param_ids_in_window = unique(param_ids_in_window);
   param_ids_NOT_in_parameters = setdiff(param_ids_in_window,param_ids);
   param_ids_NOT_in_parameters = setdiff(param_ids_NOT_in_parameters,{''});
   if ~isempty(param_ids_NOT_in_parameters)
      
      % get inconsistent indices
      idx = find(ismember({tmd.windows.U_value},param_ids_NOT_in_parameters));
      
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(param_ids_NOT_in_parameters,idx);
      
      error('Window:Inconsistency',[' U_value of %s/s %s are inconsistent with respect to %ss.\n',...
         'Unknown %s identifier/s:\t %s '],...
         lower(Constants.window),idx_str,lower(Constants.parameter_name_str),lower(Constants.parameter_name_str),ids_str);
   end
   
   % check if parameter identifier in SHGC exists
   param_ids_in_window = Constants.EMPTY_str;
   filter_NaN = str2double({tmd.windows.SHGC});
   param_ids_in_window = [param_ids_in_window {tmd.windows(isnan(filter_NaN)).SHGC}];
   
   % get only unique ones
   param_ids_in_window = unique(param_ids_in_window);
   param_ids_NOT_in_parameters = setdiff(param_ids_in_window,param_ids);
   param_ids_NOT_in_parameters = setdiff(param_ids_NOT_in_parameters,{''});
   if ~isempty(param_ids_NOT_in_parameters)
      
      % get inconsistent indices
      idx = find(ismember({tmd.windows.SHGC},param_ids_NOT_in_parameters));
      
      [ids_str,idx_str] = makeStringOfIdentifierAndIndex(param_ids_NOT_in_parameters,idx);
      
      error('Window:Inconsistency',['SHGC of %s/s %s are inconsistent with respect to %ss.\n'...
         'Unknown %s identifier/s:\t %s '],...
         lower(Constants.window_name_str),idx_str,lower(Constants.parameter_name_str),lower(Constants.parameter_name_str),ids_str);
   end
   
   tmd_consistent = true;
   tmd.is_dirty = false;
end


function [identifiers_str,idx_str] = makeStringOfIdentifierAndIndex(identifiers,idx)
   
   len = length(identifiers);
   if length(idx) > 1
      idx_str = sprintf('''%d''%s',idx(1),sprintf(',''%d''',idx(2:end)));
      if len>1
         identifiers_str = sprintf('''%s''%s',identifiers{1},sprintf(',''%s''',identifiers{2:end}));
      else
         identifiers_str = sprintf('''%s''',identifiers{1});
      end
   else
      idx_str = sprintf('''%d''',idx);
      if len>1
         identifiers_str = sprintf('''%s''%s',identifiers{1},sprintf(',''%s''',identifiers{2:end}));
      else
         identifiers_str = sprintf('''%s''',identifiers{1});
      end
   end
   
end
