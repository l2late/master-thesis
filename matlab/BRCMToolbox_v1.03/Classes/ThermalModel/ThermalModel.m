classdef ThermalModel
   %THERMALMODEL This class represents the thermal RC-model of the building one aims to control
   %   The model has the following representation:
   %   x' = A_t*x+Bq*q, where A_t = Xcap^(-1)*A_bar and Bq = Xcap^(-1)*Bq_bar
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
      n_properties@uint64 = uint64(1);    % number of required properties for instantation of object
   end % properties(Constant,Hidden)
   
       properties (SetAccess = {?Building}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      A@double = [];                      % state space matrix
      Bq@double = [];                     % heat-flux input q to state x matrix
      Xcap@double = [];                   % Capacitance matrix
   end % properties(SetAccess = {?Building})
   
       methods(Access = {?Building}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      % constructor
      function obj = ThermalModel()
         
      end % constructor
   end % methods(Access = {?Building})
   
   methods
      function delete(obj)
         disp('ThermalModel object has been deleted');
      end
      
      function [A_d,Bq_d] = discretize(obj,Ts_hrs)
         
         if ~isnumeric(Ts_hrs) || ~(Ts_hrs>0)
            error('ThermalModel:Ts_hrs','Discretization requires to be a numeric value > 0');
         end
         
         A_d = [];
         Bq_d = [];
         
         if ~isempty(obj.A) && ~isempty(obj.Bq)
            tmp = [obj.A,obj.Bq];
            tmp = [tmp;zeros(size(tmp,2)-size(tmp,1),size(tmp,2))];
            tmp = expm(tmp*Ts_hrs*3600);
            A_d = tmp(1:size(obj.A,1),1:size(obj.A,1));
            Bq_d = tmp(1:size(obj.A,1),size(obj.A,1)+1:end);
         end
      end % discretize
      
   end % methods
end % classdef
