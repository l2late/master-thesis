function simulateBM(obj,simMode)
   %SIMULATEBM This method simulates provides the engine for the simulation of the building model.
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
   %     f = obj.default_input_uv_handle;
   
   if strcmpi(simMode,Constants.sim_inputTrajectory_str)
      
      % set to input trajectory handle
      f = obj.input_uv_trajectory_handle;
      
   elseif strcmpi(simMode,Constants.sim_handle_str)
      
      % set to custom input handle
      f = obj.custom_input_uv_handle;
      
   else
      error('simulateBM:badMode','Did not recognize simulation simMode: %s\n\n',simMode);
   end
   
   
   n_u = length(obj.building.building_model.identifiers.u);
   n_x = length(obj.building.building_model.identifiers.x);
   
   % append inital state to state sequence matrix
   x0 = obj.x0;
   t_hrs = obj.t_hrs;
   obj.X(1:n_x,1) = x0;
   
   if isempty(obj.building.building_model.discrete_time_model)
      fprintfDbg(1,'Discrete-time building model does not exist. Discretizing building model with Ts_hrs = %1.3f [h].\n\n',obj.building.building_model.Ts_hrs);
      obj.building.building_model.discretize;
   end
   
   mD = obj.building.building_model.discrete_time_model;
   
   N_steps = numel(t_hrs);
   Displayer = Progressdisp(N_steps, barWidth=40, BarOrStr="bar");
   for ii = 1:N_steps
      t = t_hrs(ii);
      Displayer.Display_progress(ii); % Update progress dynamically
      % get input
      [u v] = f(x0,t,obj.building.building_model.identifiers);
      
      % append u to input sequence matrix U
      obj.U = [obj.U u];
      
      % append v to disturbance sequence matrix V
      obj.V = [obj.V v];
      
      % compute heat flux state
      %q = obj.Aq_d*x0 + obj.Bq_u_d*u + obj.Bq_v_d*v;
      
      % compute output y
      %y = sys.C*x0 + sys.Du*u + sys.Dv*v;
      y = mD.C*x0 + mD.Du*u + mD.Dv*v;
      
      for i = 1:n_u
         y = y + (mD.Dvu(:,:,i)*v+mD.Dxu(:,:,i)*x0)*u(i);
      end
      
      % append y to ouput sequence matrix Y
      obj.Y = [obj.Y y];
      
      %x0 = sys.A*x0+sys.Bu*u+sys.Bv*v;
      x = mD.A*x0+mD.Bu*u+mD.Bv*v;
      for i = 1:n_u
         x = x + (mD.Bvu(:,:,i)*v+mD.Bxu(:,:,i)*x0)*u(i);
      end
      
      % append x0 to state sequence matrix X
      obj.X = [obj.X x];
      
      % update state
      x0 = x;
      
   end
   
   % remove the last column to have equally sized matrices
   obj.X(:,end) = [];
   
   obj.plot_enabled = true;
   obj.write_enabled = true;
   
end
