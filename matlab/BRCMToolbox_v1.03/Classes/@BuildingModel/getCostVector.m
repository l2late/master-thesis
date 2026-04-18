function [cu] = getCostVector(obj,costParameters) 
   %GETCOSTVECTOR Provides the costs associated with the current building model.
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
   
   
   
   % check if model exists
   if ~obj.model_exists
      error('getConstraintsMatrices:NoModel','No % model available.\n',lower(Constants.building_name_str));
   end
   
   % check is not dirty
   if obj.model_exists && obj.is_dirty
      warning('getConstraintsMatrices:is_dirty',['Constraints do not match the currently declared external heat flux models.\n',...
         'Recompilation of %s model required.\n'],lower(Constants.building_name_str));
      cu = [];
      return
   end

   
   n_u = length(obj.identifiers.u);
   cu = zeros(n_u,1);
   
   n_EHFs = length(obj.EHF_submodels);
   
   for i = 1:n_EHFs
      
      id = obj.EHF_submodels{i}.EHF_identifier;
      if ~isfield(costParameters,id)
         parameters = struct();
      else
         parameters = costParameters.(id);
      end
      parameters.(EHFModelBaseClass.identifiers_fullModel_str) = obj.identifiers;
      parameters.Ts_hrs = obj.Ts_hrs;
      
      % get EHF cost vector fitted to building model dimension
      [cu_i] = obj.EHF_submodels{i}.getPrescribedSizeCostVector(obj.identifiers,parameters);
      
      cu = cu+cu_i;
      
   end
   
end % getCostVector
