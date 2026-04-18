function description = check_free_description(descr_str)
   %CHECK_FREE_DESCRIPTION Checks whether the description of a specific type and assigns special values if necessary.
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
   
   
   
   
   description = Constants.EMPTY_str;
   
   % catch string 'NaN' from a precedent conversion of empty xls cells to strings
   if strcmp(descr_str,Constants.NaN_str)
      return;
   elseif strcmpi(descr_str,Constants.NULL_str)
      description = Constants.NULL_str;
   elseif strcmp(strtrim(descr_str),Constants.EMPTY_str)
      return;
   else
      description = descr_str;
   end
   
end
