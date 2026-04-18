classdef Construction
   %CONSTRUCTION This class describes the construction of a building element (wall, floor, ...).
   %   n_properties:       Denotes the number of required arguments for the
   %                       instantation of an object (uint64)
   %   identifier:         Identifier of construction type, e.g. C0001 (string)
   %   description:        Describes the construction type, e.g. External_Wall
   %                       (string)
   %   material_identifiers:
   %                       List of layer materials. Convention: first element is adjacent_A - > last element is adjacent_B
   %   thickness:          List of layer thicknesses. Elements correspond to the material_identifiers entries. 
   %                       Convention: first element is adjacent_A - > last element is adjacent_B
   %   conv_coeff_adjacent_A:
   %                       Value or Parameter identifier for the
   %                       convective heat transfer coefficent of adjacent zone A in W/m^2K
   %   conv_coeff_adjacent_B:
   %                       Value or Parameter identifier for the
   %                       convective heat transfer coefficent of adjacent zone B in W/m^2K
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
      n_properties@uint64 = uint64(6);       % number of properties required for an object instance
      key@char = 'C';                      % identifier key, first letter of the identifier, e.g. C0001
   end % properties(Constant,Hidden)
   
       properties (SetAccess = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      identifier@char = '';                 % identifier of the construction type, e.g. C0001
      description@char = '';                % description of the identifier
      material_identifiers@cell;              % List of layer materials
      thickness@cell;                         % List of layer thicknesses.
      conv_coeff_adjacent_A@char = '';      % Convective heat transfer coefficient [W/m^2K]
      conv_coeff_adjacent_B@char = '';      % Convective heat transfer coefficient [W/m^2K]
   end % properties
   
       methods (Access = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      % constructor
      function obj = Construction(identifier,description,material_identifiers,thickness,conv_coeff_adjacent_A,conv_coeff_adjacent_B)
         
         if nargin == obj.n_properties
            obj.identifier = identifier;
            obj.description = description;
            obj.material_identifiers = material_identifiers;
            obj.thickness = thickness;
            
            if isnumeric(conv_coeff_adjacent_A)
               obj.conv_coeff_adjacent_A = num2str(conv_coeff_adjacent_A,Constants.num2str_precision);
            else
               obj.conv_coeff_adjacent_A = conv_coeff_adjacent_A;
            end
            if isnumeric(conv_coeff_adjacent_B)
               obj.conv_coeff_adjacent_B = num2str(conv_coeff_adjacent_B,Constants.num2str_precision);
            else
               obj.conv_coeff_adjacent_B = conv_coeff_adjacent_B;
            end
         elseif nargin > 0 && nargin ~= obj.n_properties
            error('Construction:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.construction_name_str,obj.n_properties);
         end
      end % Construction
   end
   
   methods

   end % methods
   
       methods (Access = {?ThermalModelData},Static) % IF_WITH_METACLASS_SUPPORT
   %methods(Static) % IF_NO_METACLASS_SUPPORT
      function check(identifier_str,description_str,material_identifiers,thickness,conv_coeff_adjacent_A_str,conv_coeff_adjacent_B_str) %#ok<INUSL>
         
         props = properties(Constants.construction_classname_str);
         
         if isempty(ThermalModelData.check_identifier(identifier_str,Construction.key))
            error('Construction:Identifier',Constants.error_msg_identifier(Constants.construction_name_str,identifier_str,Construction.key));
         end
         
         if isempty(ThermalModelData.check_value(conv_coeff_adjacent_A_str,true)) || strcmpi(conv_coeff_adjacent_A_str,Constants.NULL_str)
            error('Construction:ConvHeatCoeffAdjA',Constants.error_msg_value(Constants.construction_name_str,conv_coeff_adjacent_A_str,props{4},true,'> 0'));
         elseif ~isnan(str2double(conv_coeff_adjacent_A_str)) && ~(str2double(conv_coeff_adjacent_A_str)>=0)
            error('Construction:ConvHeatCoeffAdjA',Constants.error_msg_value(Constants.construction_name_str,conv_coeff_adjacent_A_str,props{4},true,'> 0'));
         end
         
         if isempty(ThermalModelData.check_value(conv_coeff_adjacent_B_str,true)) || strcmpi(conv_coeff_adjacent_B_str,Constants.NULL_str)
            error('Construction:ConvHeatCoeffAdjB',Constants.error_msg_value(Constants.construction_name_str,conv_coeff_adjacent_B_str,props{5},true,'> 0'));
         elseif ~isnan(str2double(conv_coeff_adjacent_B_str)) && ~(str2double(conv_coeff_adjacent_B_str)>=0)
            error('Construction:ConvHeatCoeffAdjB',Constants.error_msg_value(Constants.construction_name_str,conv_coeff_adjacent_B_str,props{5},true,'> 0'));
         end
         
      end % check
   end %(Access = {?ThermalModelData},Static)
end % classdef
