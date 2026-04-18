function setValue(obj,identifier,property,value)
   %SETVALUE Sets the value of the property of a building data component.
   %   This method sets the property of the associated building component.
   %   The value must fulfil the attributes of the property, e.g. parameter
   %   identifier convention or feasibilty.
   % INPUTS
   %   identifier:     Identifier of the building component.
   %   property:       Property of the component.
   %   value:          Value of the property.
   %--------------------------------------------------------------------------
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
   
   
   
   
   if ~ischar(identifier) || ~ischar(property)
      error('getValue:Arguments','Arguments 1 and 2 are required to be of type string.\n');
   end
   
   % check type of argument value
   if ~(isnumeric(value) || ischar(value) || iscellstr(value) || isa(value,Constants.layer_classname_str)) || isempty(value)
      error('getValue:Arguments','Argument 3 is required to be of either of type string, cellstring, numeric or %s.\n',Constants.layer_classname_str);
   end
   
   if isnumeric(value)
      value = num2str(value,Constants.num2str_precision);
   end
   
   % value can be of type string or cellstr or layer
   
   % Consider identifier in order to get the type of element
   if ~isempty(ThermalModelData.check_identifier(identifier,Zone.key)) % is it a zone?
      
      idx = obj.getZoneIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         
         % check property if property exists
         if ~propertyExists(obj.zones(idx),property)
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.zone_name_str),property,lower(Constants.zone_name_str),generateClassPropertiesString(properties(obj.zones(idx))));
         end
         
         % check if property is allowed to be set
         [isAllowedToSet,setableProps] = checkAndGetPropertySetAllowed(obj.zones(idx),property);
         
         if isAllowedToSet
            
            % set property
            switch property
               
               case 'description'
                  if ~ischar(value)
                     error('setValue:Zone','Invalid type for property %s. String required\n',property);
                  end
               case 'group'
                  
                  if iscellstr(value)
                     
                     n_values = length(value);
                     for i = 1:n_values
                        
                        if isempty(ThermalModelData.check_special_identifier(value{i}))
                           error('setValue:Zone','Value of property %s does not fulfil convention.\n',property);
                        end
                     end
                  else
                     error('setValue:Zone','Value of property %s requires to be of type cellstring.\n',property);
                  end
            end
            obj.zones(idx).(property) = value;
            
         else
            % print string of allowed properties
            error('setValue:Property','Property ''%s'' not allowed to be set. %s properties allowed to be set: %s.\n',property,Constants.zone_name_str,generateClassPropertiesString(setableProps));
         end
         
      else
         error('setValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.zone_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,BuildingElement.key)) % is it a building element?
      
      idx = obj.getBuildingElementIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         
         % check property if property exists
         if ~propertyExists(obj.building_elements(idx),property)
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.buildingelement_name_str),property,lower(Constants.buildingelement_name_str),generateClassPropertiesString(properties(obj.building_elements(idx))));
         end
         
         % check if property is allowed to be set
         [isAllowedToSet,setableProps] = checkAndGetPropertySetAllowed(obj.building_elements(idx),property);
         
         if isAllowedToSet
            
            switch property
               
               case 'description'
                  if ~ischar(value)
                     error('setValue:BuildingElement','Invalid type for property %s. String required\n',property);
                  end
                  
               case {'construction_identifier','window_identifier'}
                  if ~(~isempty(ThermalModelData.check_identifier(value,Construction.key)) || ~isempty(ThermalModelData.check_identifier(value,NoMassConstruction.key)) ...
                        || ~isempty(ThermalModelData.check_identifier(value,Window.key)))
                     error('setValue:BuildingElement','Invalid value for property %s. Identifier conventions violated.\n',property);
                  end
                  
               case {'adjacent_A','adjacent_B'}
                  if isempty(ThermalModelData.check_identifier_adjacent(value,Zone.key))
                     error('setValue:BuildingElement','Invalid value for property %s. Identifier conventions violated.\n',property);
                  end
            end
            
            % set property
            obj.building_elements(idx).(property) = value;
         else
            % print string of allowed properties
            error('setValue:Property','Property ''%s'' not allowed to be set. %s properties allowed to be set: %s.\n',property,Constants.buildingelement_name_str,generateClassPropertiesString(setableProps));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.buildingelement_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,Construction.key)) % is it a construction?
      
      idx = obj.getConstructionIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         
         % check property if property exists
         if ~propertyExists(obj.constructions(idx),property)
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.construction_name_str),property,lower(Constants.construction_name_str),generateClassPropertiesString(properties(obj.constructions(idx))));
            
         end
         
         % check if property is allowed to be set
         [isAllowedToSet,setableProps] = checkAndGetPropertySetAllowed(obj.constructions(idx),property);
         
         if isAllowedToSet
            
            switch property
               case 'description'
                  if ~ischar(value)
                     error('setValue:Construction','Invalid type for property %s. String required\n',property);
                  end
                  
               case 'layers'
                  
                  if ~isa(value,Constants.layer_classname_str)
                     error('setValue:Layer','Invalid value type for property %s. Type %s required\n',property,Constants.layer_classname_str);
                  else
                     n_layers = length(value);
                     
                     for i = 1:n_layers
                        
                        if ~(~isempty(ThermalModelData.check_identifier(value(i).material_identifier,Material.key)) && value(i).thickness > 0)
                           error('setValue:Layer','Invalid value for property %s. %s identifier and strictly positive value for the thickness required.\n',property,Constants.material_name_str);
                        end
                     end
                  end
                  
               case {'conv_coeff_adjacent_A','conv_coeff_adjacent_B'}
                  
                  conv_coeff = ThermalModelData.check_value(value,true);
                  if isempty(conv_coeff) || strcmp(conv_coeff,Constants.NULL_str)
                     error('setValue:Construction','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  elseif ~isnan(str2double(conv_coeff)) && ~(str2double(conv_coeff) > 0)
                     error('setValue:Construction','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  end
                  value = conv_coeff;
            end
            
            % set property
            obj.constructions(idx).(property) = value;
         else
            % print string of allowed properties
            error('setValue:Property','Property ''%s'' not allowed to be set. %s properties allowed to be set: %s.\n',property,Constants.construction_name_str,generateClassPropertiesString(setableProps));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.construction_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,Material.key)) % is it a material?
      
      idx = obj.getMaterialIdxFromIdentifier(identifier);
      if ~isempty(idx)
         
         % check property if property exists
         if ~propertyExists(obj.materials(idx),property)
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.material_name_str),property,lower(Constants.material_name_str),generateClassPropertiesString(properties(obj.materials(idx))));
         end
         
         % check if property is allowed to be set
         [isAllowedToSet,setableProps] = checkAndGetPropertySetAllowed(obj.materials(idx),property);
         
         if isAllowedToSet
            
            switch property
               case 'description'
                  if ~ischar(value)
                     error('setValue:Material','Invalid type for property %s. String required\n',property);
                  end
                  
               case {'specific_heat_capacity','specific_thermal_resistance','density','R_value'}
                  
                  value_mat = ThermalModelData.check_value(value,true);
                  if isempty(value_mat) || strcmp(value_mat,Constants.NULL_str)
                     error('setValue:Material','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  elseif ~isnan(str2double(value_mat)) && ~(str2double(value_mat) > 0)
                     error('setValue:Material','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  end
                  value = value_mat;
            end
            
            % set property
            obj.materials(idx).(property) = value;
         else
            % print string of allowed properties
            error('setValue:Property','Property ''%s'' not allowed to be set. %s properties allowed to be set: %s.\n',property,Constants.material_name_str,generateClassPropertiesString(setableProps));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.material_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,NoMassConstruction.key)) % is it a no mass construction?
      
      idx = obj.getNoMassConstructionIdxFromIdentifier(identifier);
      if ~isempty(idx)
         
         % check property if property exists
         if ~propertyExists(obj.nomass_constructions(idx),property)
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.nomass_construction_name_str),property,lower(Constants.nomass_construction_name_str),generateClassPropertiesString(properties(obj.nomass_constructions(idx))));
         end
         
         % check if property is allowed to be set
         [isAllowedToSet,setableProps] = checkAndGetPropertySetAllowed(obj.nomass_constructions(idx),property);
         
         if isAllowedToSet
            
            switch property
               case 'description'
                  if ~ischar(value)
                     error('setValue:NoMassConstruction','Invalid type for property %s. String required\n',property);
                  end
               case 'U_value'
                  value_nmp = ThermalModelData.check_value(value,true);
                  if isempty(value_nmp) || strcmp(value_nmp,Constants.NULL_str)
                     error('setValue:NoMassConstruction','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  elseif ~isnan(str2double(value_nmp)) && ~(str2double(value_nmp) > 0)
                     error('setValue:NoMassConstruction','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  end
                  value = value_nmp;
            end
            
            % set property
            obj.nomass_constructions(idx).(property) = value;
         else
            % print string of allowed properties
            error('setValue:Property','Property ''%s'' not allowed to be set. %s properties allowed to be set: %s.\n',property,Constants.nomass_construction_name_str,generateClassPropertiesString(setableProps));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.nomass_construction_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,Window.key)) % is it a window?
      
      idx = obj.getWindowIdxFromIdentifier(identifier);
      if ~isempty(idx)
         
         % check property if property exists
         if ~propertyExists(obj.windows(idx),property)
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.window_name_str),property,lower(Constants.window_name_str),generateClassPropertiesString(properties(obj.windows(idx))));
         end
         
         % check if property is allowed to be set
         [isAllowedToSet,setableProps] = checkAndGetPropertySetAllowed(obj.windows(idx),property);
         
         if isAllowedToSet
            
            switch property
               case 'description'
                  if ~ischar(value)
                     error('setValue:Window','Invalid type for property %s. String required\n',property);
                  end
               case {'glass_area','frame_area','SHGC'}
                  
                  value_win = ThermalModelData.check_value(value,true);
                  if isempty(value_win) || strcmp(value_win,Constants.NULL_str)
                     error('setValue:Window','Invalid value for property %s. %s identifier or string representing positive value.\n',property,Constants.parameter_name_str);
                  elseif ~isnan(str2double(value_win)) && ~(str2double(value_win) >= 0)
                     error('setValue:Window','Invalid value for property %s. %s identifier or string representing positive value.\n',property,Constants.parameter_name_str);
                  end
                  value = value_win;
               case {'U_value'}
                  
                  value_win = ThermalModelData.check_value(value,true);
                  if isempty(value_win) || strcmp(value_win,Constants.NULL_str)
                     error('setValue:Window','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  elseif ~isnan(str2double(value_win)) && ~(str2double(value_win) > 0)
                     error('setValue:Window','Invalid value for property %s. %s identifier or string representing strictly positive value.\n',property,Constants.parameter_name_str);
                  end
                  value = value_win;
            end
            
            % set property
            obj.windows(idx).(property) = value;
         else
            % print string of allowed properties
            error('setValue:Property','Property ''%s'' not allowed to be set. %s properties allowed to be set: %s.\n',property,Constants.window_name_str,generateClassPropertiesString(setableProps));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.window_name_str));
      end
      
   elseif ~isempty(obj.getParameterIdxFromIdentifier(identifier)) % is it a parameter?
      
      idx = obj.getParameterIdxFromIdentifier(identifier);
      if ~isempty(idx)
         
         % check property if property exists
         if ~propertyExists(obj.parameters(idx),property)
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.parameter_name_str),property,lower(Constants.parameter_name_str),generateClassPropertiesString(properties(obj.parameters(idx))));
         end
         
         % check if property is allowed to be set
         [isAllowedToSet,setableProps] = checkAndGetPropertySetAllowed(obj.parameters(idx),property);
         
         if isAllowedToSet
            
            switch property
               case 'description'
                  if ~ischar(value)
                     error('setValue:Parameter','Invalid type for property %s. String required\n',property);
                  end
               case 'value'
                  value_par = ThermalModelData.check_value(value,false);
                  if isempty(value_par) || strcmp(value_par,Constants.NULL_str)
                     error('setValue:Parameter','Invalid value for property %s.\n',property);
                  elseif ~(str2double(value_par) > 0)
                     error('setValue:Parameter','Invalid value for property %s. Strictly positive value required.\n',property);
                  end
                  value = value_par;
            end
            % set property
            obj.parameters(idx).(property) = value;
            
         else
            % print string of allowed properties
            error('setValue:Property','Property ''%s'' not allowed to be set. %s properties allowed to be set: %s.\n',property,Constants.parameter_name_str,generateClassPropertiesString(setableProps));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.parameter_name_str));
      end
      
   else
      error('getValue:Arguments','Unknown identifier type.\n');
   end
   
   function object_properties_str = generateClassPropertiesString(props)
      
      if length(props) > 1
         object_properties_str = sprintf('''%s''%s',props{1},sprintf(',''%s''',props{2:end}));
      else
         object_properties_str = props{1};
      end
   end
   
   function tf = propertyExists(Class,property)
      
      tf = true;
      props = properties(Class);
      
      member = intersect(props,property);
      
      if isempty(member)
         tf = false;
      end
      
   end
   
   function [tf,props] = checkAndGetPropertySetAllowed(Class,property)
      
      tf = true;
      props = properties(Class);
      
      switch class(Class)
         
         case Constants.zone_classname_str
            
            % only description and group
            props = { props{2} props{end}};
         case Constants.buildingelement_classname_str
            
            % description,construction_identifier,adjacent_A,adjacent_B,window_identifier
            props = props(2:6);
            
         case Constants.construction_classname_str
            
            % only description,layers and conv_coeff_A/B
            
            props = props(2:end);
            
         case Constants.material_classname_str
            
            % description,specific_heat_capacity,specific_thermal_resistance, density
            props = props(2:end);
            
         case Constants.window_classname_str
            
            % description,glass_area,frame_area,U_value and SHGC
            props = props(2:end);
            
         case Constants.nomass_construction_classname_str
            
            % description and value
            props = props(2:end);
            
         case Constants.parameter_classname_str
            
            % decription and value
            props = props(2:end);
      end
      
      member = intersect(props,property);
      
      if isempty(member)
         tf = false;
      end
      
   end
   
end
