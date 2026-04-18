function checkAllThermalModelDataFilesAvailable(file_list)
   %CHECKALLTHERMALMODELDATAFILESAVAILABLE Checks whether all the required files for the thermal model data are available.
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
   
   
   % We require 7 files, namely:
   % zones
   % buildingelements
   % constructions
   % materials
   % windows
   % parameters
   % nomassconstructions
   
   
   
   if isempty(file_list)
      error('checkTMDataFiles:Available','No .xls/.xlsx/.csv files found.\n');
   end
      
   
   
   n_found = sum(cellfun(@(x)~isempty(x),regexpi(file_list,Constants.expr_building_elements,'match')));
   if n_found == 0
      error('checkTMDataFiles:Available','%s file is missing.\n',Constants.buildingelement_name_str);
   elseif n_found>1
      fprintfDbg(0,'Found multiple %s files. Load order: .csv -> .xls ->. xlsx.\n',Constants.buildingelement_name_str);
   end
   
   % constructions
   n_found = sum(cellfun(@(x)~isempty(x),regexpi(file_list,Constants.expr_constructions,'match')));
   if n_found == 0
      error('checkTMDataFiles:Available','%s file is missing.\n',Constants.construction_name_str);
   elseif n_found>1
      fprintfDbg(0,'Found multiple %s files. Load order: .csv -> .xls ->. xlsx.\n',Constants.construction_name_str);
   end
   
   % materials
   n_found = sum(cellfun(@(x)~isempty(x),regexpi(file_list,Constants.expr_materials,'match')));
   if n_found == 0
      error('checkTMDataFiles:Available','%s file is missing.\n',Constants.material_name_str);
   elseif n_found>1
      fprintfDbg(0,'Found multiple %s files. Load order: .csv -> .xls ->. xlsx.\n',Constants.material_name_str);
   end
   
   % parameters
   n_found = sum(cellfun(@(x)~isempty(x),regexpi(file_list,Constants.expr_parameters,'match')));
   if n_found == 0
      error('checkTMDataFiles:Available','%s file is missing.\n',Constants.parameter_name_str);
   elseif n_found>1
      fprintfDbg(0,'Found multiple %s files. Load order: .csv -> .xls ->. xlsx.\n',Constants.parameter_name_str);
   end
   
   % windows
   n_found = sum(cellfun(@(x)~isempty(x),regexpi(file_list,Constants.expr_windows,'match')));
   if n_found == 0
      error('checkTMDataFiles:Available','%s file is missing.\n',Constants.window_name_str);
   elseif n_found>1
      fprintfDbg(0,'Found multiple %s files. Load order: .csv -> .xls ->. xlsx.\n',Constants.window_name_str);
   end
   
   % zones
   n_found = sum(cellfun(@(x)~isempty(x),regexpi(file_list,Constants.expr_zones,'match')));
   if n_found == 0
      error('checkTMDataFiles:Available','%s file is missing.\n',Constants.zone_name_str);
   elseif n_found>1
      fprintfDbg(0,'Found multiple %s files. Load order: .csv -> .xls ->. xlsx.\n',Constants.zone_name_str);
   end
   
   n_found = sum(cellfun(@(x)~isempty(x),regexpi(file_list,Constants.expr_nomass_constructions,'match')));
   if n_found == 0
      error('checkTMDataFiles:Available','%s file is missing.\n',Constants.nomass_construction_name_str);
   elseif n_found>1
      fprintfDbg(0,'Found multiple %s files. Load order: .csv -> .xls ->. xlsx.\n',Constants.nomass_construction_name_str);
   end
   
   
end
