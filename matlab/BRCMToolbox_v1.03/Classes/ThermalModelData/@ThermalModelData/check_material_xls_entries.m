function material = check_material_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
   %CHECK_MATERIAL_XLS_ENTRIES Checks whether the material data from .xls file fulfills convention.
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
   
   
   
   
   material = Material.empty;
   props = properties(material);
   
   % check identifier
   identifier = ThermalModelData.check_identifier(entriesCell{1},Material.key);
   if isempty(identifier)
      error('XLSFile:Identifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx),...
         Constants.error_msg_identifier(element_str,entriesCell{1},Material.key)]);
   end
   
   % check description
   description = ThermalModelData.check_free_description(entriesCell{2});
   
   % check specific heat capacity
   % catch: NaN and illegal parameter identifier
   specific_heat_capacity = ThermalModelData.check_value(entriesCell{3},true);
   %     if isempty(specific_heat_capacity)
   %         error('XLSFile:SpecificHeatCapacity',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
   %               Constants.error_msg_value(element_str,entriesCell{3},props{3},true,'> 0')]);
   %     % catch value < 0
   %     elseif ~isnan(str2double(specific_heat_capacity)) && ~(str2double(specific_heat_capacity) > 0)
   %         error('XLSFile:SpecificHeatCapacity',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
   %               Constants.error_msg_value(element_str,entriesCell{3},props{3},true,'> 0')]);
   %     end
   if ~isnan(str2double(specific_heat_capacity)) && ~(str2double(specific_heat_capacity) > 0)
      error('XLSFile:SpecificHeatCapacity',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},true,'> 0')]);
   end
   
   % check specific heat resistance
   % catch: NaN and illegal parameter identifier
   specific_thermal_resistance = ThermalModelData.check_value(entriesCell{4},true);
   %     if isempty(specific_thermal_resistance)
   %         error('XLSFile:SpecificThermalResistance',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
   %               Constants.error_msg_value(element_str,entriesCell{4},props{4},true,'> 0')]);
   %     %catch: value <= 0
   %     elseif ~isnan(str2double(specific_thermal_resistance)) && ~(str2double(specific_thermal_resistance) > 0)
   %         error('XLSFile:SpecificThermalResistance',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
   %               Constants.error_msg_value(element_str,entriesCell{4},props{4},true,'> 0')]);
   %     end
   if ~isnan(str2double(specific_thermal_resistance)) && ~(str2double(specific_thermal_resistance) > 0)
      error('XLSFile:SpecificThermalResistance',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
         Constants.error_msg_value(element_str,entriesCell{4},props{4},true,'> 0')]);
   end
   
   % check density
   % catch: NaN and illegal parameter identifier
   density = ThermalModelData.check_value(entriesCell{5},true);
   %     if isempty(density)
   %         error('XLSFile:Density',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
   %               Constants.error_msg_value(element_str,entriesCell{5},props{5},true,'> 0')]);
   %     % catch: value < 0
   %     elseif ~isnan(str2double(density)) && ~(str2double(density) >=0 )
   %             error('XLSFile:Density',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
   %               Constants.error_msg_value(element_str,entriesCell{5},props{5},true,'> 0')]);
   %     end
   if ~isnan(str2double(density)) && ~(str2double(density) >=0 )
      error('XLSFile:Density',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
         Constants.error_msg_value(element_str,entriesCell{5},props{5},true,'> 0')]);
   end
   
   
   % check R-Value
   % catch: NaN and illegal parameter identifier
   R_value = ThermalModelData.check_value(entriesCell{6},true);
   if ~isnan(str2double(R_value)) && ~(str2double(R_value) >= 0)
      error('XLSFile:R_value',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{6},props{6},true,'>= 0')]);
   end
   
   
   material = [material,Material(identifier,description,specific_heat_capacity,specific_thermal_resistance,density,R_value)];
end
