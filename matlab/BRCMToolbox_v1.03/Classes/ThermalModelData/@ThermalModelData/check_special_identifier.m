function identifier = check_special_identifier(identifier_str)
   %CHECK_SPECIAL_IDENTIFIER Checks whether the identifier of a specific fulfills the special parameter identifier convention.
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
   
   
   
   
   identifier = {};
   
   % catch string 'NaN' from a precedent conversion of empty xls cells to strings
   if strcmp(strtrim(identifier_str),Constants.NaN_str)
      return;
   end
   
   if ~isempty(regexp(strtrim(identifier_str),'^[A-Za-z]$|^[A-Za-z]\w*?[A-Za-z0-9]$','match'))
      identifier = strtrim(identifier_str);
      return;
   end
   
end
