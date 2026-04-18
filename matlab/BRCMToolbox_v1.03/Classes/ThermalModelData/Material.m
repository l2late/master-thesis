classdef Material
   %MATERIAL This class stores all the relevant material data of a building element.
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
      n_properties@uint64 = uint64(6);    % number of properties required for an object instance
      key@char = 'M';                   % identifier key, first letter of the identifier, e.g. M0001
   end % properties(Constant,Hidden)
   
       properties (SetAccess = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      identifier@char = '';             % material identifiers, e.g. M0001
      description@char = '';            % description of the material
      specific_heat_capacity@char = '';     % specific heat capacity  [J/kgK]
      specific_thermal_resistance@char = '';% specific thermal resistance in [mK/W]
      density@char = '';                % density in [kg/m^3]
      R_value@char = '';                 % R-Value, used to define no-mass layers (requires specific_heat_capacity, specific_thermal_resistance and density to be empty)
   end % properties
   
       methods (Access = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      % constructor
      function obj = Material(identifier,description,specific_heat_capacity,specific_thermal_resistance,density,R_value)
         
         if nargin == obj.n_properties
            obj.identifier = identifier;
            obj.description = description;
            
            if isnumeric(specific_heat_capacity)
               obj.specific_heat_capacity = num2str(specific_heat_capacity,Constants.num2str_precision);
            else
               obj.specific_heat_capacity = specific_heat_capacity;
            end
            if isnumeric(specific_thermal_resistance)
               obj.specific_thermal_resistance = num2str(specific_thermal_resistance,Constants.num2str_precision);
            else
               obj.specific_thermal_resistance = specific_thermal_resistance;
            end
            if isnumeric(density)
               obj.density = num2str(density,Constants.num2str_precision);
            else
               obj.density = density;
            end
            if isnumeric(R_value)
               obj.R_value = num2str(R_value,Constants.num2str_precision);
            else
               obj.R_value = R_value;
            end
         elseif nargin > 0 && nargin ~= obj.n_properties
            error('Material:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.material_name_str,obj.n_properties);
         end
         
      end % Material
      
   end % methods(Access = {?ThermalModelData})
   
       methods (Access = {?ThermalModelData},Static) % IF_WITH_METACLASS_SUPPORT
   %methods(Static) % IF_NO_METACLASS_SUPPORT
      
      function check(identifier_str,description_str,capacity_str,resistance_str,density_str,R_value_str) %#ok<INUSL>
         
         props = properties(Constants.material_classname_str);
         
         if isempty(ThermalModelData.check_identifier(identifier_str,Material.key))
            error('Material:Identifier',Constants.error_msg_identifier(Constants.material_name_str,identifier_str,Material.key));
         end
         
         R_valueEmpty = false;
         if isempty(ThermalModelData.check_value(R_value_str,true))
            R_valueEmpty = true;
         elseif strcmpi(R_value_str,Constants.NULL_str)
            error('Material:R_value',Constants.error_msg_value(Constants.material_name_str,R_value_str,props{3},true,'> 0'));
         elseif ~isnan(str2double(R_value_str)) && ~(str2double(R_value_str)>=0)
            error('Material:R_value',Constants.error_msg_value(Constants.material_name_str,R_value_str,props{3},true,'>= 0'));
         end
         
         
         if isempty(ThermalModelData.check_value(capacity_str,true)) && R_valueEmpty
            error('Material:SpecificHeatCapacity',Constants.error_msg_value(Constants.material_name_str,capacity_str,props{3},true,'> 0'));
         elseif strcmpi(capacity_str,Constants.NULL_str)
            error('Material:SpecificHeatCapacity',Constants.error_msg_value(Constants.material_name_str,capacity_str,props{3},true,'> 0'));
         elseif ~isnan(str2double(capacity_str)) && ~(str2double(capacity_str)>=0)
            error('Material:SpecificHeatCapacity',Constants.error_msg_value(Constants.material_name_str,capacity_str,props{3},true,'> 0'));
         end
         
         if isempty(ThermalModelData.check_value(resistance_str,true)) && R_valueEmpty
            error('Material:SpecificThermalResistance',Constants.error_msg_value(Constants.material_name_str,resistance_str,props{4},true,'> 0'));
         elseif strcmpi(resistance_str,Constants.NULL_str)
            error('Material:SpecificThermalResistance',Constants.error_msg_value(Constants.material_name_str,resistance_str,props{4},true,'> 0'));
         elseif ~isnan(str2double(resistance_str)) && ~(str2double(resistance_str)>0)
            error('Material:SpecificThermalResistance',Constants.error_msg_value(Constants.material_name_str,resistance_str,props{4},true,'> 0'));
         end
         
         if isempty(ThermalModelData.check_value(density_str,true)) && R_valueEmpty
            error('Material:Density',Constants.error_msg_value(Constants.material_name_str,density_str,props{5},true,'>= 0'));
         elseif strcmp(resistance_str,Constants.NULL_str)
            error('Material:Density',Constants.error_msg_value(Constants.material_name_str,density_str,props{5},true,'>= 0'));
         elseif ~isnan(str2double(density_str)) && ~(str2double(density_str)>0)
            error('Material:Density',Constants.error_msg_value(Constants.material_name_str,density_str,props{5},true,'>= 0'));
         end
      end % check
      
   end%methods(Access = {?ThermalModelData},Static)
end % classdef
