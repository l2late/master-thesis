function special_group = check_special_group_identifiers(group_str,key_str,zeroEntry)
   %CHECK_SPECIAL_GROUP_IDENTIFIERS Checks whether the group consisting of identifiers of elements and special identifiers is feasible or not.
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
   
   
   % For window identifiers we allow identifier '0':= No Window in building elmenent.
   
   
   
   special_group = {};
   
   % catch NaN
   if strcmp(group_str,Constants.NaN_str)
      return;
   end
   
   if zeroEntry % Case where '0' is allowed, e.g. for window list in builiding elments (No window)
      if strcmp(group_str,Constants.ZERO_str)
         special_group = {Constants.ZERO_str};
         return;
      end
   end
   
   % check conventions
   % split group elements by comma
   g_elems_cell = regexp(group_str,',','split');
   
   n_elems = length(g_elems_cell);
   
   % check if group elems fulfill identifier convention
   for i = 1:n_elems
      
      if ~isempty(ThermalModelData.check_identifier(g_elems_cell{i},key_str))
         special_group = [special_group; g_elems_cell{i}]; %#ok<AGROW>
      elseif ~isempty(ThermalModelData.check_special_identifier(g_elems_cell{i}))
         special_group = [special_group; g_elems_cell{i}]; %#ok<AGROW>
      else
         special_group = {};
         return;
      end
   end
   
end
