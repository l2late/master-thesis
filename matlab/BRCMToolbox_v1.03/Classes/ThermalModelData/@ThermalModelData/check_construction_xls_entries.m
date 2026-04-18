function construction = check_construction_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
   %CHECK_CONSTRUCTION_XLS_ENTRIES Checks whether construction data from .xls file fulfills convention.
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
   
   
   
   
   construction = Construction.empty;
   props = properties(construction);
   
   % check identifier
   identifier = ThermalModelData.check_identifier(entriesCell{1},Construction.key);
   if isempty(identifier)
      error('XLSFile:Identifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx),...
         Constants.error_msg_identifier(element_str,entriesCell{1},Construction.key)]);
   end
   
   % check description
   description = ThermalModelData.check_free_description(entriesCell{2});
   
   % check the set of material identifiers
   % catch: NaN and illegal identifiers
   material_identifiers = ThermalModelData.check_group_identifiers(entriesCell{3},Material.key,false);
   if isempty(material_identifiers)
      error('XLSFile:MaterialIdentifiers',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_group_identifiers(element_str,entriesCell{3},Material.key)]);
   end
   
   props_layer = properties(Constants.layer_name_str);
   
   thickness = regexp(entriesCell{4},',','split');
   
   % check if size of groups (material identifiers, thickness) are equal
   if (~strcmp(material_identifiers(1),Constants.NULL_str) && ~strcmp(thickness(1),Constants.NULL_str)) && ~(length(material_identifiers)==length(thickness))
      error('XLSFile:GroupConsistence',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2,colStartIdx+3),...
         Constants.error_group_consistency(element_str,props_layer{2})]);
   end
   
   % check convective heat transfer coefficient of adjacent zones
   % Adjacent_A
   % catch: NaN and illegal parameter identifier
   conv_coeff_adjacent_A = ThermalModelData.check_value(entriesCell{5},true);
   if isempty(conv_coeff_adjacent_A)
      error('XLSFile:ConvectiveHeatCoefficientAdjacentA',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
         Constants.error_msg_value(element_str,entriesCell{5},props{4},true,'> 0')]);
      % catch: value < 0
      % str2double(value) can be NaN if value is Parameter identifier
   elseif ~isnan(str2double(conv_coeff_adjacent_A)) && ~(str2double(conv_coeff_adjacent_A)>=0)
      error('XLSFile:ConvectiveHeatCoefficientAdjacentA',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
         Constants.error_msg_value(element_str,entriesCell{5},props{4},true,'> 0')]);
   end
   
   % Adjacent_B
   % catch: NaN and illegal parameter identifier
   conv_coeff_adjacent_B = ThermalModelData.check_value(entriesCell{6},true);
   if isempty(conv_coeff_adjacent_B)
      error('XLSFile:ConvectiveHeatCoefficientAdjacentB',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+5),...
         Constants.error_msg_value(element_str,entriesCell{6},props{5},true,'> 0')]);
      % catch: value < 0
      % str2double(value) can be NaN if value is Parameter identifier
   elseif ~isnan(str2double(conv_coeff_adjacent_B)) && ~(str2double(conv_coeff_adjacent_B)>=0)
      error('XLSFile:ConvectiveHeatCoefficientAdjacentB',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+5),...
         Constants.error_msg_value(element_str,entriesCell{6},props{5},true,'> 0')]);
   end
      
   construction = [construction,Construction(identifier,description,material_identifiers,thickness,conv_coeff_adjacent_A,conv_coeff_adjacent_B)];
   
end
