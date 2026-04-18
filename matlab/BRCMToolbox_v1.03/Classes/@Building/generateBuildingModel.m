function generateBuildingModel(obj)
   % GENERATEBUILDINGMODEL Generates the model for the building one aims to control.
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
   
   
   % Check if Building thermal model data is loaded
   
   
   if isempty(obj.thermal_model_data.zones) || isempty(obj.thermal_model_data.building_elements) || isempty(obj.thermal_model_data.constructions) ||...
         isempty(obj.thermal_model_data.materials)
      error('generateBuildingModel:NoData','Cannot generate model since %s''s %s data incomplete.',Constants.building_name_str,Constants.thermalmodel_name_str);
   end
   
   %     % check if model already exist
   %     if obj.building_model.model_exists
   %
   %         reply = input(sprintf('\n%s model already exists. Replace? Y/N (y/n): ',Constants.building_name_str), 's');
   %
   %         while(~(strcmpi(reply,'y') || strcmpi(reply,'n')))
   %             reply = input(['\nUnknown input ' sprintf('''%s''. ',reply),sprintf('%s model already exists. Replace? Y/N (y/n): ',Constants.building_name_str)], 's');
   %         end
   %
   %         if strcmpi(reply,'n')
   %             return;
   %         end
   %
   %     end
   
   % Reset models
   obj.building_model.thermal_submodel = ThermalModel.empty;
   obj.building_model.identifiers = Identifier;
   obj.building_model.EHF_submodels = {};
   
   % generate Thermal Model
   obj.generateThermalModel;
   
   % generate EHF Models
   n_EHF_declarations = length(obj.EHF_model_declarations);
   
   for i = 1:n_EHF_declarations
      obj.loadEHFModel(obj.EHF_model_declarations(i).class_file,obj.EHF_model_declarations(i).source_file,obj.EHF_model_declarations(i).EHF_identifier);
   end
   
   
   % Constuct system matrices of complete Building Model
   n_EHF = length(obj.building_model.EHF_submodels);
   n_x = length(obj.building_model.identifiers.x);
   n_q = length(obj.building_model.identifiers.q);
   n_u = length(obj.building_model.identifiers.u);
   n_v = length(obj.building_model.identifiers.v);
   n_y = length(obj.building_model.identifiers.y);
   
   Aq = zeros(n_q,n_x);
   Bq_u = zeros(n_q,n_u);
   Bq_v = zeros(n_q,n_v);
   Bq_vu = zeros(n_q,n_v,n_u);
   Bq_xu = zeros(n_q,n_x,n_u);
   
   % compute EHF model matrices according to model dimensions
   for i = 1:n_EHF
      
      [A_i,Bu_i,Bv_i,Bxu_i,Bvu_i] = obj.building_model.EHF_submodels{i}.getPrescribedSizeSystemMatrices(obj.building_model.identifiers);
      
      Aq = Aq + A_i;
      Bq_u = Bq_u + Bu_i;
      Bq_v = Bq_v + Bv_i;
      Bq_xu = Bq_xu + Bxu_i;
      Bq_vu = Bq_vu + Bvu_i;
      
   end
   
   obj.building_model.continuous_time_model = struct('A',[],'Bu',[],'Bv',[],'Bxu',[],'Bvu',[],...
      'C',[],'Du',[],'Dv',[],'Dxu',[],'Dvu',[]);
   
   obj.building_model.continuous_time_model.('A') = zeros(n_x,n_x);
   obj.building_model.continuous_time_model.('Bu') = zeros(n_x,n_u);
   obj.building_model.continuous_time_model.('Bv') = zeros(n_x,n_v);
   obj.building_model.continuous_time_model.('Bxu') = zeros(n_x,n_x,n_u);
   obj.building_model.continuous_time_model.('Bvu') = zeros(n_x,n_v,n_u);
   
   obj.building_model.continuous_time_model.('A') = obj.building_model.thermal_submodel.A+obj.building_model.thermal_submodel.Bq*Aq;
   obj.building_model.continuous_time_model.('Bu') = obj.building_model.thermal_submodel.Bq*Bq_u;
   obj.building_model.continuous_time_model.('Bv') = obj.building_model.thermal_submodel.Bq*Bq_v;
   
   for i = 1:n_u
      obj.building_model.continuous_time_model.('Bxu')(:,:,i) = obj.building_model.thermal_submodel.Bq*Bq_xu(:,:,i);
      obj.building_model.continuous_time_model.('Bvu')(:,:,i) = obj.building_model.thermal_submodel.Bq*Bq_vu(:,:,i);
   end
   
   % TODO: choice of outputs
   obj.building_model.continuous_time_model.('C') = zeros(n_y,n_x);
   obj.building_model.continuous_time_model.('Du') = zeros(n_y,n_u);
   obj.building_model.continuous_time_model.('Dv') = zeros(n_y,n_v);
   obj.building_model.continuous_time_model.('Dxu') = zeros(n_y,n_x,n_u);
   obj.building_model.continuous_time_model.('Dvu') = zeros(n_y,n_v,n_u);
   
   obj.building_model.model_exists = true;
   obj.building_model.is_dirty = false;
     
   fprintfDbg(1,'New building model of %s ''%s'' created.\n\n',lower(Constants.building_name_str),obj.identifier);
end
