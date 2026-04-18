function group = check_group_identifiers(group_str,key_str,emptyEntry)
   %CHECK_GROUP_IDENTIFIERS Checks whether the group consisting of identifiers of elements is feasible or not.
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
   
   
   
   group = {};
   
   % catch not yet specified
   if strcmpi(strtrim(group_str),Constants.NULL_str)
      group = {Constants.NULL_str};
      return;
   end
   
   
   if emptyEntry % Case where '',NaN,0 is allowed, e.g. for window list in builiding elments (No window)
      if strcmp(strtrim(group_str),Constants.ZERO_str)
         group = {Constants.ZERO_str};
         return;
      elseif strcmp(strtrim(group_str),Constants.NaN_str)
         group = {Constants.EMPTY_str};
         return;
      elseif strcmp(strtrim(group_str),Constants.EMPTY_str)
         group = {Constants.EMPTY_str};
         return;
      end
   end
   
   % check conventions
   % split group elements by comma
   % catch NaN
   if strcmp(group_str,Constants.NaN_str)
      return;
   end
   
   g_elems_cell = regexp(group_str,',','split');
   
   n_elems = length(g_elems_cell);
   
   % check if group elems fulfill identifier convention
   for i = 1:n_elems
      identifier = ThermalModelData.check_identifier(g_elems_cell{i},key_str);
      if isempty(identifier)
         group = {};
         return;
      end
      group = [group, identifier]; %#ok<AGROW>
   end
   
end
