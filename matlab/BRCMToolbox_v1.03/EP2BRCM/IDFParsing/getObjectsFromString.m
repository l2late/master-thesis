

function o = getObjectsFromString(str)
   %GETOBJECTSFROMSTRING Reads a string and converts it into an object. In the string it is assumed that ';' denotes an object to object boundary and ',' an object value to object value boundary.
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
   

   inds = find(str == ';');
   o = struct('type','','values',{});
   for i=0:length(inds)-1
      if i == 0
         o(i+1) = getObjectFromString(str(1:inds(1))); 
      else
         o(i+1) = getObjectFromString(str(inds(i)+1:inds(i+1)));      
      end
   end

end


function o = getObjectFromString(str)

   zeros_one = zeros(size(str));
   zeros_one(end) = 1;
   
   if length(str) <= 1 || ~all( (str == ';') == zeros_one) || any(str == '!')
      error('Bad string format..');
   end;
   
   str(end) = [];
   
   o.type = '';
   o.values = {};
      
   inds = find(str == ',');
   
   if length(inds)<1
      o.type = str(1:end);
      return
   end
   
   if inds(1) == 1, o.values{end+1} = '';  end
   
   o.type = str(1:inds(1)-1);
   
   for i=1:length(inds)
      if i == length(inds)
         o.values{end+1} = str(inds(i)+1:end);
      else
         o.values{end+1} = str(inds(i)+1:inds(i+1)-1);
      end
   end

end
