function buildingelement = check_buildingelement_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
   %CHECK_BUILDINGELEMENT_XLS_ENTRIES Checks whether building element data from .xls file fulfills convention.
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
   
   
   
   
   buildingelement = BuildingElement.empty;
   props = properties(buildingelement);
   
   % check identifier
   identifier = ThermalModelData.check_identifier(entriesCell{1},BuildingElement.key);
   if isempty(identifier)
      error('XLSFile:Identifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx),...
         Constants.error_msg_identifier(element_str,entriesCell{1},BuildingElement.key)]);
   end
   
   % check description
   description = ThermalModelData.check_free_description(entriesCell{2});
   
   % check constructions or no mass constructions identifiers, catch allowed 'NULL'
   if ~strcmpi(strtrim(entriesCell{3}),Constants.NULL_str)
      c_id = ThermalModelData.check_identifier(entriesCell{3},Construction.key);
      noMassC_id = ThermalModelData.check_identifier(entriesCell{3},NoMassConstruction.key);
      
      if ~isempty(c_id)
         construction_id = c_id;
      elseif ~isempty(noMassC_id)
         construction_id = noMassC_id;
      else
         error('XLSFile:ConstructionIdentifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
            Constants.error_msg_identifier(Constants.construction_name_str,entriesCell{3},Construction.key),...
            Constants.error_msg_identifier(Constants.nomass_construction_name_str,entriesCell{3},NoMassConstruction.key)]);
      end
   else
      construction_id = Constants.NULL_str;
   end
   
   % check adjacent_A identifier
   adj_A = ThermalModelData.check_identifier_adjacent(entriesCell{4},Zone.key);
   if isempty(adj_A)
      error('XLSFile:AdjacentAIdentifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
         Constants.error_msg_identifierAdjacent(entriesCell{4},Zone.key)]);
   end
   
   % check adjacent_B identifier
   adj_B = ThermalModelData.check_identifier_adjacent(entriesCell{5},Zone.key);
   if isempty(adj_B)
      error('XLSFile:AdjacentBIdentifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
         Constants.error_msg_identifierAdjacent(entriesCell{5},Zone.key)]);
   end
   
   % check: at least one identifier in adjacent_A or adjacent_B must be a zone identifier
   if (~strcmp(adj_A,Constants.NULL_str) && ~strcmp(adj_B,Constants.NULL_str)) && (isempty(ThermalModelData.check_identifier(adj_A,Zone.key)) && isempty(ThermalModelData.check_identifier(adj_B,Zone.key)))
      error('XLSFile:AdjacentIdentifiers',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3,colStartIdx+4),...
         Constants.error_msg_identifierAdjacentZone(element_str)]);
   end
   
   % check: if no mass construction defined, then adjacent_A and adjacent_B
   % are not allowed to be equal
   if ~isempty(noMassC_id)
      
      if strcmp(adj_A,adj_B)
         error('XLSFile:AdjacentIdentifiers',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3,colStartIdx+4),...
            '%s and %s are not allowed to be equal if a %s is specified.\n'],props{4},props{5},lower(Constants.nomass_construction_name_str));
      end
      
   end
   
   % check window identifier: convention and zero is valid if building
   % element has no window
   % case: window not specified
   if ~strcmpi(strtrim(entriesCell{6}),Constants.NULL_str)
      % case: no window ('NaN','0')
      if ~(strcmpi(strtrim(entriesCell{6}),Constants.NaN_str) || strcmpi(strtrim(entriesCell{6}),Constants.ZERO_str))
         
         window_identifier = ThermalModelData.check_identifier(entriesCell{6},Window.key);
         if isempty(window_identifier)
            error('XLSFile:WindowIdentifiers',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+5),...
               Constants.error_msg_identifier(Constants.window_name_str,entriesCell{6},Window.key)]);
         end
         
         % check: if window defined, then adj_A or adj_B must be AMB
         if ~(strcmp(adj_A,Constants.ambient_identifier) || strcmp(adj_B,Constants.ambient_identifier))
            error('XLSFile:AdjacentIdentifiers',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3,colStartIdx+4),...
               '%s specified, but no ''%s'' identifier found in %s or %s.\n'],Constants.window_name_str,Constants.ambient_identifier,props{4},props{5});
         end
         
      else
         window_identifier = Constants.EMPTY_str;
      end
   else
      window_identifier = Constants.NULL_str;
   end
   
   % check area
   area = ThermalModelData.check_value(entriesCell{7},false);
   
   % pass vertices as cell of string
   [vertices,no_white_spaces,in_plane] = ThermalModelData.check_vertices(entriesCell{8});
   if isa(vertices,Constants.vertex_name_str) && isempty(vertices)
      if ~no_white_spaces
         error('XLSFile:Vertices',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+7),...
            '\nVertices ''%s'' contain white-space character. Please remove all of them.\n'],entriesCell{8});
      elseif ~in_plane
         error('XLSFile:Vertices',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+7),...
            '\nVertices ''%s'' are not in a plane within tolerance %.3f [m].\n'],entriesCell{8},Constants.tol_planarity);
      else
         error('XLSFile:Vertices',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+7),'Vertices ''%s'' do not fulfill convention.\n'],entriesCell{8});
      end
   end
   
   if strcmp(vertices,Constants.EMPTY_str) && strcmp(area,Constants.EMPTY_str)
      error('XLSFile:VerticesArea',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+7,colStartIdx+8),'Vertices and %s cannot both be empty.\n'],props{7});
   elseif ~(strcmp(area,Constants.NULL_str) || strcmp(area,Constants.EMPTY_str)) && ~(str2double(area)>0)
      error('XLSFile:Area',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+7),...
         Constants.error_msg_value(element_str,entriesCell{7},props{7},false,'> 0')]);
   end
   
   buildingelement = [buildingelement,BuildingElement(identifier,description,construction_id,adj_A,adj_B,window_identifier,vertices,area)];
   
   % if both vertice and area are defined, than the area computed out of
   % the vertices must be equal to the given area within a certain
   % tolerance
   if ~(strcmp(buildingelement.area,Constants.EMPTY_str) && ~strcmp(buildingelement.area,Constants.NULL_str)) && isa(buildingelement.vertices,Constants.vertex_name_str)
      area_vert = buildingelement.computeArea;
      
      if ~(abs(area_vert-str2double(buildingelement.area)) < Constants.tol_area)
         error('XLSFile:VerticesArea',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+7,colStartIdx+8),'Vertices and %s are inconsistent. Absolute difference between areas exceeds tolerance %f.\n'],props{7},Constants.tol_area);
      end
   elseif strcmp(buildingelement.area,Constants.EMPTY_str) && isa(buildingelement.vertices,Constants.vertex_name_str)
      buildingelement.area = num2str(buildingelement.computeArea,Constants.num2str_precision);
   end
   
end
