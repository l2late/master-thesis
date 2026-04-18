function loadEHFModel(obj,class_file,source_file,identifier)
   %LOADEHFMODEL This method loads and generates an External Heat Flux model.
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
   
   
   % This check is currently contained in the EHF generator method
   
   
   if isempty(obj.building_model.thermal_submodel)
      error('loadEHFModel:NoThermalModel','%s with thermal model required.\n',Constants.building_name_str);
   end
   
   
   % get file name of class_file
   [~,constructor,~] = fileparts(class_file);
   
   % construct function handle
   constructor = str2func(constructor);
   
   % generate EHF Model with given file path
   EHFM = constructor(obj,identifier,source_file);
   
   if ~isempty(EHFM)
      
      signal_repetition = intersect(obj.building_model.identifiers.u,EHFM.identifiers.u);
      if ~isempty(signal_repetition)
         error('loadEHFModel:Input_u','Following input signal/s are already contained in the current model: ''%s''.\n',makeStringOfIdentifiers(signal_repetition));
      end
      
      signal_repetition = intersect(obj.building_model.identifiers.constraints,EHFM.identifiers.constraints);
      if ~isempty(signal_repetition)
         error('loadEHFModel:Constraints','Following input signal/s are already contained in the current model: ''%s''.\n',makeStringOfIdentifiers(signal_repetition));
      end
      
      
      % v_AMB,v_GND can appear more than one time, setdiff removes them from
      % the current EHF signals
      signal_repetition = intersect(obj.building_model.identifiers.v,setdiff(EHFM.identifiers.u,cellfun(@(x) strcat(Constants.disturbance_variable,'_',x),Constants.exterior(1:2),'UniformOutput',0)));
      if ~isempty(signal_repetition)
         error('loadEHFModel:Input_v','Following input signal/s are already contained in the current model: ''%s''.\n',makeStringOfIdentifiers(signal_repetition));
      end
      
      % set class file name
      EHFM.class_file = class_file;   % this property is currently public in the EHF base class
      obj.building_model.EHF_submodels{end+1} = EHFM;
      obj.building_model.identifiers.u = [obj.building_model.identifiers.u; reshapeVector(obj.building_model.EHF_submodels{end}.identifiers.u,'col')];
      obj.building_model.identifiers.v = [obj.building_model.identifiers.v; reshapeVector(obj.building_model.EHF_submodels{end}.identifiers.v,'col')];
      obj.building_model.identifiers.constraints = [obj.building_model.identifiers.constraints; reshapeVector(obj.building_model.EHF_submodels{end}.identifiers.constraints,'col')];
   else
      warning('loadEHFModel:Empty_Model','Generated EHF model is empty.\n');
   end
   
   % input and disturbance signals can appear twice depending on the EHF submodel, e.g v_AMB in Building Hull and Window, so we apply the unique
   % operator on the strings
   % CAVEAT:
   % Unique changes the order of the elements, so for finding columns in
   % associated matrices refer to the identifiers in the specific EHF model.
   obj.building_model.identifiers.v = unique(obj.building_model.identifiers.v);
   
end

function [identifiers_str] = makeStringOfIdentifiers(identifiers)
   if length(identifiers) > 1
      identifiers_str = sprintf('%s%s',identifiers{1},sprintf(',%s',identifiers{2:end}));
   else
      identifiers_str = identifiers{1};
   end
end
