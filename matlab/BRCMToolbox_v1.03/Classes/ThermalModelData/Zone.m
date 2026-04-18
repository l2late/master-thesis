classdef Zone
   %ZONE This class represents a Zone of a building.
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
      n_properties@uint64 = uint64(5);    % number of properties required for an object instance
      key@char = 'Z';                   % identifier key, first letter of the identifier, e.g. Z0001
   end % properties(Constant,Hidden)
   
       properties (SetAccess = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT properties
   %properties % IF_NO_METACLASS_SUPPORT
      identifier@char = '';             % identifier of the zone, e.g. Z0001
      description@char = '';            % description of the zone
      area@char = '';                   % zone area [m^2]
      volume@char = '';                 % zone voluem [m^3]
      group@cell = {};                    % cell of group identifiers to which the zone belongs to
   end % properties
   
       methods(Access = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      function obj = Zone(identifier,description,area,volume,group)
         
         if nargin == obj.n_properties
            obj.identifier = identifier;
            obj.description = description;
            obj.area = area;
            obj.volume = volume;
            obj.group = group;
         elseif nargin > 0 && nargin ~= obj.n_properties
            error('Zone:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.zone_name_str,obj.n_properties);
         end
      end % Zone
   end % methods
end % classdef
