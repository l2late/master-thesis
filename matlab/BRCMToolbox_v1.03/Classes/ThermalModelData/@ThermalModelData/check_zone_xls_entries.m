function zone = check_zone_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
   %CHECK_ZONE_XLS_ENTRIES Checks whether zone data from .xls file fulfills convention.
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
   
   
   
   
   zone = Zone.empty;
   props = properties(zone);
   
   % check identifier
   identifier = ThermalModelData.check_identifier(entriesCell{1},Zone.key);
   if isempty(identifier)
      error('XLSFile:Identifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx),...
         Constants.error_msg_identifier(element_str,entriesCell{1},Zone.key)]);
   end
   
   % check description
   description = ThermalModelData.check_free_description(entriesCell{2});
   
   % check area
   area = ThermalModelData.check_value(entriesCell{3},false);
   if isempty(area)
      error('XLSFile:Area',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},false,'> 0')]);
      % catch: area <= 0
   elseif ~strcmp(area,Constants.NULL_str) && ~(str2double(area)>0)
      error('XLSFile:Area',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},false,'> 0')]);
   end
   
   % check volume
   volume = ThermalModelData.check_value(entriesCell{4},false);
   if isempty(volume)
      error('XLSFile:Height',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
         Constants.error_msg_value(element_str,entriesCell{4},props{4},false,'> 0')]);
      % catch: volume <= 0
   elseif ~strcmp(volume,Constants.NULL_str) && ~(str2double(volume)>0)
      error('XLSFile:Height',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
         Constants.error_msg_value(element_str,entriesCell{4},props{4},false,'> 0')]);
   end
   
   % check zone group
   zone_group = ThermalModelData.check_zone_group(entriesCell{5});
   if isempty(zone_group)
      error('XLSFile:Group',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
         Constants.error_msg_zone_group(element_str,entriesCell{5})]);
   end
   zone = [zone,Zone(identifier,description,area,volume,zone_group)];
end
