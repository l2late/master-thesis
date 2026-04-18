classdef Parameter
   %PARAMETER This represents a parameter.
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
      n_properties@uint64 = uint64(3);
   end % properties(Constant,Hidden)
   
      properties (SetAccess = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      identifier@char = '';
      description@char = '';
      value@char = '0'; % since we support 'NULL'
   end % properties
   
      methods (Access = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      function obj = Parameter(identifier,description,value)
         
         if nargin == obj.n_properties
            obj.identifier = identifier;
            obj.description = description;
            
            if isnumeric(value)
               obj.value = num2str(value,Constants.num2str_precision);
            else
               obj.value = value;
            end
            
         elseif nargin > 0 && nargin ~= obj.n_properties
            error('Parameter:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.parameter_name_str,obj.n_properties);
         end
         
      end % Parameter
      
   end % methods
   
      methods (Access = {?ThermalModelData},Static) % IF_WITH_METACLASS_SUPPORT
   %methods(Static) % IF_NO_METACLASS_SUPPORT
      
      function check(identifier_str,description_str,value_str) %#ok<INUSL>
         
         props = properties(Constants.parameter_classname_str);
         
         if isempty(ThermalModelData.check_special_identifier(identifier_str))
            error('Parameter:Identifier',Constants.error_msg_identifier_special(Constants.parameter_name_str,identifier_str));
         end
         
         if isempty(ThermalModelData.check_value(value_str,false)) || strcmpi(value_str,Constants.NULL_str)
            error('Parameter:Value',Constants.error_msg_value(Constants.parameter_name_str,value_str,props{3},false,'> 0'));
         elseif ~(str2double(value_str)>=0)
            error('Parameter:Value',Constants.error_msg_value(Constants.parameter_name_str,value_str,props{3},false,'> 0'));
         end
         
      end % check
      
   end % methods(Access = {?ThermalModelData},Static)
end % classdef

