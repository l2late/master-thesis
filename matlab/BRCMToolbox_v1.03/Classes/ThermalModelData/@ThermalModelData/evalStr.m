
function r = evalStr(obj,str,errorStr)
   % EVALSTR Evaluates a string into a number. String may contain
   % parameters
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
   
      
   for i=1:length(obj.parameters)
      eval(sprintf('%s = %s;',obj.parameters(i).identifier,obj.parameters(i).value));
   end
   
   try
      
      if isempty(str)
         error('isEmpty');
      end
      
      r = eval(str);

      if isnan(r)
         error('isNan');
      elseif isempty(r)
         error('isEmpty')
      elseif ~isnumeric(r)
         error('~isNumeric')
      end
      
   catch e
      
      if nargin < 2
         error('evalStr:General','Evaluating string ''%s'' failed with message %s\n',str,e.message);
      else
         error('evalStr:General','Evaluating string ''%s'' (%s) failed with message %s\n',str,errorStr,e.message);
      end
      
   end
   
end
