function parameter = check_parameter_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
   %CHECK_PARAMTER_XLS_ENTRIES Checks whether the parameter data from .xls file fulfills convention.
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
   
   
   
   
   parameter = Parameter.empty;
   props = properties(parameter);
   
   % check identifier/parameter has other convention, like description
   identifier = ThermalModelData.check_special_identifier(entriesCell{1});
   if isempty(identifier)
      error('XLSFile:Identifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx),...
         Constants.error_msg_identifier_special(element_str,entriesCell{1})]);
   end
   
   % check description
   description = ThermalModelData.check_free_description(entriesCell{2});
   
   % check value
   % catch: NaN and string
   value = ThermalModelData.check_value(entriesCell{3},false);
   if isempty(value)
      error('XLSFile:Value',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},false,'> 0')]);
      
      % catch negative values
   elseif ~strcmp(value,Constants.NULL_str) && ~(str2double(value)>=0)
      error('XLSFile:Value',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},false,'>= 0')]);
   end
   
   parameter = [parameter, Parameter(identifier,description,value)];
end
