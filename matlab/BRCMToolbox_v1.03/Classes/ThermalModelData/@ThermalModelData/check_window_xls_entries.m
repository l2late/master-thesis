function window = check_window_xls_entries(entriesCell,rowIdx,colStartIdx,xlsFile,element_str)
   %CHECK_WINDOW_XLS_ENTRIES Checks whether window data from .xls file fulfills convention.
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
   
   
   
   
   window = Window.empty;
   props = properties(window);
   
   % check identifier
   identifier = ThermalModelData.check_identifier(entriesCell{1},Window.key);
   if isempty(identifier)
      error('XLSFile:Identifier',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx),...
         Constants.error_msg_identifier(element_str,entriesCell{1},Window.key)]);
   end
   
   % check description
   description = ThermalModelData.check_free_description(entriesCell{2});
   
   % check glass area
   glass_area = ThermalModelData.check_value(entriesCell{3},true);
   if isempty(glass_area)
      error('XLSFile:GlassArea',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},true,'>= 0')]);
      % catch: area < 0
   elseif ~isnan(str2double(glass_area)) && ~(str2double(glass_area)>=0)
      error('XLSFile:GlassArea',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+2),...
         Constants.error_msg_value(element_str,entriesCell{3},props{3},true,'>= 0')]);
   end
   
   % check frame area
   frame_area = ThermalModelData.check_value(entriesCell{4},true);
   if isempty(frame_area)
      error('XLSFile:FrameArea',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
         Constants.error_msg_value(element_str,entriesCell{4},props{4},true,'>= 0')]);
      % catch: area < 0
   elseif ~isnan(str2double(frame_area)) && ~(str2double(frame_area)>=0)
      error('XLSFile:FrameArea',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+3),...
         Constants.error_msg_value(element_str,entriesCell{4},props{4},true,'>= 0')]);
   end
   
   % U value
   % catch: NaN and illegal parameter identifier
   U_value = ThermalModelData.check_value(entriesCell{5},true);
   if isempty(U_value)
      error('XLSFile:U_value',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
         Constants.error_msg_value(element_str,entriesCell{5},props{5},true,'> 0')]);
      % catch U-value <= 0
   elseif ~isnan(str2double(U_value)) && ~(str2double(U_value)>0)
      error('XLSFile:U_value',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+4),...
         Constants.error_msg_value(element_str,entriesCell{5},props{6},true,'> 0')]);
   end
   
   % SHGC value
   % catch: NaN and illegal parameter identifier
   SHGC = ThermalModelData.check_value(entriesCell{6},true);
   if isempty(SHGC)
      error('XLSFile:SHGC',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+5),...
         Constants.error_msg_value(element_str,entriesCell{6},props{6},true,'between 0 and 1')]);
   elseif ~isnan(str2double(SHGC)) && ~(str2double(SHGC) >= 0 && str2double(SHGC) <= 1)
      error('XLSFile:SHGC',[Constants.error_msg_xlsFile(element_str,xlsFile,rowIdx,colStartIdx+5),...
         Constants.error_msg_value(element_str,entriesCell{6},props{6},true,'between 0 and 1')]);
   end
   
   window = [window,Window(identifier,description,glass_area,frame_area,U_value,SHGC)];
end
