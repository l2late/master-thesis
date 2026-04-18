classdef ThermalModelData < matlab.mixin.Copyable
   %THERMALMODELDATA This class stores all the Data of a Building, such as geometry, material, construction type.
   %   This class stores the basic geometry, construction and
   %   building systems data required for the compilation of the building's
   %   model and necessary methods in order to set, get, load and print the
   %   data.
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
   
   
       properties(SetAccess = {?Building}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      zones@Zone = Zone.empty;                                             % stores the zone data
      building_elements@BuildingElement = BuildingElement.empty;           % stores the building element data
      constructions@Construction = Construction.empty;                     % stores the construction data
      materials@Material = Material.empty;                                 % stores the material data
      windows@Window = Window.empty;                                       % stores the window data
      parameters@Parameter = Parameter.empty;                              % stores the parameter data
      nomass_constructions@NoMassConstruction = NoMassConstruction.empty;  % stores the no mass construction data
   end % properties(SetAccess = {?Building})
   
   % stores the current data source path
   properties(SetAccess=private)
      source_files@struct = struct(Constants.zone_filename,'',Constants.buildingelement_filename,'',Constants.construction_filename,'',...
         Constants.material_filename,'',Constants.window_filename,'',Constants.parameter_filename,'',Constants.nomass_construction_filename,'');
   end % (SetAccess=private)
   
   properties(Hidden)
      data_directory_source@char = '';      % stores the path of the latest loaded directory
      data_directory_target@char = '';      % stores the path of the latest target directory of a writing process
   end % properties(Hidden)
   
   properties(SetObservable)
      is_dirty@logical = false;               % flag indicating data the building data has been modified
   end % properies(SetObservable)
   
       methods(Access = {?Building}) % IF_WITH_METACLASS_SUPPORT
   %methods  % IF_NO_METACLASS_SUPPORT
      
      % constructor
      function obj = ThermalModelData()
         
      end
      
      function delete(obj) %#ok<MANU>
         fprintfDbg(2,'%s data deleted.\n',Constants.thermalmodel_name_str);
      end
      
   end %(Access = {?Building})
   
   methods
      
      function idx = getZoneIdxFromIdentifier(obj,identifier)
         
         if isempty(obj.zones)
            error('Zones:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.zone_name_str));
         end
         
         if ~ischar(identifier)
            error('Zone:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.zone_name_str)));
         end
         
         if isempty(ThermalModelData.check_identifier(identifier,Zone.key))
            error('Zone:Identifier',Constants.error_msg_identifier(Constants.zone_name_str,identifier,Zone.key));
         end
         
         idx = find(ismember(obj.getZonesIdentifiers,identifier));
      end % getZoneIdxFromIdentifier
      
      function zone_identifiers = getZoneIdentifiersFromGroupIdentifier(obj,group_identifier_str)
         
         zone_identifiers = {};
         
         if ~ischar(group_identifier_str) || isempty(group_identifier_str)
            error('Zone:Group',Constants.error_msg_string('Group identifier'));
         end
         
         % get all group identifiers from data
         group_ids_data = [obj.zones.group];
         
         % catch unknown group identifier
         if isempty(intersect(group_ids_data,group_identifier_str))
            error('Zone:Group',Constants.error_msg_unknown_identifier(group_identifier_str,sprintf('%s group',Constants.zone_name_str)));
         end
         
         n_zones = length(obj.zones);
         
         for i = 1:n_zones
            
            if isempty(find(ismember(obj.zones(i).group,group_identifier_str),1))
               continue;
            else
               zone_identifiers = [zone_identifiers; obj.zones(i).identifier]; %#ok<AGROW>
            end
            
         end
      end % getZoneIdentifiersFromGroupIdentifier
      
      function setZoneGroups(obj,identifierOrIdx,groups_cell_str)
         
         if isempty(obj.zones)
            error('Zones:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.zone_name_str));
         end
         
         if ~iscellstr(groups_cell_str) || isempty(groups_cell_str)
            error('Zones:GroupId','Argument 2 is required to be a non-empty cell array of group identifiers (String).\n');
         end
         
         n_zones = length(obj.zones);
         
         if isnumeric(identifierOrIdx) && ~isempty(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('Zones:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_zones
               error('Zones:Index','Index out of range.\nChose index between 1 and %d.',n_zones);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_identifier(identifierOrIdx,Zone.key))
            
            idx = obj.getZoneIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('Zones:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('Zones:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('Zones:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         % make comma separated string
         if length(groups_cell_str) > 1
            group_ids = strcat(groups_cell_str{1},sprintf(',%s',groups_cell_str{2:end}));
         else
            group_ids = groups_cell_str{1};
         end
         
         group = ThermalModelData.check_zone_group(group_ids);
         
         if isempty(group)
            error('Zones:Group_id',Constants.error_msg_zone_group(Constants.zone_name_str,group_ids));
         elseif strcmp(group,Constants.NULL_str)
            error('Zones:Group_id',Constants.error_msg_zone_group(Constants.zone_name_str,group_ids));
         end
         
         obj.zones(identifierOrIdx).group = group;
         
      end % setZoneGroups
      
      function zones_ids = getZonesIdentifiers(obj)
         if ~isempty(obj.zones)
            zones_ids = {obj.zones.identifier}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.zone_name_str));
            zones_ids = Constants.EMPTY_str;
         end
      end % getZonesIdentifiers
      
      function zones_descrp = getZonesDescriptions(obj)
         if ~isempty(obj.zones)
            zones_descrp = {obj.zones.description}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.zone_name_str));
            zones_descrp = Constants.EMPTY_str;
         end
      end % getZonesDescriptions
      
      function zoneData = convertZone2Cell(obj)
         
         if isempty(obj.zones)
            error('Zones:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.zone_name_str));
         else
            n_zones = length(obj.zones);
            group_id = cell(n_zones,1);
            
            % group_identifiers to string
            for i = 1:n_zones
               group_id{i} = [sprintf('%s,',obj.zones(i).group{1:end-1}) sprintf('%s',obj.zones(i).group{end})];
            end
            zoneData = [Constants.zone_file_header; {obj.zones.identifier}' {obj.zones.description}' {obj.zones.area}' {obj.zones.volume}' group_id];
         end
      end % convertZone2Cell
      
      function printZoneData(obj)
         
         if isempty(obj.zones)
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.zone_name_str))
            return;
         end
         
         data = obj.convertZone2Cell;
         [rows,cols] = size(data);
         
         % get max length of all strings for nice format
         len_max_str_cols = max(cellfun(@(x) length(num2str(x)),data));
         
         % print
         % first row of data is the header
         fprintfDbg(0,'\n %s DATA (%d %s/s)\n',upper(Constants.zone_name_str),rows-1,lower(Constants.zone_name_str));
         fprintfDbg(0,'%s\n',repmat('-',1,sum(len_max_str_cols+2)));
         for i = 1:rows
            for j=1:cols
               format = strcat('  %',num2str(len_max_str_cols(j)),'s');
               fprintfDbg(0,format,num2str(data{i,j}));
            end
            fprintfDbg(0,'\n');
         end
         fprintfDbg(0,'\n');
      end % printZoneData
      
      function idx = getBuildingElementIdxFromIdentifier(obj,identifier)
         
         if isempty(obj.building_elements)
            error('BuildingElements:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.buildingelement_name_str));
         end
         
         if isempty(ThermalModelData.check_identifier(identifier,BuildingElement.key))
            error('BuildingElement:Identifier',Constants.error_msg_identifier(Constants.buildingelement_name_str,identifier,BuildingElement.key));
         end
         
         idx = find(ismember(obj.getBuildingElementsIdentifiers,identifier));
      end % getBuildingElementIdxFromIdentifier
      
      function b_elems_ids = getBuildingElementsIdentifiers(obj)
         if ~isempty(obj.building_elements)
            b_elems_ids = {obj.building_elements.identifier}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.buildingelement_name_str));
            b_elems_ids = Constants.EMPTY_str;
         end
      end % getBuildingElementsIdentifiers
      
      function b_elems_descrp = getBuildingElementsDescriptions(obj)
         if ~isempty(obj.building_elements)
            b_elems_descrp = {obj.building_elements.description}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.buildingelement_name_str));
            b_elems_descrp = Constants.EMPTY_str;
         end
      end % getBuildingElementsDescriptions
      
      function b_elems_identifiers = getAllBEIdsFromZoneId(obj,zone_identifier)
         
         b_elems_identifiers = {};
         
         if isempty(ThermalModelData.check_identifier(zone_identifier,Zone.key))
            error('ThermalModelData:ZoneIdentifier',Constants.error_msg_identifier(Constants.zone_name_str,zone_identifier,Zone.key));
         end
         
         if ~isempty(obj.building_elements)
            idx_be_adjacent_A = ismember({obj.building_elements.adjacent_A},zone_identifier);
            idx_be_adjacent_B = ismember({obj.building_elements.adjacent_B},zone_identifier);
            
            b_elems_identifiers = union({obj.building_elements(idx_be_adjacent_A).identifier},{obj.building_elements(idx_be_adjacent_B).identifier});
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.buildingelement_name_str));
         end
      end % getAllBEIdsFromZoneId
      
      function buildingElementData = convertBuildingElement2Cell(obj)
         
         if isempty(obj.building_elements)
            error('BuildingElements:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.buildingelement_name_str));
         else
            n_building_elements = length(obj.building_elements);
            
            vertices = cell(n_building_elements,1);
            
            % vertices and windows identifiers to string
            for i = 1:n_building_elements
               vertices{i} = '';
               n_vertices = length(obj.building_elements(i).vertices);
               for j = 1:n_vertices
                  if j ~= n_vertices
                     vertices{i} = [vertices{i},sprintf('(%f,%f,%f),',obj.building_elements(i).vertices(j).x,obj.building_elements(i).vertices(j).y,obj.building_elements(i).vertices(j).z)];
                  else
                     vertices{i} = [vertices{i},sprintf('(%f,%f,%f)',obj.building_elements(i).vertices(j).x,obj.building_elements(i).vertices(j).y,obj.building_elements(i).vertices(j).z)];
                  end
               end
            end
            buildingElementData = [Constants.building_element_file_header; {obj.building_elements.identifier}' {obj.building_elements.description}'...
               {obj.building_elements.construction_identifier}' {obj.building_elements.adjacent_A}' {obj.building_elements.adjacent_B}'...
               {obj.building_elements.window_identifier}' {obj.building_elements.area}' vertices];
         end
      end % convertBuildingElement2Cell
      
      function printBuildingElementData(obj,varargin)
         
         if isempty(obj.building_elements)
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.buildingelement_name_str))
            return;
         end
         
         data = obj.convertBuildingElement2Cell;
         printOnlyWindows = false;
         if ~isempty(varargin) && length(varargin) == 1
            
            % varargin == 'window': print only BE with windows
            if strcmpi(varargin{1},Constants.window_name_str)
               printOnlyWindows = true;
               data = data(~cellfun(@isempty,data(:,6)),:); % 6 is column of window identifiers
            else
               fprintfDbg(0,'Unknown argument. Printing complete %s data instead.\n',Constants.buildingelement_name_str);
            end
         end
         
         [rows,cols] = size(data);
         
         % get max length of all strings for nice format
         len_max_str_cols = max(cellfun(@(x) length(num2str(x)),data));
         
         % print
         % first row of data is the header
         if printOnlyWindows
            fprintfDbg(0,'\n %s DATA (%d %s/s with %ss)\n',upper(Constants.buildingelement_name_str),rows-1,lower(Constants.buildingelement_name_str),lower(Constants.window_name_str));
         else
            fprintfDbg(0,'\n %s DATA (%d %s/s)\n',upper(Constants.buildingelement_name_str),rows-1,lower(Constants.buildingelement_name_str));
         end
         fprintfDbg(0,'%s\n',repmat('-',1,sum(len_max_str_cols+2)));
         
         for i = 1:rows
            for j=1:cols
               format = strcat('  %',num2str(len_max_str_cols(j)),'s');
               fprintfDbg(0,format,num2str(data{i,j}));
            end
            fprintfDbg(0,'\n');
         end
         fprintfDbg(0,'\n');
      end % printBuildingElementData
      
      function idx = getConstructionIdxFromIdentifier(obj,identifier)
         
         if isempty(obj.constructions)
            error('Construction:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.construction_name_str));
         end
         
         if ~ischar(identifier)
            error('Construction:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.construction_name_str)));
         end
         
         if isempty(ThermalModelData.check_identifier(identifier,Construction.key))
            error('Construction:Identifier',Constants.error_msg_identifier(Constants.construction_name_str,identifier,Construction.key));
         end
         
         idx = find(ismember(obj.getConstructionsIdentifiers,identifier));
      end % getConstructionIdxFromIdentifier
      
      function ct_ids = getConstructionsIdentifiers(obj)
         if ~isempty(obj.constructions)
            ct_ids = {obj.constructions.identifier}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.construction_name_str));
            ct_ids = Constants.EMPTY_str;
         end
      end % getConstructionsIdentifiers
      
      function ct_descrp = getConstructionsDescriptions(obj)
         if ~isempty(obj.constructions)
            ct_descrp = {obj.constructions.description}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.construction_name_str));
            ct_descrp = Constants.EMPTY_str;
         end
      end % getConstructionsDescriptions
      
      function addConstruction(obj,identifier,description,material_identifiers,thickness,conv_heat_adjA,conv_heat_adjB)
         
         if ~iscellstr(material_identifiers)
            error('addConstruction:MaterialIdentifiers','Argument 3 is required to be a cell array of %s identifiers (String).\n',Constants.material_name_str);
         end
         
         if ~iscellstr(thickness)
            error('addConstruction:Thickness','Argument 4 is required to be a cell array (String).\n');
         end
         
         n_layers = length(material_identifiers);
         if ~(length(thickness) == n_layers)
            error('addConstruction:NumberOfLayers',Constants.error_group_consistency(Constants.material_name_str,'thickness'));
         end
         
         % check conventions
         Construction.check(identifier,description,material_identifiers,thickness,num2str(conv_heat_adjA),num2str(conv_heat_adjB));
         
         if ~isempty(obj.constructions)
            
            % check uniquenss of identifier
            ThermalModelData.check_uniqueness_id(obj.getConstructionsIdentifiers,identifier,Constants.construction_name_str);
            obj.constructions = [obj.constructions,Construction(identifier,ThermalModelData.check_free_description(description),material_identifiers,thickness,conv_heat_adjA,conv_heat_adjB)];
            obj.is_dirty = true;
         else
            obj.constructions = [obj.constructions,Construction(identifier,ThermalModelData.check_free_description(description),material_identifiers,thickness,conv_heat_adjA,conv_heat_adjB)];
         end
         
      end % addConstruction
      
      function removeConstruction(obj,identifierOrIdx)
         
         if isempty(obj.constructions)
            error('Constructions:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.construction_name_str));
         end
         
         n_constructions = length(obj.constructions);
         
         if isnumeric(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('Construction:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_constructions
               error('Construction:Index','Index out of range.\nChose index between 1 and %d.',n_constructions);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_identifier(identifierOrIdx,Construction.key))
            
            idx = obj.getConstructionIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('Constructions:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('Constructions:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('Constructions:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         obj.constructions = [obj.constructions(1:identifierOrIdx-1) obj.constructions(identifierOrIdx+1:end)];
         obj.is_dirty = true;
         
      end % removeConstruction
      
      function constructionData = convertConstruction2Cell(obj)
         
         if isempty(obj.constructions)
            error('Constructions:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.construction_name_str));
         else
            n_constructions = length(obj.constructions);
            material_identifiers = cell(n_constructions,1);
            thickness = cell(n_constructions,1);
            
            
            % material_identifiers and thickness to string
            for i = 1:n_constructions
               material_identifiers{i} = sprintf('%s,',obj.constructions(i).material_identifiers{:});
               material_identifiers{i}(end) = '';
               thickness{i} = sprintf('%s,',obj.constructions(i).thickness{:});
               thickness{i}(end) = '';
            end
            constructionData = [Constants.construction_file_header; {obj.constructions.identifier}' {obj.constructions.description}'...
               material_identifiers thickness {obj.constructions.conv_coeff_adjacent_A}' {obj.constructions.conv_coeff_adjacent_B}'];
         end
      end % convertConstruction2Cell
      
      function printConstructionData(obj)
         
         if isempty(obj.constructions)
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.construction_name_str))
            return;
         end
         
         data = obj.convertConstruction2Cell;
         [rows,cols] = size(data);
         
         % get max length of all strings for nice format
         len_max_str_cols = max(cellfun(@(x) length(num2str(x)),data));
         
         % print
         % first row of data is the header
         fprintfDbg(0,'\n %s DATA (%d %s/s)\n',upper(Constants.construction_name_str),rows-1,lower(Constants.construction_name_str));
         fprintfDbg(0,'%s\n',repmat('-',1,sum(len_max_str_cols+2)));
         
         for i = 1:rows
            for j=1:cols
               format = strcat('  %',num2str(len_max_str_cols(j)),'s');
               fprintfDbg(0,format,num2str(data{i,j}));
            end
            fprintfDbg(0,'\n');
         end
         fprintfDbg(0,'\n');
      end % printConstructionData
      
      function idx = getMaterialIdxFromIdentifier(obj,identifier)
         
         if isempty(obj.materials)
            error('Material:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.material_name_str));
         end
         
         if ~ischar(identifier)
            error('Material:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.material_name_str)));
         end
         
         if isempty(ThermalModelData.check_identifier(identifier,Material.key))
            error('Material:Identifier',Constants.error_msg_identifier(Constants.material_name_str,identifier,Material.key));
         end
         
         idx = find(ismember(obj.getMaterialsIdentifiers,identifier));
         
      end % getMaterialsIdxFromIdentifier
      
      function mat_ids = getMaterialsIdentifiers(obj)
         if ~isempty(obj.materials)
            mat_ids = {obj.materials.identifier}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.material_name_str));
            mat_ids = Constants.EMPTY_str;
         end
      end % getMaterialsIdentifiers
      
      function mat_descrp = getMaterialsDescriptions(obj)
         if ~isempty(obj.materials)
            mat_descrp = {obj.materials.description}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.material_name_str));
            mat_descrp = Constants.EMPTY_str;
         end
      end % getMaterialsDescriptions
      
      function addMaterial(obj,identifier,description,spec_heat_cap,spec_therm_res,density)
         
         % check conventions
         if ~ischar(identifier)
            error('Material:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.material_name_str)));
         end
         
         if ~ischar(description)
            error('Material:Type',Constants.error_msg_string(sprintf('%s description',Constants.material_name_str)));
         end
         
         Material.check(identifier,description,num2str(spec_heat_cap),num2str(spec_therm_res),num2str(density));
         
         if ~isempty(obj.materials)
            
            % check uniquenss of identifier
            ThermalModelData.check_uniqueness_id(obj.getMaterialsIdentifiers,identifier,Constants.material_name_str);
            
            obj.materials = [obj.materials,Material(identifier,ThermalModelData.check_free_description(description),spec_heat_cap,spec_therm_res,density)];
            obj.is_dirty = true;
            
         else
            obj.materials = [obj.materials,Material(identifier,ThermalModelData.check_free_description(description),spec_heat_cap,spec_therm_res,density)];
         end
         
      end % addMaterial
      
      function removeMaterial(obj,identifierOrIdx)
         
         if isempty(obj.materials)
            error('Materials:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.material_name_str));
         end
         
         n_materials = length(obj.materials);
         
         if isnumeric(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('Materials:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_materials
               error('Materials:Index','Index out of range.\nChose index between 1 and %d.',n_materials);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_identifier(identifierOrIdx,Material.key))
            
            idx = obj.getMaterialIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('Materials:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('Materials:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('Materials:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         obj.materials = [obj.materials(1:identifierOrIdx-1) obj.materials(identifierOrIdx+1:end)];
         obj.is_dirty = true;
         
      end % removeMaterial
      
      function materialData = convertMaterial2Cell(obj)
         
         if isempty(obj.materials)
            error('Materials:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.material_name_str));
         else
            materialData = [Constants.material_file_header; {obj.materials.identifier}' {obj.materials.description}'...
               {obj.materials.specific_heat_capacity}' {obj.materials.specific_thermal_resistance}' {obj.materials.density}' {obj.materials.R_value}'];
         end
      end % convertMaterial2Cell
      
      function printMaterialData(obj)
         
         if isempty(obj.materials)
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.material_name_str))
            return;
         end
         
         data = obj.convertMaterial2Cell;
         [rows,cols] = size(data);
         
         % get max length of all strings for nice format
         len_max_str_cols = max(cellfun(@(x) length(num2str(x)),data));
         
         % print
         % first row of data is the header
         fprintfDbg(0,'\n %s DATA (%d %s/s)\n',upper(Constants.material_name_str),rows-1,lower(Constants.material_name_str));
         fprintfDbg(0,'%s\n',repmat('-',1,sum(len_max_str_cols+2)));
         for i = 1:rows
            for j=1:cols
               format = strcat('  %',num2str(len_max_str_cols(j)),'s');
               fprintfDbg(0,format,num2str(data{i,j}));
            end
            fprintfDbg(0,'\n');
         end
         fprintfDbg(0,'\n');
      end % printMaterialData
      
      function idx = getWindowIdxFromIdentifier(obj,identifier)
         
         if isempty(obj.windows)
            error('Window:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.window_name_str));
         end
         
         if ~ischar(identifier)
            error('Windows:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.window_name_str)));
         end
         
         if isempty(ThermalModelData.check_identifier(identifier,Window.key))
            error('Window:Identifier',Constants.error_msg_identifier(Constants.window_name_str,identifier,Window.key));
         end
         
         idx = find(ismember(obj.getWindowsIdentifiers,identifier));
         
      end % getWindowIdxFromIdentifier
      
      function win_ids = getWindowsIdentifiers(obj)
         if ~isempty(obj.windows)
            win_ids = {obj.windows.identifier}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.window_name_str));
            win_ids = Constants.EMPTY_str;
         end
      end % getWindowsIdentifiers
      
      function win_descrp = getWindowsDescriptions(obj)
         if ~isempty(obj.windows)
            win_descrp = {obj.windows.description}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.window_name_str));
            win_descrp = Constants.EMPTY_str;
         end
      end % getWindowsDescriptions
      
      function addWindow(obj,identifier,description,glass_area,frame_area,U_value,SHGC)
         
         % check conventions
         if ~ischar(identifier)
            error('Window:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.window_name_str)));
         end
         
         if ~ischar(description)
            error('Window:Type',Constants.error_msg_string(sprintf('%s description',Constants.window_name_str)));
         end
         
         Window.check(identifier,description,num2str(glass_area),num2str(frame_area),num2str(U_value),num2str(SHGC));
         
         if ~isempty(obj.windows)
            
            % check uniquenss of identifier
            ThermalModelData.check_uniqueness_id(obj.getWindowsIdentifiers,identifier,Constants.window_name_str);
            obj.windows = [obj.windows,Window(identifier,ThermalModelData.check_free_description(description),glass_area,frame_area,U_value,SHGC)];
            obj.is_dirty = true;
         else
            obj.windows = [obj.windows,Window(identifier,ThermalModelData.check_free_description(description),glass_area,frame_area,U_value,SHGC)];
         end
         
      end % addWindow
      
      function removeWindow(obj,identifierOrIdx)
         
         if isempty(obj.windows)
            error('Windows:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.window_name_str));
         end
         
         n_windows = length(obj.windows);
         
         if isnumeric(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('Windows:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_windows
               error('Windows:Index','Index out of range.\nChose index between 1 and %d.',n_windows);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_identifier(identifierOrIdx,Window.key))
            
            idx = obj.getWindowIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('Windows:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('Windows:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('Windows:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         obj.windows = [obj.windows(1:identifierOrIdx-1) obj.windows(identifierOrIdx+1:end)];
         obj.is_dirty = true;
         
      end % removeWindow
      
      function windowData = convertWindow2Cell(obj)
         
         if isempty(obj.windows)
            error('Windows:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.window_name_str));
         else
            windowData = [Constants.window_file_header; {obj.windows.identifier}' {obj.windows.description}' ...
               {obj.windows.glass_area}' {obj.windows.frame_area}' {obj.windows.U_value}' {obj.windows.SHGC}'];
         end
      end % convertWindow2Cell
      
      function printWindowData(obj)
         
         if isempty(obj.windows)
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.window_name_str))
            return;
         end
         
         data = obj.convertWindow2Cell;
         [rows,cols] = size(data);
         
         % get max length of all strings for nice format
         len_max_str_cols = max(cellfun(@(x) length(num2str(x)),data));
         
         % print
         % first row of data is the header
         fprintfDbg(0,'\n %s DATA (%d %s/s)\n',upper(Constants.window_name_str),rows-1,lower(Constants.window_name_str));
         fprintfDbg(0,'%s\n',repmat('-',1,sum(len_max_str_cols+2)));
         for i = 1:rows
            for j=1:cols
               format = strcat('  %',num2str(len_max_str_cols(j)),'s');
               fprintfDbg(0,format,num2str(data{i,j}));
            end
            fprintfDbg(0,'\n');
         end
         fprintfDbg(0,'\n');
      end % printWindowData
      
      function idx = getParameterIdxFromIdentifier(obj,identifier)
         
         if isempty(obj.parameters)
            error('Parameter:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.parameter_name_str));
         end
         
         if ~ischar(identifier)
            error('Parameter:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.parameter_name_str)));
         end
         
         if isempty(ThermalModelData.check_special_identifier(identifier))
            error('Parameter:Identifier',Constants.error_msg_identifier_special(Constants.parameter_name_str,identifier));
         end
         
         idx = find(ismember(obj.getParametersIdentifiers,identifier));
         
      end % getParametersIdxFromIdentifier
      
      function par_ids = getParametersIdentifiers(obj)
         if ~isempty(obj.parameters)
            par_ids = {obj.parameters.identifier}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.parameter_name_str));
            par_ids = Constants.EMPTY_str;
         end
      end % getParametersIdentifiers
      
      function par_descrp = getParametersDescriptions(obj)
         if ~isempty(obj.parameters)
            par_descrp = {obj.parameters.description}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.parameter_name_str));
            par_descrp = Constants.EMPTY_str;
         end
      end % getParametersDescriptions
      
      function addParameter(obj,identifier,description,value)
         
         % check conventions
         if ~ischar(identifier)
            error('Parameter:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.parameter_name_str)));
         end
         
         if ~ischar(description)
            error('Parameter:Type',Constants.error_msg_string(sprintf('%s description',Constants.parameter_name_str)));
         end
         
         Parameter.check(identifier,description,num2str(value));
         
         if ~isempty(obj.parameters)
            
            % check uniquenss of identifier
            ThermalModelData.check_uniqueness_id(obj.getParametersIdentifiers,identifier,Constants.parameter_name_str);
            obj.parameters = [obj.parameters,Parameter(identifier,ThermalModelData.check_free_description(description),value)];
            obj.is_dirty = true;
            
         else
            obj.parameters = [obj.parameters,Parameter(identifier,ThermalModelData.check_free_description(description),value)];
         end
         
      end % addParameter
      
      function removeParameter(obj,identifierOrIdx)
         
         if isempty(obj.parameters)
            error('Parameters:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.parameter_name_str));
         end
         
         n_parameters = length(obj.parameters);
         
         if isnumeric(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('Parameters:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_parameters
               error('Parameters:Index','Index out of range.\nChose index between 1 and %d.',n_parameters);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_special_identifier(identifierOrIdx))
            
            idx = obj.getParameterIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('Parameters:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('Parameters:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('Parameters:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         obj.parameters = [obj.parameters(1:identifierOrIdx-1) obj.parameters(identifierOrIdx+1:end)];
         obj.is_dirty = true;
         
      end % removeParameter
      
      function parameterData = convertParameter2Cell(obj)
         
         if isempty(obj.parameters)
            error('Parameters:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.parameter_name_str));
         else
            parameterData = [Constants.parameter_file_header; {obj.parameters.identifier}' {obj.parameters.description}'...
               {obj.parameters.value}'];
         end
      end % convertParameter2Cell
      
      function printParameterData(obj)
         
         if isempty(obj.parameters)
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.parameter_name_str));
            return;
         end
         
         data = obj.convertParameter2Cell;
         [rows,cols] = size(data);
         
         % get max length of all strings for nice format
         len_max_str_cols = max(cellfun(@(x) length(num2str(x)),data));
         
         % print
         % first row of data is the header
         fprintfDbg(0,'\n %s DATA (%d %s/s)\n',upper(Constants.parameter_name_str),rows-1,lower(Constants.parameter_name_str));
         fprintfDbg(0,'%s\n',repmat('-',1,sum(len_max_str_cols+2)));
         for i = 1:rows
            for j=1:cols
               format = strcat('  %',num2str(len_max_str_cols(j)),'s');
               fprintfDbg(0,format,num2str(data{i,j}));
            end
            fprintfDbg(0,'\n');
         end
         fprintfDbg(0,'\n');
      end % printParameterData
      
      function idx = getNoMassConstructionIdxFromIdentifier(obj,identifier)
         
         if isempty(obj.nomass_constructions)
            error('NoMassConstruction:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.nomass_construction_name_str));
         end
         
         if ~ischar(identifier)
            error('NoMassConstruction:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.nomass_construction_name_str)));
         end
         
         if isempty(ThermalModelData.check_identifier(identifier,NoMassConstruction.key))
            error('NoMassConstruction:Identifier',Constants.error_msg_identifier(Constants.nomass_construction_name_str,identifier));
         end
         
         idx = find(ismember(obj.getNoMassConstructionsIdentifiers,identifier));
         
      end % getNoMassConstructionIdxFromIdentifier
      
      function setNoMassConstructionDescription(obj,identifierOrIdx,description)
         
         if isempty(obj.nomass_constructions)
            error('NoMassConstruction:NoData','%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.nomass_construction_name_str));
         end
         
         if ~ischar(description)
            error('NoMassConstruction:Type',Constants.error_msg_string(sprintf('%s description',Constants.nomass_construction_name_str)));
         end
         
         n_nomass = length(obj.nomass_constructions);
         
         if isnumeric(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('NoMassConstruction:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_nomass
               error('NoMassConstruction:Index','Index out of range.\nChose index between 1 and %d.',n_nomass);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_identifier(identifierOrIdx,NoMassConstruction.key))
            
            idx = obj.getNoMassConstructionIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('NoMassConstruction:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('NoMassConstruction:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('NoMassConstruction:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         obj.nomass_constructions(identifierOrIdx).description = ThermalModelData.check_free_description(description);
         obj.is_dirty = true;
      end % setNoMassConstructionDescription
      
      function setNoMassConstructionUvalue(obj,identifierOrIdx,U_value)
         
         if isempty(obj.nomass_constructions)
            error('NoMassConstructions:NoData','%s data does not contain %ss yet .\n',Constants.thermalmodel_name_str,lower(Constants.nomass_construction_name_str));
         end
         
         n_nomass = length(obj.nomass_constructions);
         
         if isnumeric(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('NoMassConstruction:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_nomass
               error('NoMassConstruction:Index','Index out of range.\nChose index between 1 and %d.',n_nomass);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_identifier(identifierOrIdx,NoMassConstruction.key))
            
            idx = obj.getNoMassConstructionIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('NoMassConstruction:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('NoMassConstruction:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('NoMassConstruction:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         nomass_U_value = ThermalModelData.check_value(num2str(U_value),true);
         if isempty(nomass_U_value) || strcmp(nomass_U_value,Constants.NULL_str)
            error('NoMassConstruction:Value',Constants.error_msg_value(Constants.nomass_construction_name_str,num2str(U_value),'value',true,'> 0'));
         elseif ~isnan(str2double(nomass_U_value)) && ~(str2double(nomass_U_value) > 0)
            error('NoMassConstruction:Value',Constants.error_msg_value(Constants.nomass_construction_name_str,num2str(U_value),'value',true,'> 0'));
         end
         
         obj.nomass_constructions(identifierOrIdx).U_value = nomass_U_value;
         obj.is_dirty = true;
      end %setNoMassConstructionValue
      
      function nomass_ids = getNoMassConstructionsIdentifiers(obj)
         if ~isempty(obj.nomass_constructions)
            nomass_ids = {obj.nomass_constructions.identifier}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.nomass_construction_name_str));
            nomass_ids = Constants.EMPTY_str;
         end
      end % getNoMassConstructionsIdentifiers
      
      function nomass_descrp = getNoMassConstructionsDescriptions(obj)
         if ~isempty(obj.nomass_constructions)
            nomass_descrp = {obj.nomass_constructions.description}';
         else
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.nomass_construction_name_str));
            nomass_descrp = Constants.EMPTY_str;
         end
      end % getNoMassConstructionsDescriptions
      
      function addNoMassConstruction(obj,identifier,description,U_value)
         
         % check conventions
         if ~ischar(identifier)
            error('NoMassConstruction:Type',Constants.error_msg_string(sprintf('%s identifier',Constants.nomass_construction_name_str)));
         end
         
         if ~ischar(description)
            error('NoMassConstruction:Type',Constants.error_msg_string(sprintf('%s description',Constants.nomass_construction_name_str)));
         end
         
         NoMassConstruction.check(identifier,description,num2str(U_value));
         
         if ~isempty(obj.nomass_constructions)
            
            % check uniquenss of identifier
            ThermalModelData.check_uniqueness_id(obj.getNoMassConstructionsIdentifiers,identifier,Constants.nomass_construction_name_str);
            obj.nomass_constructions = [obj.nomass_constructions,NoMassConstruction(identifier,ThermalModelData.check_free_description(description),U_value)];
            obj.is_dirty = true;
            
         else
            obj.nomass_constructions = [obj.nomass_constructions,NoMassConstruction(identifier,ThermalModelData.check_free_description(description),U_value)];
         end
         
      end % addNoMassConstruction
      
      function removeNoMassConstruction(obj,identifierOrIdx)
         
         if isempty(obj.nomass_constructions)
            error('NoMassConstructions:NoData','%s data does not contain %ss.\n',Constants.thermalmodel_name_str,lower(Constants.nomass_construction_name_str));
         end
         
         if isnumeric(identifierOrIdx)
            
            if floor(identifierOrIdx) ~= ceil(identifierOrIdx)
               error('NoMassConstruction:Index','Index must be an integer.\n');
            end
            
            if identifierOrIdx<=0 || identifierOrIdx > n_nomass
               error('NoMassConstruction:Index','Index out of range.\nChose index between 1 and %d.',n_nomass);
            end
            
         elseif ischar(identifierOrIdx) && ~isempty(ThermalModelData.check_identifier(identifierOrIdx,NoMassConstruction.key))
            
            idx = obj.getNoMassConstructionIdxFromIdentifier(identifierOrIdx);
            
            if isempty(idx)
               error('NoMassConstruction:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
            end
            identifierOrIdx = idx;
            
         elseif ischar(identifierOrIdx)
            error('NoMassConstruction:Identifier','Unknown identifier ''%s''.\n',identifierOrIdx);
         else
            error('NoMassConstruction:Argument','Argument error. Illegal index or unknown identifier.\n');
         end
         
         obj.nomass_constructions = [obj.nomass_constructions(1:identifierOrIdx-1) obj.nomass_constructions(identifierOrIdx+1:end)];
         obj.is_dirty = true;
         
      end % removeNoMassConstruction
      
      function noMassData = convertNoMassConstruction2Cell(obj)
         
         noMassData = [Constants.nomass_construction_file_header; {obj.nomass_constructions.identifier}' {obj.nomass_constructions.description}'...
            cellfun(@num2str,{obj.nomass_constructions.U_value}','UniformOutput',0)];

      end % convertNoMassConstruction2Cell
      
      function printNoMassConstructionData(obj)
         
         if isempty(obj.nomass_constructions)
            fprintfDbg(1,'%s data does not contain %ss yet.\n',Constants.thermalmodel_name_str,lower(Constants.nomass_construction_name_str));
            return;
         end
         
         data = obj.convertNoMassConstruction2Cell;
         [rows,cols] = size(data);
         
         % get max length of all strings for nice format
         len_max_str_cols = max(cellfun(@(x) length(num2str(x)),data));
         
         % print
         % first row of data is the header
         fprintfDbg(0,'\n %s DATA (%d %s/s)\n',upper(Constants.nomass_construction_name_str),rows-1,lower(Constants.nomass_construction_name_str));
         fprintfDbg(0,'%s\n',repmat('-',1,sum(len_max_str_cols+2)));
         for i = 1:rows
            for j=1:cols
               format = strcat('  %',num2str(len_max_str_cols(j)),'s');
               fprintfDbg(0,format,num2str(data{i,j}));
            end
            fprintfDbg(0,'\n');
         end
         fprintfDbg(0,'\n');
      end % printNoMassConstructionData
      
      r = evalStr(obj,str,errorStr);
      
   end % methods
   
   methods(Static)
      
      identifier = check_identifier(id_str,key)
      
      identifier = check_special_identifier(identifier_str)
      
      identifier = check_identifier_adjacent(id_str,key)
      
      description = check_free_description(descr_str)
      
      value = check_value(value_str,isParamId)
      
      zone_group = check_zone_group(group_str)
      
      group = check_group_identifiers(group_str,key_str,emptyEntry)
      
      special_group = check_special_group_identifiers(group_str,key_str,zeroEntry)
      
      values = check_group_values(values_str)
            
      check_file_extension(ext,supported_extensions,fileXLS,type)
      
      check_xls_file_header(header_cell,correct_header_cell,fileXLS,type)
   end % methods(Static)
   
   methods(Access=private,Static)
      
      [vertices,tf_white_space,tf_in_plane] = check_vertices(vertice_str)
      
      check_uniqueness_id(currentIdsCell,newId,typeStr)
      
      zone = check_zone_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
      
      buildingelement = check_buildingelement_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
      
      construction = check_construction_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
      
      nomass_construction = check_nomass_construction_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
      
      material = check_material_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
      
      window = check_window_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
      
      parameter = check_parameter_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
      
   end % methods(Access=private,Static)
end % classdef
