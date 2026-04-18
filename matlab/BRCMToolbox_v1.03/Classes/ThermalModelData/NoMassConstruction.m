classdef NoMassConstruction
   %NOMASSCONSTRUCTION This class describes a no mass construction of a building element (wall, floor, ...).
   %   This class represents a special construction type, that does not have a
   %   state. No mass constructions are mainly used to model openings or to
   %   split large rooms in to smaller ones.
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
   
   
   
   
   
   properties(Hidden,Constant)
      n_properties@uint64 = uint64(3);    % number of properties required for an object instance
      key@char = 'NMC';                 % identifier key, first 3 letters of the identifier, e.g. NMC0001
   end % properties(Constant,Hidden)
   
       properties (SetAccess = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      identifier@char = '';             % identifier of the no mass construction, e.g. NMC0001
      description@char = '';            % description of the no mass construction
      U_value@char = '';                % Heat transfer coefficient [W/m^2K]
   end % properties
   
       methods (Access = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      % constructor
      function obj = NoMassConstruction(identifier,description,U_value)
         
         if nargin == obj.n_properties
            obj.identifier = identifier;
            obj.description = description;
            
            if isnumeric(U_value)
               obj.U_value = num2str(U_value,Constants.num2str_precision);
            else
               obj.U_value = U_value;
            end
         elseif nargin > 0 && nargin ~= obj.n_properties
            error('Construction:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.nomass_construction_name_str,obj.n_properties);
         end
      end % NoMassConstruction
      
   end % methods(Access = {?ThermalModelData})
   
       methods (Access = {?ThermalModelData},Static) % IF_WITH_METACLASS_SUPPORT
   %methods(Static) % IF_NO_METACLASS_SUPPORT
      
      function check(identifier_str,description_str,U_value_str) %#ok<INUSL>
         
         props = properties(Constants.nomass_construction_classname_str);
         
         if isempty(ThermalModelData.check_identifier(identifier_str,NoMassConstruction.key))
            error('Construction:Identifier',Constants.error_msg_identifier(Constants.nomass_construction_name_str,identifier_str,NoMassConstruction.key));
         end
         
         if isempty(ThermalModelData.check_value(U_value_str,true)) || strcmpi(U_value_str,Constants.NULL_str)
            error('Construction:U_value',Constants.error_msg_value(Constants.nomass_construction_name_str,U_value_str,props{3},true,'> 0'));
         elseif ~isnan(str2double(U_value_str)) && ~(str2double(U_value_str)>0)
            error('Construction:U_value',Constants.error_msg_value(Constants.nomass_construction_name_str,U_value_str,props{3},true,'> 0'));
         end
         
      end % check
   end %(Access = {?ThermalModelData},Static)
   
end % classdef
