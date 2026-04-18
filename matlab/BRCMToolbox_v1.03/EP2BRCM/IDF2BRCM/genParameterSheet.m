
function cp = genParameterSheet(reqParams)
   %GENPARAMETERSHEET Generates from a list of required parameters a cellstring containing the parameters part of the BRCM Toolbox thermal  model data. Default
   % values are set.
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
   
   
   cp = {};
   cp_id = 1;
   cp_description = 2;
   cp_value = 3;
   r_header = 1;
   r_current = 2;
   
   
   cp{r_header,cp_id} = 'identifier';
   cp{r_header,cp_description} = 'description';
   cp{r_header,cp_value} = 'value';
   
   
   fns = fieldnames(reqParams);
   for i = 1:numel(fns)
      r = reqParams.(fns{i});
      for j=1:length(r)
         cp{r_current,cp_id} = r{j};
         [description,value] = get_parameterDescriptionAndValue(r{j});
         cp{r_current,cp_description} = description;
         cp{r_current,cp_value} = value;
         r_current = r_current+1;
      end
   end
   
   
end


function [description,value] = get_parameterDescriptionAndValue(id)
   
   
   description = 'empty_description';
   value = nan;
   
   
   if strcmpi('UValue_IRTransparent',id)
      
      description = 'UValue of Infrared Partition (usually used to model two parts of the same room)';
      value = 100;
      
   elseif strcmpi('convCoeff_UNKNOWN',id)
      
      description = 'Convective coefficient of unknown surface (corresponding construction unused in building elements)';
      value = 0;
      
   elseif strcmpi('convCoeff_InternalMass',id)
      
      description = 'Convective Coefficient of Internal Mass (default, considering thermal radiation)';
      value = 6;
      
   elseif strncmpi('convCoeff_',id,length('convCoeff_'))
      
      tmp = id(length('convCoeff_')+1:end);
      
      if ~isempty(strfind(id,'ADB'))
         description = 'Convective coefficient of a ground contact surface (unused, set to 0)';
         value = 0;
         return
      end
      
      if ~isempty(strfind(id,'GND'))
         description = 'Convective coefficient of a adiabatic surface (unused, set to 0)';
         value = 0;
         return
      end
      
      if ~isempty(strfind(id,Constants.TBCwFC))
         n = regexp(id,'FilmCoeff_(\S*)','tokens');
         n = n{1}{1};
         n = regexprep(n,'p','.');
         n = str2double(n);
         description = 'Convective coefficient of OtherSideCoefficients boundary condition';
         value = n;
         return
      end
      
      if ~isempty(strfind(id,Constants.TBCwoFC))
         description = 'Convective coefficient of OtherSideCoefficients boundary condition (unused, set to 0)';
         value = 0;
         return
      end
      
      if ~isempty(strfind(id,'Ext'))
         description = 'Convective coefficient of a surface to ambient air (default)';
         value = 12.5;
         return
      end
      
      
      
      if strcmpi('CeilingInt',tmp)
         description = 'Convective coefficient of ceiling to zone (default, considering thermal radiation)';
         value = 8;
      elseif strcmpi('RoofInt',tmp)
         description = 'Convective coefficient of roof to zone (default, considering thermal radiation)';
         value = 8;
      elseif strcmpi('FloorInt',tmp)
         description = 'Convective coefficient of floor to zone (default, considering thermal radiation)';
         value = 5;
      elseif strcmpi('WallInt',tmp)
         description = 'Convective coefficient of wall to zone (default, considering thermal radiation)';
         value = 7;
      else
         warning(['Unknown parameter id: ',id]);
      end
      
   elseif strncmpi('UValue_Window_EPConstr_',id,length('UValue_Window_EPConstr_'))
      
      tmp = id(length('UValue_Window_EPConstr_')+1:end);
      description = ['UValue of Window with EP Construction',tmp,' (default value)'];
      value = 1;
      
   elseif strncmpi('GValue_Window_EPConstr_',id,length('GValue_Window_EPConstr_'))
      
      tmp = id(length('GValue_Window_EPConstr_')+1:end);
      description = ['GValue of Window with EP Construction',tmp,' (default value)'];
      value = 0.5;
      
   else
      
      warning(['Unknown parameter id: ',id]);
      
   end
end
