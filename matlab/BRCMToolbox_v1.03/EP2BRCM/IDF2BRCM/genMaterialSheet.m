
function [cm,EP2BRCMMaterialIDMap]  = genMaterialSheet(materials)
   %GENMATERIALSHEET Generates from the "intermediate objects" (see convertIDFObjects) a cellstring containing the material part of the BRCM Toolbox thermal
   % model data.
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
   
   
   %#ok<*AGROW>
   
   
   EP2BRCMMaterialIDMap = cell(0,2);
   cnt_EP2BRCMMaterialIDMap = 1;
   
   no_mats = length(materials);
   
   cm = {};
   cm_id = 1;
   cm_description = 2;
   cm_specific_heat_capacity = 3;
   cm_specific_thermal_resistance = 4;
   cm_density = 5;
   cm_R_value = 6;
   r_header = 1;
   r_current = 2;
   
   cm{r_header,cm_id} = 'identifier';
   cm{r_header,cm_description} = 'description';
   cm{r_header,cm_specific_heat_capacity} = 'specific_heat_capacity';
   cm{r_header,cm_specific_thermal_resistance} = 'specific_thermal_resistance';
   cm{r_header,cm_density} = 'density';
   cm{r_header,cm_R_value} = 'R_value';
   
   for i=1:no_mats
      
      m = materials(i);
      
      if strcmpi(m.type,'Material')
         specificHeat = m.specificHeat;
         resistivity = 1/m.conductivity;
         density = m.density;
         R_value = '';
      elseif strcmpi(m.type,'Material:NoMass')
         specificHeat = '';
         resistivity = '';
         density = '';
         R_value = m.thermalResistance;
      elseif strcmpi(m.type,'Material:AirGap')
         specificHeat = '';
         resistivity = '';
         density = '';
         R_value = m.thermalResistance;
      elseif strcmpi(m.type,'Material:InfraredTransparent')
         continue;
      else
         warning('genMaterialSheet:General',['Skipping ',m.identifier,' since it is of Type: ',m.type])
         continue
      end
      
      cm{r_current,cm_id} = sprintf('M%4.4d',r_current-1);
      cm{r_current,cm_description} = m.identifier;
      cm{r_current,cm_specific_heat_capacity} = specificHeat;
      cm{r_current,cm_specific_thermal_resistance} = resistivity;
      cm{r_current,cm_density} = density;
      cm{r_current,cm_R_value} = R_value;
      
      EP2BRCMMaterialIDMap{cnt_EP2BRCMMaterialIDMap,1} = m.identifier;
      EP2BRCMMaterialIDMap{cnt_EP2BRCMMaterialIDMap,2} = cm{r_current,cm_id};
      cnt_EP2BRCMMaterialIDMap = cnt_EP2BRCMMaterialIDMap+1;
      
      r_current = r_current+1;
      
      
   end
   
end
