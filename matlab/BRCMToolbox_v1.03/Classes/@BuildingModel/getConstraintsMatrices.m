function [Fx,Fu,Fv,g,constraint_identifiers] = getConstraintsMatrices(obj,constraintsParameters)
   %GETCONSTRAINTSMATRICES Provides the constraints associated with the current building model.
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
         'Recompilation of %s model recommended.\n'],lower(Constants.building_name_str));
   end
   
   
   
   n_x = length(obj.identifiers.x);
   n_u = length(obj.identifiers.u);
   n_v = length(obj.identifiers.v);
   
   Fx = zeros(0,n_x);
   Fu = zeros(0,n_u);
   Fv = zeros(0,n_v);
   g = [];
   constraint_identifiers = {};
   
   n_EHFs = length(obj.EHF_submodels);
   
   for i = 1:n_EHFs
      
      id = obj.EHF_submodels{i}.EHF_identifier;
      if ~isfield(constraintsParameters,id)
         parameters = struct();
      else
         parameters = constraintsParameters.(id);
      end
      parameters.(EHFModelBaseClass.identifiers_fullModel_str) = obj.identifiers;
      
      % get EHF sub-model constraints matrices fitted to building model dimension
      [Fx_i,Fu_i,Fv_i,g_i,constraint_identifiers_i] = obj.EHF_submodels{i}.getPrescribedSizeConstraintsMatrices(obj.identifiers,parameters);
      
      % stack matrices, vectors and identifiers vertically
      Fx = [Fx;Fx_i]; %#ok<*AGROW>
      Fu = [Fu;Fu_i];
      Fv = [Fv;Fv_i];
      g = [g;g_i];
      constraint_identifiers = [constraint_identifiers;reshapeVector(constraint_identifiers_i,'col')];
      
   end
   
   % make sure everything is in the right order
   perm = nan(length(obj.identifiers.constraints),1);
   if length(obj.identifiers.constraints) == length(constraint_identifiers)
      for i=1:length(obj.identifiers.constraints)
         perm(i) = getIdIndex(constraint_identifiers,obj.identifiers.constraints{i});
      end
   end
   
   Fx = Fx(perm,:);
   Fu = Fu(perm,:);
   Fv = Fv(perm,:);
   g = g(perm,:);
   constraint_identifiers = constraint_identifiers(perm);
   if ~all(strcmp(constraint_identifiers,obj.identifiers.constraints))
      error('ERR');
   end
   
   
end % getConstraintsMatrices
