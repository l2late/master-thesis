function nomass_construction = check_nomass_construction_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
   %CHECK_WINDOW_XLS_ENTRIES Checks whether no mass construction data from .xls file fulfills convention.
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
   
   
   
   
   nomass_construction = NoMassConstruction.empty;
   props = properties(nomass_construction);
   
   % check identifier
   identifier = ThermalModelData.check_identifier(entriesCell{1},NoMassConstruction.key);
   if isempty(identifier)
      error('XLSFile:Identifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx),...
         Constants.error_msg_identifier(element_str,entriesCell{1},NoMassConstruction.key)]);
   end
   
   % check description
   description = ThermalModelData.check_free_description(entriesCell{2});
   
   % U value
   % catch: NaN and illegal parameter identifier
   U_value = ThermalModelData.check_value(entriesCell{3},true);
   if isempty(U_value)
      error('XLSFile:U_value',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},true,'> 0')]);
      % catch U-value <= 0
   elseif ~isnan(str2double(U_value)) && ~(str2double(U_value)>0)
      error('XLSFile:U_value',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},true,'> 0')]);
   end
   
   nomass_construction = [nomass_construction,NoMassConstruction(identifier,description,U_value)];
end
