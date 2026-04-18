%     Copyright (C) 2021  Mathias Hudoba de Badyn
% 
%     This program is free software: you can redistribute it and/or modify
%     it under the terms of the GNU General Public License as published by
%     the Free Software Foundation, either version 3 of the License, or
%     (at your option) any later version.
% 
%     This program is distributed in the hope that it will be useful,
%     but WITHOUT ANY WARRANTY; without even the implied warranty of
%     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%     GNU General Public License for more details.

function [u] = infNormProj(Fu,u, g)
%infNormProj: Does the infinity norm projection for the control constraint


len_g = length(g);


for ii = 1:len_g
    
   f = Fu(ii,:);
   
   if nnz(f) == 1
       % box constraint found
       
       % get index of f that's nonzero
       ind = find(f);
       if f*u > g(ii)
           u(ind) = g(ii);
       end
   else 
       % record index of non-box constraint
   end
    
    
    
end



end

