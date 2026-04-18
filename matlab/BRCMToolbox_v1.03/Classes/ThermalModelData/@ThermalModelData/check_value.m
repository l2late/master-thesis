function value = check_value(value_str,isParamId)
   %CHECK_VALUE Checks whether value is feasible or not.
   % If isParamId = true, value can be a parameter identifier(string),
   % otherwise it must be a string containing a feasible numeric value
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
   
   
   
   
   value = [];
      
   % catch string 'NaN' from a precedent conversion of empty xls cells to strings
   if strcmp(strtrim(value_str),Constants.NaN_str)
      value = Constants.EMPTY_str;
      return;
   end
   
   % if value is not yet specified, than 'NULL' is feasible
   if strcmpi(strtrim(value_str),Constants.NULL_str)
      value = Constants.NULL_str;
      return;
   end
   
   
   % str2double(value_str) returns NaN (double) if it is a non-numeric string
   % check if parameter identifier in value fulfills convention
   if isParamId % Parameter identifier is allowed
      
      value = value_str;
%       if ~isempty(regexp(value_str,'^0\d','match'))   % not allow strings of type 00.00, 00, 0043656 ,..
%          return;
%       end
%       
%       % is it a feasible number?
%       if ~isnan(str2double(value_str))
%          value = value_str;
%          return;
%       end
%       
%       if ~isempty(regexp(value_str,'^[A-Za-z]$|^[A-Za-z]\w*?[A-Za-z0-9]$','match')) % fine if Parameter identifier fulfilling convention
%          value = value_str;
%          return;
%       end
      
   else
      % is it a feasible number?
      if ~isnan(str2double(value_str))
         value = value_str;
         return;
      end
      
   end
   
end
