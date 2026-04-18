function simulateTM(obj,simMode)
   %SIMULATETM This method provides the engine for the simulation of the thermal model
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
   
   
   % This function assumes that all checks on the model etc. have been done before.
   
   % DS: Don't allow for default simulation currently!
   % if strcmpi(simMode,Constants.sim_default_str)
   %
   %     % set to default handle
   %     f = obj.default_input_q_handle;
   
   if strcmpi(simMode,Constants.sim_inputTrajectory_str)
      
      % set to input trajectory handle
      f = obj.input_q_trajectory_handle;
      
   elseif strcmpi(simMode,Constants.sim_handle_str)
      
      % set to custom input handle
      f = obj.custom_input_q_handle;
      
   else
      error('simulateBM:badMode','Did not recognize simulation simMode: %s\n\n',simMode);
   end
   
   n_x = length(obj.building.building_model.identifiers.x);
   
   % append inital state to state sequence matrix
   x0 = obj.x0;
   t_vec = obj.t_hrs;
   obj.X(1:n_x,1) = x0;
   
   fprintfDbg(1,'Discretizing thermal model with Ts_hrs = %1.3f [h].\n\n',obj.building.building_model.Ts_hrs);
   [A_d,Bq_d] = obj.building.building_model.thermal_submodel.discretize(obj.building.building_model.Ts_hrs);
   
   
   for t = t_vec
      
      % get input
      q = f(x0,t,obj.building.building_model.identifiers);
      
      % append q to input sequence matrix
      obj.Q = [obj.Q q];
      
      % TODO: correct output equation
      % compute output
      %y = C*x0 + D*q;
      
      % append y to output sequence matrix
      %obj.Y = [obj.Y y];
      
      % compute state
      x = A_d*x0 + Bq_d*q;
      
      % append y to output sequence matrix
      obj.X = [obj.X x];
      
      % update state
      x0 = x;
   end
   
   % remove the last column to have equally sized matrices
   obj.X(:,end) = [];
   
   obj.plot_enabled = true;
   obj.write_enabled = true;
   
end
