classdef Window
   %WINDOW This class represents the window data of a building element.
   %   This class stores the window information of the building. A window is
   %   contained in a building element and referenced by a window identifier.
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
      n_properties@uint64 = uint64(6);    % number of properties required for object instance
      key@char = 'W';                   % identifier key, first letter of the identifier, e.g. W0001
   end % properties(Constant,Hidden)
   
      properties(SetAccess = {?ThermalModelData,?Building}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      identifier@char = '';             % identifier of the window, e.g. W0001
      description@char = '';            % window description
      glass_area@char = '0';            % window glass area [m^2]
      frame_area@char = '0';            % window frame area [m^2]
      U_value@char = '';                % U-value, heat transfer coefficient [W/m^2K]
      SHGC@char = '';                   % Solar Heat Gain Coefficient [%]
   end % properties
   
      methods(Access = {?ThermalModelData,?Building})% IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      % constructor
      function obj = Window(identifier,description,glass_area,frame_area,U_value,SHGC)
         
         if nargin == obj.n_properties
            obj.identifier = identifier;
            obj.description = description;
            
            if isnumeric(glass_area)
               obj.glass_area = num2str(glass_area,Constants.num2str_precision);
            else
               obj.glass_area = glass_area;
            end
            
            if isnumeric(frame_area)
               obj.frame_area = num2str(frame_area,Constants.num2str_precision);
            else
               obj.frame_area = frame_area;
            end
            
            if isnumeric(U_value)
               obj.U_value = num2str(U_value,Constants.num2str_precision);
            else
               obj.U_value = U_value;
            end
            if isnumeric(SHGC)
               obj.SHGC = num2str(SHGC,Constants.num2str_precision);
            else
               obj.SHGC = SHGC;
            end
         elseif nargin > 0 && nargin ~= obj.n_properties
            error('Window:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.window_name_str,obj.n_properties);
         end
         
      end % Window
      
   end % methods(Access = {?ThermalModelData,?Building})
   
      methods(Access = {?ThermalModelData},Static) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      
      function check(identifier_str,description_str,glass_area_str,frame_area_str,U_value_str,SHGC_str) %#ok<INUSL>
         
         props = properties(Constants.window_classname_str);
         
         if isempty(ThermalModelData.check_identifier(identifier_str,Window.key))
            error('Window:Identifier',Constants.error_msg_identifier(Constants.window_name_str,identifier_str,Window.key));
         end
         
         if isempty(ThermalModelData.check_value(glass_area_str,true)) || strcmpi(glass_area_str,Constants.NULL_str)
            error('Window:GlassArea',Constants.error_msg_value(Constants.window_name_str,glass_area_str,props{3},true,'>= 0'));
         elseif ~isnan(str2double(glass_area_str)) && ~(str2double(glass_area_str)>=0)
            error('Window:GlassArea',Constants.error_msg_value(Constants.window_name_str,glass_area_str,props{3},true,'>= 0'));
         end
         
         if isempty(ThermalModelData.check_value(frame_area_str,true)) || strcmpi(frame_area_str,Constants.NULL_str)
            error('Window:FrameArea',Constants.error_msg_value(Constants.window_name_str,frame_area_str,props{4},true,'>= 0'));
         elseif ~isnan(str2double(frame_area_str)) && ~(str2double(frame_area_str)>=0)
            error('Window:FrameArea',Constants.error_msg_value(Constants.window_name_str,frame_area_str,props{4},true,'>= 0'));
         end
         
         if isempty(ThermalModelData.check_value(U_value_str,true)) || strcmpi(U_value_str,Constants.NULL_str)
            error('Window:U_value',Constants.error_msg_value(Constants.window_name_str,U_value_str,props{5},true,'> 0'));
         elseif ~isnan(str2double(U_value_str)) && ~(str2double(U_value_str)>0)
            error('Window:U_value',Constants.error_msg_value(Constants.window_name_str,U_value_str,props{5},true,'> 0'));
         end
         
         if isempty(ThermalModelData.check_value(SHGC_str,true)) || strcmpi(SHGC_str,Constants.NULL_str)
            error('Window:SHGC',Constants.error_msg_value(Constants.window_name_str,SHGC_str,props{6},true,'between 0 and 1'));
         elseif ~isnan(str2double(SHGC_str)) && ~(str2double(SHGC_str)>=0 && str2double(SHGC_str) <= 1)
            error('Window:SHGC',Constants.error_msg_value(Constants.window_name_str,SHGC_str,props{6},true,'between 0 and 1'));
         end
         
      end % check
      
   end%methods(Access = {?ThermalModelData},Static)
end % classdef
