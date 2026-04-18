function discretize(obj)
   %DISCRETIZE This method discretizes the building model.
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
   
   
   
   
   if isempty(obj.Ts_hrs)
      error('discretize:Ts_hrs','Discretization time step ''%s'' not defined.\n','Ts_hrs');
   end
   
   obj.discrete_time_model = struct('A',[],'Bu',[],'Bv',[],'Bxu',[],'Bvu',[],...
      'C',[],'Du',[],'Dv',[],'Dxu',[],'Dvu',[]);
   
   if ~isempty(obj.continuous_time_model)
      B = [obj.continuous_time_model.Bu, obj.continuous_time_model.Bv];
      
      len_u = size(obj.continuous_time_model.Bu,2);
      len_v = size(obj.continuous_time_model.Bv,2);
      len_x = size(obj.continuous_time_model.A,2);
      
      for i = 1:len_u
         B = [B obj.continuous_time_model.Bvu(:,:,i) obj.continuous_time_model.Bxu(:,:,i)]; %#ok<AGROW>
      end
      obj.discrete_time_model.('A') = expm(obj.continuous_time_model.A*obj.Ts_hrs*3600);
      B   = obj.continuous_time_model.A\(obj.discrete_time_model.A-eye(size(obj.continuous_time_model.A)))*B;
      
      obj.discrete_time_model.('Bu') = B(:,1:len_u);  B(:,1:len_u) = [];
      obj.discrete_time_model.('Bv') = B(:,1:len_v);  B(:,1:len_v) = [];
      
      obj.discrete_time_model.('Bvu') = [];
      obj.discrete_time_model.('Bxu') = [];
      
      for i = 1:len_u
         obj.discrete_time_model.('Bvu')(:,:,i) = B(:,1:len_v);  B(:,1:len_v) = [];
         obj.discrete_time_model.('Bxu')(:,:,i) = B(:,1:len_x);  B(:,1:len_x) = [];
      end
      
      obj.discrete_time_model.('C') = obj.continuous_time_model.C;
      obj.discrete_time_model.('Dv') = obj.continuous_time_model.Dv;
      obj.discrete_time_model.('Du') = obj.continuous_time_model.Du;
      obj.discrete_time_model.('Dxu') = obj.continuous_time_model.Dxu;
      obj.discrete_time_model.('Dvu') = obj.continuous_time_model.Dvu;
   else
      obj.discrete_time_model = struct('A',[],'Bu',[],'Bv',[],'Bxu',[],'Bvu',[],...
         'C',[],'Du',[],'Dv',[],'Dxu',[],'Dvu',[]);
   end
   
end
