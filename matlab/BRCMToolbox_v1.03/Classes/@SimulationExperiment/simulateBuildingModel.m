function [X,U,V,t_hrs] = simulateBuildingModel(obj,simMode,varargin)
   %SIMULATEBUILDINGMODEL This method is a wrapper for the building model simulation engine simulateBM
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
   
   
   obj.t_hrs = obj.generateTimeVector();
   n_u = length(obj.building.building_model.identifiers.u);
   n_v = length(obj.building.building_model.identifiers.v);
   obj.X = [];
   obj.Y = [];
   obj.U = [];
   obj.V = [];
   
   if isempty(obj.building.building_model.continuous_time_model) && isempty(obj.building.building_model.discrete_time_model)
      error('simulateBuildingModel:Requirements','No building model availabel. Cannot simulate.\n');
   end
   if isempty(obj.n_simulation_time_steps)
      error('simulateBuildingModel:Requirements','''n_simulation_time_steps'' has not been set. Cannot simulate.\n');
   end
   if isempty(obj.x0)
      error('simulateBuildingModel:Requirements','''x0'' has not been set. Cannot simulate.\n');
   end
   
   
   % % DS: Don't allow for default simulation currently!
   % if strcmpi(simMode,Constants.sim_default_str) && isempty(varargin)
   %
   %     % Simulate
   %     obj.simulateBM(Constants.sim_default_str);
   
   if strcmpi(simMode,Constants.sim_inputTrajectory_str) && length(varargin) == 2 && isnumeric(varargin{1}) && isnumeric(varargin{2})
      
      % simulate using given input trajectory contained in varargin{1}
      U = varargin{1};
      V = varargin{2};
      
      [u_rows,u_cols] = size(U);
      [v_rows,v_cols] = size(V);
      
      % check matrix U
      if ~(u_rows == n_u && u_cols == obj.n_simulation_time_steps)
         error('SimulationExperiment:simulateBuildingModel',...
            'Dimension mismatch. Input argument 1 is required to be a matrix with %d rows and %d columns.\n',n_u,obj.n_simulation_time_steps);
      end
      
      % check matrix V
      if ~(v_rows == n_v && v_cols == obj.n_simulation_time_steps)
         error('SimulationExperiment:simulateBuildingModel',...
            'Dimension mismatch. Input argument 2 is required to be a matrix with %d rows and %d columns.\n',n_v,obj.n_simulation_time_steps);
      end
      
      % First call in order to set time vector and matrices U,V
      SimulationExperiment.input_uv_trajectory_generator([],[],[],obj.t_hrs,U,V);
      
      % Simulate
      obj.simulateBM(Constants.sim_inputTrajectory_str);
      
   elseif strcmpi(simMode,Constants.sim_handle_str) && length(varargin) == 1 && isa(varargin{1},'function_handle')
      
      % simulate using custom input generator given by handle in varargin{1}
      obj.custom_input_uv_handle = varargin{1};
      
      % simulate
      obj.simulateBM(Constants.sim_handle_str);
      
   else
      error('SimulationExperiment:simulateBuildingModel','Bad Arguments. Current supported types are, ''%s'', ''%s''.',...
         Constants.sim_inputTrajectory_str,Constants.sim_handle_str);
   end
   
   X = obj.X;
   U = obj.U;
   V = obj.V;
   t_hrs = obj.t_hrs;
   
end % simulateBuildingModel
