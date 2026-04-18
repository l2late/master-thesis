function [zone_group] = check_zone_group(group_str)
   %CHECK_ZONE_GROUP Checks whether zone group is feasible or not.
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
   
   
   
   
   zone_group = {};
   
   % check if group is zero: no group assignment
   if strcmp(strtrim(group_str),Constants.NaN_str);
      zone_group = {Constants.EMPTY_str};
      return;
   elseif strcmp(strtrim(group_str),Constants.EMPTY_str);
      zone_group = {Constants.EMPTY_str};
      return;
   elseif strcmpi(strtrim(group_str),Constants.NULL_str);
      zone_group = {Constants.NULL_str};
      return;
   end
   
   % check conventions
   % split group elements by comma
   g_elems_cell = regexp(group_str,',','split');
   n_elems = length(g_elems_cell);
   
   % check if group elements fullfil convention
   for i = 1:n_elems
      
      elem = ThermalModelData.check_special_identifier(g_elems_cell{i});
      if isempty(elem)
         zone_group = {};
         return;
      end
      zone_group = [zone_group,elem];
   end
   
end
