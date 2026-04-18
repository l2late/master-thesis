

function [objectTypes,n] = getUniqueCellStringsAndFrequency(c,displayFlag)
   % GETUNIQUECELLSTRINGSANDFREQUENCY Returns the unique values in a cellstring along with their frequency.
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
   
   
   if nargin < 2
      displayFlag = false;
   end

   objectTypes = unique(c);
   n = zeros(length(objectTypes),1);
   for i=1:length(objectTypes)
      n(i) = sum(strcmpi(objectTypes{i},c));
   end
   [n,p] = sort(n,'descend');
   objectTypes = objectTypes(p);
   
   if displayFlag
      % display object types
      for i = 1:length(objectTypes)
         fprintfDbg(0,'  %3d',n(i));
         fprintfDbg(0,'  |  %s',objectTypes{i});
         fprintfDbg(0,'\n');
      end
      fprintfDbg(0,'\n');
   end
   
end
