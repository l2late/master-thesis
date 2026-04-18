function [X,Q,t_hrs] = simulateThermalModel(obj,simMode,varargin)
   %SIMULATETHERMALMODEL This method is a wrapper for the thermal model simulation engine simulateTM
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
   n_q = length(obj.building.building_model.identifiers.q);
   obj.X = [];
   obj.Y = [];
   obj.Q = [];
   
   
   
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
   %     obj.simulateTM(Constants.sim_default_str);
   
   if strcmpi(simMode,Constants.sim_inputTrajectory_str) && length(varargin) == 1 && isnumeric(varargin{1})
      
      % simulate using given input trajectory contained in varargin{1}
      Q = varargin{1};
      
      [q_rows,q_cols] = size(Q);
      
      if ~(q_rows == n_q && q_cols == obj.n_simulation_time_steps)
         error('SimulationExperiment:simulateThermalModel',...
            'Dimension mismatch. Input argument is required to be a matrix with %d rows and %d columns.\n',n_q,n_simulation_time_steps);
      end
      
      % First call in order to set time vector and matrix Q
      SimulationExperiment.input_q_trajectory_generator([],[],[],obj.t_hrs,Q);
      
      % Simulate
      obj.simulateTM(Constants.sim_inputTrajectory_str);
      
   elseif strcmpi(simMode,Constants.sim_handle_str) && length(varargin) == 1 && isa(varargin{1},'function_handle')
      
      % simulate using custom input generator given by handle in varargin{1}
      obj.custom_input_q_handle = varargin{1};
      
      % simulate
      obj.simulateTM(Constants.sim_handle_str);
   else
      error('SimulationExperiment:simulateThermalModel','Bad arguments. Current supported types are ''%s'', ''%s''.',...
         Constants.sim_inputTrajectory_str,Constants.sim_handle_str);
   end
   
   X = obj.X;
   Q = obj.Q;
   t_hrs = obj.t_hrs;
   
   
end % simulateThermalModel
