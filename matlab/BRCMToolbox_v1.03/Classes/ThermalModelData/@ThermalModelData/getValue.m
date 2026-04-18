function value = getValue(obj,identifier,property)
   %GETVALUE Retrieves the value of the property of a building data component.
   % INPUTS
   %   identifier: Identifier of the component based on convention (string).
   %   property:   Property name of the component's value one wants to get (string).
   % OUTPUTS
   %   value:      Value of the component's property. If the property cannot
   %               be evaluated, the the content of the property is returned, e.g. if
   %               descriptions, layers, vertices ...
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
      error('getValue:Arguments','Arguments are required to be of type string.\n');
   end
   
   % load all paramters in to caller's workspace
   if ~isempty(obj.parameters)
      
      n_params = length(obj.parameters);
      
      for i = 1:n_params
         
         % catch inconsitent data case: value can be NULL
         if ~isnan(str2double(obj.parameters(i).value))
            assignin('caller',obj.parameters(i).identifier,str2double(obj.parameters(i).value));
         else
            continue
         end
      end
   end
   
   % Consider identifier in order to get the type of element
   if ~isempty(ThermalModelData.check_identifier(identifier,Zone.key)) % is it a zone?
      
      idx = obj.getZoneIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         
         % check property exists
         try
            value2evaluate = obj.zones(idx).(property);
         catch %#ok<*CTCH>
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.zone_name_str),property,lower(Constants.zone_name_str),generateClassProperties(Constants.zone_classname_str));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.zone_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,BuildingElement.key)) % is it a building element?
      
      idx = obj.getBuildingElementIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         % check property exists
         try
            value2evaluate = obj.building_elements(idx).(property);
         catch
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.buildingelement_name_str),property,...
               lower(Constants.buildingelement_name_str),generateClassProperties(Constants.buildingelement_classname_str));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.buildingelement_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,Construction.key)) % is it a construction?
      
      idx = obj.getConstructionIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         % check property exists
         try
            value2evaluate = obj.constructions(idx).(property);
         catch
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.construction_name_str),property,...
               lower(Constants.construction_name_str),generateClassProperties(Constants.construction_classname_str));
         end
         
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.construction_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,Material.key)) % is it a material?
      
      idx = obj.getMaterialIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         % check property exists
         try
            value2evaluate = obj.materials(idx).(property);
         catch
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.material_name_str),property,...
               lower(Constants.material_name_str),generateClassProperties(Constants.material_classname_str));
         end
         
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.material_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,NoMassConstruction.key)) % is it a no mass construction?
      
      idx = obj.getNoMassConstructionIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         
         % check property exists
         try
            value2evaluate = obj.nomass_constructions(idx).(property);
         catch
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.nomass_construction_name_str),property,...
               lower(Constants.nomass_construction_name_str),generateClassProperties(Constants.nomass_construction_classname_str));
         end
         
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.nomass_construction_name_str));
      end
      
   elseif ~isempty(ThermalModelData.check_identifier(identifier,Window.key)) % is it a window?
      
      idx = obj.getWindowIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         % check property exists
         try
            value2evaluate = obj.windows(idx).(property);
         catch
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.window_name_str),property,...
               lower(Constants.window_name_str),generateClassProperties(Constants.window_classname_str));
         end
         
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.window_name_str));
      end
      
   else
      
      idx = obj.getParameterIdxFromIdentifier(identifier);
      
      if ~isempty(idx)
         
         % check property exists
         try
            value2evaluate = obj.parameters(idx).(property);
         catch
            error('getValue:Property',['Unknown %s property ''%s''.\n',...
               'Available %s properties: %s.\n'],lower(Constants.parameter_name_str),property,...
               lower(Constants.parameter_name_str),generateClassProperties(Constants.parameter_classname_str));
         end
      else
         error('getValue:Identifier',Constants.error_msg_unknown_identifier(identifier,Constants.parameter_name_str));
      end
      
   end
   
   % convert expression to double or return expression if not evaluable (identifiers,descriptions,cells,layers,vertices)
   try
      value = evalin('caller',value2evaluate);
   catch
      
      value = value2evaluate;
   end
   
end

function object_properties_str = generateClassProperties(ClassName)
   
   props = properties(ClassName);
   
   if length(props) > 1
      object_properties_str = sprintf('''%s''%s',props{1},sprintf(',''%s''',props{2:end}));
   else
      object_properties_str = props{1};
   end
end
