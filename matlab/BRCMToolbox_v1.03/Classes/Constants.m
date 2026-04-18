classdef Constants
   %CONSTANTS This class stores all the constants such as physical constants, tolerances and conventions.
   %   This class stores the main constant parameters, such as names, physical
   %   values, identifiers, conventions and error messages used in the toolbox
   %   setup. This class cannot be instantiated.
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
   
   
   
   
   
   properties(Constant)
      % Physics
      C_air@double = 1012; % heat capacity of air @25degC, [J/kgK]
      rho_air@double = 1.2041; % density of air @25degC, [kg/m^3]
      
      % Regexp
      % Matlab version
      expr_IF_WITH_METACLASS_SUPPORT@char = '%\s*?IF_WITH_METACLASS_SUPPORT';
      expr_IF_NO_METACLASS_SUPPORT@char = '%\s*?IF_NO_METACLASS_SUPPORT';
      expr_classdef@char = '^classdef\s*[A-Za-z]\w*';
      expr_MATLAB_release@char = 'R20\d\d[a-z]';
      expr_InpFile@char = '.+\.(xls|xlsx|csv)';
      supported_file_extensions@cell = {'*.xls';'*.xlsx';'*.csv'};
      expr_zones@char = '^zones.(xls|xlsx|csv)';
      expr_building_elements@char = '^buildingelements.(xls|xlsx|csv)';
      expr_constructions@char = '^constructions.(xls|xlsx|csv)';
      expr_nomass_constructions@char ='^nomassconstructions.(xls|xlsx|csv)';
      expr_materials@char = '^materials.(xls|xlsx|csv)';
      expr_windows@char = '^windows.(xls|xlsx|csv)';
      expr_parameters@char = '^parameters.(xls|xlsx|csv)';
      expr_identifier_key@char = '\d\d\d\d$';
      expr_coordinate@char = '[-+]?[0-9]*\.?[0-9]*+([eE][-+]?[0-9]*+)?';
      expr_vertices@char = ['(\(','[-+]?[0-9]*\.?[0-9]*+([eE][-+]?[0-9]*+)?','\,','[-+]?[0-9]*\.?[0-9]*+([eE][-+]?[0-9]*+)?','\,','[-+]?[0-9]*\.?[0-9]*+([eE][-+]?[0-9]*+)?','\))'];
      
      % Conventions
      zone_file_header@cell= { 'identifier' 'description' 'area' 'volume' 'group'}; %5
      building_element_file_header@cell = {'identifier' 'description' 'construction_identifier' 'adjacent_A' 'adjacent_B' ...
         'window_identifier'  'area' 'vertices'}; %8
      construction_file_header@cell = {'identifier' 'description' 'material_identifiers' 'thickness'...
         'conv_coeff_adjacent_A' 'conv_coeff_adjacent_B'}; %6
      nomass_construction_file_header@cell = {'identifier' 'description' 'U_value'}; % 3
      material_file_header@cell = {'identifier' 'description' 'specific_heat_capacity' ...
         'specific_thermal_resistance' 'density', 'R_value'}; %5
      window_file_header@cell = {'identifier' 'description' 'glass_area' 'frame_area' 'U_value' 'SHGC'}; %6
      parameter_file_header@cell = {'identifier' 'description' 'value'}; %3
      identifier_key@char = 'dddd';
      identifier_zero@char = '0000';
      NULL_str@char = 'NULL';
      NaN_str@char = 'NaN';
      ZERO_str@char = '0';
      EMPTY_str@char = '';
      num2str_precision@char = '%.10g';
      release_Matlab_OO@char = 'R2008a';
      release_Matlab_METACLASS@char = 'R2012a';
      
      % element names
      building_name_str@char = 'Building';
      buildingmodel_name_str@char = 'Building model';
      thermalmodel_name_str@char = 'Thermal model';
      simulation_name_str@char = 'Simulation experiment';
      zone_name_str@char = 'Zone';
      buildingelement_name_str@char = 'Building element';
      construction_name_str@char = 'Construction';
      nomass_construction_name_str@char = 'No mass construction';
      material_name_str@char = 'Material';
      window_name_str@char = 'Window';
      parameter_name_str@char = 'Parameter';
      vertex_name_str@char = 'Vertex';
      layer_name_str@char = 'Layer';
      
      % element class names
      building_classname_str@char = 'Building';
      buildingmodel_classname_str@char = 'BuildingModel';
      simulation_classname_str@char = 'SimulationExperiment';
      zone_classname_str@char = 'Zone';
      buildingelement_classname_str@char = 'BuildingElement';
      construction_classname_str@char = 'Construction';
      nomass_construction_classname_str@char = 'NoMassConstruction';
      material_classname_str@char = 'Material';
      window_classname_str@char = 'Window';
      parameter_classname_str@char = 'Parameter';
      vertex_classname_str@char = 'Vertex';
      layer_classname_str@char = 'Layer';
      identifier_classname_str@char = 'Identifier';
      
      % element file names
      zone_filename@char = 'zones';
      buildingelement_filename@char = 'buildingelements';
      construction_filename@char = 'constructions';
      nomass_construction_filename@char = 'nomassconstructions';
      material_filename@char = 'materials';
      window_filename@char = 'windows';
      parameter_filename@char = 'parameters';
      fileextension_XLS@char = '.xls';
      fileextension_CSV@char = '.csv';
      
      % Special identifiers
      ground_name_str@char = 'ground';
      ambient_name_str@char = 'ambient';
      adiabatic_name_str@char = 'adiabatic';
      user_defined_name_str@char = 'user_defined';
      ground_identifier@char = 'GND'; % GND:=GROUND
      var_ground_identifier@char = 'Tgnd'; % GND:=GROUND
      ambient_identifier@char = 'AMB'; % AMB:=AMBIENT
      var_ambient_identifier@char = 'Tamb'; % amb:=AMBIENT
      adiabatic_identifier@char = 'ADB'; % ADB:=ADIABATIC
      TBCwFC@char = 'TBCwFC'; % temperature boundary condition with film coefficient 
      TBCwoFC@char = 'TBCwoFC'; % temperature boundary condition without film coefficient 
      exterior@cell= {'GND' 'AMB' 'ADB'};
      
      % Tolerances
      tol_planarity@double = 0.05; % tolerance for non-planarity of vertices in a building element [m]
      tol_area@double = 0.01; % tolerance for area, when checking consistency of building elment (floor,ceil) area and associated zone [m^2]
      tol_height@double = 0.01; % tolerance for the alignment of vertices of a vertical building elment (z-coordinates) [m]
      tol_norm_vec@double = 0.01; % tolerance for normal vector [m]
      
      % Variable names
      state_variable@char = 'x';
      layer_state_variable@char = 's';
      heat_flux_variable@char = 'q';
      input_variable@char = 'u';
      disturbance_variable@char = 'v';
      output_variable@char = 'y';
      
      % External heat flux model
      EHF_model_str@char = 'EHF model';
      
      identifier_str@char = 'identifier';

      % Simulation
      sim_default_str@char = 'default';
      sim_inputTrajectory_str@char = 'inputTrajectory';
      sim_handle_str@char = 'handle';
      
      % TODO: these depend on time vector and current matrix B
      default_amplitude@double = 5; % ?C
      default_period_hrs@double = 10;
      
      % Draw Building
      z_label@char = 'z';
      y_label@char = 'y (North)';
      x_label@char = 'x (East)';
      zone_label_FontSize@double = 18;
      aspect_ratio@double = [1 1 1];
      view3d@double = 3;
      view2d@double = 2;
      view2d_str@char = 'Floorplan';
      view3d_str@char = '3-D';
      noLabels@char = 'NoLabels';
      noBELabels@char = 'NoBELabels';
      noZoneLabels@char = 'NoZoneLabels';
      
      legend_edge_width@double = 2;
      
      % Colors for plots
      state_color@double = [0 0 1]; % blue
      building_element_color@double = [1 1 0]; % yellow
      building_element_nomass_color@double = [0.4 0 0]; % brown
      building_element_edge_color@double = [1 0.6 0]; % orange
      window_color@double = [0.2 1 1]; % turquise
      window_edge_color@double = [0 0 1]; % blue
      alpha_transparency@double = 0.05;
      vertex_color@double = [1 0 0]; % red
      vertex_size@double = 50;
      
      % Plot labels
      time@char = 'Time [hrs]';
      temperature@char = 'Temp [?C]';
      heatflux@char = 'Heat Flux [W]';
      input_u@char = 'Control input u';
      input_v@char = 'Disturbance v';
      output_y@char = 'Output y';
      tool_box_name@char = 'Building RC-Modelling Toolbox';
      figure_name_simulation@char = 'Simulation of Building';
      fig_scale_left@double = 1/16;
      fig_scale_bottom@double = 1/14;
      fig_scale_width@double = 6/7;
      fig_scale_height@double = 6/7;
   end %properties(Constant)
   
   % We do not allow an instantion of this object
   methods(Access=private)
      
      % constructor
      function obj = Constants()
         
      end % Constants
      
   end %methods(Access=private)
   
   methods(Static)
      
      function err_msg = error_msg_unknown_identifier(identifier,type)
         
         err_msg = sprintf('Unknown %s identifier ''%s''.\n',lower(type),identifier);
         
      end % error_msg_unknown_identifier
      
      function err_msg = error_msg_string(parameter_str)
         err_msg = sprintf('%s is required to be of type string.\n',parameter_str);
         
      end % err_msg_string
      
      function err_msg = error_msg_numeric(parameter_str)
         err_msg = sprintf('%s is required to be a numeric value.\n',parameter_str);
         
      end % err_msg_numeric
      
      function err_msg = error_msg_illegal_layer(construction_idx,layer_idx,parameter_str)
         err_msg = sprintf('Construction %d has illegal layer %d.\n''%s'' is required to be positive for a multi-layered construction\n',...
            construction_idx,layer_idx,parameter_str);
      end % error_msg_illegal_layer
      
      function err_msg = error_msg_xlsFile(element_str,file,row,col,varargin) %#ok<INUSD>
         
         % Catch sprintf issue when on windows machine: regexprep(file,'\\','\\\\')
         
         if length(varargin)==1
            err_msg = sprintf('In file ''%s'' at row %d columns %d and %d:\n',regexprep(file,'\\','\\\\'),row,col,varargin{1});
         elseif isempty(varargin)
            err_msg = sprintf('In file ''%s'' at row %d column %d:\n',regexprep(file,'\\','\\\\'),row,col);
         else
            error('ErrMsg:Arguments','Number of arguments inappropriate.\n');
         end
         
      end % error_msg_xlsFile
      
      function err_msg = error_msg_anchor_XLS(element_str,file,anchor)
         
         err_msg = sprintf('Unable to read %s data file ''%s'' due to missing anchor ''%s''.\n',lower(element_str),regexprep(file,'\\','\\\\'),anchor);
         
      end % error_msg_anchor_XLS
      
      function err_msg = error_msg_identifier(element_str,identifier,key_str)
         
         err_msg = sprintf('%s identifier ''%s'' is illegal.\nCONVENTION: %s%s, %s%s is illegal.\n',element_str,identifier,key_str,...
            Constants.identifier_key,key_str,Constants.identifier_zero);
      end % error_msg_identifier
      
      function err_msg = error_msg_identifierAdjacent(identifier,key_str)
         
         err_msg = sprintf('Illegal entry ''%s'' for the identifier.\nCONVENTION: %sdddd or %s, %s, %s.\n',...
            identifier,key_str,key_str,Constants.ground_identifier,Constants.ambient_identifier,Constants.adiabatic_identifier);
         
      end % error_msg_identifier_Adjacent
      
      function err_msg = error_msg_identifierAdjacentZone(element_str)
         
         err_msg = sprintf('At least one identifier must be a %s identifier.\n',lower(element_str));
         
      end % error_msg_identifierAdjacentZone
      
      function err_msg = error_msg_identifier_special(element_str,identifier)
         
         err_msg = sprintf(['Illegal entry ''%s'' for the %s identifier.\nCONVENTION: First letter must be [A-Za-z], for the remainder [A-Za-z_0-9], '...
            'except last letter must be [A-Za-z0-9].\n'],...
            identifier,lower(element_str));
         
      end % error_msg_identifier_special
      
      function err_msg = error_msg_value(element_str,value_str,parameter_str,isParamId,geqZero_str)
         
         if isParamId
            err_msg = sprintf('Illegal entry ''%s'' for the ''%s'' of a %s.\nCONVENTION: String (Parameter Identifier) or Numeric %s.\n',...
               value_str,parameter_str,lower(element_str),geqZero_str);
         else
            err_msg = sprintf('Illegal entry ''%s'' for the ''%s'' of a %s.\nCONVENTION: Numeric %s.\n',...
               value_str,parameter_str,lower(element_str),geqZero_str);
         end
         
      end % error_msg_value
      
      function err_msg = error_msg_zone_group(element_str,group_str)
         
         err_msg =  sprintf(['Illegal entry ''%s'' for the ''%s group''.\nCONVENTION: Comma separated elements required. Elements must start with alphabetic character, ',...
            'special characters ?,@,$,) etc. and identifiers of elements are not allowed, e.g. group_id1,Group_id2 or use ''%s'' for no specific group assignment.\n'],...
            group_str,lower(element_str),Constants.EMPTY_str);
         
      end % error_msg_zone_group
      
      function err_msg = error_msg_group_identifiers(element_str,group_str,key_str)
         
         err_msg = sprintf('Illegal entry ''%s'' for the ''%s identifier/s''.\nCONVENTION: Comma separeted list of %s identifiers, e.g. %s0002,%s0004,%s0001 and %s0000 is illegal.\n',...
            group_str,lower(element_str),lower(element_str),key_str,key_str,key_str,key_str);
         
      end % error_msg_group_identifiers
      
      function err_msg = error_msg_group_values(element_str,value_str,parameter_str)
         
         err_msg = sprintf('Illegal entry ''%s'' for the ''%s %s''.\nCONVENTION: Comma separated numerics > 0, e.g. 0.1,0.4,0.05.\n',...
            value_str,lower(element_str),parameter_str);
         
      end % error_msg_group_values
      
      function err_msg = error_group_consistency(element_str,parameter_str)
         
         err_msg = sprintf('Number of elements (%s identifiers, %s) must be equal.\n',lower(element_str),parameter_str);
         
      end % error_msg_group_consistency
      
      function err_msg = error_NULL_entry(element_str,idx,parameter_str)
         
         err_msg = sprintf('%s ''%d'' has entry ''%s'' for the ''%s''.\n',element_str,idx,Constants.NULL_str,parameter_str);
         
      end % error_NULL_entry
      
   end %methods(Static)
end % class def
