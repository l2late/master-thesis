function identifier = check_identifier_adjacent(id_str,key_str)
   %CHECK_IDENTIFIER_ADJACENT Checks whether the identifier is valid and fulfills our convention.
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
   
   
   %This identifier can represent a zone, ground, ambient or adiabatic.
   
   
   
   identifier = {};
   
   % catch NaN
   if strcmp(id_str,Constants.NaN_str)
      return;
   end
   
   % catch not yet specified
   if strcmpi(strtrim(id_str),Constants.NULL_str)
      identifier = Constants.NULL_str;
      return;
   end
   
   if ~isempty(ThermalModelData.check_identifier(id_str,key_str)) % is it a zone?
      identifier = id_str;
      return;
   elseif ~isempty(regexp(id_str,strcat('^',Constants.ground_identifier,'$'),'match')) % is it a ground?
      identifier = id_str;
      return;
   elseif ~isempty(regexp(id_str,strcat('^',Constants.ambient_identifier,'$'),'match')) % is it an ambient?
      identifier = id_str;
      return;
   elseif ~isempty(regexp(id_str,strcat('^',Constants.adiabatic_identifier,'$'),'match')) % is it adiabatic?
      identifier = id_str;
      return;
   end
   
   % Neither of them: Illegal
end
