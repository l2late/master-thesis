function values = check_group_values(values_str)
   %CHECK_GROUP_VALUES Checks whether the group consisting of string numerics is feasible or not.
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
   
   
   
   
   values = [];
   
   % catch NaN
   if strcmp(values_str,Constants.NaN_str)
      return;
   end
   
   % catch allowed entriy 'NULL' for not yet specified
   if strcmpi(strtrim(values_str),Constants.NULL_str)
      values = {Constants.NULL_str};
      return;
   end
   
   % check conventions
   % split group elements by comma
   g_elems_cell = regexp(values_str,',','split');
   
   n_elems = length(g_elems_cell);
   
   % check if group elems values are feasible
   for i = 1:n_elems
      value = ThermalModelData.check_value(g_elems_cell{i},false);
      if isempty(value) %|| ~(str2double(value) > 0) % DS: allow for zero values
         values = [];
         return;
      end
      values = [values, str2double(value)]; %#ok<AGROW>
   end
   
end
